"""
Implements REST API endpoints for dashboard management, including creating, retrieving,
updating, and deleting dashboards, as well as managing dashboard widgets and data retrieval.
"""
import typing
from typing import Dict, List, Optional, Any, Union

from flask import Blueprint, request, jsonify, g  # version: ^2.0.0

# Internal imports
from src.backend.common.auth.decorators import token_required, roles_required, permission_required, get_current_user
from src.backend.common.exceptions.api_exceptions import BadRequestError, NotFoundError, ConflictError
from src.backend.common.schemas.pagination import PaginationParams, create_pagination_params
from src.backend.services.analytics.services.dashboard_service import DashboardService, create_system_dashboard_templates
from src.backend.common.logging.logger import get_logger

# Blueprint for dashboard routes
dashboard_blueprint = Blueprint('dashboards', __name__, url_prefix='/api/dashboards')

# Dashboard service instance
dashboard_service = DashboardService()

# Logger instance
logger = get_logger(__name__)


@dashboard_blueprint.route('', methods=['GET'])
@token_required
def list_dashboards():
    """
    Get a paginated list of dashboards with optional filtering.

    Returns:
        JSON: Paginated list of dashboards with metadata
    """
    # Extract pagination parameters from request args
    pagination_params = create_pagination_params(request.args)

    # Extract optional filter parameters (type, project_id)
    filters = {}
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('project_id'):
        filters['project_id'] = request.args.get('project_id')
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    # Add user_id to filters to only return dashboards owned by or shared with the user
    user = get_current_user()
    if user and user.get('id'):
        filters['user_id'] = user.get('id')

    # Call dashboard_service.get_dashboards with filters and pagination
    result = dashboard_service.get_dashboards(
        filters=filters,
        page=pagination_params.page,
        page_size=pagination_params.per_page
    )

    # Return JSON response with paginated dashboard list
    return jsonify(result)


@dashboard_blueprint.route('', methods=['POST'])
@token_required
def create_dashboard():
    """
    Create a new dashboard.

    Returns:
        JSON: Created dashboard data with ID
    """
    # Extract dashboard data from request JSON
    dashboard_data = request.get_json()

    # Validate required fields (name, type)
    if not dashboard_data or 'name' not in dashboard_data:
        logger.warning("Dashboard name is required")
        raise BadRequestError(message="Dashboard name is required")

    # Call dashboard_service.create_dashboard with data and current user
    user = get_current_user()
    dashboard = dashboard_service.create_dashboard(dashboard_data, user)

    # Return JSON response with created dashboard ID and 201 status
    return jsonify({'id': dashboard.get_id_str()}), 201


@dashboard_blueprint.route('/<dashboard_id>', methods=['GET'])
@token_required
def get_dashboard(dashboard_id: str):
    """
    Get a single dashboard by ID.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Dashboard details
    """
    try:
        # Call dashboard_service.get_dashboard_by_id with dashboard_id and current user
        dashboard = dashboard_service.get_dashboard_by_id(dashboard_id)

        # Return JSON response with dashboard data
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise


@dashboard_blueprint.route('/<dashboard_id>', methods=['PUT'])
@token_required
def update_dashboard(dashboard_id: str):
    """
    Update an existing dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Updated dashboard data
    """
    # Extract dashboard data from request JSON
    dashboard_data = request.get_json()

    try:
        # Call dashboard_service.update_dashboard with dashboard_id, data and current user
        user = get_current_user()
        dashboard = dashboard_service.update_dashboard(dashboard_id, dashboard_data, user)

        # Return JSON response with updated dashboard data
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise


@dashboard_blueprint.route('/<dashboard_id>', methods=['DELETE'])
@token_required
def delete_dashboard(dashboard_id: str):
    """
    Delete a dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Deletion confirmation
    """
    try:
        # Call dashboard_service.delete_dashboard with dashboard_id and current user
        user = get_current_user()
        dashboard_service.delete_dashboard(dashboard_id, user)

        # Return JSON success response
        return jsonify({'message': 'Dashboard deleted successfully'})

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise


@dashboard_blueprint.route('/<dashboard_id>/data', methods=['GET'])
@token_required
def get_dashboard_data(dashboard_id: str):
    """
    Get data for all widgets in a dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Dashboard widget data
    """
    # Extract refresh parameter from query string (default: False)
    refresh = request.args.get('refresh', default=False, type=bool)

    try:
        # Get dashboard by ID using dashboard_service.get_dashboard_by_id
        dashboard = dashboard_service.get_dashboard_by_id(dashboard_id)

        # Get dashboard data using dashboard_service.get_dashboard_data
        widget_data = dashboard_service.get_dashboard_data(dashboard)

        # Return JSON response with widget data
        return jsonify(widget_data)

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise


