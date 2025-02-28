"""
Report Service module for the Task Management System.

This service is responsible for generating, scheduling, and managing reports 
in the analytics system. It handles report template management, report generation
in various formats, and scheduled report execution.
"""

import datetime
import io
import json
import csv
from typing import Dict, List, Optional, Any, Tuple, Union

import pandas as pd
from bson import ObjectId

from ..models.report import (
    Report, 
    ReportTemplate, 
    ReportExecution,
    REPORT_OUTPUT_FORMATS
)
from ./metrics_service import MetricsService
from ../../../common/database/mongo/connection import (
    get_database, 
    get_collection,
    with_retry
)
from ../../../common/logging/logger import logger
from ../../../common/utils/datetime import format_date, now
from ../../../common/exceptions/api_exceptions import (
    ReportNotFoundError,
    InvalidReportParametersError
)
from ../../../common/events/event_bus import get_event_bus_instance, create_event

# MongoDB collection names
REPORTS_COLLECTION = "reports"
REPORT_TEMPLATES_COLLECTION = "report_templates"

# Default pagination values
DEFAULT_PAGE_SIZE = 50

# Content type mapping for different export formats
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "csv": "text/csv",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
    "html": "text/html"
}


class ReportService:
    """
    Service class for managing reports, templates, and report generation
    within the analytics system.
    """
    
    def __init__(self):
        """
        Initializes the ReportService with database connections and dependencies.
        """
        # Get database connection
        self.db = get_database()
        
        # Initialize collections
        self.reports_collection = get_collection(REPORTS_COLLECTION)
        self.templates_collection = get_collection(REPORT_TEMPLATES_COLLECTION)
        
        # Initialize metrics service
        self.metrics_service = MetricsService()
        
        # Get event bus instance
        self.event_bus = get_event_bus_instance()
        
        logger.info("ReportService initialized successfully")
    
    @with_retry()
    def get_report_by_id(self, report_id: str) -> Dict:
        """
        Retrieves a report by its ID.
        
        Args:
            report_id: The ID of the report to retrieve
            
        Returns:
            Dict: Report data
            
        Raises:
            ReportNotFoundError: If the report is not found
        """
        # Convert string ID to ObjectId if needed
        if not isinstance(report_id, ObjectId):
            try:
                report_id = ObjectId(report_id)
            except Exception:
                raise ReportNotFoundError(
                    message=f"Invalid report ID format: {report_id}",
                    resource_type="report",
                    resource_id=report_id
                )
        
        # Query the report
        report_doc = self.reports_collection.find_one({"_id": report_id})
        
        if not report_doc:
            raise ReportNotFoundError(
                message=f"Report not found with ID: {report_id}",
                resource_type="report",
                resource_id=str(report_id)
            )
        
        # Convert report to dictionary
        report = Report(report_doc, is_new=False)
        return report.to_dict()
    
    @with_retry()
    def list_reports(self, 
                    filters: Dict = None, 
                    page: int = 1, 
                    page_size: int = None, 
                    sort_by: str = "created_at", 
                    ascending: bool = False) -> Dict:
        """
        Lists reports with filtering, pagination, and sorting.
        
        Args:
            filters: Query filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Field to sort by
            ascending: Sort direction (True for ascending, False for descending)
            
        Returns:
            Dict: Paginated list of reports with metadata
        """
        # Set default values
        filters = filters or {}
        page_size = page_size or DEFAULT_PAGE_SIZE
        page = max(1, page)  # Ensure page is at least 1
        
        # Calculate skip value for pagination
        skip = (page - 1) * page_size
        
        # Determine sort direction
        sort_direction = 1 if ascending else -1
        
        # Execute query with pagination and sorting
        cursor = self.reports_collection.find(
            filters,
            skip=skip,
            limit=page_size,
            sort=[(sort_by, sort_direction)]
        )
        
        # Count total matching documents for pagination metadata
        total_count = self.reports_collection.count_documents(filters)
        
        # Convert cursor to list of report dictionaries
        reports = []
        for doc in cursor:
            report = Report(doc, is_new=False)
            reports.append(report.to_dict())
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        # Return paginated results with metadata
        return {
            "reports": reports,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages
            }
        }
    
    @with_retry()
    def create_report_template(self, template_data: Dict) -> Dict:
        """
        Creates a new report template.
        
        Args:
            template_data: Template configuration data
            
        Returns:
            Dict: Created template data with assigned ID
        """
        # Validate required fields
        required_fields = ["name", "type", "description"]
        for field in required_fields:
            if field not in template_data:
                raise InvalidReportParametersError(
                    message=f"Missing required field in template: {field}",
                    errors={field: "This field is required"}
                )
        
        # Check if template name already exists
        existing = self.templates_collection.find_one({"name": template_data["name"]})
        if existing:
            raise InvalidReportParametersError(
                message=f"Template with name '{template_data['name']}' already exists",
                errors={"name": "Template name already exists"}
            )
        
        # Create new template
        template_data["is_template"] = True
        template = ReportTemplate(template_data, is_new=True)
        
        # Save to database
        template_id = self.templates_collection.insert_one(template.to_dict()).inserted_id
        
        # Retrieve the created template
        created_template = self.templates_collection.find_one({"_id": template_id})
        
        # Convert to ReportTemplate object and return as dict
        return ReportTemplate(created_template, is_new=False).to_dict()
    
    @with_retry()
    def get_template_by_id(self, template_id: str) -> Dict:
        """
        Retrieves a report template by its ID.
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            Dict: Template data
            
        Raises:
            ReportNotFoundError: If the template is not found
        """
        # Convert string ID to ObjectId if needed
        if not isinstance(template_id, ObjectId):
            try:
                template_id = ObjectId(template_id)
            except Exception:
                raise ReportNotFoundError(
                    message=f"Invalid template ID format: {template_id}",
                    resource_type="report_template",
                    resource_id=template_id
                )
        
        # Query the template
        template_doc = self.templates_collection.find_one({"_id": template_id})
        
        if not template_doc:
            raise ReportNotFoundError(
                message=f"Template not found with ID: {template_id}",
                resource_type="report_template",
                resource_id=str(template_id)
            )
        
        # Convert template to dictionary
        template = ReportTemplate(template_doc, is_new=False)
        return template.to_dict()
    
    @with_retry()
    def list_templates(self, 
                      filters: Dict = None, 
                      page: int = 1, 
                      page_size: int = None) -> Dict:
        """
        Lists report templates with filtering and pagination.
        
        Args:
            filters: Query filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Dict: Paginated list of templates with metadata
        """
        # Set default values
        filters = filters or {}
        page_size = page_size or DEFAULT_PAGE_SIZE
        page = max(1, page)  # Ensure page is at least 1
        
        # Add is_template filter
        filters["is_template"] = True
        
        # Calculate skip value for pagination
        skip = (page - 1) * page_size
        
        # Execute query with pagination
        cursor = self.templates_collection.find(
            filters,
            skip=skip,
            limit=page_size,
            sort=[("name", 1)]
        )
        
        # Count total matching documents for pagination metadata
        total_count = self.templates_collection.count_documents(filters)
        
        # Convert cursor to list of template dictionaries
        templates = []
        for doc in cursor:
            template = ReportTemplate(doc, is_new=False)
            templates.append(template.to_dict())
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        # Return paginated results with metadata
        return {
            "templates": templates,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages
            }
        }
    
    @with_retry()
    def update_template(self, template_id: str, template_data: Dict) -> Dict:
        """
        Updates an existing report template.
        
        Args:
            template_id: The ID of the template to update
            template_data: Updated template data
            
        Returns:
            Dict: Updated template data
            
        Raises:
            ReportNotFoundError: If the template is not found
        """
        # Convert string ID to ObjectId if needed
        if not isinstance(template_id, ObjectId):
            try:
                template_id = ObjectId(template_id)
            except Exception:
                raise ReportNotFoundError(
                    message=f"Invalid template ID format: {template_id}",
                    resource_type="report_template",
                    resource_id=template_id
                )
        
        # Find the template
        template_doc = self.templates_collection.find_one({"_id": template_id})
        
        if not template_doc:
            raise ReportNotFoundError(
                message=f"Template not found with ID: {template_id}",
                resource_type="report_template",
                resource_id=str(template_id)
            )
        
        # Check if name is being changed and is unique
        if "name" in template_data and template_data["name"] != template_doc["name"]:
            existing = self.templates_collection.find_one({
                "name": template_data["name"],
                "_id": {"$ne": template_id}
            })
            
            if existing:
                raise InvalidReportParametersError(
                    message=f"Template with name '{template_data['name']}' already exists",
                    errors={"name": "Template name already exists"}
                )
        
        # Update the template in the database
        self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": template_data}
        )
        
        # Retrieve the updated template
        updated_doc = self.templates_collection.find_one({"_id": template_id})
        
        # Convert to ReportTemplate object and return as dict
        return ReportTemplate(updated_doc, is_new=False).to_dict()
    
    @with_retry()
    def delete_template(self, template_id: str) -> bool:
        """
        Deletes a report template.
        
        Args:
            template_id: The ID of the template to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ReportNotFoundError: If the template is not found
        """
        # Convert string ID to ObjectId if needed
        if not isinstance(template_id, ObjectId):
            try:
                template_id = ObjectId(template_id)
            except Exception:
                raise ReportNotFoundError(
                    message=f"Invalid template ID format: {template_id}",
                    resource_type="report_template",
                    resource_id=template_id
                )
        
        # Find the template
        template_doc = self.templates_collection.find_one({"_id": template_id})
        
        if not template_doc:
            raise ReportNotFoundError(
                message=f"Template not found with ID: {template_id}",
                resource_type="report_template",
                resource_id=str(template_id)
            )
        
        # Delete the template
        result = self.templates_collection.delete_one({"_id": template_id})
        
        logger.info(f"Deleted template with ID {template_id}, result: {result.deleted_count}")
        
        return result.deleted_count > 0
    
    @with_retry()
    def generate_report(self, template_id: str, parameters: Dict, user_id: str) -> Dict:
        """
        Generates a report from a template with provided parameters.
        
        Args:
            template_id: The ID of the template to use
            parameters: Report parameters
            user_id: ID of the user generating the report
            
        Returns:
            Dict: Generated report data with results
            
        Raises:
            ReportNotFoundError: If the template is not found
            InvalidReportParametersError: If parameters are invalid
        """
        # Get the template
        template = self.get_template_by_id(template_id)
        
        # Validate parameters against template requirements
        self._validate_parameters(template, parameters)
        
        # Create a report instance from the template
        report_data = {
            "name": template["name"],
            "description": template["description"],
            "type": template["type"],
            "parameters": parameters,
            "owner_id": user_id,
            "output_format": template.get("default_output_format", "pdf")
        }
        
        report = Report(report_data, is_new=True)
        
        # Record execution start
        execution = report.record_execution({
            "started_at": now(),
            "status": "running",
            "triggered_by": user_id,
            "parameters": parameters
        })
        
        try:
            # Fetch report data based on type and parameters
            report_data = self._fetch_report_data(template["type"], parameters)
            
            # Process data according to report type
            if template["type"] == "task_status":
                # Format data for output
                output_format = report.get("output_format", "pdf")
                result = self._format_data_for_export(report_data, output_format)
                
                # Update execution record with results
                execution.complete(
                    output_url=f"/api/reports/{report.get_id()}/download",
                    output_format=output_format,
                    size_bytes=len(result) if isinstance(result, bytes) else 0
                )
                
                # Save the report and execution status
                report_id = self.reports_collection.insert_one(report.to_dict()).inserted_id
                
                # Publish report.generated event
                event = create_event(
                    "report.generated",
                    {
                        "report_id": str(report_id),
                        "user_id": user_id,
                        "report_type": template["type"],
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    },
                    "analytics.report_service"
                )
                self.event_bus.publish("report.generated", event)
                
                # Get the saved report
                saved_report = self.get_report_by_id(report_id)
                return saved_report
                
            else:
                # Handle other report types similarly
                # ... implementation for other report types ...
                
                # For now, just handle all types the same way
                output_format = report.get("output_format", "pdf")
                result = self._format_data_for_export(report_data, output_format)
                
                # Update execution record with results
                execution.complete(
                    output_url=f"/api/reports/{report.get_id()}/download",
                    output_format=output_format,
                    size_bytes=len(result) if isinstance(result, bytes) else 0
                )
                
                # Save the report and execution status
                report_id = self.reports_collection.insert_one(report.to_dict()).inserted_id
                
                # Publish report.generated event
                event = create_event(
                    "report.generated",
                    {
                        "report_id": str(report_id),
                        "user_id": user_id,
                        "report_type": template["type"],
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    },
                    "analytics.report_service"
                )
                self.event_bus.publish("report.generated", event)
                
                # Get the saved report
                saved_report = self.get_report_by_id(report_id)
                return saved_report
                
        except Exception as e:
            # Handle any errors in report generation
            error_message = f"Error generating report: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            # Update execution record with error
            execution.fail(error_message)
            
            # Save the report with error status
            report_id = self.reports_collection.insert_one(report.to_dict()).inserted_id
            
            # Raise the exception
            raise InvalidReportParametersError(
                message=error_message,
                errors={"general": str(e)}
            )
    
    @with_retry()
    def schedule_report(self, template_id: str, parameters: Dict, 
                       schedule: Dict, user_id: str) -> Dict:
        """
        Schedules a report for periodic generation.
        
        Args:
            template_id: The ID of the template to use
            parameters: Report parameters
            schedule: Schedule configuration
            user_id: ID of the user scheduling the report
            
        Returns:
            Dict: Scheduled report configuration
            
        Raises:
            ReportNotFoundError: If the template is not found
            InvalidReportParametersError: If parameters or schedule are invalid
        """
        # Get the template
        template = self.get_template_by_id(template_id)
        
        # Validate parameters against template requirements
        self._validate_parameters(template, parameters)
        
        # Validate schedule configuration
        required_schedule_fields = ["frequency", "enabled"]
        for field in required_schedule_fields:
            if field not in schedule:
                raise InvalidReportParametersError(
                    message=f"Missing required schedule field: {field}",
                    errors={f"schedule.{field}": "This field is required"}
                )
        
        # Create a report instance from the template
        report_data = {
            "name": template["name"],
            "description": template["description"],
            "type": template["type"],
            "parameters": parameters,
            "owner_id": user_id,
            "output_format": template.get("default_output_format", "pdf"),
            "schedule": schedule
        }
        
        # Create a new report instance
        report = Report(report_data, is_new=True)
        
        # Configure report schedule settings
        report.schedule(schedule)
        
        # Save the report
        report_id = self.reports_collection.insert_one(report.to_dict()).inserted_id
        
        # Publish report.scheduled event
        event = create_event(
            "report.scheduled",
            {
                "report_id": str(report_id),
                "user_id": user_id,
                "report_type": template["type"],
                "frequency": schedule["frequency"],
                "timestamp": datetime.datetime.utcnow().isoformat()
            },
            "analytics.report_service"
        )
        self.event_bus.publish("report.scheduled", event)
        
        # Get the saved report
        saved_report = self.get_report_by_id(report_id)
        return saved_report
    
    @with_retry()
    def list_scheduled_reports(self, 
                              filters: Dict = None, 
                              page: int = 1, 
                              page_size: int = None) -> Dict:
        """
        Lists scheduled reports with filtering and pagination.
        
        Args:
            filters: Query filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Dict: Paginated list of scheduled reports
        """
        # Set default values
        filters = filters or {}
        page_size = page_size or DEFAULT_PAGE_SIZE
        page = max(1, page)  # Ensure page is at least 1
        
        # Add scheduled filter
        filters["schedule.enabled"] = True
        
        # Calculate skip value for pagination
        skip = (page - 1) * page_size
        
        # Execute query with pagination
        cursor = self.reports_collection.find(
            filters,
            skip=skip,
            limit=page_size,
            sort=[("schedule.next_run", 1)]
        )
        
        # Count total matching documents for pagination metadata
        total_count = self.reports_collection.count_documents(filters)
        
        # Convert cursor to list of report dictionaries
        reports = []
        for doc in cursor:
            report = Report(doc, is_new=False)
            reports.append(report.to_dict())
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
        
        # Return paginated results with metadata
        return {
            "reports": reports,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages
            }
        }
    
    @with_retry()
    def cancel_scheduled_report(self, report_id: str) -> bool:
        """
        Cancels a scheduled report.
        
        Args:
            report_id: The ID of the report to cancel
            
        Returns:
            bool: True if cancelled successfully
            
        Raises:
            ReportNotFoundError: If the report is not found
        """
        # Get the report
        report_dict = self.get_report_by_id(report_id)
        
        # Convert to Report object
        report = Report(report_dict, is_new=False)
        
        # Check if the report has an active schedule
        schedule = report.get("schedule")
        if not schedule or not schedule.get("enabled"):
            raise InvalidReportParametersError(
                message="Report is not scheduled",
                errors={"schedule": "Report is not currently scheduled"}
            )
        
        # Cancel the schedule
        report.cancel_schedule()
        
        # Update the report in the database
        if isinstance(report_id, str):
            report_id = ObjectId(report_id)
            
        self.reports_collection.update_one(
            {"_id": report_id},
            {"$set": {"schedule": report.get("schedule")}}
        )
        
        # Publish report.schedule_cancelled event
        event = create_event(
            "report.schedule_cancelled",
            {
                "report_id": str(report_id),
                "user_id": report.get("owner_id"),
                "timestamp": datetime.datetime.utcnow().isoformat()
            },
            "analytics.report_service"
        )
        self.event_bus.publish("report.schedule_cancelled", event)
        
        return True
    
    @with_retry()
    def execute_scheduled_reports(self) -> List[Dict]:
        """
        Executes all reports scheduled to run now.
        
        Returns:
            List: List of execution results for scheduled reports
        """
        # Get current time
        current_time = now()
        
        # Find reports due to run
        query = {
            "schedule.enabled": True,
            "schedule.next_run": {"$lte": current_time}
        }
        
        reports_to_run = self.reports_collection.find(query)
        
        execution_results = []
        
        # Process each report
        for report_doc in reports_to_run:
            report = Report(report_doc, is_new=False)
            report_id = report.get_id()
            
            try:
                # Record execution start
                execution = report.record_execution({
                    "started_at": now(),
                    "status": "running",
                    "triggered_by": "scheduler",
                    "parameters": report.get("parameters", {})
                })
                
                # Generate the report
                report_data = self._fetch_report_data(
                    report.get("type"),
                    report.get("parameters", {})
                )
                
                # Format data for output
                output_format = report.get("output_format", "pdf")
                result = self._format_data_for_export(report_data, output_format)
                
                # Update execution with results
                execution.complete(
                    output_url=f"/api/reports/{report_id}/download",
                    output_format=output_format,
                    size_bytes=len(result) if isinstance(result, bytes) else 0
                )
                
                # Update next run time
                if "schedule" in report_doc and report_doc["schedule"].get("frequency"):
                    schedule = report.get("schedule")
                    schedule_obj = report.schedule(schedule)
                    schedule_obj.update_next_run()
                
                # Save the updated report
                self.reports_collection.update_one(
                    {"_id": report_id},
                    {"$set": {
                        "execution_history": report.get("execution_history"),
                        "schedule": report.get("schedule")
                    }}
                )
                
                # Publish report.generated event
                event = create_event(
                    "report.generated",
                    {
                        "report_id": str(report_id),
                        "scheduled": True,
                        "user_id": report.get("owner_id"),
                        "report_type": report.get("type"),
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    },
                    "analytics.report_service"
                )
                self.event_bus.publish("report.generated", event)
                
                # Add to execution results
                execution_results.append({
                    "report_id": str(report_id),
                    "name": report.get("name"),
                    "status": "completed",
                    "execution_id": execution.execution_id
                })
                
            except Exception as e:
                error_message = f"Error executing scheduled report {report_id}: {str(e)}"
                logger.error(error_message, exc_info=True)
                
                # Record failure
                execution = report.record_execution({
                    "started_at": now(),
                    "status": "failed",
                    "triggered_by": "scheduler",
                    "parameters": report.get("parameters", {}),
                    "error_message": str(e)
                })
                
                # Update next run time despite failure
                if "schedule" in report_doc and report_doc["schedule"].get("frequency"):
                    schedule = report.get("schedule")
                    schedule_obj = report.schedule(schedule)
                    schedule_obj.update_next_run()
                
                # Save the updated report
                self.reports_collection.update_one(
                    {"_id": report_id},
                    {"$set": {
                        "execution_history": report.get("execution_history"),
                        "schedule": report.get("schedule")
                    }}
                )
                
                # Add to execution results
                execution_results.append({
                    "report_id": str(report_id),
                    "name": report.get("name"),
                    "status": "failed",
                    "error": str(e),
                    "execution_id": execution.execution_id
                })
        
        return execution_results
    
    @with_retry()
    def export_report(self, report_id: str, format: str) -> Tuple[bytes, str, str]:
        """
        Exports a generated report in specified format.
        
        Args:
            report_id: The ID of the report to export
            format: The output format (pdf, csv, excel, json, html)
            
        Returns:
            Tuple: (file_content, filename, content_type)
            
        Raises:
            ReportNotFoundError: If the report is not found
            InvalidReportParametersError: If format is not supported
        """
        # Get the report
        report_dict = self.get_report_by_id(report_id)
        
        # Check if report has been generated
        execution_history = report_dict.get("execution_history", [])
        if not execution_history:
            raise InvalidReportParametersError(
                message="Report has not been generated yet",
                errors={"general": "No execution history found"}
            )
        
        # Find latest completed execution
        latest_execution = None
        for execution in reversed(execution_history):
            if execution.get("status") == "completed":
                latest_execution = execution
                break
        
        if not latest_execution:
            raise InvalidReportParametersError(
                message="Report does not have a completed execution",
                errors={"general": "No completed execution found"}
            )
        
        # Validate requested format
        format = format.lower()
        if format not in REPORT_OUTPUT_FORMATS:
            raise InvalidReportParametersError(
                message=f"Unsupported format: {format}",
                errors={"format": f"Format must be one of: {', '.join(REPORT_OUTPUT_FORMATS)}"}
            )
        
        # Get report data
        report_data = self._fetch_report_data(
            report_dict.get("type"),
            report_dict.get("parameters", {})
        )
        
        # Format data for requested format
        file_content = self._format_data_for_export(report_data, format)
        
        # Generate filename
        timestamp = format_date(now(), "%Y%m%d_%H%M%S")
        filename = f"{report_dict.get('name', 'report')}_{timestamp}.{format}"
        
        # Get content type
        content_type = self._get_content_type(format)
        
        return file_content, filename, content_type
    
    def _format_data_for_export(self, data: Dict, format: str) -> bytes:
        """
        Formats report data for the requested export format.
        
        Args:
            data: Report data
            format: Output format (pdf, csv, excel, json, html)
            
        Returns:
            bytes: Formatted data as bytes
            
        Raises:
            InvalidReportParametersError: If format is not supported
        """
        format = format.lower()
        
        if format not in REPORT_OUTPUT_FORMATS:
            raise InvalidReportParametersError(
                message=f"Unsupported format: {format}",
                errors={"format": f"Format must be one of: {', '.join(REPORT_OUTPUT_FORMATS)}"}
            )
        
        # Convert data to pandas DataFrame if it's not already
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Output buffer
        output = io.BytesIO()
        
        if format == 'csv':
            df.to_csv(output, index=False)
            
        elif format == 'json':
            # If data is already a dict, use it directly
            if isinstance(data, dict):
                output.write(json.dumps(data).encode('utf-8'))
            else:
                output.write(df.to_json(orient='records').encode('utf-8'))
            
        elif format == 'excel':
            df.to_excel(output, index=False, engine='openpyxl')
            
        elif format == 'pdf':
            # For PDF, we would use a library like ReportLab or WeasyPrint
            # This is a placeholder implementation
            html = df.to_html(index=False)
            
            # In an actual implementation, convert HTML to PDF here
            # For now, return HTML wrapped with PDF metadata as a placeholder
            pdf_placeholder = f"""
            %PDF-1.4
            % Placeholder PDF containing HTML report
            
            {html}
            
            %%EOF
            """.encode('utf-8')
            
            output.write(pdf_placeholder)
            
        elif format == 'html':
            df.to_html(output, index=False)
        
        # Return the content as bytes
        output.seek(0)
        return output.read()
    
    def _validate_parameters(self, template: Dict, parameters: Dict) -> bool:
        """
        Validates parameters against template requirements.
        
        Args:
            template: Report template
            parameters: Parameters to validate
            
        Returns:
            bool: True if parameters are valid
            
        Raises:
            InvalidReportParametersError: If parameters are not valid
        """
        # Get required parameters for the report type
        template_parameters = template.get("parameters", [])
        required_parameters = []
        
        for param in template_parameters:
            if isinstance(param, dict) and param.get("required", False):
                required_parameters.append(param.get("name"))
        
        # Check if all required parameters are present
        missing_parameters = []
        for param_name in required_parameters:
            if param_name not in parameters:
                missing_parameters.append(param_name)
        
        if missing_parameters:
            errors = {p: "Required parameter" for p in missing_parameters}
            raise InvalidReportParametersError(
                message="Missing required parameters",
                errors=errors
            )
        
        # Additional validation logic can be added here
        
        return True
    
    def _fetch_report_data(self, report_type: str, parameters: Dict) -> Dict:
        """
        Fetches data for report based on type and parameters.
        
        Args:
            report_type: Type of report
            parameters: Report parameters
            
        Returns:
            Dict: Report data
        """
        # Based on report type, fetch appropriate data
        if report_type == "task_status":
            return self.metrics_service.get_task_status_distribution(
                project_id=parameters.get("project_id"),
                date_range=parameters.get("date_range")
            )
            
        elif report_type == "workload_distribution":
            return self.metrics_service.get_workload_distribution(
                team_id=parameters.get("team_id")
            )
            
        elif report_type == "completion_rate":
            # Assume metrics service has this method
            return self.metrics_service.get_metrics_summary(
                metric_type="completion_rate",
                project_id=parameters.get("project_id"),
                date_range=parameters.get("date_range")
            )
            
        elif report_type == "bottleneck_identification":
            # Assume metrics service has this method
            return self.metrics_service.get_metrics_summary(
                metric_type="bottleneck",
                project_id=parameters.get("project_id"),
                date_range=parameters.get("date_range")
            )
            
        elif report_type == "burndown":
            # Assume metrics service has this method
            return self.metrics_service.get_metrics_summary(
                metric_type="burndown",
                project_id=parameters.get("project_id"),
                sprint_id=parameters.get("sprint_id")
            )
            
        else:
            # For other report types, fetch generic metrics data
            return self.metrics_service.get_metrics_summary(
                metric_type=report_type,
                **parameters
            )
    
    def _get_content_type(self, format: str) -> str:
        """
        Gets the appropriate content type for an export format.
        
        Args:
            format: Export format
            
        Returns:
            str: MIME content type
        """
        return CONTENT_TYPES.get(format, "application/octet-stream")