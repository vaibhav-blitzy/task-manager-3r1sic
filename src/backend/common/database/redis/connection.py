"""
Redis connection management module for the Task Management System.

This module provides a singleton Redis client and connection pool for efficient
and reliable Redis operations. It includes error handling, reconnection logic,
and health checks to ensure robust Redis connectivity.
"""

import json
import time
import functools
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar

import redis
from redis import Redis, ConnectionPool, RedisError, ConnectionError, TimeoutError

from ...config.base import BaseConfig
from ...config import get_config
from ...exceptions.api_exceptions import DependencyError
from ...logging.logger import get_logger

# Configure module logger
logger = get_logger(__name__)

# Singleton connection pool and client instances
_redis_connection_pool = None  # Singleton connection pool instance
_redis_client = None  # Singleton Redis client instance

# Connection status tracking
_connection_status = {
    'connected': False,
    'last_error': None,
    'last_connection_attempt': None
}

# Default retry settings
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 0.5


class RedisConnectionError(DependencyError):
    """
    Custom exception for Redis connection errors.
    """
    
    def __init__(self, message="Failed to connect to Redis"):
        super().__init__(message=message, dependency="Redis")


def get_redis_connection_pool() -> ConnectionPool:
    """
    Creates or returns an existing Redis connection pool as a singleton.
    
    Returns:
        ConnectionPool: Redis connection pool instance
    
    Raises:
        RedisConnectionError: If connection pool creation fails
    """
    global _redis_connection_pool, _connection_status
    
    if _redis_connection_pool is None:
        try:
            # Get config for Redis connection
            config = get_config()
            
            # Create connection pool
            _redis_connection_pool = ConnectionPool(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                decode_responses=True,  # Return strings instead of bytes
                **config.REDIS_OPTIONS
            )
            
            logger.info(f"Created Redis connection pool to {config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}")
            _connection_status['last_connection_attempt'] = time.time()
            
        except Exception as e:
            error_msg = f"Failed to create Redis connection pool: {str(e)}"
            logger.error(error_msg)
            _connection_status['last_error'] = str(e)
            _connection_status['last_connection_attempt'] = time.time()
            raise RedisConnectionError(error_msg)
    
    return _redis_connection_pool


def get_redis_client() -> Redis:
    """
    Creates or returns an existing Redis client as a singleton.
    
    Returns:
        Redis: Redis client instance
    
    Raises:
        RedisConnectionError: If client creation or connection fails
    """
    global _redis_client, _connection_status
    
    if _redis_client is None:
        try:
            # Get connection pool
            pool = get_redis_connection_pool()
            
            # Create Redis client
            _redis_client = Redis(connection_pool=pool)
            
            # Test connection with ping
            _redis_client.ping()
            
            logger.info("Successfully connected to Redis")
            _connection_status['connected'] = True
            _connection_status['last_error'] = None
            
        except (ConnectionError, TimeoutError, RedisError) as e:
            error_msg = f"Failed to connect to Redis: {str(e)}"
            logger.error(error_msg)
            _connection_status['connected'] = False
            _connection_status['last_error'] = str(e)
            raise RedisConnectionError(error_msg)
    
    return _redis_client


def ping_redis() -> bool:
    """
    Checks if the Redis connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    global _connection_status
    
    try:
        client = get_redis_client()
        response = client.ping()
        _connection_status['connected'] = True
        return response
    except (ConnectionError, TimeoutError, RedisError) as e:
        logger.warning(f"Redis ping failed: {str(e)}")
        _connection_status['connected'] = False
        _connection_status['last_error'] = str(e)
        return False


def close_connection() -> bool:
    """
    Closes the Redis connection and releases resources.
    
    Returns:
        bool: True if closed successfully, False otherwise
    """
    global _redis_client, _redis_connection_pool, _connection_status
    
    if _redis_client is not None:
        try:
            _redis_client.close()
            _redis_client = None
            _redis_connection_pool = None
            _connection_status['connected'] = False
            logger.info("Redis connection closed")
            return True
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")
            return False
    
    return True


def reconnect() -> bool:
    """
    Attempts to reconnect to Redis after a connection failure.
    
    Returns:
        bool: True if reconnection successful, False otherwise
    """
    global _redis_client, _redis_connection_pool, _connection_status
    
    # Close existing connection if any
    close_connection()
    
    # Reset connection variables
    _redis_client = None
    _redis_connection_pool = None
    
    try:
        # Attempt to get a new client
        get_redis_client()
        logger.info("Successfully reconnected to Redis")
        return True
    except RedisConnectionError as e:
        logger.error(f"Failed to reconnect to Redis: {str(e)}")
        return False


def with_retry(max_retries=DEFAULT_RETRY_COUNT, delay=DEFAULT_RETRY_DELAY, 
               retryable_errors=(ConnectionError, TimeoutError)):
    """
    Decorator that adds retry capability to Redis operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (increases exponentially)
        retryable_errors: Exception types to retry on
    
    Returns:
        callable: Decorated function with retry capability
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            current_delay = delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise
                    
                    logger.warning(f"Retrying {func.__name__} after error: {str(e)} (attempt {retry_count}/{max_retries})")
                    time.sleep(current_delay)
                    
                    # Exponential backoff
                    current_delay *= 2
        
        return wrapper
    
    return decorator


