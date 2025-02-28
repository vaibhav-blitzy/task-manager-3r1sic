"""
Primary pytest configuration file for the Task Management System backend, providing fixtures
for both unit and integration tests. This file sets up test environments, mocks necessary
services, and creates test data for consistent and reliable testing across the entire backend.
"""

# Standard library imports
import os
import datetime
import uuid
import json

# Third-party imports
import pytest
import mongomock
import fakeredis
import requests

# Internal imports
from ..common.testing.fixtures import app_factory
from ..common.database.mongo.connection import get_db
from ..common.database.redis.connection import get_redis
from ..common.testing.mocks import mock_mongo_client, mock_redis_client, mock_event_bus
from ..common.auth.jwt_utils import generate_access_token
from ..common.config.testing import TestingConfig

# Global constants
BASE_URL = "http://localhost:5000/api/v1"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminSecurePass123!"


@pytest.fixture
def base_url():
    """
    Provides the base URL for API requests in tests.
    
    Returns:
        str: Base URL for API endpoints
    """
    return BASE_URL


@pytest.fixture(scope="session")
def mongo_db():
    """
    Creates a mock or real MongoDB connection for tests based on configuration.
    
    Returns:
        mongomock.MongoClient: MongoDB client for testing
    """
    # Check if TESTING_USE_REAL_DB environment variable is set
    use_real_db = os.environ.get('TESTING_USE_REAL_DB', 'false').lower() == 'true'
    
    if use_real_db:
        # If using real DB, create a connection to a test database
        client = get_db()
        # Initialize required collections and indexes
        yield client
        # After tests, clean up by dropping test databases if using real MongoDB
        test_db_name = os.environ.get('TEST_MONGO_DB_NAME', 'task_management_test')
        client.drop_database(test_db_name)
    else:
        # Otherwise, create a mongomock client
        client = mock_mongo_client()
        yield client


@pytest.fixture(scope="session")
def redis_cache():
    """
    Creates a mock or real Redis connection for tests based on configuration.
    
    Returns:
        fakeredis.FakeStrictRedis: Redis client for testing
    """
    # Check if TESTING_USE_REAL_REDIS environment variable is set
    use_real_redis = os.environ.get('TESTING_USE_REAL_REDIS', 'false').lower() == 'true'
    
    if use_real_redis:
        # If using real Redis, create a connection to a test database
        client = get_redis()
        yield client
        # After tests, flush the Redis database if using real Redis
        client.flushall()
    else:
        # Otherwise, create a fakeredis instance
        client = mock_redis_client()
        yield client


@pytest.fixture
def event_bus():
    """
    Creates a mock event bus for event-driven communication testing.
    
    Returns:
        MagicMock: Mock event bus for testing
    """
    # Create a mock event bus
    return mock_event_bus()


@pytest.fixture
def test_app():
    """
    Creates a Flask application instance for testing.
    
    Returns:
        Flask: Flask application configured for testing
    """
    # Create a Flask application using the app_factory function
    app = app_factory()
    # Configure the application with TestingConfig
    app.config.from_object(TestingConfig)
    return app


@pytest.fixture
def test_client(test_app):
    """
    Creates a Flask test client for making requests.
    
    Args:
        test_app (Flask): Flask application
        
    Returns:
        FlaskClient: Flask test client for making HTTP requests
    """
    # Create a test client from the provided Flask app
    return test_app.test_client()


@pytest.fixture
def standard_roles(mongo_db):
    """
    Creates standard user roles for testing.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        
    Returns:
        dict: Dictionary mapping role names to role documents
    """
    # Define standard roles (user, manager, admin)
    roles = {
        "user": {
            "_id": "role_user",
            "name": "User",
            "permissions": ["task:read", "task:create", "task:update", "comment:create"]
        },
        "manager": {
            "_id": "role_manager",
            "name": "Manager",
            "permissions": ["task:read", "task:create", "task:update", "task:delete", 
                           "project:read", "project:create", "project:update", "comment:create"]
        },
        "admin": {
            "_id": "role_admin",
            "name": "Admin",
            "permissions": ["task:*", "project:*", "user:*", "comment:*"]
        }
    }
    
    # Insert roles into the database if they don't exist
    for role in roles.values():
        mongo_db.roles.update_one({"_id": role["_id"]}, {"$set": role}, upsert=True)
    
    return roles


@pytest.fixture
def test_user(mongo_db, standard_roles):
    """
    Creates a standard test user for testing.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        standard_roles (dict): Standard roles
        
    Returns:
        dict: Test user document with credentials
    """
    # Create a user document with test email and password
    user = {
        "_id": "test_user_id",
        "email": TEST_USER_EMAIL,
        "password": "$2b$12$1234567890123456789012uXJVK2Ew5V0mZrSEYvwzPrJsGmXyMDu",  # Hashed password
        "firstName": "Test",
        "lastName": "User",
        "roleIds": [standard_roles["user"]["_id"]],
        "status": "active",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "settings": {
            "theme": "light",
            "notifications": {
                "email": True,
                "inApp": True
            }
        }
    }
    
    # Insert the user into the database if not exists
    mongo_db.users.update_one({"_id": user["_id"]}, {"$set": user}, upsert=True)
    
    return user


