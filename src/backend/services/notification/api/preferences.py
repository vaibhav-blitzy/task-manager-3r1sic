# Standard Library Imports
from typing import Dict, Any

# Flask Imports
from flask import Blueprint, request, jsonify

# Internal Module Imports
from ..models.preference import NotificationPreference, NotificationChannel, DigestFrequency, get_user_preferences
from ..models.notification import NotificationType
from ....common.exceptions.api_exceptions import ValidationError, NotFoundError
from ....common.auth.decorators import token_required, get_current_user
from ....common.logging.logger import get_logger
from ....common.utils.validators import validate_enum

# Flask Blueprint for preference routes - v2.3.x
preferences_blueprint = Blueprint('preferences', __name__)

# Logger instance for the module
logger = get_logger(__name__)


@preferences_blueprint.route('/', methods=['GET'])
@token_required
def get_preferences() -> dict:
    """
    Retrieves the notification preferences for the authenticated user.

    Returns:
        dict: JSON response with user's notification preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Retrieve or create user preferences
    preferences = get_user_preferences(user_id)

    # Convert preferences to dictionary representation
    preferences_dict = preferences.to_dict()

    # Return preferences as JSON response
    return jsonify(preferences_dict)


@preferences_blueprint.route('/global', methods=['PUT'])
@token_required
def update_global_settings() -> dict:
    """
    Updates the global notification settings for the authenticated user.

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Get request JSON data containing updated global settings
    data = request.get_json()

    # Validate the settings structure
    try:
        validate_channel_settings(data)
        if "digest" in data:
            if not isinstance(data["digest"], dict):
                raise ValidationError("Digest settings must be a dictionary")
            if "enabled" not in data["digest"]:
                raise ValidationError("Digest settings must include 'enabled' field")
            if "frequency" in data["digest"]:
                validate_enum(data["digest"]["frequency"], [e.value for e in DigestFrequency], "digest frequency")
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise e

    # Retrieve user preferences or create if not found
    preferences = get_user_preferences(user_id)

    # Update global settings
    preferences.update_global_settings(data)

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


