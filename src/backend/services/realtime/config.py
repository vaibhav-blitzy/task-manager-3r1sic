import os
import logging

from ...common.config.base import BaseConfig
from ...common.config.development import DevelopmentConfig
from ...common.config.production import ProductionConfig
from ...common.config.testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Default environment
ENV = os.environ.get('FLASK_ENV', 'development')

class RealtimeConfig(BaseConfig):
    """
    Base configuration class for the Realtime Service with common settings
    across environments.
    """
    
    def __init__(self):
        """
        Initialize the Realtime configuration with default values.
        """
        super().__init__()
        
        # Service identification
        self.SERVICE_NAME = 'realtime'
        self.PORT = 5003  # Default port for the realtime service
        
        # WebSocket settings
        self.WEBSOCKET_SETTINGS = {
            'ping_interval': 25000,  # 25 seconds between pings
            'ping_timeout': 60000,   # 60 seconds before timing out
            'max_message_size': 1024 * 1024,  # 1MB
            'max_queue_size': 100,    # Maximum queued messages
            'cors_allowed_origins': [],  # To be populated by environment configs
            'compression_threshold': 1024,  # Compress messages larger than 1KB
            'async_mode': 'eventlet',  # Default async mode
            'cookie': {
                'name': 'realtime_session',
                'path': '/',
                'secure': True,
                'httponly': True,
                'samesite': 'Lax'
            }
        }
        
        # Presence tracking settings
        self.PRESENCE_SETTINGS = {
            'user_timeout': 300,  # Consider user offline after 5 minutes of inactivity
            'heartbeat_interval': 30,  # Send heartbeat every 30 seconds
            'status_change_debounce': 3,  # Wait 3 seconds before processing status changes
            'activity_tracking': True,  # Track user activity
            'status_options': ['online', 'away', 'busy', 'offline'],
            'default_status': 'online',
            'presence_channel_prefix': 'presence:',
            'max_clients_per_user': 5  # Maximum number of connected clients per user
        }
        
        # Collaboration settings
        self.COLLABORATION_SETTINGS = {
            'document_lock_timeout': 300,  # Lock expires after 5 minutes
            'operation_debounce': 500,  # Wait 500ms before sending batched operations
            'conflict_resolution': 'last_write_wins',  # Conflict resolution strategy
            'max_concurrent_editors': 5,  # Maximum number of concurrent editors per document
            'sync_interval': 2000,  # Synchronize state every 2 seconds
            'typing_indicator_timeout': 5,  # Typing indicator disappears after 5 seconds
            'change_tracking': True,  # Track changes with attribution
            'version_history': True  # Maintain version history
        }
        
        # Connection settings
        self.CONNECTION_SETTINGS = {
            'max_connections': 10000,  # Maximum concurrent connections
            'connection_timeout': 10,  # Connection timeout in seconds
            'max_reconnection_attempts': 5,  # Maximum reconnection attempts
            'reconnection_delay': 1000,  # Initial reconnection delay in ms
            'reconnection_delay_max': 5000,  # Maximum reconnection delay in ms
            'reconnection_jitter': 0.5,  # Randomization factor
            'close_timeout': 10,  # Seconds to wait before force-closing
            'transports': ['websocket', 'polling'],  # Supported transports
            'upgrade_timeout': 10000,  # Timeout for transport upgrades in ms
            'ping_interval': 25000,  # Ping interval in ms
            'ping_timeout': 20000  # Ping timeout in ms
        }
        
        # Redis PubSub settings
        self.REDIS_PUBSUB_SETTINGS = {
            'channel_prefix': 'tms:rt:',  # Prefix for all channels
            'presence_channel': 'tms:rt:presence',  # Channel for presence updates
            'event_channel': 'tms:rt:events',  # Channel for system events
            'task_channel_prefix': 'tms:rt:task:',  # Prefix for task-specific channels
            'project_channel_prefix': 'tms:rt:project:',  # Prefix for project-specific channels
            'broadcast_channel': 'tms:rt:broadcast',  # Channel for system-wide broadcasts
            'user_channel_prefix': 'tms:rt:user:',  # Prefix for user-specific channels
            'max_subscribers': 10000,  # Maximum subscribers across all channels
            'message_expiry': 86400,  # TTL for persisted messages (1 day)
            'channel_cleanup_interval': 3600  # Cleanup unused channels every hour
        }
    
    def get_websocket_settings(self) -> dict:
        """
        Returns the WebSocket configuration settings.
        
        Returns:
            dict: WebSocket configuration settings
        """
        return self.WEBSOCKET_SETTINGS
    
    def get_presence_settings(self) -> dict:
        """
        Returns the presence tracking configuration settings.
        
        Returns:
            dict: Presence configuration settings
        """
        return self.PRESENCE_SETTINGS
    
    def get_collaboration_settings(self) -> dict:
        """
        Returns the collaborative editing configuration settings.
        
        Returns:
            dict: Collaboration configuration settings
        """
        return self.COLLABORATION_SETTINGS
    
    def get_connection_settings(self) -> dict:
        """
        Returns the connection management configuration settings.
        
        Returns:
            dict: Connection configuration settings
        """
        return self.CONNECTION_SETTINGS
    
    def get_redis_pubsub_settings(self) -> dict:
        """
        Returns the Redis PubSub configuration settings.
        
        Returns:
            dict: Redis PubSub configuration settings
        """
        return self.REDIS_PUBSUB_SETTINGS


