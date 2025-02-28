"""
Permission management module for the Task Management System.

Implements role-based access control (RBAC) and permission management,
defining permission constants, role hierarchies, and utility functions
for permission checking based on user roles and resource ownership.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any

from ..exceptions.api_exceptions import AuthorizationError
from ..logging.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Special permission identifier that represents having all permissions
ALL_PERMISSIONS = "*"


class Permission(Enum):
    """
    Enumeration of all possible permissions in the system.
    These are granular permissions that can be assigned to roles.
    """
    # User related permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Task related permissions
    TASK_VIEW = "task:view"
    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"
    TASK_COMPLETE = "task:complete"
    
    # Project related permissions
    PROJECT_VIEW = "project:view"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    
    # Organization related permissions
    ORGANIZATION_VIEW = "organization:view"
    ORGANIZATION_CREATE = "organization:create"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"
    ORGANIZATION_MANAGE_MEMBERS = "organization:manage_members"
    
    # Comment related permissions
    COMMENT_VIEW = "comment:view"
    COMMENT_CREATE = "comment:create"
    COMMENT_UPDATE = "comment:update"
    COMMENT_DELETE = "comment:delete"
    
    # Attachment related permissions
    ATTACHMENT_VIEW = "attachment:view"
    ATTACHMENT_CREATE = "attachment:create"
    ATTACHMENT_DELETE = "attachment:delete"
    
    # Settings related permissions
    SETTINGS_VIEW = "settings:view"
    SETTINGS_UPDATE = "settings:update"
    
    # Report related permissions
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    
    # System level permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_SETTINGS = "system:settings"
    
    # Team related permissions
    TEAM_VIEW = "team:view"
    TEAM_CREATE = "team:create"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE_MEMBERS = "team:manage_members"


class Role(Enum):
    """
    Enumeration of system roles and their hierarchy.
    Roles have increasing levels of permission.
    """
    # System roles
    SYSTEM_ADMIN = "system_admin"  # Has all permissions
    
    # Organization roles
    ORGANIZATION_ADMIN = "organization_admin"  # Admin within an organization
    
    # Project roles
    PROJECT_MANAGER = "project_manager"  # Manages project and team
    TEAM_MEMBER = "team_member"  # Regular project team member
    VIEWER = "viewer"  # Read-only access


class ResourceType(Enum):
    """
    Enumeration of resource types for permission checking.
    """
    USER = "user"
    TASK = "task"
    PROJECT = "project"
    ORGANIZATION = "organization"
    COMMENT = "comment"
    ATTACHMENT = "attachment"
    REPORT = "report"
    TEAM = "team"


# Permissions that are automatically granted to the owner of a resource
OWNER_PERMISSIONS = [
    Permission.TASK_VIEW.value,
    Permission.TASK_UPDATE.value,
    Permission.TASK_DELETE.value,
    Permission.PROJECT_VIEW.value,
    Permission.PROJECT_UPDATE.value,
    Permission.PROJECT_DELETE.value,
    Permission.COMMENT_VIEW.value,
    Permission.COMMENT_UPDATE.value,
    Permission.COMMENT_DELETE.value,
    Permission.ATTACHMENT_VIEW.value,
    Permission.ATTACHMENT_DELETE.value
]

# Human-readable descriptions of each permission
PERMISSION_DESCRIPTIONS = {
    Permission.USER_VIEW.value: "View user details",
    Permission.USER_CREATE.value: "Create new users",
    Permission.USER_UPDATE.value: "Update user information",
    Permission.USER_DELETE.value: "Delete users",
    
    Permission.TASK_VIEW.value: "View tasks",
    Permission.TASK_CREATE.value: "Create new tasks",
    Permission.TASK_UPDATE.value: "Update task details",
    Permission.TASK_DELETE.value: "Delete tasks",
    Permission.TASK_ASSIGN.value: "Assign tasks to users",
    Permission.TASK_COMPLETE.value: "Mark tasks as complete",
    
    Permission.PROJECT_VIEW.value: "View projects",
    Permission.PROJECT_CREATE.value: "Create new projects",
    Permission.PROJECT_UPDATE.value: "Update project details",
    Permission.PROJECT_DELETE.value: "Delete projects",
    Permission.PROJECT_MANAGE_MEMBERS.value: "Manage project members",
    
    Permission.ORGANIZATION_VIEW.value: "View organization details",
    Permission.ORGANIZATION_CREATE.value: "Create new organizations",
    Permission.ORGANIZATION_UPDATE.value: "Update organization details",
    Permission.ORGANIZATION_DELETE.value: "Delete organizations",
    Permission.ORGANIZATION_MANAGE_MEMBERS.value: "Manage organization members",
    
    Permission.COMMENT_VIEW.value: "View comments",
    Permission.COMMENT_CREATE.value: "Create new comments",
    Permission.COMMENT_UPDATE.value: "Update comments",
    Permission.COMMENT_DELETE.value: "Delete comments",
    
    Permission.ATTACHMENT_VIEW.value: "View attachments",
    Permission.ATTACHMENT_CREATE.value: "Add attachments",
    Permission.ATTACHMENT_DELETE.value: "Delete attachments",
    
    Permission.SETTINGS_VIEW.value: "View settings",
    Permission.SETTINGS_UPDATE.value: "Update settings",
    
    Permission.REPORT_VIEW.value: "View reports",
    Permission.REPORT_CREATE.value: "Create reports",
    
    Permission.SYSTEM_ADMIN.value: "Full system administration access",
    Permission.SYSTEM_SETTINGS.value: "Manage system settings",
    
    Permission.TEAM_VIEW.value: "View teams",
    Permission.TEAM_CREATE.value: "Create teams",
    Permission.TEAM_UPDATE.value: "Update team details",
    Permission.TEAM_DELETE.value: "Delete teams",
    Permission.TEAM_MANAGE_MEMBERS.value: "Manage team members",
    
    ALL_PERMISSIONS: "All permissions (superuser)"
}

# Define permissions for each role with hierarchical structure
ROLE_PERMISSIONS = {
    # System admin has all permissions
    Role.SYSTEM_ADMIN.value: [ALL_PERMISSIONS],
    
    # Organization admin has organization management permissions
    Role.ORGANIZATION_ADMIN.value: [
        Permission.USER_VIEW.value,
        Permission.USER_CREATE.value,
        Permission.USER_UPDATE.value,
        
        Permission.PROJECT_VIEW.value,
        Permission.PROJECT_CREATE.value,
        Permission.PROJECT_UPDATE.value,
        Permission.PROJECT_DELETE.value,
        Permission.PROJECT_MANAGE_MEMBERS.value,
        
        Permission.ORGANIZATION_VIEW.value,
        Permission.ORGANIZATION_UPDATE.value,
        Permission.ORGANIZATION_MANAGE_MEMBERS.value,
        
        Permission.REPORT_VIEW.value,
        Permission.REPORT_CREATE.value,
        
        Permission.TEAM_VIEW.value,
        Permission.TEAM_CREATE.value,
        Permission.TEAM_UPDATE.value,
        Permission.TEAM_DELETE.value,
        Permission.TEAM_MANAGE_MEMBERS.value,
        
        Permission.SETTINGS_VIEW.value,
        Permission.SETTINGS_UPDATE.value
    ],
    
    # Project manager has project management permissions
    Role.PROJECT_MANAGER.value: [
        Permission.USER_VIEW.value,
        
        Permission.TASK_VIEW.value,
        Permission.TASK_CREATE.value,
        Permission.TASK_UPDATE.value,
        Permission.TASK_DELETE.value,
        Permission.TASK_ASSIGN.value,
        Permission.TASK_COMPLETE.value,
        
        Permission.PROJECT_VIEW.value,
        Permission.PROJECT_UPDATE.value,
        Permission.PROJECT_MANAGE_MEMBERS.value,
        
        Permission.COMMENT_VIEW.value,
        Permission.COMMENT_CREATE.value,
        Permission.COMMENT_UPDATE.value,
        Permission.COMMENT_DELETE.value,
        
        Permission.ATTACHMENT_VIEW.value,
        Permission.ATTACHMENT_CREATE.value,
        Permission.ATTACHMENT_DELETE.value,
        
        Permission.REPORT_VIEW.value,
        Permission.REPORT_CREATE.value,
        
        Permission.TEAM_VIEW.value,
        Permission.TEAM_UPDATE.value,
        Permission.TEAM_MANAGE_MEMBERS.value,
        
        Permission.SETTINGS_VIEW.value
    ],
    
    # Team member has task execution permissions
    Role.TEAM_MEMBER.value: [
        Permission.USER_VIEW.value,
        
        Permission.TASK_VIEW.value,
        Permission.TASK_CREATE.value,
        Permission.TASK_UPDATE.value,
        Permission.TASK_COMPLETE.value,
        
        Permission.PROJECT_VIEW.value,
        
        Permission.COMMENT_VIEW.value,
        Permission.COMMENT_CREATE.value,
        Permission.COMMENT_UPDATE.value,
        
        Permission.ATTACHMENT_VIEW.value,
        Permission.ATTACHMENT_CREATE.value,
        
        Permission.REPORT_VIEW.value,
        
        Permission.TEAM_VIEW.value,
        
        Permission.SETTINGS_VIEW.value
    ],
    
    # Viewer has read-only permissions
    Role.VIEWER.value: [
        Permission.USER_VIEW.value,
        Permission.TASK_VIEW.value,
        Permission.PROJECT_VIEW.value,
        Permission.COMMENT_VIEW.value,
        Permission.ATTACHMENT_VIEW.value,
        Permission.REPORT_VIEW.value,
        Permission.TEAM_VIEW.value
    ]
}


def has_permission(user: Dict[str, Any], permission: str, resource: Optional[Dict[str, Any]] = None) -> bool:
    """
    Checks if a user has the required permission based on their roles and resource context.
    
    Args:
        user: User dictionary containing roles and other attributes
        permission: The permission to check
        resource: Optional resource dictionary for resource-specific permissions
        
    Returns:
        True if user has permission, False otherwise
    """
    # Handle unauthenticated users
    if not user:
        logger.debug("Permission check failed: No user provided")
        return False
    
    # System admins have all permissions
    if has_roles(user, Role.SYSTEM_ADMIN.value):
        logger.debug(f"Permission granted: User is system admin")
        return True
    
    # Handle the special ALL_PERMISSIONS permission
    if permission == ALL_PERMISSIONS:
        return has_roles(user, Role.SYSTEM_ADMIN.value)
    
    # Check if user is the owner of the resource (if resource provided)
    if resource and is_resource_owner(user, resource):
        if permission in OWNER_PERMISSIONS:
            logger.debug(f"Permission granted: User is resource owner")
            return True
    
    # Get user roles
    user_roles = user.get('roles', [])
    
    # Check if any of the user's roles grant the required permission
    for role in user_roles:
        role_permissions = get_role_permissions(role)
        
        # Check if this role has the specific permission or ALL_PERMISSIONS
        if permission in role_permissions or ALL_PERMISSIONS in role_permissions:
            logger.debug(f"Permission granted: User role '{role}' has permission '{permission}'")
            return True
    
    logger.debug(f"Permission denied: User does not have permission '{permission}'")
    return False


def has_roles(user: Dict[str, Any], roles: Union[List[str], str]) -> bool:
    """
    Checks if a user has any of the required roles.
    
    Args:
        user: User dictionary containing roles and other attributes
        roles: Role or list of roles to check
        
    Returns:
        True if user has any required role, False otherwise
    """
    # Handle unauthenticated users
    if not user:
        logger.debug("Role check failed: No user provided")
        return False
    
    # Convert string role to list for consistent handling
    if isinstance(roles, str):
        roles = [roles]
    
    # System admins have all roles (implicit)
    user_roles = user.get('roles', [])
    if Role.SYSTEM_ADMIN.value in user_roles:
        logger.debug(f"Role check passed: User is system admin")
        return True
    
    # Check if user has any of the required roles
    for role in roles:
        if role in user_roles:
            logger.debug(f"Role check passed: User has role '{role}'")
            return True
    
    logger.debug(f"Role check failed: User does not have any required roles")
    return False


def is_resource_owner(user: Dict[str, Any], resource: Dict[str, Any]) -> bool:
    """
    Checks if a user is the owner of a resource.
    
    Args:
        user: User dictionary containing ID and other attributes
        resource: Resource dictionary with ownership information
        
    Returns:
        True if user is the resource owner, False otherwise
    """
    if not user or not resource:
        return False
    
    user_id = user.get('id')
    
    # Check different ownership fields that might be present in the resource
    if resource.get('created_by') == user_id:
        return True
    
    if resource.get('owner_id') == user_id:
        return True
    
    if resource.get('user_id') == user_id:
        return True
    
    return False


def is_project_member(user: Dict[str, Any], project_id: str, required_role: Optional[str] = None) -> bool:
    """
    Checks if a user is a member of a project with optional role requirement.
    
    Args:
        user: User dictionary containing projects and roles
        project_id: ID of the project to check
        required_role: Optional specific role required in the project
        
    Returns:
        True if user is project member with required role, False otherwise
    """
    if not user:
        return False
    
    # System admins are implicitly members of all projects
    if has_roles(user, Role.SYSTEM_ADMIN.value):
        return True
    
    # Get user's projects list
    user_projects = user.get('projects', [])
    if not user_projects:
        return False
    
    # Find the specified project in user's projects
    for project in user_projects:
        if project.get('id') == project_id:
            # If no specific role is required, return True
            if not required_role:
                return True
            
            # Check for the required role
            if project.get('role') == required_role:
                return True
    
    return False


def is_organization_member(user: Dict[str, Any], org_id: str, required_role: Optional[str] = None) -> bool:
    """
    Checks if a user is a member of an organization with optional role requirement.
    
    Args:
        user: User dictionary containing organizations and roles
        org_id: ID of the organization to check
        required_role: Optional specific role required in the organization
        
    Returns:
        True if user is organization member with required role, False otherwise
    """
    if not user:
        return False
    
    # System admins are implicitly members of all organizations
    if has_roles(user, Role.SYSTEM_ADMIN.value):
        return True
    
    # Get user's organizations list
    user_organizations = user.get('organizations', [])
    if not user_organizations:
        return False
    
    # Find the specified organization in user's organizations
    for org in user_organizations:
        if org.get('id') == org_id or org.get('org_id') == org_id:
            # If no specific role is required, return True
            if not required_role:
                return True
            
            # Check for the required role
            if org.get('role') == required_role:
                return True
    
    return False


def get_role_permissions(role_name: str) -> List[str]:
    """
    Gets the permissions associated with a specific role.
    
    Args:
        role_name: Name of the role to get permissions for
        
    Returns:
        List of permission strings for the specified role
    """
    # Return a copy of the permissions list to prevent modification of the original
    return ROLE_PERMISSIONS.get(role_name, []).copy()