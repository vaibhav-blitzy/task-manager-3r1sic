# Third-party imports
from flask import Blueprint, request, jsonify, g  # flask v2.3.x

# Internal imports
from ..services.project_service import ProjectService  # Implements project management logic
from ..models.project import PROJECT_STATUS_CHOICES  # List of valid project status values
from src.backend.common.auth.decorators import token_required, permission_required, get_current_user  # Authentication and authorization decorators
from src.backend.common.schemas.pagination import create_pagination_params  # Pagination utilities
from src.backend.common.exceptions.api_exceptions import ValidationError, NotFoundError, AuthorizationError  # Exception classes for error handling
from src.backend.common.logging.logger import get_logger  # Logging functionality

# Create a Blueprint for project API routes
projects_bp = Blueprint('projects', __name__, url_prefix='/api/v1/projects')

# Initialize logger
logger = get_logger(__name__)

# Initialize project service
project_service = ProjectService()


@projects_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Error handler for validation errors"""
    logger.error(f"Validation error: {error}")
    return jsonify(error.to_dict()), 400


@projects_bp.errorhandler(NotFoundError)
def handle_not_found_error(error):
    """Error handler for resource not found errors"""
    logger.error(f"Not found error: {error}")
    return jsonify(error.to_dict()), 404


@projects_bp.errorhandler(AuthorizationError)
def handle_authorization_error(error):
    """Error handler for authorization errors"""
    logger.error(f"Authorization error: {error}")
    return jsonify(error.to_dict()), 403


@projects_bp.route('', methods=['POST'])
@token_required
def create_project():
    """Endpoint to create a new project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project data from request JSON
        project_data = request.get_json()

        # Call project_service.create_project with data and user_id
        project = project_service.create_project(project_data, user_id)

        # Return created project with 201 status code
        return jsonify(project), 201
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception("Unexpected error creating project")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('', methods=['GET'])
@token_required
def get_projects():
    """Endpoint to list all projects accessible to the user with optional filtering and pagination"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract filter parameters from query string (status, category, etc.)
        filters = request.args.to_dict()

        # Create pagination parameters using create_pagination_params from request args
        pagination_params = create_pagination_params(request.args)

        # Call project_service.list_projects with user_id, filters, and pagination params
        projects = project_service.list_projects(user_id, filters, pagination_params.page, pagination_params.per_page)

        # Return paginated projects with 200 status code
        return jsonify(projects), 200
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.exception("Unexpected error listing projects")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>', methods=['GET'])
@token_required
def get_project(project_id):
    """Endpoint to get details of a specific project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Call project_service.get_project with project_id and user_id
        project = project_service.get_project(project_id, user_id)

        # Return project details with 200 status code
        return jsonify(project), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error getting project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>', methods=['PUT'])
@token_required
def update_project(project_id):
    """Endpoint to update an existing project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Extract update data from request JSON
        update_data = request.get_json()

        # Call project_service.update_project with project_id, update_data, and user_id
        project = project_service.update_project(project_id, update_data, user_id)

        # Return updated project with 200 status code
        return jsonify(project), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error updating project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>', methods=['DELETE'])
@token_required
def delete_project(project_id):
    """Endpoint to delete (archive) a project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Call project_service.delete_project with project_id and user_id
        project_service.delete_project(project_id, user_id)

        # Return success message with 200 status code
        return jsonify({"message": "Project deleted successfully"}), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error deleting project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/search', methods=['GET'])
@token_required
def search_projects():
    """Endpoint to search projects by text query with filtering"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract search query from query parameters
        query = request.args.get('q', '')

        # Extract filter parameters from query string
        filters = request.args.to_dict()

        # Create pagination parameters using create_pagination_params
        pagination_params = create_pagination_params(request.args)

        # Call project_service.search_projects with query, user_id, filters, and pagination params
        projects = project_service.search_projects(query, user_id, filters, pagination_params.page, pagination_params.per_page)

        # Return search results with 200 status code
        return jsonify(projects), 200
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error searching projects with query: {query}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>/stats', methods=['GET'])
@token_required
def get_project_stats(project_id):
    """Endpoint to get statistics for a specific project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Call project_service.get_project_stats with project_id and user_id
        stats = project_service.get_project_stats(project_id, user_id)

        # Return project statistics with 200 status code
        return jsonify(stats), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error getting stats for project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>/tasklists', methods=['POST'])
@token_required
def add_task_list(project_id):
    """Endpoint to add a task list to a project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Extract task list data (name, description) from request JSON
        task_list_data = request.get_json()
        name = task_list_data.get('name')
        description = task_list_data.get('description', '')

        # Call project_service.add_task_list with project_id, user_id, name, and description
        task_list = project_service.add_task_list(project_id, user_id, name, description)

        # Return created task list with 201 status code
        return jsonify(task_list), 201
    except NotFoundError as e:
        return handle_not_found_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error adding task list to project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>/tasklists/<task_list_id>', methods=['PUT'])
@token_required
def update_task_list(project_id, task_list_id):
    """Endpoint to update a task list in a project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id and task_list_id from URL parameters
        # Extract update data from request JSON
        update_data = request.get_json()

        # Call project_service.update_task_list with project_id, user_id, task_list_id, and update data
        task_list = project_service.update_task_list(project_id, user_id, task_list_id, update_data)

        # Return updated task list with 200 status code
        return jsonify(task_list), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error updating task list {task_list_id} in project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>/tasklists/<task_list_id>', methods=['DELETE'])
@token_required
def delete_task_list(project_id, task_list_id):
    """Endpoint to delete a task list from a project"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id and task_list_id from URL parameters
        # Call project_service.remove_task_list with project_id, user_id, and task_list_id
        project_service.remove_task_list(project_id, user_id, task_list_id)

        # Return success message with 200 status code
        return jsonify({"message": "Task list deleted successfully"}), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error deleting task list {task_list_id} from project {project_id}")
        return jsonify({"message": "Internal server error"}), 500


@projects_bp.route('/<project_id>/settings', methods=['PUT'])
@token_required
def update_project_settings(project_id):
    """Endpoint to update project settings"""
    try:
        # Get current authenticated user from context
        user_id = get_current_user()['user_id']

        # Extract project_id from URL parameters
        # Extract settings data from request JSON
        settings_data = request.get_json()

        # Call project_service.update_settings with project_id, user_id, and settings data
        settings = project_service.update_settings(project_id, user_id, settings_data)

        # Return updated settings with 200 status code
        return jsonify(settings), 200
    except NotFoundError as e:
        return handle_not_found_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except AuthorizationError as e:
        return handle_authorization_error(e)
    except Exception as e:
        logger.exception(f"Unexpected error updating settings for project {project_id}")
        return jsonify({"message": "Internal server error"}), 500