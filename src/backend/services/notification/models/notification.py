"""
Notification model module for the Task Management System.

This module defines the MongoDB document model for notifications,
supporting various notification types, delivery status tracking,
and notification management operations.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import uuid
import bson

from ..../../common/database/mongo/models import (
    TimestampedDocument, 
    str_to_object_id, 
    object_id_to_str,
    serialize_doc
)
from ..../../common/utils/validators import validate_enum
from ..../../common/utils/datetime import now, to_iso_format

# Define the collection name for notifications
NOTIFICATION_COLLECTION = "notifications"


class NotificationType(Enum):
    """
    Enumeration of supported notification types in the system.
    
    These values represent different triggering events that generate notifications.
    """
    TASK_ASSIGNED = "task_assigned"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    COMMENT_ADDED = "comment_added"
    MENTION = "mention"
    PROJECT_INVITATION = "project_invitation"
    STATUS_CHANGE = "status_change"


class NotificationPriority(Enum):
    """
    Enumeration of notification priority levels.
    
    These values determine how urgently a notification should be delivered/displayed.
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(Enum):
    """
    Enumeration of notification delivery statuses.
    
    These values track the delivery state for different notification channels.
    """
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DISABLED = "disabled"


class Notification(TimestampedDocument):
    """
    MongoDB document model for notifications sent to users.
    
    This class handles notification storage, delivery status tracking, and provides
    methods for notification management.
    """
    
    collection_name = NOTIFICATION_COLLECTION
    schema = {
        "id": {"type": "str", "required": True},
        "recipient_id": {"type": "ObjectId", "required": True},
        "type": {"type": "str", "required": True},
        "title": {"type": "str", "required": True},
        "content": {"type": "str", "required": True},
        "priority": {"type": "str", "required": True},
        "read": {"type": "bool", "required": True},
        "action_url": {"type": "str", "required": False, "nullable": True},
        "metadata": {"type": "dict", "required": True}
    }
    use_schema_validation = True
    
    def __init__(
        self,
        id: str = None,
        recipient_id: Union[str, bson.ObjectId] = None,
        type: NotificationType = None,
        title: str = None,
        content: str = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        read: bool = False,
        action_url: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize a new notification.
        
        Args:
            id: Unique identifier for the notification (UUID string)
            recipient_id: ID of the user who will receive the notification
            type: Type of notification (from NotificationType)
            title: Short notification title
            content: Detailed notification content
            priority: Notification priority level (from NotificationPriority)
            read: Whether the notification has been read
            action_url: URL the user should be directed to when clicking the notification
            metadata: Additional data about the notification (timestamps, event details, etc.)
        """
        # Convert string IDs to ObjectId if needed
        if recipient_id and isinstance(recipient_id, str):
            recipient_id = str_to_object_id(recipient_id)
        
        # Generate UUID for new notifications if not provided
        if id is None:
            id = str(uuid.uuid4())
        
        # Initialize default metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Ensure created timestamp exists in metadata
        if "created" not in metadata:
            metadata["created"] = now()
            
        # Initialize delivery status tracking if not present
        if "delivery_status" not in metadata:
            metadata["delivery_status"] = {
                "in_app": DeliveryStatus.PENDING.value,
                "email": DeliveryStatus.PENDING.value,
                "push": DeliveryStatus.PENDING.value
            }
            
        # Initialize delivery timestamps if not present
        if "delivery_timestamps" not in metadata:
            metadata["delivery_timestamps"] = {
                "in_app": None,
                "email": None,
                "push": None
            }
        
        # Ensure type is a NotificationType enum value
        if isinstance(type, str):
            try:
                type = NotificationType(type)
            except ValueError:
                valid_types = [t.value for t in NotificationType]
                raise ValueError(f"Invalid notification type '{type}'. Valid types: {', '.join(valid_types)}")
        
        # Ensure priority is a NotificationPriority enum value
        if isinstance(priority, str):
            try:
                priority = NotificationPriority(priority)
            except ValueError:
                valid_priorities = [p.value for p in NotificationPriority]
                raise ValueError(f"Invalid priority '{priority}'. Valid priorities: {', '.join(valid_priorities)}")
        
        # Convert enum values to their string representation for storage
        type_value = type.value if type else None
        priority_value = priority.value if priority else NotificationPriority.NORMAL.value
        
        # Prepare document data
        data = {
            "id": id,
            "recipient_id": recipient_id,
            "type": type_value,
            "title": title,
            "content": content,
            "priority": priority_value,
            "read": read,
            "action_url": action_url,
            "metadata": metadata
        }
        
        # Initialize the document
        super().__init__(data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the notification to a dictionary representation.
        
        Returns:
            Dictionary representation of the notification with proper type conversions
        """
        # Get the base dictionary from parent method
        data = super().to_dict()
        
        # Convert ObjectId to string
        if "recipient_id" in data and data["recipient_id"]:
            data["recipient_id"] = object_id_to_str(data["recipient_id"])
        
        # Format datetime objects
        if "metadata" in data:
            if "created" in data["metadata"] and isinstance(data["metadata"]["created"], datetime):
                data["metadata"]["created"] = to_iso_format(data["metadata"]["created"])
                
            if "read_at" in data["metadata"] and isinstance(data["metadata"]["read_at"], datetime):
                data["metadata"]["read_at"] = to_iso_format(data["metadata"]["read_at"])
                
            # Format delivery timestamps
            if "delivery_timestamps" in data["metadata"]:
                for channel, timestamp in data["metadata"]["delivery_timestamps"].items():
                    if timestamp and isinstance(timestamp, datetime):
                        data["metadata"]["delivery_timestamps"][channel] = to_iso_format(timestamp)
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """
        Create a notification instance from dictionary data.
        
        Args:
            data: Dictionary containing notification data
            
        Returns:
            Notification instance initialized with the provided data
        """
        # Convert string ID to ObjectId if needed
        if "recipient_id" in data and isinstance(data["recipient_id"], str):
            data["recipient_id"] = str_to_object_id(data["recipient_id"])
        
        # Create a copy to avoid modifying the input
        notification_data = data.copy()
        
        # Convert string notification type to enum if needed
        if "type" in notification_data and isinstance(notification_data["type"], str):
            try:
                notification_data["type"] = NotificationType(notification_data["type"])
            except ValueError:
                # Keep as string if not a valid enum value - validation will handle errors
                pass
        
        # Convert string priority to enum if needed
        if "priority" in notification_data and isinstance(notification_data["priority"], str):
            try:
                notification_data["priority"] = NotificationPriority(notification_data["priority"])
            except ValueError:
                # Keep as string if not a valid enum value - validation will handle errors
                pass
        
        # Parse timestamps in metadata if present
        if "metadata" in notification_data:
            metadata = notification_data["metadata"]
            
            # Parse created timestamp
            if "created" in metadata and isinstance(metadata["created"], str):
                try:
                    metadata["created"] = datetime.fromisoformat(metadata["created"].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Parse read_at timestamp
            if "read_at" in metadata and isinstance(metadata["read_at"], str):
                try:
                    metadata["read_at"] = datetime.fromisoformat(metadata["read_at"].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
                    
            # Parse delivery timestamps
            if "delivery_timestamps" in metadata:
                for channel, timestamp in metadata["delivery_timestamps"].items():
                    if timestamp and isinstance(timestamp, str):
                        try:
                            metadata["delivery_timestamps"][channel] = datetime.fromisoformat(
                                timestamp.replace('Z', '+00:00')
                            )
                        except (ValueError, AttributeError):
                            pass
        
        # Create new notification instance
        return cls(**notification_data)
    
    def mark_as_read(self) -> bool:
        """
        Mark the notification as read.
        
        Returns:
            True if successful, False otherwise
        """
        # Update read status
        self._data["read"] = True
        
        # Record read timestamp in metadata
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        
        self._data["metadata"]["read_at"] = now()
        
        # Save changes to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error (would use a proper logger in production)
            print(f"Error marking notification as read: {str(e)}")
            return False
    
    def update_delivery_status(self, channel: str, status: DeliveryStatus) -> bool:
        """
        Update delivery status for a specific channel.
        
        Args:
            channel: Channel to update status for (in_app, email, push)
            status: New delivery status
            
        Returns:
            True if successful, False otherwise
        """
        # Validate channel
        valid_channels = ["in_app", "email", "push"]
        if channel not in valid_channels:
            raise ValueError(f"Invalid channel '{channel}'. Valid channels: {', '.join(valid_channels)}")
        
        # Ensure metadata structure exists
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        if "delivery_status" not in self._data["metadata"]:
            self._data["metadata"]["delivery_status"] = {}
        if "delivery_timestamps" not in self._data["metadata"]:
            self._data["metadata"]["delivery_timestamps"] = {}
        
        # Convert enum to string value if needed
        status_value = status.value if isinstance(status, DeliveryStatus) else status
        
        # Update delivery status
        self._data["metadata"]["delivery_status"][channel] = status_value
        
        # Update timestamp if delivered or failed
        if status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED]:
            self._data["metadata"]["delivery_timestamps"][channel] = now()
        
        # Save changes to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error (would use a proper logger in production)
            print(f"Error updating delivery status: {str(e)}")
            return False
    
    def is_delivered(self, channel: Optional[str] = None) -> bool:
        """
        Check if notification has been delivered.
        
        Args:
            channel: Optional channel to check. If None, checks if any channel is delivered.
            
        Returns:
            True if delivered, False otherwise
        """
        # Get delivery status from metadata
        delivery_status = self._data.get("metadata", {}).get("delivery_status", {})
        
        if channel:
            # Check specific channel
            return delivery_status.get(channel) == DeliveryStatus.DELIVERED.value
        else:
            # Check if any channel is delivered
            return any(status == DeliveryStatus.DELIVERED.value for status in delivery_status.values())
    
    @classmethod
    def find_by_recipient(
        cls,
        recipient_id: Union[str, bson.ObjectId],
        unread_only: bool = False,
        limit: int = 50,
        skip: int = 0
    ) -> List['Notification']:
        """
        Find notifications for a specific recipient with pagination.
        
        Args:
            recipient_id: ID of the recipient user
            unread_only: If True, return only unread notifications
            limit: Maximum number of notifications to return
            skip: Number of notifications to skip (for pagination)
            
        Returns:
            List of Notification objects
        """
        # Convert string ID to ObjectId if needed
        if isinstance(recipient_id, str):
            recipient_id = str_to_object_id(recipient_id)
        
        # Prepare query filter
        query = {"recipient_id": recipient_id}
        
        # Add unread filter if requested
        if unread_only:
            query["read"] = False
        
        # Get collection and execute query
        instance = cls()
        collection = instance.collection()
        
        # Sort by creation time with newest first
        sort_order = [("metadata.created", -1)]
        
        # Execute query with pagination
        results = collection.find(query).sort(sort_order).skip(skip).limit(limit)
        
        # Convert results to Notification objects
        notifications = [cls(data=doc, is_new=False) for doc in results]
        
        return notifications
    
    @classmethod
    def count_by_recipient(cls, recipient_id: Union[str, bson.ObjectId], unread_only: bool = False) -> int:
        """
        Count notifications for a specific recipient.
        
        Args:
            recipient_id: ID of the recipient user
            unread_only: If True, count only unread notifications
            
        Returns:
            Count of matching notifications
        """
        # Convert string ID to ObjectId if needed
        if isinstance(recipient_id, str):
            recipient_id = str_to_object_id(recipient_id)
        
        # Prepare query filter
        query = {"recipient_id": recipient_id}
        
        # Add unread filter if requested
        if unread_only:
            query["read"] = False
        
        # Get collection and execute count
        instance = cls()
        collection = instance.collection()
        
        return collection.count_documents(query)
    
    @classmethod
    def mark_all_as_read(cls, recipient_id: Union[str, bson.ObjectId]) -> int:
        """
        Mark all notifications for a recipient as read.
        
        Args:
            recipient_id: ID of the recipient user
            
        Returns:
            Number of notifications updated
        """
        # Convert string ID to ObjectId if needed
        if isinstance(recipient_id, str):
            recipient_id = str_to_object_id(recipient_id)
        
        # Prepare query filter for unread notifications
        query = {"recipient_id": recipient_id, "read": False}
        
        # Prepare update with read=True and readAt timestamp
        current_time = now()
        update = {
            "$set": {
                "read": True,
                "metadata.read_at": current_time
            }
        }
        
        # Get collection and execute update
        instance = cls()
        collection = instance.collection()
        
        result = collection.update_many(query, update)
        return result.modified_count
    
    @classmethod
    def find_pending_delivery(cls, channel: str, limit: int = 100) -> List['Notification']:
        """
        Find notifications pending delivery for a specific channel.
        
        Args:
            channel: Channel to find pending notifications for (in_app, email, push)
            limit: Maximum number of notifications to return
            
        Returns:
            List of Notification objects pending delivery
        """
        # Validate channel
        valid_channels = ["in_app", "email", "push"]
        if channel not in valid_channels:
            raise ValueError(f"Invalid channel '{channel}'. Valid channels: {', '.join(valid_channels)}")
        
        # Prepare query filter for pending notifications
        query = {f"metadata.delivery_status.{channel}": DeliveryStatus.PENDING.value}
        
        # Get collection and execute query
        instance = cls()
        collection = instance.collection()
        
        # Sort by priority (higher priority first) and then by creation time
        sort_order = [
            # Map priority values to sort order
            ("priority", -1),
            ("metadata.created", 1)
        ]
        
        # Execute query with limit
        results = collection.find(query).sort(sort_order).limit(limit)
        
        # Convert results to Notification objects
        notifications = [cls(data=doc, is_new=False) for doc in results]
        
        return notifications


def create_notification(
    recipient_id: str,
    notification_type: Union[str, NotificationType],
    title: str,
    content: str,
    priority: Union[str, NotificationPriority] = NotificationPriority.NORMAL,
    action_url: str = None,
    metadata: Dict[str, Any] = None
) -> Notification:
    """
    Factory function to create a new notification with default settings.
    
    Args:
        recipient_id: ID of the user who will receive the notification
        notification_type: Type of notification
        title: Short notification title
        content: Detailed notification content
        priority: Notification priority level
        action_url: URL the user should be directed to when clicking the notification
        metadata: Additional data about the notification
        
    Returns:
        New Notification instance
    """
    # Convert string type to enum if needed
    if isinstance(notification_type, str):
        try:
            notification_type = NotificationType(notification_type)
        except ValueError:
            valid_types = [t.value for t in NotificationType]
            raise ValueError(f"Invalid notification type '{notification_type}'. Valid types: {', '.join(valid_types)}")
    
    # Convert string priority to enum if needed
    if isinstance(priority, str):
        try:
            priority = NotificationPriority(priority)
        except ValueError:
            valid_priorities = [p.value for p in NotificationPriority]
            raise ValueError(f"Invalid priority '{priority}'. Valid priorities: {', '.join(valid_priorities)}")
    
    # Initialize default metadata if not provided
    if metadata is None:
        metadata = {}
    
    # Additional metadata based on notification type
    if notification_type == NotificationType.TASK_ASSIGNED and "task_id" not in metadata:
        raise ValueError("task_id is required in metadata for TASK_ASSIGNED notifications")
        
    if notification_type == NotificationType.TASK_DUE_SOON and "task_id" not in metadata:
        raise ValueError("task_id is required in metadata for TASK_DUE_SOON notifications")
    
    # Create and return the notification
    notification = Notification(
        recipient_id=recipient_id,
        type=notification_type,
        title=title,
        content=content,
        priority=priority,
        action_url=action_url,
        metadata=metadata,
        read=False
    )
    
    return notification