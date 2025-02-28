"""
Integration tests for the Task Management System's task-related workflows.

These tests verify the complete lifecycle of tasks including creation, updates,
status transitions, assignments, subtasks, and dependencies. The tests ensure
that the API endpoints function correctly with proper authorization.
"""

import pytest
import json
import datetime
import time
import requests

# Fixtures and utilities from conftest
from conftest import (
    base_url,
    test_client,
    authenticated_client,
    authenticated_admin_client,
    test_user,
    test_admin,
    test_project,
    authenticated_user_headers,
    authenticated_admin_headers
)

# Fixtures for testing

@pytest.fixture
def test_task(base_url, authenticated_client, test_user):
    """
    Creates a test task for the authenticated user.
    
    Returns a dictionary containing the task data.
    """
    task_data = {
        "title": "Test Task",
        "description": "This is a test task for integration testing",
        "priority": "medium",
        "status": "created"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks", 
        json=task_data
    )
    
    assert response.status_code == 201
    return json.loads(response.data)

@pytest.fixture
def other_user_task(base_url, test_client, another_user):
    """
    Creates a task owned by a different user.
    
    Returns a dictionary containing the task data.
    """
    task_data = {
        "title": "Other User Task",
        "description": "This task belongs to another user",
        "priority": "medium",
        "status": "created"
    }
    
    headers = {
        "Authorization": f"Bearer {another_user['access_token']}",
        "Content-Type": "application/json"
    }
    
    response = test_client.post(
        f"{base_url}/tasks", 
        json=task_data,
        headers=headers
    )
    
    assert response.status_code == 201
    return json.loads(response.data)

@pytest.fixture
def another_user(base_url, test_client):
    """
    Creates another test user for assignment testing.
    
    Returns a dictionary with user details and authentication tokens.
    """
    user_data = {
        "email": f"another_user_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "firstName": "Another",
        "lastName": "User"
    }
    
    # Register the user
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    assert response.status_code == 201
    user_response = json.loads(response.data)
    
    # Login to get tokens
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    assert login_response.status_code == 200
    tokens = json.loads(login_response.data)
    
    # Combine user data with tokens
    user_response.update(tokens)
    return user_response

@pytest.fixture
def second_test_task(base_url, authenticated_client, test_user):
    """
    Creates a second test task for dependency testing.
    
    Returns a dictionary containing the task data.
    """
    task_data = {
        "title": "Dependent Task",
        "description": "This is a task for testing dependencies",
        "priority": "high",
        "status": "created"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks", 
        json=task_data
    )
    
    assert response.status_code == 201
    return json.loads(response.data)

@pytest.fixture
def multiple_user_tasks(base_url, authenticated_client, test_user, test_project):
    """
    Creates multiple tasks for testing listing and filtering.
    
    Returns a list of task dictionaries with various statuses, priorities, and due dates.
    """
    tasks = []
    
    # Create tasks with different statuses
    statuses = ["created", "assigned", "in_progress", "on_hold", "completed"]
    priorities = ["low", "medium", "high", "urgent"]
    
    for i in range(10):
        status = statuses[i % len(statuses)]
        priority = priorities[i % len(priorities)]
        
        # Set different due dates
        days_offset = i - 5  # Some past, some future
        due_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days_offset)).isoformat()
        
        task_data = {
            "title": f"Task {i+1}",
            "description": f"Description for task {i+1}",
            "status": status,
            "priority": priority,
            "dueDate": due_date,
            "projectId": test_project["_id"] if i % 2 == 0 else None
        }
        
        response = authenticated_client.post(
            f"{base_url}/tasks", 
            json=task_data
        )
        
        assert response.status_code == 201
        tasks.append(json.loads(response.data))
    
    return tasks

