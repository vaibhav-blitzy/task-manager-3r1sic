"""
Provides mock implementations of various components for unit and integration testing
of the Task Management System. Includes mocks for databases, external services,
authentication, event handling, and HTTP responses.
"""

# Standard library imports
import json
import datetime
from typing import Any, Dict, List, Optional, Union

# Third-party imports
import pymongo
import mongomock
import fakeredis
from unittest.mock import MagicMock, patch
import pytest

# Internal imports
from ..database.redis.connection import RedisClient
from ..exceptions.api_exceptions import ApiException, AuthenticationError, NotFoundError
from ..logging.logger import get_logger
from ..events.event_bus import EventBus

# Configure module logger
logger = get_logger(__name__)

# Fixed datetime for consistent testing
FIXED_DATETIME = datetime.datetime(2023, 1, 1, 12, 0, 0)


def mock_mongo_client():
    """
    Creates a mock MongoDB client using mongomock for testing database operations.
    
    Returns:
        mongomock.MongoClient: An in-memory MongoDB client for testing
    """
    client = mongomock.MongoClient()
    logger.info("Created mock MongoDB client")
    return client


def mock_redis_client():
    """
    Creates a mock Redis client using fakeredis for testing cache operations.
    
    Returns:
        fakeredis.FakeStrictRedis: An in-memory Redis client for testing
    """
    client = fakeredis.FakeStrictRedis()
    logger.info("Created mock Redis client")
    return client


def mock_jwt_token(payload: Dict = None, expired: bool = False) -> str:
    """
    Creates a mock JWT token for testing authentication.
    
    Args:
        payload: Dictionary of claims to include in the token
        expired: If True, creates an expired token
        
    Returns:
        str: A mock JWT token
    """
    if payload is None:
        payload = {}
    
    # Create a basic payload
    token_payload = {
        "sub": "user123",
        "name": "Test User",
        "role": "user",
        "iat": int(datetime.datetime.now().timestamp()),
    }
    
    # Add expiration
    if expired:
        # Set expiration in the past
        token_payload["exp"] = int((datetime.datetime.now() - datetime.timedelta(hours=1)).timestamp())
    else:
        # Set expiration in the future
        token_payload["exp"] = int((datetime.datetime.now() + datetime.timedelta(hours=1)).timestamp())
    
    # Add user-provided payload
    token_payload.update(payload)
    
    # Create a simplified JWT token format (header.payload.signature)
    # Not a real JWT, just a mock representation
    header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # Fixed header
    payload_base64 = "mock_payload"  # Simplified for testing
    signature = "mock_signature"  # Simplified for testing
    
    return f"{header}.{payload_base64}.{signature}"


def mock_datetime_now(fixed_datetime=None):
    """
    Creates a mock for datetime.now() that returns a fixed time.
    
    Args:
        fixed_datetime: Optional datetime to return, defaults to FIXED_DATETIME
        
    Returns:
        MagicMock: A mock datetime object with now() method returning fixed_datetime
    """
    if fixed_datetime is None:
        fixed_datetime = FIXED_DATETIME
    
    mock_dt = MagicMock()
    mock_dt.now.return_value = fixed_datetime
    return mock_dt


def mock_event_bus():
    """
    Creates a mock EventBus for testing event-driven functionality.
    
    Returns:
        MagicMock: A mock EventBus with recorded event history
    """
    mock_bus = MagicMock(spec=EventBus)
    
    # Add list to track published events
    mock_bus.published_events = []
    
    # Configure publish method to record events
    def mock_publish(event_type, event):
        mock_bus.published_events.append((event_type, event))
        return True
    
    mock_bus.publish.side_effect = mock_publish
    
    # Configure subscribe method
    def mock_subscribe(event_type, handler):
        if not hasattr(mock_bus, 'handlers'):
            mock_bus.handlers = {}
        
        if event_type not in mock_bus.handlers:
            mock_bus.handlers[event_type] = []
        
        mock_bus.handlers[event_type].append(handler)
        return True
    
    mock_bus.subscribe.side_effect = mock_subscribe
    
    return mock_bus


def mock_api_response(data=None, status_code=200, headers=None):
    """
    Creates a mock API response for testing API clients.
    
    Args:
        data: Dictionary to be returned as JSON response
        status_code: HTTP status code of the response
        headers: Optional HTTP headers dictionary
        
    Returns:
        MockResponse: A mock HTTP response object
    """
    if data is None:
        data = {}
    
    if headers is None:
        headers = {}
    
    return MockResponse(data, status_code, text=json.dumps(data), headers=headers)


def mock_logger():
    """
    Creates a mock logger for testing logging functionality.
    
    Returns:
        MagicMock: A mock logger with recording of log messages
    """
    mock_log = MagicMock()
    
    # Dictionary to track log messages by level
    mock_log.log_records = {
        'debug': [],
        'info': [],
        'warning': [],
        'error': [],
        'critical': []
    }
    
    # Configure methods to record messages
    def record_log(level, message, *args, **kwargs):
        mock_log.log_records[level].append((message, args, kwargs))
    
    mock_log.debug.side_effect = lambda message, *args, **kwargs: record_log('debug', message, *args, **kwargs)
    mock_log.info.side_effect = lambda message, *args, **kwargs: record_log('info', message, *args, **kwargs)
    mock_log.warning.side_effect = lambda message, *args, **kwargs: record_log('warning', message, *args, **kwargs)
    mock_log.error.side_effect = lambda message, *args, **kwargs: record_log('error', message, *args, **kwargs)
    mock_log.critical.side_effect = lambda message, *args, **kwargs: record_log('critical', message, *args, **kwargs)
    
    return mock_log


