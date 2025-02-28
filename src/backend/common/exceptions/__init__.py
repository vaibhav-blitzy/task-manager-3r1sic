"""
Exception handling for the Task Management System.

This package provides a centralized error handling system with standardized exception classes
and Flask error handlers. It ensures consistent error responses with appropriate status codes,
detailed error messages, and structured error payloads across the entire application.
"""

# Import exception classes from api_exceptions
from .api_exceptions import (
    APIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    DependencyError
)

# Import error handler registration function
from .error_handlers import register_error_handlers

# Export all exception classes and the registration function
__all__ = [
    # Base exception
    'APIException',
    
    # Client error exceptions (4xx)
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    
    # Server error exceptions (5xx)
    'ServerError',
    'ServiceUnavailableError',
    'DependencyError',
    
    # Error handler registration
    'register_error_handlers',
]