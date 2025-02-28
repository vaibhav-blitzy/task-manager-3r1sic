# Third-party imports
import json
import pytest  # pytest: Testing framework for writing and executing tests
from mongomock import ObjectId  # mongomock: MongoDB mock for testing database operations

# Internal imports
from conftest import member_api_client, test_user, test_admin, test_project, test_project_member, test_project_members, create_test_project_member, mock_project_db, mock_event_bus
from ..models.member import ProjectRole  # Enumeration of valid project member roles
from ..services.member_service import MemberService  # Service layer for project member operations
from '../../../common/exceptions/api_exceptions' import ValidationError, NotFoundError, AuthorizationError, ConflictError  # Exception for validation errors in API requests

# member_blueprint \u2014 Blueprint('members', __name__)
# logger \u2014 get_logger(__name__)
# member_service \u2014 MemberService()

def test_get_project_members(member_api_client, test_project, test_project_members, mock_project_db):
    """Tests the GET /api/projects/{id}/members endpoint to verify it correctly returns a list of members for a project"""
    # Send a GET request to /api/projects/{test_project.id}/members
    response = member_api_client.get(f'/{test_project.id}/members')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the response contains 'items' and 'total' keys
    assert 'items' in response.json
    assert 'total' in response.json
    # Assert the total matches the expected number of members
    assert response.json['total'] == len(test_project_members)
    # Assert each member has required fields (id, user_id, role, joined_at)
    for member in response.json['items']:
        assert 'id' in member
        assert 'user_id' in member
        assert 'role' in member
        assert 'joined_at' in member

@pytest.mark.parametrize('page,per_page,expected_count', [(1, 2, 2), (2, 2, 2), (3, 2, 1)])
def test_get_project_members_with_pagination(member_api_client, test_project, test_project_members, mock_project_db, page, per_page, expected_count):
    """Tests that the member listing API correctly implements pagination"""
    # Send a GET request to /api/projects/{test_project.id}/members?page={page}&per_page={per_page}
    response = member_api_client.get(f'/{test_project.id}/members?page={page}&per_page={per_page}')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the response contains pagination metadata (page, per_page, total)
    assert 'page' in response.json['metadata']
    assert 'per_page' in response.json['metadata']
    assert 'total' in response.json['metadata']
    # Assert the number of items returned matches the expected count
    assert len(response.json['items']) == expected_count
    # Assert the page number in the response matches the requested page
    assert response.json['metadata']['page'] == page

@pytest.mark.parametrize('role,expected_count', [('admin', 1), ('member', 3), ('viewer', 1)])
def test_get_project_members_filtering(member_api_client, test_project, test_project_members, mock_project_db, role, expected_count):
    """Tests that the member listing API correctly handles filtering by role"""
    # Send a GET request to /api/projects/{test_project.id}/members?role={role}
    response = member_api_client.get(f'/{test_project.id}/members?role={role}')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the number of items returned matches the expected count
    assert len(response.json['items']) == expected_count
    # Assert all returned members have the requested role
    for member in response.json['items']:
        assert member['role'] == role

def test_get_project_member_detail(member_api_client, test_project, test_project_member, mock_project_db):
    """Tests the GET /api/projects/{id}/members/{member_id} endpoint for retrieving a specific member"""
    # Send a GET request to /api/projects/{test_project.id}/members/{test_project_member.id}
    response = member_api_client.get(f'/{test_project.id}/members/{test_project_member.id}')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the response contains member details (id, user_id, role, joined_at)
    assert 'id' in response.json
    assert 'user_id' in response.json
    assert 'role' in response.json
    assert 'joined_at' in response.json
    # Assert the returned member ID matches the requested member ID
    assert response.json['id'] == test_project_member.id

def test_get_project_member_not_found(member_api_client, test_project, mock_project_db):
    """Tests that the API correctly handles requests for non-existent members"""
    # Generate a non-existent member ID
    non_existent_id = '60d1b9a7e9b9c6a7b3a7b3a7'
    # Send a GET request to /api/projects/{test_project.id}/members/{non_existent_id}
    response = member_api_client.get(f'/{test_project.id}/members/{non_existent_id}')
    # Assert the response status code is 404
    assert response.status_code == 404
    # Assert the response contains an appropriate error message
    assert 'message' in response.json
    assert 'Member not found' in response.json['message']

@pytest.mark.parametrize('role', ['admin', 'manager', 'member', 'viewer'])
def test_add_project_member(member_api_client, test_project, test_user, mock_project_db, mock_event_bus, role):
    """Tests the POST /api/projects/{id}/members endpoint for adding a new member to a project"""
    # Create a new user to be added as a member
    new_user_id = '64b404a7e9b9c6a7b3a7b3a8'
    # Prepare payload with user_id and role
    payload = {'user_id': new_user_id, 'role': role}
    # Send a POST request to /api/projects/{test_project.id}/members with the payload
    response = member_api_client.post(f'/{test_project.id}/members', json=payload)
    # Assert the response status code is 201
    assert response.status_code == 201
    # Assert the response contains the new member details
    assert 'id' in response.json
    assert response.json['user_id'] == new_user_id
    # Assert the role matches the requested role
    assert response.json['role'] == role
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Verify the member was added to the database
    assert mock_project_db.project_members.find_one({'user_id': new_user_id, 'project_id': test_project.id})

