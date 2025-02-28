# flask v2.3.x
from flask import Flask, request, jsonify
# datetime standard library
import datetime
# uuid standard library
import uuid
# logging standard library
import logging

# Internal imports for authentication logic
from .config import CONFIG  # Service-specific configuration settings
from .api.auth import auth_bp  # Auth blueprint for authentication routes
from .api.roles import roles_bp  # Roles blueprint for role management routes
from .api.users import users_bp  # Users blueprint for user management routes
from src.backend.common.database.mongo.connection import init_mongodb  # Initialize MongoDB connection for the service
from src.backend.common.database.redis.connection import init_redis  # Initialize Redis connection for the service
from src.backend.common.exceptions.error_handlers import register_error_handlers  # Register error handlers for the Flask application
from src.backend.common.middlewares.cors import init_cors  # Initialize CORS middleware
from src.backend.common.middlewares.rate_limiter import init_rate_limiter  # Initialize rate limiting middleware
from src.backend.common.middlewares.request_id import init_request_id  # Initialize request ID middleware
from src.backend.common.logging.logger import setup_logger  # Configure logging for the service
from src.backend.common.events.event_bus import init_event_bus  # Initialize event bus for publishing and subscribing to events
from flask import Blueprint

# Blueprint for authentication API routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
# Blueprint for roles API routes
roles_bp = Blueprint('roles', __name__, url_prefix='/roles')
# Blueprint for users API routes
users_bp = Blueprint('users', __name__, url_prefix='/users')

# Initialize logger
logger = logging.getLogger(__name__)

# Global Flask application instance
app = None


def create_app(config_override=None):
    """Factory function that creates and configures the Flask application instance

    Args:
        config_override (dict, optional): A dictionary to override the default configuration. Defaults to None.

    Returns:
        Flask: Configured Flask application instance
    """
    # Create a new Flask application instance
    app = Flask(__name__)

    # Load configuration from CONFIG dictionary
    app.config.from_object(CONFIG)

    # Apply any configuration overrides passed as parameter
    if config_override:
        app.config.update(config_override)

    # Initialize logging with setup_logger
    setup_logger(app)

    # Initialize MongoDB connection with init_mongodb
    init_mongodb()

    # Initialize Redis connection with init_redis
    init_redis()

    # Initialize CORS middleware with init_cors
    init_cors(app)

    # Initialize rate limiter middleware with init_rate_limiter
    init_rate_limiter(app)

    # Initialize request ID middleware with init_request_id
    init_request_id(app)

    # Initialize event bus with init_event_bus
    init_event_bus()

    # Register error handlers with register_error_handlers
    register_error_handlers(app)

    # Register blueprints: auth_bp, roles_bp, users_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(roles_bp, url_prefix='/api/v1/roles')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')

    # Log application initialization
    logger.info("Flask application initialized")

    # Return the configured Flask application
    return app


def init_app():
    """Initializes the application with default configuration

    Returns:
        Flask: Configured Flask application instance
    """
    # Call create_app with no overrides
    app = create_app()

    # Log application initialization
    logger.info("Flask application initialized with default configuration")

    # Return the configured Flask application
    return app


# Create Flask app instance when the script is run
if __name__ == "__main__":
    app = init_app()
    # Run the app in debug mode, on localhost, and on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)