class RealtimeDevConfig(DevelopmentConfig, RealtimeConfig):
    """
    Development environment configuration for the Realtime Service.
    """
    
    def __init__(self):
        """
        Initialize the development configuration for Realtime service.
        """
        # Initialize both parent classes
        DevelopmentConfig.__init__(self)
        RealtimeConfig.__init__(self)
        
        # Override settings for development environment
        self.DEBUG = True
        
        # Configure less restrictive CORS for development
        self.WEBSOCKET_SETTINGS.update({
            'cors_allowed_origins': ['http://localhost:3000', 'http://127.0.0.1:3000', '*'],
            'cookie': {
                'name': 'realtime_session',
                'path': '/',
                'secure': False,  # Allow non-HTTPS for development
                'httponly': True,
                'samesite': 'Lax'
            }
        })
        
        # Set longer timeouts for easier debugging
        self.CONNECTION_SETTINGS.update({
            'connection_timeout': 30,  # Longer timeout for development
            'max_reconnection_attempts': 10,  # More reconnection attempts for development
            'close_timeout': 30  # Longer close timeout for development
        })
        
        # Configure WebSocket settings for development
        self.WEBSOCKET_SETTINGS.update({
            'ping_timeout': 120000,  # 2 minutes for development
            'async_mode': 'eventlet',  # Eventlet works well for development
            'debug': True  # Enable WebSocket debug mode
        })


class RealtimeProdConfig(ProductionConfig, RealtimeConfig):
    """
    Production environment configuration for the Realtime Service.
    """
    
    def __init__(self):
        """
        Initialize the production configuration for Realtime service.
        """
        # Initialize both parent classes
        ProductionConfig.__init__(self)
        RealtimeConfig.__init__(self)
        
        # Apply strict security settings for production
        self.DEBUG = False
        
        # Configure restrictive CORS with validated origins
        self.WEBSOCKET_SETTINGS.update({
            'cors_allowed_origins': [
                'https://taskmanagement.example.com',
                'https://api.taskmanagement.example.com'
            ],
            'max_message_size': 256 * 1024,  # Reduced message size for production
            'compression_threshold': 512,  # More aggressive compression
            'async_mode': 'gevent'  # Use gevent for production performance
        })
        
        # Optimize connection parameters for production scale
        self.CONNECTION_SETTINGS.update({
            'max_connections': 50000,  # Higher limit for production
            'connection_timeout': 5,  # Shorter timeout for production efficiency
            'max_reconnection_attempts': 3,  # Fewer reconnection attempts in production
            'close_timeout': 5,  # Shorter close timeout in production
            'transports': ['websocket']  # Only use WebSocket in production for performance
        })
        
        # Configure performance-focused WebSocket settings
        self.WEBSOCKET_SETTINGS.update({
            'ping_interval': 15000,  # 15 seconds between pings for faster failure detection
            'ping_timeout': 30000,  # 30 seconds before timing out
            'debug': False  # Disable WebSocket debug mode in production
        })
        
        # Set up production Redis cluster configuration
        self.REDIS_PUBSUB_SETTINGS.update({
            'message_expiry': 43200,  # Reduce TTL to 12 hours in production
            'channel_cleanup_interval': 1800  # More frequent cleanup (30 minutes)
        })


class RealtimeTestConfig(TestingConfig, RealtimeConfig):
    """
    Testing environment configuration for the Realtime Service.
    """
    
    def __init__(self):
        """
        Initialize the testing configuration for Realtime service.
        """
        # Initialize both parent classes
        TestingConfig.__init__(self)
        RealtimeConfig.__init__(self)
        
        # Configure test-specific settings
        self.TEST_MODE = True
        
        # Configure shorter timeouts for faster tests
        self.CONNECTION_SETTINGS.update({
            'connection_timeout': 1,  # 1 second timeout for tests
            'reconnection_delay': 10,  # Minimal reconnection delay for tests
            'max_reconnection_attempts': 1  # Only attempt reconnection once in tests
        })
        
        # Set up mock Redis backend for testing
        self.REDIS_PUBSUB_SETTINGS.update({
            'message_expiry': 60,  # Short TTL for test messages
            'channel_cleanup_interval': 10  # Frequent cleanup for tests
        })
        
        # Configure in-memory pubsub for tests
        self.WEBSOCKET_SETTINGS.update({
            'ping_interval': 100,  # Very short ping interval
            'ping_timeout': 100,  # Very short ping timeout
            'async_mode': 'threading',  # Use threading for tests
            'debug': True  # Enable debugging for tests
        })


# Map environment names to their configuration classes
CONFIG = {
    'development': RealtimeDevConfig(),
    'production': RealtimeProdConfig(),
    'testing': RealtimeTestConfig()
}


def get_config(env=ENV):
    """
    Retrieve the appropriate configuration class based on the environment.
    
    Args:
        env (str): The environment name (development, production, testing)
        
    Returns:
        The configuration object for the specified environment
    """
    if env in CONFIG:
        return CONFIG[env]
    
    # Fallback to development if environment not found
    logger.warning(f"Configuration for environment '{env}' not found. Using development config.")
    return CONFIG['development']