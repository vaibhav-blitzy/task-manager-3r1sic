"""
Service for tracking and managing user presence information in real-time collaboration.
Handles user online status, activity tracking, and typing indicators across the Task Management System.
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

# Internal imports
from ..models.connection import Connection
from ....common.database.redis.connection import get_redis_client
from ....common.logging.logger import get_logger
from ....common.events.event_bus import get_event_bus_instance, create_event
from ..config import get_config
from ....common.auth.jwt_utils import validate_token

# Module logger
logger = get_logger(__name__)

# Redis client for presence data
redis_client = get_redis_client('presence')

# Event bus for publishing presence events
event_bus = get_event_bus_instance()

# Config for presence settings
config = get_config()

# Valid presence statuses
PRESENCE_STATUSES = ['online', 'away', 'busy', 'offline']

# Default expiry time for presence data (in seconds)
DEFAULT_PRESENCE_EXPIRY = 300  # 5 minutes

# Typing indicator expiry (in seconds)
TYPING_EXPIRY = 10  # 10 seconds


def get_user_presence(user_id: str) -> dict:
    """
    Retrieves presence information for a specific user.
    
    Args:
        user_id: The user ID to get presence for
        
    Returns:
        User presence data including status, last activity, and connection count
    """
    # Find all connections for the user
    connections = Connection.find_by_user_id(user_id)
    
    if not connections:
        # User has no active connections, return offline status
        return {
            "status": "offline",
            "lastActivity": None,
            "connections": 0
        }
    
    # Determine the most "active" status from all connections
    # Order: online > busy > away > offline
    status_priority = {
        "online": 3,
        "busy": 2, 
        "away": 1,
        "offline": 0
    }
    
    current_status = "offline"
    current_priority = 0
    last_activity = None
    
    # Iterate through connections to find the most active status and latest activity
    for conn in connections:
        presence = conn.get("presence", {})
        conn_status = presence.get("status", "offline")
        
        # Update status if this connection has a higher priority status
        if status_priority.get(conn_status, 0) > current_priority:
            current_status = conn_status
            current_priority = status_priority.get(conn_status, 0)
        
        # Update last activity if this is more recent
        conn_activity = presence.get("lastActivity")
        if conn_activity and (not last_activity or conn_activity > last_activity):
            last_activity = conn_activity
    
    # Return presence information
    return {
        "status": current_status,
        "lastActivity": last_activity.isoformat() if last_activity else None,
        "connections": len(connections)
    }


def get_users_presence(user_ids: list) -> dict:
    """
    Retrieves presence information for multiple users.
    
    Args:
        user_ids: List of user IDs to get presence for
        
    Returns:
        Dictionary mapping user IDs to their presence information
    """
    result = {}
    
    # Get presence for each user
    for user_id in user_ids:
        result[user_id] = get_user_presence(user_id)
    
    return result


def get_channel_presence(channel: str, object_type: str, object_id: str) -> dict:
    """
    Retrieves presence information for all users in a specific channel.
    
    Args:
        channel: Channel name (e.g., 'task', 'project')
        object_type: Type of object being subscribed to
        object_id: Unique identifier of the object
        
    Returns:
        Dictionary mapping user IDs to their presence information for the channel
    """
    # Find connections subscribed to this channel
    connections = Connection.find_by_channel(channel, object_type, object_id)
    
    # Extract unique user IDs from connections
    user_ids = set()
    for conn in connections:
        user_ids.add(conn.get_user_id())
    
    # Get presence for all users in the channel
    return get_users_presence(list(user_ids))


def update_presence(connection_id: str, presence_data: dict) -> bool:
    """
    Updates the presence status for a connection.
    
    Args:
        connection_id: The connection ID
        presence_data: Dictionary with presence information
        
    Returns:
        True if update successful, False otherwise
    """
    # Validate presence data
    if not isinstance(presence_data, dict):
        logger.error(f"Invalid presence data type: {type(presence_data)}")
        return False
    
    # Validate status if provided
    status = presence_data.get('status')
    if status and status not in PRESENCE_STATUSES:
        logger.error(f"Invalid presence status: {status}")
        return False
    
    # Find the connection
    connection = Connection.find_by_connection_id(connection_id)
    if not connection:
        logger.error(f"Connection not found: {connection_id}")
        return False
    
    # Update the connection's presence
    if not connection.update_presence(presence_data):
        logger.error(f"Failed to update presence for connection: {connection_id}")
        return False
    
    # Get user ID for event
    user_id = connection.get_user_id()
    
    # Create and publish presence event
    event = create_event(
        'user.presence',
        {
            'user_id': user_id,
            'status': presence_data.get('status'),
            'connection_id': connection_id
        },
        'presence_service'
    )
    
    # Publish to event bus
    event_bus.publish('user.presence', event)
    
    return True


def update_typing_status(connection_id: str, is_typing: bool, location: str) -> bool:
    """
    Updates typing status for a user in a specific context.
    
    Args:
        connection_id: The connection ID
        is_typing: Whether the user is typing
        location: Context where the user is typing (e.g., 'task:123:comment')
        
    Returns:
        True if update successful, False otherwise
    """
    # Find the connection
    connection = Connection.find_by_connection_id(connection_id)
    if not connection:
        logger.error(f"Connection not found: {connection_id}")
        return False
    
    # Update typing status
    if not connection.update_typing_status(is_typing, location):
        logger.error(f"Failed to update typing status for connection: {connection_id}")
        return False
    
    # Get user ID for event
    user_id = connection.get_user_id()
    
    # Create and publish typing event
    event = create_event(
        'user.typing',
        {
            'user_id': user_id,
            'is_typing': is_typing,
            'location': location,
            'connection_id': connection_id
        },
        'presence_service'
    )
    
    # Publish to event bus
    event_bus.publish('user.typing', event)
    
    return True


def handle_disconnect(connection_id: str) -> bool:
    """
    Handles a connection disconnection by updating presence status.
    
    Args:
        connection_id: The connection ID that disconnected
        
    Returns:
        True if handled successfully, False otherwise
    """
    # Find the connection
    connection = Connection.find_by_connection_id(connection_id)
    if not connection:
        logger.error(f"Connection not found for disconnect: {connection_id}")
        return False
    
    # Get user ID for event
    user_id = connection.get_user_id()
    
    # Update connection's presence status to offline
    if not connection.update_presence({'status': 'offline'}):
        logger.error(f"Failed to update presence for disconnection: {connection_id}")
        return False
    
    # Create and publish presence event
    event = create_event(
        'user.presence',
        {
            'user_id': user_id,
            'status': 'offline',
            'connection_id': connection_id,
            'event': 'disconnect'
        },
        'presence_service'
    )
    
    # Publish to event bus
    event_bus.publish('user.presence', event)
    
    return True


def handle_heartbeat(connection_id: str) -> bool:
    """
    Updates connection timestamp for heartbeat/ping messages.
    
    Args:
        connection_id: The connection ID
        
    Returns:
        True if update successful, False otherwise
    """
    # Find the connection
    connection = Connection.find_by_connection_id(connection_id)
    if not connection:
        logger.error(f"Connection not found for heartbeat: {connection_id}")
        return False
    
    # Update ping timestamp
    return connection.update_ping()


def cleanup_stale_presence(max_age_seconds: int) -> int:
    """
    Cleans up presence information for stale connections.
    
    Args:
        max_age_seconds: Maximum age in seconds before a connection is considered stale
        
    Returns:
        Number of connections cleaned up
    """
    # Get all connections
    connections = Connection.find({})
    cleanup_count = 0
    
    for connection in connections:
        # Check if connection is stale
        if connection.is_stale(max_age_seconds):
            # Update status to offline
            connection.update_presence({'status': 'offline'})
            
            # Get user ID for event
            user_id = connection.get_user_id()
            
            # Create and publish presence event
            event = create_event(
                'user.presence',
                {
                    'user_id': user_id,
                    'status': 'offline',
                    'connection_id': connection.get('connectionId'),
                    'event': 'timeout'
                },
                'presence_service'
            )
            
            # Publish to event bus
            event_bus.publish('user.presence', event)
            
            cleanup_count += 1
    
    if cleanup_count > 0:
        logger.info(f"Cleaned up {cleanup_count} stale connections")
    
    return cleanup_count


class PresenceService:
    """
    Service for managing user presence information across the system.
    """
    
    def __init__(self):
        """
        Initialize the presence service.
        """
        # Get presence settings from configuration
        self._presence_settings = config.get_presence_settings()
        
        # Initialize cached presence data
        self._cached_presence = {}
        
        # Flag for cleanup task
        self._cleanup_task_running = False
        
        # Set up event subscriptions
        event_bus.subscribe('user.presence', self.handle_presence_event)
        event_bus.subscribe('user.typing', self.handle_presence_event)
        
        # Start background cleanup task if enabled
        if self._presence_settings.get('activity_tracking', True):
            self.start_cleanup_task()
        
        logger.info("PresenceService initialized")
    
    def update_presence(self, connection_id: str, presence_data: dict) -> bool:
        """
        Updates user presence information for a connection.
        
        Args:
            connection_id: The connection ID
            presence_data: Dictionary with presence information
            
        Returns:
            True if update successful, False otherwise
        """
        # Call the module function
        result = update_presence(connection_id, presence_data)
        
        # Update cache if successful
        if result and 'status' in presence_data:
            connection = Connection.find_by_connection_id(connection_id)
            if connection:
                user_id = connection.get_user_id()
                if user_id in self._cached_presence:
                    del self._cached_presence[user_id]
        
        return result
    
    def update_typing_status(self, connection_id: str, is_typing: bool, location: str) -> bool:
        """
        Updates user typing status for a specific context.
        
        Args:
            connection_id: The connection ID
            is_typing: Whether the user is typing
            location: Context where the user is typing
            
        Returns:
            True if update successful, False otherwise
        """
        # Call the module function
        return update_typing_status(connection_id, is_typing, location)
    
    def handle_disconnect(self, connection_id: str) -> bool:
        """
        Handles connection disconnection and updates presence.
        
        Args:
            connection_id: The connection ID that disconnected
            
        Returns:
            True if handled successfully, False otherwise
        """
        # Find connection to get user ID before handling disconnect
        connection = Connection.find_by_connection_id(connection_id)
        user_id = connection.get_user_id() if connection else None
        
        # Call the module function
        result = handle_disconnect(connection_id)
        
        # Update cache if successful
        if result and user_id and user_id in self._cached_presence:
            del self._cached_presence[user_id]
        
        return result
    
    def handle_heartbeat(self, connection_id: str) -> bool:
        """
        Updates connection timestamp for heartbeat/ping messages.
        
        Args:
            connection_id: The connection ID
            
        Returns:
            True if update successful, False otherwise
        """
        # Call the module function
        return handle_heartbeat(connection_id)
    
    def get_user_presence(self, user_id: str) -> dict:
        """
        Gets presence information for a specific user.
        
        Args:
            user_id: The user ID to get presence for
            
        Returns:
            User presence information
        """
        # Check if we have recent cached data
        if user_id in self._cached_presence:
            cache_time, presence_data = self._cached_presence[user_id]
            # Use cached data if less than 10 seconds old
            if time.time() - cache_time < 10:
                return presence_data
        
        # Get fresh presence data
        presence_data = get_user_presence(user_id)
        
        # Cache the result
        self._cached_presence[user_id] = (time.time(), presence_data)
        
        return presence_data
    
    def get_users_presence(self, user_ids: list) -> dict:
        """
        Gets presence information for multiple users.
        
        Args:
            user_ids: List of user IDs to get presence for
            
        Returns:
            Dictionary of user presence information
        """
        # Call the module function
        result = get_users_presence(user_ids)
        
        # Update cache with results
        current_time = time.time()
        for user_id, presence_data in result.items():
            self._cached_presence[user_id] = (current_time, presence_data)
        
        return result
    
    def get_channel_presence(self, channel: str, object_type: str, object_id: str) -> dict:
        """
        Gets presence information for all users in a channel.
        
        Args:
            channel: Channel name
            object_type: Type of object
            object_id: Object ID
            
        Returns:
            Dictionary of user presence information for the channel
        """
        # Call the module function
        return get_channel_presence(channel, object_type, object_id)
    
    def start_cleanup_task(self) -> None:
        """
        Starts background task to clean up stale presence data.
        """
        if not self._cleanup_task_running:
            self._cleanup_task_running = True
            asyncio.create_task(self.cleanup_loop())
            logger.info("Started presence cleanup task")
    
    def stop_cleanup_task(self) -> None:
        """
        Stops the background cleanup task.
        """
        self._cleanup_task_running = False
        logger.info("Stopped presence cleanup task")
    
    async def cleanup_loop(self) -> None:
        """
        Background loop that periodically cleans up stale presence data.
        """
        cleanup_interval = self._presence_settings.get('user_timeout', 300)
        
        while self._cleanup_task_running:
            try:
                # Clean up stale connections
                max_age = self._presence_settings.get('user_timeout', DEFAULT_PRESENCE_EXPIRY)
                cleanup_count = cleanup_stale_presence(max_age)
                
                if cleanup_count > 0:
                    logger.info(f"Cleanup task removed {cleanup_count} stale connections")
                
                # Wait for next cleanup interval
                await asyncio.sleep(cleanup_interval)
            except Exception as e:
                logger.error(f"Error in presence cleanup task: {str(e)}")
                # Sleep briefly before retrying
                await asyncio.sleep(60)
    
    def handle_presence_event(self, event: dict) -> None:
        """
        Event handler for presence-related events from event bus.
        
        Args:
            event: Event data
        """
        event_type = event.get('type')
        payload = event.get('payload', {})
        
        if event_type == 'user.presence':
            # Invalidate cached presence data for this user
            user_id = payload.get('user_id')
            if user_id and user_id in self._cached_presence:
                del self._cached_presence[user_id]
            
            logger.debug(f"Processed presence event for user {user_id}")
        
        elif event_type == 'user.typing':
            # Typing events don't affect cached presence data (short-lived)
            logger.debug(f"Processed typing event")
    
    def invalidate_cache(self, user_id: str) -> None:
        """
        Invalidates cached presence data for a user.
        
        Args:
            user_id: The user ID to invalidate cache for
        """
        if user_id in self._cached_presence:
            del self._cached_presence[user_id]
            logger.debug(f"Invalidated presence cache for user {user_id}")