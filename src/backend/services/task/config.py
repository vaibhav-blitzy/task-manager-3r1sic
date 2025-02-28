import os
import logging

from common.config.base import BaseConfig
from common.config.development import DevelopmentConfig
from common.config.production import ProductionConfig
from common.config.testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Get the current environment from environment variable or default to development
ENV = os.environ.get('FLASK_ENV', 'development')

class TaskConfig(BaseConfig):
    """
    Task service specific configuration that extends the base configuration classes
    with task-specific settings.
    """
    
    def __init__(self):
        """
        Initializes the Task configuration with default values.
        """
        # Initialize base configuration
        super().__init__()
        
        # Set service name
        self.SERVICE_NAME = 'task'
        
        # Pagination settings
        self.TASK_PAGINATION_DEFAULT_LIMIT = 50
        self.TASK_PAGINATION_MAX_LIMIT = 500
        
        # Task status configuration
        self.TASK_STATUS_CONFIG = {
            'created': {
                'label': 'Created',
                'color': '#E0E0E0',
                'transitions': ['assigned', 'in-progress', 'cancelled']
            },
            'assigned': {
                'label': 'Assigned',
                'color': '#64B5F6',
                'transitions': ['in-progress', 'declined', 'cancelled']
            },
            'in-progress': {
                'label': 'In Progress',
                'color': '#4CAF50',
                'transitions': ['on-hold', 'in-review', 'completed', 'cancelled']
            },
            'on-hold': {
                'label': 'On Hold',
                'color': '#FFA726',
                'transitions': ['in-progress', 'cancelled']
            },
            'in-review': {
                'label': 'In Review',
                'color': '#AB47BC',
                'transitions': ['in-progress', 'completed', 'cancelled']
            },
            'completed': {
                'label': 'Completed',
                'color': '#66BB6A',
                'transitions': []
            },
            'cancelled': {
                'label': 'Cancelled',
                'color': '#EF5350',
                'transitions': []
            },
            'declined': {
                'label': 'Declined',
                'color': '#EF5350', 
                'transitions': ['assigned', 'cancelled']
            }
        }
        
        # Task priority configuration
        self.TASK_PRIORITY_CONFIG = {
            'low': {
                'label': 'Low',
                'color': '#90CAF9',
                'value': 0
            },
            'medium': {
                'label': 'Medium',
                'color': '#FFF59D',
                'value': 1
            },
            'high': {
                'label': 'High',
                'color': '#FFAB91',
                'value': 2
            },
            'urgent': {
                'label': 'Urgent',
                'color': '#EF9A9A',
                'value': 3
            }
        }
        
        # Enable task history tracking by default
        self.ENABLE_TASK_HISTORY = True
        
        # Task cache time-to-live in seconds (5 minutes)
        self.TASK_CACHE_TTL = 300
        
        # Search configuration
        self.TASK_SEARCH_CONFIG = {
            'indexed_fields': {
                'title': 10,  # Field weight for search relevance
                'description': 5,
                'assignee.name': 3,
                'tags': 8
            },
            'default_operator': 'OR',
            'min_score': 0.3
        }
        
        # Allowed fields for sorting
        self.ALLOWED_TASK_SORT_FIELDS = [
            'created_at',
            'updated_at',
            'due_date',
            'priority',
            'status'
        ]
        
        # Allowed fields for filtering
        self.ALLOWED_TASK_FILTER_FIELDS = [
            'status',
            'priority',
            'assignee_id',
            'creator_id',
            'project_id',
            'due_date',
            'tags'
        ]
        
        # Task events configuration
        self.TASK_EVENTS_CONFIG = {
            'task.created': {
                'description': 'Task created',
                'handlers': ['notification', 'analytics', 'search_index']
            },
            'task.updated': {
                'description': 'Task updated',
                'handlers': ['notification', 'analytics', 'search_index']
            },
            'task.status_changed': {
                'description': 'Task status changed',
                'handlers': ['notification', 'analytics', 'search_index']
            },
            'task.assigned': {
                'description': 'Task assigned',
                'handlers': ['notification', 'analytics', 'calendar']
            },
            'task.commented': {
                'description': 'Comment added to task',
                'handlers': ['notification']
            },
            'task.completed': {
                'description': 'Task completed',
                'handlers': ['notification', 'analytics', 'search_index']
            },
            'task.deleted': {
                'description': 'Task deleted',
                'handlers': ['analytics', 'search_index_remove']
            }
        }

    def get_task_settings(self):
        """
        Returns task-specific settings as a dictionary.
        
        Returns:
            dict: Dictionary of task settings
        """
        return {
            'service_name': self.SERVICE_NAME,
            'pagination': {
                'default_limit': self.TASK_PAGINATION_DEFAULT_LIMIT,
                'max_limit': self.TASK_PAGINATION_MAX_LIMIT
            },
            'statuses': self.TASK_STATUS_CONFIG,
            'priorities': self.TASK_PRIORITY_CONFIG,
            'enable_history': self.ENABLE_TASK_HISTORY,
            'cache_ttl': self.TASK_CACHE_TTL,
            'search': self.TASK_SEARCH_CONFIG,
            'sort_fields': self.ALLOWED_TASK_SORT_FIELDS,
            'filter_fields': self.ALLOWED_TASK_FILTER_FIELDS,
            'events': self.TASK_EVENTS_CONFIG
        }
    
    def get_task_collection_name(self):
        """
        Returns the collection name for tasks with optional environment prefix.
        
        Returns:
            str: MongoDB collection name for tasks
        """
        # Add environment prefix in non-production environments for isolation
        if self.ENV != 'production' and not self.TESTING:
            return f"{self.ENV}_tasks"
        return "tasks"
    
    def get_task_cache_key(self, task_id=None):
        """
        Generates a cache key pattern for task objects.
        
        Args:
            task_id (str, optional): Specific task ID. Defaults to None.
            
        Returns:
            str: Cache key for task or task pattern
        """
        if task_id:
            return f"{self.SERVICE_NAME}:task:{task_id}"
        return f"{self.SERVICE_NAME}:task:*"


