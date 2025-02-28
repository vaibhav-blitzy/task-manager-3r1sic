"""
Initializes the Realtime API module, exporting blueprints and event handlers for real-time collaboration features.
Provides a clean interface for registering all API endpoints with the Flask application.
"""
from flask import Flask  # flask - 2.0.1
from flask_socketio import SocketIO  # flask-socketio 5.3.x

from .channels import channels_blueprint  # src/backend/services/realtime/api/channels.py
from .websocket import websocket_handlers  # src/backend/services/realtime/api/websocket.py
from ....common.exceptions.error_handlers import register_error_handlers  # src/backend/common/exceptions/error_handlers.py
from ....common.logging.logger import get_logger  # src/backend/common/logging/logger.py

# Initialize logger
logger = get_logger(__name__)


def init_app(app: Flask, socketio: SocketIO) -> None:
    """
    Initializes and registers all Realtime API blueprints and handlers with the Flask application

    Args:
        app: Flask application instance
        socketio: SocketIO instance

    Returns:
        None: This function doesn't return a value
    """
    # Register the channels_blueprint with the Flask app
    app.register_blueprint(channels_blueprint)

    # Apply any blueprint-specific middleware or configuration
    # (Currently, there is no blueprint-specific middleware)

    # Register error handlers for the API endpoints
    register_error_handlers(app)

    # Log successful API initialization
    logger.info("Realtime API initialized")


__all__ = [
    "init_app",
    "channels_blueprint",
    "websocket_handlers"
]