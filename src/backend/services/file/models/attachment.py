"""
Attachment data model for the Task Management System.

This module defines the Attachment document model that links files to entities (tasks, projects, comments)
in the Task Management System. It provides the data structure and operations for file attachments,
including creation, retrieval, and access control.
"""

import bson
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from ...common.database.mongo.models import (
    Document, 
    DocumentQuery,
    str_to_object_id,
    object_id_to_str
)
from ...common.utils.validators import validate_required, validate_enum
from ...common.logging.logger import get_logger
from ...common.events.event_bus import EventBus, create_event

# Configure module logger
logger = get_logger(__name__)

# Collection name for attachments
ATTACHMENT_COLLECTION = "attachments"

# Valid entity types for attachments
ENTITY_TYPES = ["task", "project", "comment"]

# Event bus instance
event_bus = EventBus()

class Attachment(Document):
    """
    MongoDB document model representing a file attachment to an entity
    (task, project, comment) in the system.
    
    Attributes:
        collection_name (str): MongoDB collection name
        schema (dict): Document schema with field definitions
        use_schema_validation (bool): Whether to validate against schema
    """
    
    collection_name = ATTACHMENT_COLLECTION
    schema = {
        "fileId": {
            "type": "ObjectId",
            "required": True,
            "description": "Reference to the file in the storage system"
        },
        "entityType": {
            "type": "str",
            "required": True,
            "description": "Type of entity this file is attached to (task, project, comment)"
        },
        "entityId": {
            "type": "ObjectId",
            "required": True,
            "description": "ID of the entity this file is attached to"
        },
        "name": {
            "type": "str",
            "required": True,
            "description": "Original filename"
        },
        "contentType": {
            "type": "str",
            "required": True,
            "description": "MIME type of the file"
        },
        "size": {
            "type": "int",
            "required": True,
            "description": "File size in bytes"
        },
        "uploadedBy": {
            "type": "ObjectId",
            "required": True,
            "description": "User ID who uploaded the file"
        },
        "uploadedAt": {
            "type": "datetime",
            "required": True,
            "description": "When the file was uploaded"
        },
        "description": {
            "type": "str",
            "required": False,
            "description": "Optional description of the file"
        }
    }
    use_schema_validation = True
    
    def __init__(self, data: Dict[str, Any] = None, is_new: bool = True):
        """
        Initialize a new Attachment document model instance.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)
    
    def validate(self) -> bool:
        """
        Validates the attachment document against schema rules.
        
        Returns:
            bool: True if valid, raises ValidationError if invalid
        """
        # Call parent validate method first
        super().validate()
        
        # Perform specific validation
        validate_required(self._data, ["fileId", "entityType", "entityId"])
        validate_enum(self._data.get("entityType"), ENTITY_TYPES, "entityType")
        
        return True
    
    def save(self):
        """
        Saves the attachment to the database with validation.
        
        Returns:
            bson.ObjectId: Attachment document ID
        """
        # Validate before saving
        self.validate()
        
        # Determine if this is a create or update operation
        is_create = self._is_new
        
        # Call parent save method
        result = super().save()
        
        # Publish appropriate event
        event_type = "attachment.created" if is_create else "attachment.updated"
        event = create_event(
            event_type=event_type,
            payload=self.to_dict(),
            source="attachment.model"
        )
        event_bus.publish(event_type, event)
        
        logger.info(f"Attachment {event_type.split('.')[-1]}: {self.get_id_str()}")
        
        return result
    
    def delete(self) -> bool:
        """
        Deletes the attachment from the database.
        
        Returns:
            bool: True if deletion successful
        """
        # Store ID and data for event before deletion
        attachment_id = self.get_id_str()
        attachment_data = self.to_dict()
        
        # Call parent delete method
        result = super().delete()
        
        if result:
            # Publish delete event
            event = create_event(
                event_type="attachment.deleted",
                payload=attachment_data,
                source="attachment.model"
            )
            event_bus.publish("attachment.deleted", event)
            
            logger.info(f"Attachment deleted: {attachment_id}")
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts attachment to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the attachment
        """
        data = super().to_dict()
        
        # Convert ObjectIds to strings for serialization
        if "fileId" in data and data["fileId"]:
            data["fileId"] = object_id_to_str(data["fileId"])
        
        if "entityId" in data and data["entityId"]:
            data["entityId"] = object_id_to_str(data["entityId"])
        
        if "uploadedBy" in data and data["uploadedBy"]:
            data["uploadedBy"] = object_id_to_str(data["uploadedBy"])
        
        # Format datetime fields
        if "uploadedAt" in data and data["uploadedAt"]:
            if isinstance(data["uploadedAt"], datetime):
                data["uploadedAt"] = data["uploadedAt"].isoformat()
        
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Attachment':
        """
        Creates an Attachment instance from a dictionary.
        
        Args:
            data: Dictionary containing attachment data
            
        Returns:
            Attachment: New Attachment instance
        """
        # Process ObjectId fields
        processed_data = data.copy()
        
        # Convert string IDs to ObjectIds
        id_fields = ["fileId", "entityId", "uploadedBy"]
        for field in id_fields:
            if field in processed_data and processed_data[field] and isinstance(processed_data[field], str):
                processed_data[field] = str_to_object_id(processed_data[field])
        
        # Convert ISO date strings to datetime objects
        if "uploadedAt" in processed_data and isinstance(processed_data["uploadedAt"], str):
            try:
                processed_data["uploadedAt"] = datetime.fromisoformat(processed_data["uploadedAt"].replace("Z", "+00:00"))
            except ValueError:
                # If parsing fails, use current time
                processed_data["uploadedAt"] = datetime.now()
        
        return Attachment(processed_data)


