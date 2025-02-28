"""
Task model for the Task Management System.

This module defines the Task document model for storing, retrieving, and managing 
tasks in the MongoDB database. It provides methods for task operations including 
state transitions, assignments, subtask management, and dependency tracking.
"""

# Standard imports
import datetime
import bson
from typing import Dict, List, Any, Optional, Union
import uuid

# Project imports
from ...common.database.mongo.models import (
    Document, DocumentQuery, str_to_object_id, object_id_to_str
)
from ...common.database.mongo.connection import get_db
from ...common.utils.datetime import now, is_overdue, is_due_soon
from ...common.utils.validators import (
    validate_required, validate_string_length, validate_enum
)
from ...common.events.event_bus import get_event_bus_instance, create_event
from ...common.logging.logger import get_logger
from ...common.exceptions.api_exceptions import ValidationError

# Module logger
logger = get_logger(__name__)

# Get event bus instance
event_bus = get_event_bus_instance()

# MongoDB collection name
TASK_COLLECTION = "tasks"

# Task status choices
TASK_STATUS_CHOICES = [
    "created", "assigned", "in_progress", "on_hold", "in_review", "completed", "cancelled"
]

# Task priority choices
TASK_PRIORITY_CHOICES = [
    "low", "medium", "high", "urgent"
]

# Valid status transitions mapping
STATUS_TRANSITIONS = {
    "created": ["assigned", "in_progress", "cancelled"],
    "assigned": ["in_progress", "on_hold", "cancelled"],
    "in_progress": ["on_hold", "in_review", "completed", "cancelled"],
    "on_hold": ["in_progress", "cancelled"],
    "in_review": ["in_progress", "completed", "cancelled"],
    "completed": [],  # Terminal state
    "cancelled": []   # Terminal state
}

# Valid dependency types
DEPENDENCY_TYPES = ["blocks", "blocked_by"]


