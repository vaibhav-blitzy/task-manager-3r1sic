"""
Provides pytest fixtures specifically for testing the Task service API endpoints,
models, and business logic. These fixtures include mock databases, authenticated
test clients, and sample test data for tasks and comments.
"""
# Third-party imports
import pytest  # pytest-7.4.x
import mongomock  # mongomock-4.1.x
from bson import ObjectId  # pymongo-4.3.x
from datetime import datetime  # standard library
import uuid  # standard library

# Internal imports
from ....common.testing.fixtures import app, client, mongo_db, redis_cache, auth_headers, test_user, create_test_task, create_test_comment  # src/backend/common/testing/fixtures.py
from ..app import create_app  # src/backend/services/task/app.py
from ..models.task import Task  # src/backend/services/task/models/task.py
from ..models.comment import Comment  # src/backend/services/task/models/comment.py
from ....common.testing.mocks import mock_auth_middleware  # src/backend/common/testing/mocks.py

# Global constants for test collections
TASK_COLLECTION = "tasks"
COMMENT_COLLECTION = "comments"

@pytest.fixture
def task_app():
    """
    Creates a Flask test application for the Task service
    """
    # Create task service application with testing configuration
    app = create_app("testing")

    # Apply test-specific configuration and settings
    app.config['TESTING'] = True

    # Return the configured application
    return app

@pytest.fixture
def task_client(task_app):
    """
    Creates a Flask test client specifically for the Task service
    """
    # Create test client from task_app
    client = task_app.test_client()

    # Configure client for JSON requests/responses
    client.environ_base['CONTENT_TYPE'] = 'application/json'

    # Return the configured test client
    return client

@pytest.fixture
def authenticated_task_client(task_client, test_user, auth_headers):
    """
    Creates a Flask test client with valid authentication headers
    """
    # Create test client with authentication headers
    client = task_client

    # Mock authentication middleware to bypass actual JWT verification
    with mock_auth_middleware():
        # Configure client to include auth headers in all requests
        client.environ_base.update(auth_headers)

        # Return the authenticated test client
        return client

@pytest.fixture
def mock_task_db(mongo_db):
    """
    Creates a mock task database for unit testing
    """
    # Get mock database instance
    db = mongo_db

    # Ensure task collection exists
    if "tasks" not in db.list_collection_names():
        db.create_collection("tasks")

    # Ensure comment collection exists
    if "comments" not in db.list_collection_names():
        db.create_collection("comments")

    # Return the configured mock database
    return db

@pytest.fixture
def test_task(mock_task_db, test_user):
    """
    Creates a single test task for task-related tests
    """
    # Create test task data with title, description, status, and priority
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"]
    }

    # Set test_user as creator and assignee
    # Set appropriate creation timestamps
    # Create Task instance and save to database
    task = Task.from_dict(task_data)
    mock_task_db["tasks"].insert_one(task.to_dict())

    # Return the created task document
    return task.to_dict()

@pytest.fixture
def test_tasks(mock_task_db, test_user):
    """
    Creates multiple test tasks for testing listing and filtering
    """
    # Create 5 different test tasks with varying properties
    tasks_data = [
        {
            "title": "Task 1",
            "description": "Description 1",
            "status": "in_progress",
            "priority": "high",
            "createdBy": test_user["_id"],
            "assigneeId": test_user["_id"],
            "dueDate": datetime(2024, 1, 20)
        },
        {
            "title": "Task 2",
            "description": "Description 2",
            "status": "completed",
            "priority": "low",
            "createdBy": test_user["_id"],
            "assigneeId": test_user["_id"],
            "dueDate": datetime(2024, 1, 25)
        },
        {
            "title": "Task 3",
            "description": "Description 3",
            "status": "created",
            "priority": "medium",
            "createdBy": test_user["_id"],
            "assigneeId": test_user["_id"],
            "dueDate": datetime(2024, 2, 1)
        },
        {
            "title": "Task 4",
            "description": "Description 4",
            "status": "assigned",
            "priority": "urgent",
            "createdBy": test_user["_id"],
            "assigneeId": test_user["_id"],
            "dueDate": datetime(2024, 2, 5)
        },
        {
            "title": "Task 5",
            "description": "Description 5",
            "status": "in_progress",
            "priority": "low",
            "createdBy": test_user["_id"],
            "assigneeId": test_user["_id"],
            "dueDate": datetime(2024, 2, 10)
        }
    ]

    # Vary status, priority, and due dates across tasks
    # Set test_user as creator for all tasks
    # Vary assignee across tasks
    # Save all tasks to database
    tasks = []
    for task_data in tasks_data:
        task = Task.from_dict(task_data)
        mock_task_db["tasks"].insert_one(task.to_dict())
        tasks.append(task.to_dict())

    # Return list of created task documents
    return tasks