def mock_exception_response(message="An error occurred", status_code=500, error_code="server_error"):
    """
    Creates a mock exception response with API exception format.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Error code identifier
        
    Returns:
        dict: An API exception response dictionary
    """
    return {
        "status": status_code,
        "code": error_code,
        "message": message
    }


def patch_service(service_path, mock_methods=None):
    """
    Creates a context manager to patch a service with mock responses.
    
    Args:
        service_path: Import path of the service to patch
        mock_methods: Dictionary mapping method names to return values or side effects
        
    Returns:
        unittest.mock.patch: A patch context manager
    """
    if mock_methods is None:
        mock_methods = {}
    
    # Create a MagicMock for the service
    mock_service = MagicMock()
    
    # Configure each method in the mock_methods dictionary
    for method_name, return_value in mock_methods.items():
        if callable(return_value) and not isinstance(return_value, MagicMock):
            # If it's a function, use it as a side effect
            method_mock = getattr(mock_service, method_name)
            method_mock.side_effect = return_value
        else:
            # Otherwise use it as a return value
            method_mock = getattr(mock_service, method_name)
            method_mock.return_value = return_value
    
    # Return a patch for the service
    return patch(service_path, return_value=mock_service)


class MockResponse:
    """
    Mock HTTP response class for testing API clients.
    """
    
    def __init__(self, json_data=None, status_code=200, text=None, headers=None):
        """
        Initialize the mock response with data and status code.
        
        Args:
            json_data: Dictionary to be returned by json() method
            status_code: HTTP status code
            text: Response body text
            headers: HTTP headers dictionary
        """
        self.json_data = json_data if json_data is not None else {}
        self.status_code = status_code
        self.text = text if text is not None else json.dumps(self.json_data)
        self.headers = headers if headers is not None else {}
    
    def json(self):
        """
        Return the JSON data from the response.
        
        Returns:
            dict: The JSON data
        """
        return self.json_data
    
    def raise_for_status(self):
        """
        Mock the requests library raise_for_status method.
        
        Raises:
            Exception: If status_code >= 400
        """
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


class MockCollection:
    """
    Mock MongoDB collection for testing database operations.
    """
    
    def __init__(self, name="test_collection", documents=None):
        """
        Initialize the mock collection with a name and documents.
        
        Args:
            name: Collection name
            documents: Initial documents in the collection
        """
        self.name = name
        self.documents = documents if documents is not None else []
        logger.info(f"Created mock collection '{name}' with {len(self.documents)} documents")
    
    def find(self, query=None, projection=None):
        """
        Mock the MongoDB find method.
        
        Args:
            query: MongoDB query dictionary
            projection: Fields to include or exclude
            
        Returns:
            list: Filtered documents
        """
        if query is None:
            query = {}
        
        # Very simple query implementation for testing
        # In a real implementation, you'd need to handle more complex MongoDB queries
        results = []
        for doc in self.documents:
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            
            if match:
                results.append(doc)
        
        return results
    
    def find_one(self, query=None, projection=None):
        """
        Mock the MongoDB find_one method.
        
        Args:
            query: MongoDB query dictionary
            projection: Fields to include or exclude
            
        Returns:
            dict: First matching document or None
        """
        results = self.find(query, projection)
        return results[0] if results else None
    
    def insert_one(self, document):
        """
        Mock the MongoDB insert_one method.
        
        Args:
            document: Document to insert
            
        Returns:
            MagicMock: Result with inserted_id
        """
        if '_id' not in document:
            document['_id'] = str(len(self.documents) + 1)  # Simple ID generation
        
        self.documents.append(document)
        
        result = MagicMock()
        result.inserted_id = document['_id']
        return result
    
    def update_one(self, query, update):
        """
        Mock the MongoDB update_one method.
        
        Args:
            query: Query to find document to update
            update: Update operations
            
        Returns:
            MagicMock: Result with modified_count
        """
        doc = self.find_one(query)
        modified_count = 0
        
        if doc:
            # Handle $set operation
            if '$set' in update:
                for key, value in update['$set'].items():
                    doc[key] = value
                modified_count = 1
            
            # Handle $push operation
            if '$push' in update:
                for key, value in update['$push'].items():
                    if key not in doc:
                        doc[key] = []
                    doc[key].append(value)
                modified_count = 1
        
        result = MagicMock()
        result.modified_count = modified_count
        return result
    
    def delete_one(self, query):
        """
        Mock the MongoDB delete_one method.
        
        Args:
            query: Query to find document to delete
            
        Returns:
            MagicMock: Result with deleted_count
        """
        doc = self.find_one(query)
        deleted_count = 0
        
        if doc:
            self.documents.remove(doc)
            deleted_count = 1
        
        result = MagicMock()
        result.deleted_count = deleted_count
        return result


class MockEventEmitter:
    """
    Mock event emitter for testing event-based communications.
    """
    
    def __init__(self):
        """
        Initialize the mock event emitter.
        """
        self.handlers = {}  # Event handlers by event type
        self.events = []    # History of emitted events
    
    def on(self, event_type, handler):
        """
        Register an event handler.
        
        Args:
            event_type: Event type to listen for
            handler: Function to call when event occurs
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
    
    def emit(self, event_type, data=None):
        """
        Emit an event and trigger handlers.
        
        Args:
            event_type: Type of event to emit
            data: Event data
            
        Returns:
            bool: True if any handlers were called, False otherwise
        """
        if data is None:
            data = {}
        
        # Record the event
        self.events.append((event_type, data))
        
        # Call handlers if any exist
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                handler(data)
            return True
        
        return False
    
    def get_events(self):
        """
        Get all emitted events.
        
        Returns:
            list: List of emitted events (tuples of event_type and data)
        """
        return self.events
    
    def clear_events(self):
        """
        Clear the emitted events list.
        """
        self.events = []