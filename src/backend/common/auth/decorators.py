"""
Provides decorator functions for securing API endpoints with authentication and authorization requirements.
Implements JWT token validation, role-based access control, and resource-level permission checks across the
Task Management System.
"""

import functools
from flask import request, g

from .jwt_utils import validate_access_token, extract_token_from_header
from .permissions import has_permission, has_roles, is_resource_owner
from ..exceptions.api_exceptions import AuthenticationError, AuthorizationError
from ..logging.logger import get_logger

# Set up module logger
logger = get_logger(__name__)


def token_required(f):
    """
    Decorator that validates JWT access token in request headers and attaches user to request context.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function with token validation
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract Authorization header from request
        auth_header = request.headers.get('Authorization')
        
        # Extract token from Authorization header
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning("Missing authentication token in request")
            raise AuthenticationError("Missing token")
        
        try:
            # Validate the token
            user_data = validate_access_token(token)
            
            # Store the user data in Flask's g object for access in the view function
            g.user = user_data
            
            # Call the decorated function
            return f(*args, **kwargs)
        
        except AuthenticationError as e:
            # Re-raise authentication errors
            logger.warning(f"Authentication error: {str(e)}")
            raise
        
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    return decorated_function


def permission_required(permission, resource_loader=None):
    """
    Decorator that checks if the authenticated user has the required permission.
    
    Args:
        permission (str): Required permission
        resource_loader (callable, optional): Function to load the resource
            
    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.warning("Permission check failed: User not authenticated")
                raise AuthenticationError("Authentication required")
            
            # Get the resource if a resource_loader is provided
            resource = None
            if resource_loader:
                resource = resource_loader(*args, **kwargs)
            
            # Check if user has the required permission
            if has_permission(g.user, permission, resource):
                return f(*args, **kwargs)
            
            # If permission check fails, raise AuthorizationError
            logger.warning(f"Permission denied: User does not have {permission}")
            raise AuthorizationError(f"Permission denied: {permission}", required_permission=permission)
        
        return decorated_function
    
    return decorator


def roles_required(roles):
    """
    Decorator that checks if the authenticated user has any of the required roles.
    
    Args:
        roles (Union[str, List[str]]): Required role(s)
            
    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.warning("Role check failed: User not authenticated")
                raise AuthenticationError("Authentication required")
            
            # Check if user has any of the required roles
            if has_roles(g.user, roles):
                return f(*args, **kwargs)
            
            # If role check fails, raise AuthorizationError
            role_desc = roles if isinstance(roles, str) else ", ".join(roles)
            logger.warning(f"Role check failed: User does not have required role(s) {role_desc}")
            raise AuthorizationError(f"Insufficient role: {role_desc} required")
        
        return decorated_function
    
    return decorator


def owner_required(resource_loader):
    """
    Decorator that checks if the authenticated user is the owner of the resource.
    
    Args:
        resource_loader (callable): Function to load the resource
            
    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.warning("Owner check failed: User not authenticated")
                raise AuthenticationError("Authentication required")
            
            # Get the resource
            resource = resource_loader(*args, **kwargs)
            
            # Check if user is the owner of the resource
            if is_resource_owner(g.user, resource):
                return f(*args, **kwargs)
            
            # If ownership check fails, raise AuthorizationError
            logger.warning("Owner check failed: User is not the resource owner")
            raise AuthorizationError("You don't have permission to access this resource")
        
        return decorated_function
    
    return decorator


def admin_required(f):
    """
    Decorator that restricts access to admin users only.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function with admin check
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.warning("Admin check failed: User not authenticated")
                raise AuthenticationError("Authentication required")
            
            # Check if user has admin role
            if has_roles(g.user, "system_admin"):
                return f(*args, **kwargs)
            
            # If admin check fails, raise AuthorizationError
            logger.warning("Admin check failed: User is not an admin")
            raise AuthorizationError("Administrator access required")
        
        except Exception as e:
            if isinstance(e, (AuthenticationError, AuthorizationError)):
                raise
            
            logger.error(f"Unexpected error during admin check: {str(e)}")
            raise AuthorizationError("Access denied")
    
    return decorated_function


def get_current_user():
    """
    Utility function to retrieve the current authenticated user from request context.
    
    Returns:
        dict: Current user data or None if not authenticated
    """
    return getattr(g, 'user', None)