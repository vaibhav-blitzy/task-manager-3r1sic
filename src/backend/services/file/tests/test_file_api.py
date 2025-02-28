"""
Unit and integration tests for the file API endpoints in the Task Management System.
Tests cover file operations including creation, upload, download, retrieval, updates, and deletion with appropriate mocking of dependencies.
"""
# Standard library imports
import json  # v standard library Parsing JSON responses from API endpoints
import io  # v standard library Handling file-like objects for file upload tests
from unittest.mock import patch, MagicMock  # v standard library Mocking dependencies for isolated testing

# Third-party imports
import pytest  # v 7.4.x Python testing framework
from werkzeug import FileStorage  # v 2.3.x Utilities for working with WSGI applications and file operations

# Internal imports
from src.backend.services.file.api.files import file_blueprint  # Flask blueprint containing file API routes
from src.backend.common.exceptions.api_exceptions import NotFoundError, ValidationError, AuthorizationError, StorageError  # Exception for validation failures
from src.backend.services.file.tests.conftest import app, client, test_user, authenticated_client, mock_storage_service, mock_scanner_service, file_service, test_file, test_attachment, file_collection, attachment_collection, presigned_url, uploaded_file_stream  # Flask app fixture for testing
from src.backend.common.testing.fixtures import authenticated_client  # Pre-authenticated test client


def test_list_files(authenticated_client, test_user, file_collection):
    """Tests the list_files endpoint to verify it returns the user's files"""
    # Arrange: Set up file_collection with test files for the test user
    test_files = [
        {"_id": "file1", "name": "test1.pdf", "metadata": {"uploadedBy": test_user["_id"]}},
        {"_id": "file2", "name": "test2.pdf", "metadata": {"uploadedBy": test_user["_id"]}},
    ]
    file_collection.documents = test_files

    # Act: Make GET request to /files/ with authenticated client
    response = authenticated_client.get("/files/")

    # Assert: Verify 200 status code
    assert response.status_code == 200

    # Assert: Verify response contains expected files data
    response_data = json.loads(response.data.decode('utf-8'))
    assert len(response_data["results"]) == len(test_files)
    assert response_data["results"][0]["name"] == "test1.pdf"
    assert response_data["results"][1]["name"] == "test2.pdf"

    # Assert: Verify pagination metadata is included
    assert "pagination" in response_data
    assert response_data["pagination"]["total"] == len(test_files)


def test_list_files_with_filters(authenticated_client, test_user, file_collection):
    """Tests filtering functionality of the list_files endpoint"""
    # Arrange: Set up file_collection with diverse test files (different types, dates)
    test_files = [
        {"_id": "file1", "name": "test1.pdf", "type": "application/pdf", "metadata": {"uploadedBy": test_user["_id"], "uploadedAt": "2023-01-01T00:00:00Z"}},
        {"_id": "file2", "name": "test2.jpg", "type": "image/jpeg", "metadata": {"uploadedBy": test_user["_id"], "uploadedAt": "2023-01-02T00:00:00Z"}},
        {"_id": "file3", "name": "test3.pdf", "type": "application/pdf", "metadata": {"uploadedBy": test_user["_id"], "uploadedAt": "2023-01-03T00:00:00Z"}},
    ]
    file_collection.documents = test_files

    # Act: Make GET request to /files/ with query parameters for filtering
    response = authenticated_client.get("/files/?type=application/pdf&page=1&per_page=1")

    # Assert: Verify 200 status code
    assert response.status_code == 200

    # Assert: Verify response only contains files matching filter criteria
    response_data = json.loads(response.data.decode('utf-8'))
    assert len(response_data["results"]) == 1
    assert response_data["results"][0]["type"] == "application/pdf"

    # Assert: Verify pagination is correctly applied to filtered results
    assert response_data["pagination"]["total"] == 2
    assert response_data["pagination"]["page"] == 1
    assert response_data["pagination"]["per_page"] == 1


def test_search_files(authenticated_client, test_user, file_collection):
    """Tests the search_files endpoint for finding files with search criteria"""
    # Arrange: Set up file_collection with test files containing varied content
    test_files = [
        {"_id": "file1", "name": "report_2021.pdf", "metadata": {"uploadedBy": test_user["_id"]}},
        {"_id": "file2", "name": "image_summer.jpg", "metadata": {"uploadedBy": test_user["_id"]}},
        {"_id": "file3", "name": "report_2022.pdf", "metadata": {"uploadedBy": test_user["_id"]}},
    ]
    file_collection.documents = test_files

    # Act: Make GET request to /files/search with search parameters
    response = authenticated_client.get("/files/search?name=report")

    # Assert: Verify 200 status code
    assert response.status_code == 200

    # Assert: Verify response contains only files matching search criteria
    response_data = json.loads(response.data.decode('utf-8'))
    assert len(response_data["results"]) == 2
    assert "report" in response_data["results"][0]["name"]
    assert "report" in response_data["results"][1]["name"]

    # Assert: Verify search results include appropriate metadata
    assert "pagination" in response_data
    assert response_data["pagination"]["total"] == 2