class Task(Document):
    """
    MongoDB document model representing a task in the system with all relevant attributes and methods.
    
    This class extends the base Document model to provide task-specific functionality,
    including state transitions, assignments, subtasks, dependencies, and more.
    """
    
    collection_name = TASK_COLLECTION
    
    # Schema for MongoDB document validation
    schema = {
        "title": {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 200
        },
        "description": {
            "type": "str",
            "required": False,
            "max_length": 5000
        },
        "status": {
            "type": "str",
            "required": True,
            "enum": TASK_STATUS_CHOICES
        },
        "priority": {
            "type": "str",
            "required": True,
            "enum": TASK_PRIORITY_CHOICES
        },
        "dueDate": {
            "type": "datetime",
            "required": False
        },
        "createdBy": {
            "type": "ObjectId",
            "required": True
        },
        "assigneeId": {
            "type": "ObjectId",
            "required": False,
            "nullable": True
        },
        "projectId": {
            "type": "ObjectId",
            "required": False,
            "nullable": True
        },
        "tags": {
            "type": "list",
            "required": False
        },
        "subtasks": {
            "type": "list",
            "required": False
        },
        "dependencies": {
            "type": "list",
            "required": False
        },
        "comments": {
            "type": "list",
            "required": False
        },
        "attachments": {
            "type": "list",
            "required": False
        },
        "activity": {
            "type": "list",
            "required": False
        },
        "metadata": {
            "type": "dict",
            "required": False
        }
    }
    
    # Enable schema validation
    use_schema_validation = True
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new Task document model instance.
        
        Args:
            data: Initial task data
            is_new: Flag indicating if this is a new task (not yet in database)
        """
        # Initialize with defaults if data not provided
        if data is None:
            data = {}
        
        # Set default values for empty collections
        if "subtasks" not in data:
            data["subtasks"] = []
        if "dependencies" not in data:
            data["dependencies"] = []
        if "comments" not in data:
            data["comments"] = []
        if "attachments" not in data:
            data["attachments"] = []
        if "activity" not in data:
            data["activity"] = []
        if "tags" not in data:
            data["tags"] = []
        
        # Set default status and priority if not provided
        if "status" not in data:
            data["status"] = "created"
        if "priority" not in data:
            data["priority"] = "medium"
        
        # Initialize metadata
        if "metadata" not in data:
            data["metadata"] = {
                "created": now(),
                "lastUpdated": now()
            }
        
        # Call parent class constructor
        super().__init__(data, is_new)
    
    def validate(self) -> bool:
        """
        Validates the task document against schema rules and business logic.
        
        Returns:
            True if valid, raises ValidationError if invalid
        """
        # Call parent validate method for basic schema validation
        super().validate()
        
        errors = {}
        
        # Validate title (required and length constraints)
        if not self.get("title"):
            errors["title"] = "Title is required"
        elif len(self.get("title", "")) < 1:
            errors["title"] = "Title cannot be empty"
        elif len(self.get("title", "")) > 200:
            errors["title"] = "Title cannot exceed 200 characters"
        
        # Validate status
        if "status" in self._data:
            if self.get("status") not in TASK_STATUS_CHOICES:
                errors["status"] = f"Status must be one of: {', '.join(TASK_STATUS_CHOICES)}"
        
        # Validate priority
        if "priority" in self._data:
            if self.get("priority") not in TASK_PRIORITY_CHOICES:
                errors["priority"] = f"Priority must be one of: {', '.join(TASK_PRIORITY_CHOICES)}"
        
        # Validate due date
        if "dueDate" in self._data and self.get("dueDate") is not None:
            if not isinstance(self.get("dueDate"), datetime.datetime):
                errors["dueDate"] = "Due date must be a valid datetime"
        
        # Validate dependencies
        if "dependencies" in self._data and self.get("dependencies"):
            for i, dependency in enumerate(self.get("dependencies")):
                if not isinstance(dependency, dict):
                    errors[f"dependencies.{i}"] = "Dependency must be an object"
                elif "taskId" not in dependency:
                    errors[f"dependencies.{i}"] = "Dependency missing taskId"
                elif "type" not in dependency:
                    errors[f"dependencies.{i}"] = "Dependency missing type"
                elif dependency.get("type") not in DEPENDENCY_TYPES:
                    errors[f"dependencies.{i}"] = f"Dependency type must be one of: {', '.join(DEPENDENCY_TYPES)}"
        
        # Validate subtasks
        if "subtasks" in self._data and self.get("subtasks"):
            for i, subtask in enumerate(self.get("subtasks")):
                if not isinstance(subtask, dict):
                    errors[f"subtasks.{i}"] = "Subtask must be an object"
                elif "title" not in subtask:
                    errors[f"subtasks.{i}"] = "Subtask missing title"
                elif not subtask.get("title"):
                    errors[f"subtasks.{i}"] = "Subtask title cannot be empty"
                
                # Ensure completed is a boolean
                if "completed" in subtask and not isinstance(subtask.get("completed"), bool):
                    errors[f"subtasks.{i}.completed"] = "Completed must be a boolean"
        
        # If there are validation errors, raise a ValidationError
        if errors:
            raise ValidationError("Task validation failed", errors)
        
        return True
    
    def set_status(self, new_status: str) -> 'Task':
        """
        Updates task status with validation of allowed transitions.
        
        Args:
            new_status: The new status to set
            
        Returns:
            Self with updated status
            
        Raises:
            ValidationError: If status transition is not allowed
        """
        # Validate new status is a valid choice
        if new_status not in TASK_STATUS_CHOICES:
            raise ValidationError("Invalid status", {
                "status": f"Status must be one of: {', '.join(TASK_STATUS_CHOICES)}"
            })
        
        # Get current status
        current_status = self.get("status")
        
        # Allow setting the same status (no-op)
        if current_status == new_status:
            return self
        
        # Check if transition is allowed
        if new_status not in STATUS_TRANSITIONS.get(current_status, []):
            allowed = STATUS_TRANSITIONS.get(current_status, [])
            raise ValidationError("Invalid status transition", {
                "status": f"Cannot transition from '{current_status}' to '{new_status}'. "
                         f"Allowed transitions: {', '.join(allowed)}"
            })
        
        # Update status
        self._data["status"] = new_status
        
        # If task is completed, set completedAt timestamp
        if new_status == "completed" and "metadata" in self._data:
            self._data["metadata"]["completedAt"] = now()
        
        # Add to activity log
        self.add_activity("status_changed", self.get("assigneeId"), {
            "oldStatus": current_status,
            "newStatus": new_status
        })
        
        return self
    
    def assign_to(self, user_id: Union[str, bson.ObjectId]) -> 'Task':
        """
        Assigns the task to a user.
        
        Args:
            user_id: ID of the user to assign the task to
            
        Returns:
            Self with updated assignment
        """
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Get current assignee for activity log
        old_assignee = self.get("assigneeId")
        
        # Update assignee
        self._data["assigneeId"] = user_id
        
        # If task is in 'created' status, update to 'assigned'
        if self.get("status") == "created":
            self._data["status"] = "assigned"
        
        # Add to activity log
        self.add_activity("assigned", user_id, {
            "oldAssignee": old_assignee
        })
        
        return self
    
    def update_priority(self, new_priority: str) -> 'Task':
        """
        Updates the task priority.
        
        Args:
            new_priority: The new priority to set
            
        Returns:
            Self with updated priority
        """
        # Validate priority
        if new_priority not in TASK_PRIORITY_CHOICES:
            raise ValidationError("Invalid priority", {
                "priority": f"Priority must be one of: {', '.join(TASK_PRIORITY_CHOICES)}"
            })
        
        # Get current priority for activity log
        old_priority = self.get("priority")
        
        # Update priority
        self._data["priority"] = new_priority
        
        # Add to activity log
        self.add_activity("priority_changed", self.get("assigneeId"), {
            "oldPriority": old_priority,
            "newPriority": new_priority
        })
        
        return self
    
    def update_due_date(self, due_date: datetime.datetime) -> 'Task':
        """
        Updates the task due date.
        
        Args:
            due_date: The new due date to set
            
        Returns:
            Self with updated due date
        """
        # Validate due date
        if not isinstance(due_date, datetime.datetime):
            raise ValidationError("Invalid due date", {
                "dueDate": "Due date must be a valid datetime"
            })
        
        # Get current due date for activity log
        old_due_date = self.get("dueDate")
        
        # Update due date
        self._data["dueDate"] = due_date
        
        # Add to activity log
        self.add_activity("due_date_changed", self.get("assigneeId"), {
            "oldDueDate": old_due_date,
            "newDueDate": due_date
        })
        
        return self
    
    def add_subtask(self, title: str, assignee_id: Union[str, bson.ObjectId] = None) -> Dict:
        """
        Adds a subtask to the task.
        
        Args:
            title: Title of the subtask
            assignee_id: ID of the user assigned to the subtask (optional)
            
        Returns:
            The created subtask object
        """
        # Validate title
        if not title or not title.strip():
            raise ValidationError("Invalid subtask", {
                "title": "Subtask title is required"
            })
        
        # Convert assignee_id to ObjectId if provided as string
        if assignee_id is not None and isinstance(assignee_id, str):
            assignee_id = str_to_object_id(assignee_id)
        
        # Generate unique ID for subtask
        subtask_id = str(uuid.uuid4())
        
        # Create subtask object
        subtask = {
            "id": subtask_id,
            "title": title.strip(),
            "completed": False,
            "assigneeId": assignee_id
        }
        
        # Ensure subtasks list exists
        if "subtasks" not in self._data:
            self._data["subtasks"] = []
        
        # Add subtask to list
        self._data["subtasks"].append(subtask)
        
        # Add to activity log
        self.add_activity("subtask_added", self.get("assigneeId"), {
            "subtaskId": subtask_id,
            "subtaskTitle": title
        })
        
        return subtask
    
    def update_subtask(self, subtask_id: str, update_data: Dict) -> Optional[Dict]:
        """
        Updates an existing subtask.
        
        Args:
            subtask_id: ID of the subtask to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated subtask object or None if not found
        """
        # Find subtask by ID
        subtask_index = None
        subtask = None
        
        for i, st in enumerate(self.get("subtasks", [])):
            if st.get("id") == subtask_id:
                subtask_index = i
                subtask = st
                break
        
        # Return None if subtask not found
        if subtask_index is None:
            return None
        
        # Update fields
        for key, value in update_data.items():
            # Don't allow updating the ID
            if key != "id":
                subtask[key] = value
        
        # Update subtask in list
        self._data["subtasks"][subtask_index] = subtask
        
        # Add to activity log
        self.add_activity("subtask_updated", self.get("assigneeId"), {
            "subtaskId": subtask_id,
            "updates": update_data
        })
        
        return subtask
    
    def remove_subtask(self, subtask_id: str) -> bool:
        """
        Removes a subtask from the task.
        
        Args:
            subtask_id: ID of the subtask to remove
            
        Returns:
            True if removed, False if not found
        """
        # Find subtask by ID
        subtask_index = None
        subtask = None
        
        for i, st in enumerate(self.get("subtasks", [])):
            if st.get("id") == subtask_id:
                subtask_index = i
                subtask = st
                break
        
        # Return False if subtask not found
        if subtask_index is None:
            return False
        
        # Remove subtask from list
        removed = self._data["subtasks"].pop(subtask_index)
        
        # Add to activity log
        self.add_activity("subtask_removed", self.get("assigneeId"), {
            "subtaskId": subtask_id,
            "subtaskTitle": removed.get("title")
        })
        
        return True
    
    def add_dependency(self, task_id: Union[str, bson.ObjectId], dependency_type: str) -> 'Task':
        """
        Adds a dependency relationship with another task.
        
        Args:
            task_id: ID of the task to create dependency with
            dependency_type: Type of dependency ('blocks' or 'blocked_by')
            
        Returns:
            Self with updated dependencies
        """
        # Validate dependency type
        if dependency_type not in DEPENDENCY_TYPES:
            raise ValidationError("Invalid dependency type", {
                "type": f"Dependency type must be one of: {', '.join(DEPENDENCY_TYPES)}"
            })
        
        # Convert task_id to ObjectId if provided as string
        if isinstance(task_id, str):
            task_id = str_to_object_id(task_id)
        
        # Check if dependency already exists
        for dep in self.get("dependencies", []):
            if dep.get("taskId") == task_id and dep.get("type") == dependency_type:
                # Dependency already exists, no change needed
                return self
        
        # Ensure dependencies list exists
        if "dependencies" not in self._data:
            self._data["dependencies"] = []
        
        # Create dependency object
        dependency = {
            "taskId": task_id,
            "type": dependency_type
        }
        
        # Add dependency to list
        self._data["dependencies"].append(dependency)
        
        # Add to activity log
        self.add_activity("dependency_added", self.get("assigneeId"), {
            "taskId": task_id,
            "type": dependency_type
        })
        
        return self
    
    def remove_dependency(self, task_id: Union[str, bson.ObjectId]) -> bool:
        """
        Removes a dependency relationship.
        
        Args:
            task_id: ID of the task in the dependency to remove
            
        Returns:
            True if removed, False if not found
        """
        # Convert task_id to ObjectId if provided as string
        if isinstance(task_id, str):
            task_id = str_to_object_id(task_id)
        
        # Find dependency by task ID
        dependency_index = None
        
        for i, dep in enumerate(self.get("dependencies", [])):
            if dep.get("taskId") == task_id:
                dependency_index = i
                break
        
        # Return False if dependency not found
        if dependency_index is None:
            return False
        
        # Remove dependency from list
        removed = self._data["dependencies"].pop(dependency_index)
        
        # Add to activity log
        self.add_activity("dependency_removed", self.get("assigneeId"), {
            "taskId": task_id,
            "type": removed.get("type")
        })
        
        return True
    
    def add_comment_reference(self, comment_id: Union[str, bson.ObjectId]) -> 'Task':
        """
        Adds a reference to a comment.
        
        Args:
            comment_id: ID of the comment to reference
            
        Returns:
            Self with updated comment references
        """
        # Convert comment_id to ObjectId if provided as string
        if isinstance(comment_id, str):
            comment_id = str_to_object_id(comment_id)
        
        # Ensure comments list exists
        if "comments" not in self._data:
            self._data["comments"] = []
        
        # Check if comment reference already exists
        if comment_id not in self._data["comments"]:
            self._data["comments"].append(comment_id)
        
        return self
    
    def add_attachment_reference(self, file_id: Union[str, bson.ObjectId], file_name: str, 
                                uploaded_by: Union[str, bson.ObjectId]) -> Dict:
        """
        Adds a reference to a file attachment.
        
        Args:
            file_id: ID of the file to reference
            file_name: Name of the file
            uploaded_by: ID of the user who uploaded the file
            
        Returns:
            The attachment reference added
        """
        # Convert IDs to ObjectId if provided as strings
        if isinstance(file_id, str):
            file_id = str_to_object_id(file_id)
        if isinstance(uploaded_by, str):
            uploaded_by = str_to_object_id(uploaded_by)
        
        # Create attachment reference
        attachment = {
            "id": file_id,
            "name": file_name,
            "uploadedBy": uploaded_by,
            "uploadedAt": now()
        }
        
        # Ensure attachments list exists
        if "attachments" not in self._data:
            self._data["attachments"] = []
        
        # Add attachment to list
        self._data["attachments"].append(attachment)
        
        # Add to activity log
        self.add_activity("attachment_added", uploaded_by, {
            "fileId": file_id,
            "fileName": file_name
        })
        
        return attachment
    
    def remove_attachment_reference(self, file_id: Union[str, bson.ObjectId]) -> bool:
        """
        Removes a file attachment reference.
        
        Args:
            file_id: ID of the file to remove
            
        Returns:
            True if removed, False if not found
        """
        # Convert file_id to ObjectId if provided as string
        if isinstance(file_id, str):
            file_id = str_to_object_id(file_id)
        
        # Find attachment by ID
        attachment_index = None
        
        for i, att in enumerate(self.get("attachments", [])):
            if att.get("id") == file_id:
                attachment_index = i
                break
        
        # Return False if attachment not found
        if attachment_index is None:
            return False
        
        # Remove attachment from list
        removed = self._data["attachments"].pop(attachment_index)
        
        # Add to activity log
        self.add_activity("attachment_removed", self.get("assigneeId"), {
            "fileId": file_id,
            "fileName": removed.get("name")
        })
        
        return True
    
    def add_activity(self, activity_type: str, user_id: Union[str, bson.ObjectId], details: Dict = None) -> Dict:
        """
        Records an activity in the task's history.
        
        Args:
            activity_type: Type of activity
            user_id: ID of the user who performed the activity
            details: Additional details about the activity
            
        Returns:
            The activity record added
        """
        # Convert user_id to ObjectId if provided as string
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Create activity record
        activity = {
            "type": activity_type,
            "userId": user_id,
            "timestamp": now(),
            "details": details or {}
        }
        
        # Ensure activity list exists
        if "activity" not in self._data:
            self._data["activity"] = []
        
        # Add activity to list
        self._data["activity"].append(activity)
        
        return activity
    
    def is_overdue(self) -> bool:
        """
        Checks if the task is past its due date.
        
        Returns:
            True if task is overdue, False otherwise
        """
        # If task is completed or cancelled, it's not overdue
        if self.get("status") in ["completed", "cancelled"]:
            return False
        
        # If no due date, it can't be overdue
        due_date = self.get("dueDate")
        if due_date is None:
            return False
        
        # Use is_overdue utility to check
        return is_overdue(due_date)
    
    def is_due_soon(self, hours: int = 24) -> bool:
        """
        Checks if the task is due within the specified hours.
        
        Args:
            hours: Number of hours to consider as "soon"
            
        Returns:
            True if task is due soon, False otherwise
        """
        # If task is completed or cancelled, it's not due soon
        if self.get("status") in ["completed", "cancelled"]:
            return False
        
        # If no due date, it can't be due soon
        due_date = self.get("dueDate")
        if due_date is None:
            return False
        
        # Use is_due_soon utility to check
        return is_due_soon(due_date, hours)
    
    def calculate_completion_percentage(self) -> int:
        """
        Calculates the task completion percentage based on subtasks.
        
        Returns:
            Percentage of completion (0-100)
        """
        # If task is completed, it's 100% complete
        if self.get("status") == "completed":
            return 100
        
        # If task is cancelled, it's 0% complete
        if self.get("status") == "cancelled":
            return 0
        
        # If no subtasks, calculate based on status
        subtasks = self.get("subtasks", [])
        if not subtasks:
            # Not started tasks at 0%
            if self.get("status") in ["created", "assigned"]:
                return 0
            # In progress tasks at 50%
            if self.get("status") in ["in_progress", "on_hold", "in_review"]:
                return 50
            # Default to 0%
            return 0
        
        # Calculate percentage based on subtasks
        total_subtasks = len(subtasks)
        completed_subtasks = sum(1 for st in subtasks if st.get("completed", False))
        
        # Calculate percentage
        if total_subtasks > 0:
            percentage = int((completed_subtasks / total_subtasks) * 100)
            return percentage
        
        return 0
    
    def to_dict(self) -> Dict:
        """
        Converts task to a dictionary representation.
        
        Returns:
            Dictionary representation of the task
        """
        # Get base dictionary from parent class
        task_dict = super().to_dict()
        
        # Convert ObjectId fields to strings
        for field in ["createdBy", "assigneeId", "projectId"]:
            if field in task_dict and task_dict[field]:
                task_dict[field] = str(task_dict[field])
        
        # Convert ObjectIds in lists
        if "comments" in task_dict:
            task_dict["comments"] = [str(c) for c in task_dict["comments"]]
        
        if "dependencies" in task_dict and task_dict["dependencies"]:
            for dep in task_dict["dependencies"]:
                if "taskId" in dep and dep["taskId"]:
                    dep["taskId"] = str(dep["taskId"])
        
        if "attachments" in task_dict and task_dict["attachments"]:
            for att in task_dict["attachments"]:
                if "id" in att and att["id"]:
                    att["id"] = str(att["id"])
                if "uploadedBy" in att and att["uploadedBy"]:
                    att["uploadedBy"] = str(att["uploadedBy"])
        
        if "activity" in task_dict and task_dict["activity"]:
            for act in task_dict["activity"]:
                if "userId" in act and act["userId"]:
                    act["userId"] = str(act["userId"])
        
        # Convert datetime objects to ISO format
        if "dueDate" in task_dict and task_dict["dueDate"]:
            task_dict["dueDate"] = task_dict["dueDate"].isoformat()
        
        if "metadata" in task_dict:
            for field in ["created", "lastUpdated", "completedAt"]:
                if field in task_dict["metadata"] and task_dict["metadata"][field]:
                    task_dict["metadata"][field] = task_dict["metadata"][field].isoformat()
        
        # Add calculated fields
        task_dict["completionPercentage"] = self.calculate_completion_percentage()
        task_dict["isOverdue"] = self.is_overdue()
        
        return task_dict
    
    @staticmethod
    def from_dict(data: Dict) -> 'Task':
        """
        Creates a Task instance from a dictionary.
        
        Args:
            data: Dictionary with task data
            
        Returns:
            Task instance
        """
        # Create a copy of the data to avoid modifying the input
        task_data = data.copy()
        
        # Convert string IDs to ObjectIds
        for field in ["_id", "createdBy", "assigneeId", "projectId"]:
            if field in task_data and task_data[field] and isinstance(task_data[field], str):
                task_data[field] = str_to_object_id(task_data[field])
        
        # Convert string dates to datetime objects
        if "dueDate" in task_data and task_data["dueDate"] and isinstance(task_data["dueDate"], str):
            try:
                task_data["dueDate"] = datetime.datetime.fromisoformat(task_data["dueDate"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                # If date parsing fails, remove the field
                task_data.pop("dueDate")
        
        # Convert metadata dates
        if "metadata" in task_data:
            for field in ["created", "lastUpdated", "completedAt"]:
                if field in task_data["metadata"] and isinstance(task_data["metadata"][field], str):
                    try:
                        task_data["metadata"][field] = datetime.datetime.fromisoformat(
                            task_data["metadata"][field].replace('Z', '+00:00')
                        )
                    except (ValueError, TypeError):
                        # If date parsing fails, ignore this field
                        pass
        
        # Process lists of references
        if "comments" in task_data and task_data["comments"]:
            task_data["comments"] = [
                str_to_object_id(c) if isinstance(c, str) else c
                for c in task_data["comments"]
            ]
        
        if "dependencies" in task_data and task_data["dependencies"]:
            for dep in task_data["dependencies"]:
                if "taskId" in dep and isinstance(dep["taskId"], str):
                    dep["taskId"] = str_to_object_id(dep["taskId"])
        
        if "attachments" in task_data and task_data["attachments"]:
            for att in task_data["attachments"]:
                if "id" in att and isinstance(att["id"], str):
                    att["id"] = str_to_object_id(att["id"])
                if "uploadedBy" in att and isinstance(att["uploadedBy"], str):
                    att["uploadedBy"] = str_to_object_id(att["uploadedBy"])
        
        if "activity" in task_data and task_data["activity"]:
            for act in task_data["activity"]:
                if "userId" in act and isinstance(act["userId"], str):
                    act["userId"] = str_to_object_id(act["userId"])
        
        # Create Task instance
        return Task(data=task_data, is_new=False)

    def save(self) -> bson.ObjectId:
        """
        Saves the task to the database with validation.
        
        Returns:
            ObjectId: Task ID
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate task data
        self.validate()
        
        # Determine if this is a new task or an update
        is_new = self._is_new
        
        # Update metadata
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        
        if is_new:
            # For new tasks, set created timestamp
            self._data["metadata"]["created"] = now()
        
        # Always update lastUpdated timestamp
        self._data["metadata"]["lastUpdated"] = now()
        
        # Save to database
        task_id = super().save()
        
        # Publish event
        event_type = "task.created" if is_new else "task.updated"
        event = create_event(
            event_type=event_type,
            payload={"taskId": str(task_id), "task": self.to_dict()},
            source="task_service"
        )
        
        # Start event bus if not running
        if not event_bus._running:
            event_bus.start()
        
        # Publish event
        event_bus.publish(event_type, event)
        
        logger.info(f"Task {'created' if is_new else 'updated'}: {task_id}")
        
        return task_id


