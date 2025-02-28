import os
import tempfile
import logging
import shutil
from typing import Dict, Any
from datetime import timedelta

from .base import BaseConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Constants for testing
TEST_DB_NAME = "task_management_test"
TEMP_STORAGE_DIR = tempfile.mkdtemp(prefix="task_management_test_")

class TestingConfig(BaseConfig):
    """
    Configuration class for the testing environment, extending BaseConfig
    with test-specific settings for automated testing.
    """

    def __init__(self):
        """
        Initializes the testing configuration with appropriate settings for
        automated tests.
        """
        # Initialize base configuration
        super().__init__()
        
        # Basic settings
        self.ENV = 'testing'
        self.DEBUG = True
        self.TESTING = True
        
        # Use a consistent secret key for testing
        self.SECRET_KEY = "test-secret-key-for-testing-environment"
        
        # MongoDB configuration for testing
        # This URI works with both real MongoDB and mongomock
        self.MONGO_URI = os.environ.get('TEST_MONGO_URI', f"mongodb://localhost:27017/{TEST_DB_NAME}")
        self.MONGO_OPTIONS = self.get_mongodb_test_settings()
        
        # Redis configuration (use database 1 for testing)
        self.REDIS_HOST = os.environ.get('TEST_REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.environ.get('TEST_REDIS_PORT', '6379'))
        self.REDIS_PASSWORD = os.environ.get('TEST_REDIS_PASSWORD', '')
        self.REDIS_DB = int(os.environ.get('TEST_REDIS_DB', '1'))
        self.REDIS_OPTIONS = self.get_redis_test_settings()
        
        # JWT configuration - shorter expiration for faster testing
        self.JWT_SETTINGS.update({
            'SECRET_KEY': self.SECRET_KEY,
            'ACCESS_TOKEN_EXPIRES': timedelta(minutes=5),
            'REFRESH_TOKEN_EXPIRES': timedelta(hours=1),
        })
        
        # Permissive CORS for testing
        self.CORS_SETTINGS.update({
            'origins': ["*"],
            'supports_credentials': True
        })
        
        # Configure logging based on environment variable or use minimal configuration
        log_level = os.environ.get('TEST_LOG_LEVEL', 'ERROR').upper()
        self.LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': log_level,
                    'formatter': 'standard',
                }
            },
            'loggers': {
                '': {  # Root logger
                    'handlers': ['console'],
                    'level': log_level,
                },
                'app': {  # Application logger
                    'handlers': ['console'],
                    'level': log_level,
                    'propagate': False
                }
            }
        }
        
        # Disable rate limits for testing
        self.RATE_LIMITS = {
            'default': '1000/second',
            'login': '1000/second',
            'signup': '1000/second',
            'api': {
                'authenticated': '1000/second',
                'anonymous': '1000/second'
            }
        }
        
        # Use temporary directory for file storage
        self.STORAGE_PATH = os.environ.get('TEST_STORAGE_PATH', TEMP_STORAGE_DIR)
        
        # Lower maximum content length for test file uploads
        self.MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB limit for testing
        
        # Configure email settings for testing (file-based or console)
        self.EMAIL_SETTINGS = {
            'MAIL_SERVER': os.environ.get('TEST_MAIL_SERVER', 'localhost'),
            'MAIL_PORT': int(os.environ.get('TEST_MAIL_PORT', '2525')),
            'MAIL_USE_TLS': os.environ.get('TEST_MAIL_USE_TLS', 'False').lower() == 'true',
            'MAIL_USERNAME': os.environ.get('TEST_MAIL_USERNAME', ''),
            'MAIL_PASSWORD': os.environ.get('TEST_MAIL_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': os.environ.get('TEST_MAIL_SENDER', 'test@example.com'),
            'MAIL_SUPPRESS_SEND': os.environ.get('TEST_MAIL_SUPPRESS', 'True').lower() == 'true'
        }

    def get_mongodb_test_settings(self) -> Dict[str, Any]:
        """
        Returns MongoDB connection settings specifically for testing environment.
        
        Returns:
            Dict[str, Any]: MongoDB settings dictionary configured for testing
        """
        # Start with the base MongoDB options
        test_options = self.MONGO_OPTIONS.copy()
        
        # Override with test-specific settings
        test_options.update({
            'connectTimeoutMS': 1000,  # Faster timeouts for tests
            'socketTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 1000,
            'maxPoolSize': 10,  # Smaller connection pool for tests
            'minPoolSize': 1
        })
        
        return test_options

    def get_redis_test_settings(self) -> Dict[str, Any]:
        """
        Returns Redis connection settings specifically for testing environment.
        
        Returns:
            Dict[str, Any]: Redis settings dictionary configured for testing
        """
        # Start with the base Redis options
        test_options = self.REDIS_OPTIONS.copy()
        
        # Override with test-specific settings
        test_options.update({
            'socket_timeout': 1,  # Faster timeouts for tests
            'socket_connect_timeout': 1,
            'max_connections': 10,  # Smaller connection pool for tests
            'health_check_interval': 10
        })
        
        return test_options

    def cleanup_test_storage(self) -> bool:
        """
        Cleans up temporary storage used during tests.
        
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            # Clean up the temporary directory when tests are done
            shutil.rmtree(TEMP_STORAGE_DIR, ignore_errors=True)
            logger.info(f"Successfully cleaned up test storage directory: {TEMP_STORAGE_DIR}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up test storage: {str(e)}")
            return False