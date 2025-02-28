"""
Initialization file for the Task Management microservice that exports key models, services, and API blueprints while defining the service version. This file serves as the package entry point and exposes the public API for the task service.
"""

# Import Flask application factory function
from .app import create_app  # Import Flask application factory function

# Import Task model for external use
from .models.task import Task  # Import the Task model for external use

# Import Comment model for external use
from .models.comment import Comment  # Import the Comment model for external use

# Import core task management functions
from .services.task_service import (  # Import core task management functions
    create_task,
    get_task,
    update_task,
    delete_task,
    assign_task,
    update_task_status,
    get_tasks_by_user,
    get_tasks_by_project_id,
    get_tasks_due_soon,
    get_overdue_tasks,
)

# Import comment management functions
from .services.comment_service import (  # Import comment management functions
    create_comment,
    get_comment,
    get_comments_for_task,
    update_comment,
    delete_comment,
)

# Import task search functionality
from .services.search_service import search_tasks  # Import task search functionality

# Import tasks API blueprint for Flask app registration
from .api.tasks import tasks_blueprint  # Import tasks API blueprint for Flask app registration

# Import comments API blueprint for Flask app registration
from .api.comments import comments_blueprint  # Import comments API blueprint for Flask app registration

# Import search API blueprint for Flask app registration
from .api.search import search_blueprint  # Import search API blueprint for Flask app registration

# Service version for version tracking and compatibility checks
__version__ = "1.0.0"  # Export service version for version tracking and compatibility checks