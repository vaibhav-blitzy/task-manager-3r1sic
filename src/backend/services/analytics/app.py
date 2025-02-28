import os
import logging
from flask import Flask, Blueprint, jsonify, request  # flask==2.3.x
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # prometheus_client==0.14.x

# Internal imports
from .config import config
from .api.dashboards import dashboard_blueprint
from .api.metrics import metrics_blueprint
from .api.reports import reports_blueprint
from src.backend.common.database.mongo.connection import init_mongodb
from src.backend.common.database.redis.connection import init_redis
from src.backend.common.exceptions.error_handlers import register_error_handlers
from src.backend.common.middlewares.cors import init_cors
from src.backend.common.middlewares.rate_limiter import init_rate_limiter
from src.backend.common.middlewares.request_id import init_request_id
from src.backend.common.logging.logger import setup_logger
from src.backend.common.events.event_bus import init_event_bus

# Initialize Flask application
app = Flask(__name__)

# Initialize logger
logger = logging.getLogger(__name__)

def create_app(config_override=None):
    """
    Factory function to create and configure the Flask application
    """
    # Determine environment from FLASK_ENV environment variable
    env = os.environ.get('FLASK_ENV', 'default')

    # Load configuration from config module based on environment
    app.config.from_object(config[env])

    # Apply any config_override values if provided
    if config_override:
        app.config.update(config_override)

    # Set up logging with setup_logger
    setup_logger(app)

    # Initialize MongoDB connection with init_mongodb
    init_mongodb()

    # Initialize Redis connection with init_redis
    init_redis()

    # Initialize middleware (init_cors, init_rate_limiter, init_request_id)
    init_cors(app)
    init_rate_limiter(app)
    init_request_id_middleware(app)

    # Initialize event bus with init_event_bus
    init_event_bus()

    # Register error handlers with register_error_handlers
    register_error_handlers(app)

    # Register API blueprints
    register_blueprints(app)

    # Register health check and metrics endpoints
    @app.route('/health')
    def health_check():
        """Simple health check endpoint for service monitoring"""
        return jsonify({"status": "ok", "service": "analytics", "version": "1.0.0"})

    @app.route('/metrics')
    def metrics_endpoint():
        """Endpoint to expose Prometheus metrics"""
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

    return app

def init_app():
    """Initialize the application with default configuration"""
    return create_app()

def register_blueprints(app):
    """Register API blueprints with the Flask application"""
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(metrics_blueprint)
    app.register_blueprint(reports_blueprint)
    logger.info("Registered blueprints")

# Create the Flask app instance
app = create_app()

# Export the Flask app instance
if __name__ == "__main__":
    # Start the Flask development server
    app.run(debug=True)