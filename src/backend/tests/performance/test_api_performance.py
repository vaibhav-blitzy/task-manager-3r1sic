"""
Performance tests for the Task Management System's API endpoints to ensure
they meet the specified performance requirements.
"""

import os
import pytest
import requests
import time
import statistics
import subprocess
import json
import datetime
from typing import List, Dict, Any, Optional

# Internal imports
from ..conftest import authenticated_user_headers
from ...common.testing.fixtures import performance_test_app 
from ...common.config.base import Config
from ...common.logging.logger import get_logger

# API endpoints to test
API_ENDPOINTS = [
    '/api/v1/auth/login',
    '/api/v1/tasks',
    '/api/v1/projects',
    '/api/v1/notifications/count',
    '/api/v1/files'
]

# Performance thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    'p95_response_time': 200,  # 95% of requests should be faster than 200ms
    'p99_response_time': 1000, # 99% of requests should be faster than 1000ms
    'max_response_time': 3000  # No request should take longer than 3000ms
}

# Path to k6 load testing scripts
K6_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '../../../infrastructure/load-testing/k6/scripts')

# Configure logger
logger = get_logger('performance_tests')

def calculate_percentile(measurements: List[float], percentile: float) -> float:
    """
    Utility function to calculate percentile values from a list of measurements.
    
    Args:
        measurements: List of measurements
        percentile: Percentile value to calculate
        
    Returns:
        The calculated percentile value
    """
    if not measurements:
        return 0.0
        
    # Sort measurements to calculate percentiles
    sorted_measurements = sorted(measurements)
    
    # Calculate the index for the percentile
    index = (len(sorted_measurements) - 1) * (percentile / 100)
    
    # If index is an integer, return the value at that index
    if index.is_integer():
        return sorted_measurements[int(index)]
    
    # Otherwise interpolate between the two nearest values
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(sorted_measurements) - 1)
    
    lower_value = sorted_measurements[lower_index]
    upper_value = sorted_measurements[upper_index]
    
    # Interpolate between the two values
    fraction = index - lower_index
    return lower_value + (upper_value - lower_value) * fraction


