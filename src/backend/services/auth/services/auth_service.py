"""
Core authentication service that provides comprehensive user authentication,
token management, and account operations. Implements user registration, login,
token issuance, MFA, password reset, and session management features.
"""

import datetime
from typing import Dict, Optional

import bson  # pymongo v4.3.3
import secrets  # standard library

from src.backend.common.auth.jwt_utils import (
    validate_access_token,
    validate_refresh_token,
    refresh_access_token,
    blacklist_token,
    get_token_identity,
    get_redis_client,
)
from src.backend.common.exceptions.api_exceptions import (
    AuthenticationError,
    InvalidInputError,
)
from src.backend.common.logging.logger import get_logger
from src.backend.common.utils.security import (
    hash_password,
    generate_secure_token,
    validate_password_strength,
)
from src.backend.services.auth.models.user import (
    User,
    create_user,
    get_user_by_id,
    get_user_by_email,
    authenticate_user,
)
from src.backend.services.auth.models.role import (
    get_role_by_name,
    create_default_roles,
    SYSTEM_ROLES,
)
from src.backend.common.events.event_bus import (
    get_event_bus_instance,
    create_event,
)

# Initialize logger
logger = get_logger(__name__)

# Session expiry time (24 hours in seconds)
SESSION_EXPIRY = 86400

# MFA code expiry time (10 minutes in seconds)
MFA_CODE_EXPIRY = 600

# Authentication event types
AUTH_EVENT_TYPES = {
    "registered": "auth.user.registered",
    "login": "auth.user.login",
    "logout": "auth.user.logout",
    "failed_login": "auth.user.failed_login",
    "password_reset": "auth.user.password_reset",
    "email_verified": "auth.user.email_verified",
    "mfa_enabled": "auth.user.mfa_enabled",
}


def register_user(user_data: Dict) -> Dict:
    """Registers a new user in the system.

    Args:
        user_data: Dictionary containing user registration information.

    Returns:
        New user data with verification token.
    """
    try:
        # Validate required user fields (email, password, firstName, lastName)
        if not all(
            key in user_data for key in ["email", "password", "firstName", "lastName"]
        ):
            raise InvalidInputError("Missing required fields for registration")

        # Validate password strength using validate_password_strength
        validate_password_strength(user_data["password"])

        # Check if user already exists with the same email
        if get_user_by_email(user_data["email"]):
            raise InvalidInputError("User with this email already exists")

        # Create new user with create_user function
        user = create_user(user_data)

        # Ensure default roles exist by calling create_default_roles
        create_default_roles()

        # Generate email verification token
        verification_token = user.generate_verification_token()

        # Publish user.registered event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["registered"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["registered"], event)

        # Return user data with verification token for email delivery
        return {
            "user_id": str(user.get_id()),
            "email": user.get("email"),
            "firstName": user.get("firstName"),
            "lastName": user.get("lastName"),
            "verification_token": verification_token,
        }
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise


