"""
Initialization file for the task services module that makes the task-related service functions available to API endpoints and other components. Exposes functions for task CRUD operations, task assignment, status changes, comments, and search capabilities.
"""

# Internal imports
from .task_service import (
    create_task,
    get_task,
    update_task,
    delete_task,
    assign_task,
    update_task_status,
    add_task_subtask,
    update_task_subtask,
    delete_task_subtask,
    add_task_dependency,
    remove_task_dependency,
    get_tasks_by_user,
    get_tasks_by_project_id,
    get_tasks_due_soon,
    get_overdue_tasks,
    search_tasks_with_criteria,
)  # Import task management core functionality
from .comment_service import (
    create_comment,
    get_comment,
    get_comments_for_task,
    update_comment,
    delete_comment,
    get_comment_count,
    is_mentioned_in_comment,
)  # Import task comment functionality
from .search_service import search_tasks, count_tasks  # Import task search functionality

# Export task management functions
__all__ = [
    "create_task",  # Create a new task with permissions
    "get_task",  # Retrieve a task by ID
    "update_task",  # Update an existing task
    "delete_task",  # Delete (soft delete) a task
    "assign_task",  # Assign a task to a user
    "update_task_status",  # Update a task's status
    "add_task_subtask",  # Add a subtask to a task
    "update_task_subtask",  # Update a subtask
    "delete_task_subtask",  # Delete a subtask
    "add_task_dependency",  # Add a dependency between tasks
    "remove_task_dependency",  # Remove a dependency between tasks
    "get_tasks_by_user",  # Get tasks assigned to a user
    "get_tasks_by_project_id",  # Get tasks in a project
    "get_tasks_due_soon",  # Get tasks due within specified hours
    "get_overdue_tasks",  # Get overdue tasks
    "search_tasks_with_criteria",  # Search tasks with multiple criteria
    "search_tasks",  # Low-level search function for tasks
    "count_tasks",  # Count tasks matching criteria
    "create_comment",  # Create a comment on a task
    "get_comment",  # Get a specific comment
    "get_comments_for_task",  # Get all comments for a task
    "update_comment",  # Update a comment
    "delete_comment",  # Delete a comment
    "get_comment_count",  # Get number of comments for a task
    "is_mentioned_in_comment",  # Check if a user is mentioned in a comment
]