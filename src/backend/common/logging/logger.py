"""
Logging module for the Task Management System.

Provides structured logging with JSON formatting, correlation ID tracking,
and PII data redaction capabilities. Designed to work with various log handlers
and integrates with Flask for request context logging.
"""

import logging
import json
import threading
import typing
from enum import Enum
import datetime
import os
import uuid
import re
import time
from typing import Dict, Optional, Any, Union

import flask
from pythonjsonlogger import jsonlogger  # v2.0.x

from ..config import CONFIG
from ..utils.security import generate_secure_token

# Thread-local storage for correlation IDs
_correlation_id = threading.local()

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Regular expressions for identifying PII patterns in log messages
PII_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "credit_card": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
    "phone": re.compile(r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
}

# Replacement text for redacted PII
PII_REPLACEMENT = "[REDACTED]"


class LogLevel(Enum):
    """
    Enumeration of standard log levels for consistent usage across the application.
    """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def set_correlation_id(correlation_id: Optional[str] = None) -> None:
    """
    Sets the correlation ID in thread-local storage for tracking requests across services.
    
    Args:
        correlation_id: The correlation ID to set. If None, a new ID will be generated.
    """
    if correlation_id is None:
        # Generate a new correlation ID if none is provided
        correlation_id = str(uuid.uuid4())
    
    # Store the correlation ID in thread-local storage
    _correlation_id.id = correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Retrieves the correlation ID from thread-local storage.
    
    Returns:
        The current correlation ID or None if not set.
    """
    return getattr(_correlation_id, 'id', None)


def redact_pii(message: str) -> str:
    """
    Redacts personally identifiable information (PII) from log messages.
    
    Args:
        message: The log message that may contain PII.
        
    Returns:
        The message with PII redacted.
    """
    if message is None or not isinstance(message, str):
        return message
    
    # Iterate through all PII patterns and redact matches
    for pattern_name, pattern in PII_PATTERNS.items():
        message = pattern.sub(PII_REPLACEMENT, message)
    
    return message


class JsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom log formatter that outputs logs in JSON format with consistent structure.
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """
        Initialize the formatter with custom format and date format.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
        """
        if fmt is None:
            fmt = '%(timestamp)s %(name)s %(levelname)s %(message)s'
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record into a JSON string with additional context.
        
        Args:
            record: The log record to format
            
        Returns:
            Formatted JSON log string
        """
        # Get the basic formatted record
        formatted = super().format(record)
        
        try:
            # Parse the log record as JSON
            log_record = json.loads(formatted)
        except json.JSONDecodeError:
            # If parsing fails, create a new dict with the formatted string as message
            log_record = {"message": formatted}
        
        # Add timestamp in ISO 8601 format if not present
        if 'timestamp' not in log_record and hasattr(record, 'created'):
            log_record['timestamp'] = datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).isoformat()
        
        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_record['correlation_id'] = correlation_id
        
        # Add service name and environment
        log_record['service'] = os.environ.get('SERVICE_NAME', 'task-management')
        log_record['environment'] = os.environ.get('FLASK_ENV', 'development')
        
        # Add host/instance information if available
        hostname = os.environ.get('HOSTNAME')
        if hostname:
            log_record['host'] = hostname
        
        # Redact PII from log message
        if 'message' in log_record and isinstance(log_record['message'], str):
            log_record['message'] = redact_pii(log_record['message'])
        
        # Redact PII from exception info if present
        if 'exc_info' in log_record and isinstance(log_record['exc_info'], str):
            log_record['exc_info'] = redact_pii(log_record['exc_info'])
        
        # Return the JSON-formatted log
        return json.dumps(log_record)
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add additional fields to the log record.
        
        Args:
            log_record: The log record dict being built
            record: The original log record
            message_dict: Additional message dict
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['service'] = os.environ.get('SERVICE_NAME', 'task-management')
        log_record['environment'] = os.environ.get('FLASK_ENV', 'development')
        log_record['host'] = os.environ.get('HOSTNAME', 'unknown')
        
        # Add correlation ID if available
        correlation_id = get_correlation_id()
        if correlation_id:
            log_record['correlation_id'] = correlation_id
        
        # Add request context if available
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_record['request_id'] = request_id
        
        user_id = getattr(record, 'user_id', None)
        if user_id:
            log_record['user_id'] = user_id


def configure_logger(name: str, level: Optional[LogLevel] = None, enable_json: bool = True) -> logging.Logger:
    """
    Configures the logging system based on application configuration.
    
    Args:
        name: The logger name
        level: The log level (defaults to INFO if not specified)
        enable_json: Whether to enable JSON formatting
        
    Returns:
        Configured logger instance
    """
    # Get logging configuration with fallback to defaults if not available
    try:
        log_config = CONFIG.LOGGING
    except (AttributeError, ImportError):
        log_config = {
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': 'INFO'
                }
            }
        }
        logging.warning("Could not load logging configuration from CONFIG, using defaults")
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set the log level
    log_level = level.value if level else DEFAULT_LOG_LEVEL
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []
    
    # Configure console handler with appropriate formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_config.get('handlers', {}).get('console', {}).get('level', log_level))
    
    if enable_json:
        # Use JSON formatter for structured logging
        formatter = JsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z'
        )
    else:
        # Use standard formatter for development/debugging
        formatter = logging.Formatter(
            fmt=log_config.get('formatters', {}).get('standard', {}).get(
                'format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            ),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configure file handler if specified in config
    if 'file' in log_config.get('handlers', {}):
        try:
            file_config = log_config['handlers']['file']
            file_handler = logging.FileHandler(file_config.get('filename', f'{name}.log'))
            file_handler.setLevel(file_config.get('level', log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (KeyError, IOError) as e:
            # Log to console if file handler setup fails
            console_handler.setLevel(logging.WARNING)
            logger.warning(f"Failed to set up file logging: {str(e)}")
    
    # Ensure logger doesn't propagate to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str, level: Optional[LogLevel] = None, enable_json: bool = True) -> logging.Logger:
    """
    Factory function to get a configured logger for a specific module.
    
    Args:
        name: The logger name (typically __name__ of the calling module)
        level: The log level (defaults to INFO if not specified)
        enable_json: Whether to enable JSON formatting
        
    Returns:
        Configured logger instance
    """
    return configure_logger(name, level, enable_json)


def add_request_context_to_logs(app: 'flask.Flask') -> None:
    """
    Middleware function to add request context information to log records.
    
    Args:
        app: The Flask application instance
    """
    @app.before_request
    def before_request() -> None:
        # Extract request ID from headers or generate a new one
        request_id = flask.request.headers.get('X-Request-ID')
        if not request_id:
            request_id = generate_secure_token()
        
        # Set the correlation ID for this request
        set_correlation_id(request_id)
        
        # Store the request start time for duration calculation
        flask.g.request_start_time = time.time()
    
    @app.after_request
    def after_request(response: flask.Response) -> flask.Response:
        # Add correlation ID to response headers
        correlation_id = get_correlation_id()
        if correlation_id:
            response.headers['X-Correlation-ID'] = correlation_id
        
        # Calculate request duration
        if hasattr(flask.g, 'request_start_time'):
            duration = time.time() - flask.g.request_start_time
            response.headers['X-Request-Duration'] = f"{duration:.6f}"
        
        return response
    
    @app.teardown_request
    def teardown_request(exception: Optional[Exception] = None) -> None:
        # Clean up thread-local storage to prevent memory leaks
        if hasattr(_correlation_id, 'id'):
            delattr(_correlation_id, 'id')


# Default logger for direct import and use
logger = get_logger('app')