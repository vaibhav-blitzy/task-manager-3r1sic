"""
Initializes the common testing package, making testing utilities, fixtures, and mocks available for import.
Centralizes testing components to provide a consistent testing approach across all microservices
in the Task Management System.
"""

# Define global constants
TEST_DB_NAME = "task_management_test"

# Import fixtures
from .fixtures import (
    pytest_mongodb,
    pytest_redis,
    app_client,
    authenticated_client,
    mock_auth_middleware,
    test_user,
    test_admin,
    test_project,
    test_task,
    clean_db,
    create_test_user,
    create_test_project,
    create_test_task,
    setup_flask_app
)

# Import mocks
from .mocks import (
    MockDatabase,
    MockMongoClient,
    MockRedis,
    MockJWTUtil,
    create_mock_collection,
    patch_auth_middleware,
    patch_permissions
)