"""
Defines the File document model that represents file metadata in the Task Management System.
This model provides the data structure and operations for tracking files, their storage information,
security properties, version history, and preview capabilities.
"""

# Standard library imports
import os.path
from typing import Dict, List, Any, Optional
import datetime

# Third-party imports
import bson

# Internal imports
from ...common.database.mongo.models import Document, DocumentQuery, str_to_object_id, object_id_to_str
from ..config import get_config
from ...common.utils.validators import validate_required, validate_enum
from ...common.logging.logger import get_logger
from ...common.events.event_bus import EventBus, create_event
from ...common.utils.datetime import now

# Configure module logger
logger = get_logger(__name__)

# Collection name for file metadata
FILE_COLLECTION = "files"

# Access level constants
ACCESS_LEVELS = ["private", "shared", "public"]

# Scan status constants
SCAN_STATUSES = ["pending", "scanning", "clean", "infected", "error"]

# File status constants
FILE_STATUSES = ["uploading", "processing", "ready", "error"]

# Get config
config = get_config()

# Create EventBus instance
event_bus = EventBus()


class File(Document):
    """
    MongoDB document model representing a file's metadata in the Task Management System,
    including storage details, security attributes, and version history.
    """
    
    collection_name = FILE_COLLECTION
    schema = {
        "name": {"type": "str", "required": True},
        "size": {"type": "int", "required": True},
        "type": {"type": "str", "required": True},
        "extension": {"type": "str"},
        "storageKey": {"type": "str", "required": True},
        "url": {"type": "str"},
        "preview": {
            "type": "dict",
            "schema": {
                "thumbnail": {"type": "str"},
                "previewAvailable": {"type": "bool"},
                "previewType": {"type": "str"}
            }
        },
        "metadata": {
            "type": "dict",
            "schema": {
                "uploadedBy": {"type": "ObjectId", "required": True},
                "uploadedAt": {"type": "datetime", "required": True},
                "lastAccessed": {"type": "datetime"},
                "accessCount": {"type": "int"},
                "md5Hash": {"type": "str"}
            }
        },
        "security": {
            "type": "dict",
            "schema": {
                "accessLevel": {"type": "str", "required": True},
                "encryptionType": {"type": "str"},
                "scanStatus": {"type": "str", "required": True}
            }
        },
        "associations": {
            "type": "dict",
            "schema": {
                "taskId": {"type": "ObjectId"},
                "projectId": {"type": "ObjectId"},
                "commentId": {"type": "ObjectId"}
            }
        },
        "versions": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "id": {"type": "ObjectId"},
                    "storageKey": {"type": "str"},
                    "size": {"type": "int"},
                    "uploadedBy": {"type": "ObjectId"},
                    "uploadedAt": {"type": "datetime"},
                    "changeNotes": {"type": "str"}
                }
            }
        },
        "status": {"type": "str", "required": True}
    }
    
    use_schema_validation = True
    
    def __init__(self, data=None, is_new=True):
        """
        Initialize a new File document model instance.
        
        Args:
            data (dict): Initial document data
            is_new (bool): Flag indicating if this is a new document
        """
        # Initialize with default values if this is a new document
        if is_new and data is None:
            data = {}
        
        if is_new:
            # Set default values for required fields
            current_time = now()
            data.setdefault("metadata", {})
            data["metadata"].setdefault("uploadedAt", current_time)
            data["metadata"].setdefault("accessCount", 0)
            
            data.setdefault("security", {})
            data["security"].setdefault("accessLevel", "private")
            data["security"].setdefault("scanStatus", "pending")
            
            data.setdefault("preview", {})
            data["preview"].setdefault("previewAvailable", False)
            
            data.setdefault("versions", [])
            data.setdefault("status", "uploading")
        
        super().__init__(data, is_new)
    
    def validate(self):
        """
        Validates the file document against schema rules.
        
        Returns:
            bool: True if valid, raises ValidationError if invalid
        """
        # Basic schema validation from parent
        super().validate()
        
        # Additional validations
        validate_required(self._data, ["name", "size", "type", "storageKey"])
        
        # Validate enum fields
        if "security" in self._data and "accessLevel" in self._data["security"]:
            validate_enum(self._data["security"]["accessLevel"], ACCESS_LEVELS, "accessLevel")
        
        if "security" in self._data and "scanStatus" in self._data["security"]:
            validate_enum(self._data["security"]["scanStatus"], SCAN_STATUSES, "scanStatus")
        
        if "status" in self._data:
            validate_enum(self._data["status"], FILE_STATUSES, "status")
        
        return True
    
    def save(self):
        """
        Saves the file metadata to the database with validation.
        
        Returns:
            bson.ObjectId: File document ID
        """
        # Validate before saving
        self.validate()
        
        # Determine if this is a new file or an update
        is_new = self._is_new
        
        # Save the document
        file_id = super().save()
        
        # Publish event
        event_type = "file.created" if is_new else "file.updated"
        event = create_event(
            event_type=event_type,
            payload={
                "file_id": str(file_id),
                "name": self.get("name"),
                "size": self.get("size"),
                "type": self.get("type"),
                "uploaded_by": str(self.get("metadata", {}).get("uploadedBy")),
                "status": self.get("status")
            },
            source="file_service"
        )
        event_bus.publish(event_type, event)
        
        return file_id
    
    def delete(self):
        """
        Deletes the file metadata from the database.
        
        Returns:
            bool: True if deletion successful
        """
        # Get file info before deletion
        file_id = self.get_id()
        
        # Delete the document
        result = super().delete()
        
        # Publish event if deletion was successful
        if result:
            event = create_event(
                event_type="file.deleted",
                payload={
                    "file_id": str(file_id),
                    "name": self.get("name"),
                    "uploaded_by": str(self.get("metadata", {}).get("uploadedBy"))
                },
                source="file_service"
            )
            event_bus.publish("file.deleted", event)
        
        return result
    
    def to_dict(self):
        """
        Converts file metadata to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the file metadata
        """
        # Get the base dictionary from parent
        data_dict = super().to_dict()
        
        # Convert ObjectId fields to strings
        if "_id" in data_dict:
            data_dict["id"] = str(data_dict.pop("_id"))
        
        if "metadata" in data_dict and "uploadedBy" in data_dict["metadata"]:
            data_dict["metadata"]["uploadedBy"] = str(data_dict["metadata"]["uploadedBy"])
        
        if "associations" in data_dict:
            if "taskId" in data_dict["associations"] and data_dict["associations"]["taskId"]:
                data_dict["associations"]["taskId"] = str(data_dict["associations"]["taskId"])
            if "projectId" in data_dict["associations"] and data_dict["associations"]["projectId"]:
                data_dict["associations"]["projectId"] = str(data_dict["associations"]["projectId"])
            if "commentId" in data_dict["associations"] and data_dict["associations"]["commentId"]:
                data_dict["associations"]["commentId"] = str(data_dict["associations"]["commentId"])
        
        # Format datetime fields to ISO format
        if "metadata" in data_dict:
            for dt_field in ["uploadedAt", "lastAccessed"]:
                if dt_field in data_dict["metadata"] and data_dict["metadata"][dt_field]:
                    if isinstance(data_dict["metadata"][dt_field], datetime.datetime):
                        data_dict["metadata"][dt_field] = data_dict["metadata"][dt_field].isoformat()
        
        # Convert version history ObjectIds to strings
        if "versions" in data_dict and isinstance(data_dict["versions"], list):
            for version in data_dict["versions"]:
                if "id" in version:
                    version["id"] = str(version["id"])
                if "uploadedBy" in version:
                    version["uploadedBy"] = str(version["uploadedBy"])
                if "uploadedAt" in version and isinstance(version["uploadedAt"], datetime.datetime):
                    version["uploadedAt"] = version["uploadedAt"].isoformat()
        
        return data_dict
    
    @staticmethod
    def from_dict(data):
        """
        Creates a File instance from a dictionary.
        
        Args:
            data (dict): Dictionary representation of file data
            
        Returns:
            File: New File instance
        """
        # Convert string IDs to ObjectIds
        if "id" in data:
            data["_id"] = str_to_object_id(data["id"])
            del data["id"]
        
        if "metadata" in data and "uploadedBy" in data["metadata"] and data["metadata"]["uploadedBy"]:
            if isinstance(data["metadata"]["uploadedBy"], str):
                data["metadata"]["uploadedBy"] = str_to_object_id(data["metadata"]["uploadedBy"])
        
        if "associations" in data:
            for id_field in ["taskId", "projectId", "commentId"]:
                if id_field in data["associations"] and data["associations"][id_field]:
                    if isinstance(data["associations"][id_field], str):
                        data["associations"][id_field] = str_to_object_id(data["associations"][id_field])
        
        # Handle version history
        if "versions" in data and isinstance(data["versions"], list):
            for version in data["versions"]:
                if "id" in version and isinstance(version["id"], str):
                    version["id"] = str_to_object_id(version["id"])
                if "uploadedBy" in version and isinstance(version["uploadedBy"], str):
                    version["uploadedBy"] = str_to_object_id(version["uploadedBy"])
        
        return File(data=data, is_new=False)
    
    def update_status(self, status):
        """
        Updates the file status.
        
        Args:
            status (str): New status value
            
        Returns:
            File: Updated File instance
        """
        validate_enum(status, FILE_STATUSES, "status")
        self._data["status"] = status
        return self
    
    def update_scan_status(self, scan_status):
        """
        Updates the file scan status.
        
        Args:
            scan_status (str): New scan status value
            
        Returns:
            File: Updated File instance
        """
        validate_enum(scan_status, SCAN_STATUSES, "scanStatus")
        
        if "security" not in self._data:
            self._data["security"] = {}
        
        self._data["security"]["scanStatus"] = scan_status
        self._data["security"]["lastScanned"] = now()
        return self
    
    def update_access_level(self, access_level):
        """
        Updates the file access level.
        
        Args:
            access_level (str): New access level value
            
        Returns:
            File: Updated File instance
        """
        validate_enum(access_level, ACCESS_LEVELS, "accessLevel")
        
        if "security" not in self._data:
            self._data["security"] = {}
        
        self._data["security"]["accessLevel"] = access_level
        return self
    
    def add_version(self, version_data):
        """
        Adds a new version to the file's version history.
        
        Args:
            version_data (dict): Version metadata including storageKey, size, etc.
            
        Returns:
            File: Updated File instance
        """
        # Validate required version fields
        validate_required(version_data, ["storageKey", "size", "uploadedBy"])
        
        # Ensure versions list exists
        if "versions" not in self._data:
            self._data["versions"] = []
        
        # Get current version number
        next_version_number = len(self._data["versions"]) + 1
        
        # Add current file as a version if it's the first version being added
        if len(self._data["versions"]) == 0 and self._data.get("storageKey"):
            current_version = {
                "id": self.get_id() or bson.ObjectId(),
                "storageKey": self._data["storageKey"],
                "size": self._data["size"],
                "uploadedBy": self._data["metadata"]["uploadedBy"],
                "uploadedAt": self._data["metadata"]["uploadedAt"],
                "changeNotes": "Initial version"
            }
            self._data["versions"].append(current_version)
        
        # Create new version entry
        new_version = {
            "id": bson.ObjectId(),
            "storageKey": version_data["storageKey"],
            "size": version_data["size"],
            "uploadedBy": version_data["uploadedBy"],
            "uploadedAt": version_data.get("uploadedAt", now()),
            "changeNotes": version_data.get("changeNotes", f"Version {next_version_number}")
        }
        
        # Add to versions list
        self._data["versions"].append(new_version)
        
        # Update current file info to the new version
        self._data["storageKey"] = new_version["storageKey"]
        self._data["size"] = new_version["size"]
        
        # If the file type changed, update it
        if "type" in version_data:
            self._data["type"] = version_data["type"]
        
        return self
    
    def update_preview(self, preview_data):
        """
        Updates the file's preview information.
        
        Args:
            preview_data (dict): Preview data including thumbnail, type, etc.
            
        Returns:
            File: Updated File instance
        """
        if "preview" not in self._data:
            self._data["preview"] = {}
        
        # Update preview fields
        self._data["preview"].update(preview_data)
        
        # Set preview available flag
        self._data["preview"]["previewAvailable"] = True
        
        return self
    
    def increment_access_count(self):
        """
        Increments the file access count.
        
        Returns:
            File: Updated File instance
        """
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        
        # Initialize access count if not present
        if "accessCount" not in self._data["metadata"]:
            self._data["metadata"]["accessCount"] = 0
        
        # Increment access count
        self._data["metadata"]["accessCount"] += 1
        
        # Update last accessed timestamp
        self._data["metadata"]["lastAccessed"] = now()
        
        return self
    
    def get_extension(self):
        """
        Gets the file extension from the name.
        
        Returns:
            str: File extension or empty string
        """
        if not self._data.get("name"):
            return ""
        
        _, ext = os.path.splitext(self._data["name"])
        return ext.lower()[1:] if ext else ""
    
    def get_versions(self):
        """
        Gets the list of file versions.
        
        Returns:
            list: List of version dictionaries
        """
        return self._data.get("versions", [])


