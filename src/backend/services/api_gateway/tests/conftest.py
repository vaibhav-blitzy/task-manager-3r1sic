import pytest  # pytest 7.4.x
import requests_mock  # requests-mock 1.10.x
import unittest.mock  # standard library
import json  # standard library

from src.backend.services.api_gateway.app import create_app  # src/backend/services/api_gateway/app.py
from src.backend.services.api_gateway.config import TestingConfig  # src/backend/services/api_gateway/config.py
from src.backend.common.auth.jwt_utils import validate_token  # src/backend/common/auth/jwt_utils.py
from src.backend.common.testing.fixtures import mongo_db, redis_cache  # src/backend/common/testing/fixtures.py

TEST_USER_ID = "test_user_123"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwibmFtZSI6IlRlc3QgVXNlciIsInJvbGVzIjpbInVzZXIiXSwiaWF0IjoxNTE2MjM5MDIyfQ.signature"
TEST_CONFIG = {
    "SERVICE_ROUTES": {
        "auth": "http://mock-auth-service",
        "task": "http://mock-task-service",
        "project": "http://mock-project-service",
        "notification": "http://mock-notification-service",
        "file": "http://mock-file-service",
        "analytics": "http://mock-analytics-service",
        "realtime": "http://mock-realtime-service"
    }
}

@pytest.fixture
def api_gateway_config():
    """Fixture that provides a test configuration for the API Gateway with mock service URLs"""
    # Create a TestingConfig instance with mock service URLs
    config = TestingConfig()
    # Ensure all backend services have mock URLs configured
    assert all(url for url in config.SERVICE_ROUTES.values())
    # Set testing mode to True
    config.TESTING = True
    # Return the configuration dictionary
    return config

@pytest.fixture
def gateway_app(api_gateway_config):
    """Fixture that creates a Flask test application instance for the API Gateway"""
    # Call create_app with the api_gateway_config
    app = create_app(test_config=api_gateway_config.to_dict())
    # Configure app for testing mode
    app.config['TESTING'] = True
    # Return the configured application instance
    return app

@pytest.fixture
def gateway_client(gateway_app):
    """Fixture that creates a Flask test client for making test requests to the API Gateway"""
    # Create a test client from the gateway_app
    client = gateway_app.test_client()
    # Configure the client to handle JSON requests and responses
    client.environ_base['CONTENT_TYPE'] = 'application/json'
    # Return the configured test client
    return client

@pytest.fixture
def authenticated_gateway_client(gateway_app, mock_validate_token):
    """Fixture that creates an authenticated Flask test client with JWT token"""
    # Create a test client from the gateway_app
    client = gateway_app.test_client()
    # Configure validate_token mock to return true and test user data
    mock_validate_token.return_value = {"user_id": TEST_USER_ID, "roles": ["user"]}
    # Add authentication headers to the client
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {TEST_TOKEN}'
    client.environ_base['CONTENT_TYPE'] = 'application/json'
    # Return the test client with authentication headers
    return client

@pytest.fixture
def mock_validate_token():
    """Fixture that mocks the JWT token validation function to always succeed in tests"""
    # Create a mock for the validate_token function
    mock = unittest.mock.Mock()
    # Configure the mock to return a valid user payload with TEST_USER_ID
    mock.return_value = {"user_id": TEST_USER_ID, "roles": ["user"]}
    # Return the configured mock
    return mock

@pytest.fixture
def mock_services(requests_mock, api_gateway_config):
    """Fixture that mocks requests to backend services for isolated testing"""
    # Set up requests_mocker to intercept HTTP requests
    base_url = api_gateway_config.SERVICE_ROUTES
    # Register default responses for common service endpoints
    requests_mock.get(f'{base_url["auth"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["task"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["project"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["notification"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["file"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["analytics"]}/health', json={'status': 'ok'}, status_code=200)
    requests_mock.get(f'{base_url["realtime"]}/health', json={'status': 'ok'}, status_code=200)
    # Configure health check responses for all services
    for service, url in base_url.items():
        requests_mock.get(f'{url}/health', json={'status': 'ok'}, status_code=200)
    # Return the configured mocker for further customization in tests
    return requests_mock

def mock_service_response(mocker, service_url, path, response_data, status_code=200, method='GET'):
    """Helper function to configure mock responses for specific service endpoints"""
    # Construct the full URL by combining service_url and path
    full_url = f"{service_url}{path}"
    # Register the mock response with the given status code and data
    if method == 'GET':
        mocker.get(full_url, json=response_data, status_code=status_code)
    elif method == 'POST':
        mocker.post(full_url, json=response_data, status_code=status_code)
    elif method == 'PUT':
        mocker.put(full_url, json=response_data, status_code=status_code)
    elif method == 'DELETE':
        mocker.delete(full_url, status_code=status_code)
    elif method == 'PATCH':
        mocker.patch(full_url, json=response_data, status_code=status_code)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    # Return the updated mocker instance
    return mocker

@pytest.fixture
def mock_db(mongo_db):
    """Fixture that provides a mock database for API Gateway tests"""
    # Configure mongo_db for API Gateway specific collections
    db = mongo_db
    # Create indexes required for API Gateway operation
    if "users" not in db.list_collection_names():
        db.create_collection("users")
    if "tasks" not in db.list_collection_names():
        db.create_collection("tasks")
    if "projects" not in db.list_collection_names():
        db.create_collection("projects")
    if "comments" not in db.list_collection_names():
        db.create_collection("comments")
    # Return the configured mongo_db instance
    return db

@pytest.fixture
def mock_redis_client(redis_cache):
    """Fixture that provides a mock Redis client for API Gateway tests"""
    # Configure redis_cache with API Gateway specific data
    client = redis_cache
    # Set up test data for rate limiting tests
    client.set('rate_limit:anonymous:ip:127.0.0.1', 0)
    client.set('rate_limit:authenticated:user:test_user', 0)
    # Mock health check responses
    client.ping = unittest.mock.MagicMock(return_value=True)
    # Return the configured redis_cache instance
    return client

@pytest.fixture
def test_request_context(gateway_app):
    """Fixture that provides a test request context for the API Gateway"""
    # Create a test request context with gateway_app
    with gateway_app.test_request_context() as ctx:
        # Configure the context with test headers and path
        ctx.request.headers['X-Request-ID'] = 'test-request-id'
        ctx.request.path = '/test-path'
        # Yield the context for test use
        yield ctx
        # Clean up the context after test completion
        ctx.close()