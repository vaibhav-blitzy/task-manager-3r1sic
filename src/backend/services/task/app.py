"""
Main application file for the Task microservice that initializes and configures the Flask application,
registers API routes, middlewares, error handlers, and sets up database connections and event handlers.
"""

# Standard imports
import os  # Operating system interfaces for environment variables
import logging  # Standard logging functionality

# Third-party imports
from flask import Flask, jsonify, request  # flask==2.3.x
from flask_pymongo import PyMongo  # MongoDB integration for Flask - flask_pymongo==2.3.x
import redis  # Redis client for caching and pub/sub - redis==4.5.x

# Internal imports
from .config import get_config  # Import service-specific configuration
from .api import tasks as tasks_bp  # Register tasks API blueprint
from .api import comments as comments_bp  # Register comments API blueprint
from .api import search as search_bp  # Register search API blueprint
from common.exceptions import error_handlers  # Register global error handlers for the Flask application
from common.middlewares import cors  # Configure CORS middleware for cross-origin requests
from common.middlewares import request_id  # Configure request ID middleware for request tracking
from common.middlewares import rate_limiter  # Configure rate limiting middleware to prevent abuse
from common.logging import logger as logging_utils  # Configure application logging
from common.database.mongo import connection as mongo_conn  # Initialize MongoDB connection
from common.database.redis import connection as redis_conn  # Initialize Redis connection
from common.events import event_bus  # Initialize event bus for publishing and subscribing to events
from common.events import handlers as event_handlers  # Register event handlers for task-related events

# Initialize logger
logger = logging.getLogger(__name__)

def create_app(config_name: str) -> Flask:
    """
    Factory function that creates and configures the Flask application instance for the Task microservice

    Args:
        config_name: Configuration name (e.g., 'development', 'production')

    Returns:
        Configured Flask application instance
    """
    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration based on config_name parameter
    init_app_config(app, config_name)

    # Set up logging
    setup_logger(app)

    # Initialize database connections (MongoDB, Redis)
    init_mongo(app)
    init_redis(app)

    # Initialize event bus
    init_event_bus(app)

    # Register event handlers
    configure_event_handlers(app)

    # Set up middleware (CORS, request ID, rate limiter)
    configure_middlewares(app)

    # Register API blueprints (tasks, comments, search)
    register_blueprints(app)

    # Register error handlers
    error_handlers.register_error_handlers(app)

    # Return configured application
    return app

def init_app_config(app: Flask, config_name: str) -> None:
    """
    Initializes application configuration based on environment

    Args:
        app: Flask application instance
        config_name: Name of the configuration to use
    """
    # Determine configuration class based on config_name
    config = get_config(config_name)

    # Apply configuration to Flask app
    app.config.from_object(config)

    # Set additional configuration options if needed
    app.config['SERVICE_NAME'] = "task"
    logger.info(f"Application [{app.name}] configuration loaded for [{config_name}] environment")

def register_blueprints(app: Flask) -> None:
    """
    Registers all API blueprints with the Flask application

    Args:
        app: Flask application instance
    """
    # Register tasks blueprint
    app.register_blueprint(tasks_bp.tasks_bp)

    # Register comments blueprint
    app.register_blueprint(comments_bp.comments_blueprint)

    # Register search blueprint
    app.register_blueprint(search_bp.search_bp)

    # Set URL prefixes for each blueprint
    logger.info("API blueprints registered")

def register_extensions(app: Flask) -> None:
    """
    Initializes and registers Flask extensions

    Args:
        app: Flask application instance
    """
    # Initialize and configure Flask extensions
    # Register extensions with the application
    pass  # No extensions to register at this time

def configure_middlewares(app: Flask) -> None:
    """
    Sets up middleware for the Flask application

    Args:
        app: Flask application instance
    """
    # Set up CORS middleware
    cors.init_cors(app)

    # Set up request ID middleware
    request_id.init_request_id_middleware(app)

    # Set up rate limiting middleware
    rate_limiter_obj = rate_limiter.RateLimiter()
    rate_limiter_obj.apply(app)

    # Configure other middlewares as needed
    logger.info("Middlewares configured")

def health_check():
    """
    Simple health check endpoint for the service

    Returns:
        Service status information
    """
    # Check database connections
    # Return service status
    return jsonify({"status": "ok"}), 200

def init_mongo(app: Flask) -> None:
    """
    Initializes the MongoDB connection

    Args:
        app: Flask application instance
    """
    try:
        mongo_conn.initialize_database()
        logger.info("MongoDB connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB connection: {e}")

def init_redis(app: Flask) -> None:
    """
    Initializes the Redis connection

    Args:
        app: Flask application instance
    """
    try:
        redis_conn.get_redis_client()
        logger.info("Redis connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")

def init_event_bus(app: Flask) -> None:
    """
    Initializes the event bus

    Args:
        app: Flask application instance
    """
    try:
        event_bus_instance = event_bus.get_event_bus_instance()
        event_bus_instance.start()
        logger.info("Event bus initialized")
    except Exception as e:
        logger.error(f"Failed to initialize event bus: {e}")

def configure_event_handlers(app: Flask) -> None:
    """
    Sets up event handlers for the task service

    Args:
        app: Flask application instance
    """
    # Register handlers for task creation events
    # Register handlers for task update events
    # Register handlers for task deletion events
    # Register handlers for other relevant events
    pass