def verify_email(user_id: str, token: str) -> bool:
    """Verifies a user's email address using a verification token.

    Args:
        user_id: The ID of the user to verify.
        token: The verification token.

    Returns:
        True if verification successful, False otherwise.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Verify the token using user.verify_email method
        if not user.verify_email(token):
            return False

        # If verified, publish email_verified event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["email_verified"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["email_verified"], event)

        # Save the user to persist the email verification
        user.save()

        return True
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        raise


def login(email: str, password: str) -> Dict:
    """Authenticates a user and issues access and refresh tokens.

    Args:
        email: The user's email address.
        password: The user's password.

    Returns:
        Authentication result with tokens and user data.
    """
    try:
        # Normalize email (convert to lowercase)
        email = email.lower()

        # Get user by email
        user = get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Check if account is locked
        if user.is_account_locked():
            raise AuthenticationError("Account is temporarily locked")

        # Verify password using user.check_password
        if not user.check_password(password):
            # Increment failed attempts and possibly lock account
            user.increment_failed_attempts()
            raise AuthenticationError("Invalid credentials")

        # If password correct, reset failed attempts counter
        user.reset_failed_attempts()

        # Check if email verification is required but not completed
        if not user._data.get("email_verified", False):
            raise AuthenticationError("Email verification required")

        # Check if MFA is enabled for the user
        if user._data.get("mfa_enabled"):
            # If MFA enabled, return MFA challenge
            mfa_token = generate_secure_token()
            redis_client = get_redis_client()
            redis_client.setex(
                f"mfa_token:{user.get_id()}", MFA_CODE_EXPIRY, mfa_token
            )  # Store token in Redis
            return {"mfa_required": True, "mfa_token": mfa_token, "user_id": str(user.get_id())}
        else:
            # If no MFA, generate authentication tokens
            auth_tokens = user.generate_auth_tokens()

            # Store session data in Redis with expiry
            redis_client = get_redis_client()
            redis_client.setex(
                f"session:{user.get_id()}", SESSION_EXPIRY, "active"
            )  # Example session data

            # Publish login event
            event_bus = get_event_bus_instance()
            event = create_event(
                event_type=AUTH_EVENT_TYPES["login"],
                payload={"user_id": str(user.get_id()), "email": user.get("email")},
                source="auth_service",
            )
            event_bus.publish(AUTH_EVENT_TYPES["login"], event)

            # Return authentication result with tokens and user data
            return {
                "access_token": auth_tokens["access_token"],
                "refresh_token": auth_tokens["refresh_token"],
                "user": user.to_dict(),
            }
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        raise


def verify_mfa(user_id: str, mfa_code: str, mfa_token: str) -> Dict:
    """Verifies MFA code and completes the authentication process.

    Args:
        user_id: The ID of the user to verify.
        mfa_code: The multi-factor authentication code.
        mfa_token: The MFA token from login

    Returns:
        Authentication result with tokens and user data.
    """
    try:
        # Validate MFA token from Redis
        redis_client = get_redis_client()
        stored_mfa_token = redis_client.get(f"mfa_token:{user_id}")
        if not stored_mfa_token or stored_mfa_token != mfa_token:
            raise AuthenticationError("Invalid MFA token")

        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Verify MFA code using user.verify_mfa method
        if not user.verify_mfa(mfa_code):
            raise AuthenticationError("Invalid MFA code")

        # If valid, generate authentication tokens
        auth_tokens = user.generate_auth_tokens()

        # Delete MFA token from Redis
        redis_client.delete(f"mfa_token:{user_id}")

        # Store session data in Redis
        redis_client.setex(
            f"session:{user.get_id()}", SESSION_EXPIRY, "active"
        )  # Example session data

        # Publish login event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["login"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["login"], event)

        # Return authentication result with tokens and user data
        return {
            "access_token": auth_tokens["access_token"],
            "refresh_token": auth_tokens["refresh_token"],
            "user": user.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error verifying MFA: {str(e)}")
        raise


def logout(access_token: str, refresh_token: str) -> bool:
    """Logs out a user by invalidating their tokens.

    Args:
        access_token: The user's access token.
        refresh_token: The user's refresh token.

    Returns:
        True if logout successful.
    """
    try:
        # Validate access token
        payload = validate_access_token(access_token)

        # Extract user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError("Invalid token: missing user identity")

        # Blacklist both access and refresh tokens
        jti_access = get_token_jti(access_token)
        jti_refresh = get_token_jti(refresh_token)

        jwt_config = get_jwt_config()
        access_token_expiry = jwt_config.get("ACCESS_TOKEN_EXPIRES").total_seconds()
        refresh_token_expiry = jwt_config.get("REFRESH_TOKEN_EXPIRES").total_seconds()

        blacklist_token(access_token, int(access_token_expiry))
        blacklist_token(refresh_token, int(refresh_token_expiry))

        # Remove session data from Redis
        redis_client = get_redis_client()
        redis_client.delete(f"session:{user_id}")

        # Publish logout event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["logout"],
            payload={"user_id": user_id},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["logout"], event)

        return True
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
        raise


def refresh_token(refresh_token: str) -> Dict:
    """Refreshes an access token using a valid refresh token.

    Args:
        refresh_token: The refresh token to use.

    Returns:
        New token pair (access and refresh).
    """
    try:
        # Validate the refresh token
        payload = validate_refresh_token(refresh_token)

        # Use refresh_access_token function to generate new token pair
        new_tokens = refresh_access_token(refresh_token)

        return new_tokens
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise


def forgot_password(email: str) -> Dict:
    """Initiates the password reset process.

    Args:
        email: The user's email address.

    Returns:
        Reset token information for email delivery.
    """
    try:
        # Normalize email
        email = email.lower()

        # Get user by email
        user = get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email address")

        # Generate password reset token using user.generate_password_reset_token
        reset_token = user.generate_password_reset_token()

        # Return reset token information for email delivery
        return {
            "user_id": str(user.get_id()),
            "email": user.get("email"),
            "reset_token": reset_token,
        }
    except Exception as e:
        logger.error(f"Error initiating password reset: {str(e)}")
        raise


def reset_password(user_id: str, token: str, new_password: str) -> bool:
    """Resets a user's password using a valid reset token.

    Args:
        user_id: The ID of the user to reset the password for.
        token: The password reset token.
        new_password: The new password to set.

    Returns:
        True if reset successful, False otherwise.
    """
    try:
        # Validate new password strength
        validate_password_strength(new_password)

        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Reset password using user.reset_password method
        if not user.reset_password(token, new_password):
            return False

        # If successful, publish password_reset event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["password_reset"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["password_reset"], event)

        # Invalidate all existing tokens for the user
        invalidate_user_sessions(user_id)

        # Save the user to persist the password reset
        user.save()

        return True
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Changes a user's password with current password verification.

    Args:
        user_id: The ID of the user to change the password for.
        current_password: The user's current password.
        new_password: The new password to set.

    Returns:
        True if change successful, False otherwise.
    """
    try:
        # Validate new password strength
        validate_password_strength(new_password)

        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Verify current password
        if not user.check_password(current_password):
            raise AuthenticationError("Invalid current password")

        # If verified, set new password
        user.set_password(new_password)

        # Invalidate all existing tokens for the user
        invalidate_user_sessions(user_id)

        # Publish password_reset event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["password_reset"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["password_reset"], event)

        # Save the user to persist the password change
        user.save()

        return True
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise


