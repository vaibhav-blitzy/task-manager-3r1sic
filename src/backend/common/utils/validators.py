"""
Utility module providing validation functions for data validation across the Task Management System.
Implements comprehensive input validation for various entities including tasks, projects, users, and file attachments.
"""

import re
import typing
from datetime import datetime
import bson
from typing import Dict, List, Optional, Any, Union

from ..exceptions.api_exceptions import ValidationError
from .datetime import is_overdue, now

# Regular expression for email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Regular expression for password validation (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char)
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

# Valid task status values
STATUS_VALUES = ["created", "assigned", "in-progress", "on-hold", "in-review", "completed", "cancelled"]

# Valid task priority values
PRIORITY_VALUES = ["low", "medium", "high", "urgent"]

# Valid project status values
PROJECT_STATUS_VALUES = ["planning", "active", "on-hold", "completed", "archived", "cancelled"]

# Maximum file size in bytes (25MB)
FILE_SIZE_LIMIT = 25 * 1024 * 1024

# Allowed file MIME types
ALLOWED_FILE_TYPES = [
    "image/jpeg", "image/png", "image/gif", 
    "application/pdf", 
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
    "text/plain", 
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
]


def validate_required(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validates that required fields are present and not empty in the data.
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that are required
        
    Returns:
        True if all required fields are present and not empty
        
    Raises:
        ValidationError: If any required field is missing or empty
    """
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            errors[field] = "This field is required"
    
    if errors:
        raise ValidationError("Missing required fields", errors)
    
    return True


def validate_string_length(data: Dict[str, Any], length_limits: Dict[str, Dict[str, int]]) -> bool:
    """
    Validates that string fields are within specified length limits.
    
    Args:
        data: Dictionary containing the data to validate
        length_limits: Dictionary mapping field names to dictionaries with 'min_length' and 'max_length' keys
        
    Returns:
        True if all string fields are within specified length limits
        
    Raises:
        ValidationError: If any string field is outside its length limits
    """
    errors = {}
    
    for field, limits in length_limits.items():
        if field in data and data[field] is not None:
            min_length = limits.get('min_length', 0)
            max_length = limits.get('max_length', float('inf'))
            
            if not isinstance(data[field], str):
                errors[field] = "Must be a string"
            elif len(data[field]) < min_length:
                errors[field] = f"Must be at least {min_length} characters"
            elif len(data[field]) > max_length:
                errors[field] = f"Must be at most {max_length} characters"
    
    if errors:
        raise ValidationError("String length validation failed", errors)
    
    return True


def validate_email(email: str) -> bool:
    """
    Validates that an email address is correctly formatted.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if email is valid
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email validation failed", {"email": "Email is required"})
    
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email validation failed", {"email": "Invalid email format"})
    
    return True


def validate_password_strength(password: str) -> bool:
    """
    Validates that a password meets strength requirements.
    
    Args:
        password: The password to validate
        
    Returns:
        True if password meets strength requirements
        
    Raises:
        ValidationError: If password doesn't meet strength requirements
    """
    if not password:
        raise ValidationError("Password validation failed", {"password": "Password is required"})
    
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not PASSWORD_REGEX.match(password):
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        if not any(c in "@$!%*?&" for c in password):
            errors.append("Password must contain at least one special character (@$!%*?&)")
    
    if errors:
        raise ValidationError("Password validation failed", {"password": errors})
    
    return True


def validate_object_id(id_str: str, field_name: str) -> bool:
    """
    Validates that a string is a valid MongoDB ObjectId.
    
    Args:
        id_str: The string to validate as an ObjectId
        field_name: The name of the field containing the ID for error messages
        
    Returns:
        True if the string is a valid ObjectId or None
        
    Raises:
        ValidationError: If the string is not a valid ObjectId
    """
    if id_str is None:
        return True
    
    if not isinstance(id_str, str) or len(id_str) != 24 or not all(c in "0123456789abcdefABCDEF" for c in id_str):
        raise ValidationError(f"Invalid {field_name}", {field_name: "Must be a valid ID"})
    
    try:
        bson.ObjectId(id_str)
        return True
    except (bson.errors.InvalidId, TypeError):
        raise ValidationError(f"Invalid {field_name}", {field_name: "Must be a valid ID"})


def validate_enum(value: str, allowed_values: List[str], field_name: str) -> bool:
    """
    Validates that a value is one of a set of allowed values.
    
    Args:
        value: The value to validate
        allowed_values: List of allowed values
        field_name: The name of the field for error messages
        
    Returns:
        True if the value is in allowed_values or None
        
    Raises:
        ValidationError: If the value is not in allowed_values
    """
    if value is None:
        return True
    
    if value not in allowed_values:
        raise ValidationError(
            f"Invalid {field_name}", 
            {field_name: f"Must be one of: {', '.join(allowed_values)}"}
        )
    
    return True


def validate_future_date(date: datetime, field_name: str) -> bool:
    """
    Validates that a date is in the future.
    
    Args:
        date: The date to validate
        field_name: The name of the field for error messages
        
    Returns:
        True if the date is in the future or None
        
    Raises:
        ValidationError: If the date is not in the future
    """
    if date is None:
        return True
    
    # Ensure date is timezone-aware
    if date.tzinfo is None:
        # Assume UTC for naive datetimes
        from datetime import timezone
        date = date.replace(tzinfo=timezone.utc)
    
    current_time = now()
    
    if date <= current_time:
        raise ValidationError(
            f"Invalid {field_name}", 
            {field_name: "Must be a future date"}
        )
    
    return True


def validate_file_type(mime_type: str) -> bool:
    """
    Validates that a file's MIME type is allowed.
    
    Args:
        mime_type: The MIME type to validate
        
    Returns:
        True if the file type is allowed
        
    Raises:
        ValidationError: If the file type is not allowed
    """
    if mime_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(
            "Invalid file type", 
            {"file_type": f"File type must be one of: {', '.join(ALLOWED_FILE_TYPES)}"}
        )
    
    return True


def validate_file_size(size: int) -> bool:
    """
    Validates that a file size is within the allowed limit.
    
    Args:
        size: The file size in bytes to validate
        
    Returns:
        True if the file size is within limits
        
    Raises:
        ValidationError: If the file size exceeds the limit
    """
    if size > FILE_SIZE_LIMIT:
        max_size_mb = FILE_SIZE_LIMIT / (1024 * 1024)
        raise ValidationError(
            "File too large", 
            {"file_size": f"File size must be less than {max_size_mb} MB"}
        )
    
    return True


def validate_task_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validates that a task status transition is allowed.
    
    Args:
        current_status: The current status of the task
        new_status: The proposed new status
        
    Returns:
        True if the status transition is valid
        
    Raises:
        ValidationError: If the status transition is not valid
    """
    # Define allowed transitions for each status
    allowed_transitions = {
        "created": ["assigned", "in-progress", "cancelled"],
        "assigned": ["in-progress", "declined", "cancelled"],
        "in-progress": ["on-hold", "in-review", "completed", "cancelled"],
        "on-hold": ["in-progress", "cancelled"],
        "in-review": ["in-progress", "completed", "cancelled"],
        "completed": [],  # Terminal state, no transitions allowed
        "cancelled": [],  # Terminal state, no transitions allowed
        "declined": ["assigned", "cancelled"]
    }
    
    # Allow transition to same status (no change)
    if current_status == new_status:
        return True
    
    # Check if current status exists in our mapping
    if current_status not in allowed_transitions:
        raise ValidationError(
            "Invalid status transition", 
            {"status": f"Current status '{current_status}' is not recognized"}
        )
    
    # Check if transition is allowed
    if new_status not in allowed_transitions[current_status]:
        raise ValidationError(
            "Invalid status transition", 
            {"status": f"Cannot transition from '{current_status}' to '{new_status}'. " +
                     f"Allowed transitions: {', '.join(allowed_transitions[current_status])}"}
        )
    
    return True


def validate_project_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validates that a project status transition is allowed.
    
    Args:
        current_status: The current status of the project
        new_status: The proposed new status
        
    Returns:
        True if the status transition is valid
        
    Raises:
        ValidationError: If the status transition is not valid
    """
    # Define allowed transitions for each project status
    allowed_transitions = {
        "planning": ["active", "on-hold", "cancelled"],
        "active": ["on-hold", "completed", "cancelled"],
        "on-hold": ["active", "cancelled"],
        "completed": ["archived"],
        "archived": [],  # Terminal state, no transitions allowed
        "cancelled": ["archived"]
    }
    
    # Allow transition to same status (no change)
    if current_status == new_status:
        return True
    
    # Check if current status exists in our mapping
    if current_status not in allowed_transitions:
        raise ValidationError(
            "Invalid project status transition", 
            {"status": f"Current status '{current_status}' is not recognized"}
        )
    
    # Check if transition is allowed
    if new_status not in allowed_transitions[current_status]:
        raise ValidationError(
            "Invalid project status transition", 
            {"status": f"Cannot transition from '{current_status}' to '{new_status}'. " +
                     f"Allowed transitions: {', '.join(allowed_transitions[current_status])}"}
        )
    
    return True


def validate_task(task_data: Dict[str, Any], is_update: bool = False) -> bool:
    """
    Comprehensive validation for task data.
    
    Args:
        task_data: The task data to validate
        is_update: Whether this is an update operation (affects required fields)
        
    Returns:
        True if all task validations pass
        
    Raises:
        ValidationError: If any validation fails
    """
    errors = {}
    
    # Required fields validation for creation
    if not is_update:
        try:
            validate_required(task_data, ["title", "status"])
        except ValidationError as e:
            errors.update(e.errors)
    
    # String length validation
    try:
        validate_string_length(task_data, {
            "title": {"min_length": 3, "max_length": 100},
            "description": {"min_length": 0, "max_length": 5000}
        })
    except ValidationError as e:
        errors.update(e.errors)
    
    # Status validation
    if "status" in task_data and task_data["status"] is not None:
        try:
            validate_enum(task_data["status"], STATUS_VALUES, "status")
        except ValidationError as e:
            if "status" in e.errors:
                errors["status"] = e.errors["status"]
    
    # Priority validation
    if "priority" in task_data and task_data["priority"] is not None:
        try:
            validate_enum(task_data["priority"], PRIORITY_VALUES, "priority")
        except ValidationError as e:
            if "priority" in e.errors:
                errors["priority"] = e.errors["priority"]
    
    # Assignee ID validation
    if "assignee_id" in task_data and task_data["assignee_id"] is not None:
        try:
            validate_object_id(task_data["assignee_id"], "assignee_id")
        except ValidationError as e:
            if "assignee_id" in e.errors:
                errors["assignee_id"] = e.errors["assignee_id"]
    
    # Project ID validation
    if "project_id" in task_data and task_data["project_id"] is not None:
        try:
            validate_object_id(task_data["project_id"], "project_id")
        except ValidationError as e:
            if "project_id" in e.errors:
                errors["project_id"] = e.errors["project_id"]
    
    # Due date validation
    if "due_date" in task_data and task_data["due_date"] is not None:
        try:
            validate_future_date(task_data["due_date"], "due_date")
        except ValidationError as e:
            if "due_date" in e.errors:
                errors["due_date"] = e.errors["due_date"]
    
    if errors:
        raise ValidationError("Task validation failed", errors)
    
    return True


def validate_project(project_data: Dict[str, Any], is_update: bool = False) -> bool:
    """
    Comprehensive validation for project data.
    
    Args:
        project_data: The project data to validate
        is_update: Whether this is an update operation (affects required fields)
        
    Returns:
        True if all project validations pass
        
    Raises:
        ValidationError: If any validation fails
    """
    errors = {}
    
    # Required fields validation for creation
    if not is_update:
        try:
            validate_required(project_data, ["name"])
        except ValidationError as e:
            errors.update(e.errors)
    
    # String length validation
    try:
        validate_string_length(project_data, {
            "name": {"min_length": 3, "max_length": 100},
            "description": {"min_length": 0, "max_length": 5000}
        })
    except ValidationError as e:
        errors.update(e.errors)
    
    # Status validation
    if "status" in project_data and project_data["status"] is not None:
        try:
            validate_enum(project_data["status"], PROJECT_STATUS_VALUES, "status")
        except ValidationError as e:
            if "status" in e.errors:
                errors["status"] = e.errors["status"]
    
    # Category validation (simple non-empty check)
    if "category" in project_data and project_data["category"] is not None:
        if isinstance(project_data["category"], str) and not project_data["category"].strip():
            errors["category"] = "Category cannot be empty if provided"
    
    if errors:
        raise ValidationError("Project validation failed", errors)
    
    return True


def validate_user(user_data: Dict[str, Any], is_update: bool = False) -> bool:
    """
    Comprehensive validation for user data.
    
    Args:
        user_data: The user data to validate
        is_update: Whether this is an update operation (affects required fields)
        
    Returns:
        True if all user validations pass
        
    Raises:
        ValidationError: If any validation fails
    """
    errors = {}
    
    # Required fields validation for creation
    if not is_update:
        try:
            validate_required(user_data, ["email", "password", "firstName", "lastName"])
        except ValidationError as e:
            errors.update(e.errors)
    
    # String length validation
    try:
        validate_string_length(user_data, {
            "firstName": {"min_length": 1, "max_length": 50},
            "lastName": {"min_length": 1, "max_length": 50}
        })
    except ValidationError as e:
        errors.update(e.errors)
    
    # Email validation
    if "email" in user_data and user_data["email"] is not None:
        try:
            validate_email(user_data["email"])
        except ValidationError as e:
            if "email" in e.errors:
                errors["email"] = e.errors["email"]
    
    # Password validation
    if "password" in user_data and user_data["password"] is not None:
        try:
            validate_password_strength(user_data["password"])
        except ValidationError as e:
            if "password" in e.errors:
                errors["password"] = e.errors["password"]
    
    if errors:
        raise ValidationError("User validation failed", errors)
    
    return True