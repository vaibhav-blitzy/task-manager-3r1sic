"""
Implements RESTful API endpoints for managing file attachments that link files to tasks, projects, and comments in the Task Management System. Provides routes for listing, creating, retrieving, and deleting attachments with appropriate authentication and authorization checks.
"""
import uuid  # standard library
from typing import List, Dict, Any  # standard library

import flask  # version: 2.0.1
from flask import Blueprint, request, jsonify, g  # version: 2.0.1

from src.backend.services.file.models.attachment import Attachment, get_attachment_by_id, get_attachments_by_entity, delete_entity_attachments, ENTITY_TYPES  # Attachment data model and related functions for database operations
from src.backend.services.file.services.file_service import FileService  # Core service for file and attachment management operations
from src.backend.services.file.services.storage_service import StorageService  # Service for generating download URLs and storage operations
from src.backend.common.auth.decorators import token_required, permission_required  # Authentication and authorization decorators
from src.backend.common.exceptions.api_exceptions import NotFoundError, ValidationError, AuthorizationError  # Exception classes for API error handling
from src.backend.common.logging.logger import get_logger  # Get configured logger for the module
from src.backend.common.schemas.pagination import parse_pagination_params, PaginationSchema  # Handle pagination for listing attachments

# Create a Flask Blueprint for attachments API
attachments_blueprint = Blueprint('attachments', __name__)

# Get a logger instance for this module
logger = get_logger(__name__)

# Initialize the FileService with StorageService
file_service = FileService()


@attachments_blueprint.route('/', methods=['GET'])
@token_required
def get_attachments():
    """
    API endpoint to list attachments with filtering by entity (task/project/comment)
    """
    # Log the request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Listing attachments")

    # Extract query parameters from request.args
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')

    # Validate entity_type is in ENTITY_TYPES
    if entity_type not in ENTITY_TYPES:
        logger.warning(f"Request ID: {request_id} - Invalid entity_type: {entity_type}")
        raise ValidationError(f"Invalid entity_type: {entity_type}. Must be one of: {', '.join(ENTITY_TYPES)}")

    # Parse pagination parameters using parse_pagination_params
    pagination_params = parse_pagination_params(request.args)

    try:
        # Call file_service.get_entity_attachments() with entity_type, entity_id, and pagination
        attachments = file_service.get_entity_attachments(entity_type, entity_id)

        # Apply pagination to the attachments list
        start = pagination_params.get_skip()
        end = start + pagination_params.get_limit()
        paginated_attachments = attachments[start:end]
        total = len(attachments)

        # Create pagination metadata
        pagination_metadata = {
            "page": pagination_params.page,
            "per_page": pagination_params.per_page,
            "total": total,
            "total_pages": (total + pagination_params.per_page - 1) // pagination_params.per_page,
        }

        # Return JSON response with attachment list and pagination metadata
        response_data = {
            "items": paginated_attachments,
            "metadata": pagination_metadata
        }
        logger.info(f"Request ID: {request_id} - Successfully listed attachments")
        return jsonify(response_data), 200

    except NotFoundError as e:
        logger.warning(f"Request ID: {request_id} - Entity not found: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error listing attachments: {str(e)}", exc_info=True)
        return jsonify({"message": "Error listing attachments", "error": str(e)}), 500


@attachments_blueprint.route('/', methods=['POST'])
@token_required
@permission_required('files:create')
def create_attachment():
    """
    API endpoint to create a new attachment linking a file to an entity
    """
    # Log the request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Creating attachment")

    try:
        # Extract attachment data from request.json
        attachment_data = request.get_json()

        # Validate required fields (file_id, entity_type, entity_id)
        if not all(key in attachment_data for key in ('file_id', 'entity_type', 'entity_id')):
            logger.warning(f"Request ID: {request_id} - Missing required fields in attachment data")
            raise ValidationError("Missing required fields: file_id, entity_type, entity_id")

        # Validate entity_type is in ENTITY_TYPES
        if attachment_data['entity_type'] not in ENTITY_TYPES:
            logger.warning(f"Request ID: {request_id} - Invalid entity_type: {attachment_data['entity_type']}")
            raise ValidationError(f"Invalid entity_type: {attachment_data['entity_type']}. Must be one of: {', '.join(ENTITY_TYPES)}")

        # Call file_service.create_attachment() with file_id, entity_type, entity_id, and current user
        created_attachment = file_service.create_attachment(
            file_id=attachment_data['file_id'],
            entity_type=attachment_data['entity_type'],
            entity_id=attachment_data['entity_id'],
            user_id=g.user['id']
        )

        # Return JSON response with created attachment details and 201 status code
        logger.info(f"Request ID: {request_id} - Successfully created attachment")
        return jsonify(created_attachment), 201

    except NotFoundError as e:
        logger.warning(f"Request ID: {request_id} - File not found: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Request ID: {request_id} - Invalid attachment data: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error creating attachment: {str(e)}", exc_info=True)
        return jsonify({"message": "Error creating attachment", "error": str(e)}), 500