@pytest.fixture
def test_admin(mongo_db, standard_roles):
    """
    Creates an admin user for testing administrative functions.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        standard_roles (dict): Standard roles
        
    Returns:
        dict: Admin user document with credentials
    """
    # Create a user document with admin email and password
    admin = {
        "_id": "test_admin_id",
        "email": TEST_ADMIN_EMAIL,
        "password": "$2b$12$0987654321098765432109ugwfgwigfwigfwuegfuewgfgewgweweg",  # Hashed password
        "firstName": "Admin",
        "lastName": "User",
        "roleIds": [standard_roles["admin"]["_id"]],
        "status": "active",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "settings": {
            "theme": "dark",
            "notifications": {
                "email": True,
                "inApp": True
            }
        }
    }
    
    # Insert the admin user into the database if not exists
    mongo_db.users.update_one({"_id": admin["_id"]}, {"$set": admin}, upsert=True)
    
    return admin


@pytest.fixture
def authenticated_user_headers(test_user):
    """
    Creates authentication headers for a standard user.
    
    Args:
        test_user (dict): Test user document
        
    Returns:
        dict: Headers dictionary with authentication token
    """
    # Generate JWT token for the test user
    token = generate_access_token({
        "user_id": test_user["_id"],
        "email": test_user["email"],
        "role": "user"
    })
    
    # Create headers dictionary with Authorization bearer token
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def authenticated_admin_headers(test_admin):
    """
    Creates authentication headers for an admin user.
    
    Args:
        test_admin (dict): Admin user document
        
    Returns:
        dict: Headers dictionary with admin authentication token
    """
    # Generate JWT token for the admin user
    token = generate_access_token({
        "user_id": test_admin["_id"],
        "email": test_admin["email"],
        "role": "admin"
    })
    
    # Create headers dictionary with Authorization bearer token
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def authenticated_client(test_client, authenticated_user_headers):
    """
    Creates an authenticated test client with standard user permissions.
    
    Args:
        test_client (FlaskClient): Flask test client
        authenticated_user_headers (dict): Headers with auth token
        
    Returns:
        FlaskClient: Authenticated test client for API requests
    """
    # Create a test client using the test_client fixture
    test_client.environ_base = {
        'HTTP_AUTHORIZATION': authenticated_user_headers["Authorization"]
    }
    return test_client


@pytest.fixture
def authenticated_admin_client(test_client, authenticated_admin_headers):
    """
    Creates an authenticated test client with admin permissions.
    
    Args:
        test_client (FlaskClient): Flask test client
        authenticated_admin_headers (dict): Headers with admin auth token
        
    Returns:
        FlaskClient: Authenticated admin test client for API requests
    """
    # Create a test client using the test_client fixture
    test_client.environ_base = {
        'HTTP_AUTHORIZATION': authenticated_admin_headers["Authorization"]
    }
    return test_client


@pytest.fixture
def test_project(mongo_db, test_user):
    """
    Creates a test project for testing project-related functionality.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        test_user (dict): Test user document
        
    Returns:
        dict: Test project document
    """
    # Create a project document with test name and description
    project = {
        "_id": "test_project_id",
        "name": "Test Project",
        "description": "This is a test project for testing purposes",
        "status": "active",
        "owner": test_user["_id"],
        "members": [
            {"userId": test_user["_id"], "role": "owner"}
        ],
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "settings": {
            "workflow": {
                "enableReview": True,
                "allowSubtasks": True,
                "defaultTaskStatus": "not_started"
            },
            "permissions": {
                "memberInvite": "owner,admin",
                "taskCreate": "owner,admin,member",
                "commentCreate": "owner,admin,member,viewer"
            }
        },
        "tags": ["test"],
        "metadata": {
            "taskCount": 0,
            "completedTaskCount": 0
        }
    }
    
    # Insert project into database
    mongo_db.projects.insert_one(project)
    
    return project


@pytest.fixture
def test_task(mongo_db, test_user, test_project):
    """
    Creates a test task for testing task-related functionality.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        test_user (dict): Test user document
        test_project (dict): Test project document
        
    Returns:
        dict: Test task document
    """
    # Create a task document with test title and description
    due_date = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    
    task = {
        "_id": "test_task_id",
        "title": "Test Task",
        "description": "This is a test task for testing purposes",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "projectId": test_project["_id"],
        "dueDate": due_date,
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "subtasks": [],
        "attachments": [],
        "tags": ["test"],
        "metadata": {
            "completedAt": None,
            "timeEstimate": 60,  # 1 hour in minutes
            "timeSpent": 0
        }
    }
    
    # Insert task into database
    mongo_db.tasks.insert_one(task)
    
    return task


