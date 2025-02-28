"""
Service layer for project management functionality, providing CRUD operations,
team membership management, and business logic for project organization within
the Task Management System.
"""

# Standard library imports
import typing
from typing import List, Dict, Optional, Tuple, Any

# Third-party imports
import bson
from bson.objectid import ObjectId  # pymongo v4.3.x
import requests  # 2.28.x

# Internal imports
from src.backend.services.project.models.project import (
    Project,
    PROJECT_STATUS_CHOICES,
    get_project_by_id,
)  # Project model and related project retrieval function
from src.backend.services.project.services.member_service import (
    MemberService,
)  # Service for managing project members and membership operations
from src.backend.services.project.models.member import (
    ProjectRole,
)  # Project role enumeration for role-based access control
from src.backend.common.exceptions.api_exceptions import (
    ValidationError,
    NotFoundError,
    AuthorizationError,
    ConflictError,
)  # Exception classes for error handling
from src.backend.common.database.mongo.connection import (
    get_db,
)  # Database connection utility
from src.backend.common.events.event_bus import (
    get_event_bus_instance,
    create_event,
)  # Event publishing for real-time updates
from src.backend.common.auth.permissions import (
    has_permission,
    is_resource_owner,
)  # Permission checking utilities
from src.backend.common.schemas.pagination import (
    get_pagination_params,
)  # Pagination utilities for listing projects
from src.backend.common.logging.logger import get_logger  # Logging functionality
from src.backend.common.utils.validators import (
    validate_object_id,
    validate_required,
)  # Input validation utilities
from src.backend.common.utils.datetime import utcnow  # Datetime utility for timestamps

# Initialize logger
logger = get_logger(__name__)

# Get event bus
event_bus = get_event_bus_instance()


