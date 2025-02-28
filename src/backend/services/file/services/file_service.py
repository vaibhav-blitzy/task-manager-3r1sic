"""
Core service that manages file operations in the Task Management System, providing a high-level API for file uploads, downloads, processing, and management. Coordinates storage operations, virus scanning, and maintains file metadata.
"""

# Standard library imports
import typing  # Type hints for better code documentation
import uuid  # Generate unique identifiers for files
import mimetypes  # File type detection and validation
import os  # File path operations and environment access
from datetime import datetime  # Date/time operations for file timestamps

# Third-party imports

# Internal imports
from ..models.file import File, get_file_by_id, get_files_by_user, search_files  # File document model for database operations
from ..models.attachment import Attachment, get_attachments_by_file, get_attachments_by_entity  # Attachment document model for linking files to entities
from .storage_service import StorageService  # Handles low-level storage operations with AWS S3 or similar
from .scanner_service import ScannerService  # Provides virus/malware scanning for uploaded files
from ..config import get_config  # Retrieve environment-specific configuration
from ....common.logging.logger import get_logger  # Get configured logger for the module
from ....common.events.event_bus import EventBus, create_event  # Publish events for file operations
from ....common.exceptions.api_exceptions import ValidationError, NotFoundError, StorageError  # Exception for validation failures

# Initialize logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

# Initialize event bus
event_bus = EventBus()

# Define maximum file size from config
MAX_FILE_SIZE = config.get('FILE_SERVICE', {}).get('MAX_FILE_SIZE', 25 * 1024 * 1024)

# Define allowed file types from config
ALLOWED_FILE_TYPES = config.get('FILE_SERVICE', {}).get('ALLOWED_FILE_TYPES', [])


