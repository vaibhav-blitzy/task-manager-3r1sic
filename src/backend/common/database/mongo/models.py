"""
MongoDB document model classes and utilities for the Task Management System.

This module provides base document model classes and utilities for the Task Management System,
including document abstraction, CRUD operations, data validation, and advanced features like
versioning, soft deletion, timestamping, and query building.
"""

import datetime
import copy
import json
from typing import Dict, List, Any, Optional, Type, ClassVar, Union

import bson
import pymongo
from pymongo.errors import DuplicateKeyError, PyMongoError

from .connection import get_database, with_retry
from ...logging.logger import get_logger
from ...utils.datetime import now

# Configure module logger
logger = get_logger(__name__)

# Field name constants
DELETED_FIELD = "deleted_at"
CREATED_FIELD = "created_at"
UPDATED_FIELD = "updated_at"
VERSION_FIELD = "version"
ID_FIELD = "_id"


def str_to_object_id(id_str) -> bson.ObjectId:
    """
    Converts a string ID to MongoDB ObjectId.
    
    Args:
        id_str: String representation of the ObjectId
        
    Returns:
        bson.ObjectId: MongoDB ObjectId instance
        
    Raises:
        ValueError: If the string is not a valid ObjectId
    """
    if isinstance(id_str, bson.ObjectId):
        return id_str
    
    try:
        return bson.ObjectId(id_str)
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid ObjectId format: {id_str}")
        raise ValueError(f"Invalid ObjectId format: {id_str}") from e


def object_id_to_str(obj_id) -> Optional[str]:
    """
    Converts a MongoDB ObjectId to string.
    
    Args:
        obj_id: MongoDB ObjectId to convert
        
    Returns:
        str: String representation of the ObjectId
        None: If obj_id is None
    """
    if obj_id is None:
        return None
    
    return str(obj_id)


def serialize_doc(doc: Dict) -> Dict:
    """
    Serializes MongoDB document to JSON-compatible format.
    
    Converts ObjectId to string and datetime objects to ISO format for
    JSON serialization.
    
    Args:
        doc: MongoDB document to serialize
        
    Returns:
        dict: Serialized document with proper type conversions
    """
    if doc is None:
        return None
    
    # Create a deep copy to avoid modifying the original
    result = copy.deepcopy(doc)
    
    # Recursive function to process nested documents
    def process_values(data):
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if isinstance(value, bson.ObjectId):
                    data[key] = str(value)
                elif isinstance(value, datetime.datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, dict):
                    process_values(value)
                elif isinstance(value, list):
                    process_values(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, bson.ObjectId):
                    data[i] = str(item)
                elif isinstance(item, datetime.datetime):
                    data[i] = item.isoformat()
                elif isinstance(item, dict):
                    process_values(item)
                elif isinstance(item, list):
                    process_values(item)
    
    process_values(result)
    return result


