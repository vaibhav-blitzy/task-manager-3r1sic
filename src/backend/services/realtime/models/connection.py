"""
MongoDB document model for WebSocket connections in the real-time system.

This module defines the Connection document model for tracking real-time connections,
user presence, and channel subscriptions for the collaborative features of the
Task Management System.
"""

from typing import Dict, List, Optional, Any, Union
import uuid
from datetime import datetime

import bson
import pymongo

from ....common.database.mongo.models import TimestampedDocument
from ....common.logging.logger import get_logger
from ....common.utils.datetime import now

# Configure module logger
logger = get_logger(__name__)

# Valid presence statuses
PRESENCE_STATUSES = ['online', 'away', 'busy', 'offline']


def create_subscription_key(channel: str, object_type: str, object_id: str) -> str:
    """
    Creates a unique subscription key from channel, object type, and ID.
    
    Args:
        channel: Channel name (e.g., 'task', 'project')
        object_type: Type of object being subscribed to
        object_id: Unique identifier of the object
        
    Returns:
        Subscription key string in format '{channel}:{object_type}:{object_id}'
    """
    if not channel or not object_type or not object_id:
        raise ValueError("Channel, object_type, and object_id are required")
    
    return f"{channel}:{object_type}:{object_id}"


class Connection(TimestampedDocument):
    """
    MongoDB document model representing a WebSocket connection.
    
    Tracks connection metadata, user presence information, and subscribed channels
    for real-time collaboration features.
    """
    
    collection_name = "connections"
    
    schema = {
        "connectionId": {"type": "str", "required": True},
        "userId": {"type": "str", "required": True},
        "clientInfo": {
            "type": "dict",
            "required": True,
            "schema": {
                "device": {"type": "str", "required": False},
                "browser": {"type": "str", "required": False},
                "ip": {"type": "str", "required": False, "nullable": True},
                "location": {"type": "str", "required": False, "nullable": True}
            }
        },
        "subscriptions": {
            "type": "list",
            "required": False,
            "schema": {
                "type": "dict",
                "schema": {
                    "key": {"type": "str", "required": True},
                    "channel": {"type": "str", "required": True},
                    "objectType": {"type": "str", "required": True},
                    "objectId": {"type": "str", "required": True},
                    "joinedAt": {"type": "datetime", "required": True}
                }
            }
        },
        "presence": {
            "type": "dict",
            "required": True,
            "schema": {
                "status": {"type": "str", "required": True},
                "lastActivity": {"type": "datetime", "required": True},
                "currentView": {"type": "str", "required": False, "nullable": True},
                "typing": {
                    "type": "dict",
                    "required": False,
                    "schema": {
                        "isTyping": {"type": "bool", "required": False},
                        "location": {"type": "str", "required": False, "nullable": True}
                    }
                }
            }
        },
        "metadata": {
            "type": "dict",
            "required": True,
            "schema": {
                "connected": {"type": "datetime", "required": True},
                "lastPing": {"type": "datetime", "required": True}
            }
        }
    }
    
    use_schema_validation = True
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new Connection document.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document
        """
        # Initialize with defaults if not provided
        if data is None:
            data = {}
        
        if is_new and "connectionId" not in data:
            # Set default values for new connection
            data.setdefault("connectionId", self.generate_connection_id())
            data.setdefault("subscriptions", [])
            data.setdefault("presence", {
                "status": "online",
                "lastActivity": now(),
                "currentView": None,
                "typing": {
                    "isTyping": False,
                    "location": None
                }
            })
            data.setdefault("metadata", {
                "connected": now(),
                "lastPing": now()
            })
        
        # Call parent constructor
        super().__init__(data, is_new)
    
    @staticmethod
    def generate_connection_id() -> str:
        """
        Generates a unique connection identifier.
        
        Returns:
            Unique connection ID as string
        """
        return str(uuid.uuid4())
    
    @classmethod
    def find_by_connection_id(cls, connection_id: str) -> Optional['Connection']:
        """
        Finds a connection by its unique connection ID.
        
        Args:
            connection_id: The unique connection identifier
            
        Returns:
            Connection document if found, None otherwise
        """
        if not connection_id:
            logger.warning("find_by_connection_id called with empty connection_id")
            return None
        
        return cls.find_one({"connectionId": connection_id})
    
    @classmethod
    def find_by_user_id(cls, user_id: str) -> List['Connection']:
        """
        Finds all connections for a specific user.
        
        Args:
            user_id: The user ID to find connections for
            
        Returns:
            List of Connection instances for the user
        """
        if not user_id:
            logger.warning("find_by_user_id called with empty user_id")
            return []
        
        return cls.find({"userId": user_id})
    
    @classmethod
    def find_by_channel(cls, channel: str, object_type: str, object_id: str) -> List['Connection']:
        """
        Finds all connections subscribed to a specific channel.
        
        Args:
            channel: Channel name (e.g., 'task', 'project')
            object_type: Type of object subscribed to
            object_id: ID of object subscribed to
            
        Returns:
            List of Connection instances subscribed to the channel
        """
        try:
            # Create subscription key to search for
            subscription_key = create_subscription_key(channel, object_type, object_id)
            
            # Find connections with matching subscription
            return cls.find({
                "subscriptions.key": subscription_key
            })
        except ValueError as e:
            logger.error(f"Error in find_by_channel: {str(e)}")
            return []
    
    def add_subscription(self, channel: str, object_type: str, object_id: str) -> bool:
        """
        Adds a channel subscription to the connection.
        
        Args:
            channel: Channel name (e.g., 'task', 'project')
            object_type: Type of object being subscribed to
            object_id: Unique identifier of the object
            
        Returns:
            True if subscription was added, False if already exists
        """
        try:
            # Create subscription key
            subscription_key = create_subscription_key(channel, object_type, object_id)
            
            # Check if subscription already exists
            if self.has_subscription(channel, object_type, object_id):
                return False
            
            # Get existing subscriptions
            subscriptions = self.get("subscriptions", [])
            
            # Add new subscription
            subscriptions.append({
                "key": subscription_key,
                "channel": channel,
                "objectType": object_type,
                "objectId": object_id,
                "joinedAt": now()
            })
            
            # Update document
            self.set("subscriptions", subscriptions)
            self.save()
            
            logger.debug(f"Added subscription {subscription_key} for connection {self.get('connectionId')}")
            return True
        except Exception as e:
            logger.error(f"Error adding subscription: {str(e)}")
            return False
    
    def remove_subscription(self, channel: str, object_type: str, object_id: str) -> bool:
        """
        Removes a channel subscription from the connection.
        
        Args:
            channel: Channel name (e.g., 'task', 'project')
            object_type: Type of object subscribed to
            object_id: ID of object subscribed to
            
        Returns:
            True if subscription was removed, False if not found
        """
        try:
            # Create subscription key
            subscription_key = create_subscription_key(channel, object_type, object_id)
            
            # Get existing subscriptions
            subscriptions = self.get("subscriptions", [])
            
            # Find and remove subscription
            initial_count = len(subscriptions)
            subscriptions = [s for s in subscriptions if s.get("key") != subscription_key]
            
            # If no change, subscription wasn't found
            if len(subscriptions) == initial_count:
                return False
            
            # Update document
            self.set("subscriptions", subscriptions)
            self.save()
            
            logger.debug(f"Removed subscription {subscription_key} from connection {self.get('connectionId')}")
            return True
        except Exception as e:
            logger.error(f"Error removing subscription: {str(e)}")
            return False
    
    def has_subscription(self, channel: str, object_type: str, object_id: str) -> bool:
        """
        Checks if connection is subscribed to a specific channel.
        
        Args:
            channel: Channel name (e.g., 'task', 'project')
            object_type: Type of object subscribed to
            object_id: ID of object subscribed to
            
        Returns:
            True if subscribed, False otherwise
        """
        try:
            # Create subscription key
            subscription_key = create_subscription_key(channel, object_type, object_id)
            
            # Get subscriptions
            subscriptions = self.get("subscriptions", [])
            
            # Check if key exists in subscriptions
            return any(s.get("key") == subscription_key for s in subscriptions)
        except Exception as e:
            logger.error(f"Error checking subscription: {str(e)}")
            return False
    
    def update_presence(self, presence_data: Dict) -> bool:
        """
        Updates the presence status and information for the connection.
        
        Args:
            presence_data: Dictionary with presence information
                Must contain 'status' which is one of PRESENCE_STATUSES
                
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate status
            status = presence_data.get("status")
            if status and status not in PRESENCE_STATUSES:
                logger.warning(f"Invalid presence status: {status}")
                return False
            
            # Get current presence
            current_presence = self.get("presence", {})
            
            # Update presence with new data
            current_presence.update(presence_data)
            
            # Set last activity to now
            current_presence["lastActivity"] = now()
            
            # Update document
            self.set("presence", current_presence)
            self.save()
            
            logger.debug(f"Updated presence for connection {self.get('connectionId')}")
            return True
        except Exception as e:
            logger.error(f"Error updating presence: {str(e)}")
            return False
    
    def update_typing_status(self, is_typing: bool, location: str) -> bool:
        """
        Updates the typing status for a specific resource.
        
        Args:
            is_typing: Whether the user is currently typing
            location: Identifier of where the user is typing (e.g., 'task:123:comment')
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Validate parameters
            if location is None:
                logger.warning("update_typing_status called with empty location")
                return False
            
            # Get current presence
            presence = self.get("presence", {})
            
            # Get or initialize typing info
            typing = presence.get("typing", {})
            
            # Update typing status
            typing["isTyping"] = bool(is_typing)
            typing["location"] = location
            
            # Update presence
            presence["typing"] = typing
            presence["lastActivity"] = now()
            
            # Update document
            self.set("presence", presence)
            self.save()
            
            logger.debug(f"Updated typing status for connection {self.get('connectionId')}")
            return True
        except Exception as e:
            logger.error(f"Error updating typing status: {str(e)}")
            return False
    
    def update_ping(self) -> bool:
        """
        Updates the last ping timestamp for the connection.
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Get metadata
            metadata = self.get("metadata", {})
            
            # Update last ping
            metadata["lastPing"] = now()
            
            # Update document
            self.set("metadata", metadata)
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error updating ping: {str(e)}")
            return False
    
    def get_user_id(self) -> str:
        """
        Gets the user ID associated with the connection.
        
        Returns:
            User ID string
        """
        return self.get("userId")
    
    def get_subscriptions(self) -> List[Dict]:
        """
        Gets all subscriptions for the connection.
        
        Returns:
            List of subscription dictionaries
        """
        return self.get("subscriptions", [])
    
    def is_stale(self, max_age_seconds: int) -> bool:
        """
        Checks if the connection is stale based on last ping time.
        
        Args:
            max_age_seconds: Maximum age in seconds before considering stale
            
        Returns:
            True if connection is stale, False otherwise
        """
        try:
            # Get last ping timestamp
            metadata = self.get("metadata", {})
            last_ping = metadata.get("lastPing")
            
            if not last_ping:
                return True
            
            # Calculate age in seconds
            current_time = now()
            age_seconds = (current_time - last_ping).total_seconds()
            
            # Return True if older than max_age_seconds
            return age_seconds > max_age_seconds
        except Exception as e:
            logger.error(f"Error checking if connection is stale: {str(e)}")
            return True  # Consider connection stale if error occurs