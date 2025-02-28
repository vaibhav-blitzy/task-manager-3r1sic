"""
Common logging package for the Task Management System.

This package provides a standardized interface for structured JSON logging,
correlation ID tracking for distributed tracing, and PII data redaction.
"""

from .logger import (
    LogLevel,
    configure_logger,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    redact_pii,
    add_request_context_to_logs,
    JsonFormatter
)

# Create a default logger instance for direct import
logger = get_logger('app')

# Export all public components
__all__ = [
    'LogLevel',
    'configure_logger',
    'get_logger',
    'set_correlation_id',
    'get_correlation_id',
    'redact_pii',
    'add_request_context_to_logs',
    'JsonFormatter',
    'logger'
]