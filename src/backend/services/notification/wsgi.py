import logging
import os

from flask import Flask

# Internal imports
from app import create_app  # src/backend/services/notification/app.py

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

# Create Flask application instance
application = create_app(FLASK_ENV)

logger.info(f"Notification service running in {FLASK_ENV} environment")