def get_task_by_id(task_id: str) -> Optional[Task]:
    """
    Retrieves a task by its ID.
    
    Args:
        task_id: ID of the task to retrieve
        
    Returns:
        Task object if found, None otherwise
    """
    # Convert string ID to ObjectId if needed
    if isinstance(task_id, str):
        task_id = str_to_object_id(task_id)
    
    # Use the Task model's find_by_id method
    return Task.find_by_id(task_id)


def get_tasks_by_assignee(assignee_id: str, status: str = None) -> List[Task]:
    """
    Retrieves tasks assigned to a specific user.
    
    Args:
        assignee_id: ID of the assignee
        status: Optional status filter
        
    Returns:
        List of Task objects assigned to the user
    """
    # Convert string ID to ObjectId if needed
    if isinstance(assignee_id, str):
        assignee_id = str_to_object_id(assignee_id)
    
    # Create query filter
    query_filter = {"assigneeId": assignee_id}
    
    # Add status filter if provided
    if status:
        if status not in TASK_STATUS_CHOICES:
            raise ValidationError("Invalid status", {
                "status": f"Status must be one of: {', '.join(TASK_STATUS_CHOICES)}"
            })
        query_filter["status"] = status
    
    # Create and execute query
    query = DocumentQuery(Task).filter(query_filter).sort("dueDate")
    
    return query.execute()


