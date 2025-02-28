"""
Utility functions for security-related operations.

This module provides functions for password hashing, encryption, and secure token generation.
These utilities form the foundation of the system's security infrastructure.
"""

# Standard library imports
import os
import re
import secrets
import hashlib
import base64
import time
from datetime import datetime, timedelta

# Third-party imports
import bcrypt  # v4.0.x
import bleach  # v6.0.x
from cryptography.fernet import Fernet  # v41.0.x

# Constants
SALT_ROUNDS = 12  # Number of rounds for bcrypt password hashing
PASSWORD_MIN_LENGTH = 8  # Minimum password length
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'  # Pattern for password validation
TOKEN_BYTES = 32  # Number of bytes for secure token generation


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt with appropriate salt rounds.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        Hashed password string
    """
    # Generate salt using bcrypt with SALT_ROUNDS
    salt = bcrypt.gensalt(rounds=SALT_ROUNDS)
    
    # Hash password with the generated salt
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Return the hashed password as a UTF-8 string
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a hashed password.
    
    Args:
        password: The plain text password to verify
        hashed_password: The hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    # Use bcrypt.checkpw to verify if the password matches the hash
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_secure_token(bytes_length: int = TOKEN_BYTES) -> str:
    """
    Generates a cryptographically secure random token for secure operations.
    
    Args:
        bytes_length: Length of the token in bytes (default: TOKEN_BYTES)
        
    Returns:
        Secure random token string
    """
    # Use secrets.token_urlsafe to generate a secure URL-safe token
    return secrets.token_urlsafe(bytes_length)


def generate_key() -> bytes:
    """
    Generates a cryptographic key for encryption operations.
    
    Returns:
        Cryptographic key for encryption
    """
    # Use Fernet.generate_key() to create a secure symmetric encryption key
    return Fernet.generate_key()


def encrypt_data(data: str, key: bytes) -> str:
    """
    Encrypts sensitive data using AES-256-GCM via Fernet.
    
    Args:
        data: The data to encrypt
        key: The encryption key to use
        
    Returns:
        Encrypted data as a base64 string
    """
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Initialize Fernet with the provided key
    fernet = Fernet(key)
    
    # Encrypt the data using fernet.encrypt()
    encrypted_data = fernet.encrypt(data)
    
    # Return the encrypted data as a base64-encoded string
    return encrypted_data.decode('utf-8')


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """
    Decrypts encrypted data using AES-256-GCM via Fernet.
    
    Args:
        encrypted_data: The encrypted data to decrypt
        key: The encryption key to use
        
    Returns:
        Decrypted data as a string
    """
    # Convert encrypted_data to bytes if it's a string
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode('utf-8')
    
    # Initialize Fernet with the provided key
    fernet = Fernet(key)
    
    # Decrypt the data using fernet.decrypt()
    decrypted_data = fernet.decrypt(encrypted_data)
    
    # Return the decrypted data as a string
    return decrypted_data.decode('utf-8')


def sanitize_html(html_content: str, allowed_tags: list = None) -> str:
    """
    Sanitizes HTML content to prevent XSS attacks.
    
    Args:
        html_content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: None)
        
    Returns:
        Sanitized HTML content
    """
    # Default allowed tags if none specified
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'p', 'br', 'a', 'span', 'div', 'ul', 'ol', 'li']
    
    # Default allowed attributes
    allowed_attrs = {
        'a': ['href', 'title', 'target'],
        'span': ['class'],
        'div': ['class'],
        '*': ['class']
    }
    
    # Use bleach.clean() to remove potentially dangerous HTML
    sanitized = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    
    # Return the sanitized HTML content
    return sanitized


def validate_password_strength(password: str) -> bool:
    """
    Validates the strength of a password against security policy requirements.
    
    Args:
        password: The password to validate
        
    Returns:
        True if password meets strength requirements, False otherwise
    """
    # Check password length against PASSWORD_MIN_LENGTH
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    
    # Use regex to verify password contains uppercase, lowercase, number, and special characters
    if not re.match(PASSWORD_PATTERN, password):
        return False
    
    # Return True if all criteria are met
    return True


def generate_csrf_token(session_id: str) -> str:
    """
    Generates a CSRF token for form protection.
    
    Args:
        session_id: The session ID to associate with the token
        
    Returns:
        CSRF token string
    """
    # Generate a random token using secrets.token_hex()
    random_token = secrets.token_hex(16)
    
    # Get current timestamp
    timestamp = int(time.time())
    
    # Combine with session_id and timestamp to create a unique token
    token_data = f"{session_id}:{timestamp}:{random_token}"
    
    # Create a signature to verify the token
    signature = hashlib.sha256(token_data.encode('utf-8')).hexdigest()
    
    # Return the full token as a hexadecimal string
    return f"{timestamp}:{random_token}:{signature}"


def verify_csrf_token(token: str, session_id: str, max_age: int = 3600) -> bool:
    """
    Verifies a CSRF token for form protection.
    
    Args:
        token: The CSRF token to verify
        session_id: The session ID to verify against
        max_age: Maximum age of the token in seconds (default: 3600)
        
    Returns:
        True if token is valid, False otherwise
    """
    # Verify the token format and components
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        
        timestamp_str, random_token, provided_signature = parts
        timestamp = int(timestamp_str)
        
        # Check if the token has expired based on max_age
        current_time = int(time.time())
        if current_time - timestamp > max_age:
            return False
        
        # Recreate the token data
        token_data = f"{session_id}:{timestamp}:{random_token}"
        
        # Verify the signature
        expected_signature = hashlib.sha256(token_data.encode('utf-8')).hexdigest()
        
        # Return True if valid, False otherwise
        return secrets.compare_digest(provided_signature, expected_signature)
    except (ValueError, TypeError):
        return False


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Masks sensitive data for logging and display purposes.
    
    Args:
        data: The sensitive data to mask
        visible_chars: Number of characters to leave visible (default: 4)
        
    Returns:
        Masked data string
    """
    # Validate inputs
    if not data or len(data) <= visible_chars:
        return data
    
    # Determine how many characters to mask
    mask_length = len(data) - visible_chars
    
    # Keep the specified number of visible characters
    visible_part = data[-visible_chars:] if visible_chars > 0 else ""
    
    # Replace remaining characters with asterisks
    masked_part = '*' * mask_length
    
    # Return the masked string
    return masked_part + visible_part


