"""
MongoDB connection management module for the Task Management System.

This module provides a centralized connection management for MongoDB,
including connection pooling, retry mechanisms, health checks, and
database operations with proper error handling and logging.
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import pymongo  # v4.3.3
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure, 
    NetworkTimeout, 
    OperationFailure,
    ServerSelectionTimeoutError,
    AutoReconnect
)

from ...config import get_config
from ...exceptions.api_exceptions import DependencyError
from ...logging.logger import get_logger

# Configure module logger
logger = get_logger(__name__)

# Global connection instances
_client = None
_database = None

# Track connection status
_connection_status = {
    'connected': False,
    'last_error': None,
    'last_connection_attempt': None
}

# Retry configuration
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 0.5  # seconds

# Type variable for generic function return type in decorators
T = TypeVar('T')

def initialize_database() -> bool:
    """
    Initializes the MongoDB connection using application configuration.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    global _client, _database, _connection_status
    
    try:
        # Get MongoDB configuration from app config
        config = get_config()
        mongo_settings = config.get_mongodb_settings()
        
        # Extract connection URI and options
        mongo_uri = mongo_settings.get('uri')
        mongo_options = mongo_settings.get('options', {})
        
        # Log connection attempt with redacted URI (hide credentials)
        uri_parts = mongo_uri.split('@')
        redacted_uri = f"mongodb://***@{uri_parts[-1]}" if len(uri_parts) > 1 else mongo_uri
        logger.info(f"Initializing MongoDB connection to {redacted_uri}")
        
        # Create MongoDB client
        _client = pymongo.MongoClient(mongo_uri, **mongo_options)
        
        # Test connection with ping
        _client.admin.command('ping')
        
        # Get database name from config or extract from URI
        db_name = getattr(config, 'MONGO_DB_NAME', None)
        if not db_name and '/' in uri_parts[-1]:
            # Extract DB name from URI if present
            db_name = uri_parts[-1].split('/')[1].split('?')[0]
        
        # Default to 'task_management' if no DB name is found
        db_name = db_name or 'task_management'
        _database = _client[db_name]
        
        # Update connection status
        _connection_status['connected'] = True
        _connection_status['last_error'] = None
        _connection_status['last_connection_attempt'] = time.time()
        
        logger.info(f"Successfully connected to MongoDB database: {db_name}")
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
        _connection_status['connected'] = False
        _connection_status['last_error'] = str(e)
        _connection_status['last_connection_attempt'] = time.time()
        
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False

def get_client() -> pymongo.MongoClient:
    """
    Returns the MongoDB client instance, initializing it if necessary.
    
    Returns:
        pymongo.MongoClient: MongoDB client instance
        
    Raises:
        DependencyError: If unable to establish a MongoDB connection
    """
    global _client
    
    # If client doesn't exist or has been closed, initialize
    if _client is None:
        if not initialize_database():
            raise DependencyError(
                message="Unable to establish MongoDB connection",
                dependency="mongodb",
                retryable=True
            )
    
    return _client

def get_database() -> Database:
    """
    Returns the MongoDB database instance for the application.
    
    Returns:
        pymongo.database.Database: MongoDB database instance
        
    Raises:
        DependencyError: If unable to establish a MongoDB connection
    """
    global _database
    
    # If database doesn't exist, ensure client exists and get database
    if _database is None:
        client = get_client()  # This will initialize if needed
        
        # Get database name from config
        config = get_config()
        db_name = getattr(config, 'MONGO_DB_NAME', 'task_management')
        
        _database = client[db_name]
        logger.debug(f"Using MongoDB database: {db_name}")
    
    return _database

def get_collection(collection_name: str) -> Collection:
    """
    Returns a MongoDB collection by name.
    
    Args:
        collection_name (str): Name of the collection to retrieve
        
    Returns:
        pymongo.collection.Collection: MongoDB collection instance
    """
    db = get_database()
    return db[collection_name]

