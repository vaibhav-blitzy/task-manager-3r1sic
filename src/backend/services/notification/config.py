import os
from typing import Dict, Any, Optional
from pathlib import Path

from ...common.config.base import BaseConfig, get_env_variable, get_env_boolean

# Define supported notification types
NOTIFICATION_TYPES = {
    'TASK_ASSIGNED',
    'TASK_DUE_SOON',
    'TASK_OVERDUE',
    'COMMENT_ADDED',
    'MENTION',
    'PROJECT_INVITATION',
    'STATUS_CHANGE'
}

# Get current environment
ENV = os.getenv('FLASK_ENV', 'development')

class NotificationConfig(BaseConfig):
    """
    Base configuration for the notification service, extending the common BaseConfig.
    Contains settings shared across environments.
    """

    def __init__(self):
        """
        Initializes the notification configuration with default values.
        """
        super().__init__()
        
        # Service identification
        self.SERVICE_NAME = 'notification-service'
        self.VERSION = '1.0.0'
        
        # Event bus for asynchronous communication
        self.EVENT_BUS_URI = get_env_variable('EVENT_BUS_URI', 'amqp://guest:guest@rabbitmq:5672/')
        
        # Notification processing settings
        self.NOTIFICATION_BATCH_SIZE = 50
        self.NOTIFICATION_PROCESSING_INTERVAL = 30  # seconds
        self.MAX_RETRY_ATTEMPTS = 3
        
        # Email settings
        self.EMAIL_BACKEND = 'sendgrid'
        self.EMAIL_PROVIDERS = {
            'sendgrid': {
                'api_key': get_env_variable('SENDGRID_API_KEY', ''),
                'sender_email': get_env_variable('SENDER_EMAIL', 'notifications@taskmanagement.com'),
                'sender_name': get_env_variable('SENDER_NAME', 'Task Management System'),
                'timeout': 10,  # seconds
                'sandbox_mode': False
            },
            # Support for additional email providers can be added here
        }
        
        # Push notification settings
        self.ENABLE_PUSH_NOTIFICATIONS = get_env_boolean('ENABLE_PUSH_NOTIFICATIONS', False)
        
        # Notification channels configuration
        self.NOTIFICATION_CHANNELS = {
            'in-app': {
                'enabled': True,
                'default_expiry': 30,  # days
                'batch_size': 10,
                'real_time': True  # WebSocket delivery
            },
            'email': {
                'enabled': True,
                'throttle_rate': 60,  # seconds between emails to same user
                'daily_limit': 50,
                'template_dir': 'email_templates'
            },
            'push': {
                'enabled': self.ENABLE_PUSH_NOTIFICATIONS,
                'firebase_api_key': get_env_variable('FIREBASE_API_KEY', ''),
                'apns_key_id': get_env_variable('APNS_KEY_ID', ''),
                'apns_key_file': get_env_variable('APNS_KEY_FILE', ''),
                'throttle_rate': 300  # seconds
            }
        }
        
        # Templates for notification content
        self.NOTIFICATION_TEMPLATES = {
            'TASK_ASSIGNED': {
                'email_subject': 'Task Assigned: {task_title}',
                'email_template': 'task_assigned.html',
                'push_title': 'New Task Assigned',
                'push_body': '{assigner_name} assigned you a task: {task_title}',
                'in_app_message': 'You have been assigned a task: {task_title}'
            },
            'TASK_DUE_SOON': {
                'email_subject': 'Task Due Soon: {task_title}',
                'email_template': 'task_due_soon.html',
                'push_title': 'Task Due Soon',
                'push_body': 'Your task "{task_title}" is due in {time_remaining}',
                'in_app_message': 'Task "{task_title}" is due in {time_remaining}'
            },
            'TASK_OVERDUE': {
                'email_subject': 'Task Overdue: {task_title}',
                'email_template': 'task_overdue.html',
                'push_title': 'Task Overdue',
                'push_body': 'Your task "{task_title}" is overdue by {days_overdue} days',
                'in_app_message': 'Task "{task_title}" is now overdue'
            },
            'COMMENT_ADDED': {
                'email_subject': 'New Comment on Task: {task_title}',
                'email_template': 'comment_added.html',
                'push_title': 'New Comment',
                'push_body': '{commenter_name} commented on your task',
                'in_app_message': '{commenter_name} commented on task "{task_title}"'
            },
            'MENTION': {
                'email_subject': 'You were mentioned in a comment',
                'email_template': 'mention.html',
                'push_title': 'You were mentioned',
                'push_body': '{mentioner_name} mentioned you in a comment',
                'in_app_message': '{mentioner_name} mentioned you: "{content_snippet}"'
            },
            'PROJECT_INVITATION': {
                'email_subject': 'Invitation to Project: {project_name}',
                'email_template': 'project_invitation.html',
                'push_title': 'Project Invitation',
                'push_body': '{inviter_name} invited you to project {project_name}',
                'in_app_message': 'You have been invited to project {project_name} by {inviter_name}'
            },
            'STATUS_CHANGE': {
                'email_subject': 'Task Status Changed: {task_title}',
                'email_template': 'status_change.html',
                'push_title': 'Task Status Update',
                'push_body': 'Task "{task_title}" status changed to {new_status}',
                'in_app_message': 'Task "{task_title}" status changed from {old_status} to {new_status}'
            }
        }
        
        # Default values for notifications
        self.NOTIFICATION_DEFAULTS = {
            'priority': 'normal',  # low, normal, high, urgent
            'channels': ['in-app'],
            'user_overridable': True,
            'ttl': 7 * 24 * 60 * 60,  # 7 days in seconds
            'aggregation': False
        }
        
        # Path to email templates
        self.TEMPLATE_DIR = Path(__file__).parent / 'templates'
    
    def get_email_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Returns the configuration for the specified email provider.
        
        Args:
            provider_name: The name of the email provider
            
        Returns:
            Configuration dictionary for the specified email provider
            
        Raises:
            ValueError: If the provider is not configured
        """
        if provider_name in self.EMAIL_PROVIDERS:
            return self.EMAIL_PROVIDERS[provider_name]
        raise ValueError(f"Email provider '{provider_name}' not configured")
    
    def get_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """
        Returns the configuration for the specified notification channel.
        
        Args:
            channel_name: The name of the notification channel
            
        Returns:
            Configuration dictionary for the specified notification channel
            
        Raises:
            ValueError: If the channel is not configured
        """
        if channel_name in self.NOTIFICATION_CHANNELS:
            return self.NOTIFICATION_CHANNELS[channel_name]
        raise ValueError(f"Notification channel '{channel_name}' not configured")


class DevelopmentConfig(NotificationConfig):
    """
    Configuration settings specific to the development environment.
    """
    
    def __init__(self):
        """
        Initializes the development configuration with appropriate values.
        """
        super().__init__()
        self.ENV = 'development'
        self.DEBUG = True
        
        # Override MongoDB connection for development
        self.MONGO_URI = "mongodb://localhost:27017/task_management_dev"
        
        # Use development SendGrid settings
        self.EMAIL_PROVIDERS['sendgrid']['api_key'] = get_env_variable('SENDGRID_API_KEY', 'SG.development_key')
        self.EMAIL_PROVIDERS['sendgrid']['sandbox_mode'] = True  # Don't send actual emails in development
        
        # Faster processing for development
        self.NOTIFICATION_PROCESSING_INTERVAL = 10  # seconds
        
        # Enhanced logging for development
        self.LOGGING['root']['level'] = 'DEBUG'
        self.LOGGING['loggers']['app']['level'] = 'DEBUG'


class TestingConfig(NotificationConfig):
    """
    Configuration settings specific to the testing environment.
    """
    
    def __init__(self):
        """
        Initializes the testing configuration with appropriate values.
        """
        super().__init__()
        self.ENV = 'testing'
        self.DEBUG = True
        self.TESTING = True
        
        # Use test-specific database
        self.MONGO_URI = "mongodb://localhost:27017/task_management_test"
        
        # Disable actual email sending in tests
        self.EMAIL_PROVIDERS['sendgrid']['sandbox_mode'] = True
        
        # Test data
        self.TEST_USER_EMAIL = "test@example.com"
        self.TEST_USER_ID = "test_user_id"
        
        # Minimal processing intervals for fast tests
        self.NOTIFICATION_PROCESSING_INTERVAL = 1


class ProductionConfig(NotificationConfig):
    """
    Configuration settings specific to the production environment.
    """
    
    def __init__(self):
        """
        Initializes the production configuration with secure values.
        """
        super().__init__()
        self.ENV = 'production'
        self.DEBUG = False
        
        # Secure MongoDB connection
        self.MONGO_URI = get_env_variable('MONGO_URI')
        self.MONGO_OPTIONS['ssl'] = True
        self.MONGO_OPTIONS['retryWrites'] = True
        self.MONGO_OPTIONS['w'] = 'majority'
        
        # Redis for caching and pub/sub
        self.REDIS_HOST = get_env_variable('REDIS_HOST')
        self.REDIS_PORT = int(get_env_variable('REDIS_PORT', '6379'))
        self.REDIS_PASSWORD = get_env_variable('REDIS_PASSWORD')
        
        # Production SendGrid API key - strict verification
        self.EMAIL_PROVIDERS['sendgrid']['api_key'] = get_env_variable('SENDGRID_API_KEY')
        
        # Optimized batch processing for production
        self.NOTIFICATION_BATCH_SIZE = 100
        self.NOTIFICATION_PROCESSING_INTERVAL = 60  # 1 minute
        
        # Secure logging for production
        self.LOGGING['formatters']['json']['format'] = (
            '{{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", '
            '"message": "%(message)s", "environment": "production"}}'
        )
        
        # Enable push notifications in production if configured
        self.ENABLE_PUSH_NOTIFICATIONS = get_env_boolean('ENABLE_PUSH_NOTIFICATIONS', False)
        if self.ENABLE_PUSH_NOTIFICATIONS:
            self.NOTIFICATION_CHANNELS['push']['enabled'] = True
            self.NOTIFICATION_CHANNELS['push']['firebase_api_key'] = get_env_variable('FIREBASE_API_KEY')
        
        # Increase retry attempts for reliability in production
        self.MAX_RETRY_ATTEMPTS = 5


def get_config():
    """
    Returns the appropriate configuration class instance based on the current environment.
    
    Returns:
        NotificationConfig: Configuration instance for the current environment
    """
    env = os.getenv('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()