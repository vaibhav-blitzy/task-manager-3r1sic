"""
Integration tests for project-related workflows.

This module tests the complete lifecycle of projects including creation, updates, team
management, task lists, and project settings. These tests verify that the project service
API endpoints function correctly with proper authorization and maintain data integrity
across operations.
"""

import json
import time
import pytest
import requests


@pytest.fixture
def test_project(base_url, authenticated_client, test_user):
    """
    Creates a test project for the authenticated user.
    
    Args:
        base_url: Base API URL
        authenticated_client: HTTP client with authentication
        test_user: Test user fixture
        
    Returns:
        dict: Dictionary containing project details
    """
    # Generate project data
    project_data = {
        "name": "Test Project",
        "description": "A project created for integration testing",
        "category": "testing"
    }
    
    # Create project
    response = authenticated_client.post(
        f"{base_url}/projects",
        json=project_data
    )
    
    assert response.status_code == 201, f"Failed to create test project: {response.text}"
    
    return response.json()


@pytest.fixture
def another_user(base_url, test_client):
    """
    Creates another test user.
    
    Args:
        base_url: Base API URL
        test_client: HTTP client without authentication
        
    Returns:
        dict: Dictionary containing user details and authentication tokens
    """
    # Generate unique user data
    user_data = {
        "email": f"another_user_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "firstName": "Another",
        "lastName": "User"
    }
    
    # Register user
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    assert response.status_code == 201, f"Failed to create another user: {response.text}"
    
    # Login to get tokens
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )
    
    assert login_response.status_code == 200, f"Failed to login as another user: {login_response.text}"
    
    # Return user data with tokens
    tokens = login_response.json()
    return {
        "id": tokens.get("user_id"),
        "email": user_data["email"],
        "firstName": user_data["firstName"],
        "lastName": user_data["lastName"],
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token")
    }


@pytest.fixture
def other_user_project(base_url, test_client, another_user):
    """
    Creates a project owned by a different user.
    
    Args:
        base_url: Base API URL
        test_client: HTTP client without authentication
        another_user: Another test user fixture
        
    Returns:
        dict: Dictionary containing project details
    """
    # Generate project data
    project_data = {
        "name": "Other User Project",
        "description": "A project created by another user",
        "category": "testing"
    }
    
    # Create project with another user's authentication
    headers = {
        "Authorization": f"Bearer {another_user['access_token']}",
        "Content-Type": "application/json"
    }
    
    response = test_client.post(
        f"{base_url}/projects",
        headers=headers,
        json=project_data
    )
    
    assert response.status_code == 201, f"Failed to create other user project: {response.text}"
    
    return response.json()


@pytest.fixture
def multiple_user_projects(base_url, authenticated_client, test_user):
    """
    Creates multiple projects for testing listing and filtering.
    
    Args:
        base_url: Base API URL
        authenticated_client: HTTP client with authentication
        test_user: Test user fixture
        
    Returns:
        list: List of project dictionaries
    """
    projects = []
    
    # Create projects with different statuses and categories
    project_specs = [
        {"name": "Active Development Project", "status": "active", "category": "development"},
        {"name": "Active Marketing Project", "status": "active", "category": "marketing"},
        {"name": "Planning Project", "status": "planning", "category": "development"},
        {"name": "On Hold Project", "status": "on_hold", "category": "operations"},
        {"name": "Completed Project", "status": "completed", "category": "marketing"}
    ]
    
    for spec in project_specs:
        project_data = {
            "name": spec["name"],
            "description": f"A {spec['status']} project for testing",
            "category": spec["category"]
        }
        
        # Create project
        response = authenticated_client.post(
            f"{base_url}/projects",
            json=project_data
        )
        
        assert response.status_code == 201, f"Failed to create project: {response.text}"
        
        # If created in non-active status, update the status
        project = response.json()
        if spec["status"] != "planning":  # Default is planning, so only update if different
            status_response = authenticated_client.patch(
                f"{base_url}/projects/{project['id']}/status",
                json={"status": spec["status"]}
            )
            assert status_response.status_code == 200, f"Failed to update project status: {status_response.text}"
            project = status_response.json()
            
        projects.append(project)
    
    return projects


