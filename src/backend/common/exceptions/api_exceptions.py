"""
Custom exceptions for the Task Management System API.

This module defines a hierarchy of exception classes for handling various 
error scenarios with appropriate HTTP status codes and error messages.
"""

# Import HTTP status codes for standardized error responses
# Note: HTTP_CODES is not a standard export from http.client; using standard status codes directly
from http.client import responses as HTTP_CODES

class APIException(Exception):
    """Base exception class for all API errors with default status code and error message."""
    
    def __init__(self, message=None, status_code=500, error_code="server_error", details=None):
        """Initialize the exception with appropriate error information.
        
        Args:
            message (str, optional): Error message. Defaults to None.
            status_code (int, optional): HTTP status code. Defaults to 500.
            error_code (str, optional): Machine-readable error code. Defaults to "server_error".
            details (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message)
        self.message = message or "An unexpected error occurred"
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self):
        """Convert the exception to a standardized dictionary format for serialization.
        
        Returns:
            dict: Dictionary containing standardized error response
        """
        error_dict = {
            "status": self.status_code,
            "code": self.error_code,
            "message": self.message
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict

    def __str__(self):
        """String representation of the exception.
        
        Returns:
            str: String with error type and message
        """
        return f"{self.error_code}: {self.message}"


class ValidationError(APIException):
    """Exception for data validation errors with field-specific validation failures."""
    
    def __init__(self, message="Validation error", errors=None):
        """Initialize validation error with validation errors by field.
        
        Args:
            message (str, optional): Error message. Defaults to "Validation error".
            errors (dict, optional): Dictionary of field-specific errors. Defaults to None.
        """
        super().__init__(message=message, status_code=400, error_code="validation_error")
        self.errors = errors or {}

    def to_dict(self):
        """Override to_dict to include field-specific validation errors.
        
        Returns:
            dict: Dictionary containing error details and field errors
        """
        error_dict = super().to_dict()
        error_dict["errors"] = self.errors
        return error_dict


class AuthenticationError(APIException):
    """Exception for authentication failures (invalid credentials, expired tokens)."""
    
    def __init__(self, message="Authentication failed"):
        """Initialize authentication error.
        
        Args:
            message (str, optional): Error message. Defaults to "Authentication failed".
        """
        super().__init__(message=message, status_code=401, error_code="authentication_error")


class AuthorizationError(APIException):
    """Exception for authorization failures (insufficient permissions)."""
    
    def __init__(self, message="Insufficient permissions", required_permission=None):
        """Initialize authorization error with optional required permission.
        
        Args:
            message (str, optional): Error message. Defaults to "Insufficient permissions".
            required_permission (str, optional): Permission that was required. Defaults to None.
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message=message, status_code=403, error_code="authorization_error", details=details)
        self.required_permission = required_permission


class NotFoundError(APIException):
    """Exception for resource not found errors."""
    
    def __init__(self, message="Resource not found", resource_type=None, resource_id=None):
        """Initialize not found error with resource details.
        
        Args:
            message (str, optional): Error message. Defaults to "Resource not found".
            resource_type (str, optional): Type of resource not found. Defaults to None.
            resource_id (str, optional): ID of resource not found. Defaults to None.
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message=message, status_code=404, error_code="not_found", details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(APIException):
    """Exception for resource conflict errors (e.g., duplicate unique values)."""
    
    def __init__(self, message="Resource conflict", resource_type=None, resource_id=None):
        """Initialize conflict error with resource details.
        
        Args:
            message (str, optional): Error message. Defaults to "Resource conflict".
            resource_type (str, optional): Type of resource in conflict. Defaults to None.
            resource_id (str, optional): ID of resource in conflict. Defaults to None.
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message=message, status_code=409, error_code="conflict", details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitError(APIException):
    """Exception for rate limiting errors when request limits are exceeded."""
    
    def __init__(self, message="Rate limit exceeded", retry_after=None, limit=None, current=None):
        """Initialize rate limit error with retry information.
        
        Args:
            message (str, optional): Error message. Defaults to "Rate limit exceeded".
            retry_after (int, optional): Seconds to wait before retrying. Defaults to None.
            limit (int, optional): Rate limit value. Defaults to None.
            current (int, optional): Current rate count. Defaults to None.
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["limit"] = limit
        if current:
            details["current"] = current
        super().__init__(message=message, status_code=429, error_code="rate_limit_exceeded", details=details)
        self.retry_after = retry_after
        self.limit = limit
        self.current = current


class ServerError(APIException):
    """Exception for internal server errors."""
    
    def __init__(self, message="Internal server error", reference_id=None):
        """Initialize server error with error reference ID for tracking.
        
        Args:
            message (str, optional): Error message. Defaults to "Internal server error".
            reference_id (str, optional): Error reference ID for tracking. Defaults to None.
        """
        details = {}
        if reference_id:
            details["reference_id"] = reference_id
        super().__init__(message=message, status_code=500, error_code="server_error", details=details)
        self.reference_id = reference_id


class ServiceUnavailableError(APIException):
    """Exception for temporary service unavailability."""
    
    def __init__(self, message="Service temporarily unavailable", retry_after=None, reason=None):
        """Initialize service unavailable error with retry information.
        
        Args:
            message (str, optional): Error message. Defaults to "Service temporarily unavailable".
            retry_after (int, optional): Seconds to wait before retrying. Defaults to None.
            reason (str, optional): Reason for service unavailability. Defaults to None.
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if reason:
            details["reason"] = reason
        super().__init__(message=message, status_code=503, error_code="service_unavailable", details=details)
        self.retry_after = retry_after
        self.reason = reason


class DependencyError(APIException):
    """Exception for external dependency failures."""
    
    def __init__(self, message="Dependency error", dependency=None, retryable=False, retry_after=None):
        """Initialize dependency error with details about failed dependency.
        
        Args:
            message (str, optional): Error message. Defaults to "Dependency error".
            dependency (str, optional): Name of failed dependency. Defaults to None.
            retryable (bool, optional): Whether the operation can be retried. Defaults to False.
            retry_after (int, optional): Seconds to wait before retrying. Defaults to None.
        """
        details = {}
        if dependency:
            details["dependency"] = dependency
        if retryable is not None:
            details["retryable"] = retryable
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message=message, status_code=502, error_code="dependency_error", details=details)
        self.dependency = dependency
        self.retryable = retryable
        self.retry_after = retry_after