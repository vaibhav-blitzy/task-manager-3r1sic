"""
Initialization file for the auth service models package that exposes user and role models
along with their related utility functions, serving as a clean API for other modules
to interact with the authentication data models.
"""

from .user import User, get_user_by_id, get_user_by_email, get_users_by_organization  # Import User model and functions
from .role import Role, get_role_by_name, get_roles_by_ids, get_all_roles  # Import Role model and functions

__all__ = [
    "User",
    "get_user_by_id",
    "get_user_by_email",
    "get_users_by_organization",
    "Role",
    "get_role_by_name",
    "get_roles_by_ids",
    "get_all_roles"
]