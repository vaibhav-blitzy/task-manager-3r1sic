"""
API endpoints for user management in the authentication service, providing CRUD operations,
role management, and user profile functionalities.
"""

from flask import Blueprint, request, jsonify, g  # flask v2.2.3
from bson import ObjectId  # pymongo v4.3.3

from ..services.user_service import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    update_user,
    delete_user,
    change_user_password,
    reset_user_password,
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
)
from src.backend.common.auth.decorators import token_required, admin_required, owner_required, get_current_user
from src.backend.common.schemas.pagination import PaginationParams, create_pagination_params, paginate_response
from src.backend.common.exceptions.api_exceptions import ValidationError, NotFoundError, AuthenticationError, AuthorizationError, ConflictError
from src.backend.common.logging.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create a Flask Blueprint for the users API
users_bp = Blueprint('users', __name__)


@users_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users():
    """
    Retrieve a paginated list of users with optional filtering.
    """
    # Get pagination parameters from request args
    pagination_params = create_pagination_params(request.args)

    # Get optional filter parameters (email, name)
    email = request.args.get('email')
    name = request.args.get('name')

    # Create filter dictionary with provided filters
    filters = {}
    if email:
        filters['email'] = email
    if name:
        filters['$or'] = [
            {'firstName': {'$regex': name, '$options': 'i'}},
            {'lastName': {'$regex': name, '$options': 'i'}}
        ]

    # Call user service to get filtered, paginated users
    users = get_all_users(pagination_params, filters)

    # Return paginated response with user list and metadata
    return jsonify(paginate_response(users['items'], users['total'], pagination_params)), 200


@users_bp.route('/users/<user_id>', methods=['GET'])
@token_required
def get_user(user_id: str):
    """
    Retrieve a specific user by ID.
    """
    # Check if requesting user is admin or the user being requested
    if not (hasattr(g, 'user') and (g.user.get('roles') and "system_admin" in g.user.get('roles') or g.user.get('user_id') == user_id)):
        logger.warning(f"Unauthorized attempt to access user with ID: {user_id}")
        raise AuthorizationError("You don't have permission to access this user")

    # Call get_user_by_id to retrieve user
    user = get_user_by_id(user_id)

    # If user not found, raise NotFoundError
    if not user:
        logger.warning(f"User not found with ID: {user_id}")
        raise NotFoundError("User not found")

    # Return user data as JSON response
    return jsonify(user.to_dict()), 200


@users_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_new_user():
    """
    Create a new user (admin only).
    """
    # Validate that required fields are present in request JSON
    user_data = request.get_json()
    if not user_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    # Call create_user service with request data
    try:
        user = create_user(user_data)
    except ValidationError as e:
        logger.warning(f"Validation error during user creation: {str(e)}")
        raise e
    except ConflictError as e:
        logger.warning(f"Conflict error during user creation: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during user creation: {str(e)}")
        raise e

    # Return created user data with 201 status code
    return jsonify(user.to_dict()), 201


@users_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
def update_user_profile(user_id: str):
    """
    Update a user's profile information.
    """
    # Check if requesting user is admin or the user being updated
    if not (hasattr(g, 'user') and (g.user.get('roles') and "system_admin" in g.user.get('roles') or g.user.get('user_id') == user_id)):
        logger.warning(f"Unauthorized attempt to update user with ID: {user_id}")
        raise AuthorizationError("You don't have permission to update this user")

    # Validate that request contains updateable fields
    update_data = request.get_json()
    if not update_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    # Call update_user service with user_id and update data
    try:
        user = update_user(user_id, update_data)
    except ValidationError as e:
        logger.warning(f"Validation error during user update: {str(e)}")
        raise e
    except NotFoundError as e:
        logger.warning(f"User not found during update: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during user update: {str(e)}")
        raise e

    # Return updated user data
    return jsonify(user.to_dict()), 200


@users_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user_account(user_id: str):
    """
    Delete a user account (admin only).
    """
    # Call delete_user service with user_id
    try:
        deleted = delete_user(user_id)
    except NotFoundError as e:
        logger.warning(f"User not found during deletion: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during user deletion: {str(e)}")
        raise e

    # Return success message if deletion successful
    if deleted:
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        logger.warning(f"User not found with ID: {user_id}")
        raise NotFoundError("User not found")


@users_bp.route('/users/<user_id>/password', methods=['PUT'])
@token_required
def change_password(user_id: str):
    """
    Change a user's password.
    """
    # Check if requesting user is admin or the user whose password is being changed
    if not (hasattr(g, 'user') and (g.user.get('roles') and "system_admin" in g.user.get('roles') or g.user.get('user_id') == user_id)):
        logger.warning(f"Unauthorized attempt to change password for user with ID: {user_id}")
        raise AuthorizationError("You don't have permission to change this password")

    # Extract current_password and new_password from request
    password_data = request.get_json()
    if not password_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    current_password = password_data.get('current_password')
    new_password = password_data.get('new_password')

    # Validate that both fields are present
    if not current_password or not new_password:
        logger.warning("Missing current_password or new_password in request")
        raise ValidationError("Both current_password and new_password are required")

    # Call change_user_password service with user_id and passwords
    try:
        changed = change_user_password(user_id, current_password, new_password)
    except AuthenticationError as e:
        logger.warning(f"Authentication error during password change: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Validation error during password change: {str(e)}")
        raise e
    except NotFoundError as e:
        logger.warning(f"User not found during password change: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during password change: {str(e)}")
        raise e

    # Return success message if password change successful
    if changed:
        return jsonify({"message": "Password changed successfully"}), 200
    else:
        logger.warning(f"Password change failed for user with ID: {user_id}")
        return jsonify({"message": "Password change failed"}), 400


