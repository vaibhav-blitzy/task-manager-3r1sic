"""
Utility module providing standardized date and time handling functions for the Task Management System.

This module centralizes datetime operations, formatting, timezone conversions, and relative time 
calculations essential for task due dates, project timelines, and notification scheduling.
"""

from datetime import datetime, timedelta, time
import pytz  # version 2023.3
from typing import Optional, Tuple, Union, Dict, Any
import dateutil.parser  # python-dateutil 2.8.2
from dateutil.relativedelta import relativedelta  # python-dateutil 2.8.2

# Standard ISO 8601 format with milliseconds and Z suffix for UTC
ISO_DATE_FORMAT = "YYYY-MM-DDTHH:mm:ss.sssZ"

# Default timezone for the application
DEFAULT_TIMEZONE = "UTC"

# Dictionary of predefined date format strings
DATE_FORMATS: Dict[str, str] = {
    "short_date": "%m/%d/%Y",
    "long_date": "%B %d, %Y",
    "short_datetime": "%m/%d/%Y %H:%M",
    "long_datetime": "%B %d, %Y %H:%M:%S",
    "time_only": "%H:%M:%S"
}


def now() -> datetime:
    """
    Returns the current UTC datetime with tzinfo.
    
    Returns:
        datetime: Current UTC datetime with timezone information
    """
    return datetime.now(pytz.UTC)


def to_iso_format(dt: Optional[datetime]) -> str:
    """
    Converts a datetime object to ISO 8601 format string.
    
    Args:
        dt: The datetime object to format (will be converted to UTC if timezone-aware)
             If None is provided, current UTC time is used
    
    Returns:
        str: ISO 8601 formatted datetime string
    """
    if dt is None:
        dt = now()
    
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)
    
    # Format to ISO 8601 with Z suffix
    return dt.isoformat().replace('+00:00', 'Z')


def from_iso_format(iso_string: str) -> Optional[datetime]:
    """
    Parses an ISO 8601 formatted string into a datetime object.
    
    Args:
        iso_string: ISO 8601 formatted string to parse
    
    Returns:
        datetime: Parsed datetime object with UTC timezone
        None: If parsing fails
    """
    if not iso_string:
        return None
    
    try:
        dt = dateutil.parser.isoparse(iso_string)
        
        # Ensure the datetime is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        elif dt.tzinfo != pytz.UTC:
            dt = dt.astimezone(pytz.UTC)
            
        return dt
    except (ValueError, TypeError) as e:
        # Log the error here if a logging system is in place
        return None


def format_date(dt: Optional[datetime], format_key: str) -> str:
    """
    Formats a datetime object using predefined or custom format strings.
    
    Args:
        dt: The datetime object to format
            If None is provided, current UTC time is used
        format_key: Either a key in the DATE_FORMATS dictionary or a direct format string
    
    Returns:
        str: Formatted date string
    """
    if dt is None:
        dt = now()
    
    # Get the format string from DATE_FORMATS or use format_key directly
    format_string = DATE_FORMATS.get(format_key, format_key)
    
    try:
        return dt.strftime(format_string)
    except (ValueError, TypeError) as e:
        # Log the error here if a logging system is in place
        return str(dt)


def parse_date(date_string: str, format_string: Optional[str] = None) -> Optional[datetime]:
    """
    Parses a date string with flexible format detection.
    
    Args:
        date_string: The date string to parse
        format_string: Optional format string to use for parsing
                      If None, flexible parsing with dateutil is used
    
    Returns:
        datetime: Parsed datetime object with UTC timezone
        None: If parsing fails
    """
    if not date_string:
        return None
    
    try:
        if format_string:
            # Try to parse with the specified format
            dt = datetime.strptime(date_string, format_string)
        else:
            # Use dateutil for flexible parsing
            dt = dateutil.parser.parse(date_string)
        
        # Ensure the datetime is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
            
        return dt
    except (ValueError, TypeError) as e:
        # Log the error here if a logging system is in place
        return None