def get_profile(user_id: str) -> Dict:
    """Retrieves a user's profile data.

    Args:
        user_id: The ID of the user to retrieve.

    Returns:
        User profile data.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Convert user to dictionary excluding sensitive data
        user_profile = user.to_dict(include_sensitive=False)

        # Return user profile data
        return user_profile
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise


def update_profile(user_id: str, profile_data: Dict) -> Dict:
    """Updates a user's profile information.

    Args:
        user_id: The ID of the user to update.
        profile_data: The profile data to update.

    Returns:
        Updated user profile.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Validate profile data fields
        # (Add validation logic here based on allowed fields)

        # Update allowed fields (firstName, lastName, settings, etc.)
        if "firstName" in profile_data:
            user._data["firstName"] = profile_data["firstName"]
        if "lastName" in profile_data:
            user._data["lastName"] = profile_data["lastName"]
        if "settings" in profile_data:
            user._data["settings"] = profile_data["settings"]

        # Save changes to database
        user.save()

        # Return updated profile
        return user.to_dict(include_sensitive=False)
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise


def setup_mfa(user_id: str, mfa_method: str) -> Dict:
    """Sets up multi-factor authentication for a user.

    Args:
        user_id: The ID of the user to set up MFA for.
        mfa_method: The MFA method to use (totp, sms, email).

    Returns:
        MFA setup information.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Validate MFA method (totp, sms, email)
        if mfa_method not in ["totp", "sms", "email"]:
            raise InvalidInputError("Invalid MFA method")

        # Enable MFA for user with specified method
        config_data = user.enable_mfa(mfa_method)

        # Store temporary verification state in Redis
        redis_client = get_redis_client()
        setup_token = generate_secure_token()
        redis_client.setex(
            f"mfa_setup:{user.get_id()}", MFA_CODE_EXPIRY, setup_token
        )  # Store setup token in Redis

        # Save the user to persist the MFA setup
        user.save()

        # Return setup information (QR code for TOTP, etc.)
        return {"setup_token": setup_token, "config_data": config_data}
    except Exception as e:
        logger.error(f"Error setting up MFA: {str(e)}")
        raise


def confirm_mfa_setup(user_id: str, code: str, setup_token: str) -> bool:
    """Confirms MFA setup by verifying a code.

    Args:
        user_id: The ID of the user to confirm MFA setup for.
        code: The MFA code to verify.
        setup_token: The setup token from setup_mfa.

    Returns:
        True if MFA setup confirmed.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Validate setup token from Redis
        redis_client = get_redis_client()
        stored_setup_token = redis_client.get(f"mfa_setup:{user.get_id()}")
        if not stored_setup_token or stored_setup_token != setup_token:
            raise AuthenticationError("Invalid setup token")

        # Verify MFA code
        if not user.verify_mfa(code):
            raise AuthenticationError("Invalid MFA code")

        # If valid, finalize MFA setup
        user.confirm_mfa_setup()

        # Remove setup token from Redis
        redis_client.delete(f"mfa_setup:{user.get_id()}")

        # Publish mfa_enabled event
        event_bus = get_event_bus_instance()
        event = create_event(
            event_type=AUTH_EVENT_TYPES["mfa_enabled"],
            payload={"user_id": str(user.get_id()), "email": user.get("email")},
            source="auth_service",
        )
        event_bus.publish(AUTH_EVENT_TYPES["mfa_enabled"], event)

        # Save the user to persist the MFA confirmation
        user.save()

        return True
    except Exception as e:
        logger.error(f"Error confirming MFA setup: {str(e)}")
        raise


