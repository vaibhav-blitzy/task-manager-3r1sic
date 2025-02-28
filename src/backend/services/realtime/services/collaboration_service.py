"""
Core service that implements collaborative editing and real-time document synchronization 
capabilities for the Task Management System. Handles operation transformation, conflict resolution, 
document locking, and collaborative state management across concurrent users.
"""

from typing import Dict, List, Optional, Any, Union
import json
import datetime
import uuid
import difflib

import pymongo

from ..models.connection import Connection
from ../../../common/database/redis/connection import get_redis_client
from ../config import get_config
from ../../../common/events/event_bus import get_event_bus_instance, create_event
from ../../../common/logging/logger import get_logger
from ../../../common/exceptions.api_exceptions import ResourceNotFoundError, PermissionError, ConflictError

# Configure logger
logger = get_logger(__name__)

# Get Redis client for document state and lock management
redis_client = get_redis_client()

# Get event bus for broadcasting events
event_bus = get_event_bus_instance()

# Get configuration
config = get_config()

# Constants
LOCK_EXPIRY_SECONDS = 300  # 5 minutes
MAX_OPERATION_SIZE = 1024 * 10  # 10KB maximum operation size
SUPPORTED_RESOURCE_TYPES = ['task', 'project', 'comment']
RESOURCE_TYPE_CHANNELS = {
    'task': 'task-collaboration', 
    'project': 'project-collaboration',
    'comment': 'comment-collaboration'
}


def validate_operation(operation: Dict) -> bool:
    """
    Validates that an operation has the required structure and fields.
    
    Args:
        operation: The operation to validate
        
    Returns:
        True if operation is valid, False otherwise
    """
    if not isinstance(operation, dict):
        logger.error("Operation must be a dictionary")
        return False
    
    # Check for required fields
    required_fields = ['type', 'data', 'position']
    for field in required_fields:
        if field not in operation:
            logger.error(f"Operation missing required field: {field}")
            return False
    
    # Validate operation type
    valid_types = ['insert', 'delete', 'update', 'replace']
    if operation['type'] not in valid_types:
        logger.error(f"Invalid operation type: {operation['type']}")
        return False
    
    # Validate data based on operation type
    if operation['type'] == 'insert':
        if 'content' not in operation['data']:
            logger.error("Insert operation missing 'content' in data")
            return False
    elif operation['type'] == 'delete':
        if 'length' not in operation['data']:
            logger.error("Delete operation missing 'length' in data")
            return False
    elif operation['type'] == 'update' or operation['type'] == 'replace':
        if 'content' not in operation['data']:
            logger.error(f"{operation['type']} operation missing 'content' in data")
            return False
    
    # Validate position
    if not isinstance(operation['position'], int) and not isinstance(operation['position'], dict):
        logger.error("Operation position must be an integer index or position object")
        return False
    
    # Check operation size
    operation_size = len(json.dumps(operation))
    if operation_size > MAX_OPERATION_SIZE:
        logger.error(f"Operation size exceeds maximum: {operation_size} > {MAX_OPERATION_SIZE}")
        return False
    
    return True


