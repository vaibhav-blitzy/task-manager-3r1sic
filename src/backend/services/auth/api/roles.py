"""
Implements the REST API endpoints for role management in the authorization service,
providing routes for creating, retrieving, updating, and deleting roles as well as
managing role permissions. This module serves as the interface for the RBAC
(Role-Based Access Control) system.
"""

import typing
from flask import Blueprint, request

from ../../../common/auth/decorators import token_required, admin_required, permission_required
from ../../../common/exceptions/api_exceptions import ValidationError, NotFoundError, ConflictError
from ../../../common/auth/permissions import Permission
from ../../../common/schemas/pagination import create_pagination_params, paginate_response
from ../../../common/logging/logger import get_logger

from ../services/role_service import (
    create_role,
    update_role,
    delete_role,
    get_role,
    list_roles,
    add_permission_to_role,
    remove_permission_from_role,
    check_role_has_permission,
    get_role_permissions_by_id,
    init_system_roles
)

# Configure logger
logger = get_logger(__name__)

# Create Blueprint for role management endpoints
roles_blueprint = Blueprint('roles', __name__, url_prefix='/api/v1/roles')


@roles_blueprint.route('', methods=['POST'])
@permission_required(Permission.ROLE_MANAGE)
def create_role_endpoint():
    """
    API endpoint to create a new role.
    
    Returns:
        tuple: JSON response with role data and HTTP status code
    """
    # Extract role data from request JSON
    role_data = request.json
    
    # Validate required fields
    if not role_data:
        raise ValidationError("Missing role data")
    
    if 'name' not in role_data:
        raise ValidationError("Role name is required")
    
    if 'description' not in role_data:
        raise ValidationError("Role description is required")
    
    # Extract field values
    name = role_data.get('name')
    description = role_data.get('description')
    permissions = role_data.get('permissions', [])
    
    # Create the role
    new_role = create_role(name, description, permissions)
    
    logger.info(f"Created new role: {name}")
    
    # Return created role with 201 Created status code
    return new_role, 201


@roles_blueprint.route('/<role_id>', methods=['GET'])
@permission_required(Permission.ROLE_MANAGE)
def get_role_endpoint(role_id: str):
    """
    API endpoint to retrieve a role by ID.
    
    Args:
        role_id: ID of the role to retrieve
        
    Returns:
        tuple: JSON response with role data and HTTP status code
    """
    # Call get_role service function with role_id
    role = get_role(role_id)
    
    logger.debug(f"Retrieved role with ID: {role_id}")
    
    # Return role data with 200 OK status code
    return role, 200


@roles_blueprint.route('/<role_id>', methods=['PUT'])
@permission_required(Permission.ROLE_MANAGE)
def update_role_endpoint(role_id: str):
    """
    API endpoint to update a role's data.
    
    Args:
        role_id: ID of the role to update
        
    Returns:
        tuple: JSON response with updated role data and HTTP status code
    """
    # Extract role data from request JSON
    role_data = request.json
    
    # Validate request data
    if not role_data:
        raise ValidationError("Missing role data")
    
    # Call update_role service function with role_id and updated data
    updated_role = update_role(role_id, role_data)
    
    logger.info(f"Updated role with ID: {role_id}")
    
    # Return updated role with 200 OK status code
    return updated_role, 200


@roles_blueprint.route('/<role_id>', methods=['DELETE'])
@permission_required(Permission.ROLE_MANAGE)
def delete_role_endpoint(role_id: str):
    """
    API endpoint to delete a role.
    
    Args:
        role_id: ID of the role to delete
        
    Returns:
        tuple: JSON response with success message and HTTP status code
    """
    # Call delete_role service function with role_id
    delete_role(role_id)
    
    logger.info(f"Deleted role with ID: {role_id}")
    
    # Return success message with 200 OK status code
    return {"message": "Role deleted successfully"}, 200


