import os
from typing import Dict, List, Any
from dotenv import load_dotenv  # python-dotenv 0.19.1

# Import base configuration
from ...common.config.base import BaseConfig

# Load environment variables from .env file
load_dotenv()

# Global constants
SERVICE_NAME = "api-gateway"
API_VERSION = "v1"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config(BaseConfig):
    """Base configuration class for the API Gateway service"""
    
    def __init__(self):
        """Initialize configuration with default values"""
        super().__init__()
        self.DEBUG = False
        self.SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
        self.SERVICE_NAME = SERVICE_NAME
        self.API_VERSION = API_VERSION
        
        # Dictionary of backend service routes
        self.SERVICE_ROUTES = {}
        
        # CORS configuration (overrides BaseConfig.CORS_SETTINGS)
        self.CORS_SETTINGS = {
            'origins': [],  # To be overridden
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key'],
            'expose_headers': ['Content-Type', 'X-Pagination', 'X-Rate-Limit'],
            'supports_credentials': True,
            'max_age': 600  # Cache preflight requests for 10 minutes
        }
        
        # Rate limiting settings
        self.RATE_LIMIT_SETTINGS = {
            'default': {'limit': 100, 'window': 3600},  # 100 requests per hour
            'anonymous': {'limit': 30, 'window': 60},   # 30 requests per minute
            'authenticated': {'limit': 120, 'window': 60}, # 120 requests per minute
            'service': {'limit': 600, 'window': 60}     # 600 requests per minute
        }
        
        # Routes that don't require authentication
        self.PUBLIC_ROUTES = [
            '/auth/login',
            '/auth/register',
            '/auth/password/reset',
            '/auth/token/refresh',
            '/health',
            '/metrics',
            '/docs'
        ]
        
        # Proxy configuration
        self.PROXY_CONFIG = {
            'timeout': 30,  # 30 second timeout
            'retries': 3,   # 3 retries
            'circuit_breaker': {
                'failure_threshold': 5,   # 5 failures
                'recovery_timeout': 30,   # 30 second timeout
                'max_requests': 1         # 1 request during half-open state
            }
        }


class DevelopmentConfig(Config):
    """Development environment configuration with local service URLs"""
    
    def __init__(self):
        super().__init__()
        self.ENV = 'development'
        self.DEBUG = True
        
        # Local development service URLs
        self.SERVICE_ROUTES = {
            'auth': 'http://localhost:5001/api/v1',
            'task': 'http://localhost:5002/api/v1',
            'project': 'http://localhost:5003/api/v1',
            'notification': 'http://localhost:5004/api/v1',
            'file': 'http://localhost:5005/api/v1',
            'analytics': 'http://localhost:5006/api/v1',
            'realtime': 'http://localhost:5007/api/v1'
        }
        
        # More permissive CORS for development
        self.CORS_SETTINGS = {
            'origins': ['http://localhost:3000', 'http://127.0.0.1:3000'],  # Frontend dev server
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key'],
            'expose_headers': ['Content-Type', 'X-Pagination', 'X-Rate-Limit'],
            'supports_credentials': True,
            'max_age': 600
        }
        
        # More lenient rate limits for development
        self.RATE_LIMIT_SETTINGS = {
            'default': {'limit': 1000, 'window': 3600},  # 1000 requests per hour
            'anonymous': {'limit': 100, 'window': 60},   # 100 requests per minute
            'authenticated': {'limit': 200, 'window': 60}, # 200 requests per minute
            'service': {'limit': 1000, 'window': 60}     # 1000 requests per minute
        }


class TestingConfig(Config):
    """Testing environment configuration with mock service URLs"""
    
    def __init__(self):
        super().__init__()
        self.ENV = 'testing'
        self.DEBUG = True
        self.TESTING = True
        
        # Mock service URLs for testing
        self.SERVICE_ROUTES = {
            'auth': 'http://auth-service:5001/api/v1',
            'task': 'http://task-service:5002/api/v1',
            'project': 'http://project-service:5003/api/v1',
            'notification': 'http://notification-service:5004/api/v1',
            'file': 'http://file-service:5005/api/v1',
            'analytics': 'http://analytics-service:5006/api/v1',
            'realtime': 'http://realtime-service:5007/api/v1'
        }
        
        # Disable rate limiting for testing
        self.RATE_LIMIT_SETTINGS = {
            'default': {'limit': 0, 'window': 60},  # No limit
            'anonymous': {'limit': 0, 'window': 60},
            'authenticated': {'limit': 0, 'window': 60},
            'service': {'limit': 0, 'window': 60}
        }


class ProductionConfig(Config):
    """Production environment configuration with secure settings"""
    
    def __init__(self):
        super().__init__()
        self.ENV = 'production'
        self.DEBUG = False
        
        # Production service URLs (container names in orchestration)
        self.SERVICE_ROUTES = {
            'auth': 'http://auth-service:5000/api/v1',
            'task': 'http://task-service:5000/api/v1',
            'project': 'http://project-service:5000/api/v1',
            'notification': 'http://notification-service:5000/api/v1',
            'file': 'http://file-service:5000/api/v1',
            'analytics': 'http://analytics-service:5000/api/v1',
            'realtime': 'http://realtime-service:5000/api/v1'
        }
        
        # Restrictive CORS for production
        self.CORS_SETTINGS = {
            'origins': [
                'https://app.taskmanagement.com',
                'https://api.taskmanagement.com'
            ],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key'],
            'expose_headers': ['Content-Type', 'X-Pagination', 'X-Rate-Limit'],
            'supports_credentials': True,
            'max_age': 600
        }
        
        # Strict rate limits for production
        self.RATE_LIMIT_SETTINGS = {
            'default': {'limit': 100, 'window': 3600},  # 100 requests per hour
            'anonymous': {'limit': 30, 'window': 60},   # 30 requests per minute
            'authenticated': {'limit': 120, 'window': 60}, # 120 requests per minute
            'service': {'limit': 600, 'window': 60}     # 600 requests per minute
        }
        
        # Production-appropriate proxy timeout values
        self.PROXY_CONFIG = {
            'timeout': 10,  # 10 second timeout
            'retries': 3,   # 3 retries
            'circuit_breaker': {
                'failure_threshold': 5,
                'recovery_timeout': 30,
                'max_requests': 1
            }
        }


def get_service_url(service_name: str) -> str:
    """
    Get the URL for a specific backend service
    
    Args:
        service_name: The name of the service to look up
        
    Returns:
        The URL for the specified service
        
    Raises:
        ValueError: If the service name is not found in the configuration
    """
    config = get_config()
    if service_name in config.SERVICE_ROUTES:
        return config.SERVICE_ROUTES[service_name]
    raise ValueError(f"Service '{service_name}' not found in configuration")


def is_auth_required(path: str) -> bool:
    """
    Determine if a specific path requires authentication
    
    Args:
        path: The API path to check
        
    Returns:
        True if the path requires authentication, False otherwise
    """
    config = get_config()
    
    # Check for public routes
    for public_route in config.PUBLIC_ROUTES:
        if path.startswith(public_route):
            return False
            
    return True


def get_config():
    """
    Get the appropriate configuration class based on environment
    
    Returns:
        Configuration class instance for current environment
    """
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()