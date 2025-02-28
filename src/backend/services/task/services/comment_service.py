"""
Service layer implementation for comment management in the Task Management System.
Handles the business logic for creating, retrieving, updating, and deleting comments on tasks,
enforcing permissions, validating input, and triggering appropriate events.
"""

# Standard library imports
import typing
from typing import Dict, List, Any, Optional, Union

# Third-party imports
import bson  # pymongo v4.3.3
from datetime import datetime  # standard library

# Internal imports
from ..models.comment import Comment  # Core data model for comment entities
from ..models.comment import get_task_comments  # Helper function to retrieve comments for a specific task
from ..models.comment import count_task_comments  # Helper function to count comments for a specific task
from ..models.task import Task  # Task model to associate comments with tasks
from ..models.task import get_task_by_id  # Helper function to retrieve a task by ID
from ...common.events.event_bus import get_event_bus_instance  # Access the event bus for publishing comment events
from ...common.events.event_bus import create_event  # Create standardized event objects
from ...common.exceptions.api_exceptions import NotFoundError  # Exception for comment or task not found
from ...common.exceptions.api_exceptions import ValidationError  # Exception for invalid comment data
from ...common.exceptions.api_exceptions import AuthorizationError  # Exception for unauthorized operations
from ...common.auth.permissions import has_permission  # Check if user has permission for an action
from ...common.auth.permissions import is_resource_owner  # Check if user owns a resource
from ...common.auth.permissions import ResourceType  # Enum of resource types for permission checks
from ...common.logging.logger import get_logger  # Get logger for comment service

# Initialize logger
logger = get_logger(__name__)

# Get event bus instance
event_bus = get_event_bus_instance()


def create_comment(task_id: str, user_id: str, content: str) -> Dict:
    """
    Creates a new comment on a task with permission validation.

    Args:
        task_id: ID of the task to comment on
        user_id: ID of the user creating the comment
        content: Comment content

    Returns:
        Created comment data as dictionary

    Raises:
        ValidationError: If task_id, user_id, or content is invalid
        NotFoundError: If task does not exist
        AuthorizationError: If user does not have permission to comment
    """
    # Validate task_id and user_id are provided
    if not task_id:
        raise ValidationError("Task ID is required", {"task_id": "Task ID is required"})
    if not user_id:
        raise ValidationError("User ID is required", {"user_id": "User ID is required"})

    # Validate content is not empty and within length limits
    if not content or not content.strip():
        raise ValidationError("Comment content is required", {"content": "Comment content is required"})

    # Check if task exists using get_task_by_id, raise NotFoundError if not found
    task = get_task_by_id(task_id)
    if not task:
        raise NotFoundError(f"Task with ID '{task_id}' not found", resource_type="Task", resource_id=task_id)

    # Check if user has permission to comment on tasks using has_permission
    user_data = {"id": user_id}  # Minimal user data for permission check
    if not has_permission(user_data, Permission.COMMENT_CREATE.value, resource={"task_id": task_id}):
        raise AuthorizationError("You do not have permission to comment on this task",
                                 required_permission=Permission.COMMENT_CREATE.value)

    # Create Comment object using Comment.from_task_user with task_id, user_id, and content
    comment = Comment.from_task_user(task_id=task_id, user_id=user_id, content=content)

    # Save the comment to the database
    comment.save()

    # Update task to include comment reference using add_comment_reference
    task.add_comment_reference(comment.get_id())
    task.save()

    # Create comment.created event with task and comment details
    event = create_event(
        event_type="comment.created",
        payload={"task_id": task_id, "comment": comment.to_dict()},
        source="comment_service"
    )

    # Publish event to event bus for notifications and real-time updates
    event_bus.publish("comment.created", event)

    # Log successful comment creation
    logger.info(f"Comment created on task {task_id} by user {user_id}")

    # Return the created comment as a dictionary using to_dict()
    return comment.to_dict()


def get_comment(comment_id: str, user_id: str) -> Dict:
    """
    Retrieves a comment by ID with permission validation.

    Args:
        comment_id: ID of the comment to retrieve
        user_id: ID of the user requesting the comment

    Returns:
        Comment data as dictionary

    Raises:
        ValidationError: If comment_id is invalid
        NotFoundError: If comment does not exist
        AuthorizationError: If user does not have permission to view the comment
    """
    # Validate comment_id is provided
    if not comment_id:
        raise ValidationError("Comment ID is required", {"comment_id": "Comment ID is required"})

    # Attempt to find comment by ID, raise NotFoundError if not found
    comment = Comment.find_by_id(comment_id)
    if not comment:
        raise NotFoundError(f"Comment with ID '{comment_id}' not found", resource_type="Comment",
                            resource_id=comment_id)

    # Check if user has permission to view the comment
    user_data = {"id": user_id}  # Minimal user data for permission check
    if not has_permission(user_data, Permission.COMMENT_VIEW.value, resource={"comment_id": comment_id}):
        raise AuthorizationError("You do not have permission to view this comment",
                                 required_permission=Permission.COMMENT_VIEW.value)

    # Return the comment as a dictionary using to_dict()
    return comment.to_dict()


