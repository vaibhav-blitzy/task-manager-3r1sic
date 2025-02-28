"""
Project model for the Task Management System.

This module defines the Project document model for MongoDB which provides
the core data structure for organizing, tracking, and managing projects.
It implements features for project metadata, lifecycle states, team membership,
and task organization.
"""

# Standard library imports
from datetime import datetime
import typing
from typing import Dict, List, Optional, Any, Union
import uuid

# Third-party imports
import bson
from bson import ObjectId

# Internal imports
from ../../../common/database/mongo/models import (
    Document, DocumentQuery, str_to_object_id, object_id_to_str
)
from ../../../common/database/mongo/connection import get_db
from ../../../common/utils/datetime import now
from ../../../common/utils/validators import (
    validate_required, validate_string_length, validate_enum
)
from ../../../common/events/event_bus import get_event_bus_instance, create_event
from ../../../common/logging/logger import get_logger
from ../../../common/exceptions/api_exceptions import ValidationError

# Module logger
logger = get_logger(__name__)

# Get event bus
event_bus = get_event_bus_instance()

# Collection name
PROJECT_COLLECTION = "projects"

# Project status choices
PROJECT_STATUS_CHOICES = ["planning", "active", "on_hold", "completed", "archived"]

# Status transitions - enforces valid workflow transitions
STATUS_TRANSITIONS = {
    "planning": ["active", "on_hold", "archived"],
    "active": ["on_hold", "completed", "archived"],
    "on_hold": ["active", "archived"],
    "completed": ["archived"],
    "archived": []  # Terminal state, no transitions allowed
}


def get_project_by_id(project_id: str) -> Optional['Project']:
    """
    Retrieves a project by its ID.
    
    Args:
        project_id: The ID of the project to retrieve
        
    Returns:
        Project object if found, None otherwise
    """
    # Convert string ID to ObjectId if needed
    obj_id = project_id
    if isinstance(project_id, str):
        obj_id = str_to_object_id(project_id)
    
    # Use the Document.find_by_id method to retrieve the project
    return Project.find_by_id(obj_id)


def get_projects_by_user(user_id: str, filters: Dict = None, skip: int = 0, limit: int = 50) -> List['Project']:
    """
    Retrieves projects that a user is a member of.
    
    Args:
        user_id: The ID of the user to retrieve projects for
        filters: Additional filters to apply to the query
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return (pagination)
        
    Returns:
        List of Project objects the user is a member of
    """
    # Convert user_id to ObjectId if it's a string
    obj_user_id = user_id
    if isinstance(user_id, str):
        obj_user_id = str_to_object_id(user_id)
    
    # Create a base query to find projects where the user is either the owner or a member
    query = {
        "$or": [
            {"owner_id": obj_user_id},
            {"members.user": obj_user_id}
        ]
    }
    
    # Add additional filters if provided
    if filters:
        for key, value in filters.items():
            # Skip filter if the value is None
            if value is None:
                continue
                
            # Handle special case for status filter
            if key == "status" and isinstance(value, list):
                query["status"] = {"$in": value}
            # Handle special case for text search
            elif key == "search" and value:
                query["$text"] = {"$search": value}
            # Handle normal filters
            else:
                query[key] = value
    
    # Create document query
    projects_query = DocumentQuery(Project).filter(query).sort("updated_at", -1)
    
    # Apply pagination
    if skip:
        projects_query.skip(skip)
    if limit:
        projects_query.limit(limit)
    
    # Execute query and return results
    return projects_query.execute()


