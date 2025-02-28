import os
from typing import Dict, Any, Union
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Set up module logger
logger = logging.getLogger(__name__)

# Default values
DEFAULT_SECRET_KEY = "your-default-secret-key-for-development-only"
DEFAULT_PAGE_SIZE = 50
DEFAULT_MAX_PAGE_SIZE = 500

class BaseConfig:
    """
    Base configuration class that defines common settings and provides default values
    for all environments. Environment-specific configurations inherit from this class
    and override settings as needed.
    """

    def __init__(self):
        """
        Initializes the base configuration with default values that apply across all environments.
        """
        # Basic settings
        self.ENV = 'base'  # Base environment (to be overridden)
        self.DEBUG = False  # Secure default
        self.TESTING = False  # Default state

        # Secret key for signing
        self.SECRET_KEY = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)
        if self.SECRET_KEY == DEFAULT_SECRET_KEY:
            logger.warning("Using default SECRET_KEY. This is insecure and should be changed in production.")

        # MongoDB configuration
        self.MONGO_URI = ""  # To be overridden by environment configs
        self.MONGO_OPTIONS = {
            'connectTimeoutMS': 5000,
            'socketTimeoutMS': 30000,
            'serverSelectionTimeoutMS': 5000,
            'waitQueueTimeoutMS': 5000,
            'retryWrites': True,
            'w': 'majority',  # Write concern for data safety
            'journal': True,  # Journal writes for durability
            'readPreference': 'primaryPreferred',  # Read from primary when available
            'maxPoolSize': 100,  # Connection pool size
            'minPoolSize': 10
        }

        # Redis configuration
        self.REDIS_HOST = ""  # To be overridden
        self.REDIS_PORT = 6379
        self.REDIS_PASSWORD = ""
        self.REDIS_DB = 0
        self.REDIS_OPTIONS = {
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            'max_connections': 100,
            'health_check_interval': 30
        }

        # JWT configuration
        self.JWT_SETTINGS = {
            'SECRET_KEY': self.SECRET_KEY,
            'ACCESS_TOKEN_EXPIRES': timedelta(minutes=15),  # Short-lived access tokens
            'REFRESH_TOKEN_EXPIRES': timedelta(days=7),
            'ALGORITHM': 'HS256',
            'BLACKLIST_ENABLED': True,
            'BLACKLIST_STORAGE': 'redis',  # Options: 'redis', 'mongodb'
            'TOKEN_LOCATION': ['headers'],
            'HEADER_NAME': 'Authorization',
            'HEADER_TYPE': 'Bearer'
        }

        # CORS configuration
        self.CORS_SETTINGS = {
            'origins': [],  # To be overridden with specific domains
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With'],
            'expose_headers': ['Content-Type', 'X-Pagination'],
            'supports_credentials': True,
            'max_age': 600  # Cache preflight requests for 10 minutes
        }

        # Logging configuration - adapted for containerized environments
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
                    'level': 'INFO',
                    'formatter': 'json',  # Using JSON for container log aggregation
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'handlers': ['console'],
                'level': 'INFO',
            },
            'loggers': {
                'app': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False
                }
            }
        }

        # Rate limiting
        self.RATE_LIMITS = {
            'default': '100/hour',
            'login': '10/minute',
            'signup': '5/hour',
            'api': {
                'authenticated': '120/minute',
                'anonymous': '30/minute'
            }
        }

        # File storage
        self.STORAGE_PATH = os.environ.get("STORAGE_PATH", str(Path(__file__).parent.parent.parent / "storage"))
        self.UPLOAD_FOLDER = "uploads"
        self.MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB default

        # Email settings
        self.EMAIL_SETTINGS = {
            'MAIL_SERVER': "",
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': "",
            'MAIL_PASSWORD': "",
            'MAIL_DEFAULT_SENDER': "",
            'MAIL_MAX_EMAILS': 100,
            'MAIL_ASCII_ATTACHMENTS': False
        }

        # External services
        self.EXTERNAL_SERVICES = {
            'calendar': {
                'google': {
                    'enabled': False,
                    'client_id': "",
                    'client_secret': ""
                },
                'outlook': {
                    'enabled': False,
                    'client_id': "",
                    'client_secret': ""
                }
            },
            'auth': {
                'auth0': {
                    'enabled': False,
                    'domain': "",
                    'client_id': "",
                    'client_secret': ""
                }
            }
        }

        # Pagination
        self.PAGINATION = {
            'default_page_size': DEFAULT_PAGE_SIZE,
            'max_page_size': DEFAULT_MAX_PAGE_SIZE
        }

        # Security settings
        self.SECURITY = {
            'password_hash_method': 'bcrypt',
            'password_salt_rounds': 12,
            'token_bytes': 32,
            'headers': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'; script-src 'self'; object-src 'none'",
            },
            'cookie_settings': {
                'httponly': True,
                'secure': True,
                'samesite': 'Lax'
            }
        }

    def get_redis_uri(self) -> str:
        """
        Constructs a Redis connection URI from configuration components.
        
        Returns:
            str: Redis connection URI string
        """
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_mongodb_settings(self) -> Dict[str, Any]:
        """
        Returns MongoDB connection settings dictionary.
        
        Returns:
            Dict[str, Any]: MongoDB settings dictionary
        """
        return {
            'uri': self.MONGO_URI,
            'options': self.MONGO_OPTIONS
        }

    def get_file_storage_path(self) -> Path:
        """
        Returns the absolute path for file storage.
        
        Returns:
            Path: Absolute path to file storage directory
        """
        storage_path = Path(self.STORAGE_PATH) / self.UPLOAD_FOLDER
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path.absolute()

    def get_environment_settings(self) -> Dict[str, Any]:
        """
        Returns environment-specific settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary of all configuration values
        """
        # Get all attributes that don't start with underscore (not private/special)
        settings = {}
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(self, key)):
                settings[key] = getattr(self, key)
        return settings

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts configuration to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of configuration
        """
        config_dict = self.get_environment_settings()
        
        # Recursively process dict to hide sensitive values
        return self._process_sensitive_dict(config_dict)
    
    def _process_sensitive_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively processes a dictionary to hide sensitive values.
        
        Args:
            data: Dictionary to process
            
        Returns:
            Dict[str, Any]: Processed dictionary with sensitive values hidden
        """
        sensitive_keywords = ['secret', 'password', 'token', 'key', 'auth', 'credential']
        result = {}
        
        for key, value in data.items():
            # Check if this key might contain sensitive data
            is_sensitive = any(keyword in key.lower() for keyword in sensitive_keywords)
            
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = self._process_sensitive_dict(value)
            elif is_sensitive and isinstance(value, (str, bytes)) and value:
                # Hide the sensitive value if it's not empty
                result[key] = "[HIDDEN]"
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                # Process list of dictionaries
                result[key] = [self._process_sensitive_dict(item) for item in value]
            else:
                # Pass through non-sensitive and empty values
                result[key] = value
                
        return result