def ping_database() -> bool:
    """
    Checks if the MongoDB connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        client = get_client()
        # Use runCommand directly for more control
        ping_result = client.admin.command('ping')
        
        # Connection is healthy if we get a successful response
        if ping_result.get('ok', 0) == 1:
            return True
        else:
            logger.warning(f"MongoDB ping returned unexpected result: {ping_result}")
            return False
            
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {str(e)}")
        
        # Update connection status
        _connection_status['connected'] = False
        _connection_status['last_error'] = str(e)
        
        return False

def close_connection() -> bool:
    """
    Closes the MongoDB connection and releases resources.
    
    Returns:
        bool: True if closed successfully, False otherwise
    """
    global _client, _database, _connection_status
    
    if _client is not None:
        try:
            _client.close()
            logger.info("MongoDB connection closed successfully")
            
            # Reset global variables
            _client = None
            _database = None
            
            # Update connection status
            _connection_status['connected'] = False
            _connection_status['last_error'] = None
            
            return True
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
            return False
    
    return True  # Already closed

def reconnect() -> bool:
    """
    Attempts to reconnect to MongoDB after a connection failure.
    
    Returns:
        bool: True if reconnection successful, False otherwise
    """
    # Close existing connection if any
    close_connection()
    
    # Try to initialize a new connection
    success = initialize_database()
    
    if success:
        logger.info("Successfully reconnected to MongoDB")
    else:
        logger.error("Failed to reconnect to MongoDB")
    
    return success

def with_retry(max_retries: int = DEFAULT_RETRY_COUNT, 
               delay: float = DEFAULT_RETRY_DELAY,
               retryable_errors: List = None) -> Callable:
    """
    Decorator that adds retry capability to MongoDB operations.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        delay (float): Initial delay between retries (seconds)
        retryable_errors (List): List of exception types to retry on
        
    Returns:
        callable: Decorated function with retry capability
    """
    if retryable_errors is None:
        retryable_errors = [
            ConnectionFailure,
            NetworkTimeout,
            ServerSelectionTimeoutError,
            OperationFailure,
            AutoReconnect
        ]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(retryable_errors) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Use exponential backoff with a small random factor for retries
                        sleep_time = delay * (2 ** attempt) * (0.9 + 0.2 * (time.time() % 1))
                        
                        logger.warning(
                            f"MongoDB operation failed: {str(e)}. "
                            f"Retrying in {sleep_time:.2f}s ({attempt+1}/{max_retries})"
                        )
                        
                        time.sleep(sleep_time)
                        
                        # Check connection and reconnect if needed
                        if not ping_database():
                            logger.info("Attempting to reconnect to MongoDB before retry")
                            reconnect()
                    else:
                        logger.error(
                            f"MongoDB operation failed after {max_retries} retries: {str(e)}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    
    return decorator

def get_connection_status() -> Dict:
    """
    Returns the current MongoDB connection status.
    
    Returns:
        dict: Dictionary with connection status information
    """
    # Make a copy of the status dict and add current ping result
    status = _connection_status.copy()
    
    # Only ping if we think we're connected to avoid unnecessary connection attempts
    if status['connected']:
        status['healthy'] = ping_database()
    else:
        status['healthy'] = False
    
    # Add additional info for monitoring
    if _client is not None:
        try:
            server_info = _client.server_info()
            status['server_version'] = server_info.get('version', 'unknown')
            status['server_info'] = {
                'version': server_info.get('version', 'unknown'),
                'uptime': server_info.get('uptime', 0),
                'localTime': server_info.get('localTime', None)
            }
        except Exception as e:
            status['server_info_error'] = str(e)
    
    return status

def create_indexes(index_specs: Dict[str, List[Dict]]) -> Dict:
    """
    Creates indexes on MongoDB collections for performance optimization.
    
    Args:
        index_specs (dict): Dictionary mapping collection names to lists of index specifications
        
    Returns:
        dict: Dictionary with index creation results by collection
    """
    results = {}
    db = get_database()
    
    for collection_name, indexes in index_specs.items():
        results[collection_name] = {"success": [], "error": []}
        
        try:
            collection = db[collection_name]
            
            for index_spec in indexes:
                try:
                    # Extract index keys and options
                    if isinstance(index_spec, dict) and "keys" in index_spec:
                        keys = index_spec.pop("keys")
                        options = index_spec
                    else:
                        keys = index_spec
                        options = {}
                    
                    # Create the index
                    result = collection.create_index(keys, **options)
                    results[collection_name]["success"].append({
                        "name": result,
                        "keys": keys,
                        "options": options
                    })
                    
                    logger.info(f"Created index {result} on {collection_name}")
                except Exception as e:
                    error_info = {
                        "spec": str(index_spec), 
                        "error": str(e)
                    }
                    results[collection_name]["error"].append(error_info)
                    
                    logger.error(f"Failed to create index on {collection_name}: {str(e)}")
        except Exception as e:
            results[collection_name]["error"].append({"error": str(e)})
            logger.error(f"Error accessing collection {collection_name}: {str(e)}")
    
    return results

def drop_indexes(index_specs: Dict[str, List[str]]) -> Dict:
    """
    Drops specified indexes from MongoDB collections.
    
    Args:
        index_specs (dict): Dictionary mapping collection names to lists of index names
        
    Returns:
        dict: Dictionary with results of index dropping operations
    """
    results = {}
    db = get_database()
    
    for collection_name, indexes in index_specs.items():
        results[collection_name] = {"success": [], "error": []}
        
        try:
            collection = db[collection_name]
            
            for index_name in indexes:
                try:
                    collection.drop_index(index_name)
                    results[collection_name]["success"].append(index_name)
                    
                    logger.info(f"Dropped index {index_name} from {collection_name}")
                except Exception as e:
                    error_info = {"index": index_name, "error": str(e)}
                    results[collection_name]["error"].append(error_info)
                    
                    logger.error(f"Failed to drop index {index_name} from {collection_name}: {str(e)}")
        except Exception as e:
            results[collection_name]["error"].append({"error": str(e)})
            logger.error(f"Error accessing collection {collection_name}: {str(e)}")
    
    return results

class MongoDBHealthCheck:
    """
    Health check class for MongoDB connection monitoring.
    """
    
    def __init__(self):
        """
        Initializes the MongoDB health check.
        """
        self.name = "mongodb"
        self.status = {"healthy": False, "details": {}}
    
    def check(self) -> Dict:
        """
        Performs a health check on the MongoDB connection.
        
        Returns:
            dict: Health check result with status and details
        """
        start_time = time.time()
        is_healthy = False
        details = {}
        
        try:
            # Get current connection status
            conn_status = get_connection_status()
            
            # Attempt a ping to verify connection
            is_healthy = ping_database()
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Collect relevant metrics
            details = {
                "connected": conn_status['connected'],
                "responseTimeMs": round(response_time * 1000, 2),
                "lastConnectionAttempt": conn_status.get('last_connection_attempt')
            }
            
            # Add server info if available
            if 'server_info' in conn_status:
                details["serverInfo"] = conn_status["server_info"]
            
            if not is_healthy:
                details["lastError"] = conn_status.get('last_error')
            
        except Exception as e:
            is_healthy = False
            details = {
                "error": str(e),
                "lastError": _connection_status.get('last_error')
            }
            
            logger.error(f"Health check failed: {str(e)}")
        
        # Update and return health status
        self.status = {
            "healthy": is_healthy,
            "details": details
        }
        
        return self.status