"""
Initialization file for the notification service package, exporting key components for the notification system
"""

from .models.notification import Notification as NotificationModel  # Import the Notification model
from .models.preference import NotificationPreference  # Import the NotificationPreference model
from .services.notification_service import NotificationService  # Import the NotificationService class
from .services.email_service import EmailService  # Import the EmailService class
from .services.push_service import PushService  # Import the PushService class

__version__ = "1.0.0"  # Define the package version

# Expose the key components for external use
__all__ = [
    "__version__",
    "NotificationModel",  # Expose the Notification model
    "NotificationPreference",  # Expose the NotificationPreference model
    "NotificationService",  # Expose the NotificationService class
    "EmailService",  # Expose the EmailService class
    "PushService"  # Expose the PushService class
]