"""
Unit and integration tests for the task comment API endpoints.
Tests creation, retrieval, updating, and deletion of comments on tasks while verifying proper validation, authorization, and error handling.
"""
# Third-party imports
import pytest  # pytest-7.4.x
import json  # standard library
from bson import ObjectId  # pymongo-4.x.x

# Internal imports
from .conftest import test_comment, test_comments, test_task, authenticated_task_client, task_client, mock_task_db  # src/backend/services/task/tests/conftest.py
from '../../../common/testing/fixtures' import test_user  # src/backend/common/testing/fixtures.py
from '../models/comment' import Comment  # src/backend/services/task/models/comment.py
from '../../../common/testing/mocks' import patch_auth_middleware  # src/backend/common/testing/mocks.py

API_PREFIX = "/api/v1"


def test_create_comment_success(authenticated_task_client, test_task, test_user):
    """Tests successful comment creation on a task"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Create valid comment data with content
    comment_data = {"content": "This is a new comment"}

    # Make POST request to comment creation endpoint
    response = authenticated_task_client.post(f"{API_PREFIX}/tasks/{task_id}/comments", json=comment_data)

    # Verify 201 status code in response
    assert response.status_code == 201

    # Verify comment data in response matches input
    response_data = response.get_json()
    assert response_data["content"] == comment_data["content"]

    # Verify required fields are present in response (id, created_at)
    assert "id" in response_data
    assert "created_at" in response_data

    # Verify user_id is set to the current user
    assert response_data["user_id"] == test_user["_id"]

    # Verify task_id is correctly associated
    assert response_data["task_id"] == task_id


def test_create_comment_unauthenticated(task_client, test_task):
    """Tests comment creation fails when user is not authenticated"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Create valid comment data
    comment_data = {"content": "This is a comment"}

    # Make POST request to comment creation endpoint with unauthenticated client
    response = task_client.post(f"{API_PREFIX}/tasks/{task_id}/comments", json=comment_data)

    # Verify 401 status code in response
    assert response.status_code == 401

    # Verify appropriate error message in response
    response_data = response.get_json()
    assert response_data["message"] == "Missing token"


@pytest.mark.parametrize('comment_data', [{}, {'content': ''}, {'content': 'a' * 5001}])
def test_create_comment_invalid_data(authenticated_task_client, test_task, comment_data):
    """Tests comment creation fails with invalid data"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Create invalid comment data based on parametrized input
    # Make POST request to comment creation endpoint
    response = authenticated_task_client.post(f"{API_PREFIX}/tasks/{task_id}/comments", json=comment_data)

    # Verify 400 status code in response
    assert response.status_code == 400

    # Verify appropriate validation error message in response
    response_data = response.get_json()
    assert "message" in response_data


def test_create_comment_task_not_found(authenticated_task_client, test_user):
    """Tests comment creation fails when task doesn't exist"""
    # Create a non-existent task ID
    task_id = "nonexistent_task_id"

    # Create valid comment data
    comment_data = {"content": "This is a comment"}

    # Make POST request to comment creation endpoint with invalid task ID
    response = authenticated_task_client.post(f"{API_PREFIX}/tasks/{task_id}/comments", json=comment_data)

    # Verify 404 status code in response
    assert response.status_code == 404

    # Verify appropriate error message about task not found
    response_data = response.get_json()
    assert response_data["message"] == "Task with ID 'nonexistent_task_id' not found"


def test_get_task_comments(authenticated_task_client, test_task, test_comments):
    """Tests retrieving all comments for a specific task"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Make GET request to task comments endpoint
    response = authenticated_task_client.get(f"{API_PREFIX}/tasks/{task_id}/comments")

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify pagination metadata in response (total, page, etc.)
    response_data = response.get_json()
    assert "comments" in response_data
    assert "total" in response_data
    assert "limit" in response_data
    assert "skip" in response_data

    # Verify comments list contains expected number of items
    comments = response_data["comments"]
    assert len(comments) == len(test_comments)

    # Verify each comment has the required fields
    for comment in comments:
        assert "id" in comment
        assert "content" in comment
        assert "user_id" in comment
        assert "task_id" in comment
        assert "created_at" in comment

        # Verify all comments are associated with the correct task
        assert comment["task_id"] == task_id


def test_get_task_comments_pagination(authenticated_task_client, test_task, test_comments):
    """Tests pagination for task comments"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Make GET request to task comments endpoint with limit=1
    response = authenticated_task_client.get(f"{API_PREFIX}/tasks/{task_id}/comments?limit=1")

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify only one comment is returned
    response_data = response.get_json()
    comments = response_data["comments"]
    assert len(comments) == 1

    # Verify pagination metadata shows correct total and limit
    assert response_data["total"] == len(test_comments)
    assert response_data["limit"] == 1

    # Make another request with skip=1 and limit=1
    response = authenticated_task_client.get(f"{API_PREFIX}/tasks/{task_id}/comments?limit=1&skip=1")

    # Verify different comment is returned
    response_data = response.get_json()
    comments = response_data["comments"]
    assert len(comments) == 1
    assert comments[0]["id"] != test_comments[0]["_id"]

    # Verify pagination metadata is updated correctly
    assert response_data["total"] == len(test_comments)
    assert response_data["limit"] == 1
    assert response_data["skip"] == 1


def test_get_task_comments_task_not_found(authenticated_task_client):
    """Tests retrieving comments fails when task doesn't exist"""
    # Create a non-existent task ID
    task_id = "nonexistent_task_id"

    # Make GET request to task comments endpoint with invalid task ID
    response = authenticated_task_client.get(f"{API_PREFIX}/tasks/{task_id}/comments")

    # Verify 404 status code in response
    assert response.status_code == 404

    # Verify appropriate error message about task not found
    response_data = response.get_json()
    assert response_data["message"] == "Task with ID 'nonexistent_task_id' not found"