@users_bp.route('/users/<user_id>/roles', methods=['GET'])
@token_required
def get_user_roles_endpoint(user_id: str):
    """
    Get all roles assigned to a user.
    """
    # Check if requesting user is admin or the user whose roles are being requested
    if not (hasattr(g, 'user') and (g.user.get('roles') and "system_admin" in g.user.get('roles') or g.user.get('user_id') == user_id)):
        logger.warning(f"Unauthorized attempt to access roles for user with ID: {user_id}")
        raise AuthorizationError("You don't have permission to access these roles")

    # Call get_user_roles service with user_id
    try:
        roles = get_user_roles(user_id)
    except NotFoundError as e:
        logger.warning(f"User not found while retrieving roles: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during role retrieval: {str(e)}")
        raise e

    # Return list of roles as JSON response
    return jsonify({"roles": roles}), 200


@users_bp.route('/users/<user_id>/roles', methods=['POST'])
@token_required
@admin_required
def assign_role(user_id: str):
    """
    Assign a role to a user (admin only).
    """
    # Extract role_name from request JSON
    role_data = request.get_json()
    if not role_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    role_name = role_data.get('role_name')

    # Validate that role_name is present
    if not role_name:
        logger.warning("Missing role_name in request")
        raise ValidationError("role_name is required")

    # Call assign_role_to_user service with user_id and role_name
    try:
        assigned = assign_role_to_user(user_id, role_name)
    except ValidationError as e:
        logger.warning(f"Validation error during role assignment: {str(e)}")
        raise e
    except NotFoundError as e:
        logger.warning(f"User not found during role assignment: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during role assignment: {str(e)}")
        raise e

    # Return success message if role assignment successful
    if assigned:
        return jsonify({"message": f"Role '{role_name}' assigned successfully"}), 200
    else:
        return jsonify({"message": f"Role '{role_name}' already assigned"}), 200


@users_bp.route('/users/<user_id>/roles/<role_name>', methods=['DELETE'])
@token_required
@admin_required
def remove_role(user_id: str, role_name: str):
    """
    Remove a role from a user (admin only).
    """
    # Call remove_role_from_user service with user_id and role_name
    try:
        removed = remove_role_from_user(user_id, role_name)
    except NotFoundError as e:
        logger.warning(f"User not found during role removal: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during role removal: {str(e)}")
        raise e

    # Return success message if role removal successful
    if removed:
        return jsonify({"message": f"Role '{role_name}' removed successfully"}), 200
    else:
        return jsonify({"message": f"Role '{role_name}' not found on user"}), 404


@users_bp.route('/me', methods=['GET'])
@token_required
def get_current_user_profile():
    """
    Get the currently authenticated user's profile.
    """
    # Get current user from authentication context
    user = get_current_user()

    # Return user data as JSON response
    return jsonify(user.to_dict()), 200


@users_bp.route('/me', methods=['PUT'])
@token_required
def update_current_user_profile():
    """
    Update the currently authenticated user's profile.
    """
    # Get current user from authentication context
    user = get_current_user()

    # Extract update data from request JSON
    update_data = request.get_json()
    if not update_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    # Call update_user service with current user ID and update data
    try:
        updated_user = update_user(user.get('user_id'), update_data)
    except ValidationError as e:
        logger.warning(f"Validation error during user update: {str(e)}")
        raise e
    except NotFoundError as e:
        logger.warning(f"User not found during update: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during user update: {str(e)}")
        raise e

    # Return updated user data
    return jsonify(updated_user.to_dict()), 200


@users_bp.route('/me/password', methods=['PUT'])
@token_required
def change_current_user_password():
    """
    Change the currently authenticated user's password.
    """
    # Get current user from authentication context
    user = get_current_user()

    # Extract current_password and new_password from request
    password_data = request.get_json()
    if not password_data:
        logger.warning("No JSON data provided in request")
        raise ValidationError("No data provided")

    current_password = password_data.get('current_password')
    new_password = password_data.get('new_password')

    # Validate that both fields are present
    if not current_password or not new_password:
        logger.warning("Missing current_password or new_password in request")
        raise ValidationError("Both current_password and new_password are required")

    # Call change_user_password service with current user ID and passwords
    try:
        changed = change_user_password(user.get('user_id'), current_password, new_password)
    except AuthenticationError as e:
        logger.warning(f"Authentication error during password change: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Validation error during password change: {str(e)}")
        raise e
    except NotFoundError as e:
        logger.warning(f"User not found during password change: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during password change: {str(e)}")
        raise e

    # Return success message if password change successful
    if changed:
        return jsonify({"message": "Password changed successfully"}), 200
    else:
        logger.warning("Password change failed")
        return jsonify({"message": "Password change failed"}), 400


def load_user_resource():
    """
    Helper function to load user resource for owner_required decorator.
    """
    # Extract user_id from request path
    user_id = request.view_args.get('user_id')

    # Call get_user_by_id to retrieve user
    user = get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    # Return user object for permission checking
    return user