"""
Service responsible for sending push notifications to user devices.

This module provides functionality to send push notifications via Firebase Cloud Messaging (FCM),
manage device tokens, and handle retry logic for notification delivery.
"""

import os
import json
import time
from typing import Dict, List, Optional, Union, Any

# Firebase imports
import firebase_admin
from firebase_admin import messaging, credentials

# Internal imports
from ..config import get_config
from ../../../common/logging/logger import get_logger
from ../models/notification import DeliveryStatus
from ../models/preference import NotificationChannel
from ../../../common/exceptions/api_exceptions import APIException
from ../../../common/database/mongo/models import TimestampedDocument, str_to_object_id, object_id_to_str

# Initialize logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

# Service name for logging and identification
SERVICE_NAME = "push_service"


class PushService:
    """
    Service for sending push notifications to user devices via Firebase Cloud Messaging.
    
    Provides methods for sending notifications to individuals, topics, and multiple devices,
    as well as functionality for managing device tokens.
    """
    
    def __init__(self):
        """
        Initialize the push notification service with Firebase credentials.
        """
        self._firebase_app = None
        self._initialized = False
        self._max_retries = config.NOTIFICATION_CHANNELS.get('push', {}).get('max_retries', 3)
        self._channel_config = config.get_channel_config('push')
        
        # Check if push notifications are enabled in configuration
        if not self._channel_config.get('enabled', False):
            logger.info("Push notification service is disabled in configuration")
            return
        
        # Initialize Firebase app if not already initialized
        try:
            # Check if default app already exists
            try:
                self._firebase_app = firebase_admin.get_app()
                logger.debug("Firebase app already initialized")
            except ValueError:
                # Get Firebase credentials from configuration
                credentials_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 
                                               self._channel_config.get('credentials_path'))
                
                if not credentials_path:
                    logger.error("Firebase credentials path not provided")
                    return
                
                # Initialize Firebase app with credentials
                cred = credentials.Certificate(credentials_path)
                self._firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase app initialized successfully")
            
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase app: {str(e)}")
            self._initialized = False
    
    def is_enabled(self) -> bool:
        """
        Check if push notification service is enabled and initialized.
        
        Returns:
            bool: True if service is enabled and initialized, False otherwise
        """
        return self._initialized
    
    def send_notification(self, user_id: str, title: str, body: str, 
                         data: Dict = None, token: str = None) -> Dict:
        """
        Send a push notification to a single user device.
        
        Args:
            user_id: User ID to send notification to
            title: Notification title
            body: Notification body text
            data: Additional data payload (optional)
            token: Device token to send to (if None, will look up user's tokens)
            
        Returns:
            dict: Result of sending notification containing success and message ID
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot send notification.")
            return {"success": False, "error": "Push notification service is disabled"}
        
        # Validate required parameters
        if not title or not body:
            return {"success": False, "error": "Title and body are required"}
        
        # If no token provided, try to get user's device tokens
        if not token:
            tokens = DeviceToken.find_by_user(user_id, active_only=True)
            if not tokens:
                return {"success": False, "error": "No device tokens registered for user"}
            
            # If multiple tokens, use send_to_tokens instead
            if len(tokens) > 1:
                return self.send_to_tokens([t.get('token') for t in tokens], title, body, data)
            
            # Use the single token
            token = tokens[0].get('token')
        
        # Validate token
        if not self._is_token_valid(token):
            return {"success": False, "error": "Invalid device token"}
        
        # Create notification message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=token
        )
        
        # Send message with retry logic
        result = self._send_with_retry(message)
        
        return result
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Dict = None) -> Dict:
        """
        Send a push notification to a topic (groups of users).
        
        Args:
            topic: The topic to send to
            title: Notification title
            body: Notification body text
            data: Additional data payload (optional)
            
        Returns:
            dict: Result of sending notification containing success and message ID
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot send notification.")
            return {"success": False, "error": "Push notification service is disabled"}
        
        # Validate required parameters
        if not topic or not title or not body:
            return {"success": False, "error": "Topic, title, and body are required"}
        
        # Create notification message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            topic=topic
        )
        
        # Send message with retry logic
        result = self._send_with_retry(message)
        
        return result
    
    def send_to_tokens(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send a push notification to multiple device tokens.
        
        Args:
            tokens: List of device tokens to send to
            title: Notification title
            body: Notification body text
            data: Additional data payload (optional)
            
        Returns:
            dict: Results of batch sending containing success count and failures
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot send notification.")
            return {"success": False, "error": "Push notification service is disabled"}
        
        # Validate tokens
        if not tokens:
            return {"success": False, "error": "No device tokens provided"}
        
        # Filter out invalid tokens
        valid_tokens = [token for token in tokens if self._is_token_valid(token)]
        
        if not valid_tokens:
            return {"success": False, "error": "No valid device tokens provided"}
        
        # Create multicast message
        multicast_message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            tokens=valid_tokens
        )
        
        # Send multicast message with retries
        try:
            batch_response = messaging.send_multicast(multicast_message)
            
            # Process results
            success_count = batch_response.success_count
            failure_count = batch_response.failure_count
            
            # Extract failures for detailed reporting
            failures = []
            if batch_response.responses:
                for idx, resp in enumerate(batch_response.responses):
                    if not resp.success:
                        if idx < len(valid_tokens):
                            failures.append({
                                "token": valid_tokens[idx],
                                "error": str(resp.exception)
                            })
            
            return {
                "success": success_count > 0,
                "success_count": success_count,
                "failure_count": failure_count,
                "total_tokens": len(valid_tokens),
                "failures": failures
            }
        
        except Exception as e:
            logger.error(f"Error sending multicast message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "success_count": 0,
                "failure_count": len(valid_tokens),
                "total_tokens": len(valid_tokens)
            }
    
    def send_batch(self, notifications: List[Dict]) -> Dict:
        """
        Send a batch of different notifications to various users.
        
        Args:
            notifications: List of notification configurations containing
                          recipients, tokens, topics, titles, bodies, and data
            
        Returns:
            dict: Results of batch operations containing success count and failures
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot send notifications.")
            return {"success": False, "error": "Push notification service is disabled"}
        
        if not notifications:
            return {"success": False, "error": "No notifications provided"}
        
        # Group notifications by type (token-based vs topic-based)
        token_notifications = {}  # Group by token for efficiency
        topic_notifications = []
        
        for notif in notifications:
            if "token" in notif and notif["token"]:
                token = notif["token"]
                if token not in token_notifications:
                    token_notifications[token] = []
                token_notifications[token].append(notif)
            elif "topic" in notif and notif["topic"]:
                topic_notifications.append(notif)
            elif "user_id" in notif and notif["user_id"]:
                # Need to look up tokens for this user
                user_id = notif["user_id"]
                tokens = DeviceToken.find_by_user(user_id, active_only=True)
                
                if tokens:
                    for token_obj in tokens:
                        token = token_obj.get('token')
                        if token not in token_notifications:
                            token_notifications[token] = []
                        token_notifications[token].append(notif)
        
        results = {
            "total": len(notifications),
            "token_notifications": {
                "count": sum(len(notifs) for notifs in token_notifications.values()),
                "success": 0,
                "failures": []
            },
            "topic_notifications": {
                "count": len(topic_notifications),
                "success": 0,
                "failures": []
            }
        }
        
        # Process token-based notifications
        if token_notifications:
            all_tokens = list(token_notifications.keys())
            valid_tokens = [token for token in all_tokens if self._is_token_valid(token)]
            
            for token in valid_tokens:
                for notif in token_notifications[token]:
                    title = notif.get("title", "")
                    body = notif.get("body", "")
                    data = notif.get("data", {})
                    
                    result = self.send_notification(
                        user_id=notif.get("user_id", ""),
                        title=title,
                        body=body,
                        data=data,
                        token=token
                    )
                    
                    if result.get("success", False):
                        results["token_notifications"]["success"] += 1
                    else:
                        results["token_notifications"]["failures"].append({
                            "token": token,
                            "error": result.get("error", "Unknown error"),
                            "notification": {
                                "title": title,
                                "body": body[:30] + "..." if len(body) > 30 else body
                            }
                        })
        
        # Process topic-based notifications
        for notif in topic_notifications:
            topic = notif.get("topic", "")
            title = notif.get("title", "")
            body = notif.get("body", "")
            data = notif.get("data", {})
            
            result = self.send_to_topic(
                topic=topic,
                title=title,
                body=body,
                data=data
            )
            
            if result.get("success", False):
                results["topic_notifications"]["success"] += 1
            else:
                results["topic_notifications"]["failures"].append({
                    "topic": topic,
                    "error": result.get("error", "Unknown error"),
                    "notification": {
                        "title": title,
                        "body": body[:30] + "..." if len(body) > 30 else body
                    }
                })
        
        # Calculate overall success
        total_success = results["token_notifications"]["success"] + results["topic_notifications"]["success"]
        total_count = results["token_notifications"]["count"] + results["topic_notifications"]["count"]
        
        results["success"] = total_success > 0
        results["success_rate"] = (total_success / total_count) if total_count > 0 else 0
        
        return results
    
    def register_device_token(self, user_id: str, device_token: str, 
                             device_type: str, device_name: str = None) -> bool:
        """
        Register a new device token for a user.
        
        Args:
            user_id: User ID to register token for
            device_token: The device token to register
            device_type: Type of device (ios, android, web)
            device_name: Optional name of the device
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot register device token.")
            return False
        
        if not user_id or not device_token:
            logger.error("User ID and device token are required for registration")
            return False
        
        try:
            # Check if token already exists for this user
            existing_token = DeviceToken.find_by_token(device_token, user_id)
            
            if existing_token:
                # Update last used timestamp
                existing_token.update_last_used()
                logger.debug(f"Updated existing device token for user {user_id}")
                return True
            
            # Create new device token
            new_token = DeviceToken(
                user_id=user_id,
                token=device_token,
                device_type=device_type,
                device_name=device_name
            )
            
            new_token.save()
            logger.info(f"Registered new device token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering device token: {str(e)}")
            return False
    
    def unregister_device_token(self, user_id: str, device_token: str) -> bool:
        """
        Remove a device token for a user.
        
        Args:
            user_id: User ID to unregister token for
            device_token: The device token to unregister
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        if not self.is_enabled():
            logger.warning("Push notification service is disabled. Cannot unregister device token.")
            return False
        
        if not user_id or not device_token:
            logger.error("User ID and device token are required for unregistration")
            return False
        
        try:
            # Find token
            token_obj = DeviceToken.find_by_token(device_token, user_id)
            
            if not token_obj:
                logger.warning(f"Device token not found for user {user_id}")
                return False
            
            # Deactivate token
            token_obj.deactivate()
            logger.info(f"Unregistered device token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering device token: {str(e)}")
            return False
    
    def get_user_device_tokens(self, user_id: str) -> List[Dict]:
        """
        Retrieve all registered device tokens for a user.
        
        Args:
            user_id: User ID to get tokens for
            
        Returns:
            list: List of device tokens associated with the user
        """
        if not user_id:
            return []
        
        try:
            tokens = DeviceToken.find_by_user(user_id, active_only=True)
            
            # Convert to simple dict representation for API
            return [token.to_dict() for token in tokens] if tokens else []
            
        except Exception as e:
            logger.error(f"Error retrieving device tokens: {str(e)}")
            return []
    
    def _send_with_retry(self, message: messaging.Message) -> Dict:
        """
        Private method to send notification with retry logic for transient failures.
        
        Args:
            message: Firebase message to send
            
        Returns:
            dict: Result of sending with success status and details
        """
        retries = 0
        result = {"success": False, "error": "Unknown error"}
        
        while retries <= self._max_retries:
            try:
                # Send message
                message_id = messaging.send(message)
                
                # Update result with success
                result = {"success": True, "message_id": message_id}
                return result
                
            except Exception as e:
                # Check if error is retryable
                is_retryable, error_message = self._handle_fcm_error(e)
                
                if is_retryable and retries < self._max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** retries) * 0.5 + (time.time() % 0.1)
                    logger.warning(f"Retryable error sending notification: {error_message}. "
                                 f"Retrying in {delay:.2f}s (attempt {retries+1}/{self._max_retries})")
                    time.sleep(delay)
                    retries += 1
                else:
                    # Permanent error or max retries reached
                    result = {"success": False, "error": error_message}
                    logger.error(f"Failed to send notification: {error_message}")
                    return result
        
        # Should not reach here, but just in case
        return result
    
    def _handle_fcm_error(self, error: Exception) -> tuple:
        """
        Private method to handle FCM error responses.
        
        Args:
            error: The exception raised during FCM operation
            
        Returns:
            tuple: (is_retryable, error_message)
        """
        error_message = str(error)
        
        # Classify FCM errors
        if "TOO_MANY_MESSAGES" in error_message:
            # Rate limiting error - retryable
            logger.warning(f"FCM rate limiting error: {error_message}")
            return True, "Too many messages sent too quickly, will retry"
            
        elif "UNAVAILABLE" in error_message or "INTERNAL" in error_message:
            # Server is unavailable - retryable
            logger.warning(f"FCM server error: {error_message}")
            return True, "FCM server temporarily unavailable, will retry"
            
        elif "UNREGISTERED" in error_message or "INVALID_ARGUMENT" in error_message:
            # Token is invalid or unregistered - not retryable
            logger.error(f"FCM invalid token error: {error_message}")
            return False, "Invalid or unregistered device token"
            
        elif "SENDER_ID_MISMATCH" in error_message:
            # Token doesn't match sender - not retryable
            logger.error(f"FCM sender ID mismatch: {error_message}")
            return False, "Device token doesn't match sender ID"
            
        elif "QUOTA_EXCEEDED" in error_message:
            # Quota exceeded - not retryable now
            logger.error(f"FCM quota exceeded: {error_message}")
            return False, "FCM quota exceeded"
            
        elif "AUTHENTICATION_ERROR" in error_message:
            # Authentication error - not retryable without fixing credentials
            logger.error(f"FCM authentication error: {error_message}")
            return False, "FCM authentication failed"
            
        else:
            # Unknown error - retry once
            logger.error(f"Unknown FCM error: {error_message}")
            return True, f"Unknown FCM error: {error_message}"
    
    def _is_token_valid(self, token: str) -> bool:
        """
        Private method to check if a device token appears valid.
        
        Args:
            token: The token to validate
            
        Returns:
            bool: True if token format is valid, False otherwise
        """
        # Basic validation - ensure token is a non-empty string with sufficient length
        if not token or not isinstance(token, str):
            return False
            
        # FCM tokens are at least 140 characters
        if len(token) < 140:
            return False
            
        return True


class DeviceToken(TimestampedDocument):
    """
    MongoDB document model representing a device token for push notifications.
    """
    
    collection_name = "device_tokens"
    
    schema = {
        "user_id": {"type": "ObjectId", "required": True},
        "token": {"type": "str", "required": True},
        "device_type": {"type": "str", "required": True},
        "device_name": {"type": "str", "required": False, "nullable": True},
        "is_active": {"type": "bool", "required": True},
        "last_used_at": {"type": "datetime", "required": True}
    }
    
    use_schema_validation = True
    
    def __init__(self, user_id, token, device_type, device_name=None, is_active=True):
        """
        Initialize a new device token instance.
        
        Args:
            user_id: User ID the token belongs to
            token: The device token string
            device_type: Type of device (ios, android, web)
            device_name: Optional name of the device
            is_active: Whether the token is active
        """
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
            
        # Set default activation status and last used time
        is_active = True if is_active is None else is_active
        last_used_at = datetime.now()
            
        # Prepare document data
        data = {
            "user_id": user_id,
            "token": token,
            "device_type": device_type,
            "device_name": device_name,
            "is_active": is_active,
            "last_used_at": last_used_at
        }
        
        # Initialize the document
        super().__init__(data=data)
    
    @classmethod
    def find_by_user(cls, user_id, active_only=True):
        """
        Find all device tokens for a specific user.
        
        Args:
            user_id: User ID to find tokens for
            active_only: If True, only return active tokens
            
        Returns:
            list: List of DeviceToken objects
        """
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
            
        # Prepare query
        query = {"user_id": user_id}
        
        if active_only:
            query["is_active"] = True
            
        # Get collection and execute query
        instance = cls()
        collection = instance.collection()
        
        # Find all matching tokens
        results = collection.find(query)
        
        # Convert to DeviceToken objects
        return [cls(data=doc, is_new=False) for doc in results]
    
    @classmethod
    def find_by_token(cls, token, user_id=None):
        """
        Find a device token by its token string and user.
        
        Args:
            token: The token string to find
            user_id: Optional user ID to restrict search
            
        Returns:
            DeviceToken or None: DeviceToken if found, None otherwise
        """
        # Prepare query
        query = {"token": token}
        
        if user_id:
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = str_to_object_id(user_id)
                
            query["user_id"] = user_id
            
        # Get collection and execute query
        instance = cls()
        collection = instance.collection()
        
        # Find matching token
        result = collection.find_one(query)
        
        # Return DeviceToken if found, None otherwise
        return cls(data=result, is_new=False) if result else None
    
    def deactivate(self):
        """
        Mark a device token as inactive.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self._data["is_active"] = False
        
        try:
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error deactivating device token: {str(e)}")
            return False
    
    def update_last_used(self):
        """
        Update the last used timestamp for a device token.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self._data["last_used_at"] = datetime.now()
        
        try:
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error updating device token last used: {str(e)}")
            return False