class ProjectService:
    """
    Service class that implements business logic for project management,
    including CRUD operations, team management, and project organization
    """

    def __init__(self):
        """Initialize the ProjectService with required dependencies"""
        # Get database connection using get_db()
        self.db = get_db()

        # Initialize member_service as a new instance of MemberService
        self.member_service = MemberService()

        # Initialize event_bus using get_event_bus_instance()
        self.event_bus = get_event_bus_instance()

        # Set up logger for the service
        logger.debug("ProjectService initialized")

    def create_project(self, project_data: Dict, user_id: str) -> Dict:
        """
        Creates a new project with the provided data

        Args:
            project_data (dict): Project data
            user_id (str): ID of the user creating the project

        Returns:
            dict: Created project with ID and metadata
        """
        # Validate required fields in project_data (name, description, etc.)
        validate_required(project_data, ["name", "description"])

        # Check if user has permission to create projects
        if not has_permission({"id": user_id}, "project:create"):
            raise AuthorizationError(message="You do not have permission to create projects")

        # Set metadata fields (created_at, updated_at, owner_id)
        project_data["metadata"] = {
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        project_data["owner_id"] = ObjectId(user_id)

        # Set default status to 'planning'
        project_data["status"] = "planning"

        # Create new Project instance
        project = Project(data=project_data)

        # Save project to database
        project.save()

        # Add creator as project member with ADMIN role using member_service
        self.member_service.add_project_member(
            project_id=str(project.get_id()), user_id=user_id, role="admin", added_by=user_id
        )

        # Publish project.created event with project details
        event = create_event(
            event_type="project.created",
            payload={
                "project_id": str(project.get_id()),
                "name": project.get("name"),
                "owner_id": user_id,
                "status": project.get("status"),
            },
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log project creation
        logger.info(f"Project created with ID: {project.get_id()}")

        # Return created project as dictionary
        return project.to_dict()

    def get_project(self, project_id: str, user_id: str) -> Dict:
        """
        Retrieves a project by its ID

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user requesting the project

        Returns:
            dict: Project data if found and user has access
        """
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Get project using get_project_by_id function
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to view project (is owner or member)
        if not has_permission({"id": user_id}, "project:view", project._data):
            raise AuthorizationError(message="You do not have permission to view this project")

        # Convert project object to dictionary
        project_data = project.to_dict()

        # Return project data
        return project_data

    def update_project(self, project_id: str, project_data: Dict, user_id: str) -> Dict:
        """
        Updates an existing project with the provided data

        Args:
            project_id (str): ID of the project
            project_data (dict): Data to update the project with
            user_id (str): ID of the user updating the project

        Returns:
            dict: Updated project data
        """
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Get existing project
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to update project
        if not has_permission({"id": user_id}, "project:update", project._data):
            raise AuthorizationError(message="You do not have permission to update this project")

        # Update allowed fields (name, description, status, category, etc.)
        for key, value in project_data.items():
            if key in ["name", "description", "status", "category", "tags"]:
                project._data[key] = value

        # If status change requested, validate status transition
        if "status" in project_data:
            project.update_status(project_data["status"])

        # Update metadata (updated_at timestamp)
        project._data["metadata"]["updated_at"] = utcnow()

        # Save updated project to database
        project.save()

        # Publish project.updated event
        event = create_event(
            event_type="project.updated",
            payload={
                "project_id": project_id,
                "name": project.get("name"),
                "owner_id": project.get("owner_id"),
                "status": project.get("status"),
            },
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log project update
        logger.info(f"Project updated with ID: {project_id}")

        # Return updated project as dictionary
        return project.to_dict()

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """
        Soft deletes a project by setting status to 'archived'

        Args:
            project_id (str): ID of the project
            user_id (str): ID of the user deleting the project

        Returns:
            bool: True if project was successfully deleted
        """
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Get existing project
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to delete project
        if not has_permission({"id": user_id}, "project:delete", project._data):
            raise AuthorizationError(message="You do not have permission to delete this project")

        # Change project status to 'archived'
        project._data["status"] = "archived"

        # Update metadata (updated_at timestamp)
        project._data["metadata"]["updated_at"] = utcnow()

        # Save updated project to database
        project.save()

        # Publish project.deleted event
        event = create_event(
            event_type="project.deleted",
            payload={"project_id": project_id, "owner_id": project.get("owner_id")},
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log project deletion
        logger.info(f"Project deleted with ID: {project_id}")

        # Return success status (True)
        return True

    def list_projects(self, user_id: str, filters: Dict, page: int, per_page: int) -> Dict:
        """
        Lists projects with optional filtering and pagination

        Args:
            user_id (str): ID of the user requesting the list
            filters (dict): Filters to apply to the project list
            page (int): Page number for pagination
            per_page (int): Number of projects per page

        Returns:
            dict: Paginated projects data with metadata
        """
        # Validate user_id format
        validate_object_id(user_id, "user_id")

        # Get pagination parameters (skip, limit) using get_pagination_params
        pagination_params = get_pagination_params({"page": page, "per_page": per_page})
        skip = pagination_params.get_skip()
        limit = pagination_params.get_limit()

        # Get projects where user is a member using member_service.get_user_projects
        project_ids = self.member_service.get_user_projects(user_id)

        # If no projects found, return empty result with pagination metadata
        if not project_ids:
            return {
                "items": [],
                "metadata": {
                    "page": page,
                    "per_page": per_page,
                    "total": 0,
                    "total_pages": 0,
                    "next_page": None,
                    "prev_page": None,
                },
            }

        # Build query filter based on project IDs and additional filters
        query = {"_id": {"$in": [ObjectId(project_id) for project_id in project_ids]}}
        if filters:
            query.update(filters)

        # Query database for projects matching filters with pagination
        projects = Project.find(query=query, skip=skip, limit=limit)

        # Calculate total projects count
        total = Project.count(query=query)

        # Convert project objects to dictionaries
        project_list = [project.to_dict() for project in projects]

        # Construct and return result with projects and pagination metadata
        return {
            "items": project_list,
            "metadata": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "next_page": page + 1 if page * per_page < total else None,
                "prev_page": page - 1 if page > 1 else None,
            },
        }

    def add_member(self, project_id: str, user_id: str, member_id: str, role: str) -> Dict:
        """Adds a user to a project with specified role"""
        return self.member_service.add_project_member(project_id, user_id, member_id, role)

    def remove_member(self, project_id: str, user_id: str, member_id: str) -> bool:
        """Removes a user from a project"""
        return self.member_service.remove_project_member(project_id, user_id, member_id)

    def update_member_role(self, project_id: str, user_id: str, member_id: str, new_role: str) -> Dict:
        """Updates the role of a project member"""
        return self.member_service.update_member_role(project_id, user_id, member_id, new_role)

    def get_members(self, project_id: str, user_id: str, filters: Dict, page: int, per_page: int) -> Dict:
        """Gets all members of a project"""
        members, total = self.member_service.get_project_members(project_id, filters, page, per_page)
        return {
            "items": members,
            "metadata": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "next_page": page + 1 if page * per_page < total else None,
                "prev_page": page - 1 if page > 1 else None,
            },
        }

    def add_task_list(self, project_id: str, user_id: str, name: str, description: str) -> Dict:
        """Adds a new task list to a project"""
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Validate name is not empty
        validate_required({"name": name}, ["name"])

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to update project
        if not has_permission({"id": user_id}, "project:update", project._data):
            raise AuthorizationError(message="You do not have permission to update this project")

        # Call project.add_task_list method to add task list
        task_list = project.add_task_list(name, description)

        # Save updated project to database
        project.save()

        # Publish project.tasklist.added event
        event = create_event(
            event_type="project.tasklist.added",
            payload={"project_id": project_id, "task_list_id": task_list["id"], "name": name},
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log task list addition
        logger.info(f"Task list added to project {project_id} with name {name}")

        # Return created task list information
        return task_list

    def update_task_list(self, project_id: str, user_id: str, task_list_id: str, task_list_data: Dict) -> Dict:
        """Updates an existing task list in a project"""
        # Validate project_id and task_list_id format
        validate_object_id(project_id, "project_id")
        validate_object_id(task_list_id, "task_list_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to update project
        if not has_permission({"id": user_id}, "project:update", project._data):
            raise AuthorizationError(message="You do not have permission to update this project")

        # Call project.update_task_list method to update task list
        task_list = project.update_task_list(task_list_id, task_list_data)

        # If task list not found, raise NotFoundError
        if not task_list:
            raise NotFoundError(
                message="Task list not found", resource_type="task_list", resource_id=task_list_id
            )

        # Save updated project to database
        project.save()

        # Publish project.tasklist.updated event
        event = create_event(
            event_type="project.tasklist.updated",
            payload={"project_id": project_id, "task_list_id": task_list_id, "name": task_list["name"]},
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log task list update
        logger.info(f"Task list updated in project {project_id} with ID {task_list_id}")

        # Return updated task list information
        return task_list

    def remove_task_list(self, project_id: str, user_id: str, task_list_id: str) -> bool:
        """Removes a task list from a project"""
        # Validate project_id and task_list_id format
        validate_object_id(project_id, "project_id")
        validate_object_id(task_list_id, "task_list_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to update project
        if not has_permission({"id": user_id}, "project:update", project._data):
            raise AuthorizationError(message="You do not have permission to update this project")

        # Call project.remove_task_list method to remove task list
        removed = project.remove_task_list(task_list_id)

        # If task list not found, raise NotFoundError
        if not removed:
            raise NotFoundError(
                message="Task list not found", resource_type="task_list", resource_id=task_list_id
            )

        # Save updated project to database
        project.save()

        # Publish project.tasklist.removed event
        event = create_event(
            event_type="project.tasklist.removed",
            payload={"project_id": project_id, "task_list_id": task_list_id},
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log task list removal
        logger.info(f"Task list removed from project {project_id} with ID {task_list_id}")

        # Return success status (True)
        return removed

    def update_settings(self, project_id: str, user_id: str, settings: Dict) -> Dict:
        """Updates project settings"""
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to update project settings
        if not has_permission({"id": user_id}, "project:update", project._data):
            raise AuthorizationError(message="You do not have permission to update this project settings")

        # Call project.update_settings method to update settings
        project.update_settings(settings)

        # Save updated project to database
        project.save()

        # Publish project.settings.updated event
        event = create_event(
            event_type="project.settings.updated",
            payload={"project_id": project_id, "settings": settings},
            source="project_service",
        )
        self.event_bus.publish(event["type"], event)

        # Log settings update
        logger.info(f"Settings updated for project {project_id}")

        # Return updated project settings
        return project.get("settings")

    def get_project_stats(self, project_id: str, user_id: str) -> Dict:
        """Gets statistics for a project including task counts and completion rates"""
        # Validate project_id format
        validate_object_id(project_id, "project_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user has permission to view project
        if not has_permission({"id": user_id}, "project:view", project._data):
            raise AuthorizationError(message="You do not have permission to view this project")

        # Get tasks associated with project from task service
        # (Implementation depends on how task service is accessed)
        # For example, using a direct HTTP request:
        # tasks = requests.get(f"http://task-service/tasks?project_id={project_id}").json()
        # For now, we'll just return dummy data
        tasks = []

        # Calculate task stats (count by status, completion rate, etc.)
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        # Calculate member activity statistics
        # (Implementation depends on how activity is tracked)
        member_activity = {}

        # Get project completion percentage
        completion_percentage = project.calculate_completion_percentage()

        # Compile all statistics into result dictionary
        project_stats = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "member_activity": member_activity,
            "completion_percentage": completion_percentage,
        }

        # Log statistics retrieval
        logger.info(f"Statistics retrieved for project {project_id}")

        # Return project statistics
        return project_stats

    def search_projects(self, query: str, user_id: str, filters: Dict, page: int, per_page: int) -> Dict:
        """Searches for projects by text query with filtering"""
        # Validate user_id format
        validate_object_id(user_id, "user_id")

        # Get pagination parameters using get_pagination_params
        pagination_params = get_pagination_params({"page": page, "per_page": per_page})
        skip = pagination_params.get_skip()
        limit = pagination_params.get_limit()

        # Get projects where user is a member using member_service
        project_ids = self.member_service.get_user_projects(user_id)

        # Build text search query with project IDs and filters
        search_query = {"_id": {"$in": [ObjectId(project_id) for project_id in project_ids]}}
        if filters:
            search_query.update(filters)

        # Execute search query with pagination
        projects = Project.search_projects(query, user_id, search_query, skip, limit)

        # Calculate total matching projects count
        total = Project.count(query=search_query)

        # Convert project objects to dictionaries
        project_list = [project.to_dict() for project in projects]

        # Construct and return result with projects and pagination metadata
        return {
            "items": project_list,
            "metadata": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "next_page": page + 1 if page * per_page < total else None,
                "prev_page": page - 1 if page > 1 else None,
            },
        }

    def check_user_permission(self, project_id: str, user_id: str, permission: str) -> bool:
        """Checks if a user has a specific permission in a project"""
        # Validate project_id and user_id format
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user is the project owner
        if project.get("owner_id") == user_id:
            return True

        # Delegate to member_service.check_member_permission
        return self.member_service.check_member_permission(project_id, user_id, permission)

    def get_user_role(self, project_id: str, user_id: str) -> str:
        """Gets the role of a user in a project"""
        # Validate project_id and user_id format
        validate_object_id(project_id, "project_id")
        validate_object_id(user_id, "user_id")

        # Get project to verify it exists
        project = get_project_by_id(project_id)

        # If project not found, raise NotFoundError
        if not project:
            raise NotFoundError(message="Project not found", resource_type="project", resource_id=project_id)

        # Check if user is the project owner
        if project.get("owner_id") == user_id:
            return "owner"

        # Get member information from database
        member = self.member_service.get_member_by_user_and_project(user_id, project_id)

        # If member found, return role
        if member:
            return member.role

        # If not found, return None
        return None