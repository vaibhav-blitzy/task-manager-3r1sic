"""
Pytest configuration file for file service tests that provides fixtures for testing file uploads, downloads, attachments, and related functionalities. Includes mocks for storage and scanner services to enable isolated testing of the file service API.
"""

# Standard library imports
import io  # I/O stream operations for simulating file data
import uuid  # Generate unique identifiers for test files
import datetime  # Date and time utilities for test data
from unittest import mock  # Mocking objects and methods for isolated unit testing

# Third-party imports
import pytest  # Testing framework for defining fixtures

# Internal imports
from src.backend.tests.conftest import app  # Base application fixture for testing # 7.4.x
from src.backend.tests.conftest import mock_mongo_client  # Mock MongoDB client fixture # 7.4.x
from src.backend.tests.conftest import mock_redis  # Mock Redis client fixture # 7.4.x
from src.backend.common.testing.fixtures import test_user  # Test user data fixture
from src.backend.common.testing.fixtures import authenticated_client  # Authenticated Flask test client
from src.backend.services.file.models.file import File  # File document model for testing
from src.backend.services.file.models.attachment import Attachment  # Attachment document model for testing
from src.backend.services.file.services.file_service import FileService  # File service implementation to be tested
from src.backend.services.file.services.storage_service import StorageService  # Storage service to be mocked
from src.backend.services.file.services.scanner_service import ScannerService  # Scanner service to be mocked
from src.backend.common.testing.mocks import MockCollection  # Mock MongoDB collection for testing # 7.4.x

# Global test data
TEST_FILE_DATA = {
    "_id": "test_file_id",
    "name": "test_document.pdf",
    "size": 12345,
    "type": "application/pdf",
    "extension": "pdf",
    "storageKey": "test_user_id/test_document.pdf",
    "status": "ready",
    "scanStatus": "clean",
    "accessLevel": "private",
    "uploadedBy": "test_user_id",
    "uploadedAt": "2023-01-01T12:00:00Z",
    "lastUpdated": "2023-01-01T12:00:00Z",
    "lastAccessed": "2023-01-01T12:00:00Z",
    "accessCount": 0,
    "previewAvailable": True,
    "preview": {
        "thumbnail": "https://example.com/thumbnail.jpg",
        "previewType": "image"
    }
}

TEST_ATTACHMENT_DATA = {
    "_id": "test_attachment_id",
    "fileId": "test_file_id",
    "entityId": "test_task_id",
    "entityType": "task",
    "addedBy": "test_user_id",
    "addedAt": "2023-01-01T12:00:00Z"
}


@pytest.fixture
def mock_storage_service():
    """
    Fixture providing a mock storage service for file operations
    """
    with mock.patch("src.backend.services.file.services.file_service.StorageService", autospec=True) as MockStorageService:
        mock_storage_service = MockStorageService.return_value
        mock_storage_service.generate_presigned_upload_url.return_value = {"url": "https://example.com/upload", "fields": {}}
        mock_storage_service.generate_presigned_download_url.return_value = "https://example.com/download"
        mock_storage_service.check_file_exists.return_value = True
        yield mock_storage_service


@pytest.fixture
def mock_scanner_service():
    """
    Fixture providing a mock scanner service for virus scanning
    """
    with mock.patch("src.backend.services.file.services.file_service.ScannerService", autospec=True) as MockScannerService:
        mock_scanner_service = MockScannerService.return_value
        mock_scanner_service.scan_file.return_value = {"status": "clean", "details": "No threats found"}
        yield mock_scanner_service


@pytest.fixture
def file_service(mock_storage_service, mock_scanner_service):
    """
    Fixture providing a file service with mocked dependencies
    """
    return FileService()


@pytest.fixture
def test_file(mock_mongo_client, test_user):
    """
    Fixture providing a test file document
    """
    file_data = create_test_file_data({"uploadedBy": test_user["_id"]})
    file = File.from_dict(file_data)
    mock_mongo_client.db.files.insert_one(file.to_dict())
    return file


@pytest.fixture
def test_attachment(mock_mongo_client, test_file, test_user):
    """
    Fixture providing a test attachment document
    """
    attachment_data = create_test_attachment_data({"fileId": test_file.get_id(), "addedBy": test_user["_id"]})
    attachment = Attachment.from_dict(attachment_data)
    mock_mongo_client.db.attachments.insert_one(attachment.to_dict())
    return attachment


@pytest.fixture
def file_collection():
    """
    Fixture providing a mock file collection
    """
    return MockCollection(name="files")


@pytest.fixture
def attachment_collection():
    """
    Fixture providing a mock attachment collection
    """
    return MockCollection(name="attachments")


@pytest.fixture
def uploaded_file_stream():
    """
    Fixture providing a simulated file upload stream
    """
    return io.BytesIO(b"test file content")


@pytest.fixture
def presigned_url():
    """
    Fixture providing a mock pre-signed URL for S3
    """
    return "https://example.com/presigned_url"


def create_test_file_data(overrides=None):
    """
    Helper function to create test file data with customizable properties

    Args:
        overrides (dict): A dictionary of properties to override in the default file data

    Returns:
        dict: File document data dictionary
    """
    file_data = TEST_FILE_DATA.copy()
    if overrides:
        file_data.update(overrides)
    if "_id" not in file_data:
        file_data["_id"] = str(uuid.uuid4())
    return file_data


def create_test_attachment_data(overrides=None):
    """
    Helper function to create test attachment data with customizable properties

    Args:
        overrides (dict): A dictionary of properties to override in the default attachment data

    Returns:
        dict: Attachment document data dictionary
    """
    attachment_data = TEST_ATTACHMENT_DATA.copy()
    if overrides:
        attachment_data.update(overrides)
    if "_id" not in attachment_data:
        attachment_data["_id"] = str(uuid.uuid4())
    return attachment_data