@pytest.fixture
def project_with_tasks(base_url, authenticated_client, test_user):
    """
    Creates a project with multiple tasks for testing project stats.
    
    Args:
        base_url: Base API URL
        authenticated_client: HTTP client with authentication
        test_user: Test user fixture
        
    Returns:
        dict: Dictionary containing project details with tasks
    """
    # Create a test project
    project_data = {
        "name": "Project with Tasks",
        "description": "A project with multiple tasks for testing stats",
        "category": "testing"
    }
    
    project_response = authenticated_client.post(
        f"{base_url}/projects",
        json=project_data
    )
    
    assert project_response.status_code == 201, f"Failed to create project: {project_response.text}"
    
    project = project_response.json()
    
    # Add tasks with different statuses
    task_specs = [
        {"title": "Not Started Task", "status": "not_started"},
        {"title": "In Progress Task 1", "status": "in_progress"},
        {"title": "In Progress Task 2", "status": "in_progress"},
        {"title": "On Hold Task", "status": "on_hold"},
        {"title": "Completed Task 1", "status": "completed"},
        {"title": "Completed Task 2", "status": "completed"},
        {"title": "Completed Task 3", "status": "completed"}
    ]
    
    for spec in task_specs:
        task_data = {
            "title": spec["title"],
            "description": f"A task for testing with status: {spec['status']}",
            "status": "not_started",  # Start all as not started
            "priority": "medium",
            "projectId": project["id"],
            "dueDate": None
        }
        
        # Create task
        task_response = authenticated_client.post(
            f"{base_url}/tasks",
            json=task_data
        )
        
        assert task_response.status_code == 201, f"Failed to create task: {task_response.text}"
        
        task = task_response.json()
        
        # Update status if needed
        if spec["status"] != "not_started":
            status_response = authenticated_client.patch(
                f"{base_url}/tasks/{task['id']}/status",
                json={"status": spec["status"]}
            )
            
            assert status_response.status_code == 200, f"Failed to update task status: {status_response.text}"
    
    # Return the project
    return project


def test_project_creation_success(base_url, authenticated_client):
    """
    Tests successful project creation flow.
    """
    # Prepare test data
    project_data = {
        "name": "New Integration Test Project",
        "description": "A project created during integration testing",
        "category": "testing"
    }
    
    # Send request to create project
    response = authenticated_client.post(
        f"{base_url}/projects",
        json=project_data
    )
    
    # Verify response status code
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}: {response.text}"
    
    # Verify response data
    project = response.json()
    assert project["name"] == project_data["name"]
    assert project["description"] == project_data["description"]
    assert project["status"] == "planning"  # Default status should be 'planning'
    assert "id" in project
    assert "createdAt" in project
    assert "owner" in project


def test_project_creation_validation(base_url, authenticated_client):
    """
    Tests project creation with invalid data.
    """
    # Test missing name
    invalid_project = {
        "description": "Project without name",
        "category": "testing"
    }
    
    response = authenticated_client.post(
        f"{base_url}/projects",
        json=invalid_project
    )
    
    assert response.status_code == 400, f"Expected validation error for missing name, got {response.status_code}"
    assert "name" in response.text.lower()
    
    # Test empty description (if required by API)
    invalid_project = {
        "name": "Project with Empty Description",
        "description": "",
        "category": "testing"
    }
    
    response = authenticated_client.post(
        f"{base_url}/projects",
        json=invalid_project
    )
    
    assert response.status_code == 400, f"Expected validation error for empty description, got {response.status_code}"
    assert "description" in response.text.lower()
    
    # Test invalid status value
    invalid_project = {
        "name": "Project with Invalid Status",
        "description": "Testing invalid status",
        "category": "testing",
        "status": "invalid_status"
    }
    
    response = authenticated_client.post(
        f"{base_url}/projects",
        json=invalid_project
    )
    
    assert response.status_code == 400, f"Expected validation error for invalid status, got {response.status_code}"
    assert "status" in response.text.lower()


