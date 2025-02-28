"""Implements REST API endpoints for report management, including report creation, scheduling, generation, and retrieval within the analytics service of the Task Management System."""

# Standard library imports
import io
from datetime import datetime
import uuid

# Third-party imports
from flask import Blueprint, request, jsonify, g, send_file  # flask==2.0.0

# Internal imports
from ..services.report_service import ReportService  # Implements report logic
from ..models.report import REPORT_TYPES, REPORT_OUTPUT_FORMATS  # Report-related constants
from src.backend.common.auth.decorators import token_required, permission_required, roles_required  # Authentication decorators
from src.backend.common.schemas.pagination import create_pagination_params  # Pagination utilities
from src.backend.common.exceptions.api_exceptions import ReportNotFoundError, InvalidReportParametersError  # Custom exceptions
from src.backend.common.logging.logger import logger  # Logging utility

# Create a Blueprint for reports API routes
reports_blueprint = Blueprint('reports', __name__)

# Initialize the report service
report_service = ReportService()


def handle_report_service_errors(f):
    """Decorator for handling common report service exceptions"""
    def wrapper(*args, **kwargs):
        """Wrapper function that accepts any args and kwargs"""
        try:
            return f(*args, **kwargs)
        except ReportNotFoundError as e:
            """Catch ReportNotFoundError and return 404 with error message"""
            logger.error(f"Report not found: {e}", exc_info=True)
            return jsonify({"message": str(e)}), 404
        except InvalidReportParametersError as e:
            """Catch InvalidReportParametersError and return 400 with error message"""
            logger.error(f"Invalid report parameters: {e}", exc_info=True)
            return jsonify({"message": str(e), "errors": e.errors}), 400
        except Exception as e:
            """Catch other exceptions, log them, and return 500 server error"""
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return jsonify({"message": "Internal server error"}), 500
        
        """Return the wrapper function"""
    return wrapper


@reports_blueprint.route('', methods=['GET'])
@token_required
@handle_report_service_errors
def get_reports():
    """Endpoint to list reports with filtering and pagination"""
    """Extract pagination parameters from request args"""
    pagination_params = create_pagination_params(request.args)
    """Extract filter parameters from request args"""
    filters = request.args.to_dict()
    """Call report_service.list_reports with params and filters"""
    reports_data = report_service.list_reports(
        filters=filters,
        page=pagination_params.page,
        page_size=pagination_params.per_page
    )
    """Return JSON response with paginated reports data"""
    return jsonify(reports_data), 200


@reports_blueprint.route('/<report_id>', methods=['GET'])
@token_required
@handle_report_service_errors
def get_report(report_id: str):
    """Endpoint to get a specific report by ID"""
    """Call report_service.get_report_by_id with report_id"""
    report_data = report_service.get_report_by_id(report_id)
    """Return JSON response with report data"""
    return jsonify(report_data), 200


@reports_blueprint.route('/generate', methods=['POST'])
@token_required
@permission_required('reports:generate')
@handle_report_service_errors
def generate_report():
    """Endpoint to generate a report from a template"""
    """Parse request JSON for template_id and parameters"""
    data = request.get_json()
    template_id = data.get('template_id')
    parameters = data.get('parameters', {})
    """Get current user from request context"""
    user_id = g.user.get('id')
    """Call report_service.generate_report with template_id, parameters, and user_id"""
    report = report_service.generate_report(template_id, parameters, user_id)
    """Return JSON response with generated report and 201 status code"""
    return jsonify(report), 201


@reports_blueprint.route('/schedule', methods=['POST'])
@token_required
@permission_required('reports:schedule')
@handle_report_service_errors
def schedule_report():
    """Endpoint to schedule periodic report generation"""
    """Parse request JSON for template_id, parameters, and schedule configuration"""
    data = request.get_json()
    template_id = data.get('template_id')
    parameters = data.get('parameters', {})
    schedule = data.get('schedule', {})
    """Get current user from request context"""
    user_id = g.user.get('id')
    """Call report_service.schedule_report with template_id, parameters, schedule, and user_id"""
    report = report_service.schedule_report(template_id, parameters, schedule, user_id)
    """Return JSON response with scheduled report and 201 status code"""
    return jsonify(report), 201


@reports_blueprint.route('/scheduled', methods=['GET'])
@token_required
@handle_report_service_errors
def get_scheduled_reports():
    """Endpoint to list scheduled reports with pagination"""
    """Extract pagination parameters from request args"""
    pagination_params = create_pagination_params(request.args)
    """Extract filter parameters from request args"""
    filters = request.args.to_dict()
    """Call report_service.list_scheduled_reports with params and filters"""
    scheduled_reports_data = report_service.list_scheduled_reports(
        filters=filters,
        page=pagination_params.page,
        page_size=pagination_params.per_page
    )
    """Return JSON response with paginated scheduled reports data"""
    return jsonify(scheduled_reports_data), 200


