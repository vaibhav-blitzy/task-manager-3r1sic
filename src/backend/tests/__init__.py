"""
Initialization file for the backend test package that defines common imports, constants,
and configuration for all test modules in the Task Management System.
Provides centralized test utilities and establishes the testing environment.
"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import pytest

# Set up paths
TEST_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = TEST_DIR.parent

# Define testing environment constants
TEST_ENV = os.environ.get('TEST_ENV', 'unit')  # Can be 'unit' or 'integration'
TEST_DB_NAME = "task_management_test"
USE_MOCK_DB = TEST_ENV != 'integration'
USE_MOCK_REDIS = TEST_ENV != 'integration'

# Import testing configuration
from ..common.config.testing import TESTING_CONFIG

# Import mock implementations for testing
from ..common.testing.mocks import MockDatabase, MockRedis, MockJWTUtil

# Import test data generation functions
from ..common.testing.fixtures import create_test_user, create_test_project, create_test_task


def setup_test_environment():
    """
    Configures the Python environment for running tests.
    
    This function sets up necessary paths, environment variables, and
    initializes test dependencies.
    """
    # Ensure project root is in path
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # Set testing environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Configure pytest to use the correct settings
    pytest.register_assert_rewrite('src.backend.tests.assertions')
    
    # Set up logging configuration for tests
    import logging
    logging.basicConfig(level=logging.INFO)


# Run setup when the package is imported
setup_test_environment()