def test_get_project_details(base_url, authenticated_client, test_project):
    """
    Tests retrieving project details.
    """
    # Get project details
    response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    # Verify response
    assert response.status_code == 200, f"Failed to get project details: {response.text}"
    
    project = response.json()
    assert project["id"] == test_project["id"]
    assert project["name"] == test_project["name"]
    assert project["description"] == test_project["description"]
    
    # Verify all expected fields are present
    expected_fields = ["id", "name", "description", "status", "owner", "members", 
                      "createdAt", "updatedAt", "category"]
    
    for field in expected_fields:
        assert field in project, f"Expected field '{field}' missing from project response"


def test_get_project_unauthorized(base_url, authenticated_client, other_user_project):
    """
    Tests accessing project by unauthorized user.
    """
    # Attempt to access other user's project
    response = authenticated_client.get(
        f"{base_url}/projects/{other_user_project['id']}"
    )
    
    # Verify unauthorized response
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
    assert "permission" in response.text.lower() or "unauthorized" in response.text.lower()


def test_update_project(base_url, authenticated_client, test_project):
    """
    Tests updating project details.
    """
    # Prepare update data
    update_data = {
        "name": "Updated Project Name",
        "description": "Updated project description",
        "category": "development"
    }
    
    # Send update request
    response = authenticated_client.put(
        f"{base_url}/projects/{test_project['id']}",
        json=update_data
    )
    
    # Verify response
    assert response.status_code == 200, f"Failed to update project: {response.text}"
    
    updated_project = response.json()
    assert updated_project["name"] == update_data["name"]
    assert updated_project["description"] == update_data["description"]
    assert updated_project["category"] == update_data["category"]
    
    # Verify persistence by getting the project again
    get_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    assert get_response.status_code == 200
    get_project = get_response.json()
    assert get_project["name"] == update_data["name"]
    assert get_project["description"] == update_data["description"]
    assert get_project["category"] == update_data["category"]


def test_update_project_unauthorized(base_url, authenticated_client, other_user_project):
    """
    Tests updating project by unauthorized user.
    """
    # Prepare update data
    update_data = {
        "name": "Unauthorized Update Attempt",
        "description": "This update should fail",
        "category": "development"
    }
    
    # Attempt to update other user's project
    response = authenticated_client.put(
        f"{base_url}/projects/{other_user_project['id']}",
        json=update_data
    )
    
    # Verify unauthorized response
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
    assert "permission" in response.text.lower() or "unauthorized" in response.text.lower()


def test_project_status_transitions(base_url, authenticated_client, test_project):
    """
    Tests project status transition flow.
    """
    # Verify initial status
    assert test_project["status"] == "planning"
    
    # Test valid transitions
    
    # planning -> active
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "active"}
    )
    
    assert status_response.status_code == 200, f"Failed to transition status to active: {status_response.text}"
    assert status_response.json()["status"] == "active"
    
    # active -> on_hold
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "on_hold"}
    )
    
    assert status_response.status_code == 200, f"Failed to transition status to on_hold: {status_response.text}"
    assert status_response.json()["status"] == "on_hold"
    
    # on_hold -> active
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "active"}
    )
    
    assert status_response.status_code == 200, f"Failed to transition status back to active: {status_response.text}"
    assert status_response.json()["status"] == "active"
    
    # active -> completed
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "completed"}
    )
    
    assert status_response.status_code == 200, f"Failed to transition status to completed: {status_response.text}"
    project = status_response.json()
    assert project["status"] == "completed"
    
    # Verify completedAt is set
    assert "completedAt" in project["metadata"], "completedAt should be set in project metadata when completed"
    
    # Test invalid transitions
    
    # completed -> planning (should fail)
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "planning"}
    )
    
    assert status_response.status_code == 400, f"Expected 400 for invalid transition, got {status_response.status_code}"
    
    # Test invalid status value
    status_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/status",
        json={"status": "invalid_status"}
    )
    
    assert status_response.status_code == 400, f"Expected 400 for invalid status, got {status_response.status_code}"