def get_tasks_by_project(project_id: str, status: str = None) -> List[Task]:
    """
    Retrieves tasks belonging to a specific project.
    
    Args:
        project_id: ID of the project
        status: Optional status filter
        
    Returns:
        List of Task objects in the project
    """
    # Convert string ID to ObjectId if needed
    if isinstance(project_id, str):
        project_id = str_to_object_id(project_id)
    
    # Create query filter
    query_filter = {"projectId": project_id}
    
    # Add status filter if provided
    if status:
        if status not in TASK_STATUS_CHOICES:
            raise ValidationError("Invalid status", {
                "status": f"Status must be one of: {', '.join(TASK_STATUS_CHOICES)}"
            })
        query_filter["status"] = status
    
    # Create query and sort by priority (high to low) then due date
    query = DocumentQuery(Task).filter(query_filter).sort([
        ("priority", -1),  # -1 for descending (high priority first)
        ("dueDate", 1)     # 1 for ascending (earliest due date first)
    ])
    
    return query.execute()


def get_tasks_due_soon(hours: int = 24, assignee_id: str = None) -> List[Task]:
    """
    Retrieves tasks due within specified hours.
    
    Args:
        hours: Number of hours to consider as "soon"
        assignee_id: Optional assignee filter
        
    Returns:
        List of Task objects due soon
    """
    # Create query filter for incomplete tasks with due dates
    query_filter = {
        "status": {"$nin": ["completed", "cancelled"]},
        "dueDate": {"$ne": None}
    }
    
    # Add assignee filter if provided
    if assignee_id:
        if isinstance(assignee_id, str):
            assignee_id = str_to_object_id(assignee_id)
        query_filter["assigneeId"] = assignee_id
    
    # Query database for tasks with due dates
    tasks = DocumentQuery(Task).filter(query_filter).execute()
    
    # Filter results using is_due_soon method
    return [task for task in tasks if task.is_due_soon(hours)]


def get_overdue_tasks(assignee_id: str = None) -> List[Task]:
    """
    Retrieves tasks that are past their due date.
    
    Args:
        assignee_id: Optional assignee filter
        
    Returns:
        List of overdue Task objects
    """
    # Create query filter for incomplete tasks with due dates
    query_filter = {
        "status": {"$nin": ["completed", "cancelled"]},
        "dueDate": {"$ne": None}
    }
    
    # Add assignee filter if provided
    if assignee_id:
        if isinstance(assignee_id, str):
            assignee_id = str_to_object_id(assignee_id)
        query_filter["assigneeId"] = assignee_id
    
    # Query database for tasks with due dates
    tasks = DocumentQuery(Task).filter(query_filter).execute()
    
    # Filter results using is_overdue method
    return [task for task in tasks if task.is_overdue()]