def generate_random_password(length: int = 12) -> str:
    """
    Generates a secure random password that meets strength requirements.
    
    Args:
        length: Length of the password (default: 12)
        
    Returns:
        Random password string
    """
    # Ensure length is at least PASSWORD_MIN_LENGTH
    if length < PASSWORD_MIN_LENGTH:
        length = PASSWORD_MIN_LENGTH
    
    # Define character sets
    uppercase_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # Excluding similar looking characters
    lowercase_chars = "abcdefghijkmnopqrstuvwxyz"  # Excluding similar looking characters
    digit_chars = "23456789"  # Excluding 0 and 1 which look like O and l
    special_chars = "@$!%*?&"
    
    # Ensure at least one of each type
    password = [
        secrets.choice(uppercase_chars),
        secrets.choice(lowercase_chars),
        secrets.choice(digit_chars),
        secrets.choice(special_chars)
    ]
    
    # Fill remaining characters
    all_chars = uppercase_chars + lowercase_chars + digit_chars + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle the password characters
    secrets.SystemRandom().shuffle(password)
    
    # Convert to string
    password_str = ''.join(password)
    
    # Verify it meets password strength requirements
    if not validate_password_strength(password_str):
        # Recursively try again if requirements aren't met (unlikely but possible)
        return generate_random_password(length)
    
    # Return the generated password
    return password_str