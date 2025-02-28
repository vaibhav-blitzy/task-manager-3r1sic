"""
Database package initialization for the Task Management System.

This module initializes the database package by exposing MongoDB and Redis connection
modules, providing a unified entry point for all database interactions within the
Task Management System. It serves as a facade to abstract database implementation
details from application services.
"""

import logging
from typing import Dict

# Import MongoDB connection module
from .mongo.connection import (
    initialize_database,
    get_client,
    get_database,
    get_collection,
    ping_database,
    MongoDBHealthCheck,
    with_retry
)

# Import Redis connection module
from .redis.connection import (
    get_redis_client,
    RedisClient,
    ping_redis,
    RedisHealthCheck
)

# Import configuration module
from ..config import get_config

# Configure module logger
logger = logging.getLogger(__name__)

def check_database_health() -> Dict:
    """
    Checks the health of all database connections.
    
    Returns:
        dict: Health status of all database connections
    """
    mongo_health = ping_database()
    redis_health = ping_redis()
    
    health_status = {
        "mongodb": {
            "healthy": mongo_health,
            "details": "MongoDB connection is healthy" if mongo_health else "MongoDB connection is unhealthy"
        },
        "redis": {
            "healthy": redis_health,
            "details": "Redis connection is healthy" if redis_health else "Redis connection is unhealthy"
        },
        "overall": mongo_health and redis_health
    }
    
    if not health_status["overall"]:
        logger.warning("One or more database connections are unhealthy")
    
    return health_status

def initialize_connections() -> bool:
    """
    Initialize all database connections.
    
    Returns:
        bool: True if all connections initialized successfully, False otherwise
    """
    # Initialize MongoDB
    mongodb_initialized = initialize_database()
    if not mongodb_initialized:
        logger.error("Failed to initialize MongoDB connection")
    else:
        logger.info("MongoDB connection initialized successfully")
    
    # Initialize Redis
    try:
        redis_client = get_redis_client()
        redis_initialized = redis_client is not None
        if not redis_initialized:
            logger.error("Failed to initialize Redis connection")
        else:
            logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Redis connection: {str(e)}")
        redis_initialized = False
    
    # Return overall success status
    return mongodb_initialized and redis_initialized

def close_connections() -> bool:
    """
    Close all database connections.
    
    Returns:
        bool: True if all connections closed successfully, False otherwise
    """
    # Close MongoDB connection
    try:
        from .mongo.connection import close_connection as mongo_close
        mongo_closed = mongo_close()
        if not mongo_closed:
            logger.warning("Failed to close MongoDB connection")
        else:
            logger.info("MongoDB connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")
        mongo_closed = False
    
    # Close Redis connection
    try:
        from .redis.connection import close_connection as redis_close
        redis_closed = redis_close()
        if not redis_closed:
            logger.warning("Failed to close Redis connection")
        else:
            logger.info("Redis connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {str(e)}")
        redis_closed = False
    
    # Return overall success status
    return mongo_closed and redis_closed

class DatabaseHealthCheck:
    """
    Composite health check for all database systems.
    """
    
    def __init__(self):
        """
        Initialize the database health check.
        """
        self.name = 'database'
        self.status = {'healthy': False}
        self.mongodb_check = MongoDBHealthCheck()
        self.redis_check = RedisHealthCheck()
    
    def check(self) -> Dict:
        """
        Performs health checks on all database connections.
        
        Returns:
            dict: Combined health check results
        """
        # Check MongoDB health
        mongodb_status = self.mongodb_check.check()
        
        # Check Redis health
        redis_status = self.redis_check.check()
        
        # Combine results
        is_healthy = mongodb_status.get('healthy', False) and redis_status.get('healthy', False)
        
        self.status = {
            'healthy': is_healthy,
            'mongodb': mongodb_status,
            'redis': redis_status,
        }
        
        return self.status