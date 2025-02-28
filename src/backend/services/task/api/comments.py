"""
Flask REST API implementation for task comment management in the Task Management System.
Provides endpoints for creating, retrieving, updating, and deleting comments on tasks with proper authentication and authorization controls.
"""

# Standard library imports
import typing  # v3.5+

# Third-party imports
from flask import Blueprint, request, jsonify  # flask v2.3.x

# Internal imports
from ....common.auth.decorators import token_required, permission_required, get_current_user
from ....common.exceptions.api_exceptions import NotFoundError, ValidationError, AuthorizationError
from ....common.logging.logger import get_logger
from ..services.comment_service import create_comment, get_comment, get_comments_for_task, update_comment, delete_comment, get_comment_count
from ....common.auth.permissions import Permission

# Initialize logger
logger = get_logger(__name__)

# Create blueprint for comments API routes
comments_blueprint = Blueprint('comments', __name__)


@comments_blueprint.route('/tasks/<task_id>/comments', methods=['GET'])
@token_required
@permission_required(Permission.TASK_VIEW.value)
def handle_get_task_comments(task_id: str):
    """
    API endpoint to get comments for a specific task with pagination.

    Args:
        task_id: ID of the task to retrieve comments for

    Returns:
        flask.Response: JSON response with comments data
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Extract pagination parameters (limit, skip) from query string
        limit = request.args.get('limit', default=10, type=int)
        skip = request.args.get('skip', default=0, type=int)

        # Extract sorting parameters (sort_by, sort_order) from query string
        sort_by = request.args.get('sort_by', default='created_at', type=str)
        sort_order = request.args.get('sort_order', default='desc', type=str)

        # Call get_comments_for_task service function with parameters
        comments_data = get_comments_for_task(task_id=task_id, user=user, limit=limit, skip=skip, sort_by=sort_by, sort_order=sort_order)

        # Return JSON response with comments data and pagination metadata
        return jsonify(comments_data), 200

    except Exception as e:
        # Handle any exceptions and return appropriate error responses
        logger.exception(f"Error getting comments for task {task_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.route('/tasks/<task_id>/comments', methods=['POST'])
@token_required
@permission_required(Permission.TASK_COMMENT.value)
def handle_create_task_comment(task_id: str):
    """
    API endpoint to create a new comment on a task.

    Args:
        task_id: ID of the task to create a comment on

    Returns:
        flask.Response: JSON response with created comment data
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Extract comment content from request JSON body
        data = request.get_json()
        content = data.get('content')

        # Validate required fields (content must be present and not empty)
        if not content or not content.strip():
            raise ValidationError("Comment content is required", {"content": "Comment content is required"})

        # Call create_comment service function with task_id, user_id, and content
        comment = create_comment(task_id=task_id, user_id=user['id'], content=content)

        # Return JSON response with created comment and 201 Created status
        return jsonify(comment), 201

    except Exception as e:
        # Handle validation errors with 400 Bad Request response
        logger.exception(f"Error creating comment on task {task_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.route('/comments/<comment_id>', methods=['GET'])
@token_required
def handle_get_comment(comment_id: str):
    """
    API endpoint to get a specific comment by ID.

    Args:
        comment_id: ID of the comment to retrieve

    Returns:
        flask.Response: JSON response with comment data
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Call get_comment service function with comment_id and user_id
        comment = get_comment(comment_id=comment_id, user_id=user['id'])

        # Return JSON response with comment data
        return jsonify(comment), 200

    except Exception as e:
        # Handle NotFoundError with 404 Not Found response
        logger.exception(f"Error getting comment {comment_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.route('/comments/<comment_id>', methods=['PUT'])
@token_required
def handle_update_comment(comment_id: str):
    """
    API endpoint to update an existing comment.

    Args:
        comment_id: ID of the comment to update

    Returns:
        flask.Response: JSON response with updated comment data
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Extract new comment content from request JSON body
        data = request.get_json()
        new_content = data.get('content')

        # Validate required fields (content must be present and not empty)
        if not new_content or not new_content.strip():
            raise ValidationError("New content is required", {"content": "New content is required"})

        # Call update_comment service function with comment_id, user_id, and new_content
        comment = update_comment(comment_id=comment_id, user_id=user['id'], new_content=new_content)

        # Return JSON response with updated comment data
        return jsonify(comment), 200

    except Exception as e:
        # Handle NotFoundError with 404 Not Found response
        logger.exception(f"Error updating comment {comment_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.route('/comments/<comment_id>', methods=['DELETE'])
@token_required
def handle_delete_comment(comment_id: str):
    """
    API endpoint to delete a comment.

    Args:
        comment_id: ID of the comment to delete

    Returns:
        flask.Response: JSON response confirming deletion
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Call delete_comment service function with comment_id and user_id
        delete_comment(comment_id=comment_id, user_id=user['id'])

        # Return JSON response with success message and 200 OK status
        return jsonify({'message': 'Comment deleted successfully'}), 200

    except Exception as e:
        # Handle NotFoundError with 404 Not Found response
        logger.exception(f"Error deleting comment {comment_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.route('/tasks/<task_id>/comments/count', methods=['GET'])
@token_required
@permission_required(Permission.TASK_VIEW.value)
def handle_get_task_comment_count(task_id: str):
    """
    API endpoint to get the number of comments for a task.

    Args:
        task_id: ID of the task to get the comment count for

    Returns:
        flask.Response: JSON response with comment count
    """
    try:
        # Get the current authenticated user from request context
        user = get_current_user()

        # Call get_comment_count service function with task_id and user
        comment_count = get_comment_count(task_id=task_id, user=user)

        # Return JSON response with comment count data
        return jsonify(comment_count), 200

    except Exception as e:
        # Handle NotFoundError with 404 Not Found response
        logger.exception(f"Error getting comment count for task {task_id}: {str(e)}")
        return handle_api_error(e)


@comments_blueprint.errorhandler(Exception)
def handle_api_error(e):
    """
    Error handler for API exceptions.

    Args:
        e: The exception that was raised

    Returns:
        flask.Response: JSON error response with appropriate status code
    """
    # Log the exception details for debugging
    logger.exception(f"API error occurred: {str(e)}")

    # Check exception type to determine response format
    if isinstance(e, ValidationError):
        # For ValidationError, return 400 Bad Request with validation details
        return jsonify(e.to_dict()), 400
    elif isinstance(e, NotFoundError):
        # For NotFoundError, return 404 Not Found with resource information
        return jsonify(e.to_dict()), 404
    elif isinstance(e, AuthorizationError):
        # For AuthorizationError, return 403 Forbidden with permission information
        return jsonify(e.to_dict()), 403
    else:
        # For other exceptions, return 500 Internal Server Error with generic message
        return jsonify({'status': 500, 'code': 'server_error', 'message': 'Internal server error'}), 500