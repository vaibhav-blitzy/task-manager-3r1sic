"""Initialization file for the Realtime Service that exports key components
for WebSocket-based real-time collaboration features, making them available
to other modules while maintaining a clean namespace."""

import logging

# Internal imports
from .app import create_app  # src/backend/services/realtime/app.py
from .app import socketio  # src/backend/services/realtime/app.py
from .api.websocket import initialize_websocket  # src/backend/services/realtime/api/websocket.py
from .services.socket_service import SocketService  # src/backend/services/realtime/services/socket_service.py
from .config import get_config  # src/backend/services/realtime/config.py

# Initialize logger
logger = logging.getLogger(__name__)

# Version identifier for the Realtime Service package
VERSION = "1.0.0"

# Load configuration
CONFIG = get_config()

__all__ = [
    "create_app",
    "socketio",
    "SocketService",
    "initialize_websocket",
    "VERSION",
    "CONFIG"
]

logger.info("Realtime Service package initialized")