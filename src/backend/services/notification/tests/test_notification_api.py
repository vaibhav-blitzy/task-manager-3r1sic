# Standard library imports
import json
from unittest.mock import MagicMock

# Third-party imports
import pytest
from flask import Flask

# Internal imports
from src.backend.services.notification.api.notifications import notification_blueprint
from src.backend.services.notification.api.preferences import preferences_blueprint
from src.backend.services.notification.models.notification import NotificationType, NotificationPriority
from src.backend.services.notification.tests.conftest import create_test_notification, test_notification, test_notification_preferences, notification_collection, preference_collection, notification_service
from src.backend.common.testing.fixtures import test_user, mongo_db
from src.backend.common.database.mongo.models import object_id_to_str

BASE_URL = "/api/v1/notifications"
PREFERENCES_URL = "/api/v1/notifications/preferences"


@pytest.fixture
def create_test_app() -> Flask:
    """
    Create a Flask test application with notification and preference blueprints
    """
    # Create a new Flask application with test configuration
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Register notification_blueprint under '/api/v1/notifications'
    app.register_blueprint(notification_blueprint, url_prefix='/api/v1/notifications')

    # Register preferences_blueprint under '/api/v1/notifications/preferences'
    app.register_blueprint(preferences_blueprint, url_prefix='/api/v1/notifications/preferences')

    # Configure test JWT handling
    app.config['JWT_SECRET_KEY'] = 'test-secret'  # Replace with a secure key in production
    app.config['JWT_ALGORITHM'] = 'HS256'

    # Return the configured application
    return app


@pytest.fixture
def test_client(create_test_app: Flask):
    """
    Create a test client for the Flask application
    """
    # Create test client from the Flask application
    client = create_test_app.test_client()

    # Configure client to handle JSON automatically
    client.environ_base['CONTENT_TYPE'] = 'application/json'

    # Return the test client
    return client


@pytest.fixture
def authenticated_client(test_client: Flask, test_user: dict):
    """
    Create an authenticated test client with JWT tokens for testing protected endpoints
    """
    # Create JWT token for test_user
    auth_token = test_client.application.config['JWT_SECRET_KEY']
    token = generate_access_token(test_user)

    # Configure the test client with the auth token in headers
    test_client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    # Return the authenticated test client
    return test_client


def test_get_notifications(authenticated_client, test_user, notification_collection):
    """Test retrieving the list of notifications for a user"""
    # Create multiple test notifications for the test user
    notification1 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Task 1 Assigned",
        content="You have been assigned Task 1"
    )
    notification2 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.COMMENT_ADDED,
        title="New Comment on Task 2",
        content="A new comment has been added to Task 2"
    )
    notification_collection.insert_many([notification1, notification2])

    # Make GET request to '/api/v1/notifications'
    response = authenticated_client.get(BASE_URL)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains expected notifications
    data = json.loads(response.data.decode('utf-8'))
    assert len(data['items']) == 2
    assert data['items'][0]['title'] == "Task 1 Assigned"
    assert data['items'][1]['title'] == "New Comment on Task 2"

    # Verify pagination metadata is correct
    assert data['page'] == 1
    assert data['per_page'] == 50
    assert data['total'] == 2


def test_get_notification_by_id(authenticated_client, test_notification):
    """Test retrieving a single notification by ID"""
    # Extract notification ID from test_notification
    notification_id = test_notification['_id']

    # Make GET request to '/api/v1/notifications/{notification_id}'
    response = authenticated_client.get(f"{BASE_URL}/{notification_id}")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains the expected notification details
    data = json.loads(response.data.decode('utf-8'))
    assert data['title'] == "Test Task Assigned"
    assert data['content'] == "A test task has been assigned to you."

    # Verify all notification fields are correctly returned
    assert data['recipient_id'] == object_id_to_str(test_notification['recipient_id'])
    assert data['type'] == NotificationType.TASK_ASSIGNED.value
    assert data['priority'] == 'normal'
    assert data['read'] is False
    assert 'created' in data['metadata']


def test_get_notification_not_found(authenticated_client):
    """Test retrieving a non-existent notification returns 404"""
    # Create a non-existent notification ID
    non_existent_id = "nonexistent_notification_id"

    # Make GET request to '/api/v1/notifications/{non_existent_id}'
    response = authenticated_client.get(f"{BASE_URL}/{non_existent_id}")

    # Verify response status code is 404
    assert response.status_code == 404

    # Verify error message indicates resource not found
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Notification not found"


