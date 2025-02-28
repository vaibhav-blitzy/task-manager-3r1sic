"""
Project membership model for the Task Management System.

This module defines the ProjectMember model representing a user's membership in a project
with a specific role. It also provides the ProjectRole enumeration for role-based access control
and functions for retrieving and managing project memberships.
"""

from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from bson import ObjectId

from ...common.database.mongo.models import Document, str_to_object_id
from ...common.database.mongo.connection import get_db
from ...common.utils.datetime import now
from ...common.logging.logger import get_logger

# Set up module logger
logger = get_logger(__name__)

# Collection name for project members
MEMBER_COLLECTION = "project_members"


class ProjectRole(Enum):
    """
    Enumeration of project member roles with different permission levels.
    """
    ADMIN = "admin"       # Full project administration access
    MANAGER = "manager"   # Task management and assignment privileges
    MEMBER = "member"     # Basic contribution privileges
    VIEWER = "viewer"     # Read-only access to project content


class ProjectMember(Document):
    """
    Document model representing a user's membership in a project with a specific role.
    """
    
    def __init__(self, data=None, is_new=True):
        """
        Initialize a project member document.
        
        Args:
            data (dict, optional): Initial document data
            is_new (bool, optional): Flag indicating if this is a new document
        """
        self.collection_name = MEMBER_COLLECTION
        super().__init__(data, is_new)
        
        # Initialize fields with defaults if not provided
        if "project_id" not in self._data:
            self._data["project_id"] = None
        if "user_id" not in self._data:
            self._data["user_id"] = None
        if "role" not in self._data:
            self._data["role"] = ProjectRole.MEMBER.value
        if "joined_at" not in self._data:
            self._data["joined_at"] = now()
        if "is_active" not in self._data:
            self._data["is_active"] = True
    
    @property
    def project_id(self):
        """Get the project ID."""
        return self._data.get("project_id")
    
    @project_id.setter
    def project_id(self, value):
        """Set the project ID."""
        if isinstance(value, str):
            value = str_to_object_id(value)
        self._data["project_id"] = value
    
    @property
    def user_id(self):
        """Get the user ID."""
        return self._data.get("user_id")
    
    @user_id.setter
    def user_id(self, value):
        """Set the user ID."""
        if isinstance(value, str):
            value = str_to_object_id(value)
        self._data["user_id"] = value
    
    @property
    def role(self):
        """Get the role."""
        return self._data.get("role")
    
    @role.setter
    def role(self, value):
        """Set the role."""
        self._data["role"] = value
    
    @property
    def joined_at(self):
        """Get the joined_at timestamp."""
        return self._data.get("joined_at")
    
    @joined_at.setter
    def joined_at(self, value):
        """Set the joined_at timestamp."""
        self._data["joined_at"] = value
    
    @property
    def is_active(self):
        """Get the is_active flag."""
        return self._data.get("is_active")
    
    @is_active.setter
    def is_active(self, value):
        """Set the is_active flag."""
        self._data["is_active"] = value
    
    def update_role(self, new_role: str) -> bool:
        """
        Update the member's role.
        
        Args:
            new_role (str): New role value
            
        Returns:
            bool: True if role updated successfully
        """
        if new_role not in [role.value for role in ProjectRole]:
            raise ValueError(f"Invalid role: {new_role}")
        
        self.role = new_role
        return True
    
    def deactivate(self) -> bool:
        """
        Deactivate the member.
        
        Returns:
            bool: True if member deactivated successfully
        """
        self.is_active = False
        return True
    
    def activate(self) -> bool:
        """
        Activate the member.
        
        Returns:
            bool: True if member activated successfully
        """
        self.is_active = True
        return True
    
    def to_dict(self) -> Dict:
        """
        Convert the project member to a dictionary.
        
        Returns:
            dict: Dictionary representation of the project member
        """
        member_dict = super().to_dict()
        
        # Ensure ObjectIds are converted to strings
        if "project_id" in member_dict and isinstance(member_dict["project_id"], ObjectId):
            member_dict["project_id"] = str(member_dict["project_id"])
        
        if "user_id" in member_dict and isinstance(member_dict["user_id"], ObjectId):
            member_dict["user_id"] = str(member_dict["user_id"])
        
        # Format datetime to ISO format string
        if "joined_at" in member_dict and isinstance(member_dict["joined_at"], datetime):
            member_dict["joined_at"] = member_dict["joined_at"].isoformat()
        
        return member_dict
    
    @staticmethod
    def from_dict(data: Dict) -> 'ProjectMember':
        """
        Create a ProjectMember instance from a dictionary.
        
        Args:
            data (dict): Dictionary data
            
        Returns:
            ProjectMember: New ProjectMember instance
        """
        return ProjectMember(data)