def test_project_member_management(base_url, authenticated_client, test_project, another_user):
    """
    Tests adding, updating, and removing project members.
    """
    # Add another user as a member
    member_data = {
        "userId": another_user["id"],
        "role": "member"
    }
    
    add_response = authenticated_client.post(
        f"{base_url}/projects/{test_project['id']}/members",
        json=member_data
    )
    
    assert add_response.status_code == 201, f"Failed to add member: {add_response.text}"
    assert add_response.json()["userId"] == another_user["id"]
    assert add_response.json()["role"] == "member"
    
    # Update member role
    update_data = {
        "role": "manager"
    }
    
    update_response = authenticated_client.patch(
        f"{base_url}/projects/{test_project['id']}/members/{another_user['id']}",
        json=update_data
    )
    
    assert update_response.status_code == 200, f"Failed to update member role: {update_response.text}"
    assert update_response.json()["role"] == "manager"
    
    # Get project members
    members_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}/members"
    )
    
    assert members_response.status_code == 200, f"Failed to get project members: {members_response.text}"
    members = members_response.json()
    
    # Verify both the owner and the added member are in the list
    member_ids = [m["userId"] for m in members]
    assert another_user["id"] in member_ids, "Added member not found in members list"
    
    # Remove the member
    remove_response = authenticated_client.delete(
        f"{base_url}/projects/{test_project['id']}/members/{another_user['id']}"
    )
    
    assert remove_response.status_code == 200, f"Failed to remove member: {remove_response.text}"
    
    # Verify member was removed
    members_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}/members"
    )
    
    assert members_response.status_code == 200
    updated_members = members_response.json()
    updated_member_ids = [m["userId"] for m in updated_members]
    assert another_user["id"] not in updated_member_ids, "Member was not removed successfully"


def test_project_task_lists(base_url, authenticated_client, test_project):
    """
    Tests adding, updating, and removing task lists.
    """
    # Create a task list
    task_list_data = {
        "name": "Development Tasks",
        "description": "Tasks for the development phase"
    }
    
    create_response = authenticated_client.post(
        f"{base_url}/projects/{test_project['id']}/tasklists",
        json=task_list_data
    )
    
    assert create_response.status_code == 201, f"Failed to create task list: {create_response.text}"
    task_list = create_response.json()
    assert task_list["name"] == task_list_data["name"]
    assert task_list["description"] == task_list_data["description"]
    
    # Store task list ID for later use
    task_list_id = task_list["id"]
    
    # Create another task list
    another_task_list_data = {
        "name": "Testing Tasks",
        "description": "Tasks for testing phase"
    }
    
    another_create_response = authenticated_client.post(
        f"{base_url}/projects/{test_project['id']}/tasklists",
        json=another_task_list_data
    )
    
    assert another_create_response.status_code == 201, f"Failed to create second task list: {another_create_response.text}"
    another_task_list = another_create_response.json()
    
    # Update first task list
    update_data = {
        "name": "Updated Development Tasks"
    }
    
    update_response = authenticated_client.put(
        f"{base_url}/projects/{test_project['id']}/tasklists/{task_list_id}",
        json=update_data
    )
    
    assert update_response.status_code == 200, f"Failed to update task list: {update_response.text}"
    updated_task_list = update_response.json()
    assert updated_task_list["name"] == update_data["name"]
    
    # Delete second task list
    delete_response = authenticated_client.delete(
        f"{base_url}/projects/{test_project['id']}/tasklists/{another_task_list['id']}"
    )
    
    assert delete_response.status_code == 200, f"Failed to delete task list: {delete_response.text}"
    
    # Get project details and verify task lists
    project_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    assert project_response.status_code == 200
    project = project_response.json()
    
    # Check if task lists are correctly updated
    task_list_ids = [tl["id"] for tl in project.get("taskLists", [])]
    assert task_list_id in task_list_ids, "First task list should still be present"
    assert another_task_list["id"] not in task_list_ids, "Second task list should be deleted"


