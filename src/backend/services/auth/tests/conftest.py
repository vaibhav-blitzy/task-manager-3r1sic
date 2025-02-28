# pytest v7.4.x
import pytest
# mongomock v4.1.x
import mongomock
# fakeredis v2.10.x
import fakeredis
# pytest-mock v3.10.x
from pytest_mock import MockFixture
# datetime standard library
import datetime
# bson v4.3.x
import bson

# Internal imports
from src.backend.services.auth.app import create_app
from src.backend.services.auth.models.user import User
from src.backend.services.auth.models.role import Role
from src.backend.common.database.mongo.connection import get_db
from src.backend.common.database.redis.connection import get_redis
from src.backend.common.auth.jwt_utils import generate_jwt_token
from src.backend.common.utils.security import generate_password_hash

# Global test constants
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "AdminSecurePass123!"

@pytest.fixture
def app():
    """Fixture that creates a Flask application configured for testing"""
    # Create test-specific configuration dictionary
    test_config = {
        'TESTING': True,
    }
    # Create Flask app using create_app factory with test config
    app = create_app(config_override=test_config)
    # Configure app for testing context
    with app.app_context():
        yield app # Provide the app instance when tests are run

@pytest.fixture
def client(app):
    """Fixture that creates a Flask test client"""
    # Get test client from Flask app
    return app.test_client()

@pytest.fixture
def mock_mongo_client():
    """Fixture that creates a mock MongoDB client"""
    # Create mongomock client instance
    mock_client = mongomock.MongoClient()
    # Return the mock client
    return mock_client

@pytest.fixture
def mock_db(mock_mongo_client, mocker: MockFixture):
    """Fixture that patches the database connection to use a mock database"""
    # Get mock database from mock_mongo_client
    mock_db = mock_mongo_client.db
    # Patch get_db function to return the mock database
    mocker.patch('src.backend.services.auth.app.get_db', return_value=mock_db)
    # Set up basic collections needed for tests
    mock_db.users.create_index('email', unique=True)
    mock_db.roles.create_index('name', unique=True)
    # Return the mock database instance
    return mock_db

@pytest.fixture
def mock_redis(mocker: MockFixture):
    """Fixture that patches the Redis connection to use a mock Redis instance"""
    # Create FakeStrictRedis instance
    fake_redis = fakeredis.FakeStrictRedis()
    # Patch get_redis function to return the mock Redis
    mocker.patch('src.backend.services.auth.app.get_redis', return_value=fake_redis)
    # Return the mock Redis instance
    return fake_redis

@pytest.fixture
def test_roles(mock_db):
    """Fixture that creates standard roles for testing"""
    # Define standard roles (user, manager, admin)
    roles = {
        'user': {'name': 'user', 'description': 'Standard user role'},
        'manager': {'name': 'manager', 'description': 'Project manager role'},
        'admin': {'name': 'admin', 'description': 'Administrator role'}
    }
    # Insert roles into mock database
    for role_data in roles.values():
        mock_db.roles.insert_one(role_data)
    # Return dictionary of created roles
    return roles

@pytest.fixture
def test_user(mock_db, test_roles):
    """Fixture that creates a standard test user"""
    # Generate user data with TEST_USER_EMAIL
    user_data = {
        'email': TEST_USER_EMAIL,
        'firstName': 'Test',
        'lastName': 'User'
    }
    # Hash the test password
    hashed_password = generate_password_hash(TEST_USER_PASSWORD)
    user_data['password_hash'] = hashed_password
    # Assign 'user' role from test_roles
    user_data['roles'] = [test_roles['user']['name']]
    # Insert user into mock database
    mock_db.users.insert_one(user_data)
    # Return the created user document
    return user_data

@pytest.fixture
def test_admin(mock_db, test_roles):
    """Fixture that creates an admin test user"""
    # Generate admin user data with TEST_ADMIN_EMAIL
    admin_data = {
        'email': TEST_ADMIN_EMAIL,
        'firstName': 'Admin',
        'lastName': 'User'
    }
    # Hash the admin password
    hashed_password = generate_password_hash(TEST_ADMIN_PASSWORD)
    admin_data['password_hash'] = hashed_password
    # Assign 'admin' role from test_roles
    admin_data['roles'] = [test_roles['admin']['name']]
    # Insert admin user into mock database
    mock_db.users.insert_one(admin_data)
    # Return the created admin user document
    return admin_data

@pytest.fixture
def test_user_tokens(test_user):
    """Fixture that generates authentication tokens for the test user"""
    # Extract user ID and roles from test_user
    user_id = str(test_user['_id'])
    user_roles = test_user['roles']
    # Generate access token with short expiry
    access_token = generate_jwt_token(user_id, user_roles, "access")
    # Generate refresh token with longer expiry
    refresh_token = generate_jwt_token(user_id, user_roles, "refresh")
    # Return dictionary with both tokens
    return {'access_token': access_token, 'refresh_token': refresh_token}

@pytest.fixture
def test_admin_tokens(test_admin):
    """Fixture that generates authentication tokens for the admin user"""
    # Extract user ID and roles from test_admin
    admin_id = str(test_admin['_id'])
    admin_roles = test_admin['roles']
    # Generate access token with short expiry
    access_token = generate_jwt_token(admin_id, admin_roles, "access")
    # Generate refresh token with longer expiry
    refresh_token = generate_jwt_token(admin_id, admin_roles, "refresh")
    # Return dictionary with both tokens
    return {'access_token': access_token, 'refresh_token': refresh_token}

@pytest.fixture
def authenticated_client(client, test_user_tokens):
    """Fixture that creates a Flask test client with authentication headers"""
    # Create Flask test client with client fixture
    # Add Authorization header with Bearer token
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + test_user_tokens['access_token']
    # Return authenticated test client
    return client

@pytest.fixture
def admin_client(client, test_admin_tokens):
    """Fixture that creates a Flask test client with admin authentication headers"""
    # Create Flask test client with client fixture
    # Add Authorization header with admin Bearer token
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + test_admin_tokens['access_token']
    # Return authenticated admin test client
    return client

@pytest.fixture
def auth_headers(test_user_tokens):
    """Fixture that returns authentication headers for API requests"""
    # Create headers dictionary
    headers = {}
    # Add Authorization header with Bearer token
    headers['Authorization'] = 'Bearer ' + test_user_tokens['access_token']
    # Return headers dictionary
    return headers

@pytest.fixture
def admin_headers(test_admin_tokens):
    """Fixture that returns admin authentication headers for API requests"""
    # Create headers dictionary
    headers = {}
    # Add Authorization header with admin Bearer token
    headers['Authorization'] = 'Bearer ' + test_admin_tokens['access_token']
    # Return headers dictionary
    return headers