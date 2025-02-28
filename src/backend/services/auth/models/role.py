"""
Role model module for the RBAC (Role-Based Access Control) system.

This module defines the Role model for the Task Management System's RBAC system,
including standard roles (Admin, Manager, User), permissions handling, and role hierarchy.
It provides functionality for role persistence, validation, and permission management.
"""

import datetime
from typing import Dict, List, Optional, Any, Union

from bson import ObjectId  # v1.23.0
import pydantic  # v1.10.8

from ../../common.database.mongo.connection import get_db
from ../../common.auth.permissions import Permission, Resource

# Standard system roles dictionary mapping role names to display names
SYSTEM_ROLES = {
    'admin': 'Administrator',
    'manager': 'Manager',
    'user': 'User'
}

# Default permissions for standard roles
DEFAULT_PERMISSIONS = {
    'admin': [
        # Admin has all permissions
        {'resource': '*', 'action': '*'}
    ],
    'manager': [
        # Project management
        {'resource': 'project', 'action': 'view'},
        {'resource': 'project', 'action': 'create'},
        {'resource': 'project', 'action': 'update'},
        {'resource': 'project', 'action': 'delete'},
        
        # Task management
        {'resource': 'task', 'action': 'view'},
        {'resource': 'task', 'action': 'create'},
        {'resource': 'task', 'action': 'update'},
        {'resource': 'task', 'action': 'delete'},
        {'resource': 'task', 'action': 'assign'},
        
        # User management limited permissions
        {'resource': 'user', 'action': 'view'},
        
        # Team management
        {'resource': 'team', 'action': 'view'},
        {'resource': 'team', 'action': 'create'},
        {'resource': 'team', 'action': 'update'},
        {'resource': 'team', 'action': 'delete'},
        
        # Comment management
        {'resource': 'comment', 'action': 'view'},
        {'resource': 'comment', 'action': 'create'},
        {'resource': 'comment', 'action': 'update'},
        {'resource': 'comment', 'action': 'delete'},
        
        # Attachment management
        {'resource': 'attachment', 'action': 'view'},
        {'resource': 'attachment', 'action': 'create'},
        {'resource': 'attachment', 'action': 'delete'},
        
        # Reports
        {'resource': 'report', 'action': 'view'},
        {'resource': 'report', 'action': 'create'}
    ],
    'user': [
        # Basic task permissions
        {'resource': 'task', 'action': 'view'},
        {'resource': 'task', 'action': 'create'},
        {'resource': 'task', 'action': 'update'},
        
        # Basic project permissions
        {'resource': 'project', 'action': 'view'},
        
        # Basic user permissions
        {'resource': 'user', 'action': 'view'},
        
        # Comment permissions
        {'resource': 'comment', 'action': 'view'},
        {'resource': 'comment', 'action': 'create'},
        {'resource': 'comment', 'action': 'update'},
        
        # Attachment permissions
        {'resource': 'attachment', 'action': 'view'},
        {'resource': 'attachment', 'action': 'create'}
    ]
}


