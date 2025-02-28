import pytest  # pytest-7.4.x
from unittest import mock  # Standard Library
from bson import ObjectId  # pymongo-4.x
from flask import Flask  # flask==2.x
from datetime import datetime  # Standard Library

# Internal imports
from src.backend.services.analytics.tests import conftest  # For shared test fixtures and configurations
from src.backend.services.analytics import app  # The Flask application instance to be tested
from src.backend.services.analytics.services import dashboard_service  # For mocking dashboard service functions in tests
from src.backend.services.analytics.services import metrics_service  # For mocking metrics service functions in tests
from src.backend.services.analytics.services import report_service  # For mocking report service functions in tests
from src.backend.services.analytics.models.dashboard import Dashboard  # Dashboard model for creating test data
from src.backend.services.analytics.models.report import Report  # Report model for creating test data
from src.backend.common.testing import fixtures  # Common test fixtures for all services
from src.backend.common.testing import mocks  # Common mock objects and functions for testing
from src.backend.common.exceptions import api_exceptions  # Custom API exceptions for testing error scenarios


@pytest.mark.usefixtures('auth_header')
def test_get_dashboards(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving all dashboards with proper filtering and pagination"""
    # Mock dashboard_service.get_dashboards to return test dashboards
    mock_dashboards = [
        {"id": "1", "name": "Dashboard 1", "type": "personal"},
        {"id": "2", "name": "Dashboard 2", "type": "project"}
    ]
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.get_dashboards', return_value={
        "dashboards": mock_dashboards,
        "pagination": {"page": 1, "per_page": 2, "total_count": 2, "total_pages": 1}
    })

    # Make GET request to /api/dashboards endpoint with test filters
    response = client.get("/api/dashboards?type=personal&page=1&per_page=2")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected dashboard data
    data = response.get_json()
    assert len(data["dashboards"]) == 2
    assert data["dashboards"][0]["name"] == "Dashboard 1"
    assert data["dashboards"][1]["type"] == "project"

    # Assert pagination metadata is correct
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2
    assert data["pagination"]["total_count"] == 2
    assert data["pagination"]["total_pages"] == 1


@pytest.mark.usefixtures('auth_header')
def test_get_dashboard_by_id(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving a specific dashboard by ID"""
    # Create a test dashboard ID
    dashboard_id = "test_dashboard_id"

    # Mock dashboard_service.get_dashboard_by_id to return a test dashboard
    mock_dashboard = {"id": dashboard_id, "name": "Test Dashboard", "type": "personal"}
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.get_dashboard_by_id', return_value=mock_dashboard)

    # Make GET request to /api/dashboards/{id} endpoint
    response = client.get(f"/api/dashboards/{dashboard_id}")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected dashboard
    data = response.get_json()
    assert data["id"] == dashboard_id
    assert data["name"] == "Test Dashboard"


@pytest.mark.usefixtures('auth_header')
def test_create_dashboard(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test creating a new dashboard"""
    # Create test dashboard data
    dashboard_data = {"name": "New Dashboard", "type": "personal"}

    # Mock dashboard_service.create_dashboard to return a new dashboard with ID
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.create_dashboard', return_value={"id": "new_dashboard_id"})

    # Make POST request to /api/dashboards endpoint with test data
    response = client.post("/api/dashboards", json=dashboard_data)

    # Assert response status code is 201
    assert response.status_code == 201

    # Assert response contains the created dashboard ID
    data = response.get_json()
    assert data["id"] == "new_dashboard_id"

    # Assert service function was called with correct data
    # (Implementation depends on how you mock the service function)


@pytest.mark.usefixtures('auth_header')
def test_update_dashboard(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test updating an existing dashboard"""
    # Create a test dashboard ID
    dashboard_id = "test_dashboard_id"

    # Create test update data
    update_data = {"name": "Updated Dashboard", "description": "Updated description"}

    # Mock dashboard_service.update_dashboard to return updated dashboard
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.update_dashboard', return_value={"id": dashboard_id, "name": "Updated Dashboard", "description": "Updated description"})

    # Make PUT request to /api/dashboards/{id} endpoint with update data
    response = client.put(f"/api/dashboards/{dashboard_id}", json=update_data)

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected updated dashboard
    data = response.get_json()
    assert data["id"] == dashboard_id
    assert data["name"] == "Updated Dashboard"
    assert data["description"] == "Updated description"

    # Assert service function was called with correct ID and data
    # (Implementation depends on how you mock the service function)


@pytest.mark.usefixtures('auth_header')
def test_delete_dashboard(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test deleting a dashboard"""
    # Create a test dashboard ID
    dashboard_id = "test_dashboard_id"

    # Mock dashboard_service.delete_dashboard to return success
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.delete_dashboard', return_value=True)

    # Make DELETE request to /api/dashboards/{id} endpoint
    response = client.delete(f"/api/dashboards/{dashboard_id}")

    # Assert response status code is 204
    assert response.status_code == 200

    # Assert service function was called with correct ID
    # (Implementation depends on how you mock the service function)


@pytest.mark.usefixtures('auth_header')
def test_get_dashboard_not_found(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test dashboard retrieval when it doesn't exist"""
    # Create a test dashboard ID
    dashboard_id = "nonexistent_dashboard_id"

    # Mock dashboard_service.get_dashboard_by_id to raise a not found exception
    mocker.patch('src.backend.services.analytics.services.dashboard_service.DashboardService.get_dashboard_by_id', side_effect=api_exceptions.NotFoundError)

    # Make GET request to /api/dashboards/{id} endpoint
    response = client.get(f"/api/dashboards/{dashboard_id}")

    # Assert response status code is 404
    assert response.status_code == 404

    # Assert error message in response
    data = response.get_json()
    assert data["message"] == "Resource not found"


@pytest.mark.usefixtures('auth_header')
def test_get_metrics(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving analytics metrics with filters"""
    # Mock metrics_service.get_metrics to return test metrics
    mock_metrics = {"metric1": 100, "metric2": 200}
    mocker.patch('src.backend.services.analytics.services.metrics_service.MetricsService.get_metrics', return_value=mock_metrics)

    # Make GET request to /api/metrics endpoint with test filters
    response = client.get("/api/metrics?filter1=value1&filter2=value2")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected metrics data
    data = response.get_json()
    assert data == mock_metrics


@pytest.mark.usefixtures('auth_header')
def test_get_specific_metric(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving a specific metric by name"""
    # Create a test metric name
    metric_name = "test_metric"

    # Mock metrics_service.get_metric_by_name to return test metric data
    mock_metric_data = {"value": 42, "timestamp": "2024-01-01"}
    mocker.patch('src.backend.services.analytics.services.metrics_service.MetricsService.get_metric_by_name', return_value=mock_metric_data)

    # Make GET request to /api/metrics/{metric_name} endpoint
    response = client.get(f"/api/metrics/{metric_name}")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected metric data
    data = response.get_json()
    assert data == mock_metric_data


@pytest.mark.usefixtures('auth_header')
def test_get_reports(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving all reports with proper filtering and pagination"""
    # Mock report_service.get_reports to return test reports
    mock_reports = [
        {"id": "1", "name": "Report 1", "type": "task_status"},
        {"id": "2", "name": "Report 2", "type": "project_summary"}
    ]
    mocker.patch('src.backend.services.analytics.services.report_service.ReportService.get_reports', return_value={
        "reports": mock_reports,
        "pagination": {"page": 1, "per_page": 2, "total_count": 2, "total_pages": 1}
    })

    # Make GET request to /api/reports endpoint with test filters
    response = client.get("/api/reports?type=task_status&page=1&per_page=2")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected report data
    data = response.get_json()
    assert len(data["reports"]) == 2
    assert data["reports"][0]["name"] == "Report 1"
    assert data["reports"][1]["type"] == "project_summary"

    # Assert pagination metadata is correct
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2
    assert data["pagination"]["total_count"] == 2
    assert data["pagination"]["total_pages"] == 1


@pytest.mark.usefixtures('auth_header')
def test_generate_report(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test generating a new report"""
    # Create test report parameters
    report_parameters = {"project_id": "test_project_id", "date_range": "2024-01-01:2024-01-31"}

    # Mock report_service.generate_report to return a report result
    mock_report_result = {"id": "new_report_id", "name": "Generated Report"}
    mocker.patch('src.backend.services.analytics.services.report_service.ReportService.generate_report', return_value=mock_report_result)

    # Make POST request to /api/reports/generate endpoint with test parameters
    response = client.post("/api/reports/generate", json=report_parameters)

    # Assert response status code is 200
    assert response.status_code == 201

    # Assert response data contains expected report data
    data = response.get_json()
    assert data["id"] == "new_report_id"
    assert data["name"] == "Generated Report"

    # Assert service function was called with correct parameters
    # (Implementation depends on how you mock the service function)


@pytest.mark.usefixtures('auth_header')
def test_invalid_dashboard_data(client: Flask.test_client_class):
    """Test validation errors when creating dashboard with invalid data"""
    # Create invalid dashboard data (missing required fields)
    invalid_dashboard_data = {"description": "Invalid dashboard"}

    # Make POST request to /api/dashboards endpoint with invalid data
    response = client.post("/api/dashboards", json=invalid_dashboard_data)

    # Assert response status code is 400
    assert response.status_code == 400

    # Assert error messages in response corresponding to validation failures
    data = response.get_json()
    assert data["message"] == "Dashboard name is required"


@pytest.mark.usefixtures('auth_header')
def test_get_scheduled_reports(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test retrieving scheduled reports"""
    # Mock report_service.get_scheduled_reports to return test scheduled reports
    mock_scheduled_reports = [
        {"id": "1", "name": "Scheduled Report 1", "schedule": {"frequency": "daily"}},
        {"id": "2", "name": "Scheduled Report 2", "schedule": {"frequency": "weekly"}}
    ]
    mocker.patch('src.backend.services.analytics.services.report_service.ReportService.list_scheduled_reports', return_value={
        "reports": mock_scheduled_reports,
        "pagination": {"page": 1, "per_page": 2, "total_count": 2, "total_pages": 1}
    })

    # Make GET request to /api/reports/scheduled endpoint
    response = client.get("/api/reports/scheduled")

    # Assert response status code is 200
    assert response.status_code == 200

    # Assert response data matches expected scheduled reports
    data = response.get_json()
    assert len(data["reports"]) == 2
    assert data["reports"][0]["name"] == "Scheduled Report 1"
    assert data["reports"][1]["schedule"]["frequency"] == "weekly"


@pytest.mark.usefixtures('auth_header')
def test_schedule_report(client: Flask.test_client_class, mocker: pytest.fixture):
    """Test scheduling a report for periodic generation"""
    # Create test schedule parameters
    schedule_parameters = {"template_id": "test_template_id", "schedule": {"frequency": "daily"}}

    # Mock report_service.schedule_report to return a scheduled report info
    mock_scheduled_report = {"id": "new_scheduled_report_id", "schedule": {"frequency": "daily"}}
    mocker.patch('src.backend.services.analytics.services.report_service.ReportService.schedule_report', return_value=mock_scheduled_report)

    # Make POST request to /api/reports/scheduled endpoint with test parameters
    response = client.post("/api/reports/scheduled", json=schedule_parameters)

    # Assert response status code is 201
    assert response.status_code == 201

    # Assert response data contains expected schedule ID and details
    data = response.get_json()
    assert data["id"] == "new_scheduled_report_id"
    assert data["schedule"]["frequency"] == "daily"

    # Assert service function was called with correct parameters
    # (Implementation depends on how you mock the service function)


def test_unauthorized_access(client: Flask.test_client_class):
    """Test API endpoints reject requests without authentication"""
    # Make GET request to /api/dashboards without auth header
    response = client.get("/api/dashboards")

    # Assert response status code is 401
    assert response.status_code == 401

    # Make GET request to /api/metrics without auth header
    response = client.get("/api/metrics")

    # Assert response status code is 401
    assert response.status_code == 401

    # Make GET request to /api/reports without auth header
    response = client.get("/api/reports")

    # Assert response status code is 401
    assert response.status_code == 401