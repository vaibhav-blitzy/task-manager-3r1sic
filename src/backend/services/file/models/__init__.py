"""
Package initialization file for the file service models.
Exports File and Attachment models and their associated helper functions for use throughout the application.
"""

# Import the File model and related functions
from .file import (
    File,
    get_file_by_id,
    get_files_by_user,
    get_files_by_hash,
    ALLOWED_FILE_TYPES,
    MAX_FILE_SIZE,
    SCAN_STATUSES,
)

# Import the Attachment model and related functions
from .attachment import (
    Attachment,
    get_attachment_by_id,
    get_attachments_by_file,
    get_attachments_by_entity,
    ENTITY_TYPES,
)

# Define exports for the package
__all__ = [
    "File",
    "get_file_by_id",
    "get_files_by_user",
    "get_files_by_hash",
    "Attachment",
    "get_attachment_by_id",
    "get_attachments_by_file",
    "get_attachments_by_entity",
    "ALLOWED_FILE_TYPES",
    "MAX_FILE_SIZE",
    "SCAN_STATUSES",
    "ENTITY_TYPES",
]