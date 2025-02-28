"""
This module defines constants and configurations for performance testing the Task Management System.
These values are derived from the SLA requirements specified in the technical documentation and should
be used as the source of truth for all performance tests.
"""

# API response time and error rate thresholds
API_PERFORMANCE_THRESHOLDS = {
    'RESPONSE_TIME_P95_MS': 200,  # 95% of requests should complete in less than 200ms
    'RESPONSE_TIME_P99_MS': 1000,  # 99% of requests should complete in less than 1000ms
    'ERROR_RATE_PERCENT': 0.1,  # Error rate should be less than 0.1%
}

# Page load time thresholds
PAGE_PERFORMANCE_THRESHOLDS = {
    'LOAD_TIME_P90_MS': 2000,  # 90% of pages should load in less than 2 seconds
    'LOAD_TIME_P99_MS': 5000,  # 99% of pages should load in less than 5 seconds
}

# Database query performance thresholds
DATABASE_PERFORMANCE_THRESHOLDS = {
    'QUERY_TIME_P95_MS': 50,  # 95% of database queries should complete in less than 50ms
    'QUERY_TIME_P99_MS': 200,  # 99% of database queries should complete in less than 200ms
}

# End-to-end task flow performance thresholds
TASK_FLOW_THRESHOLDS = {
    'CREATION_TIME_MS': 1500,  # Task creation flow should complete in less than 1.5 seconds
    'CRITICAL_TIME_MS': 3000,  # Critical task operations should complete in less than 3 seconds
}

# Load test scenarios with user counts and duration
LOAD_TEST_SCENARIOS = {
    'NORMAL_LOAD': {
        'USERS': 500,  # Simulate 500 concurrent users
        'DURATION_SECONDS': 300,  # Run for 5 minutes
        'RAMP_UP_SECONDS': 60,  # Ramp up over 1 minute
        'SUCCESS_CRITERIA': 'Response time < 1s for 95% of requests'
    },
    'STRESS_TEST': {
        'USERS': 2000,  # Simulate 2000 concurrent users
        'DURATION_SECONDS': 600,  # Run for 10 minutes
        'RAMP_UP_SECONDS': 300,  # Ramp up over 5 minutes
        'SUCCESS_CRITERIA': 'System remains stable and recovers after load reduction'
    },
    'ENDURANCE_TEST': {
        'USERS': 300,  # Simulate 300 concurrent users
        'DURATION_SECONDS': 86400,  # Run for 24 hours
        'SUCCESS_CRITERIA': 'No memory leaks, response time degradation < 20%'
    }
}