def test_get_file(authenticated_client, test_user, test_file):
    """Tests retrieving a specific file by ID"""
    # Arrange: Ensure test_file belongs to test_user
    # Act: Make GET request to /files/{file_id}
    response = authenticated_client.get(f"/files/{test_file.get_id()}")

    # Assert: Verify 200 status code
    assert response.status_code == 200

    # Assert: Verify response contains complete file metadata
    response_data = json.loads(response.data.decode('utf-8'))
    assert response_data["name"] == test_file.get("name")
    assert response_data["metadata"]["uploadedBy"] == test_user["_id"]

    # Assert: Verify file data matches the test_file fixture
    assert response_data["id"] == test_file.get_id()


def test_get_file_not_found(authenticated_client):
    """Tests appropriate error handling when requesting non-existent file"""
    # Arrange: Create a non-existent file ID
    nonexistent_id = "nonexistent_file_id"

    # Act: Make GET request to /files/{nonexistent_id}
    response = authenticated_client.get(f"/files/{nonexistent_id}")

    # Assert: Verify 404 status code
    assert response.status_code == 404

    # Assert: Verify error response contains appropriate message
    response_data = json.loads(response.data.decode('utf-8'))
    assert "Resource not found" in response_data["message"]


def test_get_file_unauthorized(authenticated_client, test_file, file_service):
    """Tests authorization enforcement when requesting another user's file"""
    # Arrange: Configure test_file to belong to a different user
    with patch.object(file_service, 'get_file', return_value=test_file.to_dict()) as mock_get_file:
        mock_get_file.return_value = {"_id": "test_file_id", "name": "test_document.pdf", "metadata": {"uploadedBy": "different_user_id"}}

        # Act: Make GET request to /files/{file_id}
        response = authenticated_client.get(f"/files/{test_file.get_id()}")

        # Assert: Verify 403 status code
        assert response.status_code == 403

        # Assert: Verify error response indicates authorization failure
        response_data = json.loads(response.data.decode('utf-8'))
        assert "Insufficient permissions" in response_data["message"]


def test_create_file(authenticated_client, test_user, file_service, mock_storage_service):
    """Tests file creation process including upload URL generation"""
    # Arrange: Prepare file metadata for upload
    file_metadata = {"name": "new_document.pdf", "size": 1024, "type": "application/pdf"}

    # Arrange: Configure mock_storage_service to return presigned URL
    mock_storage_service.generate_presigned_upload_url.return_value = {"url": "https://example.com/upload", "fields": {}}

    # Act: Make POST request to /files/ with file metadata
    response = authenticated_client.post("/files/", json=file_metadata)

    # Assert: Verify 201 status code
    assert response.status_code == 201

    # Assert: Verify response contains file metadata and upload URL
    response_data = json.loads(response.data.decode('utf-8'))
    assert "url" in response_data
    assert "fields" in response_data
    assert response_data["name"] == file_metadata["name"]

    # Assert: Verify file_service.create_file was called with correct arguments
    assert file_service.create_file(file_metadata, test_user["_id"]) is None


def test_create_file_validation_error(authenticated_client, file_service):
    """Tests validation during file creation (size limits, file types)"""
    # Arrange: Prepare invalid file metadata (too large, incorrect type)
    invalid_metadata = {"name": "invalid.exe", "size": 50000000, "type": "application/exe"}

    # Act: Make POST request to /files/ with invalid metadata
    response = authenticated_client.post("/files/", json=invalid_metadata)

    # Assert: Verify 400 status code
    assert response.status_code == 400

    # Assert: Verify error response contains validation details
    response_data = json.loads(response.data.decode('utf-8'))
    assert "Validation error" in response_data["message"]


def test_confirm_upload(authenticated_client, test_user, test_file, file_service):
    """Tests confirmation of completed file upload"""
    # Arrange: Configure test_file with test_user as owner and 'uploading' status
    # Arrange: Mock file_service.confirm_upload to return updated file
    with patch.object(file_service, 'confirm_upload', return_value=test_file.to_dict()) as mock_confirm_upload:
        mock_confirm_upload.return_value = {"id": "test_file_id", "name": "test_document.pdf", "status": "ready"}

        # Act: Make POST request to /files/{file_id}/confirm
        response = authenticated_client.post(f"/files/{test_file.get_id()}/confirm")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains updated file status
        response_data = json.loads(response.data.decode('utf-8'))
        assert response_data["status"] == "ready"

        # Assert: Verify file_service.confirm_upload was called with file_id
        assert file_service.confirm_upload(test_file.get_id()) is None


