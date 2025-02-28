"""
Defines the User model for the authentication service, including user attributes,
authentication methods, role management, and user-specific operations like password
handling and profile management.
"""

import datetime
import re
from typing import Dict, List, Optional, Any, Union

import bson  # pymongo v4.3.3
from bson import ObjectId  # pymongo v4.3.3
import pyotp  # pyotp v2.8.0

from src.backend.common.database.mongo.models import Document  # Assuming Document class is in this module
from src.backend.services.auth.models.role import Role  # Assuming Role class is in this module
from src.backend.common.utils.security import hash_password, verify_password, generate_secure_token  # Assuming security utils are in this module
from src.backend.common.utils.validators import validate_email, validate_password_strength  # Assuming validators are in this module
from src.backend.services.auth.models.role import get_role_by_name  # Assuming role retrieval function is in this module
from src.backend.common.logging.logger import get_logger  # Assuming logger utility is in this module
from src.backend.common.auth.jwt_utils import generate_access_token, generate_refresh_token  # Assuming JWT utilities are in this module

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_USER_ROLE = "user"
PASSWORD_HISTORY_LIMIT = 10  # Number of previous passwords to store
MAX_FAILED_ATTEMPTS = 5  # Maximum failed login attempts before temporary lockout
LOCKOUT_DURATION_MINUTES = 30  # Account lockout duration in minutes


