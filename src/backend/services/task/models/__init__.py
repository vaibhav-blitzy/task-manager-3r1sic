"""
Initializes the task models package and exposes key model classes and functions for easier imports.
Makes Task and Comment models and related utility functions available for importing directly from the models package.
"""

# Import Task model and related functions
from .task import Task, get_task_by_id, get_tasks_by_assignee, get_tasks_by_project, get_tasks_due_soon, get_overdue_tasks # Importing Task model and related functions from task.py

# Import Comment model and related functions
from .comment import Comment, get_task_comments, count_task_comments # Importing Comment model and related functions from comment.py

__all__ = ["Task", "Comment", "get_task_by_id", "get_tasks_by_assignee", "get_tasks_by_project", "get_tasks_due_soon", "get_overdue_tasks", "get_task_comments", "count_task_comments"] # Defining the public API of the models package