@pytest.fixture
def tasks_with_due_dates(base_url, authenticated_client, test_user):
    """
    Creates tasks with past, soon, and future due dates.
    
    Returns a dictionary with categorized task lists.
    """
    now = datetime.datetime.utcnow()
    
    # Create overdue tasks (in the past)
    overdue_tasks = []
    for i in range(3):
        days_ago = i + 1
        due_date = (now - datetime.timedelta(days=days_ago)).isoformat()
        
        task_data = {
            "title": f"Overdue Task {i+1}",
            "description": f"This task is overdue by {days_ago} days",
            "priority": "high",
            "dueDate": due_date,
            "status": "in_progress"
        }
        
        response = authenticated_client.post(
            f"{base_url}/tasks", 
            json=task_data
        )
        
        assert response.status_code == 201
        overdue_tasks.append(json.loads(response.data))
    
    # Create tasks due soon (next 24 hours)
    due_soon_tasks = []
    for i in range(3):
        hours_future = i * 8  # 0, 8, 16 hours in the future
        due_date = (now + datetime.timedelta(hours=hours_future)).isoformat()
        
        task_data = {
            "title": f"Due Soon Task {i+1}",
            "description": f"This task is due in {hours_future} hours",
            "priority": "medium",
            "dueDate": due_date,
            "status": "in_progress"
        }
        
        response = authenticated_client.post(
            f"{base_url}/tasks", 
            json=task_data
        )
        
        assert response.status_code == 201
        due_soon_tasks.append(json.loads(response.data))
    
    # Create future tasks (more than 48 hours)
    future_tasks = []
    for i in range(3):
        days_future = i + 3  # 3, 4, 5 days in the future
        due_date = (now + datetime.timedelta(days=days_future)).isoformat()
        
        task_data = {
            "title": f"Future Task {i+1}",
            "description": f"This task is due in {days_future} days",
            "priority": "low",
            "dueDate": due_date,
            "status": "created"
        }
        
        response = authenticated_client.post(
            f"{base_url}/tasks", 
            json=task_data
        )
        
        assert response.status_code == 201
        future_tasks.append(json.loads(response.data))
    
    return {
        "overdue": overdue_tasks,
        "due_soon": due_soon_tasks,
        "future": future_tasks
    }

# Test cases

def test_task_creation_success(base_url, authenticated_client):
    """
    Tests successful task creation with valid data.
    """
    # Define test task data
    task_data = {
        "title": "New Integration Test Task",
        "description": "This is a task created during integration testing",
        "priority": "medium"
    }
    
    # Create task
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=task_data
    )
    
    # Verify response status code
    assert response.status_code == 201
    
    # Parse response data
    task = json.loads(response.data)
    
    # Verify task data
    assert task["title"] == task_data["title"]
    assert task["description"] == task_data["description"]
    assert task["priority"] == task_data["priority"]
    
    # Verify default status is "created"
    assert task["status"] == "created"
    
    # Verify creator is correct
    assert "createdBy" in task
    
    # Verify creation metadata
    assert "createdAt" in task
    assert "updatedAt" in task

def test_task_creation_with_project(base_url, authenticated_client, test_project):
    """
    Tests creating a task associated with a project.
    """
    # Define test task data with project
    task_data = {
        "title": "Project Task",
        "description": "This task belongs to a project",
        "priority": "high",
        "projectId": test_project["_id"]
    }
    
    # Create task
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=task_data
    )
    
    # Verify response status code
    assert response.status_code == 201
    
    # Parse response data
    task = json.loads(response.data)
    
    # Verify project association
    assert task["projectId"] == test_project["_id"]
    
    # Verify task appears in project tasks
    project_tasks_response = authenticated_client.get(
        f"{base_url}/projects/{test_project['_id']}/tasks"
    )
    
    assert project_tasks_response.status_code == 200
    project_tasks = json.loads(project_tasks_response.data)
    
    # Find our task in the project tasks
    task_found = any(t["_id"] == task["_id"] for t in project_tasks["items"])
    assert task_found

def test_task_creation_validation(base_url, authenticated_client):
    """
    Tests task creation with invalid data to verify validation.
    """
    # Test creating task without title
    invalid_task = {
        "description": "Task without a title",
        "priority": "medium"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=invalid_task
    )
    
    # Verify validation error
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "title" in error_data.get("errors", {})
    
    # Test creating task with invalid status
    invalid_status_task = {
        "title": "Task with invalid status",
        "description": "This task has an invalid status",
        "status": "not_a_valid_status"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=invalid_status_task
    )
    
    # Verify validation error
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "status" in error_data.get("errors", {})
    
    # Test creating task with invalid priority
    invalid_priority_task = {
        "title": "Task with invalid priority",
        "description": "This task has an invalid priority",
        "priority": "extreme"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=invalid_priority_task
    )
    
    # Verify validation error
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "priority" in error_data.get("errors", {})

