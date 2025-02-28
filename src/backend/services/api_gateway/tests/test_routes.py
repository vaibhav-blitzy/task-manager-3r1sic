"""
Unit tests for the API Gateway routes.

This module tests the API Gateway's routing, health checks, authentication,
and error handling capabilities to ensure requests are properly proxied
to downstream services and that appropriate responses are returned.
"""

import pytest
import json
import requests
from unittest.mock import patch, MagicMock, Mock

from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_request():
    """Create a mock for the requests.request function."""
    return MagicMock()


@pytest.fixture
def expired_token():
    """Create an expired JWT token for testing authentication."""
    # This would normally be a real but expired token
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjF9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


def test_health_endpoint(client):
    """Tests that the health check endpoint returns proper status and format."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'version' in data


def test_health_liveness_endpoint(client):
    """Tests that the liveness health check endpoint returns proper status."""
    response = client.get('/health/liveness')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'alive'


@patch('requests.request')
def test_health_readiness_endpoint(client, mock_request):
    """Tests that the readiness health check endpoint returns proper status and checks dependencies."""
    # Mock successful responses from all downstream services
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"status": "ok"}).encode()
    mock_request.return_value = mock_response
    
    response = client.get('/health/readiness')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ready'
    assert 'databases' in data
    assert 'mongodb' in data['databases']
    assert 'redis' in data['databases']


@patch('requests.request')
def test_auth_service_proxy(client, mock_request):
    """Tests that requests to auth service endpoints are properly proxied."""
    # Mock response from the auth service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"message": "Login successful"}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a login request that should be proxied to the auth service
    response = client.post('/api/v1/auth/login', json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'POST'
    assert 'auth' in call_args['url']
    assert 'login' in call_args['url']
    
    # Verify response from API gateway matches the mocked auth service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Login successful'


@patch('requests.request')
def test_task_service_proxy(client, mock_request):
    """Tests that requests to task service endpoints are properly proxied."""
    # Mock response from the task service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"tasks": []}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a task request that should be proxied to the task service
    response = client.get('/api/v1/tasks')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'task' in call_args['url']
    
    # Verify response from API gateway matches the mocked task service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tasks' in data


@patch('requests.request')
def test_project_service_proxy(client, mock_request):
    """Tests that requests to project service endpoints are properly proxied."""
    # Mock response from the project service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"projects": []}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a project request that should be proxied to the project service
    response = client.get('/api/v1/projects')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'project' in call_args['url']
    
    # Verify response from API gateway matches the mocked project service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'projects' in data


@patch('requests.request')
def test_notification_service_proxy(client, mock_request):
    """Tests that requests to notification service endpoints are properly proxied."""
    # Mock response from the notification service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"notifications": []}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a notification request that should be proxied to the notification service
    response = client.get('/api/v1/notifications')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'notification' in call_args['url']
    
    # Verify response from API gateway matches the mocked notification service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'notifications' in data


@patch('requests.request')
def test_file_service_proxy(client, mock_request):
    """Tests that requests to file service endpoints are properly proxied."""
    # Mock response from the file service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"files": []}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a file request that should be proxied to the file service
    response = client.get('/api/v1/files')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'file' in call_args['url']
    
    # Verify response from API gateway matches the mocked file service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'files' in data


@patch('requests.request')
def test_analytics_service_proxy(client, mock_request):
    """Tests that requests to analytics service endpoints are properly proxied."""
    # Mock response from the analytics service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"metrics": {}}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send an analytics request that should be proxied to the analytics service
    response = client.get('/api/v1/analytics/metrics')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'analytics' in call_args['url']
    
    # Verify response from API gateway matches the mocked analytics service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'metrics' in data


@patch('requests.request')
def test_realtime_service_proxy(client, mock_request):
    """Tests that requests to realtime service endpoints are properly proxied."""
    # Mock response from the realtime service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"status": "online"}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Send a realtime request that should be proxied to the realtime service
    response = client.get('/api/v1/realtime/status')
    
    # Verify request was properly proxied
    mock_request.assert_called_once()
    call_args = mock_request.call_args[1]
    assert call_args['method'] == 'GET'
    assert 'realtime' in call_args['url']
    
    # Verify response from API gateway matches the mocked realtime service response
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'online'


def test_nonexistent_endpoint(client):
    """Tests that requests to non-existent endpoints return 404."""
    response = client.get('/api/v1/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'not_found' in data['code'].lower()


@patch('requests.request', side_effect=requests.ConnectionError('Connection failed'))
def test_service_unavailable(client, mock_request):
    """Tests that gateway properly handles downstream service unavailability."""
    response = client.get('/api/v1/tasks')
    assert response.status_code == 503  # Service Unavailable
    data = json.loads(response.data)
    assert 'error' in data
    assert 'service unavailable' in data['message'].lower()


@patch('requests.request', side_effect=requests.Timeout('Request timed out'))
def test_request_timeout(client, mock_request):
    """Tests that gateway properly handles downstream service timeout."""
    response = client.get('/api/v1/tasks')
    assert response.status_code == 504  # Gateway Timeout
    data = json.loads(response.data)
    assert 'error' in data
    assert 'timeout' in data['message'].lower()


def test_jwt_authentication_missing_token(client):
    """Tests that protected endpoints reject requests without authentication token."""
    # Attempt to access a protected endpoint without authentication
    response = client.get('/api/v1/tasks')
    assert response.status_code == 401  # Unauthorized
    data = json.loads(response.data)
    assert 'error' in data
    assert 'authentication' in data['message'].lower()


def test_jwt_authentication_invalid_token(client):
    """Tests that protected endpoints reject requests with invalid JWT token."""
    # Attempt to access a protected endpoint with an invalid token
    response = client.get('/api/v1/tasks', headers={
        'Authorization': 'Bearer invalid.token.value'
    })
    assert response.status_code == 401  # Unauthorized
    data = json.loads(response.data)
    assert 'error' in data
    assert 'invalid' in data['message'].lower()


def test_jwt_authentication_expired_token(client, expired_token):
    """Tests that protected endpoints reject requests with expired JWT token."""
    # Attempt to access a protected endpoint with an expired token
    response = client.get('/api/v1/tasks', headers={
        'Authorization': f'Bearer {expired_token}'
    })
    assert response.status_code == 401  # Unauthorized
    data = json.loads(response.data)
    assert 'error' in data
    assert 'expired' in data['message'].lower()


def test_rate_limiting(client):
    """Tests that rate limiting middleware properly restricts excessive requests."""
    # Make multiple requests to trigger rate limiting
    for _ in range(31):  # Assuming anonymous limit is 30/minute
        response = client.get('/api/v1/auth/login')
    
    # The last request should be rate limited
    assert response.status_code == 429  # Too Many Requests
    
    # Check for rate limit headers
    assert 'X-RateLimit-Limit' in response.headers
    assert 'X-RateLimit-Remaining' in response.headers
    assert 'X-RateLimit-Reset' in response.headers
    assert 'Retry-After' in response.headers
    
    # Check response body
    data = json.loads(response.data)
    assert 'error' in data
    assert 'rate limit' in data['message'].lower()


@patch('requests.request')
def test_headers_forwarding(client, mock_request):
    """Tests that request headers are properly forwarded to downstream services."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"data": "test"}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Make request with custom headers
    custom_headers = {
        'Authorization': 'Bearer test-token',
        'X-Request-ID': 'test-request-id',
        'X-Custom-Header': 'test-value'
    }
    
    client.get('/api/v1/tasks', headers=custom_headers)
    
    # Verify headers were forwarded
    call_args = mock_request.call_args[1]
    assert 'headers' in call_args
    forwarded_headers = call_args['headers']
    
    assert forwarded_headers.get('Authorization') == 'Bearer test-token'
    assert forwarded_headers.get('X-Request-ID') == 'test-request-id'
    assert forwarded_headers.get('X-Custom-Header') == 'test-value'
    assert 'X-Forwarded-For' in forwarded_headers


