# Initializes the project API package, importing and exposing API blueprints for project and member management operations to be registered with the main Flask application.

from flask import Blueprint

# Internal imports
from .projects import projects_bp  # Imports the projects API Blueprint for project CRUD operations
from .members import member_blueprint  # Imports the members API Blueprint for project membership operations

# Alias for the imported projects blueprint
projects_blueprint = projects_bp
# Alias for the imported members blueprint
members_blueprint = member_blueprint

# List of exported items
__all__ = ['projects_blueprint', 'members_blueprint']