@preferences_blueprint.route('/types/<notification_type>', methods=['PUT'])
@token_required
def update_type_settings(notification_type: str) -> dict:
    """
    Updates notification settings for a specific notification type.

    Args:
        notification_type: The notification type to update settings for

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Validate notification_type is a valid NotificationType enum value
    try:
        NotificationType(notification_type)
    except ValueError:
        raise ValidationError(f"Invalid notification type: {notification_type}")

    # Get request JSON data containing updated type settings
    data = request.get_json()

    # Validate the settings structure
    try:
        validate_channel_settings(data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise e

    # Retrieve user preferences or create if not found
    preferences = get_user_preferences(user_id)

    # Update notification type settings
    preferences.update_type_settings(notification_type, data)

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


@preferences_blueprint.route('/projects/<project_id>', methods=['PUT'])
@token_required
def update_project_settings(project_id: str) -> dict:
    """
    Updates notification settings for a specific project.

    Args:
        project_id: The project ID to update settings for

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Validate project_id format
    if not isinstance(project_id, str) or not project_id:
        raise ValidationError("Invalid project_id format")

    # Get request JSON data containing updated project settings
    data = request.get_json()

    # Validate the settings structure
    try:
        validate_channel_settings(data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise e

    # Retrieve user preferences or create if not found
    preferences = get_user_preferences(user_id)

    # Update project settings
    preferences.update_project_settings(project_id, data)

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


@preferences_blueprint.route('/quiet-hours', methods=['PUT'])
@token_required
def update_quiet_hours() -> dict:
    """
    Updates quiet hours settings for the authenticated user.

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Get request JSON data containing updated quiet hours settings
    data = request.get_json()

    # Validate the settings structure
    try:
        validate_quiet_hours_settings(data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise e

    # Retrieve user preferences or create if not found
    preferences = get_user_preferences(user_id)

    # Update quiet hours
    preferences.update_quiet_hours(data)

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


@preferences_blueprint.route('/types/<notification_type>', methods=['DELETE'])
@token_required
def delete_type_settings(notification_type: str) -> dict:
    """
    Removes custom settings for a notification type, reverting to global defaults.

    Args:
        notification_type: The notification type to remove settings for

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Validate notification_type is a valid NotificationType enum value
    try:
        NotificationType(notification_type)
    except ValueError:
        raise ValidationError(f"Invalid notification type: {notification_type}")

    # Retrieve user preferences
    preferences = NotificationPreference.find_by_user_id(user_id)

    # If preferences not found, raise NotFoundError
    if not preferences:
        raise NotFoundError("Preferences not found")

    # Remove the specified notification type from preferences.type_settings
    if notification_type in preferences._data.get("type_settings", {}):
        del preferences._data["type_settings"][notification_type]

    # Save updated preferences
    preferences.save()

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


@preferences_blueprint.route('/projects/<project_id>', methods=['DELETE'])
@token_required
def delete_project_settings(project_id: str) -> dict:
    """
    Removes custom settings for a project, reverting to global/type defaults.

    Args:
        project_id: The project ID to remove settings for

    Returns:
        dict: JSON response with updated preferences
    """
    # Get the current authenticated user
    user = get_current_user()
    user_id = user.get("user_id")

    # Validate project_id format
    if not isinstance(project_id, str) or not project_id:
        raise ValidationError("Invalid project_id format")

    # Retrieve user preferences
    preferences = NotificationPreference.find_by_user_id(user_id)

    # If preferences not found, raise NotFoundError
    if not preferences:
        raise NotFoundError("Preferences not found")

    # Remove the specified project from preferences.project_settings
    if project_id in preferences._data.get("project_settings", {}):
        del preferences._data["project_settings"][project_id]

    # Save updated preferences
    preferences.save()

    # Return updated preferences as JSON response
    return jsonify(preferences.to_dict())


def validate_channel_settings(settings: dict) -> bool:
    """
    Helper function to validate notification channel settings structure.

    Args:
        settings: Settings dictionary

    Returns:
        True if valid, otherwise raises ValidationError
    """
    # Check that required channels (inApp, email, push) exist in settings
    required_channels = ["in_app", "email", "push"]
    for channel in required_channels:
        if channel not in settings:
            raise ValidationError(f"Missing channel setting: {channel}")

    # Validate that all channel values are boolean
    for channel, value in settings.items():
        if not isinstance(value, bool):
            raise ValidationError(f"Channel value for {channel} must be a boolean")

    return True


def validate_quiet_hours_settings(settings: dict) -> bool:
    """
    Helper function to validate quiet hours settings structure.

    Args:
        settings: Settings dictionary

    Returns:
        True if valid, otherwise raises ValidationError
    """
    # Check that required fields (enabled, start, end, timezone, excludeUrgent) exist in settings
    required_fields = ["enabled", "start", "end", "timezone", "excludeUrgent"]
    for field in required_fields:
        if field not in settings:
            raise ValidationError(f"Missing quiet hours setting: {field}")

    # Validate that enabled and excludeUrgent are boolean
    if not isinstance(settings["enabled"], bool):
        raise ValidationError("Quiet hours 'enabled' must be a boolean")
    if not isinstance(settings["excludeUrgent"], bool):
        raise ValidationError("Quiet hours 'excludeUrgent' must be a boolean")

    # Validate that start and end are valid time strings in format HH:MM
    try:
        datetime.strptime(settings["start"], "%H:%M")
        datetime.strptime(settings["end"], "%H:%M")
    except ValueError:
        raise ValidationError("Quiet hours 'start' and 'end' must be in HH:MM format")

    # Validate that timezone is a valid timezone string
    try:
        import pytz
        pytz.timezone(settings["timezone"])
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValidationError("Invalid timezone")

    return True