def test_add_project_member_invalid_role(member_api_client, test_project, test_user, mock_project_db):
    """Tests that the API validates member roles when adding new members"""
    # Create a new user to be added as a member
    new_user_id = '64b404a7e9b9c6a7b3a7b3a8'
    # Prepare payload with user_id and an invalid role
    payload = {'user_id': new_user_id, 'role': 'invalid_role'}
    # Send a POST request to /api/projects/{test_project.id}/members with the payload
    response = member_api_client.post(f'/{test_project.id}/members', json=payload)
    # Assert the response status code is 400
    assert response.status_code == 400
    # Assert the response contains an appropriate error message about invalid role
    assert 'message' in response.json
    assert 'Invalid role' in response.json['message']

def test_add_project_member_already_exists(member_api_client, test_project, test_project_member, mock_project_db):
    """Tests that the API correctly handles attempts to add a user who is already a member"""
    # Prepare payload with an existing member's user_id and a role
    payload = {'user_id': test_project_member.user_id, 'role': 'member'}
    # Send a POST request to /api/projects/{test_project.id}/members with the payload
    response = member_api_client.post(f'/{test_project.id}/members', json=payload)
    # Assert the response status code is 409 (Conflict)
    assert response.status_code == 409
    # Assert the response contains an error message about the user already being a member
    assert 'message' in response.json
    assert 'User is already a member' in response.json['message']

@pytest.mark.parametrize('new_role', ['admin', 'manager', 'member', 'viewer'])
def test_update_member_role(member_api_client, test_project, test_project_member, mock_project_db, mock_event_bus, new_role):
    """Tests the PATCH /api/projects/{id}/members/{member_id} endpoint for updating a member's role"""
    # Prepare payload with the new role
    payload = {'role': new_role}
    # Send a PATCH request to /api/projects/{test_project.id}/members/{test_project_member.id} with the payload
    response = member_api_client.patch(f'/{test_project.id}/members/{test_project_member.id}', json=payload)
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the response contains the updated member details
    assert 'id' in response.json
    assert response.json['user_id'] == test_project_member.user_id
    # Assert the role has been updated to the new role
    assert response.json['role'] == new_role
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Verify the member role was updated in the database
    updated_member = mock_project_db.project_members.find_one({'_id': test_project_member.id})
    assert updated_member['role'] == new_role

def test_update_member_role_invalid_role(member_api_client, test_project, test_project_member, mock_project_db):
    """Tests that the API validates roles when updating member roles"""
    # Prepare payload with an invalid role
    payload = {'role': 'invalid_role'}
    # Send a PATCH request to /api/projects/{test_project.id}/members/{test_project_member.id} with the payload
    response = member_api_client.patch(f'/{test_project.id}/members/{test_project_member.id}', json=payload)
    # Assert the response status code is 400
    assert response.status_code == 400
    # Assert the response contains an error message about invalid role
    assert 'message' in response.json
    assert 'Invalid role' in response.json['message']

def test_remove_project_member(member_api_client, test_project, mock_project_db, mock_event_bus):
    """Tests the DELETE /api/projects/{id}/members/{member_id} endpoint for removing a member"""
    # Create a non-owner member to be removed
    member_to_remove = create_test_project_member(mock_project_db, user_id='64b404a7e9b9c6a7b3a7b3a9', project_id=test_project.id, role='member')
    # Send a DELETE request to /api/projects/{test_project.id}/members/{member_id}
    response = member_api_client.delete(f'/{test_project.id}/members/{member_to_remove.id}')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Assert the response indicates successful removal
    assert 'message' in response.json
    assert 'Member removed from project' in response.json['message']
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Verify the member was removed from the database
    assert mock_project_db.project_members.find_one({'_id': member_to_remove.id}) is None

def test_remove_project_owner(member_api_client, test_project, mock_project_db):
    """Tests that the API prevents removing the project owner from the members list"""
    # Identify the project owner member
    owner_member_id = test_project.owner_id
    # Send a DELETE request to /api/projects/{test_project.id}/members/{owner_member_id}
    response = member_api_client.delete(f'/{test_project.id}/members/{owner_member_id}')
    # Assert the response status code is 400
    assert response.status_code == 400
    # Assert the response contains an error message about not being able to remove the owner
    assert 'message' in response.json
    assert 'Cannot remove the last admin' in response.json['message']

