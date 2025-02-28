"""
JWT (JSON Web Token) utilities for the Task Management System.

This module provides functions for creating, validating, and managing JWTs
for user authentication and authorization. It implements:

1. Token generation for access and refresh tokens
2. Token validation and decoding
3. Token blacklisting for revocation
4. Token refresh workflow with automatic rotation
5. Utilities for extracting token information

The implementation uses RS256 signing by default and supports token blacklisting
through Redis for enhanced security.
"""

import jwt
from datetime import datetime, timedelta
import uuid
from typing import Dict, Optional, Any, Union

from ..config import get_config
from ..database.redis.connection import get_redis_client
from ..exceptions.api_exceptions import AuthenticationError, TokenError
from ..logging.logger import get_logger

# Set up module logger
logger = get_logger(__name__)

# Prefix for blacklisted token keys in Redis
BLACKLIST_KEY_PREFIX = "blacklisted_token:"


def get_jwt_config() -> Dict[str, Any]:
    """
    Gets JWT configuration from application config.
    
    Returns:
        dict: JWT configuration dictionary
    """
    config = get_config()
    jwt_settings = getattr(config, "JWT_SETTINGS", {})
    
    # Default values if not specified in config
    defaults = {
        "SECRET_KEY": getattr(config, "SECRET_KEY", None),
        "PUBLIC_KEY": getattr(config, "PUBLIC_KEY", None),
        "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
        "REFRESH_TOKEN_EXPIRE_DAYS": 7,
        "ALGORITHM": "RS256",
        "BLACKLIST_ENABLED": True
    }
    
    # Merge defaults with config values
    for key, value in defaults.items():
        if key not in jwt_settings:
            jwt_settings[key] = value
    
    return jwt_settings


