"""
Initializes the analytics service package, exposing key models, services, and APIs
for dashboard and reporting functionality in the Task Management System.
"""

import logging  # standard library
from src.backend.common.logging.logger import setup_logger  # internal
from .models.dashboard import Dashboard  # internal
from .models.report import Report  # internal
from .services.dashboard_service import DashboardService  # internal
from .services.report_service import ReportService  # internal
from .services.metrics_service import MetricsService  # internal

# Set up module logger
logger: logging.Logger = setup_logger('analytics')

# Define the version of the analytics service
__version__ = "1.0.0"

# Expose key components for use in other modules
__all__ = [
    "Dashboard",  # Expose Dashboard model for creating and managing dashboard configurations
    "Report",  # Expose Report model for report definition and scheduling
    "DashboardService",  # Expose DashboardService for dashboard CRUD operations
    "ReportService",  # Expose ReportService for report generation and scheduling
    "MetricsService",  # Expose MetricsService for calculating and retrieving performance metrics
    "logger"  # Expose logger for consistent logging throughout the analytics service
]