"""
Event handler framework for the Task Management System.

This module provides the foundational classes and utilities for processing events
in an event-driven architecture. It includes abstract base classes for event handlers,
registration mechanisms, retry capabilities, and dead letter queue handling.
"""

# Standard library imports
import abc
import json
import time
import uuid
import functools
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime

# Internal imports
from ..logging.logger import get_logger
from .event_bus import EventBus, get_event_bus_instance, validate_event
from ..exceptions.api_exceptions import EventBusException
from ..database.redis.connection import RedisClient

# Module logger
logger = get_logger(__name__)

# Global registry of event handlers
EVENT_HANDLER_REGISTRY = {}

# Retry configuration
MAX_RETRY_COUNT = 3
DEFAULT_BACKOFF_FACTOR = 2.0


def event_handler(event_type: str) -> Callable:
    """
    Decorator that registers a function as an event handler for a specific event type.
    
    Args:
        event_type: The type of event this handler processes
        
    Returns:
        Decorator function that registers the handler
    """
    def decorator(handler_func: Callable) -> Callable:
        # Register the handler in the global registry
        if event_type not in EVENT_HANDLER_REGISTRY:
            EVENT_HANDLER_REGISTRY[event_type] = []
        
        if handler_func not in EVENT_HANDLER_REGISTRY[event_type]:
            EVENT_HANDLER_REGISTRY[event_type].append(handler_func)
            
            # Subscribe to event bus if possible
            try:
                event_bus = get_event_bus_instance()
                event_bus.subscribe(event_type, handler_func)
                logger.info(f"Registered handler {handler_func.__name__} for event type: {event_type}")
            except Exception as e:
                logger.warning(f"Could not subscribe to event bus: {str(e)}")
        
        return handler_func
    
    return decorator