@attachments_blueprint.route('/<attachment_id>', methods=['GET'])
@token_required
def get_attachment(attachment_id: str):
    """
    API endpoint to retrieve a specific attachment by ID
    """
    # Log the request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Retrieving attachment with ID: {attachment_id}")

    try:
        # Validate attachment_id format
        if not isinstance(attachment_id, str):
            logger.warning(f"Request ID: {request_id} - Invalid attachment_id format")
            raise ValidationError("Invalid attachment_id format")

        # Call get_attachment_by_id() with attachment_id
        attachment = get_attachment_by_id(attachment_id)

        # Handle NotFoundError if attachment doesn't exist
        if not attachment:
            logger.warning(f"Request ID: {request_id} - Attachment not found with ID: {attachment_id}")
            raise NotFoundError(f"Attachment with id {attachment_id} not found")

        # Check user's permission to access the attachment
        # TODO: Implement permission check based on entity type and user roles
        # if not has_permission(g.user, 'attachment:view', attachment):
        #     raise AuthorizationError("You don't have permission to view this attachment")

        # Include download URL for the associated file
        # download_url = file_service.get_download_url(attachment['file_id'])
        # attachment['download_url'] = download_url

        # Return JSON response with attachment details
        logger.info(f"Request ID: {request_id} - Successfully retrieved attachment with ID: {attachment_id}")
        return jsonify(attachment.to_dict()), 200

    except NotFoundError as e:
        logger.warning(f"Request ID: {request_id} - Attachment not found: {str(e)}")
        raise e
    except AuthorizationError as e:
        logger.warning(f"Request ID: {request_id} - Authorization error: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Request ID: {request_id} - Validation error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error retrieving attachment: {str(e)}", exc_info=True)
        return jsonify({"message": "Error retrieving attachment", "error": str(e)}), 500


@attachments_blueprint.route('/<attachment_id>', methods=['DELETE'])
@token_required
@permission_required('files:delete')
def delete_attachment(attachment_id: str):
    """
    API endpoint to delete an attachment
    """
    # Log the request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Deleting attachment with ID: {attachment_id}")

    try:
        # Validate attachment_id format
        if not isinstance(attachment_id, str):
            logger.warning(f"Request ID: {request_id} - Invalid attachment_id format")
            raise ValidationError("Invalid attachment_id format")

        # Call get_attachment_by_id() to verify attachment exists
        attachment = get_attachment_by_id(attachment_id)

        # Handle NotFoundError if attachment doesn't exist
        if not attachment:
            logger.warning(f"Request ID: {request_id} - Attachment not found with ID: {attachment_id}")
            raise NotFoundError(f"Attachment with id {attachment_id} not found")

        # Check user's permission to delete the attachment
        # TODO: Implement permission check based on entity type and user roles
        # if not has_permission(g.user, 'attachment:delete', attachment):
        #     raise AuthorizationError("You don't have permission to delete this attachment")

        # Call file_service.delete_attachment() with attachment_id
        file_service.delete_attachment(attachment_id)

        # Return JSON response with success message and 204 status code
        logger.info(f"Request ID: {request_id} - Successfully deleted attachment with ID: {attachment_id}")
        return jsonify({"message": "Attachment deleted successfully"}), 204

    except NotFoundError as e:
        logger.warning(f"Request ID: {request_id} - Attachment not found: {str(e)}")
        raise e
    except AuthorizationError as e:
        logger.warning(f"Request ID: {request_id} - Authorization error: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Request ID: {request_id} - Validation error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error deleting attachment: {str(e)}", exc_info=True)
        return jsonify({"message": "Error deleting attachment", "error": str(e)}), 500


@attachments_blueprint.route('/entity', methods=['DELETE'])
@token_required
@permission_required('files:delete')
def delete_entity_attachments_api():
    """
    API endpoint to delete all attachments for a specific entity
    """
    # Log the request ID for tracing
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Deleting attachments for entity")

    try:
        # Extract entity_type and entity_id from request.args
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')

        # Validate entity_type is in ENTITY_TYPES
        if entity_type not in ENTITY_TYPES:
            logger.warning(f"Request ID: {request_id} - Invalid entity_type: {entity_type}")
            raise ValidationError(f"Invalid entity_type: {entity_type}. Must be one of: {', '.join(ENTITY_TYPES)}")

        # Check user's permission to delete attachments for this entity
        # TODO: Implement permission check based on entity type and user roles
        # if not has_permission(g.user, 'attachment:delete', {'entity_type': entity_type, 'entity_id': entity_id}):
        #     raise AuthorizationError("You don't have permission to delete attachments for this entity")

        # Call delete_entity_attachments() with entity_type and entity_id
        deleted_count = delete_entity_attachments(entity_type, entity_id)

        # Return JSON response with success message and count of deleted attachments
        logger.info(f"Request ID: {request_id} - Successfully deleted {deleted_count} attachments for entity")
        return jsonify({"message": f"Deleted {deleted_count} attachments for entity", "deleted_count": deleted_count}), 200

    except AuthorizationError as e:
        logger.warning(f"Request ID: {request_id} - Authorization error: {str(e)}")
        raise e
    except ValidationError as e:
        logger.warning(f"Request ID: {request_id} - Validation error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error deleting attachments for entity: {str(e)}", exc_info=True)
        return jsonify({"message": "Error deleting attachments for entity", "error": str(e)}), 500


@attachments_blueprint.errorhandler(Exception)
def handle_attachment_error(error):
    """
    Error handler for attachment API exceptions
    """
    # Log the error with appropriate severity level
    if isinstance(error, NotFoundError):
        logger.warning(f"Attachment API - Not Found Error: {str(error)}")
        status_code = 404
    elif isinstance(error, ValidationError):
        logger.warning(f"Attachment API - Validation Error: {str(error)}")
        status_code = 400
    elif isinstance(error, AuthorizationError):
        logger.warning(f"Attachment API - Authorization Error: {str(error)}")
        status_code = 403
    else:
        logger.error(f"Attachment API - Unexpected Error: {str(error)}", exc_info=True)
        status_code = 500

    # Format error response based on exception type
    response = jsonify({"message": str(error)})
    response.status_code = status_code

    # Return JSON error response
    return response