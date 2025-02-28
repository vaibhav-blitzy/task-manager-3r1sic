"""
Implements RESTful API endpoints for file management in the Task Management System.
Handles file creation, upload, download, updating, and deletion with proper authentication and authorization checks. This module follows the technical specifications for the File Management Component.
"""
# Third-party imports
from flask import Blueprint, request, jsonify, g  # flask 2.3.x
import uuid  # standard library
from typing import List, Dict  # standard library

# Internal imports
from ..models.file import File, get_file_by_id, get_files_by_user, search_files  # File document model for database operations
from ..services.file_service import FileService  # Core service for file management operations
from ..services.storage_service import StorageService  # Service for storage operations like generating URLs
from ..services.scanner_service import ScannerService  # Service for scanning files for viruses
from ....common.auth.decorators import token_required, permission_required, roles_required  # Authentication decorator for route protection
from ....common.exceptions.api_exceptions import ValidationError, NotFoundError, AuthorizationError, StorageError  # Exception for validation failures
from ....common.logging.logger import get_logger  # Get configured logger for the module
from ....common.schemas.pagination import parse_pagination_params, PaginationSchema  # Process pagination parameters from requests

# Initialize logger
logger = get_logger(__name__)

# Create a Flask blueprint for route grouping
file_blueprint = Blueprint('files', __name__)

# Initialize FileService with StorageService and ScannerService
file_service = FileService()

# Default download expiry time in seconds
DEFAULT_DOWNLOAD_EXPIRY = 900


@file_blueprint.route('/', methods=['GET'])
@token_required
def list_files():
    """
    API endpoint to list and filter files accessible to the current user
    """
    # Extract query parameters (search terms, filters, etc.) from request.args
    filters = request.args.to_dict()

    # Parse pagination parameters (page, per_page) from request
    pagination_params = parse_pagination_params(request.args)

    # Call file_service.get_user_files() with current user ID from g.user
    files_data = file_service.get_user_files(user_id=g.user['user_id'], filters=filters, pagination=pagination_params.to_dict())

    # Format response with file list and pagination metadata
    return jsonify(files_data), 200


@file_blueprint.route('/search', methods=['GET'])
@token_required
def search_files_api():
    """
    API endpoint to search files with advanced filtering
    """
    # Extract search criteria from request.args
    search_criteria = request.args.to_dict()

    # Parse pagination parameters from request
    pagination_params = parse_pagination_params(request.args)

    # Call file_service.search_user_files() with search criteria
    search_results = file_service.search_user_files(user_id=g.user['user_id'], search_criteria=search_criteria, pagination=pagination_params.to_dict())

    # Format response with search results and pagination metadata
    return jsonify(search_results), 200


@file_blueprint.route('/<file_id>', methods=['GET'])
@token_required
def get_file_api(file_id: str):
    """
    API endpoint to retrieve file metadata by ID
    """
    try:
        # Call file_service.get_file() with file_id
        file_data = file_service.get_file(file_id)

        # Return JSON response with file metadata and status 200
        return jsonify(file_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except AuthorizationError as e:
        # Handle AuthorizationError if user lacks permission
        logger.warning(f"Authorization error: {str(e)}")
        return jsonify({'message': str(e)}), 403


@file_blueprint.route('/', methods=['POST'])
@token_required
@permission_required('files:create')
def create_file_api():
    """
    API endpoint to initiate file creation and get upload URL
    """
    try:
        # Extract file metadata from request.json (name, size, type)
        file_data = request.get_json()

        # Call file_service.create_file() with metadata and user ID
        upload_data = file_service.create_file(file_data, g.user['user_id'])

        # Return JSON response with file metadata, upload URL and status 201
        return jsonify(upload_data), 201

    except ValidationError as e:
        # Handle ValidationError if metadata is invalid
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400


@file_blueprint.route('/<file_id>/confirm', methods=['POST'])
@token_required
def confirm_upload_api(file_id: str):
    """
    API endpoint to confirm upload completion and initiate processing
    """
    try:
        # Call file_service.confirm_upload() with file_id
        file_data = file_service.confirm_upload(file_id)

        # Return JSON response with updated file metadata and status 200
        return jsonify(file_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if file is not in 'uploading' state
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e)}), 400

    except StorageError as e:
        logger.error(f"Storage error: {str(e)}")
        return jsonify({'message': str(e)}), 500


@file_blueprint.route('/<file_id>/download', methods=['GET'])
@token_required
def get_download_url_api(file_id: str):
    """
    API endpoint to generate a time-limited download URL for a file
    """
    try:
        # Get expiry_seconds from query parameter or use DEFAULT_DOWNLOAD_EXPIRY
        expiry_seconds = request.args.get('expiry_seconds', DEFAULT_DOWNLOAD_EXPIRY, type=int)

        # Call file_service.get_download_url() with file_id and expiry_seconds
        download_info = file_service.get_download_url(file_id, expiry_seconds)

        # Return JSON response with download URL and status 200
        return jsonify(download_info), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except AuthorizationError as e:
        # Handle AuthorizationError if user lacks permission
        logger.warning(f"Authorization error: {str(e)}")
        return jsonify({'message': str(e)}), 403

    except ValidationError as e:
        # Handle ValidationError if file is not in 'ready' state
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e)}), 400