@pytest.fixture
def test_comment(mock_task_db, test_user, test_task):
    """
    Creates a single test comment for comment-related tests
    """
    # Create test comment data with content
    comment_data = {
        "content": "This is a test comment",
        "userId": test_user["_id"],
        "taskId": test_task["_id"]
    }

    # Associate comment with test_task
    # Set test_user as comment creator
    # Create Comment instance and save to database
    comment = Comment.from_dict(comment_data)
    mock_task_db["comments"].insert_one(comment.to_dict())

    # Return the created comment document
    return comment.to_dict()

@pytest.fixture
def test_comments(mock_task_db, test_user, test_task):
    """
    Creates multiple test comments for testing comment listing
    """
    # Create 3 different test comments with varying content
    comments_data = [
        {
            "content": "Comment 1",
            "userId": test_user["_id"],
            "taskId": test_task["_id"]
        },
        {
            "content": "Comment 2",
            "userId": test_user["_id"],
            "taskId": test_task["_id"]
        },
        {
            "content": "Comment 3",
            "userId": test_user["_id"],
            "taskId": test_task["_id"]
        }
    ]

    # Associate all comments with the same test_task
    # Set test_user as creator for all comments
    # Save all comments to database
    comments = []
    for comment_data in comments_data:
        comment = Comment.from_dict(comment_data)
        mock_task_db["comments"].insert_one(comment.to_dict())
        comments.append(comment.to_dict())

    # Return list of created comment documents
    return comments

@pytest.fixture
def test_task_with_comments(mock_task_db, test_user):
    """
    Creates a test task with associated comments
    """
    # Create test task data with title, description, status, priority
    task_data = {
        "title": "Test Task with Comments",
        "description": "This task has comments",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"]
    }

    # Create Task instance and save to database
    task = Task.from_dict(task_data)
    mock_task_db["tasks"].insert_one(task.to_dict())

    # Create multiple comments associated with this task
    comments_data = [
        {
            "content": "Comment 1",
            "userId": test_user["_id"],
            "taskId": task.get_id()
        },
        {
            "content": "Comment 2",
            "userId": test_user["_id"],
            "taskId": task.get_id()
        }
    ]

    # Add comment references to the task
    for comment_data in comments_data:
        comment = Comment.from_task_user(task_id=task.get_id(), user_id=test_user["_id"], content=comment_data["content"])
        mock_task_db["comments"].insert_one(comment.to_dict())
        task.add_comment_reference(comment.get_id())
    task.save()

    # Return the task document with comment references
    return task.to_dict()

@pytest.fixture
def task_with_subtasks(mock_task_db, test_user):
    """
    Creates a test task with multiple subtasks
    """
    # Create test task data with title, description, status, priority
    task_data = {
        "title": "Test Task with Subtasks",
        "description": "This task has subtasks",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "subtasks": [
            {"id": "subtask1", "title": "Subtask 1", "completed": True},
            {"id": "subtask2", "title": "Subtask 2", "completed": False}
        ]
    }

    # Create Task instance and save to database
    task = Task.from_dict(task_data)
    mock_task_db["tasks"].insert_one(task.to_dict())

    # Add multiple subtasks with varying completion status
    # Save updated task with subtasks
    # Return the task document with subtasks
    return task.to_dict()

