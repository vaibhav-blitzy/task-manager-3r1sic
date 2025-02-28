"""
Service layer implementation for role management in the RBAC system.

This module provides business logic for creating, retrieving, updating, and deleting roles,
as well as permission management within roles. It encapsulates all role-related operations
and serves as an intermediary between the API endpoints and the role data model.
"""

import datetime
from typing import Dict, List, Optional, Any, Union

from bson import ObjectId  # v4.3.3

from ..models.role import Role, RoleSchema, get_role_by_name, SYSTEM_ROLES, get_role_permissions
from ../../../common.database.mongo.connection import get_db
from ../../../common.exceptions.api_exceptions import ValidationError, NotFoundError, ConflictError
from ../../../common.auth.permissions import Permission
from ../../../common.logging.logger import get_logger
from ../../../common.events.event_bus import get_event_bus_instance, create_event

# Configure module logger
logger = get_logger(__name__)

# Get event bus instance for publishing role events
event_bus = get_event_bus_instance()


def create_role(name: str, description: str, permissions: List = None, is_system_role: bool = False) -> Dict:
    """
    Creates a new role with specified name, description, and permissions.
    
    Args:
        name: Role name (unique identifier)
        description: Role description for display purposes
        permissions: List of permission objects with resource and action
        is_system_role: Whether this is a predefined system role
        
    Returns:
        Dict: Created role data
        
    Raises:
        ValidationError: If role data is invalid
        ConflictError: If role with same name already exists
    """
    logger.info(f"Creating new role: {name}")
    
    # Validate role name format
    if not name or not name.strip():
        raise ValidationError("Role name cannot be empty")
    
    if not all(c.isalnum() or c == '_' for c in name):
        raise ValidationError("Role name must only contain alphanumeric characters and underscores")
    
    # Check if role already exists by name
    existing_role = get_role_by_name(name)
    if existing_role:
        logger.warning(f"Role with name '{name}' already exists")
        raise ConflictError(
            message=f"Role with name '{name}' already exists",
            resource_type="role",
            resource_id=name
        )
    
    # Use empty list if permissions not provided
    if permissions is None:
        permissions = []
    
    # Validate permissions format if provided
    if permissions:
        try:
            # Use schema validation from RoleSchema
            schema = RoleSchema(
                name=name,
                description=description,
                permissions=permissions,
                is_system_role=is_system_role
            )
        except Exception as e:
            logger.error(f"Invalid role data: {str(e)}")
            raise ValidationError(message="Invalid role data", errors={"permissions": str(e)})
    
    # Create new role instance
    role = Role(
        name=name,
        description=description,
        permissions=permissions,
        is_system_role=is_system_role
    )
    
    # Save role to database
    role_id = role.save()
    
    # Log role creation
    logger.info(f"Created role '{name}' with ID: {role_id}")
    
    # Publish role.created event
    event = create_event(
        event_type="role.created",
        payload={
            "role_id": str(role_id),
            "name": name,
            "description": description,
            "is_system_role": is_system_role,
            "permissions_count": len(permissions)
        },
        source="role_service"
    )
    event_bus.publish("role.created", event)
    
    # Return created role data
    return role.to_dict()