@reports_blueprint.route('/scheduled/<report_id>/cancel', methods=['POST'])
@token_required
@permission_required('reports:schedule')
@handle_report_service_errors
def cancel_scheduled_report(report_id: str):
    """Endpoint to cancel a scheduled report"""
    """Call report_service.cancel_scheduled_report with report_id"""
    report_service.cancel_scheduled_report(report_id)
    """Return JSON response with success message"""
    return jsonify({"message": "Scheduled report cancelled successfully"}), 200


@reports_blueprint.route('/<report_id>/export', methods=['GET'])
@token_required
@handle_report_service_errors
def export_report(report_id: str):
    """Endpoint to export a report in specified format"""
    """Extract format parameter from request args"""
    format = request.args.get('format', 'pdf')
    """Validate format is in REPORT_OUTPUT_FORMATS"""
    if format not in REPORT_OUTPUT_FORMATS:
        return jsonify({"message": f"Invalid format. Supported formats: {', '.join(REPORT_OUTPUT_FORMATS)}"}), 400
    """Call report_service.export_report with report_id and format"""
    file_content, filename, content_type = report_service.export_report(report_id, format)
    """Create file-like object from the report content"""
    file_io = io.BytesIO(file_content)
    """Return file download response with appropriate content type and filename"""
    return send_file(
        file_io,
        mimetype=content_type,
        as_attachment=True,
        download_name=filename
    )

@reports_blueprint.route('/templates', methods=['GET'])
@token_required
@handle_report_service_errors
def list_report_templates():
    """Endpoint to list available report templates"""
    """Extract pagination parameters from request args"""
    pagination_params = create_pagination_params(request.args)
    """Extract filter parameters from request args"""
    filters = request.args.to_dict()
    """Call report_service.list_templates with params and filters"""
    templates_data = report_service.list_templates(
        filters=filters,
        page=pagination_params.page,
        page_size=pagination_params.per_page
    )
    """Return JSON response with paginated templates data"""
    return jsonify(templates_data), 200


@reports_blueprint.route('/templates/<template_id>', methods=['GET'])
@token_required
@handle_report_service_errors
def get_report_template(template_id: str):
    """Endpoint to get a specific report template by ID"""
    """Call report_service.get_template_by_id with template_id"""
    template_data = report_service.get_template_by_id(template_id)
    """Return JSON response with template data"""
    return jsonify(template_data), 200


@reports_blueprint.route('/templates', methods=['POST'])
@token_required
@roles_required(['admin', 'manager'])
@handle_report_service_errors
def create_report_template():
    """Endpoint to create a new report template"""
    """Parse request JSON for template data"""
    template_data = request.get_json()
    """Get current user from request context"""
    user_id = g.user.get('id')
    """Add owner_id to template data if not present"""
    if 'owner_id' not in template_data:
        template_data['owner_id'] = user_id
    """Call report_service.create_report_template with template data"""
    template = report_service.create_report_template(template_data)
    """Return JSON response with created template and 201 status code"""
    return jsonify(template), 201


@reports_blueprint.route('/templates/<template_id>', methods=['PUT'])
@token_required
@roles_required(['admin', 'manager'])
@handle_report_service_errors
def update_report_template(template_id: str):
    """Endpoint to update an existing report template"""
    """Parse request JSON for template update data"""
    template_data = request.get_json()
    """Call report_service.update_template with template_id and update data"""
    template = report_service.update_template(template_id, template_data)
    """Return JSON response with updated template data"""
    return jsonify(template), 200


@reports_blueprint.route('/templates/<template_id>', methods=['DELETE'])
@token_required
@roles_required(['admin'])
@handle_report_service_errors
def delete_report_template(template_id: str):
    """Endpoint to delete a report template"""
    """Call report_service.delete_template with template_id"""
    report_service.delete_template(template_id)
    """Return JSON response with success message"""
    return jsonify({"message": "Report template deleted successfully"}), 200


@reports_blueprint.route('/types', methods=['GET'])
@token_required
def get_report_types():
    """Endpoint to get all supported report types"""
    """Return JSON response with REPORT_TYPES list"""
    return jsonify(REPORT_TYPES), 200


@reports_blueprint.route('/formats', methods=['GET'])
@token_required
def get_report_formats():
    """Endpoint to get all supported report output formats"""
    """Return JSON response with REPORT_OUTPUT_FORMATS list"""
    return jsonify(REPORT_OUTPUT_FORMATS), 200