def transform_operation(operation: Dict, concurrent_operation: Dict) -> Dict:
    """
    Transforms an operation against another concurrent operation using operational transformation.
    
    Args:
        operation: The operation to transform
        concurrent_operation: The concurrent operation to transform against
        
    Returns:
        Transformed operation that can be applied after the concurrent operation
    """
    # Create a copy of the operation to avoid modifying the original
    transformed_op = operation.copy()
    
    # Get operation types
    op_type = operation['type']
    concurrent_type = concurrent_operation['type']
    
    # Transform based on operation types
    if op_type == 'insert' and concurrent_type == 'insert':
        # For insert vs insert, adjust position based on order
        op_position = operation['position']
        concurrent_position = concurrent_operation['position']
        
        # If the concurrent operation inserts before or at the same position,
        # shift this operation's position
        if concurrent_position <= op_position:
            concurrent_content_length = len(concurrent_operation['data']['content'])
            transformed_op['position'] = op_position + concurrent_content_length
    
    elif op_type == 'insert' and concurrent_type == 'delete':
        # For insert vs delete, adjust position if affected by deletion
        op_position = operation['position']
        concurrent_position = concurrent_operation['position']
        concurrent_length = concurrent_operation['data']['length']
        
        # If insertion point is after deletion start
        if op_position >= concurrent_position:
            # If insertion is within deleted range, move to deletion start
            if op_position < concurrent_position + concurrent_length:
                transformed_op['position'] = concurrent_position
            # If insertion is after deleted range, adjust position by deletion length
            else:
                transformed_op['position'] = op_position - concurrent_length
    
    elif op_type == 'delete' and concurrent_type == 'insert':
        # For delete vs insert, adjust position if affected by insertion
        op_position = operation['position']
        concurrent_position = concurrent_operation['position']
        concurrent_content_length = len(concurrent_operation['data']['content'])
        
        # If deletion starts after insertion, adjust position
        if op_position >= concurrent_position:
            transformed_op['position'] = op_position + concurrent_content_length
    
    elif op_type == 'delete' and concurrent_type == 'delete':
        # For delete vs delete, handle potential overlaps
        op_position = operation['position']
        op_length = operation['data']['length']
        concurrent_position = concurrent_operation['position']
        concurrent_length = concurrent_operation['data']['length']
        
        # Calculate deletion ranges
        op_end = op_position + op_length
        concurrent_end = concurrent_position + concurrent_length
        
        # Case 1: No overlap, concurrent deletion before operation deletion
        if concurrent_end <= op_position:
            transformed_op['position'] = op_position - concurrent_length
        
        # Case 2: No overlap, concurrent deletion after operation deletion
        elif op_end <= concurrent_position:
            # Position remains the same
            pass
        
        # Case 3: Overlap, concurrent deletion completely contains operation deletion
        elif concurrent_position <= op_position and concurrent_end >= op_end:
            # Nothing left to delete
            transformed_op['data']['length'] = 0
        
        # Case 4: Overlap, operation deletion completely contains concurrent deletion
        elif op_position <= concurrent_position and op_end >= concurrent_end:
            # Adjust length by the concurrent deletion length
            transformed_op['data']['length'] = op_length - concurrent_length
            
            # If the concurrent deletion starts after operation deletion, adjust position
            if concurrent_position > op_position:
                # Position remains the same, just adjust length
                pass
            else:
                # Adjust both position and length
                transformed_op['position'] = op_position - concurrent_position
        
        # Case 5: Partial overlap, concurrent deletion overlaps start of operation deletion
        elif concurrent_position < op_position and concurrent_end > op_position and concurrent_end < op_end:
            # Adjust position to start at concurrent end
            transformed_op['position'] = concurrent_end - concurrent_length
            # Adjust length to account for overlap
            overlap = concurrent_end - op_position
            transformed_op['data']['length'] = op_length - overlap
        
        # Case 6: Partial overlap, concurrent deletion overlaps end of operation deletion
        elif concurrent_position > op_position and concurrent_position < op_end and concurrent_end > op_end:
            # Position remains the same
            # Adjust length to account for overlap
            overlap = op_end - concurrent_position
            transformed_op['data']['length'] = op_length - overlap
    
    elif op_type == 'update' and concurrent_type == 'update':
        # For update vs update, typically last-writer-wins based on timestamps
        # If they update the same field, the later operation wins
        # For structured updates, merge non-conflicting field updates
        if isinstance(operation['position'], dict) and isinstance(concurrent_operation['position'], dict):
            # This is a structured update (object with fields)
            transformed_fields = operation['data']['content'].copy()
            concurrent_fields = concurrent_operation['data']['content']
            
            # For conflicting fields, use timestamps to determine winner
            op_timestamp = operation.get('timestamp', 0)
            concurrent_timestamp = concurrent_operation.get('timestamp', 0)
            
            for field in concurrent_fields:
                if field in transformed_fields and op_timestamp < concurrent_timestamp:
                    # Concurrent operation wins for this field
                    transformed_fields[field] = concurrent_fields[field]
            
            transformed_op['data']['content'] = transformed_fields
    
    return transformed_op


def apply_operation(document_state: Dict, operation: Dict) -> Dict:
    """
    Applies an operation to a document state to produce a new state.
    
    Args:
        document_state: The current document state
        operation: The operation to apply
        
    Returns:
        Updated document state after applying the operation
    """
    # Create a copy of the document state to avoid modifying the original
    updated_state = document_state.copy()
    
    # Get document content
    content = updated_state.get('content', '')
    
    # Apply operation based on type
    op_type = operation['type']
    op_position = operation['position']
    
    if op_type == 'insert':
        insert_content = operation['data']['content']
        
        if isinstance(content, str):
            # String content insertion
            updated_state['content'] = content[:op_position] + insert_content + content[op_position:]
        elif isinstance(content, dict) and isinstance(op_position, str):
            # Object field insertion/update
            content[op_position] = insert_content
            updated_state['content'] = content
        elif isinstance(content, list) and isinstance(op_position, int):
            # Array insertion
            content.insert(op_position, insert_content)
            updated_state['content'] = content
    
    elif op_type == 'delete':
        delete_length = operation['data']['length']
        
        if isinstance(content, str):
            # String content deletion
            updated_state['content'] = content[:op_position] + content[op_position + delete_length:]
        elif isinstance(content, dict) and isinstance(op_position, str):
            # Object field deletion
            if op_position in content:
                del content[op_position]
                updated_state['content'] = content
        elif isinstance(content, list) and isinstance(op_position, int):
            # Array deletion
            del content[op_position:op_position + delete_length]
            updated_state['content'] = content
    
    elif op_type == 'update':
        update_content = operation['data']['content']
        
        if isinstance(content, str) and isinstance(op_position, int):
            # String content update
            update_length = operation['data'].get('length', len(update_content))
            updated_state['content'] = content[:op_position] + update_content + content[op_position + update_length:]
        elif isinstance(content, dict):
            # Object update
            if isinstance(op_position, str):
                # Single field update
                content[op_position] = update_content
            elif isinstance(op_position, dict):
                # Multi-field update
                for field, value in update_content.items():
                    content[field] = value
            updated_state['content'] = content
        elif isinstance(content, list) and isinstance(op_position, int):
            # Array item update
            update_length = operation['data'].get('length', 1)
            content[op_position:op_position + update_length] = [update_content]
            updated_state['content'] = content
    
    elif op_type == 'replace':
        # Replace entire content
        updated_state['content'] = operation['data']['content']
    
    # Update version
    updated_state['version'] = operation.get('version', updated_state.get('version', 0) + 1)
    
    return updated_state


