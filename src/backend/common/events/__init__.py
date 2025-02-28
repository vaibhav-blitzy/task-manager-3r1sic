"""
Event module for the Task Management System.

This module provides a centralized event-driven communication system across microservices
within the Task Management System. It exposes a clean API for publishing and subscribing
to events, enabling decoupled service interactions and real-time updates.
"""

# Import internal components
from .event_bus import (
    EventBus, 
    RedisEventBus, 
    InMemoryEventBus, 
    create_event, 
    get_event_bus_instance
)
from .handlers import (
    BaseEventHandler,
    TaskEventHandler,
    ProjectEventHandler,
    NotificationEventHandler,
    AuditEventHandler,
    register_handler,
    initialize_handlers,
    dispatch_event,
    handle_with_retry,
    event_handler_factory
)
from ..logging.logger import get_logger
from ..exceptions.api_exceptions import EventBusException

# Configure module logger
logger = get_logger('events')

# Standard event types used throughout the system
EVENT_TYPES = {
    'TASK': {
        'CREATED': 'task.created',
        'UPDATED': 'task.updated',
        'STATUS_CHANGED': 'task.status_changed',
        'ASSIGNED': 'task.assigned',
        'COMMENTED': 'task.commented',
        'DELETED': 'task.deleted'
    },
    'PROJECT': {
        'CREATED': 'project.created',
        'UPDATED': 'project.updated',
        'MEMBER_ADDED': 'project.member_added',
        'MEMBER_REMOVED': 'project.member_removed',
        'COMPLETED': 'project.completed',
        'DELETED': 'project.deleted'
    },
    'USER': {
        'REGISTERED': 'user.registered',
        'UPDATED': 'user.updated',
        'SETTINGS_CHANGED': 'user.settings_changed',
        'LOGGED_IN': 'user.logged_in',
        'LOGGED_OUT': 'user.logged_out'
    },
    'NOTIFICATION': {
        'CREATED': 'notification.created',
        'DELIVERED': 'notification.delivered',
        'READ': 'notification.read'
    },
    'FILE': {
        'UPLOADED': 'file.uploaded',
        'DELETED': 'file.deleted',
        'SCANNED': 'file.scanned'
    },
    'SYSTEM': {
        'ERROR': 'system.error',
        'WARNING': 'system.warning',
        'INFO': 'system.info'
    }
}


def initialize_event_system() -> bool:
    """
    Initializes the event system by setting up the event bus and registering all handlers.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        # Get event bus instance using get_event_bus_instance()
        event_bus = get_event_bus_instance()
        
        logger.info("Initializing event system")
        
        # Initialize all registered event handlers using initialize_handlers()
        initialize_handlers()
        
        logger.info("Event system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize event system: {str(e)}", exc_info=True)
        return False


def publish(event_type: str, payload: dict, source: str) -> bool:
    """
    Convenience function to publish an event to the event bus, simplified for common use.
    
    Args:
        event_type: Type of the event to publish
        payload: Event data payload
        source: Source component publishing the event
    
    Returns:
        bool: True if published successfully, False otherwise
    """
    try:
        # Create event object using create_event() with type, payload and source
        event = create_event(event_type, payload, source)
        
        # Get event bus instance using get_event_bus_instance()
        event_bus = get_event_bus_instance()
        
        # Publish event to the event bus
        result = event_bus.publish(event_type, event)
        
        logger.debug(f"Published event {event['id']} of type {event_type}")
        return result
    except Exception as e:
        logger.error(f"Failed to publish event of type {event_type}: {str(e)}", exc_info=True)
        return False


def subscribe(event_type: str, handler: callable) -> str:
    """
    Convenience function to subscribe a handler to a specific event type.
    
    Args:
        event_type: Type of event to subscribe to
        handler: Function to call when event is received
    
    Returns:
        str: Subscription ID if successful, None otherwise
    """
    try:
        # Get event bus instance using get_event_bus_instance()
        event_bus = get_event_bus_instance()
        
        # Subscribe handler to the specified event type
        subscription_id = event_bus.subscribe(event_type, handler)
        
        logger.debug(f"Subscribed handler to event type {event_type}")
        return subscription_id
    except Exception as e:
        logger.error(f"Failed to subscribe handler to event type {event_type}: {str(e)}", exc_info=True)
        return None


def unsubscribe(subscription_id: str) -> bool:
    """
    Convenience function to unsubscribe a handler using its subscription ID.
    
    Args:
        subscription_id: ID of the subscription to cancel
    
    Returns:
        bool: True if unsubscribed successfully, False otherwise
    """
    try:
        # Get event bus instance using get_event_bus_instance()
        event_bus = get_event_bus_instance()
        
        # Unsubscribe using the provided subscription ID
        result = event_bus.unsubscribe(subscription_id)
        
        logger.debug(f"Unsubscribed handler with ID {subscription_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to unsubscribe handler with ID {subscription_id}: {str(e)}", exc_info=True)
        return False