"""
Implements RESTful API endpoints for task management in the Task Management System,
including creation, retrieval, updating, and deletion of tasks, as well as specialized
task operations such as assignment, status updates, and attachment management.
"""

# Standard imports
import typing
from typing import Dict, List, Any, Optional

# Third-party imports
from flask import Blueprint, request, jsonify, g  # flask==2.3.x
from datetime import datetime  # standard library

# Internal imports
from ..services.task_service import TaskService  # Service layer for task operations
from ..models.task import TASK_STATUS_CHOICES, TASK_PRIORITY_CHOICES  # Valid status and priority values for validation
from ....common.auth.decorators import token_required, permission_required, roles_required  # Authentication and authorization decorators
from ....common.exceptions.api_exceptions import ValidationError, NotFoundError, AuthorizationError  # Exception handling for API errors
from ....common.schemas.pagination import PaginationParams, create_pagination_params  # Pagination utilities for list endpoints
from ....common.logging.logger import get_logger  # Logging for API operations

# Initialize logger
logger = get_logger(__name__)

# Create Flask blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/v1/tasks')

# Initialize TaskService
task_service = TaskService()


@tasks_bp.route('/', methods=['GET'])
@token_required
def get_tasks():
    """Route handler for retrieving tasks with filtering and pagination"""
    try:
        # Extract pagination parameters from request args using create_pagination_params
        pagination_params = create_pagination_params(request.args)

        # Extract filter parameters from request args (status, priority, due date, etc.)
        filters = request.args.to_dict()

        # Extract search query parameter if present
        search_query = filters.pop('q', None)

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # If search query exists, call task_service.search_tasks
        if search_query:
            tasks_data = task_service.search_tasks(
                search_params={'q': search_query, **filters},
                user_id=user_id,
                pagination=pagination_params
            )
        # Otherwise, call task_service.get_user_tasks with filters and pagination
        else:
            tasks_data = task_service.get_user_tasks(
                user_id=user_id,
                filters=filters,
                pagination=pagination_params
            )

        # Return JSON response with tasks list and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.exception(f"Error retrieving tasks: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/', methods=['POST'])