@pytest.fixture
def tasks_with_dependencies(mock_task_db, test_user):
    """
    Creates multiple tasks with dependency relationships
    """
    # Create multiple test tasks
    task1_data = {
        "title": "Task 1",
        "description": "Task 1",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"]
    }
    task2_data = {
        "title": "Task 2",
        "description": "Task 2",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"]
    }
    task3_data = {
        "title": "Task 3",
        "description": "Task 3",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"]
    }

    task1 = Task.from_dict(task1_data)
    mock_task_db["tasks"].insert_one(task1.to_dict())
    task2 = Task.from_dict(task2_data)
    mock_task_db["tasks"].insert_one(task2.to_dict())
    task3 = Task.from_dict(task3_data)
    mock_task_db["tasks"].insert_one(task3.to_dict())

    # Establish dependency relationships between tasks
    task1.add_dependency(task2.get_id(), "blocks")
    task2.add_dependency(task3.get_id(), "blocks")

    # Add dependency references to tasks
    # Save updated tasks with dependencies
    task1.save()
    task2.save()
    task3.save()

    # Return list of tasks with dependency relationships
    return [task1.to_dict(), task2.to_dict(), task3.to_dict()]

@pytest.fixture
def overdue_tasks(mock_task_db, test_user):
    """
    Creates test tasks with overdue due dates
    """
    # Create test tasks with due dates in the past
    task1_data = {
        "title": "Overdue Task 1",
        "description": "Overdue Task 1",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "dueDate": datetime(2023, 1, 1)
    }
    task2_data = {
        "title": "Overdue Task 2",
        "description": "Overdue Task 2",
        "status": "completed",
        "priority": "low",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "dueDate": datetime(2022, 12, 25)
    }

    # Vary status across tasks (some completed, some not)
    # Save tasks to database
    task1 = Task.from_dict(task1_data)
    mock_task_db["tasks"].insert_one(task1.to_dict())
    task2 = Task.from_dict(task2_data)
    mock_task_db["tasks"].insert_one(task2.to_dict())

    # Return list of created task documents
    return [task1.to_dict(), task2.to_dict()]

@pytest.fixture
def due_soon_tasks(mock_task_db, test_user):
    """
    Creates test tasks with due dates in the near future
    """
    # Create test tasks with due dates within 24 hours
    task1_data = {
        "title": "Due Soon Task 1",
        "description": "Due Soon Task 1",
        "status": "in_progress",
        "priority": "medium",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "dueDate": datetime.now() + datetime.timedelta(hours=12)
    }
    task2_data = {
        "title": "Due Soon Task 2",
        "description": "Due Soon Task 2",
        "status": "assigned",
        "priority": "high",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "dueDate": datetime.now() + datetime.timedelta(hours=20)
    }
    task3_data = {
        "title": "Not Due Soon Task",
        "description": "Not Due Soon Task",
        "status": "created",
        "priority": "low",
        "createdBy": test_user["_id"],
        "assigneeId": test_user["_id"],
        "dueDate": datetime.now() + datetime.timedelta(days=2)
    }

    # Create additional tasks with due dates further in the future
    # Save tasks to database
    task1 = Task.from_dict(task1_data)
    mock_task_db["tasks"].insert_one(task1.to_dict())
    task2 = Task.from_dict(task2_data)
    mock_task_db["tasks"].insert_one(task2.to_dict())
    task3 = Task.from_dict(task3_data)
    mock_task_db["tasks"].insert_one(task3.to_dict())

    # Return list of all created task documents
    return [task1.to_dict(), task2.to_dict(), task3.to_dict()]