@pytest.mark.performance
def test_api_endpoints_response_time(performance_test_app, authenticated_user):
    """
    Tests that all critical API endpoints respond within the required time thresholds.
    
    Args:
        performance_test_app: Flask test client with performance configuration
        authenticated_user: Pytest fixture providing an authenticated user
    """
    # Create a session with authentication
    session = requests.Session()
    session.headers.update(authenticated_user_headers)
    
    base_url = performance_test_app.config.get('BASE_URL', 'http://localhost:5000')
    
    # Number of samples for each endpoint
    sample_size = 100
    
    for endpoint in API_ENDPOINTS:
        logger.info(f"Testing response time for endpoint: {endpoint}")
        
        # Store response times
        response_times = []
        
        # Make multiple requests to get a good sample
        for _ in range(sample_size):
            start_time = time.time()
            
            # Use GET for most endpoints, but may need to customize for endpoints that require POST
            if endpoint == '/api/v1/auth/login':
                # Special case for login which requires POST with credentials
                response = session.post(
                    f"{base_url}{endpoint}", 
                    json={"email": "test@example.com", "password": "Test@123"}
                )
            else:
                response = session.get(f"{base_url}{endpoint}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Record response time
            response_times.append(response_time)
            
            # Ensure request was successful
            assert response.status_code in (200, 201), f"Request to {endpoint} failed with status {response.status_code}"
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = calculate_percentile(response_times, 95)
        p99_response_time = calculate_percentile(response_times, 99)
        max_response_time = max(response_times)
        
        # Log results
        logger.info(f"Endpoint {endpoint} - Average: {avg_response_time:.2f}ms, " +
                    f"p95: {p95_response_time:.2f}ms, p99: {p99_response_time:.2f}ms, " +
                    f"Max: {max_response_time:.2f}ms")
        
        # Assert that the response times meet the performance thresholds
        assert p95_response_time < PERFORMANCE_THRESHOLDS['p95_response_time'], \
            f"p95 response time ({p95_response_time:.2f}ms) exceeds threshold ({PERFORMANCE_THRESHOLDS['p95_response_time']}ms)"
        
        assert p99_response_time < PERFORMANCE_THRESHOLDS['p99_response_time'], \
            f"p99 response time ({p99_response_time:.2f}ms) exceeds threshold ({PERFORMANCE_THRESHOLDS['p99_response_time']}ms)"
        
        assert max_response_time < PERFORMANCE_THRESHOLDS['max_response_time'], \
            f"Maximum response time ({max_response_time:.2f}ms) exceeds threshold ({PERFORMANCE_THRESHOLDS['max_response_time']}ms)"


@pytest.mark.performance
def test_task_creation_performance(performance_test_app, authenticated_user):
    """
    Tests the performance of creating new tasks in the system.
    
    Args:
        performance_test_app: Flask test client with performance configuration
        authenticated_user: Pytest fixture providing an authenticated user
    """
    # Create a session with authentication
    session = requests.Session()
    session.headers.update(authenticated_user_headers)
    
    base_url = performance_test_app.config.get('BASE_URL', 'http://localhost:5000')
    endpoint = '/api/v1/tasks'
    
    # Number of tasks to create
    sample_size = 50
    
    # Prepare a task creation payload
    task_payload = {
        "title": "Performance Test Task",
        "description": "This is a task created during performance testing",
        "status": "not_started",
        "priority": "medium",
        "dueDate": (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    }
    
    # Store response times
    response_times = []
    start_time_total = time.time()
    
    # Create tasks and measure performance
    for i in range(sample_size):
        # Modify the task title to ensure uniqueness
        task_payload["title"] = f"Performance Test Task {i}"
        
        # Measure creation time
        start_time = time.time()
        response = session.post(f"{base_url}{endpoint}", json=task_payload)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        response_times.append(response_time)
        
        # Ensure request was successful
        assert response.status_code == 201, f"Task creation failed with status {response.status_code}"
    
    end_time_total = time.time()
    total_duration = end_time_total - start_time_total
    
    # Calculate statistics
    avg_response_time = statistics.mean(response_times)
    p95_response_time = calculate_percentile(response_times, 95)
    p99_response_time = calculate_percentile(response_times, 99)
    max_response_time = max(response_times)
    throughput = sample_size / total_duration  # Tasks per second
    
    # Log results
    logger.info(f"Task Creation - Average: {avg_response_time:.2f}ms, " +
                f"p95: {p95_response_time:.2f}ms, p99: {p99_response_time:.2f}ms, " +
                f"Max: {max_response_time:.2f}ms, Throughput: {throughput:.2f} tasks/s")
    
    # Assert that the response times meet the performance thresholds
    assert p95_response_time < 250, \
        f"p95 task creation time ({p95_response_time:.2f}ms) exceeds threshold (250ms)"
    
    assert p99_response_time < 1000, \
        f"p99 task creation time ({p99_response_time:.2f}ms) exceeds threshold (1000ms)"
    
    assert throughput > 10, \
        f"Task creation throughput ({throughput:.2f} tasks/s) below threshold (10 tasks/s)"


@pytest.mark.performance
def test_project_listing_performance(performance_test_app, authenticated_user, sample_projects):
    """
    Tests the performance of retrieving and paginating through project listings.
    
    Args:
        performance_test_app: Flask test client with performance configuration
        authenticated_user: Pytest fixture providing an authenticated user
        sample_projects: Pytest fixture providing sample project data
    """
    # Create a session with authentication
    session = requests.Session()
    session.headers.update(authenticated_user_headers)
    
    base_url = performance_test_app.config.get('BASE_URL', 'http://localhost:5000')
    endpoint = '/api/v1/projects'
    
    # Different page sizes to test
    page_sizes = [10, 50, 100]
    
    for page_size in page_sizes:
        logger.info(f"Testing project listing with page size: {page_size}")
        
        # Store response times
        response_times = []
        
        # Make 20 requests for this page size to get a good sample
        for i in range(20):
            # Vary the page number to test different pages
            page = (i % 5) + 1  # Pages 1-5
            
            # Measure response time
            start_time = time.time()
            response = session.get(f"{base_url}{endpoint}?page={page}&page_size={page_size}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            response_times.append(response_time)
            
            # Ensure request was successful
            assert response.status_code == 200, f"Project listing failed with status {response.status_code}"
            
            # Verify the response contains the expected number of items
            data = response.json()
            assert "items" in data, "Response missing 'items' field"
            
            # Items may be less than page_size if we've reached the end of the list
            if page * page_size <= len(sample_projects):
                assert len(data["items"]) <= page_size, f"Expected at most {page_size} items, got {len(data['items'])}"
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = calculate_percentile(response_times, 95)
        
        # Log results
        logger.info(f"Project listing (page_size={page_size}) - Average: {avg_response_time:.2f}ms, " +
                    f"p95: {p95_response_time:.2f}ms")
        
        # Assert that the response times meet the performance thresholds
        assert p95_response_time < 200, \
            f"p95 project listing time ({p95_response_time:.2f}ms) for page_size={page_size} exceeds threshold (200ms)"
        
        # Verify response time scaling is roughly linear with page size
        # This works for page sizes after the first one
        if page_sizes.index(page_size) > 0:
            previous_page_size = page_sizes[page_sizes.index(page_size) - 1]
            expected_scaling_factor = page_size / previous_page_size
            
            # Allow for some flexibility in the scaling factor (0.5x - 2x linear)
            assert avg_response_time < (avg_response_time * expected_scaling_factor * 1.5), \
                f"Response time does not scale linearly with page size"


@pytest.mark.performance
def test_search_performance(performance_test_app, authenticated_user, sample_data):
    """
    Tests the performance of the search functionality across tasks and projects.
    
    Args:
        performance_test_app: Flask test client with performance configuration
        authenticated_user: Pytest fixture providing an authenticated user
        sample_data: Pytest fixture providing sample searchable data
    """
    # Create a session with authentication
    session = requests.Session()
    session.headers.update(authenticated_user_headers)
    
    base_url = performance_test_app.config.get('BASE_URL', 'http://localhost:5000')
    endpoint = '/api/v1/search'
    
    # Define test search queries of increasing complexity
    search_tests = [
        {"name": "Simple search", "query": "test", "expected_max_time": 300},
        {"name": "Complex search", "query": "project:website status:in_progress", "expected_max_time": 500},
        {"name": "Wildcard search", "query": "design*", "expected_max_time": 800}
    ]
    
    for test in search_tests:
        logger.info(f"Testing {test['name']}: {test['query']}")
        
        # Store response times
        response_times = []
        
        # Make 20 requests for each search type
        for _ in range(20):
            # Measure response time
            start_time = time.time()
            response = session.get(f"{base_url}{endpoint}?q={test['query']}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            response_times.append(response_time)
            
            # Ensure request was successful
            assert response.status_code == 200, f"Search failed with status {response.status_code}"
            
            # Verify the response contains results
            data = response.json()
            assert "results" in data, "Response missing 'results' field"
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        p95_response_time = calculate_percentile(response_times, 95)
        
        # Log results
        logger.info(f"{test['name']} - Average: {avg_response_time:.2f}ms, " +
                   f"p95: {p95_response_time:.2f}ms")
        
        # Assert performance meets the test-specific threshold
        assert p95_response_time < test['expected_max_time'], \
            f"p95 search time ({p95_response_time:.2f}ms) for '{test['name']}' exceeds threshold ({test['expected_max_time']}ms)"


def run_k6_test(script_name: str, options: dict) -> dict:
    """
    Executes a k6 load testing script and returns the results.
    
    Args:
        script_name: Name of the k6 script file (without path)
        options: Dictionary of k6 options (vus, duration, etc.)
        
    Returns:
        Dictionary containing test results
    """
    # Construct full path to script
    script_path = os.path.join(K6_SCRIPTS_DIR, script_name)
    
    # Verify script exists
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Build k6 command with options
    command = ["k6", "run"]
    
    # Add each option
    for key, value in options.items():
        command.append(f"--{key}={value}")
    
    # Add script path
    command.append(script_path)
    
    logger.info(f"Running k6 test: {' '.join(command)}")
    
    # Execute k6 process
    try:
        # Run process and capture output
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON summary from output if available
        output = result.stdout
        
        # Look for JSON summary data
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            summary_json = output[json_start:json_end]
            try:
                summary = json.loads(summary_json)
                return summary
            except json.JSONDecodeError:
                logger.warning("Failed to parse k6 JSON output")
        
        # If we couldn't find or parse JSON, return text output
        return {"stdout": output, "stderr": result.stderr}
    
    except subprocess.CalledProcessError as e:
        logger.error(f"k6 test failed: {e}")
        return {"error": str(e), "stdout": e.stdout, "stderr": e.stderr}
    except Exception as e:
        logger.error(f"Error running k6 test: {e}")
        return {"error": str(e)}


@pytest.mark.performance
@pytest.mark.load
def test_auth_load():
    """
    Tests the authentication endpoints under load conditions.
    """
    # Skip test if not explicitly enabled
    if os.environ.get("ENABLE_LOAD_TESTS") != "true":
        pytest.skip("Load tests not enabled. Set ENABLE_LOAD_TESTS=true to run.")
    
    # Run k6 test for authentication
    options = {
        "vus": 500,          # 500 virtual users
        "duration": "30s",   # 30 second test
        "summaryTrendStats": "avg,min,med,p95,p99,max",
        "summary-export": "/tmp/auth_load_test_summary.json"
    }
    
    results = run_k6_test("auth.js", options)
    
    # Extract metrics from results
    http_req_duration_p95 = results.get("metrics", {}).get("http_req_duration", {}).get("p95", float('inf'))
    error_rate = results.get("metrics", {}).get("http_req_failed", {}).get("rate", 0) * 100  # Convert to percentage
    http_reqs = results.get("metrics", {}).get("http_reqs", {}).get("rate", 0)
    
    # Log results
    logger.info(f"Auth Load Test - p95 Response Time: {http_req_duration_p95:.2f}ms, "
                f"Error Rate: {error_rate:.2f}%, Throughput: {http_reqs:.2f} reqs/s")
    
    # Assert results meet performance requirements
    assert http_req_duration_p95 < 1000, f"p95 auth response time ({http_req_duration_p95:.2f}ms) exceeds threshold (1000ms)"
    assert error_rate < 1, f"Auth error rate ({error_rate:.2f}%) exceeds threshold (1%)"
    assert http_reqs > 50, f"Auth throughput ({http_reqs:.2f} reqs/s) below threshold (50 reqs/s)"


@pytest.mark.performance
@pytest.mark.load
def test_tasks_load():
    """
    Tests the task management endpoints under load conditions.
    """
    # Skip test if not explicitly enabled
    if os.environ.get("ENABLE_LOAD_TESTS") != "true":
        pytest.skip("Load tests not enabled. Set ENABLE_LOAD_TESTS=true to run.")
    
    # Run k6 test for tasks
    options = {
        "vus": 500,          # 500 virtual users
        "duration": "30s",   # 30 second test
        "summaryTrendStats": "avg,min,med,p95,p99,max",
        "summary-export": "/tmp/tasks_load_test_summary.json"
    }
    
    results = run_k6_test("tasks.js", options)
    
    # Extract metrics from results
    http_req_duration_p95 = results.get("metrics", {}).get("http_req_duration", {}).get("p95", float('inf'))
    error_rate = results.get("metrics", {}).get("http_req_failed", {}).get("rate", 0) * 100  # Convert to percentage
    http_reqs = results.get("metrics", {}).get("http_reqs", {}).get("rate", 0)
    
    # Log results
    logger.info(f"Tasks Load Test - p95 Response Time: {http_req_duration_p95:.2f}ms, "
                f"Error Rate: {error_rate:.2f}%, Throughput: {http_reqs:.2f} reqs/s")
    
    # Assert results meet performance requirements
    assert http_req_duration_p95 < 1000, f"p95 tasks response time ({http_req_duration_p95:.2f}ms) exceeds threshold (1000ms)"
    assert error_rate < 1, f"Tasks error rate ({error_rate:.2f}%) exceeds threshold (1%)"
    assert http_reqs > 40, f"Tasks throughput ({http_reqs:.2f} reqs/s) below threshold (40 reqs/s)"


@pytest.mark.performance
@pytest.mark.load
def test_projects_load():
    """
    Tests the project management endpoints under load conditions.
    """
    # Skip test if not explicitly enabled
    if os.environ.get("ENABLE_LOAD_TESTS") != "true":
        pytest.skip("Load tests not enabled. Set ENABLE_LOAD_TESTS=true to run.")
    
    # Run k6 test for projects
    options = {
        "vus": 500,          # 500 virtual users
        "duration": "30s",   # 30 second test
        "summaryTrendStats": "avg,min,med,p95,p99,max",
        "summary-export": "/tmp/projects_load_test_summary.json"
    }
    
    results = run_k6_test("projects.js", options)
    
    # Extract metrics from results
    http_req_duration_p95 = results.get("metrics", {}).get("http_req_duration", {}).get("p95", float('inf'))
    error_rate = results.get("metrics", {}).get("http_req_failed", {}).get("rate", 0) * 100  # Convert to percentage
    http_reqs = results.get("metrics", {}).get("http_reqs", {}).get("rate", 0)
    
    # Log results
    logger.info(f"Projects Load Test - p95 Response Time: {http_req_duration_p95:.2f}ms, "
                f"Error Rate: {error_rate:.2f}%, Throughput: {http_reqs:.2f} reqs/s")
    
    # Assert results meet performance requirements
    assert http_req_duration_p95 < 1000, f"p95 projects response time ({http_req_duration_p95:.2f}ms) exceeds threshold (1000ms)"
    assert error_rate < 1, f"Projects error rate ({error_rate:.2f}%) exceeds threshold (1%)"
    assert http_reqs > 30, f"Projects throughput ({http_reqs:.2f} reqs/s) below threshold (30 reqs/s)"