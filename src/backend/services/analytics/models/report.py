"""
MongoDB document models for report and analytics components in the Task Management System.

This module defines the data models for reports, report templates, parameters, schedules,
and execution tracking within the analytics service.
"""

import datetime
from typing import List, Dict, Any, Optional, Union, TypeVar, cast

import bson
from bson import ObjectId

from src.backend.common.database.mongo.models import (
    AuditableDocument, 
    TimestampedDocument,
    str_to_object_id
)
from src.backend.common.database.mongo.connection import get_collection
from src.backend.common.utils.datetime import now, get_next_run_date

# Report types supported by the system
REPORT_TYPES = [
    'task_status',
    'completion_rate',
    'workload_distribution',
    'bottleneck_identification',
    'burndown',
    'performance_metrics',
    'user_productivity',
    'project_health'
]

# Supported output formats for reports
REPORT_OUTPUT_FORMATS = [
    'html',
    'pdf',
    'csv',
    'excel',
    'json'
]

# Supported scheduling frequencies
REPORT_FREQUENCIES = [
    'daily',
    'weekly', 
    'monthly',
    'quarterly'
]

# Report execution statuses
REPORT_STATUSES = [
    'scheduled',
    'running',
    'completed',
    'failed',
    'cancelled'
]


def validate_report_parameters(report_type: str, parameters: List) -> bool:
    """
    Validates that report parameters match the requirements for the specified report type.
    
    Args:
        report_type: Type of report to validate parameters for
        parameters: List of parameter objects to validate
        
    Returns:
        True if parameters are valid for the report type, False otherwise
    """
    if report_type not in REPORT_TYPES:
        return False
    
    # Get required parameters for the report type
    required_params = {
        'task_status': ['project_id', 'date_range'],
        'completion_rate': ['project_id', 'date_range'],
        'workload_distribution': ['team_id'],
        'bottleneck_identification': ['project_id', 'date_range'],
        'burndown': ['project_id', 'sprint_id'],
        'performance_metrics': ['date_range'],
        'user_productivity': ['user_id', 'date_range'],
        'project_health': ['project_id']
    }
    
    param_names = [p.get('name') if isinstance(p, dict) else p.name for p in parameters]
    
    # Check if all required parameters are present
    for req_param in required_params.get(report_type, []):
        if req_param not in param_names:
            return False
    
    # Additional validation could be added here based on parameter types and values
    
    return True


def calculate_next_run(frequency: str, schedule_settings: Dict) -> datetime.datetime:
    """
    Calculates the next run datetime based on frequency and current time.
    
    Args:
        frequency: Scheduling frequency (daily, weekly, monthly, quarterly)
        schedule_settings: Additional schedule settings like day of week, time, etc.
        
    Returns:
        Next scheduled run datetime
    """
    if frequency not in REPORT_FREQUENCIES:
        raise ValueError(f"Invalid frequency: {frequency}. Must be one of {REPORT_FREQUENCIES}")
    
    return get_next_run_date(frequency, schedule_settings)


class ReportParameter:
    """
    Embedded document for report parameters defining data selection and filtering criteria.
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a new ReportParameter.
        
        Args:
            data: Dictionary containing parameter properties
        """
        self.name = data.get('name', '')
        self.type = data.get('type', 'string')
        self.value = data.get('value')
        self.display_name = data.get('display_name', self.name)
        self.description = data.get('description', '')
    
    def to_dict(self) -> Dict:
        """
        Convert parameter to dictionary.
        
        Returns:
            Dictionary representation of parameter
        """
        return {
            'name': self.name,
            'type': self.type,
            'value': self.value,
            'display_name': self.display_name,
            'description': self.description
        }