def get_file_by_id(file_id: str) -> Optional[File]:
    """
    Retrieves a file by its ID.
    
    Args:
        file_id (str): ID of the file to retrieve
        
    Returns:
        File or None: File object if found, None otherwise
    """
    try:
        if isinstance(file_id, str):
            file_id = str_to_object_id(file_id)
        
        return File.find_by_id(file_id)
    except Exception as e:
        logger.error(f"Error retrieving file with ID {file_id}: {str(e)}")
        return None


def get_files_by_user(user_id: str, filters: Dict = None, pagination: Dict = None) -> List[File]:
    """
    Retrieves all files uploaded by a specific user.
    
    Args:
        user_id (str): ID of the user who uploaded the files
        filters (dict): Additional filters to apply
        pagination (dict): Pagination parameters (skip, limit)
        
    Returns:
        list: List of File objects uploaded by the user
    """
    try:
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Create base query
        query = DocumentQuery(File)
        query.filter({"metadata.uploadedBy": user_id})
        
        # Apply additional filters
        if filters:
            if "type" in filters:
                query.filter({"type": filters["type"]})
            
            if "accessLevel" in filters and filters["accessLevel"] in ACCESS_LEVELS:
                query.filter({"security.accessLevel": filters["accessLevel"]})
            
            if "dateRange" in filters and isinstance(filters["dateRange"], dict):
                date_query = {}
                
                if "start" in filters["dateRange"]:
                    date_query["$gte"] = filters["dateRange"]["start"]
                
                if "end" in filters["dateRange"]:
                    date_query["$lte"] = filters["dateRange"]["end"]
                
                if date_query:
                    query.filter({"metadata.uploadedAt": date_query})
        
        # Apply sorting (default to newest first)
        query.sort("metadata.uploadedAt", -1)
        
        # Apply pagination
        if pagination:
            if "skip" in pagination:
                query.skip(int(pagination["skip"]))
            
            if "limit" in pagination:
                query.limit(int(pagination["limit"]))
        
        # Execute query and return results
        return query.execute()
    
    except Exception as e:
        logger.error(f"Error retrieving files for user {user_id}: {str(e)}")
        return []


