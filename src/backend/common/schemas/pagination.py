"""
Pagination schemas and utilities for API responses.

This module defines common pagination schemas and utilities used
across all services in the Task Management System to provide
consistent API response formats for collections of resources.

The module implements standardized pagination for all API endpoints 
returning collections of resources as specified in the Technical 
Specifications/6.3.1 API DESIGN section, supporting efficient 
pagination of large data sets like task lists and project collections
as required in Technical Specifications/6.3.5 Task Query and Filtering.
"""

from pydantic import BaseModel, Field, validator
from typing import Generic, TypeVar, List, Optional, Dict, Any
import math

# Default pagination constants
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Type variable for generic response
T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Schema for pagination request parameters.
    
    Defines standard parameters for requesting paginated data
    with validation to ensure parameters are within acceptable ranges.
    """
    
    page: int = Field(DEFAULT_PAGE, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, 
                          description="Number of items per page")
    
    def __init__(self, page: int = DEFAULT_PAGE, per_page: int = DEFAULT_PAGE_SIZE, **data):
        """Initialize pagination parameters with defaults."""
        super().__init__(page=page, per_page=per_page, **data)
    
    @validator('page')
    def validate_page(cls, v):
        """Validates that page number is positive."""
        if v < 1:
            return DEFAULT_PAGE
        return v
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validates items per page is within allowed range."""
        if v < 1:
            return DEFAULT_PAGE_SIZE
        if v > MAX_PAGE_SIZE:
            return MAX_PAGE_SIZE
        return v
    
    def to_dict(self) -> Dict:
        """Converts pagination parameters to dictionary."""
        return {
            "page": self.page,
            "per_page": self.per_page
        }
    
    def get_skip(self) -> int:
        """Calculates number of items to skip for database query."""
        return (self.page - 1) * self.per_page
    
    def get_limit(self) -> int:
        """Returns the number of items to limit in database query."""
        return self.per_page


class PaginatedResponse(Generic[T], BaseModel):
    """
    Generic schema for paginated API responses.
    
    Provides a standardized format for returning paginated collections
    of any resource type, including both the resource items and
    pagination metadata.
    """
    
    items: List[T]
    page: int
    per_page: int
    total: int
    total_pages: int
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
    
    def __init__(self, items: List[T], page: int, per_page: int, total: int, 
                 total_pages: int, next_page: Optional[int] = None, 
                 prev_page: Optional[int] = None, **data):
        """Initialize paginated response with items and pagination metadata."""
        super().__init__(
            items=items, 
            page=page, 
            per_page=per_page, 
            total=total, 
            total_pages=total_pages, 
            next_page=next_page, 
            prev_page=prev_page, 
            **data
        )
    
    @classmethod
    def from_query(cls, items: List[T], total: int, params: PaginationParams) -> 'PaginatedResponse[T]':
        """Class method to create pagination response from query results."""
        total_pages = math.ceil(total / params.per_page) if total > 0 else 0
        next_page = params.page + 1 if params.page < total_pages else None
        prev_page = params.page - 1 if params.page > 1 else None
        
        return cls(
            items=items,
            page=params.page,
            per_page=params.per_page,
            total=total,
            total_pages=total_pages,
            next_page=next_page,
            prev_page=prev_page
        )
    
    def to_dict(self) -> Dict:
        """Converts paginated response to dictionary format."""
        metadata = {
            "page": self.page,
            "per_page": self.per_page,
            "total": self.total,
            "total_pages": self.total_pages,
            "next_page": self.next_page,
            "prev_page": self.prev_page
        }
        
        return {
            "items": self.items,
            "metadata": metadata
        }


def create_pagination_params(args: Dict) -> PaginationParams:
    """
    Helper function to create pagination parameters from request arguments.
    
    Extracts and validates pagination parameters from request query parameters
    or other dictionary sources.
    
    Args:
        args: Dictionary containing pagination parameters (page, per_page)
        
    Returns:
        PaginationParams: A validated pagination parameters object
    """
    page = args.get('page', DEFAULT_PAGE)
    per_page = args.get('per_page', DEFAULT_PAGE_SIZE)
    
    # Convert string values to integers if needed
    if isinstance(page, str) and page.isdigit():
        page = int(page)
    if isinstance(per_page, str) and per_page.isdigit():
        per_page = int(per_page)
    
    return PaginationParams(page=page, per_page=per_page)


def paginate_response(items: List[T], total: int, params: PaginationParams) -> PaginatedResponse[T]:
    """
    Creates a paginated response from a list of items and total count.
    
    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        params: Pagination parameters (page, per_page)
        
    Returns:
        PaginatedResponse: A standardized paginated response
    """
    return PaginatedResponse.from_query(items, total, params)


def calculate_pagination(total: int, params: PaginationParams) -> Dict:
    """
    Calculates pagination metadata from total items and pagination parameters.
    
    Args:
        total: Total number of items across all pages
        params: Pagination parameters (page, per_page)
        
    Returns:
        dict: Dictionary with pagination metadata
    """
    total_pages = math.ceil(total / params.per_page) if total > 0 else 0
    next_page = params.page + 1 if params.page < total_pages else None
    prev_page = params.page - 1 if params.page > 1 else None
    
    return {
        "page": params.page,
        "per_page": params.per_page,
        "total": total,
        "total_pages": total_pages,
        "next_page": next_page,
        "prev_page": prev_page
    }