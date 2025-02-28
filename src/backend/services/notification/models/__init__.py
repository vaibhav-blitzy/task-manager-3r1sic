"""
Notification models module for the Task Management System.

This module exports all notification-related models, enumerations, and utility functions
for creating and managing notifications in the system.
"""

# Import notification model and related types
from .notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    DeliveryStatus as NotificationStatus,
    create_notification
)

# Import notification preferences model and related types
from .preference import (
    NotificationPreference,
    NotificationChannel,
    DigestFrequency,
    get_user_preferences
)

# Export all components
__all__ = [
    # Notification models
    'Notification',
    'NotificationType',
    'NotificationPriority',
    'NotificationStatus',
    'create_notification',
    
    # Notification preference models
    'NotificationPreference',
    'NotificationChannel',
    'DigestFrequency',
    'get_user_preferences'
]