@file_blueprint.route('/<file_id>', methods=['PATCH'])
@token_required
@permission_required('files:update')
def update_file_api(file_id: str):
    """
    API endpoint to update file metadata
    """
    try:
        # Extract metadata updates from request.json
        metadata = request.get_json()

        # Call file_service.update_file_metadata() with file_id and updates
        file_data = file_service.update_file_metadata(file_id, metadata)

        # Return JSON response with updated file metadata and status 200
        return jsonify(file_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if update data is invalid
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400


@file_blueprint.route('/<file_id>/access', methods=['PATCH'])
@token_required
@permission_required('files:update')
def update_access_level_api(file_id: str):
    """
    API endpoint to update file access level (private/shared/public)
    """
    try:
        # Extract access_level from request.json
        data = request.get_json()
        access_level = data.get('access_level')

        # Call file_service.update_file_access_level() with file_id and access_level
        file_data = file_service.update_file_access_level(file_id, access_level)

        # Return JSON response with updated file metadata and status 200
        return jsonify(file_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if access_level is invalid
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400


@file_blueprint.route('/<file_id>', methods=['DELETE'])
@token_required
@permission_required('files:delete')
def delete_file_api(file_id: str):
    """
    API endpoint to delete a file
    """
    try:
        # Extract force parameter from query string (default to False)
        force = request.args.get('force', False, type=bool)

        # Call file_service.delete_file() with file_id and force flag
        file_service.delete_file(file_id, force)

        # Return JSON response with success message and status 204
        return jsonify({'message': 'File deleted successfully'}), 204

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if file has attachments and force=False
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e)}), 400


@file_blueprint.route('/<file_id>/versions', methods=['POST'])
@token_required
@permission_required('files:update')
def add_version_api(file_id: str):
    """
    API endpoint to add a new version to an existing file
    """
    try:
        # Extract version metadata from request.json (size, type)
        version_data = request.get_json()

        # Call file_service.add_file_version() with file_id, version data, and user ID
        upload_data = file_service.add_file_version(file_id, version_data, g.user['user_id'])

        # Return JSON response with upload URL for new version and status 201
        return jsonify(upload_data), 201

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if version data is invalid
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400


@file_blueprint.route('/<file_id>/versions/confirm', methods=['POST'])
@token_required
def confirm_version_upload_api(file_id: str):
    """
    API endpoint to confirm version upload completion
    """
    try:
        # Extract version_data from request.json
        version_data = request.get_json()

        # Call file_service.confirm_version_upload() with file_id and version_data
        file_data = file_service.confirm_version_upload(file_id, version_data)

        # Return JSON response with updated file metadata and status 200
        return jsonify(file_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if version confirmation fails
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400

    except StorageError as e:
        # Handle StorageError if uploaded version doesn't exist in storage
        logger.error(f"Storage error: {str(e)}")
        return jsonify({'message': str(e)}), 500


@file_blueprint.route('/<file_id>/versions', methods=['GET'])
@token_required
def get_versions_api(file_id: str):
    """
    API endpoint to list all versions of a file
    """
    try:
        # Call file_service.get_file() with file_id to get the file with versions
        file_data = file_service.get_file(file_id)

        # Extract and format version history from file metadata
        version_history = file_data.get('versions', [])

        # Return JSON response with version list and status 200
        return jsonify(version_history), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404


@file_blueprint.route('/<file_id>/preview', methods=['POST'])
@token_required
def generate_preview_api(file_id: str):
    """
    API endpoint to generate a preview for a file
    """
    try:
        # Call file_service.generate_preview() with file_id
        preview_data = file_service.generate_preview(file_id)

        # Return JSON response with preview metadata and status 200
        return jsonify(preview_data), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404

    except ValidationError as e:
        # Handle ValidationError if preview generation fails or is unsupported
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'message': str(e), 'errors': e.errors}), 400


@file_blueprint.route('/<file_id>/preview', methods=['GET'])
@token_required
def get_preview_api(file_id: str):
    """
    API endpoint to get the preview URL for a file
    """
    try:
        # Call file_service.get_file() with file_id to get the file metadata
        file_data = file_service.get_file(file_id)

        # Check if preview is available in file metadata
        if not file_data.get('preview') or not file_data['preview'].get('previewAvailable'):
            return jsonify({'message': 'Preview not available for this file'}), 404

        # Generate temporary URL for preview file if available
        preview_url = file_data['preview'].get('thumbnail')

        # Return JSON response with preview URL and status 200
        return jsonify({'url': preview_url}), 200

    except NotFoundError as e:
        # Handle NotFoundError if file doesn't exist
        logger.warning(f"File not found: {str(e)}")
        return jsonify({'message': str(e)}), 404


@file_blueprint.route('/health', methods=['GET'])
def file_health_check():
    """
    API endpoint for file service health check
    """
    try:
        # Call file_service.health_check() to get service status
        health_status = file_service.health_check()

        # Return JSON response with health information and status 200
        return jsonify(health_status), 200

    except Exception as e:
        # Handle any unexpected errors during health check
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'message': 'Service unavailable', 'error': str(e)}), 503