"""
API Gateway service package for the Task Management System.

This package implements a centralized API Gateway that routes client requests to 
appropriate backend microservices. It serves as the single entry point for all
client applications to interact with the Task Management System's backend services.

The API Gateway handles:
- Request routing to appropriate microservices
- Authentication and authorization
- Rate limiting and traffic management
- Request/response transformation
- Error handling and logging
- Health checks and monitoring

Exports:
    __version__: Package version string.
    create_app: Flask application factory function.
    health_blueprint: Health check endpoints blueprint.
    proxy_blueprint: Proxy routing endpoints blueprint.
"""

# Package version
__version__ = '0.1.0'

# Import application factory function
from .app import create_app

# Import route blueprints
from .routes.health import health_bp as health_blueprint
from .routes.proxy import proxy_bp as proxy_blueprint

# Define public API
__all__ = ['__version__', 'create_app', 'health_blueprint', 'proxy_blueprint']