def get_comments_for_task(task_id: str, user: Dict, limit: int = 10, skip: int = 0, sort_by: str = "created_at",
                          sort_order: str = "desc") -> Dict:
    """
    Retrieves comments for a specific task with pagination and ordering.

    Args:
        task_id: ID of the task to retrieve comments for
        user: User dictionary for permission check
        limit: Maximum number of comments to return (default: 10)
        skip: Number of comments to skip for pagination (default: 0)
        sort_by: Field to sort comments by (default: "created_at")
        sort_order: Sort order ("asc" or "desc", default: "desc")

    Returns:
        Paginated comments data with metadata

    Raises:
        ValidationError: If task_id is invalid or pagination parameters are invalid
        NotFoundError: If task does not exist
        AuthorizationError: If user does not have permission to view the task's comments
    """
    # Validate task_id is provided
    if not task_id:
        raise ValidationError("Task ID is required", {"task_id": "Task ID is required"})

    # Check if task exists using get_task_by_id, raise NotFoundError if not found
    task = get_task_by_id(task_id)
    if not task:
        raise NotFoundError(f"Task with ID '{task_id}' not found", resource_type="Task", resource_id=task_id)

    # Check if user has permission to view the task's comments
    if not has_permission(user, Permission.COMMENT_VIEW.value, resource={"task_id": task_id}):
        raise AuthorizationError("You do not have permission to view comments for this task",
                                 required_permission=Permission.COMMENT_VIEW.value)

    # Set default values for pagination parameters if not provided
    limit = limit if limit is not None else 10
    skip = skip if skip is not None else 0

    # Validate pagination parameters
    if not isinstance(limit, int) or limit < 0:
        raise ValidationError("Invalid limit", {"limit": "Limit must be a non-negative integer"})
    if not isinstance(skip, int) or skip < 0:
        raise ValidationError("Invalid skip", {"skip": "Skip must be a non-negative integer"})

    # Validate sort parameters
    if sort_by not in ["created_at", "updated_at"]:
        raise ValidationError("Invalid sort_by", {"sort_by": "Sort_by must be 'created_at' or 'updated_at'"})
    if sort_order not in ["asc", "desc"]:
        raise ValidationError("Invalid sort_order", {"sort_order": "Sort_order must be 'asc' or 'desc'"})

    # Determine sort direction
    sort_direction = 1 if sort_order == "asc" else -1

    # Retrieve comments using get_task_comments function with filtering and sorting
    comments = get_task_comments(task_id=task_id, limit=limit, skip=skip)

    # Count total comments for pagination metadata using count_task_comments
    total_comments = count_task_comments(task_id=task_id)

    # Convert comment objects to dictionaries
    comment_list = [comment.to_dict() for comment in comments]

    # Create and return response object with comments array and pagination metadata
    response = {
        "comments": comment_list,
        "total": total_comments,
        "limit": limit,
        "skip": skip
    }
    return response


def update_comment(comment_id: str, user_id: str, new_content: str) -> Dict:
    """
    Updates an existing comment with new content and permission validation.

    Args:
        comment_id: ID of the comment to update
        user_id: ID of the user requesting the update
        new_content: New content for the comment

    Returns:
        Updated comment data as dictionary

    Raises:
        ValidationError: If comment_id or new_content is invalid
        NotFoundError: If comment does not exist
        AuthorizationError: If user does not have permission to update the comment
    """
    # Validate comment_id and new_content are provided
    if not comment_id:
        raise ValidationError("Comment ID is required", {"comment_id": "Comment ID is required"})
    if not new_content or not new_content.strip():
        raise ValidationError("New content is required", {"new_content": "New content is required"})

    # Attempt to find comment by ID, raise NotFoundError if not found
    comment = Comment.find_by_id(comment_id)
    if not comment:
        raise NotFoundError(f"Comment with ID '{comment_id}' not found", resource_type="Comment",
                            resource_id=comment_id)

    # Check if user is the comment owner or has update permission
    user_data = {"id": user_id}  # Minimal user data for permission check
    if not is_resource_owner(user_data, comment.to_dict()) and not has_permission(user_data,
                                                                                   Permission.COMMENT_UPDATE.value,
                                                                                   resource={"comment_id": comment_id}):
        raise AuthorizationError("You do not have permission to update this comment",
                                 required_permission=Permission.COMMENT_UPDATE.value)

    # Update comment content using update_content method
    comment.update_content(new_content)

    # Save the updated comment to the database
    comment.save()

    # Create comment.updated event with task and comment details
    event = create_event(
        event_type="comment.updated",
        payload={"task_id": comment.get("task_id"), "comment": comment.to_dict()},
        source="comment_service"
    )

    # Publish event to event bus for notifications and real-time updates
    event_bus.publish("comment.updated", event)

    # Log successful comment update
    logger.info(f"Comment {comment_id} updated by user {user_id}")

    # Return the updated comment as a dictionary using to_dict()
    return comment.to_dict()