def is_overdue(dt: Optional[datetime]) -> bool:
    """
    Checks if a datetime is in the past compared to current time.
    
    Args:
        dt: The datetime to check
    
    Returns:
        bool: True if datetime is in the past, False otherwise or if dt is None
    """
    if dt is None:
        return False
    
    current_time = now()
    
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)
    
    return dt < current_time


def is_due_soon(dt: Optional[datetime], hours: int = 24) -> bool:
    """
    Checks if a datetime is approaching within specified hours.
    
    Args:
        dt: The datetime to check
        hours: Number of hours to consider as "soon"
    
    Returns:
        bool: True if datetime is within the specified hours and not overdue,
              False otherwise or if dt is None
    """
    if dt is None:
        return False
    
    current_time = now()
    
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)
    
    # Calculate threshold
    threshold = current_time + timedelta(hours=hours)
    
    # Due soon if it's in the future but within the threshold
    return current_time <= dt <= threshold


def convert_timezone(dt: datetime, timezone: str) -> Optional[datetime]:
    """
    Converts a datetime object to the specified timezone.
    
    Args:
        dt: The datetime object to convert
        timezone: The timezone name to convert to (e.g., 'US/Pacific', 'Europe/London')
    
    Returns:
        datetime: Datetime object in the new timezone
        None: If conversion fails
    """
    if dt is None:
        return None
    
    try:
        # Ensure the datetime is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        # Get the target timezone
        target_tz = pytz.timezone(timezone)
        
        # Convert to the target timezone
        return dt.astimezone(target_tz)
    except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
        # Log the error here if a logging system is in place
        return dt