class BaseDocument:
    """
    Base document model class providing core functionality for MongoDB documents.
    
    This class provides the foundation for all document models with basic CRUD operations,
    data validation, and database abstraction. It's designed to be extended by model
    classes that define specific collection and schema details.
    
    Attributes:
        collection_name (str): MongoDB collection name to use
        schema (dict): Document schema with field definitions
        use_schema_validation (bool): Whether to validate against schema
    """
    
    collection_name: str = None
    schema: Dict = {}
    use_schema_validation: bool = False
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new document model instance.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document (not yet in database)
        """
        if self.collection_name is None:
            raise ValueError("Document model must define collection_name")
        
        self._data = data or {}
        self._is_new = is_new
    
    def collection(self):
        """
        Get the MongoDB collection for this document model.
        
        Returns:
            pymongo.collection.Collection: MongoDB collection instance
        """
        db = get_database()
        return db[self.collection_name]
    
    def validate(self) -> bool:
        """
        Validates the document against schema rules.
        
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If document fails validation
        """
        if not self.use_schema_validation:
            return True
        
        if not self.schema:
            return True
        
        errors = {}
        
        # Check required fields
        for field_name, field_def in self.schema.items():
            if field_def.get('required', False) and field_name not in self._data:
                errors[field_name] = "Field is required"
            
            # Check field type if present and type is specified
            if field_name in self._data and 'type' in field_def:
                expected_type = field_def['type']
                field_value = self._data[field_name]
                
                # Skip type check for null values if nullable is True
                if field_value is None and field_def.get('nullable', False):
                    continue
                
                if expected_type == 'ObjectId':
                    if not isinstance(field_value, bson.ObjectId) and not (
                        isinstance(field_value, str) and bson.ObjectId.is_valid(field_value)
                    ):
                        errors[field_name] = f"Expected ObjectId, got {type(field_value).__name__}"
                else:
                    # Check against Python types
                    type_map = {
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'dict': dict,
                        'list': list,
                        'datetime': datetime.datetime
                    }
                    
                    if expected_type in type_map:
                        if not isinstance(field_value, type_map[expected_type]):
                            errors[field_name] = f"Expected {expected_type}, got {type(field_value).__name__}"
        
        if errors:
            error_msg = f"Document validation failed: {errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return True
    
    @with_retry()
    def save(self):
        """
        Saves the document to MongoDB.
        
        For new documents, performs an insert operation.
        For existing documents, performs an update operation.
        
        Returns:
            bson.ObjectId: The document's _id
            
        Raises:
            Exception: If save operation fails
        """
        if self.use_schema_validation:
            self.validate()
        
        try:
            if self._is_new:
                # Handle insert for new documents
                result = self.collection().insert_one(self._data)
                self._data[ID_FIELD] = result.inserted_id
                self._is_new = False
                logger.debug(f"Inserted new document in {self.collection_name} with id: {result.inserted_id}")
                return result.inserted_id
            else:
                # Handle update for existing documents
                if ID_FIELD not in self._data:
                    raise ValueError("Cannot update document without _id field")
                
                doc_id = self._data[ID_FIELD]
                result = self.collection().replace_one({ID_FIELD: doc_id}, self._data)
                
                if result.matched_count == 0:
                    logger.warning(f"Document with id {doc_id} not found for update in {self.collection_name}")
                
                logger.debug(f"Updated document in {self.collection_name} with id: {doc_id}")
                return doc_id
                
        except PyMongoError as e:
            logger.error(f"Error saving document to {self.collection_name}: {str(e)}")
            raise
    
    @with_retry()
    def delete(self) -> bool:
        """
        Deletes the document from MongoDB.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if ID_FIELD not in self._data or self._is_new:
            logger.warning("Cannot delete document without _id or document is new")
            return False
        
        try:
            doc_id = self._data[ID_FIELD]
            result = self.collection().delete_one({ID_FIELD: doc_id})
            
            if result.deleted_count == 1:
                logger.debug(f"Deleted document from {self.collection_name} with id: {doc_id}")
                return True
            else:
                logger.warning(f"Document with id {doc_id} not found for deletion in {self.collection_name}")
                return False
                
        except PyMongoError as e:
            logger.error(f"Error deleting document from {self.collection_name}: {str(e)}")
            raise
    
    def update(self, update_data: Dict) -> 'BaseDocument':
        """
        Updates the document with provided data.
        
        Args:
            update_data: Data to update document with
            
        Returns:
            BaseDocument: Self with updated fields for method chaining
        """
        self._data.update(update_data)
        return self
    
    def to_dict(self) -> Dict:
        """
        Converts document to dictionary representation.
        
        Returns:
            dict: Dictionary representation of the document
        """
        return serialize_doc(self._data)
    
    def get(self, field_name: str, default=None) -> Any:
        """
        Get value for document field.
        
        Args:
            field_name: Field name to get
            default: Default value if field doesn't exist
            
        Returns:
            Field value or default if not found
        """
        return self._data.get(field_name, default)
    
    def set(self, field_name: str, value: Any) -> 'BaseDocument':
        """
        Set value for document field.
        
        Args:
            field_name: Field name to set
            value: Value to set
            
        Returns:
            BaseDocument: Self for method chaining
        """
        self._data[field_name] = value
        return self
    
    def get_id(self):
        """
        Get document ID.
        
        Returns:
            bson.ObjectId or None: Document ID or None if new document
        """
        return self._data.get(ID_FIELD)
    
    def get_id_str(self) -> Optional[str]:
        """
        Get document ID as string.
        
        Returns:
            str or None: String ID or None if new document
        """
        doc_id = self.get_id()
        if doc_id:
            return object_id_to_str(doc_id)
        return None
    
    def exists(self) -> bool:
        """
        Check if document exists in database.
        
        Returns:
            bool: True if document exists, False otherwise
        """
        return not self._is_new
    
    @classmethod
    @with_retry()
    def find_by_id(cls, id) -> Optional['BaseDocument']:
        """
        Find document by ID.
        
        Args:
            id: Document ID (string or ObjectId)
            
        Returns:
            BaseDocument or None: Document instance if found, None otherwise
        """
        instance = cls()
        
        if isinstance(id, str):
            id = str_to_object_id(id)
        
        try:
            doc = instance.collection().find_one({ID_FIELD: id})
            
            if doc:
                return cls(data=doc, is_new=False)
            
            logger.debug(f"Document with id {id} not found in {instance.collection_name}")
            return None
            
        except PyMongoError as e:
            logger.error(f"Error finding document by id in {instance.collection_name}: {str(e)}")
            raise
    
    @classmethod
    @with_retry()
    def find_one(cls, query: Dict) -> Optional['BaseDocument']:
        """
        Find one document matching query criteria.
        
        Args:
            query: MongoDB query criteria
            
        Returns:
            BaseDocument or None: Document instance if found, None otherwise
        """
        instance = cls()
        
        try:
            doc = instance.collection().find_one(query)
            
            if doc:
                return cls(data=doc, is_new=False)
            
            return None
            
        except PyMongoError as e:
            logger.error(f"Error finding document in {instance.collection_name}: {str(e)}")
            raise
    
    @classmethod
    @with_retry()
    def find(cls, query: Dict = None, sort: Dict = None, limit: int = None, skip: int = None) -> List['BaseDocument']:
        """
        Find documents matching query criteria.
        
        Args:
            query: MongoDB query criteria
            sort: Sort criteria
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            
        Returns:
            list: List of document instances matching criteria
        """
        instance = cls()
        
        try:
            cursor = instance.collection().find(query or {})
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
            
            if skip:
                cursor = cursor.skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return [cls(data=doc, is_new=False) for doc in cursor]
            
        except PyMongoError as e:
            logger.error(f"Error finding documents in {instance.collection_name}: {str(e)}")
            raise
    
    @classmethod
    @with_retry()
    def count(cls, query: Dict = None) -> int:
        """
        Count documents matching query criteria.
        
        Args:
            query: MongoDB query criteria
            
        Returns:
            int: Count of matching documents
        """
        instance = cls()
        
        try:
            return instance.collection().count_documents(query or {})
            
        except PyMongoError as e:
            logger.error(f"Error counting documents in {instance.collection_name}: {str(e)}")
            raise
    
    @classmethod
    @with_retry()
    def create_indexes(cls, indexes: List) -> List[str]:
        """
        Create indexes for the collection.
        
        Args:
            indexes: List of index specifications
            
        Returns:
            list: List of created index names
        """
        instance = cls()
        
        try:
            result = []
            for index in indexes:
                if isinstance(index, tuple):
                    # Simple (field, direction) index
                    name = instance.collection().create_index(index)
                    result.append(name)
                elif isinstance(index, list):
                    # Compound index [(field1, direction), (field2, direction)]
                    name = instance.collection().create_index(index)
                    result.append(name)
                elif isinstance(index, dict):
                    # Index with options
                    if 'keys' in index:
                        keys = index.pop('keys')
                        name = instance.collection().create_index(keys, **index)
                        result.append(name)
                    else:
                        logger.warning(f"Invalid index specification: {index}")
            
            return result
            
        except PyMongoError as e:
            logger.error(f"Error creating indexes in {instance.collection_name}: {str(e)}")
            raise


