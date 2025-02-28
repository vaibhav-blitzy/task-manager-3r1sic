"""
Implements the search API endpoints for the Task Management System, allowing users to find tasks using advanced filtering, full-text search, and pagination capabilities.
"""
# Typing imports
import typing
# Flask imports
import flask  # ^2.0.0

# Internal imports
from ..services.search_service import search_tasks, count_tasks, build_search_query  # Service functions for task search
from ...common.auth.decorators import login_required, permission_required  # Authentication and authorization decorators
from ...common.schemas.pagination import PaginationParams, create_pagination_params  # Pagination schema and utilities
from ...common.exceptions.api_exceptions import ValidationError  # Custom exception for validation errors
from ...common.logging.logger import get_logger  # Logger for logging search API operations

# Initialize logger
logger = get_logger(__name__)

# Create Flask blueprint for search API
search_bp = flask.Blueprint('search', __name__)


@search_bp.route('/', methods=['GET'])
@login_required
@permission_required('tasks:search')
def search_tasks_endpoint() -> flask.Response:
    """
    API endpoint for searching tasks with multiple filtering options and pagination.

    Returns:
        flask.Response: JSON response with paginated search results
    """
    try:
        # Log the start of the search operation
        logger.debug("Starting task search operation")

        # Extract query parameters from request arguments
        query_params = flask.request.args

        # Create pagination parameters from request arguments
        pagination_params = create_pagination_params(query_params)

        # Extract search parameters using helper function
        search_params = extract_search_params()

        # Get the current user ID from the request context
        user_id = flask.g.user.get('user_id')

        # Call the search_tasks service function with the extracted parameters
        paginated_results = search_tasks(
            query=search_params,
            user_id=user_id,
            pagination=pagination_params
        )

        # Log the successful completion of the search operation
        logger.debug("Task search operation completed successfully")

        # Return the paginated results as a JSON response
        return flask.jsonify(paginated_results.to_dict()), 200

    except ValidationError as e:
        # Log validation errors
        logger.warning(f"Validation error during task search: {str(e)}")

        # Return a JSON error response with the validation error details
        return error_response(str(e), 400)

    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during task search: {str(e)}")

        # Return a JSON error response with a generic error message
        return error_response("An unexpected error occurred during task search", 500)


@search_bp.route('/count', methods=['GET'])
@login_required
@permission_required('tasks:search')
def count_tasks_endpoint() -> flask.Response:
    """
    API endpoint for counting tasks that match search criteria without retrieving full results.

    Returns:
        flask.Response: JSON response with task count
    """
    try:
        # Log the start of the task count operation
        logger.debug("Starting task count operation")

        # Extract query parameters from request arguments
        query_params = flask.request.args

        # Extract search parameters using helper function
        search_params = extract_search_params()

        # Get the current user ID from the request context
        user_id = flask.g.user.get('user_id')

        # Call the count_tasks service function with the extracted parameters
        task_count = count_tasks(
            query=search_params,
            user_id=user_id,
        )

        # Log the successful completion of the task count operation
        logger.debug("Task count operation completed successfully")

        # Return the task count as a JSON response
        return flask.jsonify({"count": task_count}), 200

    except ValidationError as e:
        # Log validation errors
        logger.warning(f"Validation error during task count: {str(e)}")

        # Return a JSON error response with the validation error details
        return error_response(str(e), 400)

    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during task count: {str(e)}")

        # Return a JSON error response with a generic error message
        return error_response("An unexpected error occurred during task count", 500)


def extract_search_params() -> dict:
    """
    Helper function to extract and normalize search parameters from request arguments.

    Returns:
        dict: Dictionary of normalized search parameters
    """
    # Initialize empty search parameters dictionary
    search_params = {}

    # Extract text search query parameter 'q' if present
    q = flask.request.args.get('q')
    if q:
        search_params['q'] = q

    # Extract status filter parameter 'status' if present
    status = flask.request.args.get('status')
    if status:
        search_params['status'] = status

    # Extract priority filter parameter 'priority' if present
    priority = flask.request.args.get('priority')
    if priority:
        search_params['priority'] = priority

    # Extract assignee filter parameter 'assignee_id' if present
    assignee_id = flask.request.args.get('assignee_id')
    if assignee_id:
        search_params['assignee_id'] = assignee_id

    # Extract project filter parameter 'project_id' if present
    project_id = flask.request.args.get('project_id')
    if project_id:
        search_params['project_id'] = project_id

    # Extract due date range parameter 'due_date' if present
    due_date = flask.request.args.get('due_date')
    if due_date:
        search_params['due_date'] = due_date

    # Extract tags filter parameter 'tags' if present
    tags = flask.request.args.get('tags')
    if tags:
        search_params['tags'] = tags

    # Return dictionary of extracted search parameters
    return search_params


def error_response(message: str, status_code: int) -> flask.Response:
    """
    Helper function to generate standardized error responses.

    Args:
        message: Error message
        status_code: HTTP status code

    Returns:
        flask.Response: JSON error response with message and status code
    """
    # Create error response dictionary with message and status
    error_response = {
        "message": message,
        "status": status_code
    }

    # Return JSON response with appropriate HTTP status code
    return flask.jsonify(error_response), status_code