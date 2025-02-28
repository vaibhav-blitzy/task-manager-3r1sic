"""
Initializes the task API package, importing and exposing API blueprints for task management operations to be registered with the main Flask application.
"""

# Import Flask Blueprint
from flask import Blueprint

# Internal imports
from .tasks import tasks_bp as _tasks_blueprint  # src/backend/services/task/api/tasks.py
from .comments import comments_blueprint as _comments_blueprint  # src/backend/services/task/api/comments.py
from .search import search_bp as _search_blueprint  # src/backend/services/task/api/search.py

# Define aliases for blueprints
tasks_blueprint = _tasks_blueprint
comments_blueprint = _comments_blueprint
search_blueprint = _search_blueprint

# Define __all__ to control what gets imported with a wildcard import
__all__ = ['tasks_blueprint', 'comments_blueprint', 'search_blueprint']