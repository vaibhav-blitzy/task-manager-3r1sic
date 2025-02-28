# Standard library imports
import logging

# Internal imports
from .app import init_app  # Import the Flask application instance

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize the Flask application
application = init_app()

# Log WSGI entry point initialization
logger.info("WSGI entry point initialized")

# Expose the Flask application instance to the WSGI server
# The 'application' variable is required by WSGI servers like Gunicorn
# to route incoming requests to the Flask app.