import json
from typing import Dict

from flask import Flask, request, session
from flask_socketio import SocketIO  # flask-socketio 5.3.x
from flask import copy_current_request_context

from . import events
from ..services.socket_service import SocketService  # Implements WebSocket API endpoints for the real-time collaboration service. Handles WebSocket connections, authentication, event handling, and enables real-time communication between clients for collaboration features like presence awareness, typing indicators, and collaborative editing.
from ..services.presence_service import PresenceService  # Manages user presence state and typing indicators
from ..services.collaboration_service import CollaborationService  # Handles collaborative editing operations with conflict resolution
from ..models.connection import Connection  # MongoDB model for WebSocket connection tracking
from ...common.logging.logger import get_logger  # Provides configured logger for WebSocket event tracking
from ...common.auth.jwt_utils import validate_access_token, get_token_identity, extract_token_from_header  # JWT token validation for WebSocket authentication
from .events import register_socket_events
from ..config import get_config  # Access configuration settings for WebSocket service

# Initialize logger
logger = get_logger(__name__)

# Initialize SocketIO
socketio = SocketIO()

# Initialize services
socket_service = SocketService()
presence_service = PresenceService()
collaboration_service = CollaborationService()
config = get_config()


def initialize_websocket(app: Flask) -> SocketIO:
    """
    Initializes and configures the SocketIO instance for the Flask application.
    """
    try:
        # Get WebSocket configuration from config
        websocket_config = config.get_websocket_settings()

        # Configure CORS settings for WebSocket
        cors_allowed_origins = websocket_config.get('cors_allowed_origins', [])

        # Create SocketIO instance with Flask app
        socketio.init_app(
            app,
            cors_allowed_origins=cors_allowed_origins,
            async_mode=websocket_config.get('async_mode', 'eventlet'),
            ping_interval=websocket_config.get('ping_interval', 25000) / 1000,  # Convert to seconds
            ping_timeout=websocket_config.get('ping_timeout', 60000) / 1000,  # Convert to seconds
            max_http_buffer_size=websocket_config.get('max_message_size', 1024 * 1024),
        )

        # Initialize SocketService instance
        global socket_service
        socket_service = SocketService()

        # Initialize PresenceService instance
        global presence_service
        presence_service = PresenceService()

        # Initialize CollaborationService instance
        global collaboration_service
        collaboration_service = CollaborationService()

        # Register event handlers
        register_socket_events(socketio, socket_service, presence_service, collaboration_service, logger)

        logger.info("WebSocket initialized successfully")
        return socketio
    except Exception as e:
        logger.error(f"WebSocket initialization failed: {str(e)}")
        raise


def authenticate_socket_request() -> Dict or bool:
    """
    Authenticates a WebSocket request using JWT token.
    """
    try:
        # Extract JWT token from request headers or query parameters
        auth_header = request.headers.get('Authorization')
        token = extract_token_from_header(auth_header)

        if not token:
            token = request.args.get('token')

        if not token:
            logger.warning("Authentication failed: No token provided")
            return False

        # Validate the token using validate_access_token
        user_data = validate_access_token(token)

        # Extract user identity from token
        user_id = get_token_identity(token)

        logger.debug(f"Successfully authenticated user {user_id} from token")
        return user_data

    except Exception as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return False


def get_client_info() -> Dict:
    """
    Extracts client information from the request.
    """
    try:
        # Extract IP address from request (consider X-Forwarded-For header)
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Extract user agent information from request headers
        user_agent = request.headers.get('User-Agent')

        # Parse device and browser information from user agent
        device = "Unknown"
        browser = "Unknown"

        # Return dictionary with client metadata
        client_info = {
            "ip": ip_address,
            "device": device,
            "browser": browser
        }
        return client_info
    except Exception as e:
        logger.error(f"Error extracting client info: {str(e)}")
        return {}


