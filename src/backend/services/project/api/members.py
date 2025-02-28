# typing — Type annotations for better code documentation # standard library
import typing
# Blueprint, request, jsonify — Web framework components for creating routes and handling HTTP requests # latest
from flask import Blueprint, request, jsonify

# get_current_user — Get the authenticated user from request context
# token_required, permission_required — Decorators for securing API endpoints
from '../../../common/auth/decorators' import get_current_user, token_required, permission_required
# MemberService — Service for project member operations
from '../services/member_service' import MemberService
# ProjectRole — Enumeration of project member roles
from '../models/member' import ProjectRole
# PaginationParams, create_pagination_params — Handle pagination for listing member APIs
from '../../../common/schemas/pagination' import PaginationParams, create_pagination_params
# ValidationError, NotFoundError, AuthorizationError, ConflictError — Exception handling for API errors
from '../../../common/exceptions/api_exceptions' import ValidationError, NotFoundError, AuthorizationError, ConflictError
# get_logger — Get configured logger for this module
from '../../../common/logging/logger' import get_logger
# validate_object_id, validate_required — Input validation utilities
from '../../../common/utils/validators' import validate_object_id, validate_required

# member_blueprint — Blueprint('members', __name__)
member_blueprint = Blueprint('members', __name__)
# logger — get_logger(__name__)
logger = get_logger(__name__)
# member_service — MemberService()
member_service = MemberService()