def test_get_task_details(base_url, authenticated_client, test_task):
    """
    Tests retrieving task details.
    """
    # Get task details
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    # Verify response status code
    assert response.status_code == 200
    
    # Parse response data
    task = json.loads(response.data)
    
    # Verify task data matches
    assert task["_id"] == test_task["_id"]
    assert task["title"] == test_task["title"]
    assert task["description"] == test_task["description"]
    assert task["status"] == test_task["status"]
    assert task["priority"] == test_task["priority"]
    
    # Verify all expected fields are present
    expected_fields = [
        "_id", "title", "description", "status", "priority", 
        "createdBy", "createdAt", "updatedAt"
    ]
    
    for field in expected_fields:
        assert field in task

def test_get_task_unauthorized(base_url, authenticated_client, other_user_task):
    """
    Tests attempting to access a task created by another user.
    """
    # Try to access task created by another user
    response = authenticated_client.get(
        f"{base_url}/tasks/{other_user_task['_id']}"
    )
    
    # Verify access is denied
    assert response.status_code == 403
    
    # Parse error response
    error_data = json.loads(response.data)
    assert "authorization" in error_data.get("code", "").lower()

def test_update_task(base_url, authenticated_client, test_task):
    """
    Tests updating task details.
    """
    # Define updated task data
    updated_data = {
        "title": "Updated Task Title",
        "description": "This description has been updated",
        "priority": "high",
        "dueDate": (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    }
    
    # Update the task
    response = authenticated_client.put(
        f"{base_url}/tasks/{test_task['_id']}",
        json=updated_data
    )
    
    # Verify response status code
    assert response.status_code == 200
    
    # Parse response data
    updated_task = json.loads(response.data)
    
    # Verify updated fields
    assert updated_task["title"] == updated_data["title"]
    assert updated_task["description"] == updated_data["description"]
    assert updated_task["priority"] == updated_data["priority"]
    assert "dueDate" in updated_task
    
    # Verify update was persisted by fetching task again
    get_response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert get_response.status_code == 200
    fetched_task = json.loads(get_response.data)
    
    assert fetched_task["title"] == updated_data["title"]
    assert fetched_task["description"] == updated_data["description"]
    assert fetched_task["priority"] == updated_data["priority"]

def test_task_status_transitions(base_url, authenticated_client, test_task):
    """
    Tests the task status transition workflow.
    """
    # Verify initial status
    assert test_task["status"] == "created"
    
    # Test transition: created -> assigned
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "assigned"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "assigned"
    
    # Test transition: assigned -> in_progress
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "in_progress"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "in_progress"
    
    # Test transition: in_progress -> on_hold
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "on_hold"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "on_hold"
    
    # Test transition: on_hold -> in_progress
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "in_progress"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "in_progress"
    
    # Test transition: in_progress -> completed
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "completed"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "completed"
    assert "completedAt" in updated_task["metadata"]
    
    # Test invalid transition: completed -> in_progress (should fail)
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "in_progress"}
    )
    
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "status" in error_data.get("errors", {})
    
    # Test invalid status value
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/status",
        json={"status": "invalid_status"}
    )
    
    assert response.status_code == 400
    error_data = json.loads(response.data)
    assert "status" in error_data.get("errors", {})

