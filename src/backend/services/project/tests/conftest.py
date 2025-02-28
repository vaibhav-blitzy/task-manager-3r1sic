"""
Provides pytest fixtures specifically for testing the Project service API endpoints,
models, and business logic. Includes fixtures for test database connections,
authenticated test clients, mock services, and sample test data for projects and team members.
"""

# Standard library imports
import uuid
from datetime import datetime

# Third-party imports
import pytest  # pytest: Testing framework for defining fixtures
import mongomock  # mongomock: Mocking MongoDB for unit tests
from bson import ObjectId  # bson: MongoDB BSON handling for ObjectId
from unittest import mock  # unittest.mock: Mocking framework for service dependencies

# Internal imports
from src.backend.common.testing.fixtures import app, client, mongo_db, redis_cache, auth_headers, test_user, test_admin_user, create_test_project  # app, client, mongo_db, redis_cache, auth_headers, test_user, test_admin_user, create_test_project: Import the Flask test application fixture
from src.backend.common.testing.mocks import mock_auth_middleware  # mock_auth_middleware: Import utility to mock authentication middleware
from src.backend.services.project.app import create_app  # create_app: Import project service app factory function
from src.backend.services.project.models.project import Project  # Project: Import Project model for creating test projects
from src.backend.services.project.models.member import ProjectMember, ProjectRole  # ProjectMember, ProjectRole: Import ProjectMember model for creating test members
from src.backend.common.events.event_bus import get_event_bus_instance  # get_event_bus_instance: Import event bus instance for mocking

# Global constants for collection names
PROJECT_COLLECTION = "projects"
MEMBER_COLLECTION = "project_members"

@pytest.fixture
def project_app():
    """Creates a Flask test application for the Project service"""
    app = create_app("testing")
    return app

@pytest.fixture
def project_client(project_app):
    """Creates a Flask test client specifically for the Project service"""
    return project_app.test_client()

@pytest.fixture
def authenticated_project_client(project_client, test_user, auth_headers):
    """Creates a Flask test client with valid authentication headers"""
    with mock_auth_middleware():
        project_client.environ_base['HTTP_AUTHORIZATION'] = auth_headers['Authorization']
        return project_client

@pytest.fixture
def projects_api_client(authenticated_project_client):
    """Creates an authenticated client specifically for projects API endpoints"""
    authenticated_project_client.base_url = '/api/v1/projects'
    authenticated_project_client.content_type = 'application/json'
    return authenticated_project_client

@pytest.fixture
def member_api_client(authenticated_project_client):
    """Creates an authenticated client specifically for project members API endpoints"""
    authenticated_project_client.base_url = '/api/v1/projects'
    authenticated_project_client.content_type = 'application/json'
    return authenticated_project_client

@pytest.fixture
def mock_project_db(mongo_db):
    """Creates a mock project database for unit testing"""
    db = mongo_db
    if "projects" not in db.list_collection_names():
        db.create_collection("projects")
    if "project_members" not in db.list_collection_names():
        db.create_collection("project_members")
    return db

@pytest.fixture
def test_admin(test_admin_user):
    """Creates a test admin user for admin-specific tests"""
    return test_admin_user

@pytest.fixture
def project_data():
    """Provides standard project test data for creating new projects"""
    return {
        "name": "Test Project",
        "description": "This is a test project",
        "status": "active",
        "category": "Test Category"
    }

@pytest.fixture
def test_project(mock_project_db, test_user):
    """Creates a single test project for project-related tests"""
    project_data = {
        "name": "Test Project",
        "description": "This is a test project",
        "status": "active"
    }
    project = Project.from_dict(project_data)
    project._data["owner_id"] = ObjectId(test_user["_id"])
    project.save()

    member = ProjectMember.from_dict({
        "project_id": str(project.get_id()),
        "user_id": test_user["_id"],
        "role": ProjectRole.ADMIN.value
    })
    member.save()
    return project

@pytest.fixture
def test_projects(mock_project_db, test_user):
    """Creates multiple test projects for testing listing and filtering"""
    projects = []
    for i in range(5):
        project_data = {
            "name": f"Test Project {i}",
            "description": f"This is test project {i}",
            "status": "active" if i % 2 == 0 else "planning",
            "category": f"Category {i % 3}"
        }
        project = Project.from_dict(project_data)
        project._data["owner_id"] = ObjectId(test_user["_id"])
        project.save()
        projects.append(project)
    return projects

@pytest.fixture
def member_data():
    """Provides standard project member test data"""
    return {
        "user_id": "test_user_id",
        "role": "member",
        "timestamp": datetime.now()
    }

@pytest.fixture
def test_project_member(mock_project_db, test_user, test_project):
    """Creates a test project member for member-related tests"""
    member_data = {
        "project_id": str(test_project.get_id()),
        "user_id": test_user["_id"],
        "role": ProjectRole.ADMIN.value
    }
    member = ProjectMember.from_dict(member_data)
    member.save()
    return member

@pytest.fixture
def test_project_members(mock_project_db, test_project):
    """Creates multiple test project members for testing listing and filtering"""
    members = []
    roles = [ProjectRole.ADMIN.value, ProjectRole.MEMBER.value, ProjectRole.VIEWER.value]
    for i in range(3):
        user_id = str(uuid.uuid4())
        member_data = {
            "project_id": str(test_project.get_id()),
            "user_id": user_id,
            "role": roles[i % len(roles)]
        }
        member = ProjectMember.from_dict(member_data)
        member.save()
        members.append(member)
    return members

@pytest.fixture
def test_project_with_task_lists(mock_project_db, test_user):
    """Creates a test project with multiple task lists"""
    project_data = {
        "name": "Test Project with Task Lists",
        "description": "This is a test project with task lists",
        "status": "active",
        "task_lists": [
            {"id": str(uuid.uuid4()), "name": "To Do", "description": "Tasks to do"},
            {"id": str(uuid.uuid4()), "name": "In Progress", "description": "Tasks in progress"},
            {"id": str(uuid.uuid4()), "name": "Done", "description": "Completed tasks"}
        ]
    }
    project = Project.from_dict(project_data)
    project._data["owner_id"] = ObjectId(test_user["_id"])
    project.save()
    return project

@pytest.fixture
def test_project_with_members(mock_project_db, test_user):
    """Creates a test project with multiple members"""
    project_data = {
        "name": "Test Project with Members",
        "description": "This is a test project with members",
        "status": "active",
    }
    project = Project.from_dict(project_data)
    project._data["owner_id"] = ObjectId(test_user["_id"])
    project.save()

    roles = [ProjectRole.ADMIN.value, ProjectRole.MEMBER.value, ProjectRole.VIEWER.value]
    for i in range(3):
        user_id = str(uuid.uuid4())
        member_data = {
            "project_id": str(project.get_id()),
            "user_id": user_id,
            "role": roles[i % len(roles)]
        }
        member = ProjectMember.from_dict(member_data)
        member.save()
    return project

def create_test_project_member(mock_project_db, user_id, project_id, role):
    """Utility function to create a test project member with specified parameters"""
    member_data = {
        "project_id": project_id,
        "user_id": user_id,
        "role": role
    }
    member = ProjectMember.from_dict(member_data)
    member.save()
    return member

@pytest.fixture
def mock_event_bus():
    """Mocks the event bus for testing event publishing"""
    event_bus_module = "src.backend.common.events.event_bus"
    with mock.patch(f"{event_bus_module}.get_event_bus_instance") as mock_get_event_bus:
        mock_bus = mock.MagicMock()
        mock_get_event_bus.return_value = mock_bus
        mock_bus.publish.return_value = True
        yield mock_bus