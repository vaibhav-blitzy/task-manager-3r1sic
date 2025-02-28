"""
Project Management Service configuration module.

This module provides configuration settings for the Project Management Service,
including database settings, caching parameters, and service-specific options.
Configuration is environment-aware, with different settings for development,
testing, and production environments.
"""

import os
import logging
from typing import Dict, Any, Optional

from common.config.base import BaseConfig
from common.config.development import DevelopmentConfig
from common.config.production import ProductionConfig
from common.config.testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Default environment is development
ENV = os.environ.get('FLASK_ENV', 'development')

# Project status and role choices
PROJECT_STATUS_CHOICES = ["planning", "active", "on_hold", "completed", "archived", "cancelled"]
PROJECT_ROLE_CHOICES = ["admin", "manager", "member", "viewer"]


class ProjectConfig(BaseConfig):
    """
    Project service specific configuration that extends the base configuration classes
    with project-related settings.
    """

    def __init__(self):
        """
        Initializes the Project configuration with default values.
        """
        # Initialize base configuration
        super().__init__()
        
        # Service identification
        self.SERVICE_NAME = 'project'
        
        # Pagination settings
        self.PROJECT_PAGINATION_DEFAULT_LIMIT = 20
        self.PROJECT_PAGINATION_MAX_LIMIT = 100
        
        # Project status and role choices
        self.PROJECT_STATUS_CHOICES = PROJECT_STATUS_CHOICES
        self.PROJECT_ROLE_CHOICES = PROJECT_ROLE_CHOICES
        
        # Default project settings structure
        self.PROJECT_SETTINGS_DEFAULTS = {
            'workflow': {
                'enableReview': True,
                'allowSubtasks': True,
                'defaultTaskStatus': 'not_started'
            },
            'permissions': {
                'memberInvite': 'admin,manager',
                'taskCreate': 'admin,manager,member',
                'commentCreate': 'admin,manager,member,viewer'
            },
            'notifications': {
                'taskCreate': True,
                'taskComplete': True,
                'commentAdd': True
            }
        }
        
        # Enable project history/audit trail
        self.ENABLE_PROJECT_HISTORY = True
        
        # Cache configuration
        self.PROJECT_CACHE_TTL = 300  # 5 minutes
        
        # Search configuration
        self.PROJECT_SEARCH_CONFIG = {
            'indexed_fields': {
                'name': 10,  # Higher weight for name matches
                'description': 5,
                'tags': 7,
                'members.user': 3
            },
            'max_results': 100,
            'highlight_fields': ['name', 'description'],
            'min_score': 0.5
        }
        
        # Fields allowed for sorting and filtering
        self.ALLOWED_PROJECT_SORT_FIELDS = [
            'created_at', 'updated_at', 'name', 'status', 'due_date', 'owner'
        ]
        
        self.ALLOWED_PROJECT_FILTER_FIELDS = [
            'status', 'owner', 'member', 'tags', 'created_at', 'updated_at', 'category'
        ]
        
        # Project events configuration
        self.PROJECT_EVENTS_CONFIG = {
            'project.created': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index']
            },
            'project.updated': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index']
            },
            'project.deleted': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index']
            },
            'project.member_added': {
                'topic': 'project.events',
                'handlers': ['notification', 'history']
            },
            'project.member_removed': {
                'topic': 'project.events',
                'handlers': ['notification', 'history']
            },
            'project.status_changed': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index']
            }
        }

    def get_project_settings(self) -> Dict[str, Any]:
        """
        Returns project-specific settings as a dictionary.

        Returns:
            Dict[str, Any]: Dictionary of project settings
        """
        return {
            'service_name': self.SERVICE_NAME,
            'pagination': {
                'default_limit': self.PROJECT_PAGINATION_DEFAULT_LIMIT,
                'max_limit': self.PROJECT_PAGINATION_MAX_LIMIT
            },
            'status_choices': self.PROJECT_STATUS_CHOICES,
            'role_choices': self.PROJECT_ROLE_CHOICES,
            'settings_defaults': self.PROJECT_SETTINGS_DEFAULTS,
            'enable_history': self.ENABLE_PROJECT_HISTORY,
            'cache_ttl': self.PROJECT_CACHE_TTL,
            'search': self.PROJECT_SEARCH_CONFIG,
            'sort_fields': self.ALLOWED_PROJECT_SORT_FIELDS,
            'filter_fields': self.ALLOWED_PROJECT_FILTER_FIELDS,
            'events': self.PROJECT_EVENTS_CONFIG
        }

    def get_project_collection_name(self) -> str:
        """
        Returns the collection name for projects with optional environment prefix.

        Returns:
            str: MongoDB collection name for projects
        """
        prefix = f"{self.ENV}_" if self.ENV != 'production' else ""
        return f"{prefix}projects"

    def get_member_collection_name(self) -> str:
        """
        Returns the collection name for project members with optional environment prefix.

        Returns:
            str: MongoDB collection name for project members
        """
        prefix = f"{self.ENV}_" if self.ENV != 'production' else ""
        return f"{prefix}project_members"

    def get_project_cache_key(self, project_id: Optional[str] = None) -> str:
        """
        Generates a cache key pattern for project objects.

        Args:
            project_id: Optional project ID for specific project cache key

        Returns:
            str: Cache key for project or project pattern
        """
        if project_id:
            return f"{self.SERVICE_NAME}:project:{project_id}"
        return f"{self.SERVICE_NAME}:project:*"