class ReportSchedule:
    """
    Embedded document for report scheduling configuration.
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a new ReportSchedule.
        
        Args:
            data: Dictionary containing schedule properties
        """
        self.enabled = data.get('enabled', False)
        self.frequency = data.get('frequency')
        self.next_run = data.get('next_run')
        self.settings = data.get('settings', {})
        self.last_run = data.get('last_run')
        
        # Calculate next run if enabled and frequency is set
        if self.enabled and self.frequency and not self.next_run:
            self.next_run = calculate_next_run(self.frequency, self.settings)
    
    def to_dict(self) -> Dict:
        """
        Convert schedule to dictionary.
        
        Returns:
            Dictionary representation of schedule
        """
        return {
            'enabled': self.enabled,
            'frequency': self.frequency,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'settings': self.settings,
            'last_run': self.last_run.isoformat() if self.last_run else None
        }
    
    def update_next_run(self) -> datetime.datetime:
        """
        Updates the next run time based on frequency settings.
        
        Returns:
            Updated next run datetime
        """
        if not self.frequency:
            raise ValueError("Cannot update next run time: frequency not set")
        
        self.next_run = calculate_next_run(self.frequency, self.settings)
        return self.next_run


class ReportDelivery:
    """
    Embedded document for report delivery configuration.
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a new ReportDelivery.
        
        Args:
            data: Dictionary containing delivery properties
        """
        self.email_enabled = data.get('email_enabled', False)
        self.email_recipients = data.get('email_recipients', [])
        self.email_subject_template = data.get('email_subject_template', '')
        self.storage_enabled = data.get('storage_enabled', False)
        self.storage_path = data.get('storage_path', '')
    
    def to_dict(self) -> Dict:
        """
        Convert delivery configuration to dictionary.
        
        Returns:
            Dictionary representation of delivery configuration
        """
        return {
            'email_enabled': self.email_enabled,
            'email_recipients': self.email_recipients,
            'email_subject_template': self.email_subject_template,
            'storage_enabled': self.storage_enabled,
            'storage_path': self.storage_path
        }


class ReportExecution:
    """
    Embedded document for tracking report execution details.
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a new ReportExecution record.
        
        Args:
            data: Dictionary containing execution properties
        """
        self.execution_id = data.get('execution_id', str(ObjectId()))
        self.started_at = data.get('started_at', now())
        self.completed_at = data.get('completed_at')
        self.status = data.get('status', 'running')
        self.output_format = data.get('output_format')
        self.output_url = data.get('output_url')
        self.size_bytes = data.get('size_bytes')
        self.parameters = data.get('parameters', {})
        self.error_message = data.get('error_message')
        self.triggered_by = data.get('triggered_by')
    
    def to_dict(self) -> Dict:
        """
        Convert execution record to dictionary.
        
        Returns:
            Dictionary representation of execution record
        """
        return {
            'execution_id': self.execution_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'output_format': self.output_format,
            'output_url': self.output_url,
            'size_bytes': self.size_bytes,
            'parameters': self.parameters,
            'error_message': self.error_message,
            'triggered_by': self.triggered_by
        }
    
    def complete(self, output_url: str, output_format: str, size_bytes: int) -> None:
        """
        Mark execution as completed with results.
        
        Args:
            output_url: URL or path to the generated report
            output_format: Format of the generated report
            size_bytes: Size of the generated report in bytes
        """
        self.status = 'completed'
        self.completed_at = now()
        self.output_url = output_url
        self.output_format = output_format
        self.size_bytes = size_bytes
    
    def fail(self, error_message: str) -> None:
        """
        Mark execution as failed with error details.
        
        Args:
            error_message: Error message explaining the failure
        """
        self.status = 'failed'
        self.completed_at = now()
        self.error_message = error_message


