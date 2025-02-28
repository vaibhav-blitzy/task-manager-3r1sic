"""
Task Management System - Common Package

This package provides shared utilities, configuration, and functionality 
used across all backend microservices in the Task Management System.

It includes:
- Configuration management
- Error handling and exception classes
- Logging utilities
- Authentication utilities
- Common utilities and helpers

This __init__ file exposes key components from submodules to simplify imports
and provide a consistent interface for common functionality.
"""

# Import version and typing
from typing import Dict, Any, Optional, List, Union
__version__ = "1.0.0"

# Import configuration components
from .config import CONFIG, get_config

# Import exception components
from .exceptions.api_exceptions import (
    APIException,
    ValidationError, 
    AuthenticationError,
    NotFoundError
)
from .exceptions.error_handlers import register_error_handlers

# Import logging components
from .logging.logger import get_logger, LogLevel

# Import authentication utilities
from .auth.jwt_utils import generate_access_token, validate_access_token

# Set up package-level logger
logger = get_logger(__name__)

# Explicitly list what should be available when importing from this package
__all__ = [
    "__version__",
    "CONFIG",
    "get_config",
    "APIException",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "register_error_handlers",
    "get_logger",
    "LogLevel",
    "generate_access_token",
    "validate_access_token"
]