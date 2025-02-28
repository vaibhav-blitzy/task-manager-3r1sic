"""
Error handlers for the Task Management System API.

This module registers Flask error handlers for the application's custom exception types.
It implements the error handling pattern defined in the technical specifications,
ensuring consistent error responses with appropriate status codes, logging, and details.
"""

import logging
import uuid
from flask import jsonify
import werkzeug.exceptions

from .api_exceptions import (
    APIException, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ConflictError, RateLimitError, ServerError,
    DependencyError, ServiceUnavailableError
)
from common.logging.logger import setup_logger

# Set up module logger
logger = logging.getLogger(__name__)

def handle_api_exception(error):
    """
    Generic handler for APIException and its subclasses.
    
    Args:
        error (APIException): The exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.error(f"API error: {error.error_code} - {error.message}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_validation_error(error):
    """
    Handler for ValidationError exceptions.
    
    Args:
        error (ValidationError): The validation exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.warning(f"Validation error: {error.message}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_authentication_error(error):
    """
    Handler for AuthenticationError exceptions.
    
    Args:
        error (AuthenticationError): The authentication exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.warning(f"Authentication failure: {error.message}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_authorization_error(error):
    """
    Handler for AuthorizationError exceptions.
    
    Args:
        error (AuthorizationError): The authorization exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    permission = error.required_permission or "unknown"
    logger.warning(f"Authorization error: {error.message} - Required permission: {permission}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_not_found_error(error):
    """
    Handler for NotFoundError exceptions.
    
    Args:
        error (NotFoundError): The not found exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    resource_type = error.resource_type or "unknown"
    resource_id = error.resource_id or "unknown"
    logger.info(f"Resource not found: {resource_type} - {resource_id}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_conflict_error(error):
    """
    Handler for ConflictError exceptions.
    
    Args:
        error (ConflictError): The conflict exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    resource_type = error.resource_type or "unknown"
    resource_id = error.resource_id or "unknown"
    logger.warning(f"Resource conflict: {resource_type} - {resource_id} - {error.message}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_rate_limit_error(error):
    """
    Handler for RateLimitError exceptions.
    
    Args:
        error (RateLimitError): The rate limit exception instance
        
    Returns:
        tuple: JSON response and HTTP status code with Retry-After header
    """
    logger.warning(f"Rate limit exceeded: {error.message}")
    error_dict = error.to_dict()
    headers = {'Retry-After': str(error.retry_after)} if error.retry_after else {}
    return jsonify(error_dict), error.status_code, headers

def handle_server_error(error):
    """
    Handler for ServerError exceptions.
    
    Args:
        error (ServerError): The server error exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    reference_id = error.reference_id or str(uuid.uuid4())
    logger.error(f"Server error: {error.message} - Reference ID: {reference_id}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_dependency_error(error):
    """
    Handler for DependencyError exceptions.
    
    Args:
        error (DependencyError): The dependency error exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    dependency = error.dependency or "unknown"
    logger.error(f"Dependency failure: {dependency} - {error.message} - Retryable: {error.retryable}")
    error_dict = error.to_dict()
    return jsonify(error_dict), error.status_code

def handle_service_unavailable_error(error):
    """
    Handler for ServiceUnavailableError exceptions.
    
    Args:
        error (ServiceUnavailableError): The service unavailable exception instance
        
    Returns:
        tuple: JSON response and HTTP status code with Retry-After header
    """
    reason = error.reason or "unknown"
    logger.error(f"Service unavailable: {reason} - {error.message}")
    error_dict = error.to_dict()
    headers = {'Retry-After': str(error.retry_after)} if error.retry_after else {}
    return jsonify(error_dict), error.status_code, headers

def handle_404_error(error):
    """
    Handler for Flask 404 (Not Found) errors.
    
    Args:
        error (werkzeug.exceptions.NotFound): The not found exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.info(f"404 error: {error.description}")
    error_response = {
        "status": 404,
        "code": "not_found",
        "message": "The requested resource was not found"
    }
    return jsonify(error_response), 404

def handle_405_error(error):
    """
    Handler for Flask 405 (Method Not Allowed) errors.
    
    Args:
        error (werkzeug.exceptions.MethodNotAllowed): The method not allowed exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    logger.info(f"405 error: {error.description}")
    error_response = {
        "status": 405,
        "code": "method_not_allowed",
        "message": "The method is not allowed for the requested resource"
    }
    return jsonify(error_response), 405

def handle_unhandled_exception(error):
    """
    Fallback handler for any unhandled exceptions.
    
    Args:
        error (Exception): The unhandled exception instance
        
    Returns:
        tuple: JSON response and HTTP status code
    """
    reference_id = str(uuid.uuid4())
    logger.critical(
        f"Unhandled exception: {str(error)} - Reference ID: {reference_id}",
        exc_info=True
    )
    error_response = {
        "status": 500,
        "code": "server_error",
        "message": "An unexpected error occurred",
        "details": {
            "reference_id": reference_id
        }
    }
    return jsonify(error_response), 500

def register_error_handlers(app):
    """
    Register all error handlers with the Flask application.
    
    Args:
        app (flask.Flask): The Flask application instance
        
    Returns:
        None
    """
    # Register handlers for custom exception types
    app.register_error_handler(APIException, handle_api_exception)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(AuthenticationError, handle_authentication_error)
    app.register_error_handler(AuthorizationError, handle_authorization_error)
    app.register_error_handler(NotFoundError, handle_not_found_error)
    app.register_error_handler(ConflictError, handle_conflict_error)
    app.register_error_handler(RateLimitError, handle_rate_limit_error)
    app.register_error_handler(ServerError, handle_server_error)
    app.register_error_handler(DependencyError, handle_dependency_error)
    app.register_error_handler(ServiceUnavailableError, handle_service_unavailable_error)
    
    # Register handlers for standard HTTP errors
    app.register_error_handler(werkzeug.exceptions.NotFound, handle_404_error)
    app.register_error_handler(werkzeug.exceptions.MethodNotAllowed, handle_405_error)
    
    # Register fallback handler for unhandled exceptions
    app.register_error_handler(Exception, handle_unhandled_exception)
    
    logger.info("Registered error handlers for Flask application")