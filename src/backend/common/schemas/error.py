"""
Error schema definitions for the Task Management System.

This module provides standardized error response schemas and utilities
to ensure consistent error handling across all services.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from http import HTTPStatus as HTTP_STATUS

from pydantic import BaseModel, Field, validator  # pydantic ^1.9.0


class ErrorCode(str, Enum):
    """
    Standardized error codes used throughout the system.
    
    These codes provide a consistent way to identify the type of error
    that occurred, independent of the HTTP status code.
    """
    VALIDATION_ERROR = 'validation_error'
    AUTHENTICATION_ERROR = 'authentication_error'
    AUTHORIZATION_ERROR = 'authorization_error'
    NOT_FOUND = 'not_found'
    CONFLICT = 'conflict'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    SERVER_ERROR = 'server_error'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    DEPENDENCY_ERROR = 'dependency_error'


class ErrorResponseBase(BaseModel):
    """
    Base class for all error responses providing common structure.
    
    This ensures a consistent error response format across all services.
    """
    status: int = Field(description="HTTP status code")
    code: str = Field(description="Error code for client identification")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 400,
                "code": "validation_error",
                "message": "Invalid input data",
                "details": {"context": "Additional information about the error"}
            }
        }
    
    def to_dict(self) -> Dict:
        """
        Convert the error response to a dictionary for serialization.
        
        Returns:
            Dict: Dictionary representation of error response
        """
        result = {
            "status": self.status,
            "code": self.code,
            "message": self.message
        }
        
        if self.details:
            result["details"] = self.details
            
        return result


class ValidationErrorResponse(ErrorResponseBase):
    """
    Error response for validation errors with field-specific error details.
    """
    errors: Dict[str, List[str]] = Field(
        description="Field-specific validation errors"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 400,
                "code": "validation_error",
                "message": "Validation error occurred",
                "errors": {
                    "email": ["Invalid email format"],
                    "password": ["Password must be at least 8 characters"]
                }
            }
        }
    
    def __init__(
        self, 
        message: str, 
        errors: Dict[str, List[str]], 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error with field-specific errors.
        
        Args:
            message: Human-readable error message
            errors: Dictionary mapping field names to error messages
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.BAD_REQUEST,
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details
        )
        self.errors = errors
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include field-specific validation errors.
        
        Returns:
            Dict: Dictionary with validation errors included
        """
        result = super().to_dict()
        result["errors"] = self.errors
        return result


class AuthenticationErrorResponse(ErrorResponseBase):
    """
    Error response for authentication failures.
    """
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 401,
                "code": "authentication_error",
                "message": "Invalid credentials"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication error response.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.UNAUTHORIZED,
            code=ErrorCode.AUTHENTICATION_ERROR,
            message=message,
            details=details
        )


class AuthorizationErrorResponse(ErrorResponseBase):
    """
    Error response for authorization failures.
    """
    required_permission: Optional[str] = Field(
        None,
        description="Permission required to perform the action"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 403,
                "code": "authorization_error",
                "message": "Permission denied",
                "required_permission": "task:write"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authorization error response with optional required permission.
        
        Args:
            message: Human-readable error message
            required_permission: Optional permission required for the action
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.FORBIDDEN,
            code=ErrorCode.AUTHORIZATION_ERROR,
            message=message,
            details=details
        )
        self.required_permission = required_permission
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include required permission if available.
        
        Returns:
            Dict: Dictionary with authorization details
        """
        result = super().to_dict()
        if self.required_permission:
            result["required_permission"] = self.required_permission
        return result


class NotFoundErrorResponse(ErrorResponseBase):
    """
    Error response for resource not found errors.
    """
    resource_type: Optional[str] = Field(
        None,
        description="Type of resource that wasn't found"
    )
    resource_id: Optional[str] = Field(
        None,
        description="ID of resource that wasn't found"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 404,
                "code": "not_found",
                "message": "Resource not found",
                "resource_type": "task",
                "resource_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize not found error response with resource details.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource that wasn't found
            resource_id: ID of resource that wasn't found
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.NOT_FOUND,
            code=ErrorCode.NOT_FOUND,
            message=message,
            details=details
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include resource details.
        
        Returns:
            Dict: Dictionary with resource details
        """
        result = super().to_dict()
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_id:
            result["resource_id"] = self.resource_id
        return result