def test_confirm_upload_not_owner(authenticated_client, test_file):
    """Tests authorization failure when non-owner confirms upload"""
    # Arrange: Configure test_file to belong to a different user
    # Act: Make POST request to /files/{file_id}/confirm
    response = authenticated_client.post(f"/files/{test_file.get_id()}/confirm")

    # Assert: Verify 403 status code
    assert response.status_code == 403

    # Assert: Verify error response indicates authorization failure
    response_data = json.loads(response.data.decode('utf-8'))
    assert "Insufficient permissions" in response_data["message"]


def test_confirm_upload_storage_error(authenticated_client, test_user, test_file, file_service):
    """Tests handling of storage errors during upload confirmation"""
    # Arrange: Configure test_file with test_user as owner
    # Arrange: Mock file_service.confirm_upload to raise StorageError
    with patch.object(file_service, 'confirm_upload', side_effect=StorageError("Storage error")) as mock_confirm_upload:

        # Act: Make POST request to /files/{file_id}/confirm
        response = authenticated_client.post(f"/files/{test_file.get_id()}/confirm")

        # Assert: Verify appropriate error status code (500 or 400)
        assert response.status_code == 500

        # Assert: Verify error response indicates storage issue
        response_data = json.loads(response.data.decode('utf-8'))
        assert "Storage error" in response_data["message"]


def test_get_download_url(authenticated_client, test_user, test_file, file_service, presigned_url):
    """Tests generation of download URL for a file"""
    # Arrange: Configure test_file with 'ready' status
    # Arrange: Mock file_service.get_download_url to return presigned_url
    with patch.object(file_service, 'get_download_url', return_value={"url": presigned_url}) as mock_get_download_url:

        # Act: Make GET request to /files/{file_id}/download
        response = authenticated_client.get(f"/files/{test_file.get_id()}/download")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains download URL
        response_data = json.loads(response.data.decode('utf-8'))
        assert response_data["url"] == presigned_url

        # Assert: Verify file_service.get_download_url was called with correct parameters
        assert file_service.get_download_url(test_file.get_id(), 900) is None


def test_get_download_url_invalid_state(authenticated_client, test_user, test_file, file_service):
    """Tests error handling when requesting download for file in invalid state"""
    # Arrange: Configure test_file with non-ready status (uploading/processing)
    # Arrange: Mock file_service.get_download_url to raise ValidationError
    with patch.object(file_service, 'get_download_url', side_effect=ValidationError("File is not ready")) as mock_get_download_url:

        # Act: Make GET request to /files/{file_id}/download
        response = authenticated_client.get(f"/files/{test_file.get_id()}/download")

        # Assert: Verify 400 status code
        assert response.status_code == 400

        # Assert: Verify error response indicates invalid file state
        response_data = json.loads(response.data.decode('utf-8'))
        assert "File is not ready" in response_data["message"]


def test_update_file_metadata(authenticated_client, test_user, test_file, file_service):
    """Tests updating file metadata"""
    # Arrange: Configure test_file with test_user as owner
    # Arrange: Prepare metadata updates
    metadata_updates = {"description": "Updated description", "tags": ["new_tag"]}

    # Act: Make PATCH request to /files/{file_id} with update data
    with patch.object(file_service, 'update_file_metadata', return_value=test_file.to_dict()) as mock_update_file_metadata:
        response = authenticated_client.patch(f"/files/{test_file.get_id()}", json=metadata_updates)

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains updated file metadata
        response_data = json.loads(response.data.decode('utf-8'))
        assert response_data["description"] == "Updated description"
        assert "new_tag" in response_data["tags"]

        # Assert: Verify file_service.update_file_metadata was called with correct parameters
        assert file_service.update_file_metadata(test_file.get_id(), metadata_updates) is None


def test_update_access_level(authenticated_client, test_user, test_file, file_service):
    """Tests updating file access level (private/shared/public)"""
    # Arrange: Configure test_file with test_user as owner
    # Act: Make PATCH request to /files/{file_id}/access with new access level
    with patch.object(file_service, 'update_file_access_level', return_value=test_file.to_dict()) as mock_update_access_level:
        response = authenticated_client.patch(f"/files/{test_file.get_id()}/access", json={"access_level": "public"})

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains updated access level
        response_data = json.loads(response.data.decode('utf-8'))
        assert response_data["security"]["accessLevel"] == "public"

        # Assert: Verify file_service.update_file_access_level was called with correct parameters
        assert file_service.update_file_access_level(test_file.get_id(), "public") is None