class FileService:
    """
    Core service that coordinates file operations including upload, download, scanning, and management in the Task Management System
    """

    def __init__(self):
        """
        Initialize the file service with storage and scanner services
        """
        # Create instance of StorageService for managing file storage operations
        self._storage_service = StorageService()
        # Create instance of ScannerService for scanning uploaded files
        self._scanner_service = ScannerService(self._storage_service)
        # Load configuration from environment
        self._config = config
        # Log successful initialization of the file service
        logger.info("FileService initialized")

    def create_file(self, file_data: dict, user_id: str) -> dict:
        """
        Create a new file metadata entry and generate upload URL

        Args:
            file_data (dict): File metadata
            user_id (str): User ID

        Returns:
            dict: File metadata with upload information
        """
        # Validate file metadata (name, size, type)
        if not all(key in file_data for key in ("name", "size", "type")):
            raise ValidationError("Missing required fields in file metadata")

        # Check file size against MAX_FILE_SIZE limit
        if file_data["size"] > MAX_FILE_SIZE:
            raise ValidationError(f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE} bytes")

        # Validate content type against ALLOWED_FILE_TYPES
        if file_data["type"] not in ALLOWED_FILE_TYPES:
            raise ValidationError(f"File type {file_data['type']} is not allowed")

        # Generate a unique storage key using storage service
        storage_key = self._storage_service.generate_storage_key(user_id, file_data["name"])

        # Create new File document with initial status 'uploading'
        file = File(data={
            "name": file_data["name"],
            "size": file_data["size"],
            "type": file_data["type"],
            "storageKey": storage_key,
        })

        # Set uploadedBy to provided user_id
        file.set("metadata", {"uploadedBy": user_id, "uploadedAt": datetime.utcnow()})

        # Get presigned upload URL from storage service
        upload_info = self._storage_service.generate_presigned_upload_url(user_id, file_data["name"], file_data["size"], file_data["type"])
        file.set("url", upload_info["url"])

        # Save file metadata to database
        file_id = file.save()

        # Publish file.created event
        event = create_event(
            event_type="file.created",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.created", event)

        # Return file metadata with upload URL and instructions
        file_data = file.to_dict()
        file_data.update(upload_info)
        return file_data

    def confirm_upload(self, file_id: str) -> dict:
        """
        Confirm file upload completion and initiate processing

        Args:
            file_id (str): File ID

        Returns:
            dict: Updated file metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Verify file is in 'uploading' status
        if file.get("status") != "uploading":
            raise ValidationError(f"File with id {file_id} is not in 'uploading' status")

        # Check with storage service if file exists in storage
        if not self._storage_service.check_file_exists(file.get("storageKey")):
            raise StorageError(f"File with id {file_id} does not exist in storage")

        # Update file status to 'processing'
        file.update_status("processing")

        # Save file to database
        file.save()

        # Initiate asynchronous file processing (scanning)
        self.process_file(file_id)

        # Return updated file metadata
        return file.to_dict()

    def process_file(self, file_id: str) -> dict:
        """
        Process an uploaded file, including virus scanning and preparing it for use

        Args:
            file_id (str): File ID

        Returns:
            dict: Processing result with updated file metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Verify file is in 'processing' status
        if file.get("status") != "processing":
            raise ValidationError(f"File with id {file_id} is not in 'processing' status")

        # Scan file for viruses/malware using scanner service
        scan_result = self._scanner_service.scan_file(file.get("storageKey"))

        # If scan is clean, move file from quarantine to clean storage
        if scan_result["status"] == "clean":
            # Update file metadata with storage information
            file.update_scan_status("clean")
            # Update file status to 'ready'
            file.update_status("ready")
        else:
            # Update file metadata with scan results
            file.update_scan_status(scan_result["status"])
            # Update file status to 'error'
            file.update_status("error")

        # Save updated file to database
        file.save()

        # Generate preview if applicable
        # self.generate_preview(file_id)

        # Publish file.processed event
        event = create_event(
            event_type="file.processed",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.processed", event)

        # Return updated file metadata
        return file.to_dict()

    def get_file(self, file_id: str) -> dict:
        """
        Retrieve file metadata by ID

        Args:
            file_id (str): File ID

        Returns:
            dict: File metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Return file metadata as dictionary
        return file.to_dict()

    def get_download_url(self, file_id: str, expiry_seconds: int) -> dict:
        """
        Generate a time-limited download URL for a file

        Args:
            file_id (str): File ID
            expiry_seconds (int): Expiry seconds

        Returns:
            dict: Download information with URL
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Verify file is in 'ready' status
        if file.get("status") != "ready":
            raise ValidationError(f"File with id {file_id} is not in 'ready' status")

        # Increment file access count
        file.increment_access_count()

        # Save file metadata update
        file.save()

        # Generate presigned download URL from storage service
        download_url = self._storage_service.generate_presigned_download_url(file.get("storageKey"), expiry_seconds)

        # Publish file.downloaded event
        event = create_event(
            event_type="file.downloaded",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.downloaded", event)

        # Return download URL and metadata
        return {"url": download_url, "metadata": file.to_dict()}

    def delete_file(self, file_id: str, force: bool) -> bool:
        """
        Delete a file from the system

        Args:
            file_id (str): File ID
            force (bool): Force deletion

        Returns:
            bool: True if deletion was successful
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Check for entity attachments to this file
        attachments = get_attachments_by_file(file_id)
        if attachments and not force:
            raise ValidationError(f"File with id {file_id} is attached to entities. Use force=True to delete anyway.")

        # Delete file from storage using storage service
        if not self._storage_service.delete_file(file.get("storageKey")):
            raise StorageError(f"Failed to delete file from storage: {file.get('storageKey')}")

        # Delete file metadata from database
        file.delete()

        # Publish file.deleted event
        event = create_event(
            event_type="file.deleted",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.deleted", event)

        # Return True on successful deletion
        return True

    def create_attachment(self, file_id: str, entity_type: str, entity_id: str, user_id: str) -> dict:
        """
        Link a file to an entity (task, project, comment)

        Args:
            file_id (str): File ID
            entity_type (str): Entity type
            entity_id (str): Entity ID
            user_id (str): User ID

        Returns:
            dict: Created attachment metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Validate entity_type is supported
        if entity_type not in ["task", "project", "comment"]:
            raise ValidationError(f"Entity type {entity_type} is not supported")

        # Create new Attachment object linking file to entity
        attachment = Attachment(data={
            "fileId": file_id,
            "entityType": entity_type,
            "entityId": entity_id,
            "name": file.get("name"),
            "contentType": file.get("type"),
            "size": file.get("size"),
        })

        # Set added_by to provided user_id
        attachment.set("uploadedBy", user_id)
        attachment.set("uploadedAt", datetime.utcnow())

        # Save attachment to database
        attachment.save()

        # Publish attachment.created event
        event = create_event(
            event_type="attachment.created",
            payload=attachment.to_dict(),
            source="file_service"
        )
        event_bus.publish("attachment.created", event)

        # Return attachment metadata
        return attachment.to_dict()

    def get_file_attachments(self, file_id: str) -> list:
        """
        Get all attachments for a specific file

        Args:
            file_id (str): File ID

        Returns:
            list: List of attachment metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Get all attachments for this file
        attachments = get_attachments_by_file(file_id)

        # Return list of attachment metadata as dictionaries
        return [attachment.to_dict() for attachment in attachments]

    def get_entity_attachments(self, entity_type: str, entity_id: str) -> list:
        """
        Get all file attachments for a specific entity

        Args:
            entity_type (str): Entity type
            entity_id (str): Entity ID

        Returns:
            list: List of attachment metadata with file details
        """
        # Validate entity_type is supported
        if entity_type not in ["task", "project", "comment"]:
            raise ValidationError(f"Entity type {entity_type} is not supported")

        # Get all attachments for this entity
        attachments = get_attachments_by_entity(entity_type, entity_id)

        # For each attachment, fetch the associated file details
        attachment_list = []
        for attachment in attachments:
            file = get_file_by_id(attachment.get("fileId"))
            if file:
                attachment_data = attachment.to_dict()
                attachment_data["file"] = file.to_dict()
                attachment_list.append(attachment_data)

        # Return list of attachment metadata with embedded file details
        return attachment_list

    def delete_attachment(self, attachment_id: str) -> bool:
        """
        Remove link between file and entity

        Args:
            attachment_id (str): Attachment ID

        Returns:
            bool: True if deletion was successful
        """
        # Retrieve attachment by ID, raise NotFoundError if not found
        attachment = get_attachment_by_id(attachment_id)
        if not attachment:
            raise NotFoundError(f"Attachment with id {attachment_id} not found")

        # Delete attachment from database
        attachment.delete()

        # Publish attachment.deleted event
        event = create_event(
            event_type="attachment.deleted",
            payload=attachment.to_dict(),
            source="file_service"
        )
        event_bus.publish("attachment.deleted", event)

        # Return True on successful deletion
        return True

    def update_file_metadata(self, file_id: str, metadata: dict) -> dict:
        """
        Update file metadata fields

        Args:
            file_id (str): File ID
            metadata (dict): Metadata

        Returns:
            dict: Updated file metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Validate metadata update fields (only allowed fields)
        allowed_metadata_fields = ["description", "tags"]
        for key in metadata:
            if key not in allowed_metadata_fields:
                raise ValidationError(f"Metadata field {key} is not allowed")

        # Apply changes to file document
        file.update(metadata)

        # Save updated file to database
        file.save()

        # Publish file.updated event
        event = create_event(
            event_type="file.updated",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.updated", event)

        # Return updated file metadata
        return file.to_dict()

    def update_file_access_level(self, file_id: str, access_level: str) -> dict:
        """
        Update file access level (private, shared, public)

        Args:
            file_id (str): File ID
            access_level (str): Access level

        Returns:
            dict: Updated file metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Validate access_level is valid (private, shared, public)
        if access_level not in ["private", "shared", "public"]:
            raise ValidationError(f"Access level {access_level} is not valid")

        # Update file access level
        file.update_access_level(access_level)

        # Save updated file to database
        file.save()

        # Publish file.access_changed event
        event = create_event(
            event_type="file.access_changed",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.access_changed", event)

        # Return updated file metadata
        return file.to_dict()

    def add_file_version(self, file_id: str, version_data: dict, user_id: str) -> dict:
        """
        Add a new version to an existing file

        Args:
            file_id (str): File ID
            version_data (dict): Version data
            user_id (str): User ID

        Returns:
            dict: Updated file metadata with version information and upload URL
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Validate version_data (size, type, etc.)
        if not all(key in version_data for key in ("size", "type")):
            raise ValidationError("Missing required fields in version data")

        # Generate a new storage key for the version
        storage_key = self._storage_service.generate_storage_key(user_id, version_data["name"])

        # Get presigned upload URL for the new version
        upload_info = self._storage_service.generate_presigned_upload_url(user_id, version_data["name"], version_data["size"], version_data["type"])

        # Prepare version metadata with user_id as uploader
        version_metadata = {
            "storageKey": storage_key,
            "size": version_data["size"],
            "uploadedBy": user_id,
            "uploadedAt": datetime.utcnow(),
        }

        # Update file with new version
        file.add_version(version_metadata)

        # Save updated file to database
        file.save()

        # Return file metadata with upload information for new version
        file_data = file.to_dict()
        file_data.update(upload_info)
        return file_data

    def confirm_version_upload(self, file_id: str, version_data: dict) -> dict:
        """
        Confirm version upload completion and process the new version

        Args:
            file_id (str): File ID
            version_data (dict): Version data

        Returns:
            dict: Updated file metadata with new version information
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Verify upload existence in storage
        if not self._storage_service.check_file_exists(version_data["storageKey"]):
            raise StorageError(f"Version upload not found in storage: {version_data['storageKey']}")

        # Process uploaded version (virus scanning)
        scan_result = self._scanner_service.scan_file(version_data["storageKey"])

        # Add version to file's version history
        file.add_version(version_data)

        # Update file's current storage key to the new version
        file.update({"storageKey": version_data["storageKey"]})

        # Save updated file to database
        file.save()

        # Publish file.version_added event
        event = create_event(
            event_type="file.version_added",
            payload=file.to_dict(),
            source="file_service"
        )
        event_bus.publish("file.version_added", event)

        # Return updated file metadata
        return file.to_dict()

    def generate_preview(self, file_id: str) -> dict:
        """
        Generate a preview for a file (thumbnails, etc.)

        Args:
            file_id (str): File ID

        Returns:
            dict: Preview metadata
        """
        # Retrieve file by ID, raise NotFoundError if not found
        file = get_file_by_id(file_id)
        if not file:
            raise NotFoundError(f"File with id {file_id} not found")

        # Check if preview generation is supported for file type
        # Implement preview generation logic here
        # For images: create thumbnail
        # For documents: generate image of first page
        # Store preview in appropriate storage location
        # Update file metadata with preview information
        # Return preview metadata
        return {}

    def get_user_files(self, user_id: str, filters: dict, pagination: dict) -> dict:
        """
        Get all files uploaded by a specific user

        Args:
            user_id (str): User ID
            filters (dict): Filters
            pagination (dict): Pagination

        Returns:
            dict: Paginated list of file metadata
        """
        # Call get_files_by_user with user_id and filters
        files = get_files_by_user(user_id, filters, pagination)

        # Apply pagination parameters
        total = len(files)
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 10)
        files = files[skip:skip + limit]

        # Format response with files and pagination info
        return {
            "results": [file.to_dict() for file in files],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }

    def search_user_files(self, user_id: str, search_criteria: dict, pagination: dict) -> dict:
        """
        Search for files matching criteria for a specific user

        Args:
            user_id (str): User ID
            search_criteria (dict): Search criteria
            pagination (dict): Pagination

        Returns:
            dict: Search results with pagination
        """
        # Add user_id to search criteria
        search_criteria["uploadedBy"] = user_id

        # Call search_files with enhanced search criteria
        search_results = search_files(search_criteria, pagination)

        # Apply pagination parameters
        total = search_results["pagination"]["total"]
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 10)

        # Return search results with pagination info
        return {
            "results": [file.to_dict() for file in search_results["results"]],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }

    def health_check(self) -> dict:
        """
        Check health of the file service and its dependencies

        Returns:
            dict: Health status information
        """
        # Check storage service health
        storage_health = self._storage_service.health_check()

        # Check scanner service health if enabled
        scanner_health = None
        if self._scanner_service._enabled:
            scanner_health = self._scanner_service.verify_scanner_health()

        # Check database connectivity
        # Compile health status information
        health_status = {
            "storage": storage_health,
            "scanner": scanner_health,
            "database": "OK"  # Placeholder for actual database check
        }

        # Return health status dictionary with component details
        return health_status