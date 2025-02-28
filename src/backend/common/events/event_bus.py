"""
Event Bus module for the Task Management System.

This module implements a publish-subscribe event bus system that enables
asynchronous communication between microservices. It provides functionality
for creating, publishing, and subscribing to events across the application.
"""

# Standard library imports
import uuid
import json
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import threading
import functools

# Internal imports
from ..logging.logger import get_logger
from ..config import get_config
from ..exceptions.api_exceptions import DependencyError
from ..database.redis.connection import get_redis_connection

# Module logger
logger = get_logger(__name__)

# Singleton event bus instance
_event_bus_instance = None

# Event format version
EVENT_FORMAT_VERSION = "1.0"


# Custom exception for event bus errors
class EventBusException(DependencyError):
    """Exception raised for event bus errors."""
    
    def __init__(self, message="Event bus error occurred", *args, **kwargs):
        super().__init__(message=message, dependency="EventBus", *args, **kwargs)


def create_event(event_type: str, payload: dict, source: str) -> dict:
    """
    Creates a standardized event object with required metadata.
    
    Args:
        event_type: The type of the event (e.g., 'task.created', 'project.updated')
        payload: The event data
        source: The system component that generated the event
        
    Returns:
        Formatted event with metadata and payload
    """
    if not event_type or not isinstance(event_type, str):
        raise ValueError("Event type must be a non-empty string")
    
    if not isinstance(payload, dict):
        raise ValueError("Event payload must be a dictionary")
    
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "source": source,
        "version": EVENT_FORMAT_VERSION,
        "payload": payload
    }
    
    logger.debug(f"Created event: {event_type} with ID: {event['id']}")
    return event


def validate_event(event: dict) -> bool:
    """
    Validates that an event object has the required structure and fields.
    
    Args:
        event: The event object to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(event, dict):
        logger.error("Event must be a dictionary")
        return False
    
    # Check required fields
    required_fields = ["id", "timestamp", "type", "payload"]
    for field in required_fields:
        if field not in event:
            logger.error(f"Event missing required field: {field}")
            return False
    
    # Validate types
    if not isinstance(event.get("id"), str):
        logger.error("Event ID must be a string")
        return False
    
    if not isinstance(event.get("timestamp"), str):
        logger.error("Event timestamp must be a string")
        return False
    
    if not isinstance(event.get("type"), str):
        logger.error("Event type must be a string")
        return False
    
    if not isinstance(event.get("payload"), dict):
        logger.error("Event payload must be a dictionary")
        return False
    
    return True


def with_error_handling(func: callable) -> callable:
    """
    Decorator for event bus methods to handle exceptions consistently.
    
    Args:
        func: The function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise EventBusException(f"Event bus error: {str(e)}")
    
    return wrapper


def get_event_bus_instance() -> 'EventBus':
    """
    Singleton accessor for the event bus instance.
    
    Returns:
        Singleton instance of EventBus
    """
    global _event_bus_instance
    
    if _event_bus_instance is None:
        logger.debug("Creating new EventBus instance")
        _event_bus_instance = EventBus()
    
    return _event_bus_instance