def process_event(event: dict) -> bool:
    """
    Process an event by finding and executing the appropriate handler.
    
    Args:
        event: The event to process
        
    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Validate event structure
        if not validate_event(event):
            logger.error(f"Invalid event format: {event}")
            return False
        
        event_type = event.get('type')
        if not event_type:
            logger.error(f"Event missing type: {event}")
            return False
        
        # Find handlers for this event type
        handlers = EVENT_HANDLER_REGISTRY.get(event_type, [])
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event_type}")
            return False
        
        # Execute each handler
        success = True
        for handler in handlers:
            try:
                handler_result = handler(event)
                if handler_result is False:  # Explicit False return indicates failure
                    success = False
                    logger.warning(f"Handler {handler.__name__} returned failure for event {event.get('id')}")
            except Exception as e:
                success = False
                logger.error(f"Error in handler {handler.__name__} for event {event.get('id')}: {str(e)}", exc_info=True)
        
        if success:
            logger.debug(f"Successfully processed event {event.get('id')} of type {event_type}")
        
        return success
    
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return False


def retry_event_processing(max_retries: int = MAX_RETRY_COUNT, 
                           backoff_factor: float = DEFAULT_BACKOFF_FACTOR) -> Callable:
    """
    Decorator that adds retry capability to event handlers with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Decorator function that adds retry logic
    """
    def decorator(handler_func: Callable) -> Callable:
        @functools.wraps(handler_func)
        def wrapper(event: dict) -> bool:
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # Call the original handler function
                    result = handler_func(event)
                    return result
                except Exception as e:
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for handler {handler_func.__name__} "
                            f"on event {event.get('id')}: {str(e)}", 
                            exc_info=True
                        )
                        # Send to DLQ after all retries fail
                        send_to_dead_letter_queue(event, e, retry_count)
                        return False
                    
                    # Calculate backoff time
                    backoff_time = backoff_factor ** retry_count
                    logger.warning(
                        f"Retrying handler {handler_func.__name__} for event {event.get('id')} "
                        f"after error: {str(e)} (attempt {retry_count}/{max_retries}, "
                        f"backoff: {backoff_time:.2f}s)"
                    )
                    
                    # Wait before retrying
                    time.sleep(backoff_time)
            
            # Should not reach here, but just in case
            return False
        
        return wrapper
    
    return decorator


def send_to_dead_letter_queue(event: dict, error: Exception, retry_count: int) -> bool:
    """
    Sends a failed event to the dead letter queue for later processing.
    
    Args:
        event: The original event that failed processing
        error: The exception that occurred
        retry_count: Number of retry attempts made
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Create dead letter event with metadata about the failure
        dead_letter_event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "deadletter",
            "source": "event_handler",
            "version": "1.0",
            "payload": {
                "original_event": event,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "retry_count": retry_count
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Use the event bus to publish to dead letter topic
        try:
            event_bus = get_event_bus_instance()
            result = event_bus.publish("deadletter", dead_letter_event)
            logger.info(f"Sent event {event.get('id')} to dead letter queue after {retry_count} failed attempts")
            return result
        except Exception as e:
            # If event bus fails, try direct Redis storage as fallback
            logger.warning(f"Could not publish to event bus, trying direct Redis storage: {str(e)}")
            redis_client = RedisClient()
            dlq_key = f"dlq:{event.get('type')}:{event.get('id')}"
            result = redis_client.set_json(dlq_key, dead_letter_event, expiration=86400*7)  # 7 days TTL
            logger.info(f"Stored event {event.get('id')} in Redis dead letter queue")
            return result
    
    except Exception as e:
        logger.error(f"Failed to send event {event.get('id')} to dead letter queue: {str(e)}", exc_info=True)
        return False


class EventHandler(abc.ABC):
    """
    Abstract base class for event handlers that process specific event types.
    
    All specific event handlers should inherit from this class and implement the
    handle method to process events of their target type.
    """
    
    def __init__(self, event_type: str, auto_register: bool = False):
        """
        Initialize the event handler.
        
        Args:
            event_type: The type of events this handler processes
            auto_register: Whether to automatically register with the event bus
        """
        self.event_type = event_type
        logger.debug(f"Initializing handler for event type: {event_type}")
        
        if auto_register:
            self.register()
    
    @abc.abstractmethod
    def handle(self, event_data: dict) -> bool:
        """
        Abstract method to handle an event of the specified type.
        
        Args:
            event_data: The event data to process
            
        Returns:
            True if handled successfully, False otherwise
        """
        pass
    
    def register(self) -> bool:
        """
        Register this handler with the event bus.
        
        Returns:
            True if registered successfully, False otherwise
        """
        try:
            event_bus = get_event_bus_instance()
            event_bus.subscribe(self.event_type, self.handle)
            logger.info(f"Registered handler for event type: {self.event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to register handler for event type: {self.event_type}: {str(e)}")
            return False
    
    def unregister(self) -> bool:
        """
        Unregister this handler from the event bus.
        
        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            event_bus = get_event_bus_instance()
            event_bus.unsubscribe(self.event_type, self.handle)
            logger.info(f"Unregistered handler for event type: {self.event_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister handler for event type: {self.event_type}: {str(e)}")
            return False


class TaskEventHandler(EventHandler):
    """
    Base class for handlers that process task-related events.
    
    Provides specialized methods for handling different task event subtypes.
    """
    
    def __init__(self, event_type: str, auto_register: bool = True):
        """
        Initialize the task event handler.
        
        Args:
            event_type: The task event type this handler processes
            auto_register: Whether to automatically register with the event bus
        """
        super().__init__(event_type, auto_register)
    
    def handle(self, event_data: dict) -> bool:
        """
        Handle a task event by delegating to specific methods based on event subtype.
        
        Args:
            event_data: The event data to process
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # Extract task data and event subtype from payload
            payload = event_data.get('payload', {})
            task_data = payload.get('task', {})
            event_subtype = payload.get('subtype')
            
            # Basic validation
            if not task_data:
                logger.error(f"Missing task data in event: {event_data.get('id')}")
                return False
            
            # Delegate to appropriate handler method based on subtype
            if event_subtype == 'created':
                result = self.handle_task_created(task_data)
            elif event_subtype == 'updated':
                result = self.handle_task_updated(task_data)
            elif event_subtype == 'deleted':
                result = self.handle_task_deleted(task_data)
            elif event_subtype == 'status_changed':
                result = self.handle_task_status_changed(task_data)
            else:
                # Default handling if subtype not recognized
                logger.warning(f"Unknown task event subtype: {event_subtype}")
                result = self.handle_task_updated(task_data)
            
            if result:
                logger.debug(f"Successfully handled {event_subtype} event for task {task_data.get('id')}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error handling task event {event_data.get('id')}: {str(e)}", exc_info=True)
            return False
    
    def handle_task_created(self, task_data: dict) -> bool:
        """
        Handle task creation events.
        
        Args:
            task_data: The task data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for task created: {task_data.get('id')}")
        return True
    
    def handle_task_updated(self, task_data: dict) -> bool:
        """
        Handle task update events.
        
        Args:
            task_data: The task data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for task updated: {task_data.get('id')}")
        return True
    
    def handle_task_deleted(self, task_data: dict) -> bool:
        """
        Handle task deletion events.
        
        Args:
            task_data: The task data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for task deleted: {task_data.get('id')}")
        return True
    
    def handle_task_status_changed(self, task_data: dict) -> bool:
        """
        Handle task status change events.
        
        Args:
            task_data: The task data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for task status change: {task_data.get('id')}")
        return True


class ProjectEventHandler(EventHandler):
    """
    Base class for handlers that process project-related events.
    
    Provides specialized methods for handling different project event subtypes.
    """
    
    def __init__(self, event_type: str, auto_register: bool = True):
        """
        Initialize the project event handler.
        
        Args:
            event_type: The project event type this handler processes
            auto_register: Whether to automatically register with the event bus
        """
        super().__init__(event_type, auto_register)
    
    def handle(self, event_data: dict) -> bool:
        """
        Handle a project event by delegating to specific methods based on event subtype.
        
        Args:
            event_data: The event data to process
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            # Extract project data and event subtype from payload
            payload = event_data.get('payload', {})
            project_data = payload.get('project', {})
            event_subtype = payload.get('subtype')
            
            # Basic validation
            if not project_data:
                logger.error(f"Missing project data in event: {event_data.get('id')}")
                return False
            
            # Delegate to appropriate handler method based on subtype
            if event_subtype == 'created':
                result = self.handle_project_created(project_data)
            elif event_subtype == 'updated':
                result = self.handle_project_updated(project_data)
            elif event_subtype == 'deleted':
                result = self.handle_project_deleted(project_data)
            elif event_subtype == 'member_added':
                result = self.handle_project_member_added(project_data)
            elif event_subtype == 'member_removed':
                result = self.handle_project_member_removed(project_data)
            else:
                # Default handling if subtype not recognized
                logger.warning(f"Unknown project event subtype: {event_subtype}")
                result = self.handle_project_updated(project_data)
            
            if result:
                logger.debug(f"Successfully handled {event_subtype} event for project {project_data.get('id')}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error handling project event {event_data.get('id')}: {str(e)}", exc_info=True)
            return False
    
    def handle_project_created(self, project_data: dict) -> bool:
        """
        Handle project creation events.
        
        Args:
            project_data: The project data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for project created: {project_data.get('id')}")
        return True
    
    def handle_project_updated(self, project_data: dict) -> bool:
        """
        Handle project update events.
        
        Args:
            project_data: The project data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for project updated: {project_data.get('id')}")
        return True
    
    def handle_project_deleted(self, project_data: dict) -> bool:
        """
        Handle project deletion events.
        
        Args:
            project_data: The project data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for project deleted: {project_data.get('id')}")
        return True
    
    def handle_project_member_added(self, project_data: dict) -> bool:
        """
        Handle project member addition events.
        
        Args:
            project_data: The project data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for project member added: {project_data.get('id')}")
        return True
    
    def handle_project_member_removed(self, project_data: dict) -> bool:
        """
        Handle project member removal events.
        
        Args:
            project_data: The project data
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Default implementation - override in subclasses
        logger.debug(f"Default handling for project member removed: {project_data.get('id')}")
        return True


class DeadLetterHandler(EventHandler):
    """
    Handler for processing failed events that reached the dead letter queue.
    
    This handler processes dead letter events by evaluating their retriability
    and either reprocessing them or logging permanent failures.
    """
    
    def __init__(self):
        """
        Initialize the dead letter handler.
        """
        super().__init__("deadletter", True)
    
    def handle(self, event_data: dict) -> bool:
        """
        Process failed events and attempt recovery or log permanent failures.
        
        Args:
            event_data: The dead letter event data
            
        Returns:
            True if handled successfully, False otherwise
        """
        try:
            payload = event_data.get('payload', {})
            original_event = payload.get('original_event', {})
            error_info = payload.get('error', {})
            retry_count = error_info.get('retry_count', 0)
            
            logger.info(f"Processing dead letter event: {event_data.get('id')}, original event: {original_event.get('id')}")
            
            # Determine if the event can be retried
            if self.is_retriable(event_data):
                logger.info(f"Retrying event {original_event.get('id')} (attempt {retry_count + 1})")
                
                # Republish the original event
                return self.republish_event(original_event, retry_count)
            else:
                logger.warning(
                    f"Event {original_event.get('id')} cannot be retried. "
                    f"Error: {error_info.get('type')}: {error_info.get('message')}"
                )
                
                # Here would go logic for alerting, logging to permanent failure store, etc.
                return True  # We've handled it by deciding not to retry
                
        except Exception as e:
            logger.error(f"Error processing dead letter event {event_data.get('id')}: {str(e)}", exc_info=True)
            return False
    
    def is_retriable(self, event_data: dict) -> bool:
        """
        Determine if an event is eligible for retry based on error type and retry count.
        
        Args:
            event_data: The dead letter event data
            
        Returns:
            True if event can be retried, False otherwise
        """
        payload = event_data.get('payload', {})
        error_info = payload.get('error', {})
        error_type = error_info.get('type', '')
        retry_count = error_info.get('retry_count', 0)
        
        # Define error types that are not retriable
        non_retriable_errors = [
            'ValidationError',
            'AuthorizationError',
            'NotFoundError',
            'ConflictError'
        ]
        
        # Check if error type is non-retriable
        if error_type in non_retriable_errors:
            return False
        
        # Check if we've exceeded maximum retry count
        # Note: This is a separate check from the retry mechanism to allow
        # for manual intervention after automated retries have failed
        if retry_count >= MAX_RETRY_COUNT * 2:  # Double the normal retry count for DLQ
            return False
        
        return True
    
    def republish_event(self, original_event: dict, retry_count: int) -> bool:
        """
        Republish an event to its original topic for retry.
        
        Args:
            original_event: The original event to republish
            retry_count: Current retry count
            
        Returns:
            True if republished successfully, False otherwise
        """
        try:
            event_type = original_event.get('type')
            
            # Update the event with retry information
            if 'metadata' not in original_event:
                original_event['metadata'] = {}
            
            original_event['metadata']['retry_count'] = retry_count + 1
            original_event['metadata']['reprocessed_at'] = datetime.utcnow().isoformat()
            
            # Publish the event back to its original topic
            event_bus = get_event_bus_instance()
            result = event_bus.publish(event_type, original_event)
            
            logger.info(f"Republished event {original_event.get('id')} to {event_type} topic")
            return result
            
        except Exception as e:
            logger.error(f"Failed to republish event {original_event.get('id')}: {str(e)}", exc_info=True)
            return False