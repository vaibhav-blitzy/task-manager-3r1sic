"""
WSGI entry point for the API Gateway service.

This module creates and exposes the Flask application instance for production
deployment with WSGI servers like Gunicorn.
"""

import os
from app import create_app

# Determine the environment (default to 'production')
environment = os.getenv('FLASK_ENV', 'production')

# Create the Flask application instance
application = create_app()

# Run the development server if executed directly
if __name__ == '__main__':
    # Enable debug mode in development
    debug_mode = environment == 'development'
    application.run(host='0.0.0.0', port=8000, debug=debug_mode)