@member_blueprint.route('/<project_id>/members/status', methods=['GET'])
@token_required
def check_member_status_route(project_id: str):
    """Route handler for checking if current user is a member of the project"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id as valid ObjectId
    try:
        validate_object_id(project_id, "project_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Call member_service.is_project_member with project_id and current user ID
    is_member = member_service.is_project_member(project_id, current_user.get("id"))

    # Return membership status with 200 OK status
    return jsonify({"is_member": is_member}), 200

@member_blueprint.route('/<project_id>/members', methods=['GET'])
@token_required
@permission_required('project:view')
def get_project_members_route(project_id: str):
    """Route handler for getting all members of a project with pagination"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id as valid ObjectId
    try:
        validate_object_id(project_id, "project_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Check if user is a project member
    if not member_service.is_project_member(project_id, current_user.get("id")):
        raise AuthorizationError(message="You are not a member of this project")

    # Extract pagination parameters from request arguments
    pagination_params = create_pagination_params(request.args)

    # Get filters from request query parameters
    filters = request.args.to_dict()

    # Call member_service.get_project_members with project_id, filters, pagination
    try:
        members, total = member_service.get_project_members(
            project_id,
            filters=filters,
            skip=pagination_params.get_skip(),
            limit=pagination_params.get_limit()
        )
    except Exception as e:
        logger.error(f"Error getting project members: {str(e)}")
        return jsonify({"message": "Failed to get project members"}), 500

    # Return paginated response with member list and metadata
    response_data = {
        "items": members,
        "page": pagination_params.page,
        "per_page": pagination_params.per_page,
        "total": total
    }
    return jsonify(response_data), 200

@member_blueprint.route('/<project_id>/members', methods=['POST'])
@token_required
@permission_required('project:manage_members')
def add_project_member_route(project_id: str):
    """Route handler for adding a new member to a project"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id as valid ObjectId
    try:
        validate_object_id(project_id, "project_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Parse request JSON body
    try:
        request_data = request.get_json()
    except Exception:
        return jsonify({"message": "Invalid JSON body"}), 400

    # Validate required fields (user_id and role)
    try:
        validate_required(request_data, ["user_id", "role"])
    except ValidationError as e:
        return jsonify(e.to_dict()), 400

    # Validate role is a valid ProjectRole value
    try:
        if request_data["role"] not in [role.value for role in ProjectRole]:
            raise ValidationError(message=f"Invalid role: {request_data['role']}")
    except ValidationError as e:
        return jsonify(e.to_dict()), 400

    # Call member_service.add_project_member with project_id, user_id, role, current user ID
    try:
        member = member_service.add_project_member(
            project_id,
            request_data["user_id"],
            request_data["role"],
            current_user.get("id")
        )
    except (ValidationError, NotFoundError, AuthorizationError, ConflictError) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"Error adding project member: {str(e)}")
        return jsonify({"message": "Failed to add project member"}), 500

    # Return success response with new member data and 201 Created status
    return jsonify(member), 201

def get_member(member_id: str):
    """Load a project member by ID for route handlers"""
    # Validate member_id as valid ObjectId
    try:
        validate_object_id(member_id, "member_id")
    except ValidationError:
        return None

    # Call member_service.get_member_by_id with member_id
    member = member_service.get_member_by_id(member_id)

    # Return member data or None if not found
    return member

@member_blueprint.route('/<project_id>/members/<member_id>', methods=['GET'])
@token_required
@permission_required('project:view')
def get_project_member_route(project_id: str, member_id: str):
    """Route handler for getting a specific project member by ID"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id and member_id as valid ObjectIds
    try:
        validate_object_id(project_id, "project_id")
        validate_object_id(member_id, "member_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Call member_service.get_member_by_id with member_id
    member = get_member(member_id)

    # If member not found, return 404 Not Found
    if not member:
        raise NotFoundError(message="Member not found", resource_type="member", resource_id=member_id)

    # If member's project_id doesn't match the route project_id, return 404 Not Found
    if member.get("project_id") != project_id:
        raise NotFoundError(message="Member not found in this project", resource_type="member", resource_id=member_id)

    # Return member data with 200 OK status
    return jsonify(member), 200

@member_blueprint.route('/<project_id>/members/<member_id>', methods=['PATCH'])
@token_required
@permission_required('project:manage_members')
def update_project_member_route(project_id: str, member_id: str):
    """Route handler for updating a project member's role"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id and member_id as valid ObjectIds
    try:
        validate_object_id(project_id, "project_id")
        validate_object_id(member_id, "member_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Parse request JSON body
    try:
        request_data = request.get_json()
    except Exception:
        return jsonify({"message": "Invalid JSON body"}), 400

    # Get member data using member_service.get_member_by_id
    member = get_member(member_id)

    # If member not found or doesn't belong to project, return 404 Not Found
    if not member or member.get("project_id") != project_id:
        raise NotFoundError(message="Member not found in this project", resource_type="member", resource_id=member_id)

    # Extract new role from request body
    new_role = request_data.get("role")

    # Validate role is a valid ProjectRole value
    try:
        if new_role not in [role.value for role in ProjectRole]:
            raise ValidationError(message=f"Invalid role: {new_role}")
    except ValidationError as e:
        return jsonify(e.to_dict()), 400

    # Call member_service.update_member_role with project_id, member's user_id, new role, current user ID
    try:
        updated_member = member_service.update_member_role(
            project_id,
            member.get("user_id"),
            new_role,
            current_user.get("id")
        )
    except (ValidationError, NotFoundError, AuthorizationError) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"Error updating project member role: {str(e)}")
        return jsonify({"message": "Failed to update project member role"}), 500

    # Return updated member data with 200 OK status
    return jsonify(updated_member), 200

@member_blueprint.route('/<project_id>/members/<member_id>', methods=['DELETE'])
@token_required
@permission_required('project:manage_members')
def remove_project_member_route(project_id: str, member_id: str):
    """Route handler for removing a member from a project"""
    # Get current user from request context
    current_user = get_current_user()

    # Validate project_id and member_id as valid ObjectIds
    try:
        validate_object_id(project_id, "project_id")
        validate_object_id(member_id, "member_id")
    except ValidationError as e:
        return jsonify(e.to_dict()), e.status_code

    # Get member data using member_service.get_member_by_id
    member = get_member(member_id)

    # If member not found or doesn't belong to project, return 404 Not Found
    if not member or member.get("project_id") != project_id:
        raise NotFoundError(message="Member not found in this project", resource_type="member", resource_id=member_id)

    # Call member_service.remove_project_member with project_id, member's user_id, current user ID
    try:
        member_service.remove_project_member(
            project_id,
            member.get("user_id"),
            current_user.get("id")
        )
    except (ValidationError, NotFoundError, AuthorizationError) as e:
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"Error removing project member: {str(e)}")
        return jsonify({"message": "Failed to remove project member"}), 500

    # Return success message with 200 OK status
    return jsonify({"message": "Member removed from project"}), 200

@member_blueprint.errorhandler(Exception)
def error_handler(e):
    """Error handler for member blueprint exceptions"""
    # Log the exception with error level
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

    # Check exception type and convert to appropriate API exception
    if isinstance(e, ValidationError):
        # For ValidationError, return 400 Bad Request with validation details
        return jsonify(e.to_dict()), 400
    elif isinstance(e, NotFoundError):
        # For NotFoundError, return 404 Not Found with resource details
        return jsonify(e.to_dict()), 404
    elif isinstance(e, AuthorizationError):
        # For AuthorizationError, return 403 Forbidden with message
        return jsonify(e.to_dict()), 403
    elif isinstance(e, ConflictError):
        # For ConflictError, return 409 Conflict with resource details
        return jsonify(e.to_dict()), 409
    else:
        # For other exceptions, return 500 Internal Server Error
        return jsonify({"message": "Internal server error"}), 500

# Export Flask blueprint