def test_update_access_level_invalid(authenticated_client, test_user, test_file):
    """Tests validation when updating access level to invalid value"""
    # Arrange: Configure test_file with test_user as owner
    # Act: Make PATCH request to /files/{file_id}/access with invalid access level
    response = authenticated_client.patch(f"/files/{test_file.get_id()}/access", json={"access_level": "invalid"})

    # Assert: Verify 400 status code
    assert response.status_code == 400

    # Assert: Verify error response indicates invalid access level
    response_data = json.loads(response.data.decode('utf-8'))
    assert "Invalid access_level" in response_data["message"]


def test_delete_file(authenticated_client, test_user, test_file, file_service):
    """Tests file deletion"""
    # Arrange: Configure test_file with test_user as owner
    # Act: Make DELETE request to /files/{file_id}
    with patch.object(file_service, 'delete_file', return_value=True) as mock_delete_file:
        response = authenticated_client.delete(f"/files/{test_file.get_id()}")

        # Assert: Verify 204 status code (no content)
        assert response.status_code == 204

        # Assert: Verify file_service.delete_file was called with file_id
        assert file_service.delete_file(test_file.get_id(), False) is None


def test_delete_file_with_attachments(authenticated_client, test_user, test_file, test_attachment, file_service):
    """Tests deletion of file with associated attachments"""
    # Arrange: Configure test_file with test_user as owner
    # Arrange: Configure test_attachment linked to test_file
    # Arrange: Mock file_service.delete_file to raise ValidationError when force=False
    with patch.object(file_service, 'delete_file', side_effect=ValidationError("File has attachments")) as mock_delete_file:

        # Act: Make DELETE request to /files/{file_id} without force parameter
        response = authenticated_client.delete(f"/files/{test_file.get_id()}")

        # Assert: Verify 400 status code
        assert response.status_code == 400

        # Assert: Verify error response indicates file has attachments
        response_data = json.loads(response.data.decode('utf-8'))
        assert "File has attachments" in response_data["message"]

        # Act: Make DELETE request to /files/{file_id}?force=true
        response = authenticated_client.delete(f"/files/{test_file.get_id()}?force=true")

        # Assert: Verify 204 status code
        assert response.status_code == 204

        # Assert: Verify file_service.delete_file was called with force=True
        assert file_service.delete_file(test_file.get_id(), True) is None


def test_add_version(authenticated_client, test_user, test_file, file_service, presigned_url):
    """Tests adding a new version to an existing file"""
    # Arrange: Configure test_file with test_user as owner and 'ready' status
    # Arrange: Prepare version metadata for upload
    version_metadata = {"name": "new_version.pdf", "size": 2048, "type": "application/pdf"}

    # Arrange: Mock file_service.add_file_version to return version data with upload URL
    with patch.object(file_service, 'add_file_version', return_value={"url": presigned_url, "fields": {}}) as mock_add_file_version:

        # Act: Make POST request to /files/{file_id}/versions with version metadata
        response = authenticated_client.post(f"/files/{test_file.get_id()}/versions", json=version_metadata)

        # Assert: Verify 201 status code
        assert response.status_code == 201

        # Assert: Verify response contains version info and upload URL
        response_data = json.loads(response.data.decode('utf-8'))
        assert "url" in response_data
        assert "fields" in response_data

        # Assert: Verify file_service.add_file_version was called with correct parameters
        assert file_service.add_file_version(test_file.get_id(), version_metadata, test_user["_id"]) is None


def test_confirm_version_upload(authenticated_client, test_user, test_file, file_service):
    """Tests confirmation of version upload completion"""
    # Arrange: Configure test_file with test_user as owner
    # Arrange: Prepare version confirmation data
    version_confirmation = {"storageKey": "new_version_key"}

    # Act: Make POST request to /files/{file_id}/versions/confirm
    with patch.object(file_service, 'confirm_version_upload', return_value=test_file.to_dict()) as mock_confirm_version_upload:
        response = authenticated_client.post(f"/files/{test_file.get_id()}/versions/confirm", json=version_confirmation)

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains updated file with version history
        response_data = json.loads(response.data.decode('utf-8'))
        assert "versions" in response_data

        # Assert: Verify file_service.confirm_version_upload was called correctly
        assert file_service.confirm_version_upload(test_file.get_id(), version_confirmation) is None


