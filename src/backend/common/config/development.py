"""
Development environment configuration for the Task Management System.

This module contains configuration settings specific to the development environment,
including database connections, authentication settings, and debugging options.
"""

import os
import logging
from datetime import timedelta

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """
    Configuration class for development environment settings.
    Inherits from BaseConfig and overrides settings for local development.
    """

    def __init__(self):
        """
        Initializes the development configuration with default values
        suitable for local development.
        """
        # Initialize the base config first
        super().__init__()
        
        # Basic settings
        self.DEBUG = True
        self.ENV = 'development'
        
        # MongoDB configuration - assumes a local MongoDB instance
        self.MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
        self.MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'task_management_dev')
        
        # Redis configuration - assumes a local Redis instance
        self.REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
        self.REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
        self.REDIS_DB = int(os.environ.get('REDIS_DB', 0))
        
        # Development-specific secret key
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-please-change-in-production')
        
        # JWT settings with longer expiration for easier testing
        self.JWT_SETTINGS = {
            'SECRET_KEY': self.SECRET_KEY,
            'ACCESS_TOKEN_EXPIRES': timedelta(hours=24),  # Longer expiration for development
            'REFRESH_TOKEN_EXPIRES': timedelta(days=30),  # Longer expiration for development
            'ALGORITHM': 'HS256',
            'BLACKLIST_ENABLED': True,
            'BLACKLIST_STORAGE': 'redis',
            'TOKEN_LOCATION': ['headers'],
            'HEADER_NAME': 'Authorization',
            'HEADER_TYPE': 'Bearer'
        }
        
        # CORS settings to allow local frontend development
        self.CORS_SETTINGS = {
            'origins': ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080', 'http://127.0.0.1:8080'],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With'],
            'expose_headers': ['Content-Type', 'X-Pagination'],
            'supports_credentials': True,
            'max_age': 600
        }
        
        # Set up more verbose logging for development
        self.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',  # More verbose for development
                    'formatter': 'standard',  # Use standard formatter for readability in development
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'handlers': ['console'],
                'level': 'DEBUG',  # More verbose for development
            },
            'loggers': {
                'app': {
                    'handlers': ['console'],
                    'level': 'DEBUG',  # More verbose for development
                    'propagate': False
                }
            }
        }
        
        # Relaxed rate limits for development
        self.RATE_LIMITS = {
            'default': '1000/hour',  # More generous for development
            'login': '100/minute',
            'signup': '50/hour',
            'api': {
                'authenticated': '500/minute',
                'anonymous': '100/minute'
            }
        }
        
        # Local file storage
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.STORAGE_PATH = os.environ.get('STORAGE_PATH', os.path.join(project_root, 'storage'))
        self.UPLOAD_FOLDER = 'uploads'
        
        # Email settings - development typically uses console output instead of actual sending
        self.EMAIL_SETTINGS = {
            'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'localhost'),
            'MAIL_PORT': int(os.environ.get('MAIL_PORT', 1025)),  # Default to mailhog port
            'MAIL_USE_TLS': False,  # Usually not needed for local development
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@localhost'),
            'MAIL_MAX_EMAILS': 100,
            'MAIL_ASCII_ATTACHMENTS': False,
            'USE_CONSOLE_BACKEND': True  # Development-specific option to log emails to console
        }
        
        # External services with development/sandbox credentials
        self.EXTERNAL_SERVICES = {
            'calendar': {
                'google': {
                    'enabled': os.environ.get('GOOGLE_CALENDAR_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
                    'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET', '')
                },
                'outlook': {
                    'enabled': os.environ.get('OUTLOOK_CALENDAR_ENABLED', 'False').lower() == 'true',
                    'client_id': os.environ.get('OUTLOOK_CLIENT_ID', ''),
                    'client_secret': os.environ.get('OUTLOOK_CLIENT_SECRET', '')
                }
            },
            'auth': {
                'auth0': {
                    'enabled': os.environ.get('AUTH0_ENABLED', 'False').lower() == 'true',
                    'domain': os.environ.get('AUTH0_DOMAIN', ''),
                    'client_id': os.environ.get('AUTH0_CLIENT_ID', ''),
                    'client_secret': os.environ.get('AUTH0_CLIENT_SECRET', '')
                }
            },
            # Mock services for development
            'mock_enabled': True
        }
        
        # Security settings - relax some restrictions for development
        self.SECURITY = {
            'password_hash_method': 'bcrypt',
            'password_salt_rounds': 4,  # Lower for faster development testing
            'token_bytes': 32,
            'headers': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1; mode=block',
                # HSTS disabled for development
                'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:",  # More permissive for development
            },
            'cookie_settings': {
                'httponly': True,
                'secure': False,  # Allow non-HTTPS for development
                'samesite': 'Lax'
            }
        }