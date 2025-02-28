"""
Main application file for the Project Management Service that initializes and configures the Flask application,
registers API routes, middlewares, error handlers, and sets up database connections for project and member management.
"""

import os
import logging
from flask import Flask, jsonify, request  # flask v2.3.x

from .config import get_config  # Import service-specific configuration
from .api.projects import projects_bp  # Register projects API blueprint
from .api.members import member_blueprint  # Register members API blueprint
from src.backend.common.exceptions.error_handlers import register_error_handlers  # Register global error handlers for the Flask application
from src.backend.common.middlewares.cors import init_cors  # Configure CORS middleware for cross-origin requests
from src.backend.common.middlewares.request_id import init_request_id_middleware  # Configure request ID middleware for request tracking
from src.backend.common.middlewares.rate_limiter import RateLimiter  # Configure rate limiting middleware to prevent abuse
from src.backend.common.logging.logger import get_logger, add_request_context_to_logs  # Configure application logging
from src.backend.common.database.mongo.connection import initialize_database as init_mongo  # Initialize MongoDB connection
from src.backend.common.database.redis.connection import get_redis_client as init_redis  # Initialize Redis connection for caching and real-time features
from src.backend.common.events.event_bus import get_event_bus_instance as init_event_bus  # Initialize event bus for publishing and subscribing to events
from src.backend.common.events.handlers import register_project_event_handlers  # Register event handlers for project-related events

logger = logging.getLogger(__name__)  # Initialize logger

def create_app(config_name: str = None) -> Flask:
    """
    Factory function that creates and configures the Flask application instance for the Project microservice

    Args:
        config_name: The configuration name (e.g., 'development', 'production')

    Returns:
        Configured Flask application instance
    """
    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration based on config_name parameter from config.get_config
    init_app_config(app, config_name)

    # Set up logging with setup_logger
    add_request_context_to_logs(app)

    # Initialize database connections (MongoDB, Redis)
    init_mongo()
    init_redis()

    # Initialize event bus for project-related events
    init_event_bus()

    # Register project event handlers
    register_project_event_handlers()

    # Set up middleware (CORS, request ID, rate limiter)
    configure_middlewares(app)

    # Register API blueprints (projects_bp, member_blueprint)
    register_blueprints(app)

    # Register error handlers using register_error_handlers
    register_error_handlers(app)

    # Register health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint for the project service"""
        return jsonify({"status": "ok", "version": "1.0", "service": "project"})

    # Return configured application
    return app

def init_app_config(app: Flask, config_name: str) -> None:
    """Initializes application configuration based on environment"""
    config = get_config(config_name)
    app.config.from_object(config)
    logger.info(f"Configuring app with {config.__class__.__name__}")

def register_blueprints(app: Flask) -> None:
    """Registers all API blueprints with the Flask application"""
    app.register_blueprint(projects_bp)
    app.register_blueprint(member_blueprint)
    logger.info("Registered blueprints")

def configure_middlewares(app: Flask) -> None:
    """Sets up middleware for the Flask application"""
    init_cors(app)
    init_request_id_middleware(app)
    RateLimiter().apply(app)
    logger.info("Configured middlewares")

def configure_event_handlers(app: Flask) -> None:
    """Sets up event handlers for the project service"""
    register_project_event_handlers()
    logger.info("Configured event handlers")

# Export Flask application factory
if __name__ == "__main__":
    app = create_app(os.getenv('FLASK_ENV'))
    app.run(debug=True, host='0.0.0.0', port=5002)