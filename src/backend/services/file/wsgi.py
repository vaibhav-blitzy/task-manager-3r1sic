"""
WSGI entry point for the File Service, used by WSGI servers like Gunicorn to interact with the Flask application
"""
# Internal imports
from app import app # Import the Flask application instance to be used as the WSGI application

# Expose the Flask application instance to WSGI servers
application = app