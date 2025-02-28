"""
Configuration for the File Management Service.

This module provides configuration classes for the File Management Service,
including storage settings, file size limits, allowed file types, and
virus scanning policies.
"""

import os
import logging
from pathlib import Path

from common.config.base import BaseConfig
from common.config.development import DevelopmentConfig
from common.config.production import ProductionConfig
from common.config.testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Get the current environment
ENV = os.environ.get('FLASK_ENV', 'development')


class FileConfig(BaseConfig):
    """
    File service specific configuration extending the base configuration
    with file management settings.
    """

    def __init__(self):
        """
        Initialize the File configuration with default values.
        """
        super().__init__()
        
        # Service identification
        self.SERVICE_NAME = 'file'
        
        # Storage configuration
        self.STORAGE_CONFIG = {
            'enabled': True,
            'cache_control': 'max-age=86400',  # 1 day in seconds
            'acl': 'private'
        }
        self.STORAGE_PROVIDER = 's3'  # Options: 's3', 'local', 'azure', 'gcp'
        self.BUCKET_NAME = 'task-management-files'
        self.QUARANTINE_BUCKET_NAME = 'task-management-files-quarantine'
        self.CLEAN_BUCKET_NAME = 'task-management-files-clean'
        
        # S3 specific configuration
        self.S3_CONFIG = {
            'region': 'us-east-1',
            'access_key': '',  # Empty by default, will be set from environment
            'secret_key': '',  # Empty by default, will be set from environment
            'signature_version': 's3v4',
            'endpoint_url': None  # Default to AWS S3 service
        }
        
        # File size and expiration limits
        self.MAX_FILE_SIZE = 26214400  # 25MB in bytes
        self.UPLOAD_URL_EXPIRY = 3600  # 1 hour in seconds
        self.DOWNLOAD_URL_EXPIRY = 900  # 15 minutes in seconds
        
        # File type restrictions
        self.ALLOWED_FILE_TYPES = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            'text/csv',
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/zip',
            'application/x-tar',
            'application/x-gzip'
        ]
        self.BLOCKED_FILE_EXTENSIONS = [
            'exe', 'bat', 'cmd', 'com', 'js', 'jsx', 'ts', 'tsx', 
            'msi', 'dll', 'sh', 'bin', 'vbs', 'ps1', 'scr', 'php'
        ]
        
        # Virus scanner configuration
        self.SCANNER_CONFIG = {
            'timeout': 30,  # scan timeout in seconds
            'max_file_scan_size': 52428800,  # 50MB max file size to scan
            'action_on_scan_fail': 'reject',  # Options: 'reject', 'quarantine', 'accept'
            'retry_count': 3,
            'retry_delay': 5,  # seconds between retries
            'clamav': {
                'host': 'localhost',
                'port': 3310,
                'socket': None  # Alternative to host/port
            },
            'mock': {
                'always_clean': False,
                'scan_time': 0.5,  # Mock scan time in seconds
                'threat_detection_rate': 0.0  # 0% chance to detect a threat in mock mode
            }
        }
        self.SCANNER_ENABLED = True
        self.SCANNER_TYPE = 'clamav'  # Options: 'clamav', 'mock', 'external'
        
        # Temporary storage for uploads
        self.TEMP_UPLOAD_FOLDER = os.path.join(self.STORAGE_PATH, 'temp')
        
        # File cache configuration
        self.FILE_CACHE_CONFIG = {
            'enabled': True,
            'prefix': 'file:',
            'invalidate_on_update': True
        }
        self.FILE_CACHE_TTL = 300  # 5 minutes in seconds

    def get_file_settings(self):
        """
        Returns file-specific settings as a dictionary.
        
        Returns:
            dict: Dictionary of file settings
        """
        settings = {
            'service_name': self.SERVICE_NAME,
            'storage_provider': self.STORAGE_PROVIDER,
            'bucket_name': self.BUCKET_NAME,
            'max_file_size': self.MAX_FILE_SIZE,
            'allowed_file_types': self.ALLOWED_FILE_TYPES,
            'blocked_file_extensions': self.BLOCKED_FILE_EXTENSIONS,
            'scanner_enabled': self.SCANNER_ENABLED,
            'scanner_type': self.SCANNER_TYPE
        }
        
        # Combine with base configuration settings
        settings.update(self.get_environment_settings())
        
        return settings

    def get_file_collection_name(self):
        """
        Returns the collection name for file metadata with optional environment prefix.
        
        Returns:
            str: MongoDB collection name for files
        """
        collection_name = 'files'
        
        # Add environment prefix if not in production
        if self.ENV != 'production':
            collection_name = f"{self.ENV}_{collection_name}"
            
        return collection_name

    def get_storage_config(self):
        """
        Returns storage configuration settings.
        
        Returns:
            dict: Storage configuration dictionary
        """
        storage_config = {
            'provider': self.STORAGE_PROVIDER,
            'bucket_name': self.BUCKET_NAME,
            'quarantine_bucket': self.QUARANTINE_BUCKET_NAME,
            'clean_bucket': self.CLEAN_BUCKET_NAME,
        }
        
        # Add S3 specific config if using S3
        if self.STORAGE_PROVIDER == 's3':
            storage_config['s3'] = self.S3_CONFIG
            
        return storage_config

    def get_scanner_config(self):
        """
        Returns virus scanner configuration settings.
        
        Returns:
            dict: Scanner configuration dictionary
        """
        scanner_config = {
            'enabled': self.SCANNER_ENABLED,
            'type': self.SCANNER_TYPE,
            'timeout': self.SCANNER_CONFIG['timeout'],
            'max_file_scan_size': self.SCANNER_CONFIG['max_file_scan_size'],
            'action_on_scan_fail': self.SCANNER_CONFIG['action_on_scan_fail'],
        }
        
        # Add scanner-specific config
        scanner_config[self.SCANNER_TYPE] = self.SCANNER_CONFIG.get(self.SCANNER_TYPE, {})
            
        return scanner_config

    def is_file_type_allowed(self, mime_type, file_extension):
        """
        Checks if a file type is allowed based on MIME type and extension.
        
        Args:
            mime_type (str): MIME type of the file
            file_extension (str): Extension of the file (without dot)
            
        Returns:
            bool: True if the file type is allowed
        """
        # Check if MIME type is in allowed list
        mime_allowed = mime_type in self.ALLOWED_FILE_TYPES
        
        # Check if extension is not in blocked list
        ext_allowed = file_extension.lower() not in self.BLOCKED_FILE_EXTENSIONS
        
        # Both conditions must be true
        return mime_allowed and ext_allowed

    def get_file_cache_key(self, file_id=None):
        """
        Generates a cache key pattern for file objects.
        
        Args:
            file_id (str, optional): File ID for specific file key
            
        Returns:
            str: Cache key for file or file pattern
        """
        prefix = self.FILE_CACHE_CONFIG['prefix']
        
        if file_id:
            return f"{prefix}{file_id}"
        else:
            return f"{prefix}*"