class Report(TimestampedDocument):
    """
    MongoDB document for report definitions including parameters, scheduling, and execution history.
    """
    
    # Collection configuration
    meta = {
        'collection': 'reports', 
        'indexes': [
            {'fields': ['owner_id']},
            {'fields': ['created_at']},
            {'fields': ['type']}
        ]
    }
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new Report document.
        
        Args:
            data: Dictionary containing report properties
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)
        
        # Initialize lists and dictionaries if not provided
        if 'parameters' not in self._data:
            self._data['parameters'] = []
        
        if 'filters' not in self._data:
            self._data['filters'] = {}
        
        if 'execution_history' not in self._data:
            self._data['execution_history'] = []
        
        # Set default output format if not provided
        if 'output_format' not in self._data:
            self._data['output_format'] = 'pdf'
        
        # Set default is_template flag if not provided
        if 'is_template' not in self._data:
            self._data['is_template'] = False
        
        # Initialize sharing settings if not provided
        if 'sharing' not in self._data:
            self._data['sharing'] = {'public': False, 'shared_with': []}
    
    def validate(self) -> bool:
        """
        Validates the report configuration.
        
        Returns:
            True if report configuration is valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check that name is not empty
        if not self.get('name'):
            raise ValueError("Report name is required")
        
        # Check that type is valid
        report_type = self.get('type')
        if report_type not in REPORT_TYPES:
            raise ValueError(f"Invalid report type: {report_type}")
        
        # Validate parameters
        parameters = self.get('parameters', [])
        if not validate_report_parameters(report_type, parameters):
            raise ValueError(f"Invalid parameters for report type: {report_type}")
        
        # Validate output format
        output_format = self.get('output_format')
        if output_format not in REPORT_OUTPUT_FORMATS:
            raise ValueError(f"Invalid output format: {output_format}")
        
        return True
    
    def set_parameters(self, params: List) -> 'Report':
        """
        Sets the report parameters.
        
        Args:
            params: List of parameter objects or dictionaries
            
        Returns:
            Self for method chaining
        """
        # Convert dictionaries to ReportParameter objects if needed
        parameters = []
        for param in params:
            if isinstance(param, dict):
                parameters.append(ReportParameter(param))
            else:
                parameters.append(param)
        
        # Validate parameters against report type
        if not validate_report_parameters(self.get('type'), parameters):
            raise ValueError(f"Invalid parameters for report type: {self.get('type')}")
        
        # Convert to dictionaries for storage
        self._data['parameters'] = [p.to_dict() for p in parameters]
        
        return self
    
    def set_filters(self, filters_data: Dict) -> 'Report':
        """
        Sets the report filters.
        
        Args:
            filters_data: Dictionary of filter criteria
            
        Returns:
            Self for method chaining
        """
        # Validate filter structure
        if not isinstance(filters_data, dict):
            raise ValueError("Filters must be a dictionary")
        
        self._data['filters'] = filters_data
        
        return self
    
    def set_output_format(self, format: str) -> 'Report':
        """
        Sets the report output format.
        
        Args:
            format: Output format (pdf, csv, excel, html, json)
            
        Returns:
            Self for method chaining
        """
        if format not in REPORT_OUTPUT_FORMATS:
            raise ValueError(f"Invalid output format: {format}. Must be one of {REPORT_OUTPUT_FORMATS}")
        
        self._data['output_format'] = format
        
        return self
    
    def schedule(self, schedule_data: Dict) -> 'Report':
        """
        Configures report scheduling.
        
        Args:
            schedule_data: Dictionary containing schedule configuration
            
        Returns:
            Self for method chaining
        """
        # Create or update ReportSchedule object
        if 'schedule' in self._data and self._data['schedule']:
            # Update existing schedule
            current_schedule = ReportSchedule(self._data['schedule'])
            for key, value in schedule_data.items():
                setattr(current_schedule, key, value)
            schedule = current_schedule
        else:
            # Create new schedule
            schedule = ReportSchedule(schedule_data)
        
        # Validate frequency
        if schedule.frequency and schedule.frequency not in REPORT_FREQUENCIES:
            raise ValueError(f"Invalid frequency: {schedule.frequency}. Must be one of {REPORT_FREQUENCIES}")
        
        # Set next_run if enabled
        if schedule.enabled and schedule.frequency:
            schedule.next_run = calculate_next_run(schedule.frequency, schedule.settings)
        
        # Store schedule data
        self._data['schedule'] = schedule.to_dict()
        
        return self
    
    def cancel_schedule(self) -> 'Report':
        """
        Cancels report scheduling.
        
        Returns:
            Self for method chaining
        """
        if 'schedule' in self._data and self._data['schedule']:
            schedule = ReportSchedule(self._data['schedule'])
            schedule.enabled = False
            schedule.next_run = None
            self._data['schedule'] = schedule.to_dict()
        
        return self
    
    def set_delivery_options(self, delivery_data: Dict) -> 'Report':
        """
        Sets report delivery options.
        
        Args:
            delivery_data: Dictionary containing delivery configuration
            
        Returns:
            Self for method chaining
        """
        # Create or update ReportDelivery object
        if 'delivery' in self._data and self._data['delivery']:
            # Update existing delivery config
            current_delivery = ReportDelivery(self._data['delivery'])
            for key, value in delivery_data.items():
                setattr(current_delivery, key, value)
            delivery = current_delivery
        else:
            # Create new delivery config
            delivery = ReportDelivery(delivery_data)
        
        # Validate email recipients if email delivery enabled
        if delivery.email_enabled and not delivery.email_recipients:
            raise ValueError("Email recipients are required when email delivery is enabled")
        
        # Validate storage path if storage delivery enabled
        if delivery.storage_enabled and not delivery.storage_path:
            raise ValueError("Storage path is required when storage delivery is enabled")
        
        # Store delivery data
        self._data['delivery'] = delivery.to_dict()
        
        return self
    
    def record_execution(self, execution_data: Dict) -> ReportExecution:
        """
        Records a new execution in the report's history.
        
        Args:
            execution_data: Dictionary containing execution details
            
        Returns:
            The created execution record
        """
        # Create new execution record
        execution = ReportExecution(execution_data)
        
        # Add to execution history (limit to last 20)
        execution_history = self._data.get('execution_history', [])
        execution_history.append(execution.to_dict())
        self._data['execution_history'] = execution_history[-20:]
        
        # If this is a scheduled execution, update the schedule.last_run
        if 'schedule' in self._data and self._data['schedule']:
            schedule = ReportSchedule(self._data['schedule'])
            schedule.last_run = execution.started_at
            self._data['schedule'] = schedule.to_dict()
        
        return execution
    
    def update_execution(self, execution_id: str, execution_data: Dict) -> Optional[ReportExecution]:
        """
        Updates an existing execution record.
        
        Args:
            execution_id: ID of the execution to update
            execution_data: Dictionary containing updated execution details
            
        Returns:
            The updated execution record or None if not found
        """
        # Find execution with matching ID
        execution_history = self._data.get('execution_history', [])
        for i, exec_dict in enumerate(execution_history):
            if exec_dict.get('execution_id') == execution_id:
                # Update execution fields
                for key, value in execution_data.items():
                    exec_dict[key] = value
                
                # Update in the history list
                execution_history[i] = exec_dict
                self._data['execution_history'] = execution_history
                
                # Return updated execution object
                return ReportExecution(exec_dict)
        
        return None
    
    def get_execution(self, execution_id: str) -> Optional[ReportExecution]:
        """
        Gets an execution record by ID.
        
        Args:
            execution_id: ID of the execution to retrieve
            
        Returns:
            The execution record or None if not found
        """
        # Find execution with matching ID
        for exec_dict in self._data.get('execution_history', []):
            if exec_dict.get('execution_id') == execution_id:
                return ReportExecution(exec_dict)
        
        return None
    
    def to_dict(self) -> Dict:
        """
        Converts report to dictionary.
        
        Returns:
            Dictionary representation of report
        """
        report_dict = super().to_dict()
        
        # Convert parameters to dictionaries if they aren't already
        parameters = report_dict.get('parameters', [])
        for i, param in enumerate(parameters):
            if not isinstance(param, dict):
                parameters[i] = param.to_dict()
        
        # Convert schedule to dictionary if not already
        if 'schedule' in report_dict and not isinstance(report_dict['schedule'], dict):
            report_dict['schedule'] = report_dict['schedule'].to_dict()
        
        # Convert delivery to dictionary if not already
        if 'delivery' in report_dict and not isinstance(report_dict['delivery'], dict):
            report_dict['delivery'] = report_dict['delivery'].to_dict()
        
        # Ensure execution_history is a list of dictionaries
        if 'execution_history' in report_dict:
            execution_history = report_dict['execution_history']
            for i, exec_item in enumerate(execution_history):
                if not isinstance(exec_item, dict):
                    execution_history[i] = exec_item.to_dict()
        
        return report_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Report':
        """
        Creates a Report instance from dictionary data.
        
        Args:
            data: Dictionary of report data
            
        Returns:
            New Report instance
        """
        # Convert parameters to ReportParameter objects
        if 'parameters' in data:
            parameters = []
            for param_data in data['parameters']:
                parameters.append(ReportParameter(param_data))
            data['parameters'] = [p.to_dict() for p in parameters]
        
        # Convert schedule to ReportSchedule if present
        if 'schedule' in data and data['schedule']:
            data['schedule'] = ReportSchedule(data['schedule']).to_dict()
        
        # Convert delivery to ReportDelivery if present
        if 'delivery' in data and data['delivery']:
            data['delivery'] = ReportDelivery(data['delivery']).to_dict()
        
        # Convert execution_history to ReportExecution objects
        if 'execution_history' in data:
            execution_history = []
            for exec_data in data['execution_history']:
                execution_history.append(ReportExecution(exec_data).to_dict())
            data['execution_history'] = execution_history
        
        # Create new Report instance
        return cls(data)


class ReportTemplate(TimestampedDocument):
    """
    MongoDB document for reusable report templates.
    """
    
    # Collection configuration
    meta = {
        'collection': 'report_templates',
        'indexes': [
            {'fields': ['name']},
            {'fields': ['type']}
        ]
    }
    
    def __init__(self, data: Dict = None, is_new: bool = True):
        """
        Initialize a new ReportTemplate document.
        
        Args:
            data: Dictionary containing template properties
            is_new: Flag indicating if this is a new document
        """
        super().__init__(data, is_new)
        
        # Initialize parameters, default_filters if not provided
        if 'parameters' not in self._data:
            self._data['parameters'] = []
        
        if 'default_filters' not in self._data:
            self._data['default_filters'] = {}
        
        # Set default flags if not provided
        if 'is_system' not in self._data:
            self._data['is_system'] = False
        
        if 'default_output_format' not in self._data:
            self._data['default_output_format'] = 'pdf'
    
    def create_report(self, user: Dict, override_data: Dict = None) -> Report:
        """
        Creates a Report instance from this template.
        
        Args:
            user: User creating the report
            override_data: Optional data to override template defaults
            
        Returns:
            New Report instance based on template
        """
        # Start with template data
        report_data = {
            'name': self.get('name'),
            'description': self.get('description'),
            'type': self.get('type'),
            'parameters': self.get('parameters', []),
            'filters': self.get('default_filters', {}),
            'output_format': self.get('default_output_format', 'pdf'),
            'owner_id': user.get('id'),
            'is_template': False
        }
        
        # Apply any override data
        if override_data:
            report_data.update(override_data)
        
        # Create and return Report instance
        return Report.from_dict(report_data)
    
    def to_dict(self) -> Dict:
        """
        Converts template to dictionary.
        
        Returns:
            Dictionary representation of template
        """
        template_dict = super().to_dict()
        
        # Convert parameters to dictionaries if they aren't already
        parameters = template_dict.get('parameters', [])
        for i, param in enumerate(parameters):
            if not isinstance(param, dict):
                parameters[i] = param.to_dict()
        
        return template_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReportTemplate':
        """
        Creates a ReportTemplate instance from dictionary data.
        
        Args:
            data: Dictionary of template data
            
        Returns:
            New ReportTemplate instance
        """
        # Convert parameters to ReportParameter objects
        if 'parameters' in data:
            parameters = []
            for param_data in data['parameters']:
                parameters.append(ReportParameter(param_data))
            data['parameters'] = [p.to_dict() for p in parameters]
        
        # Create new ReportTemplate instance
        return cls(data)