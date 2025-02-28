"""
Cross-Origin Resource Sharing (CORS) middleware for Flask applications.

This module provides a configurable CORS middleware that controls which domains
can access the API and what methods and headers are allowed, helping to prevent
unauthorized cross-origin requests while enabling legitimate integrations.
"""

import logging
from typing import Dict, Any, Optional, List

from flask import Flask
from flask_cors import CORS

from ..config.base import BaseConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Default CORS settings to use if not overridden by configuration
DEFAULT_CORS_SETTINGS = {
    'origins': ['http://localhost:3000', 'http://localhost:5173'],  # Development origins
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],  # Standard REST methods
    'allow_headers': ['Content-Type', 'Authorization', 'X-Request-ID'],  # Common headers
    'expose_headers': ['X-Request-ID'],  # Headers client can access
    'supports_credentials': True,  # Allow cookies to be sent with requests
    'max_age': 600  # Cache preflight requests for 10 minutes
}


def get_cors_settings(config: Dict) -> Dict:
    """
    Extract and validate CORS settings from the application configuration.
    
    Args:
        config: The configuration dictionary to extract settings from.
        
    Returns:
        Dict: Validated CORS settings dictionary merged with defaults.
    """
    # Extract CORS settings or use empty dict if not present
    cors_config = config.get('CORS_SETTINGS', {})
    
    # Create final settings by merging defaults with config settings
    # This gives priority to the provided config values while filling in any missing values
    settings = {**DEFAULT_CORS_SETTINGS}
    
    # Update with user-provided settings
    for key, value in cors_config.items():
        if key in settings:
            settings[key] = value
    
    # Validate settings types to avoid runtime errors
    
    # Origins should be a list of strings
    if not isinstance(settings['origins'], list):
        logger.warning("CORS origins should be a list. Using default origins.")
        settings['origins'] = DEFAULT_CORS_SETTINGS['origins']
    
    # Methods should be a list of valid HTTP methods
    if not isinstance(settings['methods'], list) or not all(isinstance(m, str) for m in settings['methods']):
        logger.warning("CORS methods should be a list of strings. Using default methods.")
        settings['methods'] = DEFAULT_CORS_SETTINGS['methods']
    
    # Allow headers should be a list of strings
    if not isinstance(settings['allow_headers'], list) or not all(isinstance(h, str) for h in settings['allow_headers']):
        logger.warning("CORS allow_headers should be a list of strings. Using default headers.")
        settings['allow_headers'] = DEFAULT_CORS_SETTINGS['allow_headers']
    
    # Expose headers should be a list of strings
    if not isinstance(settings['expose_headers'], list) or not all(isinstance(h, str) for h in settings['expose_headers']):
        logger.warning("CORS expose_headers should be a list of strings. Using default headers.")
        settings['expose_headers'] = DEFAULT_CORS_SETTINGS['expose_headers']
    
    # Supports credentials should be a boolean
    if not isinstance(settings['supports_credentials'], bool):
        logger.warning("CORS supports_credentials should be a boolean. Using default (True).")
        settings['supports_credentials'] = DEFAULT_CORS_SETTINGS['supports_credentials']
    
    # Max age should be an integer
    if not isinstance(settings['max_age'], int) or settings['max_age'] < 0:
        logger.warning("CORS max_age should be a positive integer. Using default (600).")
        settings['max_age'] = DEFAULT_CORS_SETTINGS['max_age']
    
    return settings


def configure_cors(app: Flask, config: Optional[Dict] = None) -> CORS:
    """
    Configure and initialize CORS for a Flask application using settings from config.
    
    Args:
        app: The Flask application to configure CORS for.
        config: Optional configuration dictionary. If not provided, app.config will be used.
        
    Returns:
        CORS: The configured CORS instance.
    """
    # Use provided config or get from app if not provided
    if config is None:
        config = app.config
    
    # Get validated CORS settings
    cors_settings = get_cors_settings(config)
    
    # Create CORS instance with extracted settings
    cors = CORS(app,
                resources={r"/*": {"origins": cors_settings['origins']}},
                methods=cors_settings['methods'],
                allow_headers=cors_settings['allow_headers'],
                expose_headers=cors_settings['expose_headers'],
                supports_credentials=cors_settings['supports_credentials'],
                max_age=cors_settings['max_age'])
    
    # Log successful configuration
    logger.info(f"CORS configured. Allowed origins: {cors_settings['origins']}")
    
    return cors


def init_cors(app: Flask) -> None:
    """
    Initialize CORS for a Flask application.
    
    This is a simplified function intended for use in the application factory pattern.
    
    Args:
        app: The Flask application to initialize CORS for.
    """
    configure_cors(app)