def search_files(search_criteria: Dict, pagination: Dict = None) -> Dict:
    """
    Search for files matching specific criteria.
    
    Args:
        search_criteria (dict): Search parameters
        pagination (dict): Pagination parameters (skip, limit)
        
    Returns:
        dict: Dictionary containing results and pagination info
    """
    try:
        # Create base query
        query = DocumentQuery(File)
        
        # Apply search criteria
        if "name" in search_criteria:
            query.filter({"name": {"$regex": search_criteria["name"], "$options": "i"}})
        
        if "type" in search_criteria:
            query.filter({"type": search_criteria["type"]})
        
        if "uploadedBy" in search_criteria:
            user_id = search_criteria["uploadedBy"]
            if isinstance(user_id, str):
                user_id = str_to_object_id(user_id)
            query.filter({"metadata.uploadedBy": user_id})
        
        if "taskId" in search_criteria:
            task_id = search_criteria["taskId"]
            if isinstance(task_id, str):
                task_id = str_to_object_id(task_id)
            query.filter({"associations.taskId": task_id})
        
        if "projectId" in search_criteria:
            project_id = search_criteria["projectId"]
            if isinstance(project_id, str):
                project_id = str_to_object_id(project_id)
            query.filter({"associations.projectId": project_id})
        
        if "accessLevel" in search_criteria and search_criteria["accessLevel"] in ACCESS_LEVELS:
            query.filter({"security.accessLevel": search_criteria["accessLevel"]})
        
        if "scanStatus" in search_criteria and search_criteria["scanStatus"] in SCAN_STATUSES:
            query.filter({"security.scanStatus": search_criteria["scanStatus"]})
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        if pagination:
            if "skip" in pagination:
                query.skip(int(pagination["skip"]))
            
            if "limit" in pagination:
                query.limit(int(pagination["limit"]))
        
        # Apply sorting (default to newest first)
        sort_field = search_criteria.get("sortBy", "metadata.uploadedAt")
        sort_order = search_criteria.get("sortOrder", "desc")
        query.sort(sort_field, -1 if sort_order == "desc" else 1)
        
        # Execute query
        results = query.execute()
        
        # Return formatted response
        return {
            "results": results,
            "pagination": {
                "total": total_count,
                "skip": pagination.get("skip", 0) if pagination else 0,
                "limit": pagination.get("limit", len(results)) if pagination else len(results)
            }
        }
    
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        return {"results": [], "pagination": {"total": 0, "skip": 0, "limit": 0}}