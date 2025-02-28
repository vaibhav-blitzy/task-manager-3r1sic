# flask==2.3.x
from flask import Blueprint

# Internal imports
from .dashboards import dashboard_blueprint  # Import the Blueprint for dashboard-related endpoints
from .metrics import metrics_blueprint  # Import the Blueprint for metrics-related endpoints
from .reports import reports_blueprint  # Import the Blueprint for report-related endpoints
from common.auth.decorators import require_auth, has_permission  # Authentication decorator for securing API endpoints
from common.exceptions.error_handlers import register_error_handlers  # Register error handlers for the analytics API

# Blueprint for the entire analytics API
analytics_blueprint = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

def init_app(app):
    """
    Initialize the analytics API with the Flask application

    Args:
        app: Flask application instance
    """
    # Register the dashboards blueprint with the analytics blueprint
    analytics_blueprint.register_blueprint(dashboard_blueprint)

    # Register the metrics blueprint with the analytics blueprint
    analytics_blueprint.register_blueprint(metrics_blueprint)

    # Register the reports blueprint with the analytics blueprint
    analytics_blueprint.register_blueprint(reports_blueprint)

    # Register the analytics blueprint with the Flask application
    app.register_blueprint(analytics_blueprint)

    # Apply any necessary middleware or configuration
    # (Currently, there are no specific middleware or configurations applied here)

    # Register error handlers for the analytics API routes
    register_error_handlers(app)
    print("Analytics API registered")

# Define what to export from the module
__all__ = [
    'analytics_blueprint',  # Combined blueprint for all analytics API endpoints
    'init_app'  # Function to initialize the analytics API with the Flask application
]