class ConflictErrorResponse(ErrorResponseBase):
    """
    Error response for resource conflict errors.
    """
    resource_type: Optional[str] = Field(
        None,
        description="Type of resource with conflict"
    )
    resource_id: Optional[str] = Field(
        None,
        description="ID of resource with conflict"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 409,
                "code": "conflict",
                "message": "Resource already exists",
                "resource_type": "user",
                "resource_id": "user@example.com"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize conflict error response with resource details.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource with conflict
            resource_id: ID of resource with conflict
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.CONFLICT,
            code=ErrorCode.CONFLICT,
            message=message,
            details=details
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include resource details.
        
        Returns:
            Dict: Dictionary with resource details
        """
        result = super().to_dict()
        if self.resource_type:
            result["resource_type"] = self.resource_type
        if self.resource_id:
            result["resource_id"] = self.resource_id
        return result


class ServerErrorResponse(ErrorResponseBase):
    """
    Error response for internal server errors.
    """
    reference_id: Optional[str] = Field(
        None,
        description="Reference ID for error tracking"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 500,
                "code": "server_error",
                "message": "An internal server error occurred",
                "reference_id": "error-abc123"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        reference_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize server error response with reference ID for tracking.
        
        Args:
            message: Human-readable error message
            reference_id: Reference ID for error tracking
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            code=ErrorCode.SERVER_ERROR,
            message=message,
            details=details
        )
        self.reference_id = reference_id
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include reference ID.
        
        Returns:
            Dict: Dictionary with reference ID
        """
        result = super().to_dict()
        if self.reference_id:
            result["reference_id"] = self.reference_id
        return result


class DependencyErrorResponse(ErrorResponseBase):
    """
    Error response for dependency failures.
    """
    dependency: str = Field(
        description="Name of the dependency that failed"
    )
    retryable: bool = Field(
        description="Indicates if the request can be retried"
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 502,
                "code": "dependency_error",
                "message": "Dependency service unavailable",
                "dependency": "authentication-service",
                "retryable": True,
                "retry_after": 30
            }
        }
    
    def __init__(
        self, 
        message: str, 
        dependency: str,
        retryable: bool,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize dependency error response with dependency details.
        
        Args:
            message: Human-readable error message
            dependency: Name of the dependency that failed
            retryable: Indicates if the request can be retried
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.BAD_GATEWAY,
            code=ErrorCode.DEPENDENCY_ERROR,
            message=message,
            details=details
        )
        self.dependency = dependency
        self.retryable = retryable
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include dependency details.
        
        Returns:
            Dict: Dictionary with dependency information
        """
        result = super().to_dict()
        result["dependency"] = self.dependency
        result["retryable"] = self.retryable
        if self.retry_after is not None:
            result["retry_after"] = self.retry_after
        return result


class RateLimitErrorResponse(ErrorResponseBase):
    """
    Error response for rate limiting errors.
    """
    retry_after: int = Field(
        description="Seconds to wait before retrying"
    )
    limit: Optional[int] = Field(
        None,
        description="Rate limit threshold"
    )
    current: Optional[int] = Field(
        None,
        description="Current usage count"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 429,
                "code": "rate_limit_exceeded",
                "message": "Rate limit exceeded",
                "retry_after": 60,
                "limit": 100,
                "current": 105
            }
        }
    
    def __init__(
        self, 
        message: str, 
        retry_after: int,
        limit: Optional[int] = None,
        current: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error response with rate limit details.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            limit: Rate limit threshold
            current: Current usage count
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.TOO_MANY_REQUESTS,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details
        )
        self.retry_after = retry_after
        self.limit = limit
        self.current = current
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include rate limit details.
        
        Returns:
            Dict: Dictionary with rate limit information
        """
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        if self.limit is not None:
            result["limit"] = self.limit
        if self.current is not None:
            result["current"] = self.current
        return result


class ServiceUnavailableErrorResponse(ErrorResponseBase):
    """
    Error response for service unavailability.
    """
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for service unavailability"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": 503,
                "code": "service_unavailable",
                "message": "Service is temporarily unavailable",
                "retry_after": 300,
                "reason": "Scheduled maintenance"
            }
        }
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[int] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize service unavailable error response with retry information.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            reason: Reason for service unavailability
            details: Additional error details
        """
        super().__init__(
            status=HTTP_STATUS.SERVICE_UNAVAILABLE,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            details=details
        )
        self.retry_after = retry_after
        self.reason = reason
    
    def to_dict(self) -> Dict:
        """
        Override to_dict to include service unavailability details.
        
        Returns:
            Dict: Dictionary with unavailability information
        """
        result = super().to_dict()
        if self.retry_after is not None:
            result["retry_after"] = self.retry_after
        if self.reason:
            result["reason"] = self.reason
        return result


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict] = None
) -> Dict:
    """
    Creates a standardized error response dictionary based on error type.
    
    This utility function helps create consistent error responses without
    needing to instantiate the specific error classes.
    
    Args:
        error_code: The error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Dict: Standardized error response dictionary
    """
    error_response = {
        "status": status_code,
        "code": error_code,
        "message": message
    }
    
    if details:
        error_response["details"] = details
    
    return error_response