def test_get_notification_wrong_user(authenticated_client, notification_collection):
    """Test retrieving a notification belonging to another user returns 403"""
    # Create a notification assigned to a different user ID
    other_user_notification = create_test_notification(
        recipient_id="other_user_id",
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Other User Task",
        content="This task is not for you"
    )
    notification_collection.insert_one(other_user_notification)
    other_user_notification_id = other_user_notification['_id']

    # Make GET request to '/api/v1/notifications/{other_user_notification_id}'
    response = authenticated_client.get(f"{BASE_URL}/{other_user_notification_id}")

    # Verify response status code is 403
    assert response.status_code == 403

    # Verify error message indicates permission denied
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Unauthorized: Notification does not belong to this user"


def test_mark_notification_as_read(authenticated_client, test_notification, notification_collection):
    """Test marking a notification as read"""
    # Extract notification ID from test_notification
    notification_id = test_notification['_id']

    # Verify notification is initially unread
    notification = notification_collection.find_one({"_id": notification_id})
    assert notification['read'] is False

    # Make PATCH request to '/api/v1/notifications/{notification_id}/read'
    response = authenticated_client.patch(f"{BASE_URL}/{notification_id}/read")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response indicates notification was marked as read
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Notification marked as read"
    assert data['notification']['read'] is True

    # Verify notification in database is now marked as read
    updated_notification = notification_collection.find_one({"_id": notification_id})
    assert updated_notification['read'] is True


def test_mark_nonexistent_notification_as_read(authenticated_client):
    """Test marking a non-existent notification as read returns 404"""
    # Create a non-existent notification ID
    non_existent_id = "nonexistent_notification_id"

    # Make PATCH request to '/api/v1/notifications/{non_existent_id}/read'
    response = authenticated_client.patch(f"{BASE_URL}/{non_existent_id}/read")

    # Verify response status code is 404
    assert response.status_code == 404

    # Verify error message indicates resource not found
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Notification not found"


def test_mark_wrong_user_notification_as_read(authenticated_client, notification_collection):
    """Test marking another user's notification as read returns 403"""
    # Create a notification assigned to a different user ID
    other_user_notification = create_test_notification(
        recipient_id="other_user_id",
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Other User Task",
        content="This task is not for you"
    )
    notification_collection.insert_one(other_user_notification)
    other_user_notification_id = other_user_notification['_id']

    # Make PATCH request to '/api/v1/notifications/{other_user_notification_id}/read'
    response = authenticated_client.patch(f"{BASE_URL}/{other_user_notification_id}/read")

    # Verify response status code is 403
    assert response.status_code == 403

    # Verify error message indicates permission denied
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Unauthorized: Notification does not belong to this user"


def test_get_unread_count(authenticated_client, test_user, notification_collection):
    """Test retrieving the count of unread notifications"""
    # Create multiple test notifications, some read and some unread
    notification1 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Task 1 Assigned",
        content="You have been assigned Task 1"
    )
    notification2 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.COMMENT_ADDED,
        title="New Comment on Task 2",
        content="A new comment has been added to Task 2"
    )
    notification3 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Task 3 Assigned",
        content="You have been assigned Task 3"
    )
    notification1['read'] = True
    notification_collection.insert_many([notification1, notification2, notification3])

    # Make GET request to '/api/v1/notifications/unread/count'
    response = authenticated_client.get(f"{BASE_URL}/unread/count")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains the correct count of unread notifications
    data = json.loads(response.data.decode('utf-8'))
    assert data['unread_count'] == 2


def test_mark_all_as_read(authenticated_client, test_user, notification_collection):
    """Test marking all notifications as read"""
    # Create multiple unread test notifications
    notification1 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Task 1 Assigned",
        content="You have been assigned Task 1"
    )
    notification2 = create_test_notification(
        recipient_id=test_user['_id'],
        notification_type=NotificationType.COMMENT_ADDED,
        title="New Comment on Task 2",
        content="A new comment has been added to Task 2"
    )
    notification_collection.insert_many([notification1, notification2])

    # Make POST request to '/api/v1/notifications/read-all'
    response = authenticated_client.post(f"{BASE_URL}/read-all")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response indicates correct number of notifications marked as read
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "2 notifications marked as read"

    # Verify all notifications in database are now marked as read
    notifications = notification_collection.find({"recipient_id": test_user['_id']})
    for notification in notifications:
        assert notification['read'] is True


