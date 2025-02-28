import pytest  # pytest-7.4.x
from unittest.mock import Mock  # Standard Library
import mongomock  # mongomock-4.1.x
import fakeredis  # fakeredis-2.x
from pytest_flask import FixtureRequest  # pytest-flask-1.2.x
from freezegun import freeze_time  # freezegun-1.2.x

# Internal imports
from src.backend.services.analytics.app import create_app  # Import the Flask application
from src.backend.common.database.mongo.connection import mongodb_connection  # Import MongoDB connection
from src.backend.common.database.redis.connection import redis_connection  # Import Redis connection
from src.backend.services.analytics.models.dashboard import Dashboard  # Import Dashboard model
from src.backend.services.analytics.models.report import Report  # Import Report model
from src.backend.services.analytics.services.dashboard_service import DashboardService  # Import DashboardService
from src.backend.services.analytics.services.metrics_service import MetricsService  # Import MetricsService
from src.backend.services.analytics.services.report_service import ReportService  # Import ReportService
from src.backend.services.task.services.task_service import TaskService  # Import TaskService
from src.backend.services.project.services.project_service import ProjectService  # Import ProjectService


@pytest.fixture
def mongo_client():
    """Fixture providing a MongoDB client for testing using a mocked client"""
    # Create a mongomock client instance
    client = mongomock.MongoClient()
    # Configure the client for testing
    yield client
    # Clean up after tests


@pytest.fixture
def mongo_db(mongo_client):
    """Fixture providing a MongoDB database for testing"""
    # Get a test database from the mongo_client
    db = mongo_client.db
    # Create necessary collections for analytics (dashboards, reports)
    db.create_collection("dashboards")
    db.create_collection("reports")
    # Yield the database for test usage
    yield db
    # Drop the database after tests
    mongo_client.drop_database('db')


@pytest.fixture
def redis_client():
    """Fixture providing a Redis client for testing using fakeredis"""
    # Create a fakeredis client instance
    client = fakeredis.FakeRedis(decode_responses=True)  # decode_responses for string handling
    # Yield the client for test usage
    yield client
    # Flush all keys after tests
    client.flushall()


@pytest.fixture
def app():
    """Fixture providing the Flask application for testing"""
    # Import the Flask application from the analytics service
    app = create_app()
    # Configure the app for testing with test config values
    app.config.update({
        'TESTING': True,
    })
    # Return the configured app
    return app


@pytest.fixture
def client(app):
    """Fixture providing a Flask test client"""
    # Create a test client using the app fixture
    with app.test_request_context():
        with app.test_client() as client:
            # Configure the client for testing
            yield client


@pytest.fixture
def mock_task_service():
    """Fixture providing a mocked task service for testing analytics with task data"""
    # Create a mock for the TaskService
    task_service_mock = Mock(spec=TaskService)
    # Configure mock methods to return predictable task data
    task_service_mock.get_task.return_value = {"id": "task1", "title": "Test Task"}
    # Yield the mock for test usage
    yield task_service_mock


@pytest.fixture
def mock_project_service():
    """Fixture providing a mocked project service for testing analytics with project data"""
    # Create a mock for the ProjectService
    project_service_mock = Mock(spec=ProjectService)
    # Configure mock methods to return predictable project data
    project_service_mock.get_project.return_value = {"id": "project1", "name": "Test Project"}
    # Yield the mock for test usage
    yield project_service_mock


@pytest.fixture
def dashboard_service(mongo_db, redis_client):
    """Fixture providing a dashboard service for testing"""
    # Create a real DashboardService instance
    dashboard_service = DashboardService()
    # Configure it to use test database and Redis connections
    dashboard_service._dashboard_collection = mongo_db["dashboards"]
    dashboard_service._template_collection = mongo_db["dashboard_templates"]
    # Yield the service for test usage
    yield dashboard_service


@pytest.fixture
def metrics_service(mongo_db, redis_client, mock_task_service, mock_project_service):
    """Fixture providing a metrics service for testing"""
    # Create a real MetricsService instance
    metrics_service = Mock(spec=MetricsService)
    # Configure it to use test database and Redis connections
    # Inject mock task and project services
    # Yield the service for test usage
    yield metrics_service


@pytest.fixture
def report_service(mongo_db, redis_client, metrics_service):
    """Fixture providing a report service for testing"""
    # Create a real ReportService instance
    report_service = ReportService()
    # Configure it to use test database and Redis connections
    report_service.reports_collection = mongo_db["reports"]
    report_service.templates_collection = mongo_db["report_templates"]
    # Inject the metrics service fixture
    report_service.metrics_service = metrics_service
    # Yield the service for test usage
    yield report_service


@pytest.fixture
def sample_dashboard(mongo_db):
    """Fixture providing a sample dashboard for testing"""
    # Create a sample dashboard with predefined configuration
    dashboard_data = {
        "name": "Sample Dashboard",
        "type": "personal",
        "owner": "user123",
        "layout": {"columns": 2},
        "widgets": []
    }
    dashboard = Dashboard.from_dict(dashboard_data)
    # Insert it into the test database
    mongo_db["dashboards"].insert_one(dashboard.to_dict())
    # Return the dashboard instance for test usage
    return dashboard


@pytest.fixture
def sample_report(mongo_db):
    """Fixture providing a sample report for testing"""
    # Create a sample report with predefined configuration
    report_data = {
        "name": "Sample Report",
        "type": "task_status",
        "owner": "user123",
        "parameters": {},
        "filters": {}
    }
    report = Report.from_dict(report_data)
    # Insert it into the test database
    mongo_db["reports"].insert_one(report.to_dict())
    # Return the report instance for test usage
    return report


@pytest.fixture
def sample_task_data():
    """Fixture providing sample task data for testing analytics"""
    # Create a list of sample task dictionaries with various statuses and dates
    task_data = [
        {"title": "Task 1", "status": "completed", "dueDate": "2023-11-01"},
        {"title": "Task 2", "status": "in_progress", "dueDate": "2023-12-15"},
        {"title": "Task 3", "status": "created", "dueDate": "2024-01-01"}
    ]
    # Return the list for test usage
    return task_data


@pytest.fixture
def sample_project_data():
    """Fixture providing sample project data for testing analytics"""
    # Create a list of sample project dictionaries with various statuses and metrics
    project_data = [
        {"name": "Project 1", "status": "completed", "completionRate": 90},
        {"name": "Project 2", "status": "in_progress", "completionRate": 50},
        {"name": "Project 3", "status": "planning", "completionRate": 10}
    ]
    # Return the list for test usage
    return project_data

@pytest.fixture
def frozen_time():
    """Fixture to freeze time for predictable analytics tests"""
    # Use freezegun to freeze time at a specific datetime
    with freeze_time("2024-01-01T00:00:00Z") as ft:
        # Yield the frozen time object
        yield ft
        # Automatically unfreeze time after tests