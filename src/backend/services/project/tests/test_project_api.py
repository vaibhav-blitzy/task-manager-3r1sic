"""
Unit tests for the project service API endpoints, including tests for project creation,
retrieval, updating, deletion, task list management, and project settings management.
"""
import json
import pytest
from unittest import mock
from bson import ObjectId

from src.backend.services.project.models.project import PROJECT_STATUS_CHOICES


def test_create_project_success(projects_api_client, project_data, test_user, mock_event_bus):
    """Test successful project creation with valid data"""
    # Make POST request to /api/v1/projects with project_data
    response = projects_api_client.post("/api/v1/projects", json=project_data)

    # Assert response status code is 201 (Created)
    assert response.status_code == 201

    # Assert response JSON contains expected project data
    response_data = response.get_json()
    assert response_data["name"] == project_data["name"]
    assert response_data["description"] == project_data["description"]
    assert response_data["status"] == "planning"  # Default status
    assert response_data["category"] == project_data["category"]

    # Assert owner_id in response matches test_user id
    assert response_data["owner_id"] == test_user["_id"]

    # Assert project was saved to database
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.created event
    mock_event_bus.publish.assert_called_with(
        "project.created",
        mock.ANY  # Check that it was called with some event
    )


def test_create_project_validation_error(projects_api_client):
    """Test project creation with invalid data returns validation error"""
    # Create invalid project data (missing required fields)
    invalid_data = {"description": "This is a test project"}

    # Make POST request to /api/v1/projects with invalid data
    response = projects_api_client.post("/api/v1/projects", json=invalid_data)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert response contains validation error message
    response_data = response.get_json()
    assert "message" in response_data
    assert "errors" in response_data
    assert "name" in response_data["errors"]

    # Assert project was not saved to database
    # (Verification depends on how the database is mocked)


def test_get_project_success(projects_api_client, test_project):
    """Test successful retrieval of a project by ID"""
    # Make GET request to /api/v1/projects/{project_id}
    response = projects_api_client.get(f"/api/v1/projects/{test_project.get_id()}")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response JSON contains expected project data
    response_data = response.get_json()
    assert response_data["name"] == test_project.get("name")
    assert response_data["description"] == test_project.get("description")
    assert response_data["status"] == test_project.get("status")

    # Assert project ID in response matches test_project id
    assert response_data["_id"] == test_project.get_id_str()


def test_get_project_not_found(projects_api_client):
    """Test project retrieval with non-existent ID returns not found error"""
    # Create a non-existent project ID
    nonexistent_id = "60d1b7e9a7b3c40000d4e2f0"

    # Make GET request to /api/v1/projects/{nonexistent_id}
    response = projects_api_client.get(f"/api/v1/projects/{nonexistent_id}")

    # Assert response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert response contains error message about project not found
    response_data = response.get_json()
    assert "message" in response_data
    assert "Project not found" in response_data["message"]


def test_get_projects_list(projects_api_client, test_projects):
    """Test listing all projects accessible to the user"""
    # Make GET request to /api/v1/projects
    response = projects_api_client.get("/api/v1/projects")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains a list of projects
    response_data = response.get_json()
    assert "items" in response_data
    assert isinstance(response_data["items"], list)

    # Assert the number of projects matches expected count
    assert len(response_data["items"]) == len(test_projects)

    # Assert pagination metadata is included in response
    assert "metadata" in response_data
    assert "page" in response_data["metadata"]
    assert "per_page" in response_data["metadata"]
    assert "total" in response_data["metadata"]


def test_get_projects_with_filters(projects_api_client, test_projects):
    """Test filtering projects by status and other criteria"""
    # Make GET request to /api/v1/projects with status filter
    response = projects_api_client.get("/api/v1/projects?status=active")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert only projects with matching status are returned
    response_data = response.get_json()
    assert all(project["status"] == "active" for project in response_data["items"])

    # Make GET request with category filter
    response = projects_api_client.get("/api/v1/projects?category=Category 0")

    # Assert only projects with matching category are returned
    response_data = response.get_json()
    assert all(project["category"] == "Category 0" for project in response_data["items"])

    # Test combining multiple filters
    response = projects_api_client.get("/api/v1/projects?status=active&category=Category 0")
    response_data = response.get_json()
    assert all(project["status"] == "active" and project["category"] == "Category 0" for project in response_data["items"])


def test_update_project_success(projects_api_client, test_project, mock_event_bus):
    """Test successful project update with valid data"""
    # Create updated project data (new name, description, etc.)
    update_data = {"name": "Updated Project Name", "description": "Updated description"}

    # Make PUT request to /api/v1/projects/{project_id} with updated data
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}", json=update_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response JSON contains updated project data
    response_data = response.get_json()
    assert response_data["name"] == update_data["name"]
    assert response_data["description"] == update_data["description"]

    # Assert project in database has been updated
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.updated event
    mock_event_bus.publish.assert_called_with(
        "project.updated",
        mock.ANY  # Check that it was called with some event
    )