def disable_mfa(user_id: str, password: str) -> bool:
    """Disables multi-factor authentication for a user.

    Args:
        user_id: The ID of the user to disable MFA for.
        password: The user's password for verification.

    Returns:
        True if MFA disabled successfully.
    """
    try:
        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Verify password for security
        if not user.check_password(password):
            raise AuthenticationError("Invalid password")

        # Disable MFA using user.disable_mfa method
        user.disable_mfa()

        # Save the user to persist the MFA disabling
        user.save()

        return True
    except Exception as e:
        logger.error(f"Error disabling MFA: {str(e)}")
        raise


def validate_token(token: str) -> Dict:
    """Validates an access token and returns the associated user data.

    Args:
        token: The access token to validate.

    Returns:
        User data associated with the token.
    """
    try:
        # Validate the access token
        payload = validate_access_token(token)

        # Extract user ID from token
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError("Invalid token: missing user identity")

        # Get user by ID
        user = get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("Invalid user ID")

        # Return user data
        return user.to_dict()
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise


def invalidate_user_sessions(user_id: str) -> bool:
    """Invalidates all active sessions for a user.

    Args:
        user_id: The ID of the user whose sessions to invalidate.

    Returns:
        True if sessions invalidated successfully.
    """
    try:
        # Get all session keys for the user from Redis
        redis_client = get_redis_client()
        session_keys = redis_client.keys(f"session:{user_id}")

        # Delete all session data
        if session_keys:
            redis_client.delete(*session_keys)

        return True
    except Exception as e:
        logger.error(f"Error invalidating user sessions: {str(e)}")
        return False


def get_active_sessions(user_id: str) -> List:
    """Retrieves all active sessions for a user.

    Args:
        user_id: The ID of the user to retrieve sessions for.

    Returns:
        List of active sessions with metadata.
    """
    try:
        # Get all session keys for the user from Redis
        redis_client = get_redis_client()
        session_keys = redis_client.keys(f"session:{user_id}")

        # Retrieve session data for each key
        sessions = []
        for key in session_keys:
            session_data = redis_client.get(key)
            if session_data:
                # Format session information (device, IP, last active)
                sessions.append({"session_id": key, "data": session_data})

        return sessions
    except Exception as e:
        logger.error(f"Error retrieving active sessions: {str(e)}")
        return []