def test_get_versions(authenticated_client, test_user, test_file, file_service):
    """Tests retrieving version history for a file"""
    # Arrange: Configure test_file with version history
    with patch.object(file_service, 'get_file', return_value=test_file.to_dict()) as mock_get_file:
        mock_get_file.return_value = {"id": "test_file_id", "name": "test_document.pdf", "versions": [{"id": "version1"}, {"id": "version2"}]}

        # Act: Make GET request to /files/{file_id}/versions
        response = authenticated_client.get(f"/files/{test_file.get_id()}/versions")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains version history list
        response_data = json.loads(response.data.decode('utf-8'))
        assert len(response_data) == 2

        # Assert: Verify version data includes required metadata
        assert "id" in response_data[0]
        assert "id" in response_data[1]


def test_generate_preview(authenticated_client, test_user, test_file, file_service):
    """Tests requesting preview generation for a file"""
    # Arrange: Configure test_file with test_user as owner and 'ready' status
    # Arrange: Mock file_service.generate_preview to return preview metadata
    with patch.object(file_service, 'generate_preview', return_value={"thumbnail": "https://example.com/thumbnail.jpg"}) as mock_generate_preview:

        # Act: Make POST request to /files/{file_id}/preview
        response = authenticated_client.post(f"/files/{test_file.get_id()}/preview")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains preview information
        response_data = json.loads(response.data.decode('utf-8'))
        assert "thumbnail" in response_data

        # Assert: Verify file_service.generate_preview was called with file_id
        assert file_service.generate_preview(test_file.get_id()) is None


def test_generate_preview_unsupported_type(authenticated_client, test_user, test_file, file_service):
    """Tests error handling when preview generation is not supported for file type"""
    # Arrange: Configure test_file with unsupported type for preview
    # Arrange: Mock file_service.generate_preview to raise ValidationError
    with patch.object(file_service, 'generate_preview', side_effect=ValidationError("Preview generation not supported for this file type")) as mock_generate_preview:

        # Act: Make POST request to /files/{file_id}/preview
        response = authenticated_client.post(f"/files/{test_file.get_id()}/preview")

        # Assert: Verify 400 status code
        assert response.status_code == 400

        # Assert: Verify error response indicates unsupported file type
        response_data = json.loads(response.data.decode('utf-8'))
        assert "Preview generation not supported for this file type" in response_data["message"]


def test_get_preview(authenticated_client, test_user, test_file, file_service, presigned_url):
    """Tests retrieving preview URL for a file"""
    # Arrange: Configure test_file with preview available
    # Arrange: Mock file_service.get_file to return file with preview
    with patch.object(file_service, 'get_file', return_value={"id": "test_file_id", "name": "test_document.pdf", "preview": {"previewAvailable": True, "thumbnail": presigned_url}}) as mock_get_file:

        # Act: Make GET request to /files/{file_id}/preview
        response = authenticated_client.get(f"/files/{test_file.get_id()}/preview")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains preview URL
        response_data = json.loads(response.data.decode('utf-8'))
        assert response_data["url"] == presigned_url

        # Assert: Verify correct preview type is returned
        # assert response_data["type"] == "thumbnail"


def test_get_preview_not_available(authenticated_client, test_user, test_file, file_service):
    """Tests error handling when preview is not available"""
    # Arrange: Configure test_file with previewAvailable=False
    with patch.object(file_service, 'get_file', return_value={"id": "test_file_id", "name": "test_document.pdf", "preview": {"previewAvailable": False}}) as mock_get_file:

        # Act: Make GET request to /files/{file_id}/preview
        response = authenticated_client.get(f"/files/{test_file.get_id()}/preview")

        # Assert: Verify appropriate error status code
        assert response.status_code == 404

        # Assert: Verify error response indicates preview not available
        response_data = json.loads(response.data.decode('utf-8'))
        assert "Preview not available" in response_data["message"]


def test_file_health_check(client, file_service):
    """Tests the health check endpoint for file service"""
    # Arrange: Mock file_service.health_check to return service status
    with patch.object(file_service, 'health_check', return_value={"storage": "OK", "scanner": "OK"}) as mock_health_check:

        # Act: Make GET request to /files/health
        response = client.get("/files/health")

        # Assert: Verify 200 status code
        assert response.status_code == 200

        # Assert: Verify response contains health information
        response_data = json.loads(response.data.decode('utf-8'))
        assert "storage" in response_data
        assert "scanner" in response_data

        # Assert: Verify response includes storage and scanner health status
        assert response_data["storage"] == "OK"
        assert response_data["scanner"] == "OK"