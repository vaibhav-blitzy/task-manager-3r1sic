"""
Service layer module that implements business logic for project membership operations,
including adding, removing, and updating members with appropriate role assignments and permission checks.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

import bson.objectid
from bson.objectid import ObjectId  # pymongo v4.3.3

from src.backend.services.project.models.member import (
    ProjectMember,
    ProjectRole,
    get_member_by_id,
    get_member_by_user_and_project,
    get_members_by_project,
)  # Member model and related database operations
from src.backend.services.project.models.project import get_project_by_id  # Retrieve project by ID for validation
from src.backend.services.auth.services.user_service import get_user_by_id  # Retrieve user by ID for validation
from src.backend.common.database.mongo.connection import get_db  # Get database connection for MongoDB operations
from src.backend.common.exceptions.api_exceptions import (
    ValidationError,
    NotFoundError,
    AuthorizationError,
    ConflictError,
)  # Exception classes for error handling
from src.backend.common.auth.permissions import (
    has_permission,
    is_resource_owner,
)  # Permission checking utilities
from src.backend.common.events.event_bus import (
    get_event_bus_instance,
    create_event,
)  # Event publishing for real-time updates
from src.backend.common.logging.logger import get_logger  # Logging functionality
from src.backend.common.utils.validators import (
    validate_object_id,
    validate_required,
)  # Input validation utilities

# Initialize logger
logger = get_logger(__name__)

# Get event bus
event_bus = get_event_bus_instance()


class MemberService:
    """
    Service class for managing project membership operations, providing methods for adding,
    removing, and updating project members with proper role management and permission checks
    """

    def __init__(self):
        """Initialize the MemberService with dependencies"""
        # Get database connection using get_db()
        self.db = get_db()

        # Get event bus instance using get_event_bus_instance()
        self.event_bus = get_event_bus_instance()

        # Initialize logger
        logger.debug("MemberService initialized")

    def add_project_member(
        self, project_id: str, user_id: str, role: str, added_by: str
    ) -> Dict:
        """
        Adds a user as a member to a project with a specific role

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user to add
            role (str): Role to assign to the user
            added_by (str): ID of the user adding the member

        Returns:
            Dict: Added member data

        Raises:
            ValidationError: If input is invalid
            NotFoundError: If project or user not found
            AuthorizationError: If user doesn't have permission
            ConflictError: If user is already a member
        """
        # Validate project_id, user_id, and added_by using validate_object_id
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")
        validate_object_id(added_by, "added_by")

        # Validate role against ProjectRole enum
        if role not in [role.value for role in ProjectRole]:
            raise ValidationError(message=f"Invalid role: {role}")

        # Check if project exists using get_project_by_id
        project = get_project_by_id(project_id)
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user exists using get_user_by_id
        user = get_user_by_id(user_id)
        if not user:
            raise NotFoundError(message="User not found", resource_type="user", resource_id=user_id)

        # Check if the requesting user has permission to manage project members
        requesting_user = get_user_by_id(added_by)
        if not has_permission(requesting_user._data, "project:manage_members", project._data):
            raise AuthorizationError(message="You do not have permission to manage project members")

        # Check if user is already a member using get_member_by_user_and_project
        existing_member = get_member_by_user_and_project(user_id, project_id)
        if existing_member:
            raise ConflictError(message="User is already a member of this project")

        # Create new ProjectMember instance with project_id, user_id, and role
        member = ProjectMember(data={"project_id": project_id, "user_id": user_id, "role": role})

        # Save member to database
        member.save()

        # Create and publish a project.member_added event
        event = create_event(
            event_type="project.member_added",
            payload={"project_id": project_id, "user_id": user_id, "role": role, "added_by": added_by},
            source="member_service",
        )
        event_bus.publish(event["type"], event)

        # Log the member addition
        logger.info(f"Added user {user_id} to project {project_id} with role {role}")

        # Return member data as dictionary using to_dict()
        return member.to_dict()

    def remove_project_member(self, project_id: str, user_id: str, removed_by: str) -> bool:
        """
        Removes a user from a project (soft delete by deactivating)

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user to remove
            removed_by (str): ID of the user removing the member

        Returns:
            bool: True if removal successful

        Raises:
            ValidationError: If input is invalid
            NotFoundError: If member not found
            AuthorizationError: If user doesn't have permission
        """
        # Validate project_id, user_id, and removed_by using validate_object_id
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")
        validate_object_id(removed_by, "removed_by")

        # Get project member using get_member_by_user_and_project
        member = get_member_by_user_and_project(user_id, project_id)
        if not member:
            raise NotFoundError(message="Member not found", resource_type="member", resource_id=user_id)

        # Check if the requesting user has permission to manage project members
        requesting_user = get_user_by_id(removed_by)
        project = get_project_by_id(project_id)
        if not has_permission(requesting_user._data, "project:manage_members", project._data):
            raise AuthorizationError(message="You do not have permission to manage project members")

        # Check if it's the last project admin trying to leave
        members = get_members_by_project(project_id)
        admin_count = sum(1 for m in members if m.role == ProjectRole.ADMIN.value and m.is_active)
        if member.role == ProjectRole.ADMIN.value and admin_count <= 1:
            raise ValidationError(message="Cannot remove the last admin from the project")

        # Deactivate the member using deactivate() method
        member.deactivate()

        # Save changes to database
        member.save()

        # Create and publish a project.member_removed event
        event = create_event(
            event_type="project.member_removed",
            payload={"project_id": project_id, "user_id": user_id, "removed_by": removed_by},
            source="member_service",
        )
        event_bus.publish(event["type"], event)

        # Log the member removal
        logger.info(f"Removed user {user_id} from project {project_id}")

        # Return True on success
        return True

    def update_member_role(
        self, project_id: str, user_id: str, new_role: str, updated_by: str
    ) -> Dict:
        """
        Updates the role of a project member

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user to update
            new_role (str): New role to assign
            updated_by (str): ID of the user updating the role

        Returns:
            Dict: Updated member data

        Raises:
            ValidationError: If input is invalid
            NotFoundError: If member not found
            AuthorizationError: If user doesn't have permission
        """
        # Validate project_id, user_id, and updated_by using validate_object_id
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")
        validate_object_id(updated_by, "updated_by")

        # Validate new_role against ProjectRole enum
        if new_role not in [role.value for role in ProjectRole]:
            raise ValidationError(message=f"Invalid role: {new_role}")

        # Get project member using get_member_by_user_and_project
        member = get_member_by_user_and_project(user_id, project_id)
        if not member:
            raise NotFoundError(message="Member not found", resource_type="member", resource_id=user_id)

        # Check if the requesting user has permission to manage project members
        requesting_user = get_user_by_id(updated_by)
        project = get_project_by_id(project_id)
        if not has_permission(requesting_user._data, "project:manage_members", project._data):
            raise AuthorizationError(message="You do not have permission to manage project members")

        # Update member role using update_role() method
        member.update_role(new_role)

        # Save changes to database
        member.save()

        # Create and publish a project.member_role_updated event
        event = create_event(
            event_type="project.member_role_updated",
            payload={"project_id": project_id, "user_id": user_id, "new_role": new_role, "updated_by": updated_by},
            source="member_service",
        )
        event_bus.publish(event["type"], event)

        # Log the role update
        logger.info(f"Updated role of user {user_id} in project {project_id} to {new_role}")

        # Return updated member data as dictionary
        return member.to_dict()

    def is_project_member(self, project_id: str, user_id: str) -> bool:
        """
        Checks if a user is a member of a project

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user

        Returns:
            bool: True if user is a member, False otherwise
        """
        # Validate project_id and user_id using validate_object_id
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")

        # Get project member using get_member_by_user_and_project
        member = get_member_by_user_and_project(user_id, project_id)

        # Return True if member found and is_active is True
        if member and member.is_active:
            return True

        # Return False otherwise
        return False

    def check_member_permission(self, project_id: str, user_id: str, permission: str) -> bool:
        """
        Checks if a project member has a specific permission based on their role

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user
            permission (str): Permission to check

        Returns:
            bool: True if member has permission, False otherwise
        """
        # Validate project_id and user_id using validate_object_id
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")

        # Get project member using get_member_by_user_and_project
        member = get_member_by_user_and_project(user_id, project_id)

        # If member not found, return False
        if not member:
            return False

        # If member role is ADMIN, return True (full access)
        if member.role == ProjectRole.ADMIN.value:
            return True

        # Check if member role has the required permission
        # (Implementation depends on how permissions are stored and checked)
        # For example, you might have a dictionary mapping roles to permissions
        # and check if the permission is in the list of permissions for the role
        # For simplicity, we'll just return False for now
        return False

    def get_project_members(
        self, project_id: str, filters: Optional[dict] = None, skip: Optional[int] = 0, limit: Optional[int] = 100
    ) -> Tuple[List[Dict], int]:
        """
        Retrieves all members of a project with optional filtering and pagination

        Args:
            project_id (str): ID of the project
            filters (Optional[dict]): Additional filters to apply
            skip (Optional[int]): Number of records to skip for pagination
            limit (Optional[int]): Maximum number of records to return

        Returns:
            Tuple[List[Dict], int]: List of members and total count
        """
        # Validate project_id using validate_object_id
        validate_object_id(project_id, "project_id")

        # Initialize empty filters dictionary if not provided
        if filters is None:
            filters = {}

        # Set default pagination values if not provided
        if skip is None:
            skip = 0
        if limit is None:
            limit = 100

        # Call get_members_by_project with parameters
        members = get_members_by_project(project_id, filters, skip, limit)

        # Count total number of members matching filters
        total_count = self.count_project_members(project_id, filters.get("role"))

        # Convert member objects to dictionaries
        member_list = [member.to_dict() for member in members]

        # Return tuple of (members list, total count)
        return member_list, total_count

    def get_user_projects(
        self, user_id: str, filters: Optional[dict] = None, skip: Optional[int] = 0, limit: Optional[int] = 100
    ) -> List[str]:
        """
        Retrieves all projects that a user is a member of

        Args:
            user_id (str): ID of the user
            filters (Optional[dict]): Additional filters to apply
            skip (Optional[int]): Number of records to skip for pagination
            limit (Optional[int]): Maximum number of records to return

        Returns:
            List[str]: List of project IDs
        """
        # Validate user_id using validate_object_id
        validate_object_id(user_id, "user_id")

        # Initialize empty filters dictionary if not provided
        if filters is None:
            filters = {}

        # Set default pagination values if not provided
        if skip is None:
            skip = 0
        if limit is None:
            limit = 100

        # Apply user_id filter
        filters["user_id"] = user_id

        # Query database for project members with user_id
        project_ids = get_projects_by_user(user_id, filters, skip, limit)

        # Return list of project IDs
        return project_ids

    def count_project_members(self, project_id: str, role: Optional[str] = None) -> int:
        """
        Counts the number of members in a project with optional role filtering

        Args:
            project_id (str): ID of the project
            role (Optional[str]): Role to filter by

        Returns:
            int: Count of project members
        """
        # Validate project_id using validate_object_id
        validate_object_id(project_id, "project_id")

        # Initialize query filter with project_id
        query = {"project_id": project_id, "is_active": True}

        # If role provided, add role filter
        if role:
            query["role"] = role

        # Get database connection
        db = get_db()

        # Execute count query on members collection
        count = db["project_members"].count_documents(query)

        # Return count of matching members
        return count

    def get_member_by_id(self, member_id: str) -> Optional[Dict]:
        """
        Retrieves a project member by its ID

        Args:
            member_id (str): ID of the member to retrieve

        Returns:
            Optional[Dict]: Member data if found, None otherwise
        """
        # Validate member_id using validate_object_id
        validate_object_id(member_id, "member_id")

        # Get member using get_member_by_id function
        member = get_member_by_id(member_id)

        # If member found, return member data as dictionary
        if member:
            return member.to_dict()

        # If not found, return None
        return None