def test_task_assignment(base_url, authenticated_client, test_task, another_user):
    """
    Tests assigning a task to a user.
    """
    # Ensure task starts unassigned or assigned to creator
    assert "assigneeId" not in test_task or test_task["assigneeId"] == test_task["createdBy"]
    
    # Assign the task to another user
    response = authenticated_client.patch(
        f"{base_url}/tasks/{test_task['_id']}/assign",
        json={"assigneeId": another_user["_id"]}
    )
    
    # Verify response status code
    assert response.status_code == 200
    
    # Parse response data
    updated_task = json.loads(response.data)
    
    # Verify assignment
    assert updated_task["assigneeId"] == another_user["_id"]
    
    # Verify status updated to "assigned" if previously "created"
    if test_task["status"] == "created":
        assert updated_task["status"] == "assigned"
    
    # Verify task appears in the assigned user's task list
    # We need to use the another_user's authentication token for this
    headers = {
        "Authorization": f"Bearer {another_user['access_token']}",
        "Content-Type": "application/json"
    }
    
    assigned_tasks_response = test_client.get(
        f"{base_url}/tasks?assignedTo={another_user['_id']}",
        headers=headers
    )
    
    assert assigned_tasks_response.status_code == 200
    assigned_tasks = json.loads(assigned_tasks_response.data)
    
    # Find our task in the assigned tasks
    task_found = any(t["_id"] == test_task["_id"] for t in assigned_tasks["items"])
    assert task_found

def test_list_user_tasks(base_url, authenticated_client, multiple_user_tasks):
    """
    Tests retrieving a user's tasks with filtering and pagination.
    """
    # Get all tasks
    response = authenticated_client.get(
        f"{base_url}/tasks"
    )
    
    assert response.status_code == 200
    task_list = json.loads(response.data)
    
    # Verify response contains expected structure
    assert "items" in task_list
    assert "totalItems" in task_list
    assert "page" in task_list
    assert "pageSize" in task_list
    
    # Verify the task count matches what we expect
    assert len(task_list["items"]) >= len(multiple_user_tasks)
    
    # Test filtering by status
    in_progress_response = authenticated_client.get(
        f"{base_url}/tasks?status=in_progress"
    )
    
    assert in_progress_response.status_code == 200
    in_progress_tasks = json.loads(in_progress_response.data)
    
    # Verify all tasks have the correct status
    for task in in_progress_tasks["items"]:
        assert task["status"] == "in_progress"
    
    # Test filtering by priority
    high_priority_response = authenticated_client.get(
        f"{base_url}/tasks?priority=high"
    )
    
    assert high_priority_response.status_code == 200
    high_priority_tasks = json.loads(high_priority_response.data)
    
    # Verify all tasks have the correct priority
    for task in high_priority_tasks["items"]:
        assert task["priority"] == "high"
    
    # Test filtering by due date range
    now = datetime.datetime.utcnow()
    start_date = (now - datetime.timedelta(days=2)).isoformat()
    end_date = (now + datetime.timedelta(days=2)).isoformat()
    
    date_range_response = authenticated_client.get(
        f"{base_url}/tasks?dueDateStart={start_date}&dueDateEnd={end_date}"
    )
    
    assert date_range_response.status_code == 200
    date_range_tasks = json.loads(date_range_response.data)
    
    # Verify due dates are within range (if due date is set)
    for task in date_range_tasks["items"]:
        if "dueDate" in task and task["dueDate"]:
            task_date = datetime.datetime.fromisoformat(task["dueDate"].replace("Z", "+00:00"))
            assert task_date >= now - datetime.timedelta(days=2)
            assert task_date <= now + datetime.timedelta(days=2)
    
    # Test pagination
    paginated_response = authenticated_client.get(
        f"{base_url}/tasks?page=1&pageSize=2"
    )
    
    assert paginated_response.status_code == 200
    paginated_tasks = json.loads(paginated_response.data)
    
    # Verify pagination data
    assert paginated_tasks["page"] == 1
    assert paginated_tasks["pageSize"] == 2
    assert len(paginated_tasks["items"]) <= 2

def test_overdue_tasks(base_url, authenticated_client, tasks_with_due_dates):
    """
    Tests retrieving overdue tasks.
    """
    # Get overdue tasks
    response = authenticated_client.get(
        f"{base_url}/tasks/overdue"
    )
    
    assert response.status_code == 200
    overdue_tasks = json.loads(response.data)
    
    # Verify we have tasks in the response
    assert len(overdue_tasks["items"]) >= len(tasks_with_due_dates["overdue"])
    
    # Verify all tasks are actually overdue
    now = datetime.datetime.utcnow()
    for task in overdue_tasks["items"]:
        # Skip tasks without due date
        if "dueDate" not in task or not task["dueDate"]:
            continue
        
        # Parse due date and check if it's in the past
        due_date = datetime.datetime.fromisoformat(task["dueDate"].replace("Z", "+00:00"))
        assert due_date < now
        
        # Check task is not completed
        assert task["status"] != "completed"