def search_projects(query: str, user_id: str, filters: Dict = None, skip: int = 0, limit: int = 50) -> List['Project']:
    """
    Searches for projects based on text search and filters.
    
    Args:
        query: Text to search for in project names and descriptions
        user_id: ID of the user making the search (for permission filtering)
        filters: Additional filters to apply
        skip: Number of results to skip (pagination)
        limit: Maximum number of results to return (pagination)
        
    Returns:
        List of Project objects matching search criteria
    """
    # Convert user_id to ObjectId if it's a string
    obj_user_id = user_id
    if isinstance(user_id, str):
        obj_user_id = str_to_object_id(user_id)
    
    # Create a search query
    search_query = {
        "$text": {"$search": query},
        "$or": [
            {"owner_id": obj_user_id},
            {"members.user": obj_user_id}
        ]
    }
    
    # Add additional filters if provided
    if filters:
        for key, value in filters.items():
            if value is not None:
                search_query[key] = value
    
    # Get database connection
    db = get_db()
    
    # Execute the search query with text score sorting
    results = db[PROJECT_COLLECTION].find(
        search_query,
        {"score": {"$meta": "textScore"}}
    ).sort(
        [("score", {"$meta": "textScore"})]
    ).skip(skip).limit(limit)
    
    # Convert results to Project objects
    projects = [Project(data=doc, is_new=False) for doc in results]
    
    return projects