@patch('requests.request')
def test_response_formatting(client, mock_request):
    """Tests that responses from downstream services are properly formatted."""
    # Setup mock response with specific headers
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"data": "test"}).encode()
    mock_response.headers = {
        'Content-Type': 'application/json',
        'X-Custom-Header': 'test-value',
        'X-Total-Count': '10'
    }
    mock_request.return_value = mock_response
    
    # Make request
    response = client.get('/api/v1/tasks')
    
    # Verify response status and content
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['data'] == 'test'
    
    # Verify headers were preserved
    assert response.headers.get('Content-Type') == 'application/json'
    assert response.headers.get('X-Custom-Header') == 'test-value'
    assert response.headers.get('X-Total-Count') == '10'


@patch('requests.request')
def test_request_id_propagation(client, mock_request):
    """Tests that request IDs are properly generated and propagated to downstream services."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = json.dumps({"status": "ok"}).encode()
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_request.return_value = mock_response
    
    # Make request without X-Request-ID header
    response = client.get('/api/v1/tasks')
    
    # Verify that API gateway adds X-Request-ID header to response
    assert 'X-Correlation-ID' in response.headers or 'X-Request-ID' in response.headers
    
    # Verify this header was forwarded to the downstream service
    call_args = mock_request.call_args[1]
    forwarded_headers = call_args['headers']
    assert 'X-Correlation-ID' in forwarded_headers or 'X-Request-ID' in forwarded_headers
    
    # Make a request with existing X-Request-ID header
    existing_request_id = 'existing-request-id'
    response = client.get('/api/v1/tasks', headers={'X-Request-ID': existing_request_id})
    
    # Verify that API gateway preserves this header
    call_args = mock_request.call_args[1]
    forwarded_headers = call_args['headers']
    assert forwarded_headers.get('X-Request-ID') == existing_request_id or forwarded_headers.get('X-Correlation-ID') == existing_request_id


def test_cors_headers(client):
    """Tests that CORS headers are properly set in responses."""
    # Make a request with Origin header to test CORS
    response = client.get('/api/v1/auth/login', headers={
        'Origin': 'http://localhost:3000'
    })
    
    # Verify CORS headers are present
    assert 'Access-Control-Allow-Origin' in response.headers
    
    # Make a preflight OPTIONS request
    response = client.options('/api/v1/tasks', headers={
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
    })
    
    # Verify preflight response headers
    assert response.status_code == 200
    assert 'Access-Control-Allow-Origin' in response.headers
    assert 'Access-Control-Allow-Methods' in response.headers
    assert 'Access-Control-Allow-Headers' in response.headers
    
    # Verify allowed methods include our request method
    allowed_methods = response.headers['Access-Control-Allow-Methods']
    assert 'GET' in allowed_methods