def test_due_soon_tasks(base_url, authenticated_client, tasks_with_due_dates):
    """
    Tests retrieving tasks due soon.
    """
    # Get tasks due soon (default 24 hours)
    response = authenticated_client.get(
        f"{base_url}/tasks/due-soon"
    )
    
    assert response.status_code == 200
    due_soon_tasks = json.loads(response.data)
    
    # Verify we have tasks in the response
    assert len(due_soon_tasks["items"]) >= 1
    
    # Verify all tasks are due within the next 24 hours
    now = datetime.datetime.utcnow()
    future_24h = now + datetime.timedelta(hours=24)
    
    for task in due_soon_tasks["items"]:
        # Skip tasks without due date
        if "dueDate" not in task or not task["dueDate"]:
            continue
            
        # Parse due date and check if it's within the next 24 hours
        due_date = datetime.datetime.fromisoformat(task["dueDate"].replace("Z", "+00:00"))
        assert due_date >= now
        assert due_date <= future_24h
        
        # Check task is not completed
        assert task["status"] != "completed"
    
    # Test with custom hours parameter (48 hours)
    custom_response = authenticated_client.get(
        f"{base_url}/tasks/due-soon?hours=48"
    )
    
    assert custom_response.status_code == 200
    custom_due_soon = json.loads(custom_response.data)
    
    # Verify all tasks are due within the next 48 hours
    future_48h = now + datetime.timedelta(hours=48)
    
    for task in custom_due_soon["items"]:
        # Skip tasks without due date
        if "dueDate" not in task or not task["dueDate"]:
            continue
            
        # Parse due date and check if it's within the next 48 hours
        due_date = datetime.datetime.fromisoformat(task["dueDate"].replace("Z", "+00:00"))
        assert due_date >= now
        assert due_date <= future_48h
        
        # Check task is not completed
        assert task["status"] != "completed"