def create_test_task(mongo_db, title, description, status="not_started", priority="medium", 
                    creator=None, assignee=None, project=None, due_date=None):
    """
    Utility function to create customized test tasks.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        title (str): Task title
        description (str): Task description
        status (str): Task status
        priority (str): Task priority
        creator (dict): Creator user document
        assignee (dict): Assignee user document
        project (dict): Project document
        due_date (datetime.datetime): Due date for the task
        
    Returns:
        dict: Created task document
    """
    # Create task document with provided parameters
    task_id = str(uuid.uuid4())
    
    # Set default values for any missing parameters
    if creator is None:
        creator = {"_id": "default_creator_id"}
    
    if due_date is None:
        due_date = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    
    task = {
        "_id": task_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "createdBy": creator["_id"],
        "assigneeId": assignee["_id"] if assignee else None,
        "projectId": project["_id"] if project else None,
        "dueDate": due_date,
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "subtasks": [],
        "attachments": [],
        "tags": ["test"],
        "metadata": {
            "completedAt": None,
            "timeEstimate": 60,
            "timeSpent": 0
        }
    }
    
    # Insert task into database
    mongo_db.tasks.insert_one(task)
    
    return task


def create_test_project(mongo_db, name, description, owner, members=None, status="active"):
    """
    Utility function to create customized test projects.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        name (str): Project name
        description (str): Project description
        owner (dict): Owner user document
        members (list): List of project members
        status (str): Project status
        
    Returns:
        dict: Created project document
    """
    # Create project document with provided parameters
    project_id = str(uuid.uuid4())
    
    # Format members list with appropriate role information
    if members is None:
        members = [{"userId": owner["_id"], "role": "owner"}]
    
    project = {
        "_id": project_id,
        "name": name,
        "description": description,
        "status": status,
        "owner": owner["_id"],
        "members": members,
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "settings": {
            "workflow": {
                "enableReview": True,
                "allowSubtasks": True,
                "defaultTaskStatus": "not_started"
            },
            "permissions": {
                "memberInvite": "owner,admin",
                "taskCreate": "owner,admin,member",
                "commentCreate": "owner,admin,member,viewer"
            }
        },
        "tags": ["test"],
        "metadata": {
            "taskCount": 0,
            "completedTaskCount": 0
        }
    }
    
    # Insert project into database
    mongo_db.projects.insert_one(project)
    
    return project


def create_test_user(mongo_db, email, password, roles=None, first_name="Test", last_name="User"):
    """
    Utility function to create customized test users.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        email (str): User email
        password (str): User password
        roles (list): List of role IDs
        first_name (str): User's first name
        last_name (str): User's last name
        
    Returns:
        dict: Created user document
    """
    # Create user document with provided parameters
    user_id = str(uuid.uuid4())
    
    # Hash the provided password (simplified for testing)
    password_hash = f"$2b$12${uuid.uuid4().hex[:22]}"
    
    # Set default values for any missing parameters
    if roles is None:
        roles = ["role_user"]
    
    user = {
        "_id": user_id,
        "email": email,
        "password": password_hash,
        "firstName": first_name,
        "lastName": last_name,
        "roleIds": roles,
        "status": "active",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
        "settings": {
            "theme": "light",
            "notifications": {
                "email": True,
                "inApp": True
            }
        }
    }
    
    # Insert user into database
    mongo_db.users.insert_one(user)
    
    return user


@pytest.fixture
def test_notification(mongo_db, test_user):
    """
    Creates a test notification for testing notification functionality.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        test_user (dict): Test user document
        
    Returns:
        dict: Test notification document
    """
    # Create a notification document for test_user
    notification = {
        "_id": "test_notification_id",
        "userId": test_user["_id"],
        "type": "task_assigned",
        "title": "Task Assigned",
        "content": "You have been assigned a new task: Test Task",
        "read": False,
        "actionUrl": "/tasks/test_task_id",
        "createdAt": datetime.datetime.utcnow(),
        "metadata": {
            "taskId": "test_task_id"
        }
    }
    
    # Insert notification into database
    mongo_db.notifications.insert_one(notification)
    
    return notification


@pytest.fixture
def test_file(mongo_db, test_user):
    """
    Creates a test file attachment for testing file functionality.
    
    Args:
        mongo_db (mongomock.MongoClient): MongoDB client
        test_user (dict): Test user document
        
    Returns:
        dict: Test file document
    """
    # Create a file document with test filename and content type
    file = {
        "_id": "test_file_id",
        "name": "test_document.pdf",
        "size": 12345,
        "type": "application/pdf",
        "storageKey": "uploads/test_user_id/test_document.pdf",
        "uploadedBy": test_user["_id"],
        "uploadedAt": datetime.datetime.utcnow(),
        "metadata": {
            "md5Hash": "abcdef1234567890abcdef1234567890"
        },
        "tags": ["test", "document"]
    }
    
    # Insert file into database
    mongo_db.files.insert_one(file)
    
    return file