def get_member_by_id(member_id: str) -> Optional[ProjectMember]:
    """
    Retrieves a project member by its ID.
    
    Args:
        member_id (str): The ID of the member to retrieve
        
    Returns:
        ProjectMember or None: The project member if found, None otherwise
    """
    try:
        # Convert string ID to ObjectId if needed
        member_id_obj = str_to_object_id(member_id)
        
        # Get database connection
        db = get_db()
        
        # Query the member collection for document with matching _id
        member_data = db[MEMBER_COLLECTION].find_one({"_id": member_id_obj})
        
        # If found, create and return a ProjectMember instance
        if member_data:
            return ProjectMember(member_data, is_new=False)
        
        # If not found, return None
        return None
    except Exception as e:
        logger.error(f"Error retrieving project member with ID {member_id}: {str(e)}")
        return None


def get_member_by_user_and_project(user_id: str, project_id: str) -> Optional[ProjectMember]:
    """
    Retrieves a project member by user ID and project ID.
    
    Args:
        user_id (str): The ID of the user
        project_id (str): The ID of the project
        
    Returns:
        ProjectMember or None: The project member if found, None otherwise
    """
    try:
        # Convert string IDs to ObjectId if needed
        user_id_obj = str_to_object_id(user_id)
        project_id_obj = str_to_object_id(project_id)
        
        # Get database connection
        db = get_db()
        
        # Query the member collection for document with matching user_id and project_id
        member_data = db[MEMBER_COLLECTION].find_one({
            "user_id": user_id_obj,
            "project_id": project_id_obj
        })
        
        # If found, create and return a ProjectMember instance
        if member_data:
            return ProjectMember(member_data, is_new=False)
        
        # If not found, return None
        return None
    except Exception as e:
        logger.error(f"Error retrieving project member for user {user_id} and project {project_id}: {str(e)}")
        return None


def get_members_by_project(project_id: str, filters: Dict = None, skip: int = 0, limit: int = 100) -> List[ProjectMember]:
    """
    Retrieves all members of a project.
    
    Args:
        project_id (str): The ID of the project
        filters (dict, optional): Additional filters to apply
        skip (int, optional): Number of records to skip for pagination
        limit (int, optional): Maximum number of records to return
        
    Returns:
        List[ProjectMember]: List of ProjectMember instances
    """
    try:
        # Convert string project_id to ObjectId if needed
        project_id_obj = str_to_object_id(project_id)
        
        # Get database connection
        db = get_db()
        
        # Initialize query with project_id filter
        query = {"project_id": project_id_obj}
        
        # Add additional filters if provided
        if filters:
            query.update(filters)
        
        # Apply pagination with skip and limit parameters
        member_data_list = list(db[MEMBER_COLLECTION].find(query).skip(skip).limit(limit))
        
        # Create ProjectMember instances for each result
        members = [ProjectMember(member_data, is_new=False) for member_data in member_data_list]
        
        return members
    except Exception as e:
        logger.error(f"Error retrieving members for project {project_id}: {str(e)}")
        return []


def get_projects_by_user(user_id: str, filters: Dict = None, skip: int = 0, limit: int = 100) -> List[str]:
    """
    Retrieves all projects where the user is a member.
    
    Args:
        user_id (str): The ID of the user
        filters (dict, optional): Additional filters to apply
        skip (int, optional): Number of records to skip for pagination
        limit (int, optional): Maximum number of records to return
        
    Returns:
        List[str]: List of project IDs
    """
    try:
        # Convert string user_id to ObjectId if needed
        user_id_obj = str_to_object_id(user_id)
        
        # Get database connection
        db = get_db()
        
        # Initialize query with user_id filter
        query = {"user_id": user_id_obj}
        
        # Add additional filters if provided
        if filters:
            query.update(filters)
        
        # Apply pagination with skip and limit parameters
        project_cursor = db[MEMBER_COLLECTION].find(query, {"project_id": 1}).skip(skip).limit(limit)
        
        # Extract project_ids from results
        project_ids = [str(doc["project_id"]) for doc in project_cursor]
        
        return project_ids
    except Exception as e:
        logger.error(f"Error retrieving projects for user {user_id}: {str(e)}")
        return []