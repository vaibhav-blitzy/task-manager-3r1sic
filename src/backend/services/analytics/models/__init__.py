"""
Analytics models initialization module.

This module exports the data models and constants for the analytics service,
including dashboards, reports, and templates for the Task Management System.
"""

# Import models from dashboard module
from .dashboard import Dashboard

# Import models and constants from report module
from .report import (
    Report,
    ReportTemplate,
    REPORT_OUTPUT_FORMATS,
    REPORT_TYPES,
    REPORT_FREQUENCIES,
    validate_report_parameters
)

# Define what should be accessible when importing from this package
__all__ = [
    'Dashboard',
    'Report',
    'ReportTemplate',
    'REPORT_OUTPUT_FORMATS',
    'REPORT_TYPES',
    'REPORT_FREQUENCIES',
    'validate_report_parameters'
]