@socketio.on('connect')
def on_connect():
    """
    Handles new WebSocket connections.
    """
    try:
        # Authenticate the socket request
        user_data = authenticate_socket_request()
        if not user_data:
            return False

        # Get client information
        client_info = get_client_info()

        # Create new connection
        connection_id = socket_service.create_connection(user_data, client_info)

        # Store connection_id in session for future event handlers
        session['connection_id'] = connection_id

        # Register connection handler
        def handler(event_type, data):
            socketio.emit(event_type, data, room=request.sid)

        socket_service.register_connection_handler(connection_id, handler)

        logger.info(f"New connection established: {connection_id}")
        return True

    except Exception as e:
        logger.error(f"Error during connection: {str(e)}")
        return False


@socketio.on('disconnect')
def on_disconnect():
    """
    Handles WebSocket disconnection.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Disconnect event received without connection ID")
            return

        # Close and clean up connection
        socket_service.close_connection(connection_id)
        socket_service.unregister_connection_handler(connection_id)

        logger.info(f"Connection disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"Error during disconnection: {str(e)}")


@socketio.on('ping')
def on_ping():
    """
    Handles ping messages to keep connection alive.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Ping event received without connection ID")
            return

        # Update last ping timestamp
        socket_service.update_connection_ping(connection_id)

        # Return pong response with server timestamp
        return {'type': 'pong', 'timestamp': socket_service.update_connection_ping(connection_id)}

    except Exception as e:
        logger.error(f"Error during ping: {str(e)}")


