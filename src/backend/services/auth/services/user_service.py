"""
Service layer for user management that provides CRUD operations for users,
implements business logic for user-related operations, and enforces
validation and security rules.
"""

import datetime  # standard library
from typing import Dict, Optional, Union  # standard library

import bson  # pymongo v4.3.3
from bson import ObjectId  # pymongo v4.3.3

from src.backend.common.auth.jwt_utils import (  # Assuming JWT utilities are in this module
    generate_access_token,
    generate_refresh_token,
)
from src.backend.common.database.mongo.connection import get_db  # Database connection for user operations
from src.backend.common.exceptions.api_exceptions import (  # Exception for API errors
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.backend.common.logging.logger import get_logger  # Get logger for user service operations
from src.backend.common.utils.security import (  # Password hashing and verification
    hash_password,
    verify_password,
    validate_password_strength,
)
from src.backend.common.utils.validators import validate_email  # Email format validation utility
from src.backend.services.auth.models.role import (  # Assuming Role class is in this module
    get_role_by_name,
)
from src.backend.services.auth.models.user import User  # User model for database operations

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_USER_ROLE = "user"
REQUIRED_FIELDS = ["email", "password", "firstName", "lastName"]


def create_user(user_data: Dict) -> User:
    """
    Creates a new user with validated data and assigns default role.

    Args:
        user_data (dict): User data containing email, password, firstName, lastName.

    Returns:
        User: Created user instance

    Raises:
        ValueError: If required fields are missing or validation fails.
        ConflictError: If a user with the same email already exists.
    """
    # Validate required fields in user_data (email, password, firstName, lastName)
    if not all(key in user_data for key in REQUIRED_FIELDS):
        logger.error(f"Missing required fields in user data: {user_data.keys()}")
        raise ValidationError(message="Missing required fields")

    # Validate email format using validate_email function
    try:
        validate_email(user_data["email"])
    except ValidationError as e:
        logger.error(f"Invalid email format: {user_data['email']}")
        raise e

    # Validate password strength with validate_password_strength
    try:
        validate_password_strength(user_data["password"])
    except ValidationError as e:
        logger.error("Password strength validation failed")
        raise e

    # Check if user with the same email already exists
    existing_user = get_user_by_email(user_data["email"])
    if existing_user:
        logger.error(f"User with email already exists: {user_data['email']}")
        raise ConflictError(message="User with this email already exists")

    # Create a new User instance with the provided data
    user = User(
        data={
            "email": user_data["email"],
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
        }
    )

    # Set the user's password securely using hash_password
    user.set_password(user_data["password"])

    # Get default user role and assign it to the user
    try:
        user.add_role(DEFAULT_USER_ROLE)
    except ValueError as e:
        logger.error(f"Failed to assign default role: {str(e)}")
        raise ValidationError(message=str(e))

    # Generate email verification token
    user.generate_verification_token()

    # Save the user to the database
    user.save()

    # Log user creation with masked sensitive data
    logger.info(f"Created user with email: {user_data['email']}")

    # Return the created user instance
    return user


def get_user_by_id(user_id: Union[str, ObjectId]) -> Optional[User]:
    """
    Retrieves a user by their ID.

    Args:
        user_id (str or ObjectId): User ID to retrieve.

    Returns:
        User: User instance if found, None otherwise.

    Raises:
        NotFoundError: If user not found.
    """
    # Convert string ID to ObjectId if necessary
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
    except bson.errors.InvalidId:
        logger.warning(f"Invalid ObjectId format: {user_id}")
        raise NotFoundError(message="User not found")

    # Query the database for user with matching ID
    user = User.find_by_id(user_id)

    # If user not found, raise NotFoundError
    if not user:
        logger.warning(f"User not found with ID: {user_id}")
        raise NotFoundError(message="User not found")

    # Return the User instance
    return user


def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieves a user by their email address.

    Args:
        email (str): Email address to search for.

    Returns:
        User: User instance if found, None otherwise.
    """
    # Normalize email (convert to lowercase)
    email = email.lower()

    # Query the database for user with matching email
    user = User.find_one({"email": email})

    # Return the User instance if found, None otherwise
    return user


def update_user(user_or_id: Union[User, str, ObjectId], update_data: Dict) -> User:
    """
    Updates user data with validated fields.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to update.
        update_data (dict): Dictionary containing fields to update.

    Returns:
        User: Updated user instance.

    Raises:
        NotFoundError: If user not found.
        ValueError: If validation fails.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Remove restricted fields from update_data (e.g., password, email)
    restricted_fields = ["password", "email"]
    for field in restricted_fields:
        if field in update_data:
            del update_data[field]
            logger.warning(f"Attempt to update restricted field: {field}")

    # Update allowed user fields (firstName, lastName, profile info)
    for field, value in update_data.items():
        user._data[field] = value

    # Validate any updated fields as needed
    try:
        user.validate()
    except ValueError as e:
        logger.error(f"User update validation failed: {str(e)}")
        raise ValidationError(message=str(e))

    # Save changes to the database
    user.save()

    # Log user update with masked sensitive data
    logger.info(f"Updated user with ID: {user.get_id()}")

    # Return the updated user instance
    return user


def delete_user(user_or_id: Union[User, str, ObjectId]) -> bool:
    """
    Deletes a user from the system.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to delete.

    Returns:
        bool: True if user was deleted, False otherwise.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Delete the user from the database
    deleted = user.delete()

    # Log user deletion
    if deleted:
        logger.info(f"Deleted user with ID: {user.get_id()}")
    else:
        logger.warning(f"Failed to delete user with ID: {user.get_id()}")

    # Return True if deletion was successful, False otherwise
    return deleted


def change_user_password(
    user_or_id: Union[User, str, ObjectId], current_password: str, new_password: str
) -> bool:
    """
    Changes a user's password after validating current password.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to update.
        current_password (str): The user's current password.
        new_password (str): The user's new password.

    Returns:
        bool: True if password was changed, False otherwise.

    Raises:
        NotFoundError: If user not found.
        AuthenticationError: If current password is invalid.
        ValueError: If new password validation fails.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Verify current password using user.check_password
    if not user.check_password(current_password):
        logger.warning("Invalid current password provided")
        raise AuthenticationError(message="Invalid current password")

    # Validate new password strength with validate_password_strength
    try:
        validate_password_strength(new_password)
    except ValidationError as e:
        logger.error(f"New password validation failed: {str(e)}")
        raise e

    # Set the new password using user.set_password
    user.set_password(new_password)

    # Save changes to the database
    user.save()

    # Log password change (without actual passwords)
    logger.info(f"Password changed for user with ID: {user.get_id()}")

    # Return True for successful password change
    return True


def reset_user_password(user_or_id: Union[User, str, ObjectId], new_password: str) -> bool:
    """
    Resets a user's password to a new value without requiring the current password.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to update.
        new_password (str): The user's new password.

    Returns:
        bool: True if password was reset, False otherwise.

    Raises:
        NotFoundError: If user not found.
        ValueError: If new password validation fails.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Validate new password strength with validate_password_strength
    try:
        validate_password_strength(new_password)
    except ValidationError as e:
        logger.error(f"New password validation failed: {str(e)}")
        raise e

    # Set the new password using user.set_password
    user.set_password(new_password)

    # Save changes to the database
    user.save()

    # Log password reset (without actual password)
    logger.info(f"Password reset for user with ID: {user.get_id()}")

    # Return True for successful password reset
    return True


def authenticate_user(email: str, password: str) -> Dict:
    """
    Authenticates a user with email and password.

    Args:
        email (str): User's email address.
        password (str): User's password.

    Returns:
        dict: Authentication result with user data and tokens.

    Raises:
        AuthenticationError: If user not found or password incorrect.
    """
    # Normalize email (convert to lowercase)
    email = email.lower()

    # Find user by email using get_user_by_email
    user = get_user_by_email(email)
    if not user:
        logger.warning(f"Authentication failed: User not found with email: {email}")
        raise AuthenticationError(message="Invalid credentials")

    # Check if account is locked due to failed attempts
    if user.is_account_locked():
        logger.warning(f"Authentication failed: Account is locked for user: {email}")
        raise AuthenticationError(message="Account is temporarily locked")

    # Verify provided password against stored hash
    if not user.check_password(password):
        # Increment failed attempts
        user.increment_failed_attempts()
        logger.warning(f"Authentication failed: Invalid password for user: {email}")
        raise AuthenticationError(message="Invalid credentials")

    # If password correct, reset failed attempts counter
    user.reset_failed_attempts()

    # Check if email verification is required but not completed
    if not user._data.get("email_verified", False):
        logger.warning(f"Authentication failed: Email verification required for user: {email}")
        raise AuthenticationError(message="Email verification required")

    # Generate access and refresh tokens
    auth_tokens = user.generate_auth_tokens()

    # Update last login timestamp
    user.save()

    # Return authentication result with tokens and user data
    return auth_tokens


def assign_role_to_user(user_or_id: Union[User, str, ObjectId], role_name: str) -> bool:
    """
    Assigns a role to a user.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to update.
        role_name (str): Name of the role to assign.

    Returns:
        bool: True if role was assigned, False if already assigned.

    Raises:
        NotFoundError: If user not found.
        ValidationError: If role does not exist.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Get role by name using get_role_by_name
    role = get_role_by_name(role_name)
    if not role:
        logger.warning(f"Role not found: {role_name}")
        raise ValidationError(message=f"Role '{role_name}' not found")

    # Add role to user using user.add_role
    assigned = user.add_role(role_name)

    # Save changes to database
    user.save()

    # Log role assignment
    logger.info(f"Assigned role '{role_name}' to user with ID: {user.get_id()}")

    # Return True if role was assigned, False if already assigned
    return assigned


def remove_role_from_user(user_or_id: Union[User, str, ObjectId], role_name: str) -> bool:
    """
    Removes a role from a user.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to update.
        role_name (str): Name of the role to remove.

    Returns:
        bool: True if role was removed, False if not found.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Call user.remove_role method to remove the role
    removed = user.remove_role(role_name)

    # Save changes to database
    user.save()

    # Log role removal
    logger.info(f"Removed role '{role_name}' from user with ID: {user.get_id()}")

    # Return True if role was removed, False if not found
    return removed


def get_user_roles(user_or_id: Union[User, str, ObjectId]) -> List[str]:
    """
    Gets all roles assigned to a user.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to retrieve roles for.

    Returns:
        list: List of role names assigned to the user.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Extract role names from user.roles
    role_names = user._data.get("roles", [])

    # Return list of role names
    return role_names


def check_user_has_role(user_or_id: Union[User, str, ObjectId], role_name: str) -> bool:
    """
    Checks if a user has a specific role.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to check.
        role_name (str): Name of the role to check for.

    Returns:
        bool: True if user has the role, False otherwise.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Call user.has_role method to check if user has the role
    has_role = user.has_role(role_name)

    # Return True if user has the role, False otherwise
    return has_role


def generate_password_reset_token(user_or_id: Union[User, str, ObjectId]) -> Dict:
    """
    Generates a password reset token for a user.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to generate token for.

    Returns:
        dict: Dict with reset token and expiration time.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Generate reset token using user.generate_password_reset_token
    token = user.generate_password_reset_token()
    expiry = user._data.get("reset_token_expiry")

    # Return dictionary with token, expiration time, and user info
    return {"token": token, "expiry": expiry, "user_id": str(user.get_id())}


def verify_password_reset_token(
    user_or_id: Union[User, str, ObjectId], token: str, new_password: str
) -> bool:
    """
    Verifies a password reset token and resets the password.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to verify token for.
        token (str): The password reset token to verify.
        new_password (str): The new password to set.

    Returns:
        bool: True if password was reset, False otherwise.

    Raises:
        NotFoundError: If user not found.
        ValueError: If new password validation fails.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Validate new password strength with validate_password_strength
    try:
        validate_password_strength(new_password)
    except ValidationError as e:
        logger.error(f"New password validation failed: {str(e)}")
        raise e

    # Verify reset token and set new password using user.reset_password
    reset = user.reset_password(token, new_password)

    # Log password reset (without actual password)
    logger.info(f"Password reset via token for user with ID: {user.get_id()}")

    # Return True if password was reset successfully, False otherwise
    return reset


def generate_email_verification_token(user_or_id: Union[User, str, ObjectId]) -> Dict:
    """
    Generates an email verification token for a user.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to generate token for.

    Returns:
        dict: Dict with verification token and expiration time.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Generate verification token using user.generate_verification_token
    token = user.generate_verification_token()
    expiry = user._data.get("verification_token_expiry")

    # Return dictionary with token, expiration time, and user info
    return {"token": token, "expiry": expiry, "user_id": str(user.get_id())}


def verify_email_token(user_or_id: Union[User, str, ObjectId], token: str) -> bool:
    """
    Verifies an email verification token.

    Args:
        user_or_id (User or str or ObjectId): User instance or ID to verify token for.
        token (str): The email verification token to verify.

    Returns:
        bool: True if email was verified, False otherwise.

    Raises:
        NotFoundError: If user not found.
    """
    # Get user instance if user_or_id is not a User object
    if isinstance(user_or_id, User):
        user = user_or_id
    else:
        user = get_user_by_id(user_or_id)

    # Verify email token using user.verify_email
    verified = user.verify_email(token)

    # Log email verification result
    logger.info(f"Email verification result: {verified} for user with ID: {user.get_id()}")

    # Return True if email was verified successfully, False otherwise
    return verified