"""
Initialization file for the Project Management service that exports key components and defines the service version.
"""

# Import the Project model for external use
from .models.project import Project
# Import the Member model for external use
from .models.member import Member
# Import the ProjectService for external use
from .services.project_service import ProjectService
# Import the MemberService for external use
from .services.member_service import MemberService
# Import the projects API blueprint for Flask registration
from .api.projects import projects_blueprint
# Import the members API blueprint for Flask registration
from .api.members import members_blueprint

# Define service version for version tracking and compatibility checks
__version__ = "1.0.0"

# Export service version for version tracking and compatibility checks
__all__ = [
    "__version__",
    "Project",
    "Member",
    "ProjectService",
    "MemberService",
    "projects_blueprint",
    "members_blueprint",
]