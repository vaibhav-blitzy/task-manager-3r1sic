"""
Health check endpoints for the API Gateway service.

This module implements various health check endpoints for monitoring,
high availability management, and alerting. It provides basic, readiness,
liveness, database, and dependencies health checks.
"""

import time
import datetime
import requests
from flask import Blueprint, jsonify, current_app

from src.backend.common.database.mongo.connection import ping_database, get_connection_status
from src.backend.common.database.redis.connection import ping_redis, get_connection_status
from src.backend.services.api_gateway.config import get_config, get_service_url

# Create a blueprint for health routes
health_bp = Blueprint('health', __name__, url_prefix='/health')

# Default timeout for external service checks
TIMEOUT = 3.0


def check_service(service_name, url, timeout=TIMEOUT):
    """
    Checks the health of a service by making an HTTP request to its health endpoint.
    
    Args:
        service_name (str): The name of the service to check
        url (str): The base URL of the service
        timeout (float): Request timeout in seconds
        
    Returns:
        dict: Status of the service including availability, response time, and status code
    """
    start_time = time.time()
    result = {
        'service': service_name,
        'url': url,
        'available': False,
        'status_code': None,
        'response_time': None,
        'error': None
    }
    
    try:
        # Append the health endpoint to the URL
        health_url = f"{url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=timeout)
        response_time = time.time() - start_time
        
        result.update({
            'available': response.status_code == 200,
            'status_code': response.status_code,
            'response_time': round(response_time * 1000, 2),  # Convert to ms
        })
        
        # If response is not 200, add error details
        if response.status_code != 200:
            result['error'] = f"Service returned status {response.status_code}"
            
    except requests.RequestException as e:
        result.update({
            'available': False,
            'error': str(e),
            'response_time': round((time.time() - start_time) * 1000, 2)  # Convert to ms
        })
    
    return result


def check_mongo():
    """
    Checks the health of the MongoDB connection.
    
    Returns:
        dict: Status of the MongoDB connection including availability and response time
    """
    start_time = time.time()
    is_healthy = ping_database()
    response_time = time.time() - start_time
    
    connection_status = get_connection_status()
    
    return {
        'available': is_healthy,
        'response_time': round(response_time * 1000, 2),  # Convert to ms
        'details': connection_status
    }


def check_redis():
    """
    Checks the health of the Redis connection.
    
    Returns:
        dict: Status of the Redis connection including availability and response time
    """
    start_time = time.time()
    is_healthy = ping_redis()
    response_time = time.time() - start_time
    
    connection_status = get_connection_status()
    
    return {
        'available': is_healthy,
        'response_time': round(response_time * 1000, 2),  # Convert to ms
        'details': connection_status
    }


@health_bp.route('', methods=['GET'])
def health():
    """
    Basic health check endpoint that verifies the service is running.
    
    Returns:
        Response: JSON response with basic health status
    """
    response = {
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': current_app.config.get('SERVICE_NAME', 'api-gateway'),
        'version': current_app.config.get('API_VERSION', 'v1')
    }
    
    return jsonify(response), 200


@health_bp.route('/readiness', methods=['GET'])
def readiness():
    """
    Readiness check endpoint that verifies the service is ready to handle requests.
    
    This checks database connections and essential dependencies to ensure
    the service can properly handle incoming requests.
    
    Returns:
        Response: JSON response with readiness status details
    """
    # Check database connections
    mongo_status = check_mongo()
    redis_status = check_redis()
    
    # Determine if the service is ready based on database availability
    is_ready = mongo_status['available'] and redis_status['available']
    
    response = {
        'status': 'ready' if is_ready else 'not_ready',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': current_app.config.get('SERVICE_NAME', 'api-gateway'),
        'version': current_app.config.get('API_VERSION', 'v1'),
        'databases': {
            'mongodb': mongo_status,
            'redis': redis_status
        }
    }
    
    return jsonify(response), 200 if is_ready else 503


@health_bp.route('/liveness', methods=['GET'])
def liveness():
    """
    Liveness check endpoint that verifies the service is functioning correctly.
    
    This checks basic application functionality to ensure the service is alive
    and not in a deadlocked or error state.
    
    Returns:
        Response: JSON response with liveness status details
    """
    # Check if basic application functionality is working
    try:
        # Try to access application config
        _ = get_config()
        is_alive = True
        error = None
    except Exception as e:
        is_alive = False
        error = str(e)
    
    response = {
        'status': 'alive' if is_alive else 'not_alive',
        'timestamp': datetime.datetime.now().isoformat(),
        'service': current_app.config.get('SERVICE_NAME', 'api-gateway'),
        'version': current_app.config.get('API_VERSION', 'v1'),
        'error': error
    }
    
    # Include memory and process information if available
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        response['system'] = {
            'memory_usage': memory_info.rss,
            'cpu_percent': process.cpu_percent(interval=0.1),
            'thread_count': process.num_threads(),
            'uptime': time.time() - process.create_time()
        }
    except (ImportError, Exception):
        # This is optional, so continue if psutil is not available
        pass
    
    return jsonify(response), 200 if is_alive else 500


@health_bp.route('/db', methods=['GET'])
def db():
    """
    Database health check endpoint that verifies database connectivity.
    
    This checks connections to all database systems used by the application.
    
    Returns:
        Response: JSON response with database health status
    """
    # Check database connections
    mongo_status = check_mongo()
    redis_status = check_redis()
    
    # Determine overall database health
    is_healthy = mongo_status['available'] and redis_status['available']
    
    response = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'databases': {
            'mongodb': mongo_status,
            'redis': redis_status
        }
    }
    
    return jsonify(response), 200 if is_healthy else 503


@health_bp.route('/dependencies', methods=['GET'])
def dependencies():
    """
    Dependency health check endpoint that verifies connectivity to dependent services.
    
    This checks the health of all backend services that the API Gateway depends on.
    
    Returns:
        Response: JSON response with dependency health status
    """
    # Get service configuration
    config = get_config()
    service_routes = config.SERVICE_ROUTES
    
    # Check each service
    results = {}
    for service_name in service_routes:
        try:
            service_url = get_service_url(service_name)
            results[service_name] = check_service(service_name, service_url, TIMEOUT)
        except ValueError:
            results[service_name] = {
                'service': service_name,
                'available': False,
                'error': 'Service URL not configured'
            }
    
    # Determine overall status
    is_healthy = all(service['available'] for service in results.values())
    
    response = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'services': results
    }
    
    return jsonify(response), 200 if is_healthy else 503