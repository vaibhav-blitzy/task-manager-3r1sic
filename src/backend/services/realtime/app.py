import os
import sys
import logging
import traceback
import signal

# Third-party imports
from flask import Flask
from flask_socketio import SocketIO  # flask-socketio 5.3.x

# Internal imports
from .config import get_config  # src/backend/services/realtime/config.py
from .services.socket_service import SocketService  # src/backend/services/realtime/services/socket_service.py
from .services.presence_service import PresenceService  # src/backend/services/realtime/services/presence_service.py
from .services.collaboration_service import CollaborationService  # src/backend/services/realtime/services/collaboration_service.py
from .api.channels import channels_bp  # src/backend/services/realtime/api/channels.py
from .api.websocket import initialize_websocket  # src/backend/services/realtime/api/websocket.py
from ...common.exceptions.error_handlers import register_error_handlers  # src/backend/common/exceptions/error_handlers.py
from ...common.middlewares.cors import setup_cors  # src/backend/common/middlewares/cors.py
from ...common.database.redis.connection import get_redis_connection  # src/backend/common/database/redis/connection.py
from ...common.logging.logger import setup_logger  # src/backend/common/logging/logger.py

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize global variables
app = Flask(__name__)
socketio = SocketIO()
config = get_config()
socket_service = SocketService()
presence_service = PresenceService()
collaboration_service = CollaborationService()
redis_client = get_redis_connection()


def create_app():
    """
    Factory function to create and configure the Flask application with all necessary extensions and middlewares
    """
    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration from config module using get_config()
    app.config.from_object(config)

    # Set up logging using setup_logger function
    setup_logger(app)

    # Initialize Redis connection
    redis_client = get_redis_connection()

    # Set up CORS middleware
    setup_cors(app)

    # Register channels API blueprint
    app.register_blueprint(channels_bp)

    # Register error handlers
    register_error_handlers(app)

    # Initialize SocketIO with Flask app
    socketio = initialize_websocket(app)

    # Initialize socket_service, presence_service, and collaboration_service
    socket_service, presence_service, collaboration_service = setup_services(app, socketio)

    # Return tuple containing app and socketio instances
    return app, socketio


def setup_services(app, socketio):
    """
    Initialize and configure service instances needed for realtime functionality
    """
    # Initialize SocketService instance
    socket_service = SocketService()

    # Initialize PresenceService instance
    presence_service = PresenceService()

    # Initialize CollaborationService instance
    collaboration_service = CollaborationService()

    # Configure services with app and SocketIO references
    # (No specific configuration needed at this time)

    # Set up event handlers and integrations between services
    # (No specific event handlers or integrations needed at this time)

    # Return tuple of initialized services
    return socket_service, presence_service, collaboration_service


def signal_handler(signum, frame):
    """
    Handler for system signals to ensure graceful shutdown
    """
    # Log receipt of system signal
    logger.info(f"Received system signal: {signum}")

    # Perform graceful shutdown of SocketIO connections
    print("Shutting down SocketIO...")
    socketio.stop()

    # Clean up resources and close connections
    print("Cleaning up resources...")
    # Add any specific cleanup logic here

    # Exit the application cleanly
    print("Exiting application...")
    sys.exit(0)


def register_signal_handlers():
    """
    Register handlers for system signals
    """
    # Register SIGINT handler
    signal.signal(signal.SIGINT, signal_handler)

    # Register SIGTERM handler
    signal.signal(signal.SIGTERM, signal_handler)

    # Log registration of signal handlers
    logger.info("Registered signal handlers")


if __name__ == '__main__':
    # Create the Flask application
    app, socketio = create_app()

    # Register signal handlers for graceful shutdown
    register_signal_handlers()

    # Run the application
    try:
        socketio.run(app, host='0.0.0.0', port=5003, debug=True)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()