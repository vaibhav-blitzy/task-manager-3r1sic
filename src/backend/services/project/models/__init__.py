"""
Project models package for the Task Management System.

This package provides models and utilities for managing projects, project memberships,
and their relationships within the Task Management System.

Models:
    Project: MongoDB document model for projects with team management capabilities
    ProjectMember: MongoDB document model for project membership with role-based access

Utilities:
    get_project_by_id: Retrieves a project by its ID
    get_projects_by_user: Retrieves projects accessible to a user
    get_member_by_id: Retrieves a project member by its ID
    get_member_by_user_and_project: Retrieves a specific project membership
    get_members_by_project: Retrieves all members of a project

Constants:
    PROJECT_STATUS_CHOICES: Valid status values for projects
    ProjectRole: Enumeration of project role types
"""

# Import from project.py
from .project import (
    Project,
    get_project_by_id,
    get_projects_by_user,
    PROJECT_STATUS_CHOICES
)

# Import from member.py
from .member import (
    ProjectMember,
    ProjectRole,
    get_member_by_id,
    get_member_by_user_and_project,
    get_members_by_project
)

# Export all imported models and functions
__all__ = [
    'Project',
    'get_project_by_id',
    'get_projects_by_user',
    'PROJECT_STATUS_CHOICES',
    'ProjectMember',
    'ProjectRole',
    'get_member_by_id',
    'get_member_by_user_and_project',
    'get_members_by_project'
]