@token_required
@permission_required('create_task')
def create_task():
    """Route handler for creating a new task"""
    try:
        # Extract task data from request JSON
        task_data = request.get_json()

        # Validate required fields (title)
        if not task_data or 'title' not in task_data:
            return jsonify({"message": "Title is required"}), 400

        # Validate status against TASK_STATUS_CHOICES if provided
        if 'status' in task_data and task_data['status'] not in TASK_STATUS_CHOICES:
            return jsonify({"message": "Invalid status value"}), 400

        # Validate priority against TASK_PRIORITY_CHOICES if provided
        if 'priority' in task_data and task_data['priority'] not in TASK_PRIORITY_CHOICES:
            return jsonify({"message": "Invalid priority value"}), 400

        # Parse and validate due_date if provided
        if 'due_date' in task_data and task_data['due_date']:
            try:
                datetime.fromisoformat(task_data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"message": "Invalid due_date format"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.create_task with data and user_id
        created_task = task_service.create_task(task_data, user_id)

        # Return JSON response with created task and 201 status code
        return jsonify(created_task), 201

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error creating task: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error creating task: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """Route handler for retrieving a specific task by ID"""
    try:
        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.get_task with task_id and user_id
        task = task_service.get_task(task_id, user_id)

        # Return JSON response with task data
        return jsonify(task), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error retrieving task: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error retrieving task: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Route handler for updating a task"""
    try:
        # Extract task data from request JSON
        update_data = request.get_json()

        # Validate fields against allowed values (status, priority)
        if 'status' in update_data and update_data['status'] not in TASK_STATUS_CHOICES:
            return jsonify({"message": "Invalid status value"}), 400
        if 'priority' in update_data and update_data['priority'] not in TASK_PRIORITY_CHOICES:
            return jsonify({"message": "Invalid priority value"}), 400

        # Parse and validate due_date if provided
        if 'due_date' in update_data and update_data['due_date']:
            try:
                datetime.fromisoformat(update_data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"message": "Invalid due_date format"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.update_task with task_id, data, and user_id
        updated_task = task_service.update_task(task_id, update_data, user_id)

        # Return JSON response with updated task data
        return jsonify(updated_task), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error updating task: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error updating task: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error updating task: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """Route handler for deleting a task"""
    try:
        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.delete_task with task_id and user_id
        task_service.delete_task(task_id, user_id)

        # Return JSON response with success message
        return jsonify({"message": "Task deleted successfully"}), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error deleting task: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error deleting task: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/status', methods=['PATCH'])
@token_required
def update_task_status(task_id):
    """Route handler for updating a task's status"""
    try:
        # Extract status data from request JSON
        status_data = request.get_json()

        # Validate status against TASK_STATUS_CHOICES
        if not status_data or 'status' not in status_data:
            return jsonify({"message": "Status is required"}), 400
        if status_data['status'] not in TASK_STATUS_CHOICES:
            return jsonify({"message": "Invalid status value"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.update_task_status with task_id, status, and user_id
        updated_task = task_service.update_task_status(task_id, status_data['status'], user_id)

        # Return JSON response with updated task data
        return jsonify(updated_task), 200

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error updating task status: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error updating task status: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error updating task status: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/assign', methods=['PATCH'])
@token_required
def assign_task(task_id):
    """Route handler for assigning a task to a user"""
    try:
        # Extract assignee_id from request JSON
        assign_data = request.get_json()

        # Validate assignee_id is provided
        if not assign_data or 'assignee_id' not in assign_data:
            return jsonify({"message": "assignee_id is required"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.assign_task with task_id, assignee_id, and user_id
        updated_task = task_service.assign_task(task_id, assign_data['assignee_id'], user_id)

        # Return JSON response with updated task data
        return jsonify(updated_task), 200

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error assigning task: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error assigning task: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error assigning task: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/assigned', methods=['GET'])
@token_required
def get_assigned_tasks():
    """Route handler for retrieving tasks assigned to the current user"""
    try:
        # Extract pagination parameters from request args
        pagination_params = create_pagination_params(request.args)

        # Extract status filter from request args
        status = request.args.get('status')

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.get_user_tasks with assignee filter, status, and pagination
        tasks_data = task_service.get_user_tasks(
            user_id=user_id,
            filters={'assignee_id': user_id, 'status': status},
            pagination=pagination_params
        )

        # Return JSON response with tasks list and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.exception(f"Error retrieving assigned tasks: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/project/<string:project_id>', methods=['GET'])
@token_required
def get_tasks_by_project(project_id):
    """Route handler for retrieving tasks within a project"""
    try:
        # Extract pagination parameters from request args
        pagination_params = create_pagination_params(request.args)

        # Extract filter parameters (status, priority, etc.)
        filters = request.args.to_dict()

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.get_tasks_by_project with project_id, filters, and pagination
        tasks_data = task_service.get_user_tasks(
            user_id=user_id,
            filters={'project_id': project_id, **filters},
            pagination=pagination_params
        )

        # Return JSON response with tasks list and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Project not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error retrieving tasks by project: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error retrieving tasks by project: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/due-soon', methods=['GET'])
@token_required
def get_tasks_due_soon():
    """Route handler for retrieving tasks due within specified hours"""
    try:
        # Extract pagination parameters from request args
        pagination_params = create_pagination_params(request.args)

        # Extract hours parameter with default value (24)
        hours = int(request.args.get('hours', 24))

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.get_tasks_due_soon with user_id, hours, and pagination
        tasks_data = task_service.get_user_tasks(
            user_id=user_id,
            filters={'due_soon': hours},
            pagination=pagination_params
        )

        # Return JSON response with tasks list and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.exception(f"Error retrieving tasks due soon: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/overdue', methods=['GET'])
@token_required
def get_overdue_tasks():
    """Route handler for retrieving overdue tasks"""
    try:
        # Extract pagination parameters from request args
        pagination_params = create_pagination_params(request.args)

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.get_overdue_tasks with user_id and pagination
         tasks_data = task_service.get_user_tasks(
            user_id=user_id,
            filters={'overdue': True},
            pagination=pagination_params
        )

        # Return JSON response with tasks list and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except Exception as e:
        # Handle exceptions and return appropriate error responses
        logger.exception(f"Error retrieving overdue tasks: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/subtasks', methods=['POST'])
@token_required
def add_subtask(task_id):
    """Route handler for adding a subtask to a task"""
    try:
        # Extract subtask data from request JSON (title, assignee_id)
        subtask_data = request.get_json()

        # Validate title is provided
        if not subtask_data or 'title' not in subtask_data:
            return jsonify({"message": "Title is required"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.add_task_subtask with task_id, title, assignee_id, and user_id
        new_subtask = task_service.add_task_subtask(
            task_id=task_id,
            title=subtask_data['title'],
            assignee_id=subtask_data.get('assignee_id'),
            user_id=user_id
        )

        # Return JSON response with subtask data and 201 status code
        return jsonify(new_subtask), 201

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error adding subtask: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error adding subtask: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error adding subtask: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/subtasks/<string:subtask_id>', methods=['PUT'])
@token_required
def update_subtask(task_id, subtask_id):
    """Route handler for updating a subtask"""
    try:
        # Extract update data from request JSON
        update_data = request.get_json()

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.update_task_subtask with task_id, subtask_id, update_data, and user_id
        updated_subtask = task_service.update_task_subtask(
            task_id=task_id,
            subtask_id=subtask_id,
            update_data=update_data,
            user_id=user_id
        )

        # Return JSON response with updated subtask data
        return jsonify(updated_subtask), 200

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error updating subtask: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task or subtask not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error updating subtask: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error updating subtask: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/subtasks/<string:subtask_id>', methods=['DELETE'])
@token_required
def delete_subtask(task_id, subtask_id):
    """Route handler for deleting a subtask"""
    try:
        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.delete_task_subtask with task_id, subtask_id, and user_id
        task_service.delete_task_subtask(
            task_id=task_id,
            subtask_id=subtask_id,
            user_id=user_id
        )

        # Return JSON response with success message
        return jsonify({"message": "Subtask deleted successfully"}), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task or subtask not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error deleting subtask: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error deleting subtask: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/attachments', methods=['POST'])
@token_required
def add_attachment(task_id):
    """Route handler for adding a file attachment to a task"""
    try:
        # Extract attachment data from request JSON (file_id, file_name)
        attachment_data = request.get_json()

        # Validate required fields (file_id, file_name)
        if not attachment_data or 'file_id' not in attachment_data or 'file_name' not in attachment_data:
            return jsonify({"message": "file_id and file_name are required"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.add_task_attachment with task_id, file_id, file_name, and user_id
        attachment = task_service.add_task_attachment(
            task_id=task_id,
            file_id=attachment_data['file_id'],
            file_name=attachment_data['file_name'],
            user_id=user_id
        )

        # Return JSON response with attachment data and 201 status code
        return jsonify(attachment), 201

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error adding attachment: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error adding attachment: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error adding attachment: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/attachments/<string:file_id>', methods=['DELETE'])
@token_required
def remove_attachment(task_id, file_id):
    """Route handler for removing a file attachment from a task"""
    try:
        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.remove_task_attachment with task_id, file_id, and user_id
        task_service.remove_task_attachment(
            task_id=task_id,
            file_id=file_id,
            user_id=user_id
        )

        # Return JSON response with success message
        return jsonify({"message": "Attachment removed successfully"}), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task or attachment not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error removing attachment: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error removing attachment: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/search', methods=['GET'])
@token_required
def search_tasks():
    """Route handler for searching tasks with advanced filtering"""
    try:
        # Extract pagination parameters from request args
        pagination_params = create_pagination_params(request.args)

        # Extract search parameters from request args (query, filters)
        search_params = request.args.to_dict()

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Build search_params dictionary from request parameters
        # Call task_service.search_tasks with search_params, user_id, and pagination
        tasks_data = task_service.search_tasks(
            search_params=search_params,
            user_id=user_id,
            pagination=pagination_params
        )

        # Return JSON response with search results and pagination metadata
        return jsonify(tasks_data.to_dict()), 200

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error searching tasks: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error searching tasks: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/dependencies', methods=['POST'])
@token_required
def add_task_dependency(task_id):
    """Route handler for adding a dependency between tasks"""
    try:
        # Extract dependency data from request JSON (dependency_task_id, dependency_type)
        dependency_data = request.get_json()

        # Validate required fields and dependency_type value
        if not dependency_data or 'dependency_task_id' not in dependency_data or 'dependency_type' not in dependency_data:
            return jsonify({"message": "dependency_task_id and dependency_type are required"}), 400
        if dependency_data['dependency_type'] not in ['blocks', 'blocked_by']:
            return jsonify({"message": "Invalid dependency_type value"}), 400

        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.add_task_dependency with task_id, dependency_task_id, dependency_type, and user_id
        updated_task = task_service.add_task_dependency(
            task_id=task_id,
            dependency_task_id=dependency_data['dependency_task_id'],
            dependency_type=dependency_data['dependency_type'],
            user_id=user_id
        )

        # Return JSON response with updated task data
        return jsonify(updated_task), 200

    except ValidationError as e:
        # Handle ValidationError and return 400 response
        logger.warning(f"Validation error adding task dependency: {e}")
        return jsonify({"message": str(e), "errors": e.errors}), 400
    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error adding task dependency: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error adding task dependency: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.route('/<string:task_id>/dependencies/<string:dependency_id>', methods=['DELETE'])
@token_required
def remove_task_dependency(task_id, dependency_id):
    """Route handler for removing a dependency between tasks"""
    try:
        # Get user_id from authenticated user (g.user['id'])
        user_id = g.user['id']

        # Call task_service.remove_task_dependency with task_id, dependency_id, and user_id
        task_service.remove_task_dependency(
            task_id=task_id,
            dependency_task_id=dependency_id,
            user_id=user_id
        )

        # Return JSON response with success message
        return jsonify({"message": "Task dependency removed successfully"}), 200

    except NotFoundError as e:
        # Handle NotFoundError and return 404 response
        logger.warning(f"Task or dependency not found: {e}")
        return jsonify({"message": str(e)}), 404
    except AuthorizationError as e:
        # Handle AuthorizationError and return 403 response
        logger.warning(f"Authorization error removing task dependency: {e}")
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Handle other exceptions and return appropriate error responses
        logger.exception(f"Error removing task dependency: {e}")
        return jsonify({"message": "Internal server error"}), 500


@tasks_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Register handler for ValidationError returning 400 response"""
    logger.warning(f"Validation error: {e}")
    return jsonify({"message": str(e), "errors": e.errors}), 400


@tasks_bp.errorhandler(NotFoundError)
def handle_not_found_error(e):
    """Register handler for NotFoundError returning 404 response"""
    logger.warning(f"Resource not found: {e}")
    return jsonify({"message": str(e)}), 404


@tasks_bp.errorhandler(AuthorizationError)
def handle_authorization_error(e):
    """Register handler for AuthorizationError returning 403 response"""
    logger.warning(f"Authorization error: {e}")
    return jsonify({"message": str(e)}), 403


@tasks_bp.errorhandler(Exception)
def handle_generic_error(e):
    """Register handler for generic Exception returning 500 response"""
    logger.exception(f"Internal server error: {e}")
    return jsonify({"message": "Internal server error"}), 500