class FileDevConfig(DevelopmentConfig, FileConfig):
    """
    Development environment configuration for file service.
    """
    
    def __init__(self):
        """
        Initialize the development configuration for file service.
        """
        # Initialize both parent classes
        DevelopmentConfig.__init__(self)
        FileConfig.__init__(self)
        
        # Override settings for development environment
        self.STORAGE_PROVIDER = 'local'
        
        # Local file paths for development
        project_root = Path(__file__).parent.parent.parent.parent
        self.STORAGE_PATH = os.environ.get('FILE_STORAGE_PATH', 
                                          str(project_root / 'storage' / 'files'))
        self.TEMP_UPLOAD_FOLDER = os.environ.get('FILE_TEMP_PATH',
                                               str(project_root / 'storage' / 'temp'))
        
        # Larger size limits for development
        self.MAX_FILE_SIZE = 52428800  # 50MB in bytes
        
        # Use mock virus scanner for development
        self.SCANNER_ENABLED = True
        self.SCANNER_TYPE = 'mock'
        
        # Configure mock scanner settings
        self.SCANNER_CONFIG['mock'] = {
            'always_clean': True,
            'scan_time': 0.1,  # Fast scanning for development
            'threat_detection_rate': 0.0  # No threats in development
        }
        
        # Longer cache TTL for development
        self.FILE_CACHE_TTL = 600  # 10 minutes in seconds