class TaskDevConfig(DevelopmentConfig, TaskConfig):
    """
    Development environment configuration for task service.
    """
    
    def __init__(self):
        """
        Initializes the development configuration for task service.
        """
        # Initialize parent classes
        DevelopmentConfig.__init__(self)
        TaskConfig.__init__(self)
        
        # Override with development-specific settings
        
        # In development, keep history for debugging
        self.ENABLE_TASK_HISTORY = True
        
        # Longer cache TTL for development (10 minutes)
        self.TASK_CACHE_TTL = 600
        
        # Simplified search configuration for development
        self.TASK_SEARCH_CONFIG = {
            'indexed_fields': {
                'title': 10,
                'description': 5
            },
            'default_operator': 'OR',
            'min_score': 0.1  # Lower threshold for dev environment
        }


class TaskProdConfig(ProductionConfig, TaskConfig):
    """
    Production environment configuration for task service.
    """
    
    def __init__(self):
        """
        Initializes the production configuration for task service.
        """
        # Initialize parent classes
        ProductionConfig.__init__(self)
        TaskConfig.__init__(self)
        
        # Override with production-specific settings
        
        # Optimize pagination for production
        self.TASK_PAGINATION_DEFAULT_LIMIT = 25  # Smaller default for better performance
        self.TASK_PAGINATION_MAX_LIMIT = 100  # Limit maximum to prevent resource exhaustion
        
        # Standard cache TTL for production (5 minutes)
        self.TASK_CACHE_TTL = 300
        
        # Optimized search configuration for production
        self.TASK_SEARCH_CONFIG = {
            'indexed_fields': {
                'title': 10,
                'description': 5,
                'assignee.name': 3,
                'tags': 8,
                'status': 2,
                'priority': 2
            },
            'default_operator': 'AND',  # Stricter matching for production
            'min_score': 0.5,  # Higher threshold for production
            'highlight': True,  # Enable result highlighting
            'fuzzy_matching': {
                'enabled': True,
                'max_expansions': 50,
                'prefix_length': 2
            }
        }
        
        # Advanced event configuration for production
        self.TASK_EVENTS_CONFIG.update({
            'task.due_soon': {
                'description': 'Task due date approaching',
                'handlers': ['notification', 'analytics']
            },
            'task.overdue': {
                'description': 'Task is overdue',
                'handlers': ['notification', 'analytics', 'alert']
            }
        })


class TaskTestConfig(TestingConfig, TaskConfig):
    """
    Testing environment configuration for task service.
    """
    
    def __init__(self):
        """
        Initializes the testing configuration for task service.
        """
        # Initialize parent classes
        TestingConfig.__init__(self)
        TaskConfig.__init__(self)
        
        # Override with test-specific settings
        
        # Lower pagination limits for testing
        self.TASK_PAGINATION_DEFAULT_LIMIT = 10
        self.TASK_PAGINATION_MAX_LIMIT = 50
        
        # Simplified history for testing
        self.ENABLE_TASK_HISTORY = False  # Disable for faster tests
        
        # Short cache TTL for testing (30 seconds)
        self.TASK_CACHE_TTL = 30
        
        # Minimal search configuration for tests
        self.TASK_SEARCH_CONFIG = {
            'indexed_fields': {
                'title': 1,
                'description': 1
            },
            'default_operator': 'OR',
            'min_score': 0.1
        }
        
        # Simplify task statuses for testing
        self.TASK_STATUS_CONFIG = {
            'created': {
                'label': 'Created',
                'color': '#E0E0E0',
                'transitions': ['in-progress', 'completed', 'cancelled']
            },
            'in-progress': {
                'label': 'In Progress',
                'color': '#4CAF50',
                'transitions': ['completed', 'cancelled']
            },
            'completed': {
                'label': 'Completed',
                'color': '#66BB6A',
                'transitions': []
            },
            'cancelled': {
                'label': 'Cancelled',
                'color': '#EF5350',
                'transitions': []
            }
        }
        
        # Simplify priorities for testing
        self.TASK_PRIORITY_CONFIG = {
            'low': {
                'label': 'Low',
                'color': '#90CAF9',
                'value': 0
            },
            'high': {
                'label': 'High',
                'color': '#FFAB91',
                'value': 1
            }
        }


# Mapping of environment names to configuration classes
CONFIG = {
    'development': TaskDevConfig,
    'production': TaskProdConfig,
    'testing': TaskTestConfig
}


def get_config(env=ENV):
    """
    Function to retrieve the appropriate configuration class based on the environment.
    
    Args:
        env (str): The environment name. Defaults to the value of ENV.
        
    Returns:
        object: Configuration class for the specified environment.
    """
    config_class = CONFIG.get(env)
    if config_class:
        return config_class()
    else:
        logger.warning(f"Unknown environment: {env}. Falling back to development configuration.")
        return TaskDevConfig()