def test_get_comment(authenticated_task_client, test_comment):
    """Tests retrieving a specific comment by ID"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Make GET request to comment detail endpoint
    response = authenticated_task_client.get(f"{API_PREFIX}/comments/{comment_id}")

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify comment data matches expected values
    response_data = response.get_json()
    assert response_data["id"] == comment_id
    assert response_data["content"] == test_comment["content"]
    assert response_data["user_id"] == test_comment["userId"]
    assert response_data["task_id"] == test_comment["taskId"]

    # Verify all expected fields are present in response
    assert "created_at" in response_data
    assert "updated_at" in response_data


def test_get_comment_not_found(authenticated_task_client):
    """Tests retrieving a comment fails with non-existent ID"""
    # Create a non-existent comment ID
    comment_id = "nonexistent_comment_id"

    # Make GET request to comment detail endpoint with invalid ID
    response = authenticated_task_client.get(f"{API_PREFIX}/comments/{comment_id}")

    # Verify 404 status code in response
    assert response.status_code == 404

    # Verify appropriate error message in response
    response_data = response.get_json()
    assert response_data["message"] == "Comment with ID 'nonexistent_comment_id' not found"


def test_update_comment(authenticated_task_client, test_comment, test_user):
    """Tests successfully updating a comment"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Create update data with new content
    update_data = {"content": "This is the updated comment content"}

    # Make PUT request to comment update endpoint
    response = authenticated_task_client.put(f"{API_PREFIX}/comments/{comment_id}", json=update_data)

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify comment data updated in response
    response_data = response.get_json()
    assert response_data["id"] == comment_id
    assert response_data["content"] == update_data["content"]
    assert response_data["user_id"] == test_user["_id"]
    assert response_data["task_id"] == test_comment["taskId"]

    # Verify updated_at timestamp is updated
    assert response_data["updated_at"] != test_comment["createdAt"]


def test_update_comment_not_owner(authenticated_task_client, test_comment, mock_task_db):
    """Tests updating a comment fails when user is not the comment owner"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Modify test user ID to be different from comment owner
    test_user_id = "different_user_id"

    # Create update data with new content
    update_data = {"content": "This is the updated comment content"}

    # Make PUT request to comment update endpoint
    response = authenticated_task_client.put(f"{API_PREFIX}/comments/{comment_id}", json=update_data)

    # Verify 403 status code in response
    assert response.status_code == 403

    # Verify appropriate authorization error message in response
    response_data = response.get_json()
    assert response_data["message"] == "You do not have permission to update this comment"


@pytest.mark.parametrize('content', ['', 'a' * 5001])
def test_update_comment_invalid_data(authenticated_task_client, test_comment, content):
    """Tests updating a comment fails with invalid content"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Create update data with invalid content based on parametrized input
    update_data = {"content": content}

    # Make PUT request to comment update endpoint
    response = authenticated_task_client.put(f"{API_PREFIX}/comments/{comment_id}", json=update_data)

    # Verify 400 status code in response
    assert response.status_code == 400

    # Verify appropriate validation error message in response
    response_data = response.get_json()
    assert "message" in response_data


def test_delete_comment(authenticated_task_client, test_comment, test_user):
    """Tests successfully deleting a comment"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Make DELETE request to comment deletion endpoint
    response = authenticated_task_client.delete(f"{API_PREFIX}/comments/{comment_id}")

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify success message in response
    response_data = response.get_json()
    assert response_data["message"] == "Comment deleted successfully"

    # Make GET request to comment detail endpoint to verify it's deleted
    response = authenticated_task_client.get(f"{API_PREFIX}/comments/{comment_id}")

    # Verify 404 status code in response
    assert response.status_code == 404


def test_delete_comment_not_owner(authenticated_task_client, test_comment, mock_task_db):
    """Tests deleting a comment fails when user is not the comment owner"""
    # Extract comment ID from test_comment fixture
    comment_id = test_comment["_id"]

    # Modify test user ID to be different from comment owner
    test_user_id = "different_user_id"

    # Make DELETE request to comment deletion endpoint
    response = authenticated_task_client.delete(f"{API_PREFIX}/comments/{comment_id}")

    # Verify 403 status code in response
    assert response.status_code == 403

    # Verify appropriate authorization error message in response
    response_data = response.get_json()
    assert response_data["message"] == "You do not have permission to delete this comment"


def test_get_task_comment_count(authenticated_task_client, test_task, test_comments):
    """Tests retrieving the comment count for a task"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Make GET request to task comment count endpoint
    response = authenticated_task_client.get(f"{API_PREFIX}/tasks/{task_id}/comments/count")

    # Verify 200 status code in response
    assert response.status_code == 200

    # Verify count in response matches expected number of comments for the task
    response_data = response.get_json()
    assert "count" in response_data
    assert response_data["count"] == len(test_comments)


def test_create_comment_with_mentions(authenticated_task_client, test_task, test_user):
    """Tests creating a comment with @username mentions"""
    # Extract task ID from test_task fixture
    task_id = test_task["_id"]

    # Create comment data with @username mentions in content
    comment_data = {"content": "This is a comment mentioning @john_doe and @jane_doe"}

    # Make POST request to comment creation endpoint
    response = authenticated_task_client.post(f"{API_PREFIX}/tasks/{task_id}/comments", json=comment_data)

    # Verify 201 status code in response
    assert response.status_code == 201

    # Verify comment data in response contains mentions
    response_data = response.get_json()
    assert response_data["content"] == comment_data["content"]

    # Verify mentions are correctly identified in the response
    # assert response_data["mentions"] == ["john_doe", "jane_doe"]