class Role:
    """MongoDB model representing a role in the RBAC system."""
    
    def __init__(self, name: str, description: str, permissions: List[Dict], is_system_role: bool = False):
        """
        Initializes a new Role instance.
        
        Args:
            name: Role name (unique identifier)
            description: Role description for display purposes
            permissions: List of permission objects with resource and action
            is_system_role: Whether this is a predefined system role (protected from deletion)
        """
        self._id = None  # MongoDB document ID
        self.name = name
        self.description = description
        self.permissions = permissions
        self.is_system_role = is_system_role
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict:
        """
        Converts Role instance to a dictionary for database storage.
        
        Returns:
            Dictionary representation of the role suitable for MongoDB
        """
        role_dict = {
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions,
            'is_system_role': self.is_system_role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # Include _id if it exists
        if self._id:
            role_dict['_id'] = self._id
        
        return role_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Role':
        """
        Creates a Role instance from a database dictionary.
        
        Args:
            data: Dictionary containing role data from MongoDB
            
        Returns:
            New Role instance populated with the data
        """
        role = cls(
            name=data.get('name'),
            description=data.get('description'),
            permissions=data.get('permissions', []),
            is_system_role=data.get('is_system_role', False)
        )
        
        # Set fields that are not part of initialization
        role._id = data.get('_id')
        
        # Use provided timestamps or defaults
        role.created_at = data.get('created_at', datetime.datetime.utcnow())
        role.updated_at = data.get('updated_at', datetime.datetime.utcnow())
        
        return role
    
    def save(self) -> ObjectId:
        """
        Saves the role to the database, either inserting a new role or updating an existing one.
        
        Returns:
            ObjectId: The MongoDB _id of the inserted/updated role
        """
        db = get_db()
        roles_collection = db.roles
        
        # Update timestamp before saving
        self.updated_at = datetime.datetime.utcnow()
        
        # Convert role to dictionary
        role_dict = self.to_dict()
        
        if self._id:
            # Update existing role
            result = roles_collection.update_one(
                {'_id': self._id},
                {'$set': role_dict}
            )
            return self._id
        else:
            # Insert new role
            result = roles_collection.insert_one(role_dict)
            self._id = result.inserted_id
            return result.inserted_id
    
    def delete(self) -> bool:
        """
        Deletes the role from the database. System roles cannot be deleted.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # System roles cannot be deleted for security reasons
        if self.is_system_role:
            return False
        
        # Cannot delete a role without an ID
        if not self._id:
            return False
        
        db = get_db()
        roles_collection = db.roles
        
        result = roles_collection.delete_one({'_id': self._id})
        return result.deleted_count > 0
    
    def has_permission(self, resource: str, action: str) -> bool:
        """
        Checks if the role has a specific permission.
        
        Args:
            resource: Resource type to check permission for
            action: Action on the resource to check
            
        Returns:
            bool: True if role has permission, False otherwise
        """
        # Check for wildcard permissions and direct matches
        for permission in self.permissions:
            # Direct match
            if permission['resource'] == resource and permission['action'] == action:
                return True
            
            # Wildcard resource match
            if permission['resource'] == '*' and (permission['action'] == action or permission['action'] == '*'):
                return True
            
            # Wildcard action match
            if permission['resource'] == resource and permission['action'] == '*':
                return True
            
            # Full wildcard match (superuser)
            if permission['resource'] == '*' and permission['action'] == '*':
                return True
        
        return False
    
    def add_permission(self, permission: Dict) -> None:
        """
        Adds a permission to the role if it doesn't already exist.
        
        Args:
            permission: Permission dictionary with 'resource' and 'action' keys
            
        Raises:
            ValueError: If permission format is invalid
        """
        # Validate permission format
        if not isinstance(permission, dict) or 'resource' not in permission or 'action' not in permission:
            raise ValueError("Permission must be a dictionary with 'resource' and 'action' keys")
        
        # Check if permission already exists to avoid duplicates
        for existing in self.permissions:
            if (existing['resource'] == permission['resource'] and 
                existing['action'] == permission['action']):
                return  # Permission already exists
        
        # Add the new permission
        self.permissions.append(permission)
        self.updated_at = datetime.datetime.utcnow()
    
    def remove_permission(self, resource: str, action: str) -> bool:
        """
        Removes a permission from the role.
        
        Args:
            resource: Resource type
            action: Action on the resource
            
        Returns:
            bool: True if permission removed, False if not found
        """
        for i, permission in enumerate(self.permissions):
            if permission['resource'] == resource and permission['action'] == action:
                self.permissions.pop(i)
                self.updated_at = datetime.datetime.utcnow()
                return True
        
        return False


class RoleSchema(pydantic.BaseModel):
    """Pydantic schema for role validation."""
    
    name: str
    description: str
    permissions: List[Dict[str, str]]
    is_system_role: bool = False
    
    @pydantic.validator('name')
    def validate_name(cls, name: str) -> str:
        """
        Validates that the role name is properly formatted.
        
        Args:
            name: Role name to validate
            
        Returns:
            str: Validated name
            
        Raises:
            ValueError: If name is empty or contains invalid characters
        """
        if not name or not name.strip():
            raise ValueError("Role name cannot be empty")
        
        # Role names should be lowercase alphanumeric with underscores
        if not all(c.isalnum() or c == '_' for c in name):
            raise ValueError("Role name must only contain alphanumeric characters and underscores")
        
        return name.strip()
    
    @pydantic.validator('permissions')
    def validate_permissions(cls, permissions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validates permission format in the role.
        
        Args:
            permissions: List of permission dictionaries
            
        Returns:
            List[Dict[str, str]]: Validated permissions list
            
        Raises:
            ValueError: If permission format is invalid
        """
        validated_permissions = []
        
        for permission in permissions:
            if not isinstance(permission, dict):
                raise ValueError("Each permission must be a dictionary")
            
            if 'resource' not in permission or 'action' not in permission:
                raise ValueError("Each permission must have 'resource' and 'action' keys")
            
            # Validate that values are strings
            if not isinstance(permission['resource'], str) or not isinstance(permission['action'], str):
                raise ValueError("Permission resource and action must be strings")
            
            validated_permissions.append({
                'resource': permission['resource'],
                'action': permission['action']
            })
        
        return validated_permissions


def create_default_roles() -> None:
    """
    Creates the standard system roles (Admin, Manager, User) with their default permissions
    if they don't exist. This ensures the system has the basic roles needed for operation.
    """
    db = get_db()
    roles_collection = db.roles
    
    # Check if roles already exist
    existing_roles = list(roles_collection.find({'is_system_role': True}))
    existing_role_names = [r['name'] for r in existing_roles]
    
    # Create each system role if it doesn't exist
    for role_name, display_name in SYSTEM_ROLES.items():
        if role_name not in existing_role_names:
            # Create new role with default permissions
            role = Role(
                name=role_name,
                description=display_name,
                permissions=DEFAULT_PERMISSIONS.get(role_name, []),
                is_system_role=True
            )
            
            # Save to database
            role.save()


def get_role_by_name(name: str) -> Optional[Dict]:
    """
    Retrieves a role by its name from the database.
    
    Args:
        name: The role name to search for
        
    Returns:
        Optional[Dict]: Role document if found, None otherwise
    """
    db = get_db()
    roles_collection = db.roles
    
    role_doc = roles_collection.find_one({'name': name})
    return role_doc


def get_role_permissions(role_name: str) -> List[Dict]:
    """
    Retrieves the permissions associated with a role.
    
    Args:
        role_name: Name of the role
        
    Returns:
        List[Dict]: List of permission objects with resource and action
    """
    role_doc = get_role_by_name(role_name)
    
    if role_doc:
        return role_doc.get('permissions', [])
    
    return []