class User(Document):
    """
    MongoDB document model representing a user in the system.
    """

    collection_name: str = "users"
    schema: Dict = {
        "email": {"type": "str", "required": True},
        "password_hash": {"type": "str", "required": True},
        "password_history": {"type": "list", "items": {"type": "str"}},
        "firstName": {"type": "str", "required": True},
        "lastName": {"type": "str", "required": True},
        "roles": {"type": "list", "items": {"type": "str"}},
        "organizations": {"type": "list", "items": {"type": "dict"}},
        "settings": {"type": "dict"},
        "security": {"type": "dict"},
        "status": {"type": "str"},
        "created_at": {"type": "datetime"},
        "updated_at": {"type": "datetime"},
        "account_locked": {"type": "bool"},
        "locked_until": {"type": "datetime"},
        "failed_attempts": {"type": "int"},
        "email_verified": {"type": "bool"},
        "verification_token": {"type": "str"},
        "verification_token_expiry": {"type": "datetime"},
        "reset_token": {"type": "str"},
        "reset_token_expiry": {"type": "datetime"},
        "mfa_enabled": {"type": "bool"},
        "mfa_method": {"type": "str"},
        "mfa_secret": {"type": "str"},
        "password_last_changed": {"type": "datetime"}
    }
    use_schema_validation: bool = True

    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new User instance.
        """
        super().__init__(data, is_new)

    def set_password(self, password: str) -> None:
        """
        Sets a new password for the user with proper hashing.
        """
        # Validate password strength
        validate_password_strength(password)

        # Check password history to prevent reuse
        if "password_history" in self._data and self._data["password_history"]:
            for old_password_hash in self._data["password_history"]:
                if verify_password(password, old_password_hash):
                    raise ValueError("Cannot reuse previous passwords")

        # Hash the new password
        hashed_password = hash_password(password)

        # Update password history with current password
        if "password_history" not in self._data:
            self._data["password_history"] = []

        self._data["password_history"].insert(0, self._data.get("password_hash"))
        self._data["password_history"] = self._data["password_history"][:PASSWORD_HISTORY_LIMIT]

        # Set the new password hash
        self._data["password_hash"] = hashed_password

        # Update password_last_changed timestamp
        self._data["password_last_changed"] = datetime.datetime.utcnow()

    def check_password(self, password: str) -> bool:
        """
        Verifies if the provided password matches the stored hash.
        """
        # Retrieve the stored password hash
        stored_hash = self._data.get("password_hash")

        # Use verify_password utility to check the password
        if not stored_hash:
            return False
        return verify_password(password, stored_hash)

    def has_role(self, role_name: str) -> bool:
        """
        Checks if user has a specific role.
        """
        # Get user roles list
        roles = self._data.get("roles", [])

        # Check if the specified role is in the list
        return role_name in roles

    def add_role(self, role_name: str) -> bool:
        """
        Adds a role to the user.
        """
        # Get role document by name
        role = get_role_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        # Check if user already has this role
        if self.has_role(role_name):
            return False

        # Add role to user's roles list if not present
        if "roles" not in self._data:
            self._data["roles"] = []
        self._data["roles"].append(role_name)
        return True

    def remove_role(self, role_name: str) -> bool:
        """
        Removes a role from the user.
        """
        # Get user roles list
        roles = self._data.get("roles", [])

        # Check if the specified role is in the list
        if role_name not in roles:
            return False

        # Remove role if found
        roles.remove(role_name)
        self._data["roles"] = roles
        return True

    def generate_verification_token(self) -> str:
        """
        Generates a token for email verification.
        """
        # Generate secure token using generate_secure_token
        token = generate_secure_token()

        # Set token expiration time (24 hours from now)
        self._data["verification_token"] = token
        self._data["verification_token_expiry"] = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

        return token

    def verify_email(self, token: str) -> bool:
        """
        Verifies user's email using a token.
        """
        # Get stored verification token and expiration
        stored_token = self._data.get("verification_token")
        token_expiry = self._data.get("verification_token_expiry")

        # Check if token has expired
        if not stored_token or not token_expiry or token_expiry < datetime.datetime.utcnow():
            return False

        # Verify token matches stored hash
        if token != stored_token:
            return False

        # If valid, set email_verified to True
        self._data["email_verified"] = True

        # Clear verification token data
        self._data["verification_token"] = None
        self._data["verification_token_expiry"] = None
        return True

    def generate_password_reset_token(self) -> str:
        """
        Generates a token for password reset.
        """
        # Generate secure token using generate_secure_token
        token = generate_secure_token()

        # Set token expiration time (1 hour from now)
        self._data["reset_token"] = token
        self._data["reset_token_expiry"] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Resets user's password using a valid token.
        """
        # Get stored reset token and expiration
        stored_token = self._data.get("reset_token")
        token_expiry = self._data.get("reset_token_expiry")

        # Check if token has expired
        if not stored_token or not token_expiry or token_expiry < datetime.datetime.utcnow():
            return False

        # Verify token matches stored hash
        if token != stored_token:
            return False

        # If valid, set new password using set_password
        self.set_password(new_password)

        # Clear reset token data
        self._data["reset_token"] = None
        self._data["reset_token_expiry"] = None

        # Reset failed login attempts
        self.reset_failed_attempts()
        return True

    def enable_mfa(self, method: str) -> Dict:
        """
        Enables multi-factor authentication for the user.
        """
        # Validate MFA method (totp, sms, email)
        if method not in ["totp", "sms", "email"]:
            raise ValueError("Invalid MFA method")

        # For TOTP: Generate secret key using pyotp
        if method == "totp":
            secret = pyotp.random_base32()
            self._data["mfa_secret"] = secret
        # For SMS/Email: Verify phone/email is set (implementation specific)
        else:
            raise NotImplementedError("SMS and Email MFA are not yet implemented")

        # Set mfa_enabled to True
        self._data["mfa_enabled"] = True

        # Set mfa_method to provided method
        self._data["mfa_method"] = method

        # Store method-specific configuration
        config_data = {"secret": secret} if method == "totp" else {}

        return config_data

    def verify_mfa(self, code: str) -> bool:
        """
        Verifies a multi-factor authentication code.
        """
        # Check if MFA is enabled
        if not self._data.get("mfa_enabled"):
            return False

        # Get MFA method and configuration
        method = self._data.get("mfa_method")
        secret = self._data.get("mfa_secret")

        # For TOTP: Verify code against secret using pyotp
        if method == "totp":
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        # For SMS/Email: Verify code against stored code (implementation specific)
        else:
            raise NotImplementedError("SMS and Email MFA are not yet implemented")

    def disable_mfa(self) -> bool:
        """
        Disables multi-factor authentication for the user.
        """
        # Set mfa_enabled to False
        self._data["mfa_enabled"] = False

        # Clear mfa_method and configuration
        self._data["mfa_method"] = None
        self._data["mfa_secret"] = None
        return True

    def increment_failed_attempts(self) -> int:
        """
        Increments the failed login attempts counter.
        """
        # Retrieve current failed_attempts count
        failed_attempts = self._data.get("failed_attempts", 0)

        # Increment count by 1
        failed_attempts += 1
        self._data["failed_attempts"] = failed_attempts

        # If count exceeds MAX_FAILED_ATTEMPTS, lock account
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            self._data["account_locked"] = True
            self._data["locked_until"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=LOCKOUT_DURATION_MINUTES)

        # Save changes to the database
        self.save()
        return failed_attempts

    def reset_failed_attempts(self) -> None:
        """
        Resets the failed login attempts counter.
        """
        # Set failed_attempts to 0
        self._data["failed_attempts"] = 0

        # Clear account_locked and locked_until if set
        self._data["account_locked"] = False
        self._data["locked_until"] = None

        # Save changes to the database
        self.save()

    def is_account_locked(self) -> bool:
        """
        Checks if the user account is temporarily locked.
        """
        # Check if account_locked is True
        if not self._data.get("account_locked"):
            return False

        # If locked, check if locked_until time has passed
        locked_until = self._data.get("locked_until")
        if locked_until and locked_until < datetime.datetime.utcnow():
            # If lock has expired, reset lock status and return False
            self.reset_failed_attempts()
            return False

        # Return True if still locked, False otherwise
        return True

    def to_dict(self, include_sensitive: bool = False) -> Dict:
        """
        Converts user model to dictionary excluding sensitive data.
        """
        # Get base dictionary from parent class method
        user_dict = super().to_dict()

        # If not include_sensitive, remove password_hash, password_history, etc.
        if not include_sensitive:
            sensitive_fields = ["password_hash", "password_history", "verification_token", "reset_token", "mfa_secret"]
            for field in sensitive_fields:
                if field in user_dict:
                    del user_dict[field]

        return user_dict

    def generate_auth_tokens(self) -> Dict:
        """
        Generates authentication tokens for the user.
        """
        # Create user data dict with id, email, roles, etc.
        user_data = {
            "user_id": str(self.get_id()),
            "email": self._data.get("email"),
            "roles": self._data.get("roles", [])
        }

        # Generate access token using generate_access_token
        access_token = generate_access_token(user_data)

        # Generate refresh token using generate_refresh_token
        refresh_token = generate_refresh_token(str(self.get_id()))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def save(self) -> ObjectId:
        """
        Saves the user document to the database.
        """
        # If new user, set created_at timestamp
        if self._is_new:
            self._data["created_at"] = datetime.datetime.utcnow()

        # Update updated_at timestamp
        self._data["updated_at"] = datetime.datetime.utcnow()

        # Call parent class save method
        return super().save()