def get_connection_status() -> Dict[str, Any]:
    """
    Returns the current Redis connection status.
    
    Returns:
        dict: Dictionary with connection status information
    """
    status = _connection_status.copy()
    
    # Add current status from ping attempt if client exists
    if _redis_client is not None:
        try:
            status['ping'] = _redis_client.ping()
        except:
            status['ping'] = False
    
    return status


class RedisClient:
    """
    Wrapper class for Redis client providing convenient access to common Redis operations.
    """
    
    def __init__(self):
        """
        Initialize Redis client wrapper.
        """
        try:
            self._client = get_redis_client()
        except RedisConnectionError as e:
            logger.error(f"Failed to initialize RedisClient: {str(e)}")
            raise

    def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key to retrieve
            
        Returns:
            Value from Redis or None if key doesn't exist
        """
        try:
            value = self._client.get(key)
            logger.debug(f"Retrieved value for key '{key}'")
            return value
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error retrieving key '{key}' from Redis: {str(e)}")
            return None

    def set(self, key: str, value: Any, expiration: Optional[int] = None) -> bool:
        """
        Set a value in Redis with optional expiration.
        
        Args:
            key: Redis key
            value: Value to store
            expiration: Expiration time in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert value to string if it's not already
            if not isinstance(value, (str, int, float, bool)):
                value = str(value)
                
            self._client.set(key, value, ex=expiration)
            logger.debug(f"Set value for key '{key}'{' with expiration ' + str(expiration) + 's' if expiration else ''}")
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error setting key '{key}' in Redis: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._client.delete(key)
            logger.debug(f"Deleted key '{key}'")
            return True
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error deleting key '{key}' from Redis: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self._client.exists(key))
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error checking existence of key '{key}' in Redis: {str(e)}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self._client.expire(key, seconds))
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error setting expiration for key '{key}' in Redis: {str(e)}")
            return False

    def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a Redis channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of subscribers that received the message
        """
        try:
            # Convert message to JSON string if it's not a string
            if not isinstance(message, str):
                message = json.dumps(message)
                
            return self._client.publish(channel, message)
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"Error publishing to channel '{channel}' in Redis: {str(e)}")
            return 0

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a JSON value from Redis and deserialize it.
        
        Args:
            key: Redis key to retrieve
            
        Returns:
            Deserialized JSON object or None if key doesn't exist
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Error deserializing JSON from key '{key}': {str(e)}")
        return None

    def set_json(self, key: str, value: Any, expiration: Optional[int] = None) -> bool:
        """
        Serialize and store a JSON-serializable object in Redis.
        
        Args:
            key: Redis key
            value: JSON-serializable value to store
            expiration: Expiration time in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            json_string = json.dumps(value)
            return self.set(key, json_string, expiration)
        except TypeError as e:
            logger.error(f"Error serializing JSON for key '{key}': {str(e)}")
            return False


class RedisHealthCheck:
    """
    Health check class for Redis connection monitoring.
    """
    
    def __init__(self):
        """
        Initialize the Redis health check.
        """
        self.name = "redis"
        self.status = {"healthy": False}
    
    def check(self) -> Dict[str, Any]:
        """
        Performs a health check on the Redis connection.
        
        Returns:
            Health check result with status and details
        """
        start_time = time.time()
        
        # Get connection status
        status = get_connection_status()
        
        # Try to ping Redis
        try:
            client = get_redis_client()
            ping_result = client.ping()
            response_time = time.time() - start_time
            
            self.status = {
                "healthy": ping_result,
                "responseTime": round(response_time * 1000, 2),  # Convert to ms
                "lastError": status.get("last_error"),
                "lastConnectionAttempt": status.get("last_connection_attempt"),
                "details": "Redis connection is healthy"
            }
        except Exception as e:
            self.status = {
                "healthy": False,
                "error": str(e),
                "lastError": status.get("last_error"),
                "lastConnectionAttempt": status.get("last_connection_attempt"),
                "details": "Redis connection is not healthy"
            }
        
        return self.status