@socketio.on('subscribe')
def on_subscribe(data: Dict):
    """
    Handles channel subscription requests.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Subscribe event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract channel, object_type, and object_id from data
        channel = data.get('channel')
        object_type = data.get('object_type')
        object_id = data.get('object_id')

        # Subscribe to channel
        success = socket_service.subscribe_to_channel(connection_id, channel, object_type, object_id)

        if success:
            logger.info(f"Subscribed to channel {channel}:{object_type}:{object_id}")
            return {'status': 'success', 'channel': channel, 'object_type': object_type, 'object_id': object_id}
        else:
            logger.error(f"Failed to subscribe to channel {channel}:{object_type}:{object_id}")
            return {'status': 'error', 'message': 'Subscription failed'}

    except Exception as e:
        logger.error(f"Error during subscription: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('unsubscribe')
def on_unsubscribe(data: Dict):
    """
    Handles channel unsubscription requests.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Unsubscribe event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract channel, object_type, and object_id from data
        channel = data.get('channel')
        object_type = data.get('object_type')
        object_id = data.get('object_id')

        # Unsubscribe from channel
        success = socket_service.unsubscribe_from_channel(connection_id, channel, object_type, object_id)

        if success:
            logger.info(f"Unsubscribed from channel {channel}:{object_type}:{object_id}")
            return {'status': 'success'}
        else:
            logger.error(f"Failed to unsubscribe from channel {channel}:{object_type}:{object_id}")
            return {'status': 'error', 'message': 'Unsubscription failed'}

    except Exception as e:
        logger.error(f"Error during unsubscription: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('presence')
def on_presence_update(data: Dict):
    """
    Handles user presence status updates.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Presence update event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract status and additional presence data
        status = data.get('status')

        # Update presence
        success = presence_service.update_presence(connection_id, {'status': status})

        if success:
            logger.info(f"Presence updated to {status} for connection {connection_id}")
            return {'status': 'success'}
        else:
            logger.error(f"Failed to update presence to {status} for connection {connection_id}")
            return {'status': 'error', 'message': 'Presence update failed'}

    except Exception as e:
        logger.error(f"Error during presence update: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('typing')
def on_typing(data: Dict):
    """
    Handles typing indicator updates.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Typing event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract isTyping boolean and location info
        is_typing = data.get('isTyping')
        location = data.get('location')

        # Update typing status
        success = presence_service.update_typing_status(connection_id, is_typing, location)

        if success:
            logger.info(f"Typing status updated to {is_typing} at {location} for connection {connection_id}")
            return {'status': 'success'}
        else:
            logger.error(f"Failed to update typing status to {is_typing} at {location} for connection {connection_id}")
            return {'status': 'error', 'message': 'Typing update failed'}

    except Exception as e:
        logger.error(f"Error during typing update: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('join_collaboration')
def on_join_collaboration(data: Dict):
    """
    Handles user joining a collaborative editing session.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Join collaboration event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract resource_type, resource_id, and field_name from data
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        field_name = data.get('field_name')

        # Join collaboration session
        session_details = collaboration_service.join_session(connection_id, resource_type, resource_id, field_name)

        logger.info(f"User joined collaboration session for {resource_type}:{resource_id}:{field_name}")
        return session_details

    except Exception as e:
        logger.error(f"Error during join collaboration: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('leave_collaboration')
def on_leave_collaboration(data: Dict):
    """
    Handles user leaving a collaborative editing session.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Leave collaboration event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract resource_type, resource_id, and field_name from data
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        field_name = data.get('field_name')

        # Leave collaboration session
        success = collaboration_service.leave_session(connection_id, resource_type, resource_id, field_name)

        if success:
            logger.info(f"User left collaboration session for {resource_type}:{resource_id}:{field_name}")
            return {'status': 'success'}
        else:
            logger.error(f"Failed to leave collaboration session for {resource_type}:{resource_id}:{field_name}")
            return {'status': 'error', 'message': 'Leave collaboration failed'}

    except Exception as e:
        logger.error(f"Error during leave collaboration: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('operation')
def on_edit_operation(data: Dict):
    """
    Handles collaborative editing operations.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Edit operation event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract resource_type, resource_id, field_name, operation, and version from data
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        field_name = data.get('field_name')
        operation = data.get('operation')
        version = data.get('version')

        # Submit operation
        operation_result = collaboration_service.submit_operation(connection_id, operation, resource_type, resource_id, field_name, version)

        logger.info(f"Edit operation submitted for {resource_type}:{resource_id}:{field_name}")
        return operation_result

    except Exception as e:
        logger.error(f"Error during edit operation: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('lock')
def on_lock_request(data: Dict):
    """
    Handles request to lock a resource for exclusive editing.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Lock request event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract resource_type, resource_id, and field_name from data
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        field_name = data.get('field_name')

        # Acquire lock
        lock_result = collaboration_service.lock_resource(connection_id, resource_type, resource_id, field_name)

        logger.info(f"Lock requested for {resource_type}:{resource_id}:{field_name}")
        return lock_result

    except Exception as e:
        logger.error(f"Error during lock request: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@socketio.on('unlock')
def on_unlock_request(data: Dict):
    """
    Handles request to release a resource editing lock.
    """
    try:
        # Get connection_id from session
        connection_id = session.get('connection_id')

        if not connection_id:
            logger.warning("Unlock request event received without connection ID")
            return {'status': 'error', 'message': 'Connection ID not found'}

        # Extract resource_type, resource_id, and field_name from data
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        field_name = data.get('field_name')

        # Release lock
        unlock_result = collaboration_service.unlock_resource(connection_id, resource_type, resource_id, field_name)

        logger.info(f"Lock released for {resource_type}:{resource_id}:{field_name}")
        return unlock_result

    except Exception as e:
        logger.error(f"Error during unlock request: {str(e)}")
        return {'status': 'error', 'message': str(e)}


def handle_error(error: Exception, event_name: str) -> Dict:
    """
    Handles and formats WebSocket errors.
    """
    try:
        # Log error details with appropriate level based on error type
        logger.error(f"Error during {event_name}: {str(error)}")

        # Create standardized error response with code and message
        error_response = {
            'status': 'error',
            'code': 'websocket_error',
            'message': str(error)
        }

        # Include error type and event name in response
        error_response['error_type'] = type(error).__name__
        error_response['event_name'] = event_name

        # Sanitize sensitive information from error details
        # (e.g., remove database connection strings)

        # Return formatted error response
        return error_response

    except Exception as e:
        logger.error(f"Error handling error: {str(e)}")
        return {'status': 'error', 'code': 'error_handler_error', 'message': 'Failed to handle error'}