def get_date_range(range_type: str, reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Generates a tuple of start and end datetime objects for a specified range.
    
    Args:
        range_type: Type of range ('day', 'week', 'month', 'quarter', 'year')
        reference_date: Reference date to calculate range from
                       If None, current date is used
    
    Returns:
        tuple: (start_date, end_date) for the range
        
    Raises:
        ValueError: If invalid range_type is provided
    """
    if reference_date is None:
        reference_date = now()
    
    # Ensure the datetime is timezone-aware
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.UTC)
    
    if range_type == 'day':
        start_date = get_start_of_day(reference_date)
        end_date = get_end_of_day(reference_date)
    
    elif range_type == 'week':
        # Get the start of the week (Monday)
        start_date = reference_date - timedelta(days=reference_date.weekday())
        start_date = get_start_of_day(start_date)
        
        # End of the week (Sunday)
        end_date = start_date + timedelta(days=6)
        end_date = get_end_of_day(end_date)
    
    elif range_type == 'month':
        # Start of month
        start_date = reference_date.replace(day=1)
        start_date = get_start_of_day(start_date)
        
        # End of month
        if reference_date.month == 12:
            next_month = reference_date.replace(year=reference_date.year + 1, month=1)
        else:
            next_month = reference_date.replace(month=reference_date.month + 1)
            
        end_date = next_month.replace(day=1) - timedelta(days=1)
        end_date = get_end_of_day(end_date)
    
    elif range_type == 'quarter':
        # Determine current quarter
        quarter = (reference_date.month - 1) // 3 + 1
        
        # Start of quarter
        quarter_month = 3 * (quarter - 1) + 1
        start_date = reference_date.replace(month=quarter_month, day=1)
        start_date = get_start_of_day(start_date)
        
        # End of quarter
        if quarter == 4:
            end_quarter = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
        else:
            end_quarter = reference_date.replace(month=quarter_month + 3, day=1)
            
        end_date = end_quarter - timedelta(days=1)
        end_date = get_end_of_day(end_date)
    
    elif range_type == 'year':
        # Start of year
        start_date = reference_date.replace(month=1, day=1)
        start_date = get_start_of_day(start_date)
        
        # End of year
        end_date = reference_date.replace(month=12, day=31)
        end_date = get_end_of_day(end_date)
    
    else:
        raise ValueError(f"Invalid range_type: {range_type}. "
                         f"Valid options are 'day', 'week', 'month', 'quarter', 'year'.")
    
    return (start_date, end_date)


def calculate_duration(start_date: datetime, end_date: Optional[datetime] = None, unit: str = 'seconds') -> float:
    """
    Calculates the duration between two datetimes in the specified unit.
    
    Args:
        start_date: Start datetime
        end_date: End datetime (if None, current time is used)
        unit: Unit for the result ('seconds', 'minutes', 'hours', 'days')
    
    Returns:
        float: Duration in the specified unit
        
    Raises:
        ValueError: If invalid unit is provided
    """
    if start_date is None:
        return 0.0
    
    if end_date is None:
        end_date = now()
    
    # Ensure both datetimes are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=pytz.UTC)
    elif start_date.tzinfo != pytz.UTC:
        start_date = start_date.astimezone(pytz.UTC)
        
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=pytz.UTC)
    elif end_date.tzinfo != pytz.UTC:
        end_date = end_date.astimezone(pytz.UTC)
    
    # Calculate the time difference
    delta = end_date - start_date
    
    # Convert to the specified unit
    if unit == 'seconds':
        return delta.total_seconds()
    elif unit == 'minutes':
        return delta.total_seconds() / 60
    elif unit == 'hours':
        return delta.total_seconds() / 3600
    elif unit == 'days':
        return delta.total_seconds() / 86400
    else:
        raise ValueError(f"Invalid unit: {unit}. "
                         f"Valid options are 'seconds', 'minutes', 'hours', 'days'.")


def get_relative_date(amount: int, unit: str, reference_date: Optional[datetime] = None) -> datetime:
    """
    Calculates a date relative to a reference date based on the specified unit and amount.
    
    Args:
        amount: Amount to add/subtract (positive for future, negative for past)
        unit: Unit for the calculation ('days', 'weeks', 'months', 'years')
        reference_date: Reference date (if None, current time is used)
    
    Returns:
        datetime: Calculated relative date
        
    Raises:
        ValueError: If invalid unit is provided
    """
    if reference_date is None:
        reference_date = now()
    
    # Ensure the datetime is timezone-aware
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=pytz.UTC)
    
    if unit == 'days':
        delta = relativedelta(days=amount)
    elif unit == 'weeks':
        delta = relativedelta(weeks=amount)
    elif unit == 'months':
        delta = relativedelta(months=amount)
    elif unit == 'years':
        delta = relativedelta(years=amount)
    else:
        raise ValueError(f"Invalid unit: {unit}. "
                         f"Valid options are 'days', 'weeks', 'months', 'years'.")
    
    return reference_date + delta


def get_start_of_day(dt: Optional[datetime] = None) -> datetime:
    """
    Gets the datetime representing the start of the day (00:00:00).
    
    Args:
        dt: The datetime to get the start of day for
            If None, current UTC time is used
    
    Returns:
        datetime: Datetime at start of day with the same timezone as the input
    """
    if dt is None:
        dt = now()
    
    # Preserve timezone information
    timezone_info = dt.tzinfo if dt.tzinfo else pytz.UTC
    
    # Set time to 00:00:00
    return dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone_info)


def get_end_of_day(dt: Optional[datetime] = None) -> datetime:
    """
    Gets the datetime representing the end of the day (23:59:59.999999).
    
    Args:
        dt: The datetime to get the end of day for
            If None, current UTC time is used
    
    Returns:
        datetime: Datetime at end of day with the same timezone as the input
    """
    if dt is None:
        dt = now()
    
    # Preserve timezone information
    timezone_info = dt.tzinfo if dt.tzinfo else pytz.UTC
    
    # Set time to 23:59:59.999999
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone_info)