def acquire_lock(resource_type: str, resource_id: str, user_id: str, field_name: str) -> bool:
    """
    Acquires an editing lock on a resource for a user.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        user_id: ID of the user requesting the lock
        field_name: Name of the field being locked
        
    Returns:
        True if lock acquired successfully, False if already locked by another user
    """
    # Create lock key
    lock_key = f"lock:{resource_type}:{resource_id}:{field_name}"
    
    # Check if lock exists
    existing_lock = redis_client.get(lock_key)
    if existing_lock:
        # Parse existing lock
        try:
            lock_data = json.loads(existing_lock)
            existing_user = lock_data.get('user_id')
            
            # If locked by the same user, extend the lock
            if existing_user == user_id:
                lock_data['timestamp'] = datetime.datetime.utcnow().isoformat()
                redis_client.set(lock_key, json.dumps(lock_data), ex=LOCK_EXPIRY_SECONDS)
                logger.debug(f"Extended lock on {resource_type}:{resource_id}:{field_name} for user {user_id}")
                return True
            else:
                logger.debug(f"Lock acquisition failed: {resource_type}:{resource_id}:{field_name} already locked by {existing_user}")
                return False
        except json.JSONDecodeError:
            # If lock data is corrupted, overwrite it
            pass
    
    # Set lock with user ID and timestamp
    lock_data = {
        'user_id': user_id,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'resource_type': resource_type,
        'resource_id': resource_id,
        'field_name': field_name
    }
    
    # Store lock with expiration
    redis_client.set(lock_key, json.dumps(lock_data), ex=LOCK_EXPIRY_SECONDS)
    
    # Publish lock acquired event
    event = create_event(
        event_type='lock.acquired',
        payload={
            'resource_type': resource_type,
            'resource_id': resource_id,
            'field_name': field_name,
            'user_id': user_id,
            'expires_at': (datetime.datetime.utcnow() + datetime.timedelta(seconds=LOCK_EXPIRY_SECONDS)).isoformat()
        },
        source='collaboration_service'
    )
    event_bus.publish('lock.acquired', event)
    
    logger.debug(f"Acquired lock on {resource_type}:{resource_id}:{field_name} for user {user_id}")
    return True


def release_lock(resource_type: str, resource_id: str, user_id: str, field_name: str) -> bool:
    """
    Releases an editing lock on a resource.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        user_id: ID of the user releasing the lock
        field_name: Name of the field being unlocked
        
    Returns:
        True if lock released successfully, False if not owned by user
    """
    # Create lock key
    lock_key = f"lock:{resource_type}:{resource_id}:{field_name}"
    
    # Check if lock exists and belongs to the user
    existing_lock = redis_client.get(lock_key)
    if not existing_lock:
        logger.debug(f"No lock exists for {resource_type}:{resource_id}:{field_name}")
        return True  # No lock to release
    
    try:
        lock_data = json.loads(existing_lock)
        existing_user = lock_data.get('user_id')
        
        # Verify lock ownership
        if existing_user != user_id:
            logger.warning(f"Lock release failed: {resource_type}:{resource_id}:{field_name} locked by {existing_user}, not {user_id}")
            return False
        
        # Delete the lock
        redis_client.delete(lock_key)
        
        # Publish lock released event
        event = create_event(
            event_type='lock.released',
            payload={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'field_name': field_name,
                'user_id': user_id
            },
            source='collaboration_service'
        )
        event_bus.publish('lock.released', event)
        
        logger.debug(f"Released lock on {resource_type}:{resource_id}:{field_name} for user {user_id}")
        return True
    
    except json.JSONDecodeError:
        # If lock data is corrupted, delete it
        redis_client.delete(lock_key)
        return True


def get_document_state(resource_type: str, resource_id: str, field_name: str) -> Dict:
    """
    Retrieves the current state of a collaborative document.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        field_name: Name of the field (document)
        
    Returns:
        Current document state including content and version
    """
    # Create document key
    doc_key = f"doc:{resource_type}:{resource_id}:{field_name}"
    
    # Try to get from Redis first
    doc_json = redis_client.get(doc_key)
    if doc_json:
        try:
            return json.loads(doc_json)
        except json.JSONDecodeError:
            logger.error(f"Error parsing document state for {doc_key}")
            # Continue to fetch from database
    
    # If not in Redis, fetch from MongoDB
    try:
        db = pymongo.MongoClient().get_database('task_management')
        collection = db[resource_type + 's']  # Pluralize collection name
        
        document = collection.find_one({'_id': resource_id})
        if document and field_name in document:
            # Create document state
            doc_state = {
                'content': document[field_name],
                'version': document.get('version', 0),
                'resource_type': resource_type,
                'resource_id': resource_id,
                'field_name': field_name
            }
            
            # Cache in Redis
            redis_client.set(doc_key, json.dumps(doc_state), ex=3600)  # Cache for 1 hour
            
            return doc_state
    except Exception as e:
        logger.error(f"Error fetching document from database: {str(e)}")
    
    # If document not found, initialize with empty content
    empty_state = {
        'content': '' if field_name == 'description' else {} if field_name == 'metadata' else [],
        'version': 0,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'field_name': field_name
    }
    
    # Cache in Redis
    redis_client.set(doc_key, json.dumps(empty_state), ex=3600)  # Cache for 1 hour
    
    return empty_state