def test_subtask_management(base_url, authenticated_client, test_task):
    """
    Tests adding, updating, and removing subtasks.
    """
    # Add a subtask
    subtask_data = {
        "title": "Test Subtask 1"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks/{test_task['_id']}/subtasks",
        json=subtask_data
    )
    
    assert response.status_code == 201
    subtask = json.loads(response.data)
    
    # Verify subtask data
    assert subtask["title"] == subtask_data["title"]
    assert subtask["completed"] is False
    
    # Store subtask ID for later
    subtask_id = subtask["_id"]
    
    # Add another subtask
    subtask_data2 = {
        "title": "Test Subtask 2"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks/{test_task['_id']}/subtasks",
        json=subtask_data2
    )
    
    assert response.status_code == 201
    subtask2 = json.loads(response.data)
    subtask2_id = subtask2["_id"]
    
    # Update first subtask to completed
    update_data = {
        "completed": True
    }
    
    response = authenticated_client.put(
        f"{base_url}/tasks/{test_task['_id']}/subtasks/{subtask_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    updated_subtask = json.loads(response.data)
    assert updated_subtask["completed"] is True
    
    # Delete the second subtask
    response = authenticated_client.delete(
        f"{base_url}/tasks/{test_task['_id']}/subtasks/{subtask2_id}"
    )
    
    assert response.status_code == 200
    
    # Get task to verify subtasks
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert response.status_code == 200
    task = json.loads(response.data)
    
    # Verify the first subtask is present and completed
    found_subtask = False
    for st in task["subtasks"]:
        if st["_id"] == subtask_id:
            found_subtask = True
            assert st["completed"] is True
    
    assert found_subtask
    
    # Verify the second subtask was removed
    for st in task["subtasks"]:
        assert st["_id"] != subtask2_id

def test_task_dependencies(base_url, authenticated_client, test_task, second_test_task):
    """
    Tests managing task dependencies.
    """
    # Create a dependency - test_task depends on second_test_task
    dependency_data = {
        "taskId": second_test_task["_id"],
        "type": "blocks"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks/{test_task['_id']}/dependencies",
        json=dependency_data
    )
    
    assert response.status_code == 200
    
    # Get the task to verify dependency
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert response.status_code == 200
    task = json.loads(response.data)
    
    # Verify dependency exists
    assert "dependencies" in task
    assert any(d["taskId"] == second_test_task["_id"] and d["type"] == "blocks" for d in task["dependencies"])
    
    # Get the second task to verify reverse dependency
    response = authenticated_client.get(
        f"{base_url}/tasks/{second_test_task['_id']}"
    )
    
    assert response.status_code == 200
    second_task = json.loads(response.data)
    
    # Verify reverse dependency exists
    assert "dependencies" in second_task
    assert any(d["taskId"] == test_task["_id"] and d["type"] == "is-blocked-by" for d in second_task["dependencies"])
    
    # Test circular dependency prevention
    # Try to create opposite dependency - should fail
    reverse_dependency = {
        "taskId": test_task["_id"],
        "type": "blocks"
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks/{second_test_task['_id']}/dependencies",
        json=reverse_dependency
    )
    
    # This should fail because it would create a circular dependency
    assert response.status_code == 400
    
    # Remove the dependency
    response = authenticated_client.delete(
        f"{base_url}/tasks/{test_task['_id']}/dependencies/{second_test_task['_id']}"
    )
    
    assert response.status_code == 200
    
    # Verify dependency is removed from both tasks
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    assert response.status_code == 200
    task = json.loads(response.data)
    assert not any(d["taskId"] == second_test_task["_id"] for d in task.get("dependencies", []))
    
    response = authenticated_client.get(
        f"{base_url}/tasks/{second_test_task['_id']}"
    )
    assert response.status_code == 200
    second_task = json.loads(response.data)
    assert not any(d["taskId"] == test_task["_id"] for d in second_task.get("dependencies", []))

def test_task_attachments(base_url, authenticated_client, test_task, test_file):
    """
    Tests adding and removing file attachments.
    """
    # Add an attachment
    attachment_data = {
        "fileId": test_file["_id"],
        "fileName": test_file["name"]
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks/{test_task['_id']}/attachments",
        json=attachment_data
    )
    
    assert response.status_code == 201
    attachment = json.loads(response.data)
    
    # Verify attachment data
    assert attachment["fileId"] == test_file["_id"]
    assert attachment["fileName"] == test_file["name"]
    
    # Get task to verify attachment
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert response.status_code == 200
    task = json.loads(response.data)
    
    # Verify attachment exists in task
    assert "attachments" in task
    assert any(a["fileId"] == test_file["_id"] for a in task["attachments"])
    
    # Remove the attachment
    response = authenticated_client.delete(
        f"{base_url}/tasks/{test_task['_id']}/attachments/{test_file['_id']}"
    )
    
    assert response.status_code == 200
    
    # Get task to verify attachment removed
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert response.status_code == 200
    task = json.loads(response.data)
    
    # Verify attachment is gone
    assert not any(a["fileId"] == test_file["_id"] for a in task.get("attachments", []))

def test_search_tasks(base_url, authenticated_client, multiple_user_tasks):
    """
    Tests searching for tasks with different criteria.
    """
    # Search for tasks by keyword
    search_term = "Task"  # Should match most task titles
    
    response = authenticated_client.get(
        f"{base_url}/tasks/search?q={search_term}"
    )
    
    assert response.status_code == 200
    search_results = json.loads(response.data)
    
    # Verify we have search results
    assert len(search_results["items"]) > 0
    
    # Verify results contain the search term in title or description
    for task in search_results["items"]:
        assert (search_term.lower() in task["title"].lower() or 
                search_term.lower() in task["description"].lower())
    
    # Test search with combined filters
    response = authenticated_client.get(
        f"{base_url}/tasks/search?q={search_term}&status=in_progress&priority=high"
    )
    
    assert response.status_code == 200
    filtered_results = json.loads(response.data)
    
    # Verify results match all criteria
    for task in filtered_results["items"]:
        assert search_term.lower() in task["title"].lower() or search_term.lower() in task["description"].lower()
        assert task["status"] == "in_progress"
        assert task["priority"] == "high"
    
    # Test search with project filter
    project_id = multiple_user_tasks[0]["projectId"]
    if project_id:
        response = authenticated_client.get(
            f"{base_url}/tasks/search?projectId={project_id}"
        )
        
        assert response.status_code == 200
        project_results = json.loads(response.data)
        
        # Verify results are from the specified project
        for task in project_results["items"]:
            assert task["projectId"] == project_id

def test_task_deletion(base_url, authenticated_client, test_task):
    """
    Tests task deletion.
    """
    # Delete the task
    response = authenticated_client.delete(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    
    # Verify success message
    assert "success" in result
    assert result["success"] is True
    
    # Try to get the deleted task
    response = authenticated_client.get(
        f"{base_url}/tasks/{test_task['_id']}"
    )
    
    # Should return not found (404) or indicate the task is deleted
    assert response.status_code in [404, 200]
    
    if response.status_code == 200:
        task = json.loads(response.data)
        assert task.get("status") == "deleted" or task.get("isDeleted") is True

def test_complete_task_workflow(base_url, authenticated_client, test_project, another_user):
    """
    Tests a complete task workflow from creation to completion.
    """
    # Step 1: Create a new task with project association
    task_data = {
        "title": "Complete Workflow Test Task",
        "description": "This task tests the entire workflow",
        "priority": "high",
        "projectId": test_project["_id"]
    }
    
    response = authenticated_client.post(
        f"{base_url}/tasks",
        json=task_data
    )
    
    assert response.status_code == 201
    task = json.loads(response.data)
    task_id = task["_id"]
    
    # Verify initial task status
    assert task["status"] == "created"
    
    # Step 2: Assign task to another user
    assign_data = {
        "assigneeId": another_user["_id"]
    }
    
    response = authenticated_client.patch(
        f"{base_url}/tasks/{task_id}/assign",
        json=assign_data
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    
    # Verify task is assigned and status updated
    assert updated_task["assigneeId"] == another_user["_id"]
    assert updated_task["status"] == "assigned"
    
    # Step 3: Update task status to in progress
    status_data = {
        "status": "in_progress"
    }
    
    response = authenticated_client.patch(
        f"{base_url}/tasks/{task_id}/status",
        json=status_data
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "in_progress"
    
    # Step 4: Add subtasks
    subtasks = [
        {"title": "Workflow Subtask 1"},
        {"title": "Workflow Subtask 2"},
        {"title": "Workflow Subtask 3"}
    ]
    
    subtask_ids = []
    for subtask_data in subtasks:
        response = authenticated_client.post(
            f"{base_url}/tasks/{task_id}/subtasks",
            json=subtask_data
        )
        
        assert response.status_code == 201
        subtask = json.loads(response.data)
        subtask_ids.append(subtask["_id"])
    
    # Step 5: Complete first subtask
    response = authenticated_client.put(
        f"{base_url}/tasks/{task_id}/subtasks/{subtask_ids[0]}",
        json={"completed": True}
    )
    
    assert response.status_code == 200
    
    # Get task to check completion percentage
    response = authenticated_client.get(
        f"{base_url}/tasks/{task_id}"
    )
    
    assert response.status_code == 200
    task = json.loads(response.data)
    
    # Verify one of three subtasks is completed
    completed_count = sum(1 for s in task["subtasks"] if s["completed"])
    assert completed_count == 1
    
    # Step 6: Move task to review
    response = authenticated_client.patch(
        f"{base_url}/tasks/{task_id}/status",
        json={"status": "in_review"}
    )
    
    assert response.status_code == 200
    updated_task = json.loads(response.data)
    assert updated_task["status"] == "in_review"
    
    # Step 7: Complete the task
    response = authenticated_client.patch(
        f"{base_url}/tasks/{task_id}/status",
        json={"status": "completed"}
    )
    
    assert response.status_code == 200
    completed_task = json.loads(response.data)
    
    # Verify task is completed
    assert completed_task["status"] == "completed"
    assert "completedAt" in completed_task["metadata"]
    
    # Verify task appears in completed tasks list
    response = authenticated_client.get(
        f"{base_url}/tasks?status=completed"
    )
    
    assert response.status_code == 200
    completed_tasks = json.loads(response.data)
    
    # Find our task in the completed tasks
    task_found = any(t["_id"] == task_id for t in completed_tasks["items"])
    assert task_found