"""
Provides reusable pytest fixtures for testing backend services of the Task Management System.

These fixtures help set up consistent test environments, mock dependencies, and create test data
for various test scenarios. They can be used in both unit tests and integration tests.
"""

# Standard library imports
import os
import uuid
import datetime
from typing import Dict, List, Any, Optional, Union

# Third-party imports
import pytest
import mongomock
import fakeredis
from flask import Flask

# Internal imports
from ..database.mongo.connection import MongoClient
from ..database.redis.connection import RedisClient
from .mocks import mock_mongo_client, mock_redis_client
from ..config.testing import TestingConfig
from ..utils.security import generate_password_hash
from ..auth.jwt_utils import generate_access_token

# Fixtures for application setup

@pytest.fixture
def app():
    """
    Creates a Flask test application instance for testing API endpoints.
    
    Returns:
        Flask: Flask application instance configured for testing
    """
    # Create Flask app instance
    app = Flask("test_app")
    
    # Configure with testing config
    app.config.from_object(TestingConfig())
    
    # Set testing flag
    app.testing = True
    
    return app

@pytest.fixture
def client(app):
    """
    Creates a Flask test client for making test requests to API endpoints.
    
    Args:
        app: Flask application fixture
        
    Returns:
        FlaskClient: Flask test client for making requests
    """
    return app.test_client()

# Fixtures for database mocking

@pytest.fixture
def mongo_db():
    """
    Creates a mock MongoDB connection for testing database operations.
    
    Returns:
        mongomock.MongoClient: Mock MongoDB client instance
    """
    # Check if we should use a real database for testing
    use_real_db = os.environ.get('TESTING_USE_REAL_DB', 'false').lower() == 'true'
    
    if use_real_db:
        # Use a real MongoDB but with a test database
        import pymongo
        test_db_name = f"test_db_{uuid.uuid4().hex[:8]}"
        mongo_uri = os.environ.get('TEST_MONGO_URI', f"mongodb://localhost:27017/{test_db_name}")
        mongo_client = pymongo.MongoClient(mongo_uri)
        
        # Use the test database
        db = mongo_client[test_db_name]
        
        yield mongo_client
        
        # Clean up - drop the test database after tests
        mongo_client.drop_database(test_db_name)
    else:
        # Use mongomock for isolated tests
        mongo_client = mock_mongo_client()
        yield mongo_client

@pytest.fixture
def redis_cache():
    """
    Creates a mock Redis connection for testing caching and real-time features.
    
    Returns:
        fakeredis.FakeStrictRedis: Mock Redis client instance
    """
    # Check if we should use a real Redis for testing
    use_real_redis = os.environ.get('TESTING_USE_REAL_REDIS', 'false').lower() == 'true'
    
    if use_real_redis:
        # Use a real Redis but with a test database
        import redis
        redis_client = redis.Redis(
            host=os.environ.get('TEST_REDIS_HOST', 'localhost'),
            port=int(os.environ.get('TEST_REDIS_PORT', '6379')),
            db=int(os.environ.get('TEST_REDIS_DB', '15')),  # Use DB 15 for tests
            password=os.environ.get('TEST_REDIS_PASSWORD', '')
        )
        
        yield redis_client
        
        # Clean up - flush the test database after tests
        redis_client.flushdb()
    else:
        # Use fakeredis for isolated tests
        redis_client = mock_redis_client()
        yield redis_client

# Fixtures for authentication

@pytest.fixture
def auth_headers(user_data=None):
    """
    Creates authentication headers with JWT tokens for authenticated API testing.
    
    Args:
        user_data: Optional user data for token payload
        
    Returns:
        dict: Headers containing Authorization with JWT token
    """
    if user_data is None:
        # Use default test user data
        user_data = {
            "user_id": "test_user_id", 
            "email": "test@example.com",
            "role": "user"
        }
    
    # Generate a test JWT token
    token = generate_access_token(user_data)
    
    # Create headers dictionary with token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    return headers

# Fixtures for test data

@pytest.fixture
def test_user(mongo_db):
    """
    Creates a test user document for authentication and user-related tests.
    
    Args:
        mongo_db: MongoDB fixture
        
    Returns:
        dict: Test user document with all required fields
    """
    user = create_test_user(
        email="test@example.com",
        password="Test@123",
        roles=["user"]
    )
    
    # Insert user into database if we're not using mongomock
    if not isinstance(mongo_db, mongomock.MongoClient):
        mongo_db.users.insert_one(user)
    
    return user

@pytest.fixture
def test_admin_user(mongo_db):
    """
    Creates a test admin user document for admin-specific tests.
    
    Args:
        mongo_db: MongoDB fixture
        
    Returns:
        dict: Test admin user document with admin role
    """
    admin_user = create_test_user(
        email="admin@example.com",
        password="Admin@123",
        roles=["admin"]
    )
    
    # Insert admin user into database
    mongo_db.users.insert_one(admin_user)
    
    return admin_user