def update_document_state(resource_type: str, resource_id: str, field_name: str, document_state: Dict) -> bool:
    """
    Updates the state of a collaborative document.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        field_name: Name of the field (document)
        document_state: New document state
        
    Returns:
        True if update successful
    """
    # Create document key
    doc_key = f"doc:{resource_type}:{resource_id}:{field_name}"
    
    try:
        # Update Redis cache
        redis_client.set(doc_key, json.dumps(document_state), ex=3600)  # Cache for 1 hour
        
        # Update MongoDB
        db = pymongo.MongoClient().get_database('task_management')
        collection = db[resource_type + 's']  # Pluralize collection name
        
        # Update the field and version
        update_data = {
            field_name: document_state['content'],
            'version': document_state['version'],
            'updated_at': datetime.datetime.utcnow()
        }
        
        collection.update_one({'_id': resource_id}, {'$set': update_data})
        
        return True
    except Exception as e:
        logger.error(f"Error updating document state: {str(e)}")
        return False


def register_operation(resource_type: str, resource_id: str, field_name: str, operation: Dict, user_id: str) -> bool:
    """
    Registers an operation in the operation history.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        field_name: Name of the field (document)
        operation: The operation to register
        user_id: ID of the user who performed the operation
        
    Returns:
        True if registration successful
    """
    # Create operation history key
    history_key = f"history:{resource_type}:{resource_id}:{field_name}"
    
    try:
        # Add timestamp and user_id to operation metadata
        op_with_metadata = operation.copy()
        op_with_metadata['timestamp'] = datetime.datetime.utcnow().isoformat()
        op_with_metadata['user_id'] = user_id
        
        # Convert to JSON string
        op_json = json.dumps(op_with_metadata)
        
        # Add to history list in Redis
        redis_client.rpush(history_key, op_json)
        
        # Trim history if it gets too long (keep last 100 operations)
        redis_client.ltrim(history_key, -100, -1)
        
        # Set expiry for history (30 days)
        redis_client.expire(history_key, 2592000)
        
        return True
    except Exception as e:
        logger.error(f"Error registering operation: {str(e)}")
        return False


def get_operation_history(resource_type: str, resource_id: str, field_name: str, limit: int = 50) -> List[Dict]:
    """
    Retrieves operation history for a collaborative document.
    
    Args:
        resource_type: Type of resource (task, project, etc.)
        resource_id: Unique ID of the resource
        field_name: Name of the field (document)
        limit: Maximum number of operations to retrieve
        
    Returns:
        List of operations in chronological order
    """
    # Create operation history key
    history_key = f"history:{resource_type}:{resource_id}:{field_name}"
    
    try:
        # Get operations from Redis list
        op_jsons = redis_client.lrange(history_key, -limit, -1)
        
        # Parse JSON strings to objects
        operations = []
        for op_json in op_jsons:
            try:
                op = json.loads(op_json)
                operations.append(op)
            except json.JSONDecodeError:
                logger.error(f"Error parsing operation JSON: {op_json}")
                continue
        
        return operations
    except Exception as e:
        logger.error(f"Error retrieving operation history: {str(e)}")
        return []


class CollaborationError(Exception):
    """
    Custom exception for collaboration-related errors.
    """
    
    def __init__(self, message: str, code: str = "collaboration_error"):
        """
        Initialize collaboration error with code and message.
        
        Args:
            message: Error message
            code: Error code identifier
        """
        super().__init__(message)
        self.message = message
        self.code = code