class Project(Document):
    """
    MongoDB document model representing a project in the system with all relevant
    attributes and methods for project management.
    
    A project serves as a container for related tasks, providing organization,
    team management, and workflow capabilities.
    """
    
    collection_name = PROJECT_COLLECTION
    schema = {
        "name": {"type": "str", "required": True},
        "description": {"type": "str", "required": False, "nullable": True},
        "status": {"type": "str", "required": True, "default": "planning"},
        "category": {"type": "str", "required": False, "nullable": True},
        "owner_id": {"type": "ObjectId", "required": True},
        "members": {"type": "list", "required": False},
        "task_lists": {"type": "list", "required": False},
        "settings": {"type": "dict", "required": False},
        "metadata": {"type": "dict", "required": False},
        "tags": {"type": "list", "required": False}
    }
    use_schema_validation = True
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new Project document model instance.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document (not yet in database)
        """
        # Set defaults if data is provided
        if data is None:
            data = {}
        
        # Ensure required arrays and objects exist
        if "task_lists" not in data:
            data["task_lists"] = []
        
        if "members" not in data:
            data["members"] = []
        
        if "settings" not in data:
            data["settings"] = {}
        
        if "tags" not in data:
            data["tags"] = []
        
        if "metadata" not in data:
            data["metadata"] = {
                "created": now(),
                "updated": now()
            }
        
        # Set default status for new projects
        if is_new and "status" not in data:
            data["status"] = "planning"
        
        # Call parent constructor
        super().__init__(data, is_new)
    
    def validate(self) -> bool:
        """
        Validates the project document against schema rules and business logic.
        
        Returns:
            True if valid, raises ValidationError if invalid
        """
        # Call parent validate method first for basic schema validation
        super().validate()
        
        errors = {}
        
        # Validate name (required and length constraints)
        if not self.get("name"):
            errors["name"] = "Project name is required"
        elif len(self.get("name", "")) < 3:
            errors["name"] = "Project name must be at least 3 characters"
        elif len(self.get("name", "")) > 100:
            errors["name"] = "Project name must be at most 100 characters"
        
        # Validate description length if provided
        if self.get("description") and len(self.get("description")) > 5000:
            errors["description"] = "Project description must be at most 5000 characters"
        
        # Validate status is one of the allowed values
        if self.get("status") and self.get("status") not in PROJECT_STATUS_CHOICES:
            errors["status"] = f"Project status must be one of: {', '.join(PROJECT_STATUS_CHOICES)}"
        
        # Validate owner_id is a valid ObjectId
        if not self.get("owner_id"):
            errors["owner_id"] = "Project owner is required"
        elif not isinstance(self.get("owner_id"), ObjectId):
            try:
                # Try to convert to ObjectId if it's a string
                if isinstance(self.get("owner_id"), str):
                    self._data["owner_id"] = ObjectId(self.get("owner_id"))
            except:
                errors["owner_id"] = "Project owner must be a valid ID"
        
        # Validate task_lists structure
        if self.get("task_lists"):
            for i, task_list in enumerate(self.get("task_lists", [])):
                if not task_list.get("id"):
                    errors[f"task_lists.{i}.id"] = "Task list ID is required"
                if not task_list.get("name"):
                    errors[f"task_lists.{i}.name"] = "Task list name is required"
        
        # Validate settings structure
        if self.get("settings"):
            settings = self.get("settings")
            
            # Validate workflow settings if present
            if "workflow" in settings:
                workflow = settings["workflow"]
                if "enableReview" in workflow and not isinstance(workflow["enableReview"], bool):
                    errors["settings.workflow.enableReview"] = "Enable review must be a boolean"
                if "allowSubtasks" in workflow and not isinstance(workflow["allowSubtasks"], bool):
                    errors["settings.workflow.allowSubtasks"] = "Allow subtasks must be a boolean"
            
            # Validate permissions settings if present
            if "permissions" in settings:
                permissions = settings["permissions"]
                valid_roles = ["admin", "manager", "member", "viewer"]
                for key, value in permissions.items():
                    if value not in valid_roles:
                        errors[f"settings.permissions.{key}"] = f"Permission must be one of: {', '.join(valid_roles)}"
        
        # Raise validation error if any errors were found
        if errors:
            raise ValidationError("Project validation failed", errors)
        
        return True
    
    def update_status(self, new_status: str) -> 'Project':
        """
        Updates project status with validation of allowed transitions.
        
        Args:
            new_status: The new status to set
            
        Returns:
            Self with updated status
            
        Raises:
            ValidationError: If the status transition is not allowed
        """
        # Validate that new_status is a valid status
        if new_status not in PROJECT_STATUS_CHOICES:
            raise ValidationError(
                "Invalid project status",
                {"status": f"Status must be one of: {', '.join(PROJECT_STATUS_CHOICES)}"}
            )
        
        # If status isn't changing, do nothing
        current_status = self.get("status")
        if current_status == new_status:
            return self
        
        # Check if transition is allowed
        if new_status not in STATUS_TRANSITIONS.get(current_status, []):
            raise ValidationError(
                "Invalid status transition",
                {"status": f"Cannot transition from '{current_status}' to '{new_status}'. "
                          f"Allowed transitions: {', '.join(STATUS_TRANSITIONS.get(current_status, []))}"}
            )
        
        # Update status
        self._data["status"] = new_status
        
        # If moving to completed status, record the completion time
        if new_status == "completed" and "metadata" in self._data:
            self._data["metadata"]["completedAt"] = now()
        
        return self
    
    def add_task_list(self, name: str, description: str = "") -> Dict:
        """
        Adds a new task list to the project.
        
        Args:
            name: Name of the task list
            description: Optional description of the task list
            
        Returns:
            The created task list as a dictionary
        """
        # Validate name is not empty
        if not name:
            raise ValidationError(
                "Invalid task list",
                {"name": "Task list name is required"}
            )
        
        # Generate a unique ID for the task list
        task_list_id = str(uuid.uuid4())
        
        # Create task list object
        task_list = {
            "id": task_list_id,
            "name": name,
            "description": description,
            "created": now(),
            "sortOrder": len(self.get("task_lists", []))
        }
        
        # Initialize task_lists array if it doesn't exist
        if "task_lists" not in self._data:
            self._data["task_lists"] = []
        
        # Add task list to array
        self._data["task_lists"].append(task_list)
        
        return task_list
    
    def update_task_list(self, task_list_id: str, update_data: Dict) -> Optional[Dict]:
        """
        Updates an existing task list.
        
        Args:
            task_list_id: ID of the task list to update
            update_data: Data to update (name, description, sortOrder)
            
        Returns:
            Updated task list or None if not found
        """
        # Find the task list
        task_lists = self.get("task_lists", [])
        task_list_index = None
        
        for i, task_list in enumerate(task_lists):
            if task_list.get("id") == task_list_id:
                task_list_index = i
                break
        
        # If task list not found, return None
        if task_list_index is None:
            return None
        
        # Update the task list
        for key, value in update_data.items():
            # Skip id - cannot be changed
            if key == "id":
                continue
            
            # Update only valid fields
            if key in ["name", "description", "sortOrder"]:
                self._data["task_lists"][task_list_index][key] = value
        
        return self._data["task_lists"][task_list_index]
    
    def remove_task_list(self, task_list_id: str) -> bool:
        """
        Removes a task list from the project.
        
        Args:
            task_list_id: ID of the task list to remove
            
        Returns:
            True if removed, False if not found
        """
        # Find the task list
        task_lists = self.get("task_lists", [])
        task_list_index = None
        
        for i, task_list in enumerate(task_lists):
            if task_list.get("id") == task_list_id:
                task_list_index = i
                break
        
        # If task list not found, return False
        if task_list_index is None:
            return False
        
        # Remove the task list
        self._data["task_lists"].pop(task_list_index)
        
        return True
    
    def update_settings(self, new_settings: Dict) -> 'Project':
        """
        Updates project settings.
        
        Args:
            new_settings: New settings data to merge with existing
            
        Returns:
            Self with updated settings
        """
        # Initialize settings if it doesn't exist
        if "settings" not in self._data:
            self._data["settings"] = {}
        
        # Update settings (recursive merge)
        self._deep_update(self._data["settings"], new_settings)
        
        return self
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """
        Helper method to recursively update nested dictionaries.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with updates
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._deep_update(target[key], value)
            else:
                # Update or add value
                target[key] = value
    
    def add_custom_field(self, name: str, field_type: str, options: List = None) -> Dict:
        """
        Adds a custom field definition to the project.
        
        Args:
            name: Name of the custom field
            field_type: Type of field (text, number, date, select)
            options: Options for select field type
            
        Returns:
            The created custom field as a dictionary
        """
        # Validate name is not empty
        if not name:
            raise ValidationError(
                "Invalid custom field",
                {"name": "Custom field name is required"}
            )
        
        # Validate field type
        valid_field_types = ["text", "number", "date", "select"]
        if field_type not in valid_field_types:
            raise ValidationError(
                "Invalid custom field",
                {"field_type": f"Field type must be one of: {', '.join(valid_field_types)}"}
            )
        
        # For select type, options must be provided
        if field_type == "select" and not options:
            raise ValidationError(
                "Invalid custom field",
                {"options": "Options are required for select field type"}
            )
        
        # Generate a unique ID for the custom field
        field_id = str(uuid.uuid4())
        
        # Create custom field object
        custom_field = {
            "id": field_id,
            "name": name,
            "type": field_type
        }
        
        # Add options for select type
        if field_type == "select" and options:
            custom_field["options"] = options
        
        # Initialize settings and customFields if they don't exist
        if "settings" not in self._data:
            self._data["settings"] = {}
        
        if "customFields" not in self._data["settings"]:
            self._data["settings"]["customFields"] = []
        
        # Add custom field to array
        self._data["settings"]["customFields"].append(custom_field)
        
        return custom_field
    
    def get_task_list(self, task_list_id: str) -> Optional[Dict]:
        """
        Gets a task list by ID.
        
        Args:
            task_list_id: ID of the task list to retrieve
            
        Returns:
            Task list if found, None otherwise
        """
        # Initialize task_lists array if it doesn't exist
        if "task_lists" not in self._data:
            self._data["task_lists"] = []
        
        # Find the task list
        for task_list in self._data["task_lists"]:
            if task_list.get("id") == task_list_id:
                return task_list
        
        return None
    
    def add_tag(self, tag: str) -> 'Project':
        """
        Adds a tag to the project.
        
        Args:
            tag: Tag to add
            
        Returns:
            Self with updated tags
        """
        # Validate tag is not empty
        if not tag:
            raise ValidationError(
                "Invalid tag",
                {"tag": "Tag cannot be empty"}
            )
        
        # Initialize tags array if it doesn't exist
        if "tags" not in self._data:
            self._data["tags"] = []
        
        # Add tag if it doesn't already exist
        if tag not in self._data["tags"]:
            self._data["tags"].append(tag)
        
        return self
    
    def remove_tag(self, tag: str) -> 'Project':
        """
        Removes a tag from the project.
        
        Args:
            tag: Tag to remove
            
        Returns:
            Self with updated tags
        """
        # Initialize tags array if it doesn't exist
        if "tags" not in self._data:
            self._data["tags"] = []
        
        # Remove tag if it exists
        if tag in self._data["tags"]:
            self._data["tags"].remove(tag)
        
        return self
    
    def calculate_completion_percentage(self) -> int:
        """
        Calculates the project completion percentage based on tasks.
        
        Returns:
            Percentage of completion (0-100)
        """
        # If project is already completed/archived, return 100%
        if self.get("status") in ["completed", "archived"]:
            return 100
        
        # Get database connection
        db = get_db()
        
        # Query for tasks associated with this project
        total_tasks = db.tasks.count_documents({"project_id": self.get_id()})
        
        # If no tasks, return 0%
        if total_tasks == 0:
            return 0
        
        # Count completed tasks
        completed_tasks = db.tasks.count_documents({
            "project_id": self.get_id(),
            "status": "completed"
        })
        
        # Calculate percentage
        completion_percentage = int((completed_tasks / total_tasks) * 100)
        
        return completion_percentage
    
    def to_dict(self) -> Dict:
        """
        Converts project to a dictionary representation.
        
        Returns:
            Dictionary representation of the project
        """
        # Get the base dictionary from parent class
        project_dict = super().to_dict()
        
        # Add calculated completion percentage
        project_dict["completion_percentage"] = self.calculate_completion_percentage()
        
        # Convert ObjectId fields to string
        if "owner_id" in project_dict and isinstance(project_dict["owner_id"], ObjectId):
            project_dict["owner_id"] = str(project_dict["owner_id"])
        
        # Convert member user IDs to string
        if "members" in project_dict:
            for member in project_dict["members"]:
                if "user" in member and isinstance(member["user"], ObjectId):
                    member["user"] = str(member["user"])
        
        # Ensure all datetime fields are formatted properly
        if "metadata" in project_dict:
            for date_field in ["created", "updated", "completedAt"]:
                if date_field in project_dict["metadata"] and isinstance(project_dict["metadata"][date_field], datetime):
                    project_dict["metadata"][date_field] = project_dict["metadata"][date_field].isoformat()
        
        return project_dict
    
    @staticmethod
    def from_dict(data: Dict) -> 'Project':
        """
        Creates a Project instance from a dictionary.
        
        Args:
            data: Dictionary representation of a project
            
        Returns:
            New Project instance
        """
        # Make a copy to avoid modifying the original
        project_data = data.copy()
        
        # Convert string IDs to ObjectId if needed
        if "owner_id" in project_data and isinstance(project_data["owner_id"], str):
            try:
                project_data["owner_id"] = ObjectId(project_data["owner_id"])
            except:
                pass
        
        if "members" in project_data:
            for member in project_data["members"]:
                if "user" in member and isinstance(member["user"], str):
                    try:
                        member["user"] = ObjectId(member["user"])
                    except:
                        pass
        
        # Create Project instance
        return Project(data=project_data, is_new=False if "_id" in project_data else True)
    
    def save(self) -> ObjectId:
        """
        Saves the project to the database with validation.
        
        Returns:
            Project ID
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate project data
        self.validate()
        
        # Get current data for event generation
        is_new = self._is_new
        old_data = None
        
        if not is_new:
            # For existing projects, check status transition
            if '_id' in self._data:
                old_project = Project.find_by_id(self._data['_id'])
                if old_project:
                    old_data = old_project._data.copy()
                    
                    # If status is changing, validate the transition
                    if old_project.get("status") != self.get("status"):
                        self.update_status(self.get("status"))
        else:
            # For new projects, set created timestamp
            if "metadata" not in self._data:
                self._data["metadata"] = {}
            
            self._data["metadata"]["created"] = now()
        
        # Always update the updated timestamp
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        
        self._data["metadata"]["updated"] = now()
        
        # Call parent save method to persist changes
        project_id = super().save()
        
        # Publish event based on operation type
        event_type = "project.created" if is_new else "project.updated"
        event_data = {
            "project_id": str(project_id),
            "name": self.get("name"),
            "owner_id": str(self.get("owner_id")),
            "status": self.get("status")
        }
        
        # Add status change info if status changed
        if not is_new and old_data and old_data.get("status") != self.get("status"):
            event_data["old_status"] = old_data.get("status")
            event_data["new_status"] = self.get("status")
        
        # Create and publish event
        event = create_event(
            event_type=event_type,
            payload=event_data,
            source="project_service"
        )
        
        # Start event bus if needed and publish event
        if not event_bus._running:
            event_bus.start()
        event_bus.publish(event_type, event)
        
        return project_id