def test_update_project_status(projects_api_client, test_project):
    """Test updating a project's status with valid transition"""
    # Create update data with new valid status
    update_data = {"status": "active"}

    # Make PUT request to /api/v1/projects/{project_id} with status update
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}", json=update_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert project status in response matches new status
    response_data = response.get_json()
    assert response_data["status"] == "active"

    # Assert project status in database has been updated
    # (Verification depends on how the database is mocked)


def test_update_project_invalid_status(projects_api_client, test_project):
    """Test updating a project with invalid status transition"""
    # Create update data with invalid status transition
    update_data = {"status": "invalid"}

    # Make PUT request to /api/v1/projects/{project_id} with invalid status
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}", json=update_data)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert response contains validation error about invalid status transition
    response_data = response.get_json()
    assert "message" in response_data
    assert "errors" in response_data
    assert "status" in response_data["errors"]


def test_update_project_not_found(projects_api_client):
    """Test updating a non-existent project returns not found error"""
    # Create a non-existent project ID
    nonexistent_id = "60d1b7e9a7b3c40000d4e2f0"

    # Make PUT request to /api/v1/projects/{nonexistent_id} with update data
    response = projects_api_client.put(f"/api/v1/projects/{nonexistent_id}", json={"name": "Updated Name"})

    # Assert response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert response contains error message about project not found
    response_data = response.get_json()
    assert "message" in response_data
    assert "Project not found" in response_data["message"]


def test_delete_project_success(projects_api_client, test_project, mock_event_bus):
    """Test successful project deletion (archive)"""
    # Make DELETE request to /api/v1/projects/{project_id}
    response = projects_api_client.delete(f"/api/v1/projects/{test_project.get_id()}")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains success message
    response_data = response.get_json()
    assert "message" in response_data
    assert "Project deleted successfully" in response_data["message"]

    # Verify project in database has status set to 'archived'
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.deleted event
    mock_event_bus.publish.assert_called_with(
        "project.deleted",
        mock.ANY  # Check that it was called with some event
    )


def test_delete_project_not_found(projects_api_client):
    """Test deleting a non-existent project returns not found error"""
    # Create a non-existent project ID
    nonexistent_id = "60d1b7e9a7b3c40000d4e2f0"

    # Make DELETE request to /api/v1/projects/{nonexistent_id}
    response = projects_api_client.delete(f"/api/v1/projects/{nonexistent_id}")

    # Assert response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert response contains error message about project not found
    response_data = response.get_json()
    assert "message" in response_data
    assert "Project not found" in response_data["message"]


def test_add_task_list_success(projects_api_client, test_project, mock_event_bus):
    """Test successfully adding a task list to a project"""
    # Create task list data with name and description
    task_list_data = {"name": "New Task List", "description": "Task list description"}

    # Make POST request to /api/v1/projects/{project_id}/tasklists with task list data
    response = projects_api_client.post(f"/api/v1/projects/{test_project.get_id()}/tasklists", json=task_list_data)

    # Assert response status code is 201 (Created)
    assert response.status_code == 201

    # Assert response contains created task list with ID
    response_data = response.get_json()
    assert "id" in response_data
    assert response_data["name"] == task_list_data["name"]
    assert response_data["description"] == task_list_data["description"]

    # Verify task list was added to project in database
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.tasklist.added event
    mock_event_bus.publish.assert_called_with(
        "project.tasklist.added",
        mock.ANY  # Check that it was called with some event
    )


def test_add_task_list_validation_error(projects_api_client, test_project):
    """Test adding a task list with invalid data returns validation error"""
    # Create invalid task list data (missing required fields)
    invalid_data = {"description": "Task list description"}

    # Make POST request to /api/v1/projects/{project_id}/tasklists with invalid data
    response = projects_api_client.post(f"/api/v1/projects/{test_project.get_id()}/tasklists", json=invalid_data)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert response contains validation error message
    response_data = response.get_json()
    assert "message" in response_data
    assert "errors" in response_data
    assert "name" in response_data["errors"]


def test_update_task_list_success(projects_api_client, test_project_with_task_lists, mock_event_bus):
    """Test successfully updating a task list in a project"""
    # Get an existing task list ID from the project
    task_list_id = test_project_with_task_lists.get("task_lists")[0]["id"]

    # Create update data with new name and description
    update_data = {"name": "Updated Task List", "description": "Updated description"}

    # Make PUT request to /api/v1/projects/{project_id}/tasklists/{task_list_id} with update data
    response = projects_api_client.put(f"/api/v1/projects/{test_project_with_task_lists.get_id()}/tasklists/{task_list_id}", json=update_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains updated task list data
    response_data = response.get_json()
    assert response_data["id"] == task_list_id
    assert response_data["name"] == update_data["name"]
    assert response_data["description"] == update_data["description"]

    # Verify task list was updated in project in database
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.tasklist.updated event
    mock_event_bus.publish.assert_called_with(
        "project.tasklist.updated",
        mock.ANY  # Check that it was called with some event
    )


def test_update_task_list_not_found(projects_api_client, test_project):
    """Test updating a non-existent task list returns not found error"""
    # Create a non-existent task list ID
    nonexistent_id = "60d1b7e9a7b3c40000d4e2f0"

    # Make PUT request to /api/v1/projects/{project_id}/tasklists/{nonexistent_id} with update data
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}/tasklists/{nonexistent_id}", json={"name": "Updated Name"})

    # Assert response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert response contains error message about task list not found
    response_data = response.get_json()
    assert "message" in response_data
    assert "Task list not found" in response_data["message"]


