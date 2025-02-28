"""
Initialization module for the analytics services package that exposes the core service classes and utilities for dashboard, metrics, and report functionality.
"""

# Internal imports
from .dashboard_service import DashboardService  # Import dashboard service for public exposure
from .metrics_service import MetricsService  # Import metrics service for public exposure
from .metrics_service import get_task_completion_rate  # Import common metric function for direct access
from .metrics_service import get_on_time_completion_rate  # Import common metric function for direct access
from .metrics_service import get_task_status_distribution  # Import common metric function for direct access
from .metrics_service import get_workload_distribution  # Import common metric function for direct access
from .report_service import ReportService  # Import report service for public exposure
from .report_service import schedule_due_reports  # Import schedule function for background tasks

__all__ = [
    "DashboardService",  # Service for dashboard management operations
    "MetricsService",  # Service for analytics metrics calculations
    "ReportService",  # Service for report generation and management
    "get_task_completion_rate",  # Direct access to task completion metrics
    "get_on_time_completion_rate",  # Direct access to on-time completion metrics
    "get_task_status_distribution",  # Direct access to task status distribution
    "get_workload_distribution",  # Direct access to workload distribution metrics
    "schedule_due_reports"  # Background task function for scheduled reports
]