@pytest.fixture
def test_task(mongo_db, test_user):
    """
    Creates a test task document for task-related tests.
    
    Args:
        mongo_db: MongoDB fixture
        test_user: Test user fixture
        
    Returns:
        dict: Test task document with all required fields
    """
    task = create_test_task(
        title="Test Task",
        description="This is a test task for testing purposes",
        creator_id=test_user["_id"],
        assignee_id=test_user["_id"],
        status="in_progress",
        priority="medium"
    )
    
    # Insert task into database
    mongo_db.tasks.insert_one(task)
    
    return task

@pytest.fixture
def test_project(mongo_db, test_user):
    """
    Creates a test project document for project-related tests.
    
    Args:
        mongo_db: MongoDB fixture
        test_user: Test user fixture
        
    Returns:
        dict: Test project document with all required fields
    """
    project = create_test_project(
        name="Test Project",
        description="This is a test project for testing purposes",
        owner_id=test_user["_id"],
        members=[
            {"user_id": test_user["_id"], "role": "owner"}
        ],
        status="active"
    )
    
    # Insert project into database
    mongo_db.projects.insert_one(project)
    
    return project

@pytest.fixture
def test_comment(mongo_db, test_user, test_task):
    """
    Creates a test comment document for comment-related tests.
    
    Args:
        mongo_db: MongoDB fixture
        test_user: Test user fixture
        test_task: Test task fixture
        
    Returns:
        dict: Test comment document with all required fields
    """
    comment = create_test_comment(
        content="This is a test comment",
        user_id=test_user["_id"],
        task_id=test_task["_id"]
    )
    
    # Insert comment into database
    mongo_db.comments.insert_one(comment)
    
    return comment

# Utility functions for creating test data

def create_test_user(email, password, roles):
    """
    Utility function to create a test user with specified parameters.
    
    Args:
        email: User email address
        password: Plain text password (will be hashed)
        roles: List of role identifiers
        
    Returns:
        dict: User document with provided parameters
    """
    user_id = str(uuid.uuid4())
    
    # Hash the password for secure storage
    hashed_password = generate_password_hash(password)
    
    return {
        "_id": user_id,
        "email": email,
        "password": hashed_password,
        "firstName": "Test",
        "lastName": "User",
        "roles": roles,
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

def create_test_task(title, description, creator_id, assignee_id=None, status="not_started", priority="medium"):
    """
    Utility function to create a test task with specified parameters.
    
    Args:
        title: Task title
        description: Task description
        creator_id: ID of the user creating the task
        assignee_id: ID of the user assigned to the task (optional)
        status: Task status (default: "not_started")
        priority: Task priority (default: "medium")
        
    Returns:
        dict: Task document with provided parameters
    """
    task_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    due_date = now + datetime.timedelta(days=7)  # Default due date 1 week in the future
    
    return {
        "_id": task_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "createdBy": creator_id,
        "assigneeId": assignee_id,
        "dueDate": due_date,
        "createdAt": now,
        "updatedAt": now,
        "subtasks": [],
        "attachments": [],
        "tags": ["test"],
        "metadata": {
            "completedAt": None,
            "timeEstimate": 60,  # 1 hour in minutes
            "timeSpent": 0
        }
    }

def create_test_project(name, description, owner_id, members=None, status="active"):
    """
    Utility function to create a test project with specified parameters.
    
    Args:
        name: Project name
        description: Project description
        owner_id: ID of the project owner
        members: List of project members (optional)
        status: Project status (default: "active")
        
    Returns:
        dict: Project document with provided parameters
    """
    project_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    
    # If members not provided, default to just the owner
    if members is None:
        members = [
            {"user_id": owner_id, "role": "owner"}
        ]
    
    return {
        "_id": project_id,
        "name": name,
        "description": description,
        "status": status,
        "owner": owner_id,
        "members": members,
        "createdAt": now,
        "updatedAt": now,
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
            "completedAt": None,
            "taskCount": 0,
            "completedTaskCount": 0
        }
    }

def create_test_comment(content, user_id, task_id):
    """
    Utility function to create a test comment with specified parameters.
    
    Args:
        content: Comment text content
        user_id: ID of the user creating the comment
        task_id: ID of the task the comment belongs to
        
    Returns:
        dict: Comment document with provided parameters
    """
    comment_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    
    return {
        "_id": comment_id,
        "content": content,
        "userId": user_id,
        "taskId": task_id,
        "createdAt": now,
        "updatedAt": now,
        "mentions": [],
        "attachments": []
    }