def update_role(role_id: str, role_data: Dict) -> Dict:
    """
    Updates an existing role with new description and/or permissions.
    
    Args:
        role_id: ID of the role to update
        role_data: Dictionary containing updated role data
        
    Returns:
        Dict: Updated role data
        
    Raises:
        NotFoundError: If role with specified ID does not exist
        ValidationError: If role data is invalid or attempting to rename system role
        ConflictError: If updating to a name that already exists
    """
    logger.info(f"Updating role with ID: {role_id}")
    
    # Get role by ID
    role = get_role_by_id(role_id)
    if not role:
        logger.warning(f"Role with ID '{role_id}' not found")
        raise NotFoundError(
            message=f"Role with ID '{role_id}' not found",
            resource_type="role",
            resource_id=role_id
        )
    
    # Get original values for comparison
    original_name = role.name
    is_system_role = role.is_system_role
    
    # Check if trying to change system role name (not allowed)
    if is_system_role and 'name' in role_data and role_data['name'] != original_name:
        logger.warning(f"Attempted to rename system role '{original_name}'")
        raise ValidationError(message="Cannot rename system roles")
    
    # Update role fields with provided data
    if 'name' in role_data and role_data['name'] != original_name:
        # Check if new name already exists
        existing_role = get_role_by_name(role_data['name'])
        if existing_role:
            logger.warning(f"Role with name '{role_data['name']}' already exists")
            raise ConflictError(
                message=f"Role with name '{role_data['name']}' already exists",
                resource_type="role",
                resource_id=role_data['name']
            )
        role.name = role_data['name']
    
    if 'description' in role_data:
        role.description = role_data['description']
    
    if 'permissions' in role_data:
        # Validate permissions format
        try:
            # Use schema validation 
            schema = RoleSchema(
                name=role.name,
                description=role.description,
                permissions=role_data['permissions'],
                is_system_role=role.is_system_role
            )
            role.permissions = role_data['permissions']
        except Exception as e:
            logger.error(f"Invalid permission data: {str(e)}")
            raise ValidationError(message="Invalid permission data", errors={"permissions": str(e)})
    
    # Update timestamp
    role.updated_at = datetime.datetime.utcnow()
    
    # Save updated role
    role.save()
    
    # Log role update
    logger.info(f"Updated role '{role.name}' with ID: {role_id}")
    
    # Publish role.updated event
    event = create_event(
        event_type="role.updated",
        payload={
            "role_id": str(role_id),
            "name": role.name,
            "description": role.description,
            "is_system_role": role.is_system_role,
            "permissions_count": len(role.permissions)
        },
        source="role_service"
    )
    event_bus.publish("role.updated", event)
    
    # Return updated role data
    return role.to_dict()


def delete_role(role_id: str) -> bool:
    """
    Deletes a role if it's not a system role and not in use.
    
    Args:
        role_id: ID of the role to delete
        
    Returns:
        bool: True if deleted successfully
        
    Raises:
        NotFoundError: If role with specified ID does not exist
        ValidationError: If attempting to delete a system role
        ConflictError: If role is currently assigned to users
    """
    logger.info(f"Deleting role with ID: {role_id}")
    
    # Get role by ID
    role = get_role_by_id(role_id)
    if not role:
        logger.warning(f"Role with ID '{role_id}' not found")
        raise NotFoundError(
            message=f"Role with ID '{role_id}' not found",
            resource_type="role",
            resource_id=role_id
        )
    
    # Check if it's a system role (cannot be deleted)
    if role.is_system_role:
        logger.warning(f"Attempted to delete system role '{role.name}'")
        raise ValidationError(message="System roles cannot be deleted")
    
    # Check if role is in use by any users
    if is_role_in_use(role_id):
        logger.warning(f"Cannot delete role '{role.name}' as it is assigned to users")
        raise ConflictError(
            message=f"Cannot delete role '{role.name}' as it is assigned to users",
            resource_type="role",
            resource_id=role_id
        )
    
    # Store role name for logging/event
    role_name = role.name
    
    # Delete the role
    success = role.delete()
    
    if success:
        logger.info(f"Deleted role '{role_name}' with ID: {role_id}")
        
        # Publish role.deleted event
        event = create_event(
            event_type="role.deleted",
            payload={
                "role_id": str(role_id),
                "name": role_name
            },
            source="role_service"
        )
        event_bus.publish("role.deleted", event)
    else:
        logger.error(f"Failed to delete role '{role_name}' with ID: {role_id}")
    
    return success


def get_role(role_id: str) -> Dict:
    """
    Retrieves a role by its ID.
    
    Args:
        role_id: ID of the role to retrieve
        
    Returns:
        Dict: Role data
        
    Raises:
        NotFoundError: If role with specified ID does not exist
    """
    logger.debug(f"Getting role with ID: {role_id}")
    
    # Convert string ID to ObjectId if necessary
    if isinstance(role_id, str) and not role_id.startswith('_id:'):
        try:
            object_id = ObjectId(role_id)
        except Exception:
            object_id = role_id
    else:
        object_id = role_id
    
    # Get database connection
    db = get_db()
    roles_collection = db.roles
    
    # Query for role by ID
    role_doc = roles_collection.find_one({"_id": object_id})
    
    if not role_doc:
        logger.warning(f"Role with ID '{role_id}' not found")
        raise NotFoundError(
            message=f"Role with ID '{role_id}' not found",
            resource_type="role",
            resource_id=role_id
        )
    
    # Convert to Role instance then to dictionary
    role = Role.from_dict(role_doc)
    
    return role.to_dict()