@roles_blueprint.route('', methods=['GET'])
@token_required
def list_roles_endpoint():
    """
    API endpoint to list all roles with optional filtering.
    
    Returns:
        tuple: JSON response with paginated roles list and HTTP status code
    """
    # Extract pagination parameters from request args
    pagination_params = create_pagination_params(request.args)
    
    # Extract include_system parameter from query string (default to True)
    include_system = request.args.get('include_system', 'true').lower() != 'false'
    
    # Call list_roles service function with include_system flag
    roles = list_roles(include_system=include_system)
    
    # Return paginated list of roles with 200 OK status code
    paginated_roles = paginate_response(roles, len(roles), pagination_params)
    
    logger.debug(f"Listed {len(roles)} roles (include_system={include_system})")
    
    return paginated_roles, 200


@roles_blueprint.route('/<role_id>/permissions', methods=['POST'])
@permission_required(Permission.ROLE_MANAGE)
def add_permission_endpoint(role_id: str):
    """
    API endpoint to add a permission to a role.
    
    Args:
        role_id: ID of the role to update
        
    Returns:
        tuple: JSON response with updated role data and HTTP status code
    """
    # Extract permission data from request JSON
    permission_data = request.json
    
    # Validate permission field exists
    if not permission_data or 'permission' not in permission_data:
        raise ValidationError("Missing permission data")
    
    # Call add_permission_to_role service function with role_id and permission
    updated_role = add_permission_to_role(role_id, permission_data['permission'])
    
    logger.info(f"Added permission to role {role_id}")
    
    # Return updated role data with 200 OK status code
    return updated_role, 200


@roles_blueprint.route('/<role_id>/permissions/<permission>', methods=['DELETE'])
@permission_required(Permission.ROLE_MANAGE)
def remove_permission_endpoint(role_id: str, permission: str):
    """
    API endpoint to remove a permission from a role.
    
    Args:
        role_id: ID of the role to update
        permission: Permission to remove
        
    Returns:
        tuple: JSON response with updated role data and HTTP status code
    """
    # Call remove_permission_from_role service function with role_id and permission
    updated_role = remove_permission_from_role(role_id, permission)
    
    logger.info(f"Removed permission {permission} from role {role_id}")
    
    # Return updated role data with 200 OK status code
    return updated_role, 200


@roles_blueprint.route('/<role_id>/permissions/<permission>', methods=['GET'])
@permission_required(Permission.ROLE_MANAGE)
def check_permission_endpoint(role_id: str, permission: str):
    """
    API endpoint to check if a role has a specific permission.
    
    Args:
        role_id: ID of the role to check
        permission: Permission to check
        
    Returns:
        tuple: JSON response with permission check result and HTTP status code
    """
    # Call check_role_has_permission service function with role_id and permission
    has_permission = check_role_has_permission(role_id, permission)
    
    logger.debug(f"Checked if role {role_id} has permission {permission}: {has_permission}")
    
    # Return check result with 200 OK status code
    return {"has_permission": has_permission}, 200


@roles_blueprint.route('/<role_id>/permissions', methods=['GET'])
@permission_required(Permission.ROLE_MANAGE)
def get_role_permissions_endpoint(role_id: str):
    """
    API endpoint to get all permissions for a role.
    
    Args:
        role_id: ID of the role to check
        
    Returns:
        tuple: JSON response with permissions list and HTTP status code
    """
    # Call get_role_permissions_by_id service function with role_id
    permissions = get_role_permissions_by_id(role_id)
    
    logger.debug(f"Retrieved permissions for role {role_id}")
    
    # Return list of permissions with 200 OK status code
    return {"permissions": permissions}, 200


@roles_blueprint.route('/init', methods=['POST'])
@admin_required
def init_system_roles_endpoint():
    """
    API endpoint to initialize default system roles.
    
    Returns:
        tuple: JSON response with initialization result and HTTP status code
    """
    # Call init_system_roles service function
    result = init_system_roles()
    
    logger.info("Initialized system roles")
    
    # Return initialization result with 200 OK status code
    return result, 200