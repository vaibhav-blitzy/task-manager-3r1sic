"""
Package initialization file for the file service that exposes key components and defines service metadata to facilitate file storage, retrieval, and management within the Task Management System
"""

# Import the version of the file service
__version__ = "0.1.0"

# Import File data model for re-export
from .models.file import File as FileModel # File data model class
from .models.file import get_file_by_id # Utility function for file retrieval

# Import Attachment data model for re-export
from .models.attachment import Attachment as AttachmentModel # Attachment data model class
from .models.attachment import get_attachments_by_entity # Utility function for attachment retrieval

# Import FileService class for re-export
from .services.file_service import FileService # FileService class

# Import StorageService class for re-export
from .services.storage_service import StorageService # StorageService class

# Import ScannerService class and ScanResult enum for re-export
from .services.scanner_service import ScannerService # ScannerService class
from .services.scanner_service import ScanResult # ScanResult enum

# Define __all__ to control what gets imported with *
__all__ = ["FileModel", "AttachmentModel", "FileService", "StorageService", "ScannerService", "ScanResult", "get_file_by_id", "get_attachments_by_entity"]