def get_role_by_id(role_id: str) -> Optional[Role]:
    """
    Internal method to get role by ID returning the role instance.
    
    Args:
        role_id: ID of the role to retrieve
        
    Returns:
        Role: Role instance if found
        
    Raises:
        NotFoundError: If role with specified ID does not exist
    """
    # Convert string ID to ObjectId if necessary
    if isinstance(role_id, str) and not role_id.startswith('_id:'):
        try:
            object_id = ObjectId(role_id)
        except Exception:
            object_id = role_id
    else:
        object_id = role_id
    
    # Get database connection
    db = get_db()
    roles_collection = db.roles
    
    # Query for role by ID
    role_doc = roles_collection.find_one({"_id": object_id})
    
    if not role_doc:
        raise NotFoundError(
            message=f"Role with ID '{role_id}' not found",
            resource_type="role",
            resource_id=role_id
        )
    
    # Convert to Role instance
    return Role.from_dict(role_doc)


def list_roles(include_system: bool = True) -> List[Dict]:
    """
    Retrieves a list of roles with optional filtering.
    
    Args:
        include_system: Whether to include system roles in the results
        
    Returns:
        List[Dict]: List of role dictionaries
    """
    logger.debug(f"Listing roles (include_system={include_system})")
    
    # Get database connection
    db = get_db()
    roles_collection = db.roles
    
    # Prepare filter query
    query = {}
    if not include_system:
        query["is_system_role"] = False
    
    # Execute the query
    role_docs = roles_collection.find(query)
    
    # Convert to Role instances then to dictionaries
    roles = [Role.from_dict(doc).to_dict() for doc in role_docs]
    
    logger.debug(f"Found {len(roles)} roles")
    return roles


def add_permission_to_role(role_id: str, permission: Dict) -> Dict:
    """
    Adds a permission to an existing role.
    
    Args:
        role_id: ID of the role to update
        permission: Permission dictionary with resource and action
        
    Returns:
        Dict: Updated role data
        
    Raises:
        NotFoundError: If role with specified ID does not exist
        ValidationError: If permission format is invalid
    """
    logger.info(f"Adding permission to role {role_id}: {permission}")
    
    # Validate permission format
    if not isinstance(permission, dict) or 'resource' not in permission or 'action' not in permission:
        raise ValidationError(
            message="Invalid permission format",
            errors={"permission": "Must be a dictionary with 'resource' and 'action' keys"}
        )
    
    # Get role by ID
    role = get_role_by_id(role_id)
    
    # Add permission to role
    try:
        role.add_permission(permission)
    except ValueError as e:
        logger.error(f"Invalid permission format: {str(e)}")
        raise ValidationError(message=str(e))
    
    # Save updated role
    role.save()
    
    # Log permission addition
    logger.info(f"Added permission '{permission['resource']}:{permission['action']}' to role '{role.name}'")
    
    # Publish role.permission_added event
    event = create_event(
        event_type="role.permission_added",
        payload={
            "role_id": str(role_id),
            "role_name": role.name,
            "permission": permission
        },
        source="role_service"
    )
    event_bus.publish("role.permission_added", event)
    
    # Return updated role data
    return role.to_dict()


def remove_permission_from_role(role_id: str, permission: str) -> Dict:
    """
    Removes a permission from an existing role.
    
    Args:
        role_id: ID of the role to update
        permission: Permission string in format "resource:action"
        
    Returns:
        Dict: Updated role data
        
    Raises:
        NotFoundError: If role with specified ID does not exist
        ValidationError: If permission format is invalid
    """
    logger.info(f"Removing permission from role {role_id}: {permission}")
    
    # Parse permission string to get resource and action
    try:
        resource, action = permission.split(':')
    except ValueError:
        raise ValidationError(
            message="Invalid permission format",
            errors={"permission": "Must be in format 'resource:action'"}
        )
    
    # Get role by ID
    role = get_role_by_id(role_id)
    
    # Remove permission from role
    removed = role.remove_permission(resource, action)
    
    if not removed:
        logger.warning(f"Permission '{permission}' not found in role '{role.name}'")
    else:
        # Save updated role
        role.save()
        
        # Log permission removal
        logger.info(f"Removed permission '{permission}' from role '{role.name}'")
        
        # Publish role.permission_removed event
        event = create_event(
            event_type="role.permission_removed",
            payload={
                "role_id": str(role_id),
                "role_name": role.name,
                "permission": permission
            },
            source="role_service"
        )
        event_bus.publish("role.permission_removed", event)
    
    # Return updated role data
    return role.to_dict()


