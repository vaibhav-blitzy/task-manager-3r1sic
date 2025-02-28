"""
MongoDB model for user notification preferences.

This module defines the MongoDB document model for user notification preferences,
providing structured storage and retrieval of user-configurable notification settings
at multiple levels (global, notification type, project-specific, and temporary settings
like quiet hours).
"""

from enum import Enum
from datetime import datetime, time
from typing import Dict, List, Optional, Union, Any
import bson

from ..../../common/database/mongo/models import (
    TimestampedDocument, 
    str_to_object_id, 
    object_id_to_str
)
from .notification import NotificationType
from ..../../common/utils/validators import validate_enum
from ..../../common/utils/datetime import now

# Define the collection name for notification preferences
PREFERENCE_COLLECTION = "notification_preferences"


class NotificationChannel(Enum):
    """Enumeration of supported notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class DigestFrequency(Enum):
    """Enumeration of supported notification digest frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class NotificationPreference(TimestampedDocument):
    """MongoDB document model representing user notification preferences."""
    
    collection_name = PREFERENCE_COLLECTION
    
    schema = {
        "user_id": {"type": "ObjectId", "required": True},
        "global_settings": {"type": "dict", "required": True},
        "type_settings": {"type": "dict", "required": True},
        "project_settings": {"type": "dict", "required": True},
        "quiet_hours": {"type": "dict", "required": True}
    }
    
    use_schema_validation = True
    
    def __init__(
        self,
        user_id: Union[str, bson.ObjectId],
        global_settings: Dict[str, Any] = None,
        type_settings: Dict[str, Dict[str, bool]] = None,
        project_settings: Dict[str, Dict[str, bool]] = None,
        quiet_hours: Dict[str, Any] = None,
    ):
        """
        Initialize a new notification preference instance.
        
        Args:
            user_id: The user ID these preferences belong to
            global_settings: Default settings for all notifications
            type_settings: Settings overrides for specific notification types
            project_settings: Settings overrides for specific projects
            quiet_hours: Configuration for quiet hours
        """
        # Convert user_id to ObjectId if string
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Default global settings if not provided
        if global_settings is None:
            global_settings = {
                "in_app": True,
                "email": True,
                "push": False,
                "digest": {
                    "enabled": True,
                    "frequency": DigestFrequency.DAILY.value
                }
            }
        
        # Default empty dictionaries if not provided
        if type_settings is None:
            type_settings = {}
            
        if project_settings is None:
            project_settings = {}
            
        # Default quiet hours settings if not provided
        if quiet_hours is None:
            quiet_hours = {
                "enabled": False,
                "start": "22:00",
                "end": "08:00",
                "timezone": "UTC",
                "excludeUrgent": True
            }
        
        # Prepare document data
        data = {
            "user_id": user_id,
            "global_settings": global_settings,
            "type_settings": type_settings,
            "project_settings": project_settings,
            "quiet_hours": quiet_hours
        }
        
        # Initialize the document
        super().__init__(data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert preference to dictionary representation.
        
        Returns:
            Dictionary representation of preferences with proper type conversions
        """
        # Get the base dictionary from parent method
        data = super().to_dict()
        
        # Convert ObjectId to string
        if "user_id" in data and data["user_id"]:
            data["user_id"] = object_id_to_str(data["user_id"])
        
        # Format time values for quiet hours if needed
        if "quiet_hours" in data:
            quiet_hours = data["quiet_hours"]
            # No conversion needed for string time format
            
        # Convert any enum values to strings
        if "global_settings" in data and "digest" in data["global_settings"]:
            if "frequency" in data["global_settings"]["digest"]:
                frequency = data["global_settings"]["digest"]["frequency"]
                if isinstance(frequency, DigestFrequency):
                    data["global_settings"]["digest"]["frequency"] = frequency.value
                    
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationPreference':
        """
        Create preference instance from dictionary data.
        
        Args:
            data: Dictionary containing preference data
            
        Returns:
            NotificationPreference instance initialized with the provided data
        """
        # Extract fields from data
        user_id = data.get("user_id")
        global_settings = data.get("global_settings")
        type_settings = data.get("type_settings")
        project_settings = data.get("project_settings")
        quiet_hours = data.get("quiet_hours")
        
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Create and return new instance
        return cls(
            user_id=user_id,
            global_settings=global_settings,
            type_settings=type_settings,
            project_settings=project_settings,
            quiet_hours=quiet_hours
        )
    
    @classmethod
    def find_by_user_id(cls, user_id: Union[str, bson.ObjectId]) -> Optional['NotificationPreference']:
        """
        Find notification preferences for a specific user.
        
        Args:
            user_id: ID of the user to find preferences for
            
        Returns:
            NotificationPreference object if found, None otherwise
        """
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Create query for user_id
        query = {"user_id": user_id}
        
        # Use find_one class method to get preferences
        return cls.find_one(query)
    
    def update_global_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update global notification settings.
        
        Args:
            settings: New global settings with in_app, email, push, and digest configuration
            
        Returns:
            True if successful, False otherwise
        """
        # Validate settings have required keys
        required_keys = ["in_app", "email", "push"]
        
        for key in required_keys:
            if key not in settings:
                raise ValueError(f"Missing required key '{key}' in global settings")
        
        # Validate digest settings if present
        if "digest" in settings:
            digest = settings["digest"]
            if not isinstance(digest, dict):
                raise ValueError("Digest settings must be a dictionary")
                
            if "enabled" not in digest:
                raise ValueError("Digest settings must include 'enabled' field")
                
            if "frequency" in digest:
                try:
                    valid_frequencies = [f.value for f in DigestFrequency]
                    validate_enum(digest["frequency"], valid_frequencies, "digest frequency")
                except ValueError as e:
                    raise ValueError(f"Invalid digest frequency: {str(e)}")
        
        # Update global settings
        self._data["global_settings"] = settings
        
        # Save to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error
            print(f"Error updating global settings: {str(e)}")
            return False
    
    def update_type_settings(self, notification_type: Union[str, NotificationType], settings: Dict[str, bool]) -> bool:
        """
        Update settings for a specific notification type.
        
        Args:
            notification_type: The notification type to update settings for
            settings: New settings for the notification type with in_app, email, push configuration
            
        Returns:
            True if successful, False otherwise
        """
        # Convert string type to enum if needed
        if isinstance(notification_type, str):
            try:
                notification_type = NotificationType(notification_type)
            except ValueError:
                valid_types = [t.value for t in NotificationType]
                raise ValueError(f"Invalid notification type '{notification_type}'. Valid types: {', '.join(valid_types)}")
        
        # Get type value
        type_value = notification_type.value
        
        # Validate settings have required keys
        required_keys = ["in_app", "email", "push"]
        
        for key in required_keys:
            if key not in settings:
                raise ValueError(f"Missing required key '{key}' in type settings")
        
        # Ensure type_settings dictionary exists
        if "type_settings" not in self._data:
            self._data["type_settings"] = {}
        
        # Update type settings
        self._data["type_settings"][type_value] = settings
        
        # Save to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error
            print(f"Error updating type settings: {str(e)}")
            return False
    
    def update_project_settings(self, project_id: str, settings: Dict[str, bool]) -> bool:
        """
        Update notification settings for a specific project.
        
        Args:
            project_id: The project ID to update settings for
            settings: New settings for the project with in_app, email, push configuration
            
        Returns:
            True if successful, False otherwise
        """
        # Validate project_id format
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID must be a non-empty string")
        
        # Validate settings have required keys
        required_keys = ["in_app", "email", "push"]
        
        for key in required_keys:
            if key not in settings:
                raise ValueError(f"Missing required key '{key}' in project settings")
        
        # Ensure project_settings dictionary exists
        if "project_settings" not in self._data:
            self._data["project_settings"] = {}
        
        # Update project settings
        self._data["project_settings"][project_id] = settings
        
        # Save to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error
            print(f"Error updating project settings: {str(e)}")
            return False
    
    def update_quiet_hours(self, settings: Dict[str, Any]) -> bool:
        """
        Update quiet hours settings.
        
        Args:
            settings: New quiet hours settings with enabled flag, start/end times,
                     timezone, and excludeUrgent flag
            
        Returns:
            True if successful, False otherwise
        """
        # Validate settings have required keys
        required_keys = ["enabled", "start", "end", "timezone", "excludeUrgent"]
        
        for key in required_keys:
            if key not in settings:
                raise ValueError(f"Missing required key '{key}' in quiet hours settings")
        
        # Validate time format
        try:
            start_time = datetime.strptime(settings["start"], "%H:%M").time()
            end_time = datetime.strptime(settings["end"], "%H:%M").time()
        except ValueError:
            raise ValueError("Time values must be in 24-hour format (HH:MM)")
        
        # Update quiet hours settings
        self._data["quiet_hours"] = settings
        
        # Save to database
        try:
            self.save()
            return True
        except Exception as e:
            # Log the error
            print(f"Error updating quiet hours settings: {str(e)}")
            return False
    
    def should_send_notification(self, notification_type: Union[str, NotificationType],
                                channel: NotificationChannel, priority: str = "normal",
                                project_id: str = None) -> bool:
        """
        Determine if notification should be sent based on preferences.
        
        Args:
            notification_type: Type of notification
            channel: Notification channel (in_app, email, push)
            priority: Priority of notification
            project_id: Project ID if notification is related to a project
            
        Returns:
            True if notification should be sent, False otherwise
        """
        # Get effective preference based on type and project
        effective_preference = self.get_effective_preference(notification_type, project_id)
        
        # Check if channel is enabled in effective preference
        channel_enabled = effective_preference.get(channel.value, False)
        
        # If channel is not enabled, don't send
        if not channel_enabled:
            return False
        
        # Check quiet hours
        if self.is_in_quiet_hours():
            # Don't send during quiet hours, unless it's urgent and excludeUrgent is True
            quiet_hours = self._data.get("quiet_hours", {})
            exclude_urgent = quiet_hours.get("excludeUrgent", True)
            
            if priority == "urgent" and exclude_urgent:
                # Allow urgent notifications during quiet hours if excludeUrgent is True
                return True
            else:
                # Don't send during quiet hours
                return False
        
        # Default case: send the notification
        return True
    
    def get_effective_preference(self, notification_type: Union[str, NotificationType],
                                project_id: str = None) -> Dict[str, bool]:
        """
        Get effective notification preferences considering all override levels.
        
        Args:
            notification_type: Type of notification
            project_id: Project ID if notification is related to a project
            
        Returns:
            Dictionary with effective preferences for the given context
        """
        # Start with global settings
        effective_preference = self._data.get("global_settings", {}).copy()
        
        # Remove digest setting since it's not relevant for channel-specific checks
        if "digest" in effective_preference:
            del effective_preference["digest"]
        
        # Convert string type to enum if needed
        if isinstance(notification_type, str):
            try:
                notification_type = NotificationType(notification_type)
            except ValueError:
                # If not a valid enum, treat as a string key
                pass
        
        # Get notification type value
        type_value = notification_type.value if hasattr(notification_type, "value") else str(notification_type)
        
        # Override with type-specific settings if available
        type_settings = self._data.get("type_settings", {}).get(type_value)
        if type_settings:
            effective_preference.update(type_settings)
        
        # Override with project-specific settings if available
        if project_id:
            project_settings = self._data.get("project_settings", {}).get(project_id)
            if project_settings:
                effective_preference.update(project_settings)
        
        return effective_preference
    
    def is_channel_enabled(self, channel: NotificationChannel,
                          notification_type: Union[str, NotificationType] = None,
                          project_id: str = None) -> bool:
        """
        Check if a specific notification channel is enabled.
        
        Args:
            channel: The notification channel to check
            notification_type: Type of notification (optional)
            project_id: Project ID (optional)
            
        Returns:
            True if channel is enabled, False otherwise
        """
        if notification_type:
            # Get effective preference based on type and project
            effective_preference = self.get_effective_preference(notification_type, project_id)
            return effective_preference.get(channel.value, False)
        else:
            # Just check global settings
            return self._data.get("global_settings", {}).get(channel.value, False)
    
    def is_in_quiet_hours(self) -> bool:
        """
        Check if current time is within configured quiet hours.
        
        Returns:
            True if in quiet hours, False otherwise
        """
        quiet_hours = self._data.get("quiet_hours", {})
        
        # If quiet hours not enabled, always return False
        if not quiet_hours.get("enabled", False):
            return False
        
        # Get current time in user's timezone
        current_time = datetime.now().time()  # TODO: Convert to user's timezone
        
        # Get quiet hours start and end times
        try:
            start_time = datetime.strptime(quiet_hours.get("start", "22:00"), "%H:%M").time()
            end_time = datetime.strptime(quiet_hours.get("end", "08:00"), "%H:%M").time()
        except ValueError:
            # Default to no quiet hours if time format is invalid
            return False
        
        # Check if current time is within quiet hours
        if start_time < end_time:
            # Simple case: start time is before end time
            return start_time <= current_time <= end_time
        else:
            # Complex case: quiet hours span midnight
            return current_time >= start_time or current_time <= end_time


def get_default_preferences() -> Dict[str, Any]:
    """
    Creates default notification preferences.
    
    Returns:
        Dictionary with default preference settings
    """
    return {
        "global_settings": {
            "in_app": True,
            "email": True,
            "push": False,
            "digest": {
                "enabled": True,
                "frequency": DigestFrequency.DAILY.value
            }
        },
        "type_settings": {},
        "project_settings": {},
        "quiet_hours": {
            "enabled": False,
            "start": "22:00",
            "end": "08:00",
            "timezone": "UTC",
            "excludeUrgent": True
        }
    }


def get_user_preferences(user_id: str) -> NotificationPreference:
    """
    Retrieves or creates notification preferences for a user.
    
    Args:
        user_id: The user ID to get preferences for
        
    Returns:
        NotificationPreference instance for the user
    """
    # Convert string ID to ObjectId if needed
    if isinstance(user_id, str):
        user_id = str_to_object_id(user_id)
    
    # Try to find existing preferences
    preferences = NotificationPreference.find_by_user_id(user_id)
    
    # If found, return them
    if preferences:
        return preferences
    
    # Otherwise, create default preferences
    default_prefs = get_default_preferences()
    new_preferences = NotificationPreference(
        user_id=user_id,
        global_settings=default_prefs["global_settings"],
        type_settings=default_prefs["type_settings"],
        project_settings=default_prefs["project_settings"],
        quiet_hours=default_prefs["quiet_hours"]
    )
    
    # Save to database
    new_preferences.save()
    
    return new_preferences