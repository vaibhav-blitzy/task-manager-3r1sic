"""
Flask middleware for request ID generation and propagation.

This module provides middleware for Flask applications to ensure each request
has a unique identifier that can be used for distributed tracing, logging,
and debugging. The middleware generates a new request ID if none is provided,
makes it available throughout the request context, and adds it to response headers.
"""

from typing import Optional
from uuid import uuid4
from flask import Flask, request, g, Response
from ..logging.logger import get_logger

# Standard header for request ID propagation
REQUEST_ID_HEADER = 'X-Request-ID'

# Module logger
logger = get_logger(__name__)


def init_request_id_middleware(app: Flask) -> None:
    """
    Initialize request ID middleware for a Flask application to ensure each request
    has a unique identifier that is available throughout the request lifecycle and
    included in the response.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request() -> None:
        """Process incoming request and ensure it has a request ID."""
        # Check if request already has a request ID (e.g., from gateway or client)
        request_id = request.headers.get(REQUEST_ID_HEADER)
        
        # Generate a new UUID if no request ID is provided
        if not request_id:
            request_id = str(uuid4())
        
        # Store request ID in Flask g object for use during the request
        g.request_id = request_id
        
        # Log the request ID for tracing purposes
        logger.debug(f"Processing request with ID: {request_id}")
    
    @app.after_request
    def after_request(response: Response) -> Response:
        """Add request ID to response headers."""
        return set_request_id_in_response(response)


def get_request_id() -> Optional[str]:
    """
    Helper function to retrieve the current request ID from flask.g,
    making it available to other components.
    
    Returns:
        The current request ID or None if not in request context
    """
    try:
        return g.request_id if hasattr(g, 'request_id') else None
    except RuntimeError:
        # Handle case when outside of request context
        return None


def set_request_id_in_response(response: Response) -> Response:
    """
    Add the request ID to response headers to enable client-side tracking and debugging.
    
    Args:
        response: Flask response object to modify
        
    Returns:
        The modified response with request ID header
    """
    request_id = get_request_id()
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    return response