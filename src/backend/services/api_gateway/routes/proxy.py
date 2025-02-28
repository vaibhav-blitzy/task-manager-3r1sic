"""
Proxy module for the API Gateway service.

This module implements the core proxy functionality for API Gateway, handling request routing
to appropriate backend microservices, authentication validation, request/response transformation,
and circuit breaker patterns for resiliency.
"""

from flask import Blueprint, request, Response, jsonify, current_app
import requests
import time
from pybreaker import CircuitBreaker  # pybreaker 1.0.x

from ..config import get_service_url, is_auth_required
from src.backend.common.auth.jwt_utils import validate_access_token, extract_token_from_header
from src.backend.common.exceptions.api_exceptions import ServiceUnavailableError, DependencyError, AuthenticationError
from src.backend.common.logging.logger import logger

# Create a blueprint for the proxy routes
proxy_bp = Blueprint('proxy', __name__)

# Request timeout (in seconds)
REQUEST_TIMEOUT = 5.0

# Configure circuit breaker
circuit_breaker = CircuitBreaker(
    fail_max=5,           # Number of failures before opening the circuit
    reset_timeout=30,     # Seconds until trying to close the circuit
    exclude=[requests.exceptions.ConnectionError]  # Don't count connection errors
)


@circuit_breaker
def forward_request(service_url, path, headers):
    """
    Forwards the request to the appropriate backend service and returns the response.
    
    Args:
        service_url (str): URL of the target service
        path (str): Request path
        headers (dict): Headers to forward
    
    Returns:
        Response: Flask Response object containing the proxied service response
    
    Raises:
        ServiceUnavailableError: If the target service is unavailable
        DependencyError: If the target service returns an error
    """
    try:
        # Create a session for connection pooling
        session = requests.Session()
        
        # Forward the request method and any request data
        method = request.method
        data = request.data if request.data else None
        params = request.args.to_dict()
        json_data = request.get_json(silent=True)
        
        # Record start time for request duration measurement
        start_time = time.time()
        
        # Forward the request to the target service
        target_url = f"{service_url}/{path.lstrip('/')}"
        response = session.request(
            method=method,
            url=target_url,
            headers=headers,
            data=data,
            params=params,
            json=json_data,
            timeout=REQUEST_TIMEOUT
        )
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the request details
        logger.info(
            f"Proxied {method} {path} to {service_url} - Status: {response.status_code}, "
            f"Duration: {duration:.3f}s"
        )
        
        # Create a response object with the service response
        proxy_response = Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
        return proxy_response
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error connecting to {service_url}/{path}")
        raise ServiceUnavailableError(
            message="Service timed out",
            retry_after=30
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {service_url}/{path}")
        raise ServiceUnavailableError(
            message="Service is currently unavailable",
            retry_after=60
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error to {service_url}/{path}: {str(e)}")
        raise DependencyError(
            message=f"Error communicating with service: {str(e)}",
            dependency=service_url,
            retryable=True
        )
    except Exception as e:
        logger.error(f"Unexpected error forwarding request to {service_url}/{path}: {str(e)}")
        raise ServiceUnavailableError(
            message="Internal server error",
            reason=str(e)
        )


def preprocess_request(headers, path):
    """
    Prepares the request for forwarding by processing headers and authentication.
    
    Args:
        headers (dict): Original request headers
        path (str): Request path
    
    Returns:
        dict: Processed headers dictionary for the forwarded request
    
    Raises:
        AuthenticationError: If authentication fails
    """
    # Create a copy of headers to avoid modifying the original
    processed_headers = dict(headers)
    
    # Remove headers that shouldn't be forwarded
    headers_to_remove = ['Host', 'Content-Length']
    for header in headers_to_remove:
        if header in processed_headers:
            del processed_headers[header]
    
    # Check if the path requires authentication
    if is_auth_required(path):
        # Get the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError("Authentication required")
        
        # Extract and validate the token
        token = extract_token_from_header(auth_header)
        if not token:
            raise AuthenticationError("Invalid authorization format")
        
        # Validate the token
        try:
            token_data = validate_access_token(token)
            
            # Add user information to headers for the backend service
            processed_headers['X-User-ID'] = token_data.get('user_id', '')
            processed_headers['X-User-Roles'] = ','.join(token_data.get('roles', []))
        except AuthenticationError as e:
            logger.warning(f"Authentication failed for path {path}: {str(e)}")
            raise
    
    # Add proxy-specific headers
    client_ip = request.remote_addr
    processed_headers['X-Forwarded-For'] = client_ip
    processed_headers['X-Forwarded-Host'] = request.host
    processed_headers['X-Forwarded-Proto'] = request.scheme
    
    # Add or forward correlation ID for request tracing
    correlation_id = request.headers.get('X-Correlation-ID') or request.headers.get('X-Request-ID')
    if correlation_id:
        processed_headers['X-Correlation-ID'] = correlation_id
    
    return processed_headers


def determine_target_service(path):
    """
    Determines which backend service should handle the request based on the path.
    
    Args:
        path (str): Request path
    
    Returns:
        str: URL of the target service
    
    Raises:
        ValueError: If no matching service is found
    """
    # Extract service identifier from path (e.g., /auth/, /tasks/)
    parts = path.strip('/').split('/')
    
    # If no parts, default to auth service
    if not parts or not parts[0]:
        service_name = 'auth'
    else:
        # First part of the path is likely the service name
        service_name = parts[0]
    
    # Get the service URL from configuration
    try:
        service_url = get_service_url(service_name)
        return service_url
    except ValueError:
        # If not found, try removing 'api' prefix if present
        if service_name == 'api' and len(parts) > 1:
            service_name = parts[1]
            try:
                service_url = get_service_url(service_name)
                return service_url
            except ValueError as e:
                logger.error(f"Service not found for path {path}: {str(e)}")
                raise
        else:
            logger.error(f"Service not found for path {path}")
            raise ValueError(f"Unable to determine service for path: {path}")


def construct_target_url(service_url, path):
    """
    Builds the complete target URL for the proxied request.
    
    Args:
        service_url (str): Base URL of the target service
        path (str): Request path
    
    Returns:
        str: Complete URL for the proxied request
    """
    # Strip any API prefix that shouldn't be forwarded to the backend service
    if path.startswith('api/'):
        path = path[4:]  # Remove 'api/'
    
    # Ensure we don't have double slashes
    path = path.lstrip('/')
    service_url = service_url.rstrip('/')
    
    # Combine the service URL with the path
    return f"{service_url}/{path}" if path else service_url


@proxy_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy_request(path):
    """
    Main request handler that proxies all API requests to backend services.
    
    Args:
        path (str): Request path
    
    Returns:
        Response: Response from the backend service or error response
    """
    logger.info(f"Received {request.method} request for /{path}")
    
    # Handle preflight OPTIONS requests specially
    preflight_response = handle_preflight(path)
    if preflight_response:
        return preflight_response
    
    try:
        # Determine the target service
        service_url = determine_target_service(path)
        
        # Process request headers and check authentication
        headers = preprocess_request(request.headers, path)
        
        # Construct the target URL
        target_url = construct_target_url(service_url, path)
        
        # Forward the request to the target service
        response = forward_request(service_url, path, headers)
        
        return response
    
    except AuthenticationError as e:
        logger.warning(f"Authentication error: {str(e)}")
        return jsonify({"error": "Authentication failed", "message": str(e)}), 401
    
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {str(e)}")
        response = jsonify({"error": "Service unavailable", "message": str(e.message)})
        if hasattr(e, 'retry_after') and e.retry_after:
            response.headers['Retry-After'] = str(e.retry_after)
        return response, 503
    
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        return jsonify({"error": "Bad request", "message": str(e)}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in proxy_request: {str(e)}")
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500


def handle_preflight(path):
    """
    Special handler for CORS preflight OPTIONS requests.
    
    Args:
        path (str): Request path
    
    Returns:
        Response: Response with CORS headers for preflight requests or None
    """
    if request.method == 'OPTIONS':
        # Create response
        response = Response('')
        
        # Add CORS headers based on configuration
        cors_settings = current_app.config.get('CORS_SETTINGS', {})
        
        # Set allowed origins
        origins = cors_settings.get('origins', ['*'])
        if origins and len(origins) > 0:
            response.headers['Access-Control-Allow-Origin'] = origins[0] if len(origins) == 1 else '*'
        
        # Set allowed methods
        methods = cors_settings.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
        response.headers['Access-Control-Allow-Methods'] = ', '.join(methods)
        
        # Set allowed headers
        allowed_headers = cors_settings.get('allow_headers', ['Content-Type', 'Authorization'])
        response.headers['Access-Control-Allow-Headers'] = ', '.join(allowed_headers)
        
        # Set expose headers
        expose_headers = cors_settings.get('expose_headers', [])
        if expose_headers:
            response.headers['Access-Control-Expose-Headers'] = ', '.join(expose_headers)
        
        # Set max age
        max_age = cors_settings.get('max_age', 600)
        response.headers['Access-Control-Max-Age'] = str(max_age)
        
        # Set allow credentials
        if cors_settings.get('supports_credentials', False):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Return the preflight response
        return response
    
    return None