def test_project_settings(base_url, authenticated_client, test_project):
    """
    Tests updating project settings.
    """
    # Prepare settings data
    settings_data = {
        "workflow": {
            "enableReview": True,
            "allowSubtasks": True,
            "defaultTaskStatus": "not_started"
        },
        "permissions": {
            "memberInvite": "owner,manager",
            "taskCreate": "owner,manager,member",
            "commentCreate": "owner,manager,member,viewer"
        },
        "notifications": {
            "taskCreate": True,
            "taskComplete": True,
            "commentAdd": False
        }
    }
    
    # Update project settings
    response = authenticated_client.put(
        f"{base_url}/projects/{test_project['id']}/settings",
        json=settings_data
    )
    
    assert response.status_code == 200, f"Failed to update project settings: {response.text}"
    updated_settings = response.json()
    
    # Verify workflow settings
    assert updated_settings["workflow"]["enableReview"] == settings_data["workflow"]["enableReview"]
    assert updated_settings["workflow"]["allowSubtasks"] == settings_data["workflow"]["allowSubtasks"]
    assert updated_settings["workflow"]["defaultTaskStatus"] == settings_data["workflow"]["defaultTaskStatus"]
    
    # Verify permissions settings
    assert updated_settings["permissions"]["memberInvite"] == settings_data["permissions"]["memberInvite"]
    assert updated_settings["permissions"]["taskCreate"] == settings_data["permissions"]["taskCreate"]
    assert updated_settings["permissions"]["commentCreate"] == settings_data["permissions"]["commentCreate"]
    
    # Verify notifications settings if present
    if "notifications" in updated_settings:
        assert updated_settings["notifications"]["taskCreate"] == settings_data["notifications"]["taskCreate"]
        assert updated_settings["notifications"]["taskComplete"] == settings_data["notifications"]["taskComplete"]
        assert updated_settings["notifications"]["commentAdd"] == settings_data["notifications"]["commentAdd"]
    
    # Get project details and verify settings
    project_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    assert project_response.status_code == 200
    project = project_response.json()
    
    # Verify settings are saved in project
    assert project["settings"]["workflow"]["enableReview"] == settings_data["workflow"]["enableReview"]
    assert project["settings"]["permissions"]["memberInvite"] == settings_data["permissions"]["memberInvite"]


def test_list_user_projects(base_url, authenticated_client, multiple_user_projects):
    """
    Tests retrieving a user's projects with filtering.
    """
    # Get all projects
    response = authenticated_client.get(f"{base_url}/projects")
    
    assert response.status_code == 200, f"Failed to list projects: {response.text}"
    
    projects = response.json()
    assert isinstance(projects, list), "Expected a list of projects"
    assert len(projects) >= len(multiple_user_projects), "Should return at least the created test projects"
    
    # Test filtering by status
    status_response = authenticated_client.get(f"{base_url}/projects?status=active")
    
    assert status_response.status_code == 200
    active_projects = status_response.json()
    
    # Verify that all returned projects have active status
    for project in active_projects:
        assert project["status"] == "active", f"Project with status {project['status']} in active filter results"
    
    # Test filtering by category
    category_response = authenticated_client.get(f"{base_url}/projects?category=development")
    
    assert category_response.status_code == 200
    dev_projects = category_response.json()
    
    # Verify that all returned projects have development category
    for project in dev_projects:
        assert project["category"] == "development", f"Project with category {project['category']} in development filter results"
    
    # Test pagination
    page_response = authenticated_client.get(f"{base_url}/projects?page=1&per_page=2")
    
    assert page_response.status_code == 200
    paged_projects = page_response.json()
    
    # Verify pagination
    assert len(paged_projects) <= 2, "Page size should limit results to 2 projects"
    
    # Check for pagination headers
    assert "X-Pagination-Page" in page_response.headers, "Pagination header X-Pagination-Page missing"
    assert "X-Pagination-Per-Page" in page_response.headers, "Pagination header X-Pagination-Per-Page missing"
    assert "X-Pagination-Total" in page_response.headers, "Pagination header X-Pagination-Total missing"


