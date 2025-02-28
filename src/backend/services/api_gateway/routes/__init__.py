"""
Route blueprints initialization for the API Gateway service.

This module imports and exports route blueprints from different modules,
making them available for registration in the main application. It serves
as the central collection point for all API Gateway routing components.
"""

# Import blueprints from route modules
from .health import health_bp as health_blueprint
from .proxy import proxy_bp as proxy_blueprint

# Create a dictionary of all blueprints for convenient registration
blueprints = {
    'health': health_blueprint,
    'proxy': proxy_blueprint
}

# Export individual blueprints and the blueprints dictionary
__all__ = ['health_blueprint', 'proxy_blueprint', 'blueprints']