def check_role_has_permission(role_id: str, permission: str) -> bool:
    """
    Checks if a role has a specific permission.
    
    Args:
        role_id: ID of the role to check
        permission: Permission string in format "resource:action"
        
    Returns:
        bool: True if role has permission, False otherwise
        
    Raises:
        NotFoundError: If role with specified ID does not exist
        ValidationError: If permission format is invalid
    """
    logger.debug(f"Checking if role {role_id} has permission: {permission}")
    
    # Parse permission string to get resource and action
    try:
        resource, action = permission.split(':')
    except ValueError:
        raise ValidationError(
            message="Invalid permission format",
            errors={"permission": "Must be in format 'resource:action'"}
        )
    
    # Get role by ID
    role = get_role_by_id(role_id)
    
    # Check if role has permission
    has_permission = role.has_permission(resource, action)
    
    logger.debug(f"Role '{role.name}' {'has' if has_permission else 'does not have'} permission '{permission}'")
    return has_permission


def init_system_roles() -> Dict:
    """
    Initializes default system roles if they don't exist.
    
    Returns:
        Dict: Summary of initialization results
    """
    logger.info("Initializing system roles")
    
    from ..models.role import create_default_roles
    
    # Create default system roles if they don't exist
    create_default_roles()
    
    # Log system roles initialization
    logger.info("System roles initialization completed")
    
    # Return summary of created roles
    return {
        "status": "success",
        "message": "System roles initialized",
        "roles": list(SYSTEM_ROLES.keys())
    }


def get_roles_by_ids(role_ids: List[str]) -> List[Dict]:
    """
    Retrieves multiple roles by their IDs.
    
    Args:
        role_ids: List of role IDs to retrieve
        
    Returns:
        List[Dict]: List of role dictionaries
    """
    logger.debug(f"Getting roles with IDs: {role_ids}")
    
    if not role_ids:
        return []
    
    # Convert string IDs to ObjectIds
    object_ids = []
    for role_id in role_ids:
        if isinstance(role_id, str) and not role_id.startswith('_id:'):
            try:
                object_id = ObjectId(role_id)
                object_ids.append(object_id)
            except Exception:
                object_ids.append(role_id)
        else:
            object_ids.append(role_id)
    
    # Get database connection
    db = get_db()
    roles_collection = db.roles
    
    # Query for roles by IDs
    role_docs = roles_collection.find({"_id": {"$in": object_ids}})
    
    # Convert to Role instances then to dictionaries
    roles = [Role.from_dict(doc).to_dict() for doc in role_docs]
    
    logger.debug(f"Found {len(roles)} roles")
    return roles


def get_role_permissions_by_id(role_id: str) -> List[Dict]:
    """
    Retrieves all permissions for a specific role.
    
    Args:
        role_id: ID of the role to get permissions for
        
    Returns:
        List[Dict]: List of permission objects
        
    Raises:
        NotFoundError: If role with specified ID does not exist
    """
    logger.debug(f"Getting permissions for role {role_id}")
    
    # Get role by ID
    role = get_role_by_id(role_id)
    
    # Return permissions list
    return role.permissions


def is_role_in_use(role_id: str) -> bool:
    """
    Checks if a role is currently assigned to any users.
    
    Args:
        role_id: ID of the role to check
        
    Returns:
        bool: True if role is in use, False otherwise
    """
    logger.debug(f"Checking if role {role_id} is in use")
    
    # Get database connection
    db = get_db()
    users_collection = db.users
    
    # Convert string ID to ObjectId if necessary
    if isinstance(role_id, str) and not role_id.startswith('_id:'):
        try:
            object_id = ObjectId(role_id)
        except Exception:
            object_id = role_id
    else:
        object_id = role_id
    
    # Count users with this role
    user_count = users_collection.count_documents({"roles": object_id})
    
    is_used = user_count > 0
    logger.debug(f"Role {role_id} is {'in use' if is_used else 'not in use'} by {user_count} users")
    
    return is_used