class OperationTransformer:
    """
    Utility class for operational transformation functions.
    """
    
    def __init__(self):
        """
        Initializes the operation transformer.
        """
        # Define transformation rule mappings
        self._transform_rules = {
            ('insert', 'insert'): self._transform_insert_insert,
            ('insert', 'delete'): self._transform_insert_delete,
            ('delete', 'insert'): self._transform_delete_insert,
            ('delete', 'delete'): self._transform_delete_delete,
            ('update', 'update'): self._transform_update_update
            # Additional transformations can be added as needed
        }
    
    def transform(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform an operation against another concurrent operation.
        
        Args:
            op1: The operation to transform
            op2: The concurrent operation to transform against
            
        Returns:
            Transformed operation
        """
        op1_type = op1['type']
        op2_type = op2['type']
        
        # Get the appropriate transformation function
        transform_key = (op1_type, op2_type)
        if transform_key in self._transform_rules:
            return self._transform_rules[transform_key](op1, op2)
        else:
            # If no specific transformation rule, return unmodified operation
            return op1.copy()
    
    def _transform_insert_insert(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform insert operation against another insert.
        
        Args:
            op1: Insert operation to transform
            op2: Concurrent insert operation
            
        Returns:
            Transformed operation
        """
        transformed = op1.copy()
        
        # Get positions
        pos1 = op1['position']
        pos2 = op2['position']
        
        # If op2 inserts before or at same position as op1, shift op1
        if pos2 <= pos1:
            content_length = len(op2['data']['content'])
            transformed['position'] = pos1 + content_length
        
        return transformed
    
    def _transform_insert_delete(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform insert operation against a delete.
        
        Args:
            op1: Insert operation to transform
            op2: Concurrent delete operation
            
        Returns:
            Transformed operation
        """
        transformed = op1.copy()
        
        # Get positions
        pos1 = op1['position']
        pos2 = op2['position']
        length2 = op2['data']['length']
        
        # If insertion point is after deletion start
        if pos1 >= pos2:
            # If insertion point is within deletion range, move to deletion start
            if pos1 < pos2 + length2:
                transformed['position'] = pos2
            # If insertion point is after deletion range, adjust position
            else:
                transformed['position'] = pos1 - length2
        
        return transformed
    
    def _transform_delete_insert(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform delete operation against an insert.
        
        Args:
            op1: Delete operation to transform
            op2: Concurrent insert operation
            
        Returns:
            Transformed operation
        """
        transformed = op1.copy()
        
        # Get positions
        pos1 = op1['position']
        pos2 = op2['position']
        
        # If deletion starts at or after insertion, adjust position
        if pos1 >= pos2:
            content_length = len(op2['data']['content'])
            transformed['position'] = pos1 + content_length
        
        return transformed
    
    def _transform_delete_delete(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform delete operation against another delete.
        
        Args:
            op1: Delete operation to transform
            op2: Concurrent delete operation
            
        Returns:
            Transformed operation
        """
        transformed = op1.copy()
        
        # Get positions and lengths
        pos1 = op1['position']
        length1 = op1['data']['length']
        pos2 = op2['position']
        length2 = op2['data']['length']
        
        # Calculate ranges
        end1 = pos1 + length1
        end2 = pos2 + length2
        
        # Case 1: op2 completely before op1
        if end2 <= pos1:
            transformed['position'] = pos1 - length2
        
        # Case 2: op2 completely after op1
        elif pos2 >= end1:
            # No change needed
            pass
        
        # Case 3: op2 completely contains op1
        elif pos2 <= pos1 and end2 >= end1:
            # Nothing left to delete
            transformed['data']['length'] = 0
        
        # Case 4: op1 completely contains op2
        elif pos1 <= pos2 and end1 >= end2:
            # Reduce length by the deleted portion
            transformed['data']['length'] = length1 - length2
            
            # If op2 starts after op1, keep original position
            if pos2 > pos1:
                pass
            else:
                # Otherwise, adjust position
                transformed['position'] = pos1 - pos2
        
        # Case 5: partial overlap, op2 overlaps start of op1
        elif pos2 < pos1 and end2 > pos1 and end2 < end1:
            # Adjust position to end of op2
            transformed['position'] = pos2
            # Adjust length
            overlap = end2 - pos1
            transformed['data']['length'] = length1 - overlap
        
        # Case 6: partial overlap, op2 overlaps end of op1
        elif pos2 > pos1 and pos2 < end1 and end2 > end1:
            # Position remains the same
            # Adjust length to account for overlap
            overlap = end1 - pos2
            transformed['data']['length'] = length1 - overlap
        
        return transformed
    
    def _transform_update_update(self, op1: Dict, op2: Dict) -> Dict:
        """
        Transform update operation against another update.
        
        Args:
            op1: Update operation to transform
            op2: Concurrent update operation
            
        Returns:
            Transformed operation
        """
        transformed = op1.copy()
        
        # Handle field-based updates (for objects)
        if isinstance(op1['data']['content'], dict) and isinstance(op2['data']['content'], dict):
            # Merge updates, with last-writer-wins for conflicting fields
            content = op1['data']['content'].copy()
            
            # Get timestamps for conflict resolution
            ts1 = op1.get('timestamp', 0)
            ts2 = op2.get('timestamp', 0)
            
            # For each field in op2
            for field, value in op2['data']['content'].items():
                # If field exists in op1 and op2 is newer, op2 wins
                if field in content and ts2 > ts1:
                    content[field] = value
            
            transformed['data']['content'] = content
        
        # For position-based updates to strings, transform position similar to insert/delete
        if isinstance(op1['position'], int) and isinstance(op2['position'], int):
            # Simple last-writer-wins based on timestamp
            # This is a simplified approach; actual implementation would be more complex
            ts1 = op1.get('timestamp', 0)
            ts2 = op2.get('timestamp', 0)
            
            # If op2 is newer, it wins
            if ts2 > ts1:
                # Return op1 but make it a no-op (empty update)
                transformed['data']['content'] = ""
                transformed['data']['length'] = 0
        
        return transformed


class CollaborationService:
    """
    Main service class for real-time collaborative editing features.
    """
    
    def __init__(self):
        """
        Initializes the collaboration service with required settings and connections.
        """
        # Initialize Redis client for document state and locking
        self._redis_client = redis_client
        
        # Get collaboration settings from config
        self._collaboration_settings = config.get_collaboration_settings()
        
        # Initialize dictionary to track active editing sessions
        self._active_sessions = {}
        
        # Initialize operation transformer
        self._operation_transformer = OperationTransformer()
        
        # Subscribe to collaboration events
        self._event_bus = event_bus
        self._event_bus.subscribe('collaboration.operation', self._handle_collaboration_event)
        self._event_bus.subscribe('collaboration.join', self._handle_collaboration_event)
        self._event_bus.subscribe('collaboration.leave', self._handle_collaboration_event)
        self._event_bus.subscribe('collaboration.lock', self._handle_collaboration_event)
        self._event_bus.subscribe('collaboration.unlock', self._handle_collaboration_event)
        
        # Start periodic cleanup of stale locks
        # This would typically be done with a background thread or task
        
        self._initialized = True
        logger.info("CollaborationService initialized")
    
    def join_session(self, connection_id: str, resource_type: str, resource_id: str, field_name: str) -> Dict:
        """
        Registers a user joining a collaborative editing session.
        
        Args:
            connection_id: The WebSocket connection ID
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field being edited
            
        Returns:
            Session details including document state and active users
        """
        # Validate resource type
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection not found")
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # TODO: Check user permission to access this resource
        # This would involve a call to an authorization service
        
        # Create session key
        session_key = f"session:{resource_type}:{resource_id}:{field_name}"
        
        # Get or create session data
        session_data = self._redis_client.get_json(session_key) or {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'field_name': field_name,
            'participants': {},
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Add user to participants
        session_data['participants'][user_id] = {
            'connection_id': connection_id,
            'joined_at': datetime.datetime.utcnow().isoformat(),
            'typing': False
        }
        
        # Update session data in Redis
        self._redis_client.set_json(session_key, session_data, ex=3600)  # 1 hour expiry
        
        # Also track in memory for faster access
        if session_key not in self._active_sessions:
            self._active_sessions[session_key] = session_data
        else:
            self._active_sessions[session_key]['participants'][user_id] = session_data['participants'][user_id]
        
        # Get current document state
        document_state = get_document_state(resource_type, resource_id, field_name)
        
        # Get current locks
        lock_key = f"lock:{resource_type}:{resource_id}:{field_name}"
        current_lock = self._redis_client.get_json(lock_key)
        
        # Create and publish join event
        channel = RESOURCE_TYPE_CHANNELS.get(resource_type, 'general-collaboration')
        event = create_event(
            event_type='collaboration.join',
            payload={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'field_name': field_name,
                'user_id': user_id,
                'connection_id': connection_id
            },
            source='collaboration_service'
        )
        self._event_bus.publish(channel, event)
        
        # Return session data with document state
        return {
            'session': session_data,
            'document': document_state,
            'lock': current_lock,
            'success': True
        }
    
    def leave_session(self, connection_id: str, resource_type: str, resource_id: str, field_name: str) -> bool:
        """
        Handles a user leaving a collaborative editing session.
        
        Args:
            connection_id: The WebSocket connection ID
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field being edited
            
        Returns:
            True if session left successfully
        """
        # Validate parameters
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            logger.warning(f"Connection {connection_id} not found for leave_session")
            return False
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # Create session key
        session_key = f"session:{resource_type}:{resource_id}:{field_name}"
        
        # Get session data
        session_data = self._redis_client.get_json(session_key)
        if not session_data:
            logger.warning(f"Session {session_key} not found for leave_session")
            return False
        
        # Remove user from participants
        if user_id in session_data['participants']:
            del session_data['participants'][user_id]
            
            # Update session data in Redis
            if session_data['participants']:
                # If there are still participants, update the session
                self._redis_client.set_json(session_key, session_data, ex=3600)
                
                # Update in-memory cache
                if session_key in self._active_sessions:
                    self._active_sessions[session_key] = session_data
            else:
                # If no participants left, remove the session
                self._redis_client.delete(session_key)
                
                # Remove from in-memory cache
                if session_key in self._active_sessions:
                    del self._active_sessions[session_key]
        
        # Release any locks held by this user
        release_lock(resource_type, resource_id, user_id, field_name)
        
        # Create and publish leave event
        channel = RESOURCE_TYPE_CHANNELS.get(resource_type, 'general-collaboration')
        event = create_event(
            event_type='collaboration.leave',
            payload={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'field_name': field_name,
                'user_id': user_id,
                'connection_id': connection_id
            },
            source='collaboration_service'
        )
        self._event_bus.publish(channel, event)
        
        return True
    
    def submit_operation(self, connection_id: str, operation_data: Dict,
                        resource_type: str, resource_id: str, field_name: str, 
                        version: int) -> Dict:
        """
        Processes and applies a collaborative editing operation.
        
        Args:
            connection_id: The WebSocket connection ID
            operation_data: The operation to apply
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field being edited
            version: Client's current document version
            
        Returns:
            Updated document state and operation result
        """
        # Validate operation structure
        if not validate_operation(operation_data):
            raise ValueError("Invalid operation format")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection not found")
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # TODO: Check if user has permission to modify this resource
        # This would involve a call to an authorization service
        
        # Get current document state
        document_state = get_document_state(resource_type, resource_id, field_name)
        
        # Check version for conflicts
        if version != document_state['version']:
            logger.warning(f"Version mismatch: client {version}, server {document_state['version']}")
            
            # Get operations since client version
            history = get_operation_history(resource_type, resource_id, field_name)
            server_operations = [op for op in history if op.get('version', 0) > version]
            
            # Try to resolve conflict
            resolved_operation = self._resolve_conflict(operation_data, server_operations, document_state)
            
            if not resolved_operation:
                # Cannot resolve conflict automatically
                return {
                    'success': False,
                    'error': 'conflict',
                    'message': 'Document was modified by another user',
                    'current_version': document_state['version'],
                    'client_version': version,
                    'document': document_state
                }
            
            # Use the resolved operation
            operation_data = resolved_operation
        
        # Create full operation object with metadata
        operation = {
            'id': str(uuid.uuid4()),
            'type': operation_data['type'],
            'data': operation_data['data'],
            'position': operation_data['position'],
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'user_id': user_id,
            'version': document_state['version'] + 1
        }
        
        # Apply operation to document
        updated_state = apply_operation(document_state, operation)
        
        # Update document state
        update_document_state(resource_type, resource_id, field_name, updated_state)
        
        # Register operation in history
        register_operation(resource_type, resource_id, field_name, operation, user_id)
        
        # Create and publish operation event
        channel = RESOURCE_TYPE_CHANNELS.get(resource_type, 'general-collaboration')
        event = create_event(
            event_type='collaboration.operation',
            payload={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'field_name': field_name,
                'operation': operation,
                'user_id': user_id,
                'connection_id': connection_id
            },
            source='collaboration_service'
        )
        self._event_bus.publish(channel, event)
        
        # Return updated document state
        return {
            'success': True,
            'document': updated_state,
            'operation': operation,
            'version': updated_state['version']
        }
    
    def update_typing_status(self, connection_id: str, is_typing: bool,
                            resource_type: str, resource_id: str, field_name: str) -> bool:
        """
        Updates a user's typing status in a collaborative session.
        
        Args:
            connection_id: The WebSocket connection ID
            is_typing: Whether the user is currently typing
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field being edited
            
        Returns:
            True if status updated successfully
        """
        # Validate parameters
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection not found")
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # Create session key
        session_key = f"session:{resource_type}:{resource_id}:{field_name}"
        
        # Get session data
        session_data = self._redis_client.get_json(session_key)
        if not session_data:
            logger.warning(f"Session {session_key} not found for update_typing_status")
            return False
        
        # Update typing status if user is a participant
        if user_id in session_data['participants']:
            # Update typing status
            session_data['participants'][user_id]['typing'] = is_typing
            
            # Update last activity
            session_data['participants'][user_id]['last_activity'] = datetime.datetime.utcnow().isoformat()
            
            # Update session data in Redis
            self._redis_client.set_json(session_key, session_data, ex=3600)
            
            # Update in-memory cache
            if session_key in self._active_sessions:
                self._active_sessions[session_key] = session_data
            
            # Create and publish typing status event
            channel = RESOURCE_TYPE_CHANNELS.get(resource_type, 'general-collaboration')
            event = create_event(
                event_type='collaboration.typing',
                payload={
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'field_name': field_name,
                    'user_id': user_id,
                    'is_typing': is_typing
                },
                source='collaboration_service'
            )
            self._event_bus.publish(channel, event)
            
            return True
        
        return False
    
    def lock_resource(self, connection_id: str, resource_type: str, resource_id: str, field_name: str) -> Dict:
        """
        Acquires an edit lock on a resource field for a user.
        
        Args:
            connection_id: The WebSocket connection ID
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field to lock
            
        Returns:
            Lock status and result
        """
        # Validate parameters
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection not found")
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # TODO: Check if user has permission to lock this resource
        # This would involve a call to an authorization service
        
        # Attempt to acquire lock
        lock_success = acquire_lock(resource_type, resource_id, user_id, field_name)
        
        # Return lock status
        return {
            'success': lock_success,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'field_name': field_name,
            'user_id': user_id,
            'message': 'Lock acquired successfully' if lock_success else 'Resource is locked by another user'
        }
    
    def unlock_resource(self, connection_id: str, resource_type: str, resource_id: str, field_name: str) -> Dict:
        """
        Releases an edit lock on a resource field.
        
        Args:
            connection_id: The WebSocket connection ID
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field to unlock
            
        Returns:
            Unlock status and result
        """
        # Validate parameters
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Get connection to find user
        connection = Connection.find_by_connection_id(connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection not found")
        
        # Get user ID from connection
        user_id = connection.get_user_id()
        
        # Attempt to release lock
        unlock_success = release_lock(resource_type, resource_id, user_id, field_name)
        
        # Return unlock status
        return {
            'success': unlock_success,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'field_name': field_name,
            'user_id': user_id,
            'message': 'Lock released successfully' if unlock_success else 'Lock is not owned by this user'
        }
    
    def get_active_collaborators(self, resource_type: str, resource_id: str, field_name: str) -> List[Dict]:
        """
        Gets list of users actively collaborating on a resource.
        
        Args:
            resource_type: Type of resource (task, project, etc.)
            resource_id: Unique ID of the resource
            field_name: Name of the field
            
        Returns:
            List of active collaborators with status information
        """
        # Validate parameters
        if resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        # Create session key
        session_key = f"session:{resource_type}:{resource_id}:{field_name}"
        
        # Get session data
        session_data = self._redis_client.get_json(session_key)
        if not session_data or not session_data.get('participants'):
            return []
        
        # Format collaborator information
        collaborators = []
        for user_id, user_data in session_data['participants'].items():
            collaborator = {
                'user_id': user_id,
                'joined_at': user_data.get('joined_at'),
                'is_typing': user_data.get('typing', False),
                'last_activity': user_data.get('last_activity')
            }
            collaborators.append(collaborator)
        
        return collaborators
    
    def cleanup_stale_locks(self) -> int:
        """
        Removes locks that have expired to prevent deadlocks.
        
        Returns:
            Number of locks removed
        """
        try:
            # Find lock keys in Redis
            lock_keys = self._redis_client.keys("lock:*")
            
            removed_count = 0
            current_time = datetime.datetime.utcnow()
            
            for key in lock_keys:
                # Get lock data
                lock_data = self._redis_client.get_json(key)
                if not lock_data:
                    continue
                
                # Check if lock is expired
                lock_time_str = lock_data.get('timestamp')
                if not lock_time_str:
                    continue
                
                try:
                    lock_time = datetime.datetime.fromisoformat(lock_time_str)
                    lock_age = (current_time - lock_time).total_seconds()
                    
                    # If lock is expired, remove it
                    if lock_age > LOCK_EXPIRY_SECONDS:
                        self._redis_client.delete(key)
                        removed_count += 1
                        
                        # Extract resource information from key
                        key_parts = key.split(':')
                        if len(key_parts) >= 4:
                            resource_type = key_parts[1]
                            resource_id = key_parts[2]
                            field_name = key_parts[3]
                            
                            # Publish lock expired event
                            event = create_event(
                                event_type='lock.expired',
                                payload={
                                    'resource_type': resource_type,
                                    'resource_id': resource_id,
                                    'field_name': field_name,
                                    'user_id': lock_data.get('user_id')
                                },
                                source='collaboration_service'
                            )
                            self._event_bus.publish('lock.expired', event)
                except (ValueError, TypeError):
                    # Invalid timestamp, remove the lock
                    self._redis_client.delete(key)
                    removed_count += 1
            
            return removed_count
        except Exception as e:
            logger.error(f"Error cleaning up stale locks: {str(e)}")
            return 0
    
    def _handle_collaboration_event(self, event: Dict) -> None:
        """
        Internal handler for incoming collaboration events.
        
        Args:
            event: The event to handle
        """
        if not event or not isinstance(event, dict):
            return
        
        event_type = event.get('type')
        payload = event.get('payload', {})
        
        if not event_type or not payload:
            return
        
        try:
            if event_type == 'collaboration.operation':
                # Handle operation event
                resource_type = payload.get('resource_type')
                resource_id = payload.get('resource_id')
                field_name = payload.get('field_name')
                operation = payload.get('operation')
                user_id = payload.get('user_id')
                
                if resource_type and resource_id and field_name and operation and user_id:
                    # Update in-memory session if needed
                    session_key = f"session:{resource_type}:{resource_id}:{field_name}"
                    if session_key in self._active_sessions:
                        # Update last activity for user
                        if user_id in self._active_sessions[session_key]['participants']:
                            self._active_sessions[session_key]['participants'][user_id]['last_activity'] = \
                                datetime.datetime.utcnow().isoformat()
            
            elif event_type == 'collaboration.join':
                # Handle join event
                pass  # Additional handling if needed
            
            elif event_type == 'collaboration.leave':
                # Handle leave event
                pass  # Additional handling if needed
            
            elif event_type == 'lock.acquired' or event_type == 'lock.released' or event_type == 'lock.expired':
                # Handle lock events
                pass  # Additional handling if needed
        
        except Exception as e:
            logger.error(f"Error handling collaboration event: {str(e)}")
    
    def _resolve_conflict(self, client_operation: Dict, server_operations: List[Dict], base_document: Dict) -> Optional[Dict]:
        """
        Attempts to automatically resolve conflicting operations.
        
        Args:
            client_operation: Client's operation to apply
            server_operations: Operations applied on the server since client's version
            base_document: The original document state client was working on
            
        Returns:
            Resolved operation or None if conflict can't be resolved
        """
        if not server_operations:
            return client_operation
        
        # Create a copy of the client operation
        resolved_op = client_operation.copy()
        
        try:
            # Apply operational transformation for each server operation
            for server_op in server_operations:
                resolved_op = self._operation_transformer.transform(resolved_op, server_op)
                
                # If the operation becomes a no-op (e.g., delete with length 0), we can't resolve
                if resolved_op['type'] == 'delete' and resolved_op['data'].get('length', 0) == 0:
                    return None
            
            # If the operation is still valid after transformation, we've successfully resolved the conflict
            return resolved_op
        
        except Exception as e:
            logger.error(f"Error resolving conflict: {str(e)}")
            
            # Handle text-based merge as fallback for simple operations
            if client_operation['type'] in ['insert', 'delete', 'update'] and isinstance(base_document.get('content', ''), str):
                try:
                    # Try to merge text changes using difflib
                    current_content = base_document.get('content', '')
                    server_content = get_document_state(
                        base_document['resource_type'],
                        base_document['resource_id'],
                        base_document['field_name']
                    ).get('content', '')
                    
                    # Get the content the client is trying to produce
                    client_content = ''
                    if client_operation['type'] == 'insert':
                        pos = client_operation['position']
                        content = client_operation['data']['content']
                        client_content = current_content[:pos] + content + current_content[pos:]
                    elif client_operation['type'] == 'delete':
                        pos = client_operation['position']
                        length = client_operation['data']['length']
                        client_content = current_content[:pos] + current_content[pos+length:]
                    elif client_operation['type'] == 'update':
                        pos = client_operation['position']
                        content = client_operation['data']['content']
                        length = client_operation['data'].get('length', len(content))
                        client_content = current_content[:pos] + content + current_content[pos+length:]
                    else:
                        return None
                    
                    # Use difflib to try to merge changes
                    matcher = difflib.SequenceMatcher(None, current_content, server_content)
                    merged_content = ''
                    
                    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                        if tag == 'equal':
                            # Take from either current or server - they're the same
                            merged_content += current_content[i1:i2]
                        elif tag == 'replace':
                            # Conflict - use client's version of this section if it changed
                            client_section = client_content[i1:i2]
                            if client_section != current_content[i1:i2]:
                                merged_content += client_section
                            else:
                                merged_content += server_content[j1:j2]
                        elif tag == 'delete':
                            # Server deleted this section
                            # Check if client modified this section
                            client_section = client_content[i1:i2]
                            if client_section != current_content[i1:i2]:
                                merged_content += client_section
                        elif tag == 'insert':
                            # Server inserted content
                            merged_content += server_content[j1:j2]
                    
                    # Create new replace operation with merged content
                    return {
                        'type': 'replace',
                        'position': 0,
                        'data': {
                            'content': merged_content
                        }
                    }
                except Exception as merge_err:
                    logger.error(f"Error during text merge: {str(merge_err)}")
                    return None
            
            return None