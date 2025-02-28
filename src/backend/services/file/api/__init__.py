"""
Initialization file for the File Service API package that imports and exports file and attachment API blueprints for registration with the Flask application. Acts as a central entry point for all API routes related to file management.
"""
# Third-party imports - Check versions in the comments
from flask import Flask

# Internal imports
from .files import file_blueprint  # Import the files API Flask Blueprint
from .attachments import attachment_blueprint  # Import the attachments API Flask Blueprint
from ....common.logging.logger import get_logger  # Configure logging for the API package

# Initialize logger
logger = get_logger(__name__)

# Export the blueprints for registration with the Flask app
__all__ = ['file_blueprint', 'attachment_blueprint']