@pytest.mark.parametrize('endpoint,method', [
    ('/api/projects/{id}/members', 'GET'),
    ('/api/projects/{id}/members', 'POST'),
    ('/api/projects/{id}/members/{member_id}', 'GET'),
    ('/api/projects/{id}/members/{member_id}', 'PATCH'),
    ('/api/projects/{id}/members/{member_id}', 'DELETE')
])
def test_member_api_authorization(app, test_project, test_user, endpoint, method):
    """Tests that member management endpoints enforce proper authorization checks"""
    # Create a client with a non-member user token
    client = app.test_client()
    with app.test_request_context():
        # Make requests to the specified endpoint with the specified method
        if method == 'GET':
            response = client.get(endpoint.format(id=test_project.id, member_id=test_user['_id']))
        elif method == 'POST':
            response = client.post(endpoint.format(id=test_project.id, member_id=test_user['_id']), json={'user_id': test_user['_id'], 'role': 'member'})
        elif method == 'PATCH':
            response = client.patch(endpoint.format(id=test_project.id, member_id=test_user['_id']), json={'role': 'manager'})
        elif method == 'DELETE':
            response = client.delete(endpoint.format(id=test_project.id, member_id=test_user['_id']))
        # Assert the response status code is 403 (Forbidden)
        assert response.status_code == 403
        # Assert the response contains an appropriate error message
        assert 'message' in response.json
        assert 'You do not have permission' in response.json['message']

@pytest.mark.parametrize('member_role,target_role,expected_status', [
    ('member', 'admin', 403),
    ('manager', 'admin', 403),
    ('admin', 'admin', 201),
    ('admin', 'member', 201)
])
def test_role_hierarchy_permissions(member_api_client, test_project, test_user, mock_project_db, member_role, target_role, expected_status):
    """Tests that members can only assign roles equal to or lower than their own"""
    # Create a member with the specified member_role
    requesting_member = create_test_project_member(mock_project_db, user_id='64b404a7e9b9c6a7b3a7b3aa', project_id=test_project.id, role=member_role)
    # Create a client authenticated as this member
    payload = {'user_id': '64b404a7e9b9c6a7b3a7b3ab', 'role': target_role}
    # Send a POST request to add the new member
    response = member_api_client.post(f'/{test_project.id}/members', json=payload)
    # Assert the response status code matches expected_status
    assert response.status_code == expected_status
    # If expected_status is 201, verify the member was added correctly
    if expected_status == 201:
        assert 'id' in response.json
        assert response.json['user_id'] == '64b404a7e9b9c6a7b3a7b3ab'
        assert response.json['role'] == target_role
    # If expected_status is 403, verify the error message indicates insufficient permissions
    elif expected_status == 403:
        assert 'message' in response.json
        assert 'You do not have permission' in response.json['message']

def test_notification_on_member_add(member_api_client, test_project, test_user, mock_project_db, mock_event_bus):
    """Tests that adding a member triggers a notification event"""
    # Create a new user to be added as a member
    new_user_id = '64b404a7e9b9c6a7b3a7b3a8'
    # Prepare payload with user_id and role
    payload = {'user_id': new_user_id, 'role': 'member'}
    # Send a POST request to add the member
    response = member_api_client.post(f'/{test_project.id}/members', json=payload)
    # Assert the response status code is 201
    assert response.status_code == 201
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Assert the event has the correct type ('project.member_added')
    event_type, event_data = mock_event_bus.publish.call_args[0]
    assert event_type == 'project.member_added'
    # Assert the event contains the project ID, user ID, and role
    assert event_data['payload']['project_id'] == test_project.id
    assert event_data['payload']['user_id'] == new_user_id
    assert event_data['payload']['role'] == 'member'

def test_notification_on_member_role_update(member_api_client, test_project, test_project_member, mock_project_db, mock_event_bus):
    """Tests that updating a member's role triggers a notification event"""
    # Prepare payload with a new role different from the current role
    new_role = 'manager'
    payload = {'role': new_role}
    # Send a PATCH request to update the member's role
    response = member_api_client.patch(f'/{test_project.id}/members/{test_project_member.id}', json=payload)
    # Assert the response status code is 200
    assert response.status_code == 200
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Assert the event has the correct type ('project.member_role_updated')
    event_type, event_data = mock_event_bus.publish.call_args[0]
    assert event_type == 'project.member_role_updated'
    # Assert the event contains the project ID, user ID, old role, and new role
    assert event_data['payload']['project_id'] == test_project.id
    assert event_data['payload']['user_id'] == test_project_member.user_id
    assert event_data['payload']['new_role'] == new_role

def test_notification_on_member_remove(member_api_client, test_project, mock_project_db, mock_event_bus):
    """Tests that removing a member triggers a notification event"""
    # Create a non-owner member to be removed
    member_to_remove = create_test_project_member(mock_project_db, user_id='64b404a7e9b9c6a7b3a7b3a9', project_id=test_project.id, role='member')
    # Send a DELETE request to remove the member
    response = member_api_client.delete(f'/{test_project.id}/members/{member_to_remove.id}')
    # Assert the response status code is 200
    assert response.status_code == 200
    # Verify that an event was published to the event bus
    assert mock_event_bus.publish.called
    # Assert the event has the correct type ('project.member_removed')
    event_type, event_data = mock_event_bus.publish.call_args[0]
    assert event_type == 'project.member_removed'
    # Assert the event contains the project ID and user ID
    assert event_data['payload']['project_id'] == test_project.id
    assert event_data['payload']['user_id'] == member_to_remove.user_id