class ProjectDevConfig(DevelopmentConfig, ProjectConfig):
    """
    Development environment configuration for project service.
    """

    def __init__(self):
        """
        Initializes the development configuration for project service.
        """
        # Initialize both parent classes
        DevelopmentConfig.__init__(self)
        ProjectConfig.__init__(self)
        
        # Override settings for development environment
        
        # Enable PROJECT_HISTORY for debugging
        self.ENABLE_PROJECT_HISTORY = True
        
        # Set higher PROJECT_CACHE_TTL for development (600 seconds)
        self.PROJECT_CACHE_TTL = 600
        
        # Configure simplified PROJECT_SEARCH_CONFIG for faster development
        self.PROJECT_SEARCH_CONFIG = {
            'indexed_fields': {
                'name': 5,
                'description': 3,
                'tags': 3
            },
            'max_results': 100,
            'highlight_fields': ['name'],
            'min_score': 0.3  # Lower threshold for development
        }
        
        # Enable additional debug settings specific to the project service
        self.DEBUG_PROJECT_FEATURES = {
            'mock_data': True,
            'extended_logging': True,
            'performance_tracing': True
        }


class ProjectProdConfig(ProductionConfig, ProjectConfig):
    """
    Production environment configuration for project service.
    """

    def __init__(self):
        """
        Initializes the production configuration for project service.
        """
        # Initialize both parent classes
        ProductionConfig.__init__(self)
        ProjectConfig.__init__(self)
        
        # Apply optimized settings for production
        
        # Configure PROJECT_PAGINATION with optimized values
        self.PROJECT_PAGINATION_DEFAULT_LIMIT = 25
        self.PROJECT_PAGINATION_MAX_LIMIT = 100
        
        # Set production-appropriate PROJECT_CACHE_TTL (300 seconds)
        self.PROJECT_CACHE_TTL = 300
        
        # Configure optimized PROJECT_SEARCH_CONFIG with proper indexing
        self.PROJECT_SEARCH_CONFIG = {
            'indexed_fields': {
                'name': 10,
                'description': 5,
                'tags': 7,
                'members.user': 3,
                'category': 4
            },
            'max_results': 100,
            'highlight_fields': ['name', 'description'],
            'min_score': 0.6  # Higher quality threshold for production
        }
        
        # Set up advanced PROJECT_EVENTS_CONFIG with proper handlers
        self.PROJECT_EVENTS_CONFIG = {
            'project.created': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index', 'analytics']
            },
            'project.updated': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index', 'analytics']
            },
            'project.deleted': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index', 'analytics']
            },
            'project.member_added': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'analytics']
            },
            'project.member_removed': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'analytics']
            },
            'project.status_changed': {
                'topic': 'project.events',
                'handlers': ['notification', 'history', 'search_index', 'analytics', 'workflow']
            }
        }
        
        # Configure project collection sharding and indexing for production
        self.PROJECT_DB_CONFIG = {
            'sharding': {
                'enabled': True,
                'shard_key': {'owner': 1, '_id': 1}
            },
            'indexes': [
                {'fields': [('name', 'text'), ('description', 'text')], 'options': {'name': 'project_text_search'}},
                {'fields': [('owner', 1), ('created_at', -1)], 'options': {'name': 'project_owner_date'}},
                {'fields': [('status', 1), ('updated_at', -1)], 'options': {'name': 'project_status_date'}},
                {'fields': [('members.user', 1)], 'options': {'name': 'project_members'}}
            ]
        }


class ProjectTestConfig(TestingConfig, ProjectConfig):
    """
    Testing environment configuration for project service.
    """

    def __init__(self):
        """
        Initializes the testing configuration for project service.
        """
        # Initialize both parent classes
        TestingConfig.__init__(self)
        ProjectConfig.__init__(self)
        
        # Configure test-specific settings
        
        # Set lower PROJECT_PAGINATION limits for testing
        self.PROJECT_PAGINATION_DEFAULT_LIMIT = 10
        self.PROJECT_PAGINATION_MAX_LIMIT = 50
        
        # Disable or simplify PROJECT_HISTORY for faster tests
        self.ENABLE_PROJECT_HISTORY = False
        
        # Set low PROJECT_CACHE_TTL for testing (30 seconds)
        self.PROJECT_CACHE_TTL = 30
        
        # Configure minimal PROJECT_SEARCH_CONFIG for tests
        self.PROJECT_SEARCH_CONFIG = {
            'indexed_fields': {
                'name': 1,
                'description': 1
            },
            'max_results': 20,
            'highlight_fields': [],
            'min_score': 0.1  # Very low threshold for predictable test results
        }
        
        # Set up predictable test data for project statuses and roles
        self.TEST_PROJECT_DATA = {
            'statuses': ['planning', 'active', 'completed'],
            'roles': ['admin', 'member'],
            'default_owner': 'test_user_id',
            'test_projects': 5  # Number of test projects to create
        }


# Configuration mapping for different environments
CONFIG = {
    'development': ProjectDevConfig,
    'production': ProjectProdConfig,
    'testing': ProjectTestConfig
}


def get_config(env: str = ENV):
    """
    Function to retrieve the appropriate configuration class based on the environment.

    Args:
        env: The environment to get configuration for, defaults to current ENV

    Returns:
        object: Configuration class for the specified environment
    """
    if env in CONFIG:
        return CONFIG[env]()
    else:
        logger.warning(f"Unknown environment: {env}, falling back to development configuration")
        return ProjectDevConfig()