def generate_access_token(user_data: Dict[str, Any]) -> str:
    """
    Generates a new JWT access token for a user.
    
    Args:
        user_data: Dictionary containing user information
        
    Returns:
        Encoded JWT access token
    """
    # Create a copy of the user data to avoid modifying the original
    payload = user_data.copy()
    
    # Get JWT configuration
    jwt_config = get_jwt_config()
    
    # Generate a unique JWT ID (jti)
    jti = str(uuid.uuid4())
    
    # Calculate expiration time
    now = datetime.utcnow()
    expiration = now + timedelta(minutes=jwt_config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    
    # Update payload with token metadata
    payload.update({
        "jti": jti,                # JWT ID
        "exp": expiration,         # Expiration time
        "iat": now,                # Issued at time
    })
    
    # Encode the token
    token = jwt.encode(
        payload,
        jwt_config.get("SECRET_KEY"),
        algorithm=jwt_config.get("ALGORITHM", "RS256")
    )
    
    logger.debug(f"Generated access token with jti: {jti} for user: {payload.get('user_id', 'unknown')}")
    return token


def generate_refresh_token(user_id: str) -> str:
    """
    Generates a new refresh token for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Encoded JWT refresh token
    """
    # Get JWT configuration
    jwt_config = get_jwt_config()
    
    # Generate a unique JWT ID (jti)
    jti = str(uuid.uuid4())
    
    # Calculate expiration time
    now = datetime.utcnow()
    expiration = now + timedelta(days=jwt_config.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # Create payload with user ID and token metadata
    payload = {
        "user_id": user_id,
        "jti": jti,                # JWT ID
        "exp": expiration,         # Expiration time
        "iat": now,                # Issued at time
        "type": "refresh"          # Token type
    }
    
    # Encode the token
    token = jwt.encode(
        payload,
        jwt_config.get("SECRET_KEY"),
        algorithm=jwt_config.get("ALGORITHM", "RS256")
    )
    
    logger.debug(f"Generated refresh token with jti: {jti} for user: {user_id}")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenError: If token is invalid or expired
    """
    # Get JWT configuration
    jwt_config = get_jwt_config()
    
    try:
        # Determine the key to use for verification
        verification_key = jwt_config.get("PUBLIC_KEY") if jwt_config.get("ALGORITHM") == "RS256" else jwt_config.get("SECRET_KEY")
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            verification_key,
            algorithms=[jwt_config.get("ALGORITHM", "RS256")],
            options={"verify_exp": True}
        )
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise TokenError("Token has expired")
    
    except jwt.InvalidSignatureError:
        logger.warning("Invalid token signature")
        raise TokenError("Invalid token signature")
    
    except jwt.DecodeError:
        logger.warning("Token could not be decoded")
        raise TokenError("Token could not be decoded")
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise TokenError(f"Invalid token: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        raise TokenError(f"Token validation failed: {str(e)}")


def validate_access_token(token: str) -> Dict[str, Any]:
    """
    Validates an access token and returns the payload if valid.
    
    Args:
        token: JWT access token to validate
        
    Returns:
        Validated token payload
        
    Raises:
        AuthenticationError: If token is invalid or blacklisted
    """
    try:
        # Decode the token
        payload = decode_token(token)
        
        # Check if it's a refresh token (access tokens shouldn't have this type)
        if payload.get("type") == "refresh":
            logger.warning("Invalid token type: using refresh token as access token")
            raise AuthenticationError("Invalid token type")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Token with jti {jti} has been revoked")
            raise AuthenticationError("Token has been revoked")
        
        return payload
    
    except TokenError as e:
        # Convert TokenError to AuthenticationError with original message
        raise AuthenticationError(str(e))


def validate_refresh_token(token: str) -> Dict[str, Any]:
    """
    Validates a refresh token and returns the payload if valid.
    
    Args:
        token: JWT refresh token to validate
        
    Returns:
        Validated token payload
        
    Raises:
        AuthenticationError: If token is invalid or blacklisted
    """
    try:
        # Decode the token
        payload = decode_token(token)
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type: expecting refresh token")
            raise AuthenticationError("Invalid token type")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Refresh token with jti {jti} has been revoked")
            raise AuthenticationError("Token has been revoked")
        
        return payload
    
    except TokenError as e:
        # Convert TokenError to AuthenticationError with original message
        raise AuthenticationError(str(e))


def blacklist_token(token: str, expires_in: int) -> bool:
    """
    Adds a token to the blacklist in Redis.
    
    Args:
        token: JWT token to blacklist
        expires_in: Time in seconds until token expiration
        
    Returns:
        True if token was successfully blacklisted
    """
    try:
        # Extract JTI from token
        jti = get_token_jti(token)
        
        # Get Redis client
        redis_client = get_redis_client()
        
        # Create blacklist key
        blacklist_key = f"{BLACKLIST_KEY_PREFIX}{jti}"
        
        # Add to Redis with expiration time
        redis_client.set(blacklist_key, "1", ex=expires_in)
        
        logger.info(f"Token with jti {jti} blacklisted for {expires_in} seconds")
        return True
    
    except TokenError as e:
        logger.error(f"Error blacklisting token - invalid token: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error blacklisting token - unexpected error: {str(e)}")
        return False


def is_token_blacklisted(token_jti: str) -> bool:
    """
    Checks if a token is in the blacklist.
    
    Args:
        token_jti: JWT ID to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    try:
        # Get Redis client
        redis_client = get_redis_client()
        
        # Create blacklist key
        blacklist_key = f"{BLACKLIST_KEY_PREFIX}{token_jti}"
        
        # Check if key exists in Redis
        is_blacklisted = redis_client.exists(blacklist_key)
        
        return bool(is_blacklisted)
    
    except Exception as e:
        logger.error(f"Error checking token blacklist: {str(e)}")
        return False  # Fail-safe approach: if there's an error, assume not blacklisted


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Creates a new access token using a valid refresh token.
    
    Args:
        refresh_token: Refresh token to use
        
    Returns:
        Dictionary containing new access_token and refresh_token
        
    Raises:
        AuthenticationError: If refresh token is invalid
    """
    # Validate the refresh token
    payload = validate_refresh_token(refresh_token)
    
    # Extract user ID from payload
    user_id = payload.get("user_id")
    if not user_id:
        raise AuthenticationError("Invalid refresh token: missing user identity")
    
    # Calculate token expiration for blacklisting
    exp = payload.get("exp")
    now = datetime.utcnow().timestamp()  # Current time as timestamp
    
    # Calculate seconds until expiration (or use default if exp not available)
    expires_in = max(0, int(exp - now)) if exp else (60 * 60 * 24 * 7)  # 7 days in seconds
    
    # Blacklist the used refresh token for security (token rotation)
    blacklist_token(refresh_token, expires_in)
    
    # Generate new tokens
    new_access_token = generate_access_token({"user_id": user_id})
    new_refresh_token = generate_refresh_token(user_id)
    
    logger.info(f"Refreshed tokens for user {user_id}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }


def get_token_identity(token: str) -> str:
    """
    Extracts the user identity from a token.
    
    Args:
        token: JWT token
        
    Returns:
        User ID extracted from token
        
    Raises:
        AuthenticationError: If user identity is not found
    """
    # Decode the token
    payload = decode_token(token)
    
    # Extract user ID
    user_id = payload.get("user_id")
    if not user_id:
        raise AuthenticationError("Invalid token: missing user identity")
    
    return user_id


def get_token_jti(token: str) -> str:
    """
    Extracts the JWT ID (jti) from a token.
    
    Args:
        token: JWT token
        
    Returns:
        JWT ID (jti) extracted from token
        
    Raises:
        TokenError: If JTI is not found
    """
    # Decode the token
    payload = decode_token(token)
    
    # Extract JTI
    jti = payload.get("jti")
    if not jti:
        raise TokenError("Invalid token: missing jti")
    
    return jti


def extract_token_from_header(auth_header: str) -> Optional[str]:
    """
    Extracts JWT token from the Authorization header.
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        Extracted token or None if not found
    """
    if not auth_header or not auth_header.strip():
        return None
    
    # Check for Bearer token
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()
        return token
    
    return None