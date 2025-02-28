# Flask Blueprint for organizing notification-related routes
from flask import Blueprint

# Import the notification routes blueprint from the notifications module
from .notifications import notification_blueprint  # Import notification routes blueprint

# Import the notification preferences routes blueprint from the preferences module
from .preferences import preferences_blueprint  # Import preferences routes blueprint


# Expose the notification routes blueprint for registration with the Flask app
__all__ = ['notification_blueprint', 'preferences_blueprint']