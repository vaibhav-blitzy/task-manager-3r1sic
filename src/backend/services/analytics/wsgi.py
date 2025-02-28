import logging
import os

from flask import Flask

# Internal imports
from src.backend.services.analytics.app import create_app

# Set up module logger
logger = logging.getLogger(__name__)

# Determine environment from FLASK_ENV environment variable
env = os.environ.get('FLASK_ENV', 'default')

# Create the Flask app instance using the factory function
try:
    application = create_app()
    logger.info(f"Flask application created successfully in {env} environment")
except Exception as e:
    logger.critical(f"Failed to create Flask application: {str(e)}", exc_info=True)
    raise

# Export the Flask app instance as a WSGI callable
if __name__ == "__main__":
    # This block is only executed when the script is run directly (for development)
    # It's not used in production when the app is served by a WSGI server
    application.run(debug=True)