def test_send_test_notification(authenticated_client, test_user, notification_service):
    """Test sending a test notification"""
    # Prepare test notification data
    test_data = {
        "message": "This is a test notification",
        "channel": "in_app"
    }

    # Make POST request to '/api/v1/notifications/test' with test data
    response = authenticated_client.post(f"{BASE_URL}/test", json=test_data)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response indicates notification was sent successfully
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Test notification sent"

    # Verify notification_service.create_notification was called with correct parameters
    notification_service.send_test_notification.assert_called_once()
    args, kwargs = notification_service.send_test_notification.call_args
    assert args[0] == test_user['user_id']
    assert args[1] == "This is a test notification"
    assert args[2] == "in_app"


def test_send_test_notification_missing_data(authenticated_client):
    """Test sending a test notification with missing data returns 400"""
    # Prepare incomplete test notification data (missing required fields)
    test_data = {}

    # Make POST request to '/api/v1/notifications/test' with incomplete data
    response = authenticated_client.post(f"{BASE_URL}/test", json=test_data)

    # Verify response status code is 400
    assert response.status_code == 400

    # Verify error message indicates validation error
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Missing required parameters"


def test_get_preferences(authenticated_client, test_notification_preferences):
    """Test retrieving notification preferences"""
    # Make GET request to '/api/v1/notifications/preferences'
    response = authenticated_client.get(PREFERENCES_URL)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains expected preference data
    data = json.loads(response.data.decode('utf-8'))
    assert data['user_id'] == object_id_to_str(test_notification_preferences['user_id'])

    # Verify global settings match expected values
    assert data['global_settings']['in_app'] is True
    assert data['global_settings']['email'] is True
    assert data['global_settings']['push'] is False

    # Verify other preference sections exist
    assert 'type_settings' in data
    assert 'project_settings' in data
    assert 'quiet_hours' in data


def test_update_global_settings(authenticated_client, test_notification_preferences, preference_collection):
    """Test updating global notification preferences"""
    # Prepare updated global settings data
    updated_data = {
        "in_app": False,
        "email": True,
        "push": False,
        "digest": {
            "enabled": False,
            "frequency": "daily"
        }
    }

    # Make PUT request to '/api/v1/notifications/preferences/global' with updated data
    response = authenticated_client.put(f"{PREFERENCES_URL}/global", json=updated_data)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains updated preference data
    data = json.loads(response.data.decode('utf-8'))
    assert data['global_settings']['in_app'] is False
    assert data['global_settings']['email'] is True
    assert data['global_settings']['push'] is False
    assert data['global_settings']['digest']['enabled'] is False

    # Verify preference document in database was updated correctly
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert updated_preferences['global_settings']['in_app'] is False
    assert updated_preferences['global_settings']['email'] is True
    assert updated_preferences['global_settings']['push'] is False
    assert updated_preferences['global_settings']['digest']['enabled'] is False


def test_update_global_settings_invalid_data(authenticated_client):
    """Test updating global settings with invalid data returns 400"""
    # Prepare invalid global settings data (wrong types or missing fields)
    invalid_data = {
        "in_app": "not_a_boolean",
        "email": 123,
        "push": None
    }

    # Make PUT request to '/api/v1/notifications/preferences/global' with invalid data
    response = authenticated_client.put(f"{PREFERENCES_URL}/global", json=invalid_data)

    # Verify response status code is 400
    assert response.status_code == 400

    # Verify error message indicates validation error
    data = json.loads(response.data.decode('utf-8'))
    assert data['message'] == "Validation error"


def test_update_notification_type_settings(authenticated_client, test_notification_preferences, preference_collection):
    """Test updating preferences for a specific notification type"""
    # Prepare updated type settings data
    updated_data = {
        "in_app": True,
        "email": False,
        "push": True
    }

    # Make PUT request to '/api/v1/notifications/preferences/types/TASK_ASSIGNED' with updated data
    response = authenticated_client.put(f"{PREFERENCES_URL}/types/TASK_ASSIGNED", json=updated_data)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains updated preference data
    data = json.loads(response.data.decode('utf-8'))
    assert data['type_settings']['TASK_ASSIGNED']['in_app'] is True
    assert data['type_settings']['TASK_ASSIGNED']['email'] is False
    assert data['type_settings']['TASK_ASSIGNED']['push'] is True

    # Verify preference document in database was updated correctly for the specific type
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert updated_preferences['type_settings']['TASK_ASSIGNED']['in_app'] is True
    assert updated_preferences['type_settings']['TASK_ASSIGNED']['email'] is False
    assert updated_preferences['type_settings']['TASK_ASSIGNED']['push'] is True


