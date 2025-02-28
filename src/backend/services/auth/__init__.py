"""
Authentication Service package that exposes key functionality from internal modules
to simplify imports for other services and components.
"""

__version__ = "1.0.0"

from .models.user import User  # Import User model for exposing in package
from .models.role import Role  # Import Role model for exposing in package
from .services.auth_service import (  # Import user registration function
    register_user,
    login,
    verify_email,
    verify_mfa,
    refresh_token,
    logout,
    forgot_password,
    reset_password,
)
from .services.user_service import (  # Import user retrieval function
    get_user_by_id,
    get_user_by_email,
    update_user,
)
from .services.role_service import get_roles  # Import roles retrieval function
from .api.auth import auth_bp  # Import authentication API blueprint
from .api.roles import roles_bp  # Import roles API blueprint
from .api.users import users_bp  # Import users API blueprint


__all__ = [
    "__version__",
    "User",
    "Role",
    "register_user",
    "login",
    "verify_email",
    "verify_mfa",
    "refresh_token",
    "logout",
    "forgot_password",
    "reset_password",
    "get_user_by_id",
    "get_user_by_email",
    "update_user",
    "get_roles",
    "auth_bp",
    "roles_bp",
    "users_bp",
]