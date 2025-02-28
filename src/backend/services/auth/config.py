"""
Authentication Service Configuration Module

This module provides configuration classes for the Authentication Service,
extending the base application configuration with authentication-specific settings.
It selects the appropriate configuration based on the deployment environment.
"""

import os
import logging
from typing import Dict, Any

# Import base configuration classes
from common.config.base import BaseConfig
from common.config.development import DevelopmentConfig
from common.config.production import ProductionConfig
from common.config.testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Get environment from environment variable with fallback to development
ENV = os.environ.get('FLASK_ENV', 'development')


class AuthConfig(BaseConfig):
    """
    Authentication service specific configuration that extends the base configuration
    with authentication-specific settings.
    """

    def __init__(self):
        """
        Initialize the Auth configuration with default values.
        """
        # Initialize base config
        super().__init__()
        
        # Set service name
        self.AUTH_SERVICE_NAME = 'auth'
        
        # Password policy configuration
        self.PASSWORD_POLICY = {
            'min_length': 10,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'max_attempts': 5,
            'history_limit': 10,
            'max_age_days': 90
        }
        
        # Token settings
        self.TOKEN_SETTINGS = {
            'access_token_lifetime_minutes': 15,
            'refresh_token_lifetime_days': 7,
            'algorithm': 'HS256',
            'token_bytes': 32,
            'rotation_enabled': True
        }
        
        # Multi-factor authentication settings
        self.MFA_SETTINGS = {
            'enabled': True,
            'methods': ['totp', 'sms', 'email'],
            'default_method': 'totp',
            'totp_issuer': 'TaskManagementSystem',
            'totp_digits': 6,
            'totp_period': 30,
            'verification_expiry_minutes': 10,
            'remember_device_days': 30
        }
        
        # OAuth configuration for external identity providers
        self.OAUTH_SETTINGS = {
            'providers': {
                'google': {
                    'enabled': False,
                    'client_id': '',
                    'client_secret': '',
                    'scopes': ['openid', 'email', 'profile']
                },
                'microsoft': {
                    'enabled': False,
                    'client_id': '',
                    'client_secret': '',
                    'scopes': ['openid', 'email', 'profile', 'offline_access']
                },
                'auth0': {
                    'enabled': False,
                    'domain': '',
                    'client_id': '',
                    'client_secret': '',
                    'audience': ''
                }
            },
            'callback_url': '/api/v1/auth/oauth/callback'
        }
        
        # Session management settings
        self.SESSION_SETTINGS = {
            'inactivity_timeout_minutes': 30,
            'max_concurrent_sessions': 5,
            'extend_session_on_activity': True,
            'strict_ip_matching': False,
            'strict_user_agent_matching': False,
            'session_store': 'redis'
        }
        
        # Authentication rate limits
        self.AUTH_RATE_LIMITS = {
            'login': '10/minute',
            'forgot_password': '5/hour',
            'verify_email': '5/hour',
            'register': '5/hour',
            'reset_password': '5/hour',
            'mfa_verify': '10/minute'
        }

    def get_auth_settings(self) -> Dict[str, Any]:
        """
        Returns authentication-specific settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary of authentication settings
        """
        return {
            'auth_service_name': self.AUTH_SERVICE_NAME,
            'password_policy': self.PASSWORD_POLICY,
            'token_settings': self.TOKEN_SETTINGS,
            'mfa_settings': self.MFA_SETTINGS,
            'oauth_settings': self.OAUTH_SETTINGS,
            'session_settings': self.SESSION_SETTINGS,
            'auth_rate_limits': self.AUTH_RATE_LIMITS
        }


