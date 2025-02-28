"""
Initialization file for the task service test package.
Marks the tests directory as a Python package, enabling proper test discovery 
and organization. Re-exports test database setup and teardown utilities from
the common testing package.
"""

# Import database setup/teardown utilities from common testing package
from src.backend.common.testing import setup_test_db, teardown_test_db

# Define version
__version__ = "0.1.0"