class EventBus:
    """
    Core event bus implementation providing publish-subscribe functionality.
    
    This class manages event publishing and subscription using Redis as the
    transport mechanism. It handles the lifecycle of the event bus, including
    starting and stopping the background thread that listens for events.
    """
    
    def __init__(self):
        """
        Initializes the event bus with configuration.
        """
        # Dictionary to track subscriptions by event type
        self._subscribers = {}
        
        # Dictionary to track event handlers
        self._event_handlers = {}
        
        # Redis connection
        self._redis = get_redis_connection()
        
        # Background thread for subscription handling
        self._subscription_thread = None
        
        # Flag to control the background thread
        self._running = False
        
        # Get configuration
        self._config = get_config()
        
        logger.info("EventBus initialized")
    
    @with_error_handling
    def start(self) -> bool:
        """
        Starts the event bus subscription thread.
        
        Returns:
            True if started successfully
        """
        if self._running:
            logger.debug("EventBus already running")
            return True
        
        self._running = True
        
        # Create and start the subscription thread
        self._subscription_thread = threading.Thread(
            target=self._subscription_loop,
            name="EventBus-SubscriptionThread",
            daemon=True
        )
        self._subscription_thread.start()
        
        logger.info("EventBus started")
        return True
    
    @with_error_handling
    def stop(self) -> bool:
        """
        Stops the event bus subscription thread.
        
        Returns:
            True if stopped successfully
        """
        if not self._running:
            logger.debug("EventBus already stopped")
            return True
        
        self._running = False
        
        # Wait for subscription thread to terminate
        if self._subscription_thread and self._subscription_thread.is_alive():
            logger.debug("Waiting for subscription thread to terminate")
            self._subscription_thread.join(timeout=5.0)
        
        logger.info("EventBus stopped")
        return True
    
    @with_error_handling
    def publish(self, event_type: str, event: dict) -> bool:
        """
        Publishes an event to the specified channel.
        
        Args:
            event_type: The type of the event (also used as the channel name)
            event: The event object to publish
            
        Returns:
            True if published successfully
        """
        # Validate event
        if not validate_event(event):
            logger.error(f"Invalid event format for event type: {event_type}")
            return False
        
        # Serialize event to JSON
        try:
            event_json = json.dumps(event)
        except Exception as e:
            logger.error(f"Error serializing event: {str(e)}")
            return False
        
        # Publish to Redis channel
        result = self._redis.publish(event_type, event_json)
        
        logger.debug(f"Published event {event['id']} to channel {event_type}, received by {result} subscribers")
        return True
    
    @with_error_handling
    def subscribe(self, event_type: str, handler_func: callable) -> bool:
        """
        Subscribes a handler function to an event type.
        
        Args:
            event_type: The event type to subscribe to
            handler_func: The function to call when events of this type are received
            
        Returns:
            True if subscribed successfully
        """
        if not event_type or not isinstance(event_type, str):
            raise ValueError("Event type must be a non-empty string")
        
        if not callable(handler_func):
            raise ValueError("Handler must be a callable function")
        
        # Initialize the subscriber list for this event type if needed
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Add the handler to the subscribers list
        if handler_func not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler_func)
            
            # Update Redis subscription
            if self._running:
                # Ensure the Redis connection is subscribed to this channel
                pubsub = self._redis.pubsub()
                pubsub.subscribe(event_type)
                pubsub.close()
            
            logger.debug(f"Added subscription for event type: {event_type}")
        else:
            logger.debug(f"Handler already subscribed to event type: {event_type}")
        
        return True
    
    @with_error_handling
    def unsubscribe(self, event_type: str, handler_func: callable) -> bool:
        """
        Unsubscribes a handler function from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            handler_func: The function to remove from the subscribers list
            
        Returns:
            True if unsubscribed successfully, False if not found
        """
        if event_type not in self._subscribers:
            logger.debug(f"No subscribers found for event type: {event_type}")
            return False
        
        # Remove the handler from the subscribers list
        if handler_func in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler_func)
            logger.debug(f"Removed subscription for event type: {event_type}")
            
            # If no subscribers left, remove the event type
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
                
                # Update Redis subscription if running
                if self._running:
                    # Ensure Redis is unsubscribed from this channel
                    pubsub = self._redis.pubsub()
                    pubsub.unsubscribe(event_type)
                    pubsub.close()
                
                logger.debug(f"Removed event type with no subscribers: {event_type}")
            
            return True
        
        logger.debug(f"Handler not found for event type: {event_type}")
        return False
    
    def _message_handler(self, channel: str, message: str) -> None:
        """
        Internal method that processes received events and calls subscribed handlers.
        
        Args:
            channel: The channel (event type) the message was received on
            message: The message content (JSON string)
        """
        # Decode channel from bytes if needed
        if isinstance(channel, bytes):
            channel = channel.decode('utf-8')
        
        try:
            # Parse the message
            event = json.loads(message)
            
            # Validate the event structure
            if not validate_event(event):
                logger.error(f"Received invalid event on channel {channel}: {message}")
                return
            
            # Check if we have subscribers for this event type
            event_type = event.get('type')
            if event_type in self._subscribers:
                logger.debug(f"Processing event {event.get('id')} of type {event_type}")
                
                # Call each handler with the event
                for handler in self._subscribers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {str(e)}", exc_info=True)
                        # Continue processing other handlers
            else:
                logger.debug(f"No handlers registered for event type: {event_type}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON message from channel {channel}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message from channel {channel}: {str(e)}", exc_info=True)
    
    def _subscription_loop(self) -> None:
        """
        Background thread that listens for Redis Pub/Sub messages.
        """
        logger.info("Starting subscription loop")
        
        retry_count = 0
        max_retries = 5
        retry_delay = 1.0
        
        while self._running:
            try:
                # Get a pubsub connection
                pubsub = self._redis.pubsub()
                
                # Subscribe to all event types in the subscribers dictionary
                channels = list(self._subscribers.keys())
                if channels:
                    logger.debug(f"Subscribing to channels: {channels}")
                    pubsub.subscribe(*channels)
                else:
                    logger.debug("No channels to subscribe to")
                    # Sleep briefly and check again
                    time.sleep(1.0)
                    continue
                
                # Reset retry counter on successful connection
                retry_count = 0
                
                # Listen for messages with a timeout
                for message in pubsub.listen():
                    if not self._running:
                        break
                    
                    if message['type'] == 'message':
                        # Handle the message in the current thread
                        self._message_handler(
                            message['channel'],
                            message['data']
                        )
                
                # Close the pubsub connection
                pubsub.close()
            
            except Exception as e:
                # Handle connection errors and retry with backoff
                if not self._running:
                    break
                
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Max retries exceeded in subscription loop: {str(e)}")
                    self._running = False
                    break
                
                logger.error(f"Error in subscription loop (retry {retry_count}/{max_retries}): {str(e)}")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30.0)  # Exponential backoff up to 30 seconds
        
        logger.info("Subscription loop terminated")
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Returns the number of subscribers for a given event type.
        
        Args:
            event_type: The event type to count subscribers for
            
        Returns:
            Number of subscribers
        """
        if event_type in self._subscribers:
            return len(self._subscribers[event_type])
        return 0