class TimestampedDocument(BaseDocument):
    """
    Document model with automatic timestamp tracking.
    
    Automatically adds created_at and updated_at timestamps to documents.
    """
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a timestamped document instance.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)
        
        # Initialize timestamps for new documents
        if is_new:
            current_time = now()
            self._data[CREATED_FIELD] = current_time
            self._data[UPDATED_FIELD] = current_time
    
    def save(self):
        """
        Save document with updated timestamp.
        
        Updates the updated_at timestamp before saving.
        
        Returns:
            bson.ObjectId: Document ID
        """
        # Update the updated_at timestamp
        self._data[UPDATED_FIELD] = now()
        
        # Call the parent class save method
        return super().save()


class SoftDeleteDocument(TimestampedDocument):
    """
    Document model with soft deletion capability.
    
    Instead of permanently removing documents, marks them as deleted with a timestamp.
    """
    
    def is_deleted(self) -> bool:
        """
        Check if document has been soft deleted.
        
        Returns:
            bool: True if deleted, False otherwise
        """
        return DELETED_FIELD in self._data and self._data[DELETED_FIELD] is not None
    
    def delete(self):
        """
        Soft delete document by setting deleted_at timestamp.
        
        Returns:
            bson.ObjectId: Document ID
        """
        # Set the deleted_at timestamp
        self._data[DELETED_FIELD] = now()
        
        # Save the document to persist the deleted status
        return self.save()
    
    def hard_delete(self) -> bool:
        """
        Permanently delete document from database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Call the parent class's delete method for permanent deletion
        return super(TimestampedDocument, self).delete()
    
    def restore(self):
        """
        Restore a soft-deleted document.
        
        Returns:
            bson.ObjectId: Document ID
        """
        # Clear the deleted_at field
        self._data[DELETED_FIELD] = None
        
        # Save the document to persist the change
        return self.save()
    
    @classmethod
    def find(cls, query: Dict = None, sort: Dict = None, limit: int = None, 
             skip: int = None, include_deleted: bool = False) -> List['SoftDeleteDocument']:
        """
        Find documents excluding soft-deleted ones by default.
        
        Args:
            query: MongoDB query criteria
            sort: Sort criteria
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            include_deleted: Whether to include soft-deleted documents
            
        Returns:
            list: List of document instances matching criteria
        """
        # Clone the query to avoid modifying the original
        query = copy.deepcopy(query) if query else {}
        
        # Exclude soft-deleted documents unless explicitly included
        if not include_deleted:
            query[DELETED_FIELD] = None
        
        # Call the parent class's find method
        return super(SoftDeleteDocument, cls).find(query, sort, limit, skip)
    
    @classmethod
    def find_one(cls, query: Dict, include_deleted: bool = False) -> Optional['SoftDeleteDocument']:
        """
        Find one document excluding soft-deleted ones by default.
        
        Args:
            query: MongoDB query criteria
            include_deleted: Whether to include soft-deleted documents
            
        Returns:
            SoftDeleteDocument or None: Document instance if found, None otherwise
        """
        # Clone the query to avoid modifying the original
        query = copy.deepcopy(query)
        
        # Exclude soft-deleted documents unless explicitly included
        if not include_deleted:
            query[DELETED_FIELD] = None
        
        # Call the parent class's find_one method
        return super(SoftDeleteDocument, cls).find_one(query)


class VersionedDocument(TimestampedDocument):
    """
    Document model with versioning capability.
    
    Tracks document versions and can maintain history of changes.
    """
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a document with versioning.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)
        
        # Initialize version for new documents
        if is_new:
            self._data[VERSION_FIELD] = 1
    
    def save(self):
        """
        Save document with version increment.
        
        Increments the version number for existing documents.
        
        Returns:
            bson.ObjectId: Document ID
        """
        # Increment version for existing documents
        if not self._is_new:
            current_version = self._data.get(VERSION_FIELD, 0)
            self._data[VERSION_FIELD] = current_version + 1
        
        # Call the parent class save method
        return super().save()
    
    def get_version_history(self) -> List[Dict]:
        """
        Retrieve version history for document.
        
        Returns:
            list: List of historical versions
        """
        if not self.get_id():
            return []
        
        try:
            # Get the history collection (assuming naming convention collection_name + "_history")
            db = get_database()
            history_collection = db[f"{self.collection_name}_history"]
            
            # Find historical versions
            history = list(history_collection.find(
                {ID_FIELD: self.get_id()},
                sort=[(VERSION_FIELD, pymongo.ASCENDING)]
            ))
            
            return [serialize_doc(version) for version in history]
            
        except PyMongoError as e:
            logger.error(f"Error retrieving version history: {str(e)}")
            return []


class DocumentQuery:
    """
    Fluent interface for building MongoDB queries.
    
    Provides a chainable API for constructing queries with filters, sort, pagination, etc.
    """
    
    def __init__(self, document_class):
        """
        Initialize a query builder for document class.
        
        Args:
            document_class: The document model class to query
        """
        self.document_class = document_class
        self._query = {}
        self._sort = {}
        self._limit = None
        self._skip = None
        self._projection = None
    
    def filter(self, query: Dict) -> 'DocumentQuery':
        """
        Add filter criteria to query.
        
        Args:
            query: MongoDB query criteria
            
        Returns:
            DocumentQuery: Self for method chaining
        """
        self._query.update(query)
        return self
    
    def sort(self, sort_by, direction: int = pymongo.ASCENDING) -> 'DocumentQuery':
        """
        Add sort criteria to query.
        
        Args:
            sort_by: Field to sort by or dictionary of sort criteria
            direction: Sort direction, pymongo.ASCENDING or pymongo.DESCENDING
            
        Returns:
            DocumentQuery: Self for method chaining
        """
        if isinstance(sort_by, str):
            self._sort[sort_by] = direction
        elif isinstance(sort_by, dict):
            self._sort.update(sort_by)
        return self
    
    def limit(self, limit: int) -> 'DocumentQuery':
        """
        Set maximum number of results.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            DocumentQuery: Self for method chaining
        """
        self._limit = limit
        return self
    
    def skip(self, skip: int) -> 'DocumentQuery':
        """
        Set number of results to skip.
        
        Args:
            skip: Number of documents to skip
            
        Returns:
            DocumentQuery: Self for method chaining
        """
        self._skip = skip
        return self
    
    def project(self, fields) -> 'DocumentQuery':
        """
        Set fields to include in results.
        
        Args:
            fields: List of fields to include or dictionary of field projections
            
        Returns:
            DocumentQuery: Self for method chaining
        """
        if isinstance(fields, list):
            self._projection = {field: 1 for field in fields}
        elif isinstance(fields, dict):
            self._projection = fields
        return self
    
    def count(self) -> int:
        """
        Count documents matching query.
        
        Returns:
            int: Count of matching documents
        """
        return self.document_class.count(self._query)
    
    def execute(self) -> List:
        """
        Execute query and return results.
        
        Returns:
            list: List of document instances matching criteria
        """
        return self.document_class.find(
            query=self._query,
            sort=self._sort,
            limit=self._limit,
            skip=self._skip
        )
    
    def first(self) -> Optional[Any]:
        """
        Execute query and return first result.
        
        Returns:
            Document instance or None: First matching document or None
        """
        results = self.limit(1).execute()
        return results[0] if results else None


class Document(SoftDeleteDocument, VersionedDocument):
    """
    Comprehensive document model combining all features.
    
    Inherits from SoftDeleteDocument and VersionedDocument to provide all features:
    - CRUD operations
    - Timestamps
    - Soft deletion
    - Versioning
    """
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a complete document model instance.
        
        Args:
            data: Initial document data
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)