def delete_comment(comment_id: str, user_id: str) -> bool:
    """
    Deletes a comment with permission validation.

    Args:
        comment_id: ID of the comment to delete
        user_id: ID of the user requesting the deletion

    Returns:
        True if deletion was successful

    Raises:
        ValidationError: If comment_id is invalid
        NotFoundError: If comment does not exist
        AuthorizationError: If user does not have permission to delete the comment
    """
    # Validate comment_id is provided
    if not comment_id:
        raise ValidationError("Comment ID is required", {"comment_id": "Comment ID is required"})

    # Attempt to find comment by ID, raise NotFoundError if not found
    comment = Comment.find_by_id(comment_id)
    if not comment:
        raise NotFoundError(f"Comment with ID '{comment_id}' not found", resource_type="Comment",
                            resource_id=comment_id)

    # Check if user is the comment owner or has delete permission
    user_data = {"id": user_id}  # Minimal user data for permission check
    if not is_resource_owner(user_data, comment.to_dict()) and not has_permission(user_data,
                                                                                   Permission.COMMENT_DELETE.value,
                                                                                   resource={"comment_id": comment_id}):
        raise AuthorizationError("You do not have permission to delete this comment",
                                 required_permission=Permission.COMMENT_DELETE.value)

    # Get task ID from comment for event publishing
    task_id = comment.get("task_id")

    # Perform deletion by removing the comment from database
    comment.delete()

    # Create comment.deleted event with task and comment details
    event = create_event(
        event_type="comment.deleted",
        payload={"task_id": task_id, "comment": comment.to_dict()},
        source="comment_service"
    )

    # Publish event to event bus for notifications and real-time updates
    event_bus.publish("comment.deleted", event)

    # Log successful comment deletion
    logger.info(f"Comment {comment_id} deleted by user {user_id}")

    # Return True indicating successful deletion
    return True


def get_comment_count(task_id: str, user: Dict) -> Dict:
    """
    Gets the count of comments for a specific task.

    Args:
        task_id: ID of the task to count comments for
        user: User dictionary for permission check

    Returns:
        Object containing comment count

    Raises:
        ValidationError: If task_id is invalid
        NotFoundError: If task does not exist
        AuthorizationError: If user does not have permission to view the task's comments
    """
    # Validate task_id is provided
    if not task_id:
        raise ValidationError("Task ID is required", {"task_id": "Task ID is required"})

    # Check if task exists using get_task_by_id, raise NotFoundError if not found
    task = get_task_by_id(task_id)
    if not task:
        raise NotFoundError(f"Task with ID '{task_id}' not found", resource_type="Task", resource_id=task_id)

    # Check if user has permission to view the task's comments
    if not has_permission(user, Permission.COMMENT_VIEW.value, resource={"task_id": task_id}):
        raise AuthorizationError("You do not have permission to view comments for this task",
                                 required_permission=Permission.COMMENT_VIEW.value)

    # Get count using count_task_comments function
    count = count_task_comments(task_id=task_id)

    # Return dictionary with count value
    return {"count": count}


def process_comment_mentions(comment: Comment, task: Task) -> None:
    """
    Processes user mentions in a comment and triggers notification events.

    Args:
        comment: Comment object
        task: Task object

    Returns:
        None
    """
    # Check if comment has mentions using has_mentions method
    if not comment.has_mentions():
        return

    # Extract mentioned usernames using get_mentions method
    mentioned_usernames = comment.get_mentions()

    # For each mentioned username, create a mention event
    for username in mentioned_usernames:
        event = create_event(
            event_type="comment.mention",
            payload={
                "task_id": task.get_id_str(),
                "comment_id": comment.get_id_str(),
                "mentioned_user": username
            },
            source="comment_service"
        )

        # Publish mention events to the event bus for notification processing
        event_bus.publish("comment.mention", event)

    # Log the mention processing completion
    logger.info(f"Processed mentions in comment {comment.get_id_str()} on task {task.get_id_str()}")