class FileProdConfig(ProductionConfig, FileConfig):
    """
    Production environment configuration for file service.
    """
    
    def __init__(self):
        """
        Initialize the production configuration for file service.
        """
        # Initialize both parent classes
        ProductionConfig.__init__(self)
        FileConfig.__init__(self)
        
        # Apply production settings
        self.STORAGE_PROVIDER = 's3'
        
        # Configure AWS S3 buckets for production
        self.BUCKET_NAME = 'task-management-files-prod'
        self.QUARANTINE_BUCKET_NAME = 'task-management-files-quarantine-prod'
        self.CLEAN_BUCKET_NAME = 'task-management-files-clean-prod'
        
        # Configure S3 settings from environment
        self.S3_CONFIG = {
            'region': os.environ.get('AWS_REGION', 'us-east-1'),
            'access_key': os.environ.get('AWS_ACCESS_KEY_ID', ''),
            'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
            'signature_version': 's3v4',
            'endpoint_url': os.environ.get('AWS_S3_ENDPOINT_URL', None),
            'encryption': {
                'enabled': True,
                'kms_key_id': os.environ.get('AWS_KMS_KEY_ID', None)
            }
        }
        
        # Production file size limits
        self.MAX_FILE_SIZE = 26214400  # 25MB in bytes
        
        # Use ClamAV scanner for production
        self.SCANNER_ENABLED = True
        self.SCANNER_TYPE = 'clamav'
        
        # Configure ClamAV settings for production
        self.SCANNER_CONFIG['clamav'] = {
            'host': os.environ.get('CLAMAV_HOST', 'clamav'),
            'port': int(os.environ.get('CLAMAV_PORT', 3310)),
            'socket': os.environ.get('CLAMAV_SOCKET', None)
        }
        
        # Optimized cache in production
        self.FILE_CACHE_TTL = 300  # 5 minutes
        
        # Configure file collection sharding and indexing
        self.FILE_COLLECTION_CONFIG = {
            'sharded': True,
            'shard_key': {'_id': 'hashed'},
            'indexes': [
                {'fields': [('metadata.uploadedBy', 1), ('metadata.uploadedAt', -1)]},
                {'fields': [('associations.taskId', 1)]},
                {'fields': [('associations.projectId', 1)]},
                {'fields': [('metadata.md5Hash', 1)], 'unique': True}
            ]
        }


class FileTestConfig(TestingConfig, FileConfig):
    """
    Testing environment configuration for file service.
    """
    
    def __init__(self):
        """
        Initialize the testing configuration for file service.
        """
        # Initialize both parent classes
        TestingConfig.__init__(self)
        FileConfig.__init__(self)
        
        # Configure test-specific settings
        self.STORAGE_PROVIDER = 'local'
        
        # Temporary local storage for tests
        import tempfile
        test_dir = tempfile.mkdtemp(prefix="task_management_file_test_")
        self.STORAGE_PATH = test_dir
        self.TEMP_UPLOAD_FOLDER = os.path.join(test_dir, 'temp')
        
        # Smaller limits for tests
        self.MAX_FILE_SIZE = 1048576  # 1MB in bytes
        
        # Configure mock scanner for testing
        self.SCANNER_ENABLED = True
        self.SCANNER_TYPE = 'mock'
        self.SCANNER_CONFIG['mock'] = {
            'always_clean': True,
            'scan_time': 0.01,  # Very fast for tests
            'threat_detection_rate': 0.0  # Predictable behavior for tests
        }
        
        # Specific test data
        self.ALLOWED_FILE_TYPES = [
            'application/pdf',
            'text/plain',
            'image/jpeg',
            'image/png'
        ]
        self.BLOCKED_FILE_EXTENSIONS = [
            'exe', 'bat', 'cmd'
        ]
        
        # Disable caching for tests
        self.FILE_CACHE_CONFIG['enabled'] = False
        self.FILE_CACHE_TTL = 1  # 1 second for tests


# Configuration mapping
CONFIG = {
    'development': FileDevConfig,
    'production': FileProdConfig,
    'testing': FileTestConfig
}


def get_config(env=ENV):
    """
    Function to retrieve the appropriate configuration based on environment.
    
    Args:
        env (str): Environment name
        
    Returns:
        object: Configuration class for the specified environment
    """
    config_class = CONFIG.get(env)
    if not config_class:
        logger.warning(f"Unknown environment: {env}, falling back to development")
        config_class = FileDevConfig
    
    return config_class()