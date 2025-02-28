"""
WSGI entry point for the Task Management Service that initializes the Flask application instance
for production deployment with WSGI servers like Gunicorn or uWSGI.
"""
import os  # standard library

from .app import create_app  # Import the application factory function

# Determine the application environment from the environment variable
environment = os.getenv('FLASK_ENV', 'production')

# Create the Flask application instance using the factory function
app = create_app(environment)

# Export the configured Flask application instance for use by WSGI servers
# such as Gunicorn or uWSGI.
# WSGI servers use this 'app' object to serve the Flask application.

def main():
    """
    Development server entry point when the script is executed directly
    """
    # Check if the script is being run directly (__name__ == '__main__')
    if __name__ == '__main__':
        # If running directly, start the Flask development server
        # Configure the server to run on host '0.0.0.0' (all interfaces)
        # Use the port defined in the application configuration
        # Enable debug mode for development environment
        app.run(host='0.0.0.0', port=5000, debug=True)