"""
Pytest fixtures for the notification service tests. Provides mocks and test data
for notification models, services, and dependencies to enable isolated and
repeatable testing of notification functionality.
"""

import datetime
import uuid
import pytest
from unittest.mock import MagicMock

# Third-party imports
import mongomock  # v4.1.2

# Internal imports
from src.backend.services.notification.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    DeliveryStatus,
    create_notification
)
from src.backend.services.notification.models.preference import (
    NotificationPreference,
    NotificationChannel,
    get_default_preferences
)
from src.backend.services.notification.services.notification_service import NotificationService
from src.backend.services.notification.services.email_service import EmailService
from src.backend.services.notification.services.push_service import PushService
from src.backend.common.testing.fixtures import mongo_db, test_user
from src.backend.common.testing.mocks import mock_event_bus


@pytest.fixture
def email_service():
    """Fixture that creates a mock EmailService for testing"""
    # Create MagicMock for EmailService
    mock_email_service = MagicMock(spec=EmailService)
    
    # Configure send_email method to return True (success)
    mock_email_service.send_email.return_value = True
    
    # Configure specific email methods (send_task_assigned_notification, etc.) to return True
    mock_email_service.send_task_assigned_notification.return_value = True
    mock_email_service.send_task_due_soon_notification.return_value = True
    mock_email_service.send_task_overdue_notification.return_value = True
    mock_email_service.send_comment_notification.return_value = True
    mock_email_service.send_project_invitation.return_value = True
    mock_email_service.send_status_change_notification.return_value = True
    
    # Return the configured mock
    return mock_email_service


@pytest.fixture
def push_service():
    """Fixture that creates a mock PushService for testing"""
    # Create MagicMock for PushService
    mock_push_service = MagicMock(spec=PushService)
    
    # Configure is_enabled method to return True
    mock_push_service.is_enabled.return_value = True
    
    # Configure send_notification method to return {'success': True, 'message_id': 'test-msg-id'}
    mock_push_service.send_notification.return_value = {'success': True, 'message_id': 'test-msg-id'}
    
    # Configure send_batch method to return {'success': True, 'count': 1}
    mock_push_service.send_batch.return_value = {'success': True, 'count': 1}
    
    # Return the configured mock
    return mock_push_service


@pytest.fixture
def event_bus():
    """Fixture that creates a mock event bus for testing notification events"""
    # Use mock_event_bus function to create a mock event bus
    mock_bus = mock_event_bus()
    
    # Configure publish method to track events
    def mock_publish(event_type, event):
        mock_bus.published_events.append((event_type, event))
        return True
    mock_bus.publish.side_effect = mock_publish
    
    # Configure subscribe method to store event handlers
    def mock_subscribe(event_type, handler):
        if not hasattr(mock_bus, 'handlers'):
            mock_bus.handlers = {}
        if event_type not in mock_bus.handlers:
            mock_bus.handlers[event_type] = []
        mock_bus.handlers[event_type].append(handler)
        return True
    mock_bus.subscribe.side_effect = mock_subscribe
    
    # Return the configured mock
    return mock_bus


@pytest.fixture
def notification_service(email_service, push_service, event_bus):
    """Fixture that creates a NotificationService instance with mock dependencies"""
    # Create NotificationService instance
    service = NotificationService()
    
    # Replace _email_service with the mock email_service
    service._email_service = email_service
    
    # Replace _push_service with the mock push_service
    service._push_service = push_service
    
    # Replace _event_bus with the mock event_bus
    service._event_bus = event_bus
    
    # Return the service instance with mock dependencies
    return service


@pytest.fixture
def notification_collection(mongo_db):
    """Fixture that sets up a MongoDB collection for notifications"""
    # Get or create 'notifications' collection in the test database
    collection = mongo_db.get_collection('notifications')
    
    # Ensure any indexes needed for testing
    # (Example: collection.create_index([('recipient_id', 1), ('read', 1)]))
    
    # Return the collection for test use
    return collection


@pytest.fixture
def preference_collection(mongo_db):
    """Fixture that sets up a MongoDB collection for notification preferences"""
    # Get or create 'notification_preferences' collection in the test database
    collection = mongo_db.get_collection('notification_preferences')
    
    # Ensure any indexes needed for testing
    # (Example: collection.create_index('user_id', unique=True))
    
    # Return the collection for test use
    return collection


@pytest.fixture
def test_notification(test_user, notification_collection):
    """Fixture that creates a test notification for testing"""
    # Create notification data with essential fields
    notification_data = {
        "recipient_id": test_user['_id'],
        "type": NotificationType.TASK_ASSIGNED.value,
        "title": "Test Task Assigned",
        "content": "A test task has been assigned to you."
    }
    
    # Set recipient_id to test_user['_id']
    notification_data["recipient_id"] = test_user['_id']
    
    # Set type to TASK_ASSIGNED
    notification_data["type"] = NotificationType.TASK_ASSIGNED.value
    
    # Set title and content with test values
    notification_data["title"] = "Test Task Assigned"
    notification_data["content"] = "A test task has been assigned to you."
    
    # Set metadata with appropriate test data
    notification_data["metadata"] = {
        "created": datetime.datetime.utcnow(),
        "task_id": "test_task_id"
    }
    
    # Insert into notification_collection
    notification_collection.insert_one(notification_data)
    
    # Return the created notification document
    return notification_data


@pytest.fixture
def test_notification_preferences(test_user, preference_collection):
    """Fixture that creates test notification preferences for a user"""
    # Get default preferences using get_default_preferences()
    default_preferences = get_default_preferences()
    
    # Create preferences document with test_user['_id'] as user_id
    preferences_data = {
        "user_id": test_user['_id'],
        "global_settings": default_preferences["global_settings"],
        "type_settings": default_preferences["type_settings"],
        "project_settings": default_preferences["project_settings"],
        "quiet_hours": default_preferences["quiet_hours"]
    }
    
    # Add custom test-specific preferences (enable all channels)
    preferences_data["global_settings"]["in_app"] = True
    preferences_data["global_settings"]["email"] = True
    preferences_data["global_settings"]["push"] = True
    
    # Insert into preference_collection
    preference_collection.insert_one(preferences_data)
    
    # Return the created preference document
    return preferences_data


def create_test_notification(recipient_id, notification_type, title, content, priority=NotificationPriority.NORMAL):
    """Helper function to create a test notification with specific values"""
    # Create notification document with provided parameters
    notification = {
        "recipient_id": recipient_id,
        "type": notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
        "title": title,
        "content": content,
        "priority": priority.value if isinstance(priority, NotificationPriority) else priority
    }
    
    # Set read to False by default
    notification["read"] = False
    
    # Set action_url to a test URL
    notification["action_url"] = "http://test.example.com/task/123"
    
    # Set default metadata if not provided
    notification["metadata"] = {
        "created": datetime.datetime.utcnow(),
        "source": "test"
    }
    
    # Set default delivery status tracking
    notification["metadata"]["delivery_status"] = {
        "in_app": DeliveryStatus.PENDING.value,
        "email": DeliveryStatus.PENDING.value,
        "push": DeliveryStatus.PENDING.value
    }
    
    # Return the created notification document
    return notification