def get_attachment_by_id(attachment_id: str) -> Optional[Attachment]:
    """
    Retrieves an attachment by its ID.
    
    Args:
        attachment_id: String ID of the attachment
        
    Returns:
        Attachment or None: Attachment object if found, None otherwise
    """
    if not attachment_id:
        return None
    
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(attachment_id, str):
            obj_id = str_to_object_id(attachment_id)
        else:
            obj_id = attachment_id
        
        # Use the find_by_id class method
        return Attachment.find_by_id(obj_id)
    except ValueError:
        logger.error(f"Invalid attachment ID format: {attachment_id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving attachment by ID: {str(e)}")
        return None


def get_attachments_by_file(file_id: str) -> List[Attachment]:
    """
    Retrieves all attachments for a specific file.
    
    Args:
        file_id: String ID of the file
        
    Returns:
        list: List of Attachment objects for the file
    """
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(file_id, str):
            file_obj_id = str_to_object_id(file_id)
        else:
            file_obj_id = file_id
        
        # Create query
        query = DocumentQuery(Attachment).filter({"fileId": file_obj_id})
        
        # Execute query and return results
        return query.execute()
    except ValueError:
        logger.error(f"Invalid file ID format: {file_id}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving attachments by file ID: {str(e)}")
        return []


def get_attachments_by_entity(entity_type: str, entity_id: str) -> List[Attachment]:
    """
    Retrieves all attachments for a specific entity (task, project, comment).
    
    Args:
        entity_type: Type of entity (task, project, comment)
        entity_id: String ID of the entity
        
    Returns:
        list: List of Attachment objects for the entity
    """
    if entity_type not in ENTITY_TYPES:
        logger.error(f"Invalid entity type: {entity_type}")
        return []
    
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(entity_id, str):
            entity_obj_id = str_to_object_id(entity_id)
        else:
            entity_obj_id = entity_id
        
        # Create query
        query = DocumentQuery(Attachment).filter({
            "entityType": entity_type,
            "entityId": entity_obj_id
        })
        
        # Execute query and return results
        return query.execute()
    except ValueError:
        logger.error(f"Invalid entity ID format: {entity_id}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving attachments by entity: {str(e)}")
        return []


def delete_entity_attachments(entity_type: str, entity_id: str) -> int:
    """
    Deletes all attachments for a specific entity.
    
    Args:
        entity_type: Type of entity (task, project, comment)
        entity_id: String ID of the entity
        
    Returns:
        int: Number of attachments deleted
    """
    if entity_type not in ENTITY_TYPES:
        logger.error(f"Invalid entity type: {entity_type}")
        return 0
    
    try:
        # Get all attachments for the entity
        attachments = get_attachments_by_entity(entity_type, entity_id)
        
        # Delete each attachment
        deleted_count = 0
        for attachment in attachments:
            if attachment.delete():
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} attachments for {entity_type} {entity_id}")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Error deleting attachments for entity: {str(e)}")
        return 0