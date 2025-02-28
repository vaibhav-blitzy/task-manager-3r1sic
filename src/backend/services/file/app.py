"""
Main application file for the File Management Service microservice that initializes the Flask application,
configures middleware, registers API routes, and sets up database connections and error handlers.
This service handles file uploads, downloads, and management for the Task Management System.
"""
# Third-party imports
from flask import Flask, jsonify # flask 2.3.x
import os # standard library
import sys # standard library

# Internal imports
from .config import get_config # Import configuration for file service environment settings
from .api.files import file_blueprint # Import API routes for file operations
from .api.attachments import attachments_blueprint # Import API routes for attachment operations
from ...common.database.mongo.connection import initialize_database # Initialize MongoDB connection for file metadata storage
from ...common.middlewares.cors import configure_cors # Configure CORS settings for the file service API
from ...common.middlewares.request_id import init_request_id_middleware # Initialize request ID tracking for distributed tracing
from ...common.exceptions.error_handlers import register_error_handlers # Register standardized error handlers for API exceptions
from ...common.logging.logger import get_logger # Get configured logger for the file service

# Initialize logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

def create_app(test_config=None):
    """
    Flask application factory that creates and configures the file service application
    """
    # Create Flask application instance with appropriate name and configuration
    app = Flask(__name__)
    app.config.from_object(config)

    # Override configuration with test_config if provided (for testing)
    if test_config:
        app.config.update(test_config)

    # Initialize MongoDB connection for file metadata storage
    initialize_database()

    # Register file and attachment blueprints with URL prefixes
    app.register_blueprint(file_blueprint, url_prefix='/api/v1/files')
    app.register_blueprint(attachments_blueprint, url_prefix='/api/v1/attachments')

    # Configure CORS middleware for cross-origin requests
    configure_cors(app)

    # Initialize request ID middleware for request tracking
    init_request_id_middleware(app)

    # Register standardized error handlers for consistent API responses
    register_error_handlers(app)

    # Create health check endpoint for service monitoring
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint to verify service status for monitoring"""
        # Check database connection status
        db_status = "OK"  # Placeholder for actual database check

        # Check storage service availability
        storage_status = "OK"  # Placeholder for actual storage check

        # Check configuration status
        config_status = "OK"  # Placeholder for actual config check

        # Return health status dictionary with component statuses
        return jsonify({
            'database': db_status,
            'storage': storage_status,
            'config': config_status
        }), 200

    # Log successful application initialization
    logger.info("File service application initialized")

    # Return the configured Flask application
    return app