def test_delete_task_list_success(projects_api_client, test_project_with_task_lists, mock_event_bus):
    """Test successfully deleting a task list from a project"""
    # Get an existing task list ID from the project
    task_list_id = test_project_with_task_lists.get("task_lists")[0]["id"]

    # Make DELETE request to /api/v1/projects/{project_id}/tasklists/{task_list_id}
    response = projects_api_client.delete(f"/api/v1/projects/{test_project_with_task_lists.get_id()}/tasklists/{task_list_id}")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains success message
    response_data = response.get_json()
    assert "message" in response_data
    assert "Task list deleted successfully" in response_data["message"]

    # Verify task list was removed from project in database
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.tasklist.removed event
    mock_event_bus.publish.assert_called_with(
        "project.tasklist.removed",
        mock.ANY  # Check that it was called with some event
    )


def test_delete_task_list_not_found(projects_api_client, test_project):
    """Test deleting a non-existent task list returns not found error"""
    # Create a non-existent task list ID
    nonexistent_id = "60d1b7e9a7b3c40000d4e2f0"

    # Make DELETE request to /api/v1/projects/{project_id}/tasklists/{nonexistent_id}
    response = projects_api_client.delete(f"/api/v1/projects/{test_project.get_id()}/tasklists/{nonexistent_id}")

    # Assert response status code is 404 (Not Found)
    assert response.status_code == 404

    # Assert response contains error message about task list not found
    response_data = response.get_json()
    assert "message" in response_data
    assert "Task list not found" in response_data["message"]


def test_update_project_settings_success(projects_api_client, test_project, mock_event_bus):
    """Test successfully updating project settings"""
    # Create settings update data (workflow settings, permissions, etc.)
    settings_data = {"workflow": {"enableReview": False}, "permissions": {"memberInvite": "admin"}}

    # Make PUT request to /api/v1/projects/{project_id}/settings with settings data
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}/settings", json=settings_data)

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains updated settings
    response_data = response.get_json()
    assert response_data["workflow"]["enableReview"] == False
    assert response_data["permissions"]["memberInvite"] == "admin"

    # Verify settings were updated in project in database
    # (Verification depends on how the database is mocked)
    # Assert event_bus.publish was called with project.settings.updated event
    mock_event_bus.publish.assert_called_with(
        "project.settings.updated",
        mock.ANY  # Check that it was called with some event
    )


def test_update_project_settings_validation_error(projects_api_client, test_project):
    """Test updating project settings with invalid data returns validation error"""
    # Create invalid settings data (invalid permission values, etc.)
    invalid_data = {"permissions": {"memberInvite": "invalid"}}

    # Make PUT request to /api/v1/projects/{project_id}/settings with invalid data
    response = projects_api_client.put(f"/api/v1/projects/{test_project.get_id()}/settings", json=invalid_data)

    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert response contains validation error message
    response_data = response.get_json()
    assert "message" in response_data
    assert "errors" in response_data
    assert "permissions" in response_data["errors"]


def test_get_project_stats_success(projects_api_client, test_project):
    """Test successfully retrieving project statistics"""
    # Make GET request to /api/v1/projects/{project_id}/stats
    response = projects_api_client.get(f"/api/v1/projects/{test_project.get_id()}/stats")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains project statistics
    response_data = response.get_json()
    assert "total_tasks" in response_data
    assert "completed_tasks" in response_data
    assert "completion_rate" in response_data

    # Verify statistics include task counts, completion percentage, etc.
    assert isinstance(response_data["total_tasks"], int)
    assert isinstance(response_data["completed_tasks"], int)
    assert isinstance(response_data["completion_rate"], (int, float))


def test_search_projects_success(projects_api_client, test_projects):
    """Test successfully searching for projects"""
    # Make GET request to /api/v1/projects/search?q={search_term}
    response = projects_api_client.get("/api/v1/projects/search?q=Test")

    # Assert response status code is 200 (OK)
    assert response.status_code == 200

    # Assert response contains matching projects
    response_data = response.get_json()
    assert "items" in response_data
    assert isinstance(response_data["items"], list)

    # Assert pagination metadata is included in response
    assert "metadata" in response_data
    assert "page" in response_data["metadata"]
    assert "per_page" in response_data["metadata"]
    assert "total" in response_data["metadata"]


def test_unauthenticated_access(projects_api_client):
    """Test that unauthenticated requests are rejected"""
    # Make GET request to /api/v1/projects without auth headers
    response = projects_api_client.get("/api/v1/projects")

    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401

    # Make POST request to /api/v1/projects without auth headers
    response = projects_api_client.post("/api/v1/projects", json={"name": "Test", "description": "Test"})

    # Assert response status code is 401 (Unauthorized)
    assert response.status_code == 401