def test_update_project_settings(authenticated_client, test_notification_preferences, preference_collection):
    """Test updating preferences for a specific project"""
    # Prepare updated project settings data
    updated_data = {
        "in_app": False,
        "email": True,
        "push": False
    }

    # Make PUT request to '/api/v1/notifications/preferences/projects/project123' with updated data
    response = authenticated_client.put(f"{PREFERENCES_URL}/projects/project123", json=updated_data)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains updated preference data
    data = json.loads(response.data.decode('utf-8'))
    assert data['project_settings']['project123']['in_app'] is False
    assert data['project_settings']['project123']['email'] is True
    assert data['project_settings']['project123']['push'] is False

    # Verify preference document in database was updated correctly for the specific project
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert updated_preferences['project_settings']['project123']['in_app'] is False
    assert updated_preferences['project_settings']['project123']['email'] is True
    assert updated_preferences['project_settings']['project123']['push'] is False


def test_update_quiet_hours(authenticated_client, test_notification_preferences, preference_collection):
    """Test updating quiet hours settings"""
    # Prepare updated quiet hours settings data
    updated_data = {
        "enabled": True,
        "start": "23:00",
        "end": "07:00",
        "timezone": "America/Los_Angeles",
        "excludeUrgent": False
    }

    # Make PUT request to '/api/v1/notifications/preferences/quiet-hours' with updated data
    response = authenticated_client.put(f"{PREFERENCES_URL}/quiet-hours", json=updated_data)

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response contains updated preference data
    data = json.loads(response.data.decode('utf-8'))
    assert data['quiet_hours']['enabled'] is True
    assert data['quiet_hours']['start'] == "23:00"
    assert data['quiet_hours']['end'] == "07:00"
    assert data['quiet_hours']['timezone'] == "America/Los_Angeles"
    assert data['quiet_hours']['excludeUrgent'] is False

    # Verify preference document in database was updated correctly for quiet hours
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert updated_preferences['quiet_hours']['enabled'] is True
    assert updated_preferences['quiet_hours']['start'] == "23:00"
    assert updated_preferences['quiet_hours']['end'] == "07:00"
    assert updated_preferences['quiet_hours']['timezone'] == "America/Los_Angeles"
    assert updated_preferences['quiet_hours']['excludeUrgent'] is False


def test_delete_type_settings(authenticated_client, test_notification_preferences, preference_collection):
    """Test deleting custom settings for a notification type"""
    # Set up test data with custom notification type settings
    type_settings = {"in_app": False, "email": True, "push": False}
    test_notification_preferences['type_settings'] = {"TASK_ASSIGNED": type_settings}
    preference_collection.update_one(
        {"user_id": test_notification_preferences['user_id']},
        {"$set": {"type_settings": test_notification_preferences['type_settings']}}
    )

    # Make DELETE request to '/api/v1/notifications/preferences/types/TASK_ASSIGNED'
    response = authenticated_client.delete(f"{PREFERENCES_URL}/types/TASK_ASSIGNED")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response shows updated preferences without the specific type settings
    data = json.loads(response.data.decode('utf-8'))
    assert "TASK_ASSIGNED" not in data['type_settings']

    # Verify type settings were removed from database document
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert "TASK_ASSIGNED" not in updated_preferences['type_settings']


def test_delete_project_settings(authenticated_client, test_notification_preferences, preference_collection):
    """Test deleting custom settings for a project"""
    # Set up test data with custom project settings
    project_settings = {"in_app": False, "email": True, "push": False}
    test_notification_preferences['project_settings'] = {"project123": project_settings}
    preference_collection.update_one(
        {"user_id": test_notification_preferences['user_id']},
        {"$set": {"project_settings": test_notification_preferences['project_settings']}}
    )

    # Make DELETE request to '/api/v1/notifications/preferences/projects/project123'
    response = authenticated_client.delete(f"{PREFERENCES_URL}/projects/project123")

    # Verify response status code is 200
    assert response.status_code == 200

    # Verify response shows updated preferences without the specific project settings
    data = json.loads(response.data.decode('utf-8'))
    assert "project123" not in data['project_settings']

    # Verify project settings were removed from database document
    updated_preferences = preference_collection.find_one({"user_id": test_notification_preferences['user_id']})
    assert "project123" not in updated_preferences['project_settings']