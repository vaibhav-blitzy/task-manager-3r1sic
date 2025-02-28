"""
Common utility functions for the Task Management System.

This package provides a comprehensive set of utility functions for date/time handling,
security operations, and data validation that are used throughout the application.

All functions are re-exported at the package level for convenient access.
"""

# Import all utility functions from submodules
from .datetime import *
from .security import *
from .validators import *

# Package version
__version__ = "1.0.0"

# Define the exported names from this package
__all__ = [
    # From datetime.py
    'now', 'to_iso_format', 'from_iso_format', 'format_date', 'parse_date',
    'is_overdue', 'is_due_soon', 'convert_timezone', 'get_date_range', 'calculate_duration',
    'get_relative_date', 'get_start_of_day', 'get_end_of_day', 'ISO_DATE_FORMAT',
    'DEFAULT_TIMEZONE', 'DATE_FORMATS',
    # From security.py
    'hash_password', 'verify_password', 'validate_password_strength', 'generate_secure_token',
    'generate_api_key', 'encrypt_data', 'decrypt_data', 'generate_key_from_password',
    'generate_hmac', 'verify_hmac', 'secure_compare', 'sanitize_input',
    # From validators.py
    'validate_email', 'validate_required', 'validate_string_length', 'validate_pattern',
    'validate_enum', 'validate_url', 'validate_future_date', 'validate_date_format',
    'validate_object_id', 'validate_numeric_range', 'validate_list_items',
    'validate_json_schema', 'sanitize_string', 'validate_task_priority',
    'validate_task_status', 'validate_password', 'validate_file_type',
    'validate_file_size', 'EMAIL_REGEX', 'URL_REGEX', 'PRIORITY_VALUES', 'STATUS_VALUES'
]