def test_search_projects(base_url, authenticated_client, multiple_user_projects):
    """
    Tests searching for projects with various criteria.
    """
    # Create a recognizable project for testing search
    unique_keyword = f"unique_search_term_{int(time.time())}"
    search_project_data = {
        "name": f"Searchable Project with {unique_keyword}",
        "description": "A project specifically for testing search functionality",
        "category": "testing"
    }
    
    create_response = authenticated_client.post(
        f"{base_url}/projects",
        json=search_project_data
    )
    
    assert create_response.status_code == 201, f"Failed to create search test project: {create_response.text}"
    
    # Basic search by keyword
    search_response = authenticated_client.get(
        f"{base_url}/projects/search?q={unique_keyword}"
    )
    
    assert search_response.status_code == 200, f"Search request failed: {search_response.text}"
    search_results = search_response.json()
    
    # Verify keyword search works
    assert len(search_results) >= 1, "Expected at least one result for keyword search"
    assert any(unique_keyword.lower() in project["name"].lower() for project in search_results), \
        "Search did not return project with the unique keyword"
    
    # Test combined search (keyword + filters)
    # Find active marketing projects
    combined_response = authenticated_client.get(
        f"{base_url}/projects/search?status=active&category=marketing"
    )
    
    assert combined_response.status_code == 200
    combined_results = combined_response.json()
    
    # Verify combined filters work
    for project in combined_results:
        assert project["status"] == "active", "Non-active project in filtered results"
        assert project["category"] == "marketing", "Non-marketing project in filtered results"


def test_project_stats(base_url, authenticated_client, project_with_tasks):
    """
    Tests retrieving project statistics.
    """
    # Get project stats
    response = authenticated_client.get(
        f"{base_url}/projects/{project_with_tasks['id']}/stats"
    )
    
    assert response.status_code == 200, f"Failed to get project stats: {response.text}"
    
    stats = response.json()
    
    # Verify task statistics
    assert "taskStats" in stats, "Expected taskStats in response"
    task_stats = stats["taskStats"]
    
    assert "total" in task_stats, "Expected total task count"
    assert task_stats["total"] >= 7, "Expected at least 7 tasks (from fixture)"
    
    assert "completed" in task_stats, "Expected completed task count"
    assert task_stats["completed"] >= 3, "Expected at least 3 completed tasks (from fixture)"
    
    assert "inProgress" in task_stats, "Expected inProgress task count"
    assert task_stats["inProgress"] >= 2, "Expected at least 2 in-progress tasks (from fixture)"
    
    # Verify completion percentage
    assert "completionPercentage" in stats, "Expected completionPercentage in response"
    assert 0 <= stats["completionPercentage"] <= 100, "Completion percentage should be between 0 and 100"
    
    # Verify expected percentage calculation
    expected_percentage = (task_stats["completed"] / task_stats["total"]) * 100
    assert abs(stats["completionPercentage"] - expected_percentage) < 0.1, "Completion percentage calculation mismatch"


def test_project_deletion(base_url, authenticated_client, test_project):
    """
    Tests project deletion (soft delete by archiving).
    """
    # Delete (archive) the project
    response = authenticated_client.delete(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    assert response.status_code == 200, f"Failed to delete project: {response.text}"
    assert "success" in response.json(), "Expected success message in response"
    
    # Verify project is archived, not hard-deleted
    get_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['id']}"
    )
    
    assert get_response.status_code == 200, "Project should still be accessible after soft-delete"
    project = get_response.json()
    assert project["status"] == "archived", "Project status should be changed to 'archived'"