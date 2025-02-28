"""
Initialization file for the authentication services package that exports the core service classes and functions from individual service modules. This file simplifies imports by allowing consumers to import directly from the services package.
"""

# Import authentication service functions
from .auth_service import (
    authenticate_user,
    register_user,
    verify_email,
    request_password_reset,
    reset_password,
    change_password,
    refresh_authentication,
    logout_user,
    setup_mfa,
    verify_mfa_setup,
    disable_mfa,
    validate_auth_token,
    get_user_from_header,
)

# Import role management service functions
from .role_service import (
    create_role,
    update_role,
    delete_role,
    get_role,
    list_roles,
    add_permission_to_role,
    remove_permission_from_role,
    get_role_permissions,
    check_role_has_permission,
    init_system_roles,
    is_role_in_use,
)

# Import user management service functions
from .user_service import (
    create_user,
    set_user_password,
    update_user,
    delete_user,
    get_user,
    find_user_by_email,
    list_users,
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
    add_user_to_organization,
    remove_user_from_organization,
    get_user_organizations,
    list_organization_users,
    add_user_to_project,
    remove_user_from_project,
    get_user_projects,
    search_users,
    update_user_status,
    bulk_add_users_to_organization,
    bulk_add_users_to_project,
)

# Authentication service exports
__all__ = [
    "authenticate_user",  # Authenticate users with credentials
    "register_user",  # Register new users in the system
    "verify_email",  # Verify user email addresses
    "request_password_reset",  # Initiate password reset workflow
    "reset_password",  # Reset password using token
    "change_password",  # Change password with current password verification
    "refresh_authentication",  # Get new tokens using refresh token
    "logout_user",  # Logout user by invalidating tokens
    "setup_mfa",  # Configure MFA for user accounts
    "verify_mfa_setup",  # Verify MFA configuration
    "disable_mfa",  # Disable MFA for user accounts
    "validate_auth_token",  # Validate authentication tokens
    "get_user_from_header",  # Extract user from Authorization header
    "create_role",  # Create a new role with permissions
    "update_role",  # Update an existing role's details
    "delete_role",  # Delete a role if not in use
    "get_role",  # Retrieve a role by ID
    "list_roles",  # List all roles with optional filtering
    "add_permission_to_role",  # Add a permission to a role
    "remove_permission_from_role",  # Remove a permission from a role
    "get_role_permissions",  # Get all permissions for a role
    "check_role_has_permission",  # Check if a role has a specific permission
    "init_system_roles",  # Initialize default system roles
    "is_role_in_use",  # Check if any users have a specific role
    "create_user",  # Create a new user account
    "set_user_password",  # Set or change a user's password
    "update_user",  # Update a user's profile information
    "delete_user",  # Delete or deactivate a user account
    "get_user",  # Retrieve a user by ID
    "find_user_by_email",  # Find a user by email address
    "list_users",  # List users with optional filtering
    "assign_role_to_user",  # Assign a role to a user
    "remove_role_from_user",  # Remove a role from a user
    "get_user_roles",  # Get all roles assigned to a user
    "add_user_to_organization",  # Add a user to an organization
    "remove_user_from_organization",  # Remove a user from an organization
    "get_user_organizations",  # Get all organizations a user belongs to
    "list_organization_users",  # List all users in an organization
    "add_user_to_project",  # Add a user to a project
    "remove_user_from_project",  # Remove a user from a project
    "get_user_projects",  # Get all projects a user belongs to
    "search_users",  # Search for users by various criteria
    "update_user_status",  # Update a user's status
    "bulk_add_users_to_organization",  # Add multiple users to an organization
    "bulk_add_users_to_project",  # Add multiple users to a project
]