@dashboard_blueprint.route('/<dashboard_id>/widgets', methods=['POST'])
@token_required
def add_dashboard_widget(dashboard_id: str):
    """
    Add a new widget to a dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Updated dashboard with new widget
    """
    # Extract widget data from request JSON
    widget_data = request.get_json()

    # Validate required widget fields (type, title, config)
    if not widget_data or 'type' not in widget_data:
        logger.warning("Widget type is required")
        raise BadRequestError(message="Widget type is required")

    try:
        # Call dashboard_service.add_widget with dashboard_id, widget data and current user
        user = get_current_user()
        dashboard = dashboard_service.add_widget(dashboard_id, widget_data, user)

        # Return JSON response with updated dashboard
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if widget data is invalid
        logger.warning(f"Invalid widget data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/<dashboard_id>/widgets/<widget_id>', methods=['PUT'])
@token_required
def update_dashboard_widget(dashboard_id: str, widget_id: str):
    """
    Update an existing widget in a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        widget_id: ID of the widget to update

    Returns:
        JSON: Updated dashboard with modified widget
    """
    # Extract widget data from request JSON
    widget_data = request.get_json()

    try:
        # Call dashboard_service.update_widget with dashboard_id, widget_id, data and current user
        user = get_current_user()
        dashboard = dashboard_service.update_widget(dashboard_id, widget_id, widget_data, user)

        # Return JSON response with updated dashboard
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard or widget doesn't exist
        logger.warning(f"Dashboard or widget not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if widget data is invalid
        logger.warning(f"Invalid widget data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/<dashboard_id>/widgets/<widget_id>', methods=['DELETE'])
@token_required
def delete_dashboard_widget(dashboard_id: str, widget_id: str):
    """
    Remove a widget from a dashboard.

    Args:
        dashboard_id: ID of the dashboard
        widget_id: ID of the widget to remove

    Returns:
        JSON: Updated dashboard without the widget
    """
    try:
        # Call dashboard_service.remove_widget with dashboard_id, widget_id and current user
        user = get_current_user()
        dashboard = dashboard_service.remove_widget(dashboard_id, widget_id, user)

        # Return JSON success response
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard or widget doesn't exist
        logger.warning(f"Dashboard or widget not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if widget data is invalid
        logger.warning(f"Invalid widget data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/<dashboard_id>/layout', methods=['PUT'])
@token_required
def update_dashboard_layout(dashboard_id: str):
    """
    Update the layout configuration of a dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Updated dashboard with new layout
    """
    # Extract layout data from request JSON
    layout_data = request.get_json()

    try:
        # Call dashboard_service.update_layout with dashboard_id, layout data and current user
        user = get_current_user()
        dashboard = dashboard_service.update_layout(dashboard_id, layout_data, user)

        # Return JSON response with updated dashboard
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if layout data is invalid
        logger.warning(f"Invalid layout data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/<dashboard_id>/scope', methods=['PUT'])
@token_required
def update_dashboard_scope(dashboard_id: str):
    """
    Update the data scope of a dashboard (projects, users, date range).

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Updated dashboard with new scope
    """
    # Extract scope data from request JSON
    scope_data = request.get_json()

    try:
        # Call dashboard_service.update_dashboard_scope with dashboard_id, scope data and current user
        user = get_current_user()
        dashboard = dashboard_service.update_dashboard_scope(dashboard_id, scope_data, user)

        # Return JSON response with updated dashboard
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if scope data is invalid
        logger.warning(f"Invalid scope data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/<dashboard_id>/sharing', methods=['PUT'])
@token_required
def update_dashboard_sharing(dashboard_id: str):
    """
    Update the sharing settings of a dashboard.

    Args:
        dashboard_id: ID of the dashboard

    Returns:
        JSON: Updated dashboard with new sharing settings
    """
    # Extract sharing data from request JSON
    sharing_data = request.get_json()

    try:
        # Call dashboard_service.update_sharing with dashboard_id, sharing data and current user
        user = get_current_user()
        dashboard = dashboard_service.update_sharing(dashboard_id, sharing_data, user)

        # Return JSON response with updated dashboard
        return jsonify(dashboard.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if dashboard doesn't exist
        logger.warning(f"Dashboard not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if sharing data is invalid
        logger.warning(f"Invalid sharing data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/templates', methods=['GET'])
@token_required
def list_dashboard_templates():
    """
    Get a paginated list of dashboard templates.

    Returns:
        JSON: Paginated list of dashboard templates
    """
    # Extract pagination parameters from request args
    pagination_params = create_pagination_params(request.args)

    # Extract optional filter parameters (type, category)
    filters = {}
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    if request.args.get('category'):
        filters['category'] = request.args.get('category')

    # Call dashboard_service.get_templates with filters and pagination
    result = dashboard_service.get_templates(
        filters=filters,
        page=pagination_params.page,
        page_size=pagination_params.per_page
    )

    # Return JSON response with paginated template list
    return jsonify(result)


@dashboard_blueprint.route('/templates/<template_id>', methods=['GET'])
@token_required
def get_dashboard_template(template_id: str):
    """
    Get a single dashboard template by ID.

    Args:
        template_id: ID of the template

    Returns:
        JSON: Dashboard template details
    """
    try:
        # Call dashboard_service.get_template_by_id with template_id
        template = dashboard_service.get_template_by_id(template_id)

        # Return JSON response with template data
        return jsonify(template.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if template doesn't exist
        logger.warning(f"Dashboard template not found: {str(e)}")
        raise


@dashboard_blueprint.route('/templates/<template_id>/create', methods=['POST'])
@token_required
def create_dashboard_from_template(template_id: str):
    """
    Create a new dashboard from a template.

    Args:
        template_id: ID of the template

    Returns:
        JSON: Created dashboard data with ID
    """
    # Extract dashboard customization data from request JSON
    dashboard_data = request.get_json()

    # Validate required fields (name)
    if not dashboard_data or 'name' not in dashboard_data:
        logger.warning("Dashboard name is required")
        raise BadRequestError(message="Dashboard name is required")

    try:
        # Call dashboard_service.create_dashboard_from_template with template_id, data and current user
        user = get_current_user()
        dashboard = dashboard_service.create_dashboard_from_template(template_id, dashboard_data, user)

        # Return JSON response with created dashboard ID and 201 status
        return jsonify({'id': dashboard.get_id_str()}), 201

    except NotFoundError as e:
        # Handle NotFoundError if template doesn't exist
        logger.warning(f"Dashboard template not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if dashboard data is invalid
        logger.warning(f"Invalid dashboard data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/templates', methods=['POST'])
@token_required
@roles_required(['admin', 'manager'])
def create_dashboard_template():
    """
    Create a new dashboard template.

    Returns:
        JSON: Created template data with ID
    """
    # Extract template data from request JSON
    template_data = request.get_json()

    # Validate required fields (name, type, definition)
    if not template_data or 'name' not in template_data:
        logger.warning("Template name is required")
        raise BadRequestError(message="Template name is required")

    try:
        # Call dashboard_service.create_template with template data and current user
        user = get_current_user()
        template = dashboard_service.create_template(template_data, user)

        # Return JSON response with created template ID and 201 status
        return jsonify({'id': template.get_id_str()}), 201

    except ValueError as e:
        # Handle ValueError if template data is invalid
        logger.warning(f"Invalid template data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/templates/<template_id>', methods=['PUT'])
@token_required
@roles_required(['admin', 'manager'])
def update_dashboard_template(template_id: str):
    """
    Update an existing dashboard template.

    Args:
        template_id: ID of the template

    Returns:
        JSON: Updated template data
    """
    # Extract template data from request JSON
    template_data = request.get_json()

    try:
        # Call dashboard_service.update_template with template_id, data and current user
        user = get_current_user()
        template = dashboard_service.update_template(template_id, template_data, user)

        # Return JSON response with updated template data
        return jsonify(template.to_dict())

    except NotFoundError as e:
        # Handle NotFoundError if template doesn't exist
        logger.warning(f"Dashboard template not found: {str(e)}")
        raise
    except ValueError as e:
        # Handle ValueError if template data is invalid
        logger.warning(f"Invalid template data: {str(e)}")
        raise BadRequestError(message=str(e))


@dashboard_blueprint.route('/templates/<template_id>', methods=['DELETE'])
@token_required
@roles_required(['admin', 'manager'])
def delete_dashboard_template(template_id: str):
    """
    Delete a dashboard template.

    Args:
        template_id: ID of the template

    Returns:
        JSON: Deletion confirmation
    """
    try:
        # Call dashboard_service.delete_template with template_id and current user
        user = get_current_user()
        dashboard_service.delete_template(template_id, user)

        # Return JSON success response
        return jsonify({'message': 'Dashboard template deleted successfully'})

    except NotFoundError as e:
        # Handle NotFoundError if template doesn't exist
        logger.warning(f"Dashboard template not found: {str(e)}")
        raise