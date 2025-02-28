"""
Initialization file for the notification service module.
Exports the key service classes and functions needed by the notification API and other services to interact with the notification system.
"""

# Internal imports
from .notification_service import NotificationService  # src/backend/services/notification/services/notification_service.py
from .email_service import EmailService  # src/backend/services/notification/services/email_service.py
from .push_service import PushService  # src/backend/services/notification/services/push_service.py
from .notification_service import create_user_notification  # src/backend/services/notification/services/notification_service.py
from .notification_service import get_user_notifications  # src/backend/services/notification/services/notification_service.py
from .notification_service import process_event  # src/backend/services/notification/services/notification_service.py

__all__ = [
    "NotificationService",
    "EmailService",
    "PushService",
    "create_user_notification",
    "get_user_notifications",
    "process_event"
]