class AuthDevConfig(DevelopmentConfig, AuthConfig):
    """
    Development environment configuration for authentication service.
    Extends both DevelopmentConfig and AuthConfig.
    """

    def __init__(self):
        """
        Initializes the development configuration for auth service.
        """
        # Initialize parent classes
        DevelopmentConfig.__init__(self)
        AuthConfig.__init__(self)
        
        # Override settings for development environment
        # Password policy - less strict for development
        self.PASSWORD_POLICY.update({
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': False,  # Simplified for development
            'max_attempts': 10,  # More attempts for development testing
            'history_limit': 3,  # Fewer remembered passwords for development
            'max_age_days': 180  # Longer password validity for development
        })
        
        # Token settings - longer lifetimes for easier development
        self.TOKEN_SETTINGS.update({
            'access_token_lifetime_minutes': 60,  # 1 hour for development
            'refresh_token_lifetime_days': 30,  # 30 days for development
        })
        
        # Disable MFA by default in development for easier testing
        self.MFA_SETTINGS.update({
            'enabled': False,
            'methods': ['totp', 'email'],  # Limited methods for development
            'default_method': 'email',  # Easier to test with email
        })
        
        # Configure OAuth with development settings
        self.OAUTH_SETTINGS.update({
            'providers': {
                'google': {
                    'enabled': os.environ.get('OAUTH_GOOGLE_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('OAUTH_GOOGLE_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_GOOGLE_CLIENT_SECRET', ''),
                },
                'microsoft': {
                    'enabled': os.environ.get('OAUTH_MS_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('OAUTH_MS_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_MS_CLIENT_SECRET', ''),
                },
                'auth0': {
                    'enabled': os.environ.get('OAUTH_AUTH0_ENABLED', 'False').lower() == 'true',
                    'domain': os.environ.get('OAUTH_AUTH0_DOMAIN', ''),
                    'client_id': os.environ.get('OAUTH_AUTH0_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_AUTH0_CLIENT_SECRET', ''),
                }
            },
            'callback_url': 'http://localhost:5000/api/v1/auth/oauth/callback'
        })
        
        # More relaxed session settings for development
        self.SESSION_SETTINGS.update({
            'inactivity_timeout_minutes': 120,  # 2 hours for development
            'max_concurrent_sessions': 10,  # More concurrent sessions allowed
        })
        
        # Less strict rate limits for development
        self.AUTH_RATE_LIMITS.update({
            'login': '100/minute',
            'forgot_password': '20/hour',
            'verify_email': '20/hour',
            'register': '20/hour',
            'reset_password': '20/hour',
            'mfa_verify': '50/minute'
        })


class AuthProdConfig(ProductionConfig, AuthConfig):
    """
    Production environment configuration for authentication service.
    Extends both ProductionConfig and AuthConfig.
    """

    def __init__(self):
        """
        Initializes the production configuration for auth service.
        """
        # Initialize parent classes
        ProductionConfig.__init__(self)
        AuthConfig.__init__(self)
        
        # Override settings for production environment
        # Strict password policy for production
        self.PASSWORD_POLICY.update({
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'max_attempts': 5,
            'history_limit': 10,
            'max_age_days': 90
        })
        
        # Secure token settings for production
        self.TOKEN_SETTINGS.update({
            'access_token_lifetime_minutes': 15,  # Short-lived tokens for security
            'refresh_token_lifetime_days': 7,
            'rotation_enabled': True
        })
        
        # Enable all MFA options for production
        self.MFA_SETTINGS.update({
            'enabled': True,
            'methods': ['totp', 'sms', 'email'],
            'default_method': 'totp',
            'remember_device_days': 30
        })
        
        # Load production OAuth settings from environment
        self.OAUTH_SETTINGS.update({
            'providers': {
                'google': {
                    'enabled': os.environ.get('OAUTH_GOOGLE_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('OAUTH_GOOGLE_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_GOOGLE_CLIENT_SECRET', ''),
                },
                'microsoft': {
                    'enabled': os.environ.get('OAUTH_MS_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('OAUTH_MS_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_MS_CLIENT_SECRET', ''),
                },
                'auth0': {
                    'enabled': os.environ.get('OAUTH_AUTH0_ENABLED', 'False').lower() == 'true',
                    'domain': os.environ.get('OAUTH_AUTH0_DOMAIN', ''),
                    'client_id': os.environ.get('OAUTH_AUTH0_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OAUTH_AUTH0_CLIENT_SECRET', ''),
                    'audience': os.environ.get('OAUTH_AUTH0_AUDIENCE', '')
                }
            },
            'callback_url': os.environ.get('OAUTH_CALLBACK_URL', 'https://taskmanagement.example.com/api/v1/auth/oauth/callback')
        })
        
        # Strict session settings for production
        self.SESSION_SETTINGS.update({
            'inactivity_timeout_minutes': 30,
            'max_concurrent_sessions': 5,
            'strict_ip_matching': True,
            'strict_user_agent_matching': True
        })
        
        # Standard rate limits for production
        self.AUTH_RATE_LIMITS.update({
            'login': '10/minute',
            'forgot_password': '5/hour',
            'verify_email': '5/hour',
            'register': '5/hour',
            'reset_password': '5/hour',
            'mfa_verify': '10/minute'
        })


class AuthTestConfig(TestingConfig, AuthConfig):
    """
    Testing environment configuration for authentication service.
    Extends both TestingConfig and AuthConfig.
    """

    def __init__(self):
        """
        Initializes the testing configuration for auth service.
        """
        # Initialize parent classes
        TestingConfig.__init__(self)
        AuthConfig.__init__(self)
        
        # Override settings for testing environment
        # Simplified password policy for tests
        self.PASSWORD_POLICY.update({
            'min_length': 8,
            'require_uppercase': False,
            'require_lowercase': False,
            'require_numbers': False,
            'require_special_chars': False,
            'max_attempts': 10,
            'history_limit': 3,
            'max_age_days': 365
        })
        
        # Short-lived tokens for tests
        self.TOKEN_SETTINGS.update({
            'access_token_lifetime_minutes': 5,
            'refresh_token_lifetime_days': 1,
        })
        
        # Simplified MFA for testing
        self.MFA_SETTINGS.update({
            'enabled': True,
            'methods': ['totp', 'email'],
            'default_method': 'email',
            'verification_expiry_minutes': 60
        })
        
        # Mock OAuth providers for testing
        self.OAUTH_SETTINGS.update({
            'providers': {
                'google': {
                    'enabled': True,
                    'client_id': 'test-client-id',
                    'client_secret': 'test-client-secret',
                },
                'microsoft': {
                    'enabled': True,
                    'client_id': 'test-client-id',
                    'client_secret': 'test-client-secret',
                },
                'auth0': {
                    'enabled': True,
                    'domain': 'test.auth0.com',
                    'client_id': 'test-client-id',
                    'client_secret': 'test-client-secret',
                }
            },
            'callback_url': 'http://localhost:5000/api/v1/auth/oauth/callback'
        })
        
        # Session settings for testing
        self.SESSION_SETTINGS.update({
            'inactivity_timeout_minutes': 60,
            'max_concurrent_sessions': 10,
            'strict_ip_matching': False,
            'strict_user_agent_matching': False
        })
        
        # Disable rate limits for testing
        self.AUTH_RATE_LIMITS.update({
            'login': '1000/minute',
            'forgot_password': '1000/hour',
            'verify_email': '1000/hour',
            'register': '1000/hour',
            'reset_password': '1000/hour',
            'mfa_verify': '1000/minute'
        })


# Map of environment names to configuration classes
CONFIG = {
    'development': AuthDevConfig,
    'production': AuthProdConfig,
    'testing': AuthTestConfig
}


def get_config(env=ENV):
    """
    Function to retrieve the appropriate configuration class based on the environment.
    
    Args:
        env (str): Environment name, defaults to FLASK_ENV environment variable
                  or 'development' if not set
    
    Returns:
        object: Configuration class for the specified environment
    """
    # Get the appropriate config class
    config_class = CONFIG.get(env)
    
    # If env is not found, default to development with a warning
    if not config_class:
        logger.warning(
            f"Unknown environment '{env}', falling back to development configuration."
        )
        config_class = CONFIG['development']
    
    # Return an instance of the config class
    return config_class()