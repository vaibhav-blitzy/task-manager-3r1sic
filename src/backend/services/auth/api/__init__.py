# flask v2.3.x
from flask import Blueprint

# Internal imports for authentication API routes
from .auth import auth_bp  # Import the authentication API endpoints
from .users import users_bp  # Import the user management API endpoints
from .roles import roles_bp  # Import the role management API endpoints


def init_app(app):
    """Function to register all authentication API blueprints with a Flask application"""
    # Validate that app is a valid Flask application
    if not hasattr(app, 'register_blueprint'):
        raise ValueError("Invalid Flask application instance provided.")

    # Register the auth_bp with the Flask app with URL prefix '/api/v1/auth'
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    # Register the users_bp with the Flask app with URL prefix '/api/v1/users'
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')

    # Register the roles_bp with the Flask app with URL prefix '/api/v1/roles'
    app.register_blueprint(roles_bp, url_prefix='/api/v1/roles')

    # Return None
    return None