class UserSchema:
    """
    Schema for validating user data.
    """

    schema: Dict = {
        "email": {"type": "str", "required": True},
        "password": {"type": "str", "required": True},
        "firstName": {"type": "str", "required": True},
        "lastName": {"type": "str", "required": True}
    }

    def __init__(self):
        """
        Initialize the user schema.
        """
        pass

    def validate(self, data: Dict) -> bool:
        """
        Validates user data against schema.
        """
        # Check required fields
        if not all(key in data for key in self.schema if self.schema[key].get("required")):
            return False

        # Validate field types and formats
        # (Implementation specific to validation library)
        return True


def create_user(user_data: Dict) -> User:
    """
    Creates a new user with validated data and default role.
    """
    # Validate required fields (email, password, firstName, lastName)
    if not all(key in user_data for key in ["email", "password", "firstName", "lastName"]):
        raise ValueError("Missing required fields")

    # Validate email format using validate_email
    validate_email(user_data["email"])

    # Validate password strength using validate_password_strength
    validate_password_strength(user_data["password"])

    # Check if user with email already exists
    existing_user = get_user_by_email(user_data["email"])
    if existing_user:
        raise ValueError("User with this email already exists")

    # Create new User instance with provided data
    user = User(data={
        "email": user_data["email"],
        "firstName": user_data["firstName"],
        "lastName": user_data["lastName"]
    })

    # Assign default user role
    user.add_role(DEFAULT_USER_ROLE)

    # Hash password before storing
    user.set_password(user_data["password"])

    # Generate email verification token
    user.generate_verification_token()

    # Save user to database
    user.save()

    # Return the created user instance
    return user


def get_user_by_id(user_id: Union[str, ObjectId]) -> Optional[User]:
    """
    Retrieves a user by their ID.
    """
    # Convert string ID to ObjectId if necessary
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            return None

    # Query database for user with matching ID
    user = User.find_by_id(user_id)

    # Return User instance if found, None otherwise
    return user


def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieves a user by their email address.
    """
    # Normalize email (lowercase)
    email = email.lower()

    # Query database for user with matching email
    user = User.find_one({"email": email})

    # Return User instance if found, None otherwise
    return user


def authenticate_user(email: str, password: str) -> Dict:
    """
    Authenticates a user by email and password.
    """
    # Normalize email (lowercase)
    email = email.lower()

    # Retrieve user by email
    user = get_user_by_email(email)
    if not user:
        raise AuthenticationError("Invalid credentials")

    # Check if account is locked due to failed attempts
    if user.is_account_locked():
        raise AuthenticationError("Account is temporarily locked")

    # Verify provided password against stored hash
    if not user.check_password(password):
        # Increment failed attempts
        user.increment_failed_attempts()
        raise AuthenticationError("Invalid credentials")

    # If password correct, reset failed attempts counter
    user.reset_failed_attempts()

    # Check if email verification is required but not completed
    if not user._data.get("email_verified", False):
        raise AuthenticationError("Email verification required")

    # Generate access and refresh tokens
    auth_tokens = user.generate_auth_tokens()

    # Update last login timestamp
    user.save()

    # Return authentication result with tokens and user data
    return auth_tokens