"""
Common Schema Definitions for Task Management System

This module provides common schema definitions and utilities used throughout
the Task Management System to ensure consistency in API responses, error handling,
and pagination.

It consolidates error schemas for standardized error responses and pagination utilities
for consistent handling of paginated collections across all backend services.
"""

# Import all error schemas and utilities from error module
from .error import (
    ErrorCode, ErrorResponseBase, ValidationErrorResponse,
    AuthenticationErrorResponse, AuthorizationErrorResponse,
    NotFoundErrorResponse, ConflictErrorResponse, ServerErrorResponse,
    DependencyErrorResponse, RateLimitErrorResponse,
    ServiceUnavailableErrorResponse, create_error_response
)

# Import all pagination schemas and utilities from pagination module
from .pagination import (
    PaginationParams, PaginatedResponse, create_pagination_params,
    paginate_response, calculate_pagination, DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
)

# Export all imported entities
__all__ = [
    # Error schemas and utilities
    'ErrorCode', 'ErrorResponseBase', 'ValidationErrorResponse',
    'AuthenticationErrorResponse', 'AuthorizationErrorResponse',
    'NotFoundErrorResponse', 'ConflictErrorResponse', 'ServerErrorResponse',
    'DependencyErrorResponse', 'RateLimitErrorResponse',
    'ServiceUnavailableErrorResponse', 'create_error_response',
    
    # Pagination schemas and utilities
    'PaginationParams', 'PaginatedResponse', 'create_pagination_params',
    'paginate_response', 'calculate_pagination', 'DEFAULT_PAGE',
    'DEFAULT_PAGE_SIZE', 'MAX_PAGE_SIZE'
]