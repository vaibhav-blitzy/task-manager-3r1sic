# Standard library imports
from typing import Dict, Any, Optional

# Third-party imports
from flask import Blueprint, request, jsonify  # flask==2.3.x

# Internal imports
from ..services.notification_service import NotificationService  # Assuming version 1.0
from ..models.notification import NotificationType, NotificationPriority  # Assuming version 1.0
from common.schemas.pagination import create_pagination_params  # Assuming version 1.0
from common.exceptions.api_exceptions import APIException, NotFoundError, ValidationError  # Assuming version 1.0
from common.auth.jwt_utils import get_jwt_identity  # Assuming version 1.0
from common.auth.decorators import jwt_required  # Assuming version 1.0
from common.logging.logger import get_logger  # Assuming version 1.0

# Create a Flask Blueprint for notification routes
notification_blueprint = Blueprint('notifications', __name__)

# Get logger for the notifications API module
logger = get_logger(__name__)

# Instantiate NotificationService
notification_service = NotificationService()


@notification_blueprint.route('/', methods=['GET'])
@jwt_required()
def get_notifications() -> dict:
    """
    Retrieves a paginated list of notifications for the authenticated user.

    Returns:
        dict: JSON response with paginated notification list
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Extract pagination parameters from request.args
        pagination = create_pagination_params(request.args)

        # Extract optional 'unread_only' filter from request.args
        unread_only = request.args.get('unread_only', '').lower() == 'true'

        # Call notification_service.get_notifications with user_id, pagination, and filters
        notifications, total = notification_service.get_notifications(
            user_id=user_id,
            pagination=pagination,
            unread_only=unread_only
        )

        # Prepare the response data
        response_data = {
            "items": [notification.to_dict() for notification in notifications],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total
        }

        # Return JSON response with notifications list, count, and pagination metadata
        return jsonify(response_data), 200

    except Exception as e:
        logger.exception("Error retrieving notifications")
        raise APIException(message="Error retrieving notifications") from e


@notification_blueprint.route('/<notification_id>', methods=['GET'])
@jwt_required()
def get_notification(notification_id: str) -> dict:
    """
    Retrieves a single notification by ID.

    Args:
        notification_id: The ID of the notification to retrieve

    Returns:
        dict: JSON response with notification details
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Try to retrieve notification from notification_service
        notification = notification_service.get_notification(notification_id)

        # If notification doesn't exist, raise NotFoundError
        if not notification:
            raise NotFoundError(message="Notification not found", resource_type="notification", resource_id=notification_id)

        # Verify notification belongs to the current user, otherwise raise APIException
        if str(notification.recipient_id) != user_id:
            raise APIException(message="Unauthorized: Notification does not belong to this user", status_code=403)

        # Return JSON response with notification details
        return jsonify(notification.to_dict()), 200

    except NotFoundError:
        raise
    
    except APIException:
        raise

    except Exception as e:
        logger.exception(f"Error retrieving notification with ID: {notification_id}")
        raise APIException(message="Error retrieving notification") from e


@notification_blueprint.route('/<notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id: str) -> dict:
    """
    Marks a notification as read.

    Args:
        notification_id: The ID of the notification to mark as read

    Returns:
        dict: JSON response with updated notification
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Try to mark notification as read using notification_service.mark_as_read
        notification = notification_service.mark_as_read(notification_id, user_id)

        # If notification doesn't exist, raise NotFoundError
        if not notification:
            raise NotFoundError(message="Notification not found", resource_type="notification", resource_id=notification_id)

        # Return JSON response with success message and updated notification
        return jsonify({"message": "Notification marked as read", "notification": notification.to_dict()}), 200

    except NotFoundError:
        raise
    
    except APIException:
        raise

    except Exception as e:
        logger.exception(f"Error marking notification as read with ID: {notification_id}")
        raise APIException(message="Error marking notification as read") from e


@notification_blueprint.route('/unread/count', methods=['GET'])
@jwt_required()
def get_unread_count() -> dict:
    """
    Gets the count of unread notifications for the user.

    Returns:
        dict: JSON response with unread notification count
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Call notification_service.get_unread_count with user_id
        unread_count = notification_service.get_unread_count(user_id)

        # Return JSON response with unread count
        return jsonify({"unread_count": unread_count}), 200

    except Exception as e:
        logger.exception("Error getting unread notification count")
        raise APIException(message="Error getting unread notification count") from e


@notification_blueprint.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_as_read() -> dict:
    """
    Marks all notifications as read for the user.

    Returns:
        dict: JSON response with success message
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Extract optional filter parameters from request.get_json() if provided
        filters = request.get_json() if request.get_json() else {}

        # Call notification_service.mark_all_as_read with user_id and filters
        updated_count = notification_service.mark_all_as_read(user_id, filters)

        # Return JSON response with number of notifications marked as read
        return jsonify({"message": f"{updated_count} notifications marked as read"}), 200

    except Exception as e:
        logger.exception("Error marking all notifications as read")
        raise APIException(message="Error marking all notifications as read") from e


@notification_blueprint.route('/test', methods=['POST'])
@jwt_required()
def send_test_notification() -> dict:
    """
    Sends a test notification to the current user.

    Returns:
        dict: JSON response with test notification details
    """
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()

        # Extract message and channel from request.get_json()
        data = request.get_json()
        message = data.get('message', 'Test notification')
        channel = data.get('channel', 'in_app')

        # Validate required parameters are provided, otherwise raise ValidationError
        if not message or not channel:
            raise ValidationError(message="Missing required parameters", errors={"message": "Message is required", "channel": "Channel is required"})

        # Call notification_service method to create and send test notification
        notification, delivery_status = notification_service.send_test_notification(user_id, message, channel)

        # Return JSON response with test notification details and delivery status
        return jsonify({
            "message": "Test notification sent",
            "notification": notification.to_dict(),
            "delivery_status": delivery_status
        }), 200

    except ValidationError:
        raise

    except Exception as e:
        logger.exception("Error sending test notification")
        raise APIException(message="Error sending test notification") from e