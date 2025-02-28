"""
Main application entry point for the API Gateway service that routes client requests to 
appropriate backend microservices. Configures middleware for CORS, rate limiting, error 
handling, and request logging while providing health check endpoints and route proxying 
functionality.
"""

import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv  # python-dotenv 0.19.1

# Internal imports
from .config import get_config
from .routes import blueprints
from src.backend.common.middlewares.cors import configure_cors
from src.backend.common.middlewares.rate_limiter import RateLimiter
from src.backend.common.exceptions.error_handlers import register_error_handlers
from src.backend.common.logging.logger import get_logger, add_request_context_to_logs

# Set up module logger
logger = get_logger(__name__)

def create_app(test_config=None):
    """
    Flask application factory that creates and configures the API Gateway Flask application.
    
    Args:
        test_config (dict): Optional test configuration to override default settings
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask application instance with appropriate name and configuration
    app = Flask(__name__, instance_relative_config=True)
    
    # Load environment-specific configuration using get_config()
    config = get_config()
    app.config.from_object(config)
    
    # Override with test_config if provided (for testing purposes)
    if test_config is not None:
        app.config.update(test_config)
        logger.info("Applied test configuration")
    
    # Configure cross-origin resource sharing (CORS) with settings from config
    configure_cors(app)
    logger.info("CORS configured")
    
    # Apply rate limiting middleware with limits from configuration
    rate_limiter = RateLimiter()
    rate_limiter.apply(app)
    logger.info("Rate limiting middleware applied")
    
    # Register error handlers for standardized error responses
    register_error_handlers(app)
    logger.info("Error handlers registered")
    
    # Add request context to logs for distributed tracing
    add_request_context_to_logs(app)
    logger.info("Request context logging configured")
    
    # Register health check blueprint for monitoring endpoints
    app.register_blueprint(blueprints['health'])
    logger.info("Health check blueprint registered")
    
    # Register proxy blueprint for routing requests to backend services
    app.register_blueprint(blueprints['proxy'])
    logger.info("Proxy blueprint registered")
    
    logger.info("API Gateway application successfully created and configured")
    
    return app