"""
Python package initialization file for the integration tests directory.
This module provides a base class and common imports for integration tests
that verify interactions between components through API calls and database operations.
"""

import pytest
from ..conftest import app_client, db_connection
from ...common.testing.mocks import mock_auth_service

__all__ = ['IntegrationTest']

class IntegrationTest:
    """
    Base class for all integration tests providing common setup and teardown functionality.
    This class handles environment initialization, database connections, and test data cleanup.
    """
    
    def __init__(self):
        """
        Initializes the integration test with common properties for API testing.
        """
        # Set default API URL to localhost test server
        self.app_url = "http://localhost:5000/api/v1"
        
        # Set default request headers including content-type and accept
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @classmethod
    def setup_class(cls):
        """
        Class method for setting up test environment before any tests run.
        Initializes database connections and configures mock services.
        
        Args:
            cls: The test class
        """
        # Initialize database connection
        cls.db = db_connection()
        
        # Set up necessary test data
        # This will be extended by subclasses as needed
        
        # Configure mock services if needed
        cls.auth_service = mock_auth_service()
    
    @classmethod
    def teardown_class(cls):
        """
        Class method for cleaning up test environment after all tests have run.
        Removes test data and closes database connections.
        
        Args:
            cls: The test class
        """
        # Clean up test data
        if hasattr(cls, 'db'):
            # Removal of test data would go here
            # This will be extended by subclasses as needed
            pass
        
        # Close database connections
        if hasattr(cls, 'db'):
            # No explicit close needed for mongomock, but kept for real DB compatibility
            pass
        
        # Reset any mock services
        if hasattr(cls, 'auth_service'):
            cls.auth_service.reset_mock()