import pytest
from unittest.mock import MagicMock
import json
from datetime import datetime

from flask_socketio import SocketIOTestClient  # flask-socketio 5.3.x

from ..models.connection import Connection  # src/backend/services/realtime/models/connection.py
from ..services.presence_service import PresenceService  # src/backend/services/realtime/services/presence_service.py
from ..services.collaboration_service import CollaborationService  # src/backend/services/realtime/services/collaboration_service.py
from ..app import create_app  # src/backend/services/realtime/app.py
from ....common.testing.fixtures import mongo_db  # src/backend/common/testing/fixtures.py
from ....common.testing.fixtures import redis_cache  # src/backend/common/testing/fixtures.py
from ....common.testing.fixtures import test_user  # src/backend/common/testing/fixtures.py

TEST_CONNECTION_ID = "test_connection_id"
TEST_USER_ID = "test_user_id"
TEST_CHANNEL = "task:test_task_id"

@pytest.fixture
def app():
    """Creates a Flask test application instance with SocketIO configured"""
    app, socketio = create_app()
    app.config['TESTING'] = True
    return app, socketio

@pytest.fixture
def socket_test_client(app):
    """Creates a SocketIO test client for testing WebSocket endpoints"""
    app, socketio = app
    client = SocketIOTestClient(app, socketio)
    client.sid = TEST_CONNECTION_ID
    return client

@pytest.fixture
def mongodb(mongo_db):
    """Provides access to MongoDB test database with connection collections"""
    db = mongo_db
    if "connections" not in db.list_collection_names():
        db.create_collection("connections")
    yield db
    db.connections.drop()

@pytest.fixture
def redis_client(redis_cache):
    """Provides a Redis client for testing real-time features"""
    client = redis_cache
    client.realtime_prefix = "realtime:"
    yield client
    client.flushdb()

@pytest.fixture
def mock_socket_service():
    """Creates a mock socket service for testing"""
    mock_service = MagicMock()
    mock_service.create_connection.return_value = TEST_CONNECTION_ID
    mock_service.close_connection.return_value = True
    mock_service.subscribe_to_channel.return_value = True
    mock_service.unsubscribe_from_channel.return_value = True
    mock_service.broadcast_to_channel.return_value = 1
    mock_service.emit_to_connection.return_value = True
    mock_service.register_connection_handler.return_value = True
    mock_service.unregister_connection_handler.return_value = True
    mock_service.update_connection_ping.return_value = datetime.utcnow()
    mock_service.authenticate_connection.return_value = {"user_id": TEST_USER_ID}
    return mock_service

@pytest.fixture
def mock_presence_service():
    """Creates a mock presence service for testing"""
    mock_service = MagicMock()
    mock_service.update_presence.return_value = True
    mock_service.update_typing_status.return_value = True
    mock_service.handle_disconnect.return_value = True
    return mock_service

@pytest.fixture
def mock_collaboration_service():
    """Creates a mock collaboration service for testing"""
    mock_service = MagicMock()
    mock_service.join_session.return_value = {"session": {}, "document": {}, "lock": None, "success": True}
    mock_service.leave_session.return_value = True
    mock_service.submit_operation.return_value = {"success": True, "document": {}, "operation": {}, "version": 1}
    mock_service.lock_resource.return_value = {"success": True}
    mock_service.unlock_resource.return_value = {"success": True}
    return mock_service

@pytest.fixture
def mock_event_bus():
    """Creates a mock event bus for testing"""
    mock_bus = MagicMock()
    mock_bus.publish.return_value = True
    mock_bus.subscribe.return_value = True
    return mock_bus

@pytest.fixture
def mock_websocket_client():
    """Creates a mock WebSocket client for testing"""
    mock_client = MagicMock()
    mock_client.emit.return_value = "response"
    mock_client.disconnect.return_value = None
    return mock_client

@pytest.fixture
def test_connection(mongodb, test_user):
    """Creates a test connection document for testing"""
    connection = {
        "connectionId": TEST_CONNECTION_ID,
        "userId": test_user["_id"],
        "clientInfo": {
            "device": "test_device",
            "browser": "test_browser",
            "ip": "127.0.0.1",
            "location": "test_location"
        },
        "subscriptions": [],
        "presence": {
            "status": "online",
            "lastActivity": datetime.utcnow(),
            "currentView": "test_view",
            "typing": {
                "isTyping": False,
                "location": None
            }
        },
        "metadata": {
            "connected": datetime.utcnow(),
            "lastPing": datetime.utcnow()
        }
    }
    mongodb.connections.insert_one(connection)
    return connection

@pytest.fixture
def test_subscription():
    """Creates a test subscription for testing"""
    subscription = {
        "key": TEST_CHANNEL + ":key",
        "channel": TEST_CHANNEL,
        "objectType": "task",
        "objectId": "test_task_id",
        "joinedAt": datetime.utcnow()
    }
    return subscription

@pytest.fixture
def patch_services(mock_socket_service, mock_presence_service, mock_collaboration_service, mock_event_bus):
    """Patches services with mocks for isolated testing"""
    with patch('src.backend.services.realtime.api.websocket.socket_service', mock_socket_service), \
         patch('src.backend.services.realtime.api.websocket.presence_service', mock_presence_service), \
         patch('src.backend.services.realtime.api.websocket.collaboration_service', mock_collaboration_service), \
         patch('src.backend.services.realtime.services.socket_service.event_bus', mock_event_bus), \
         patch('src.backend.services.realtime.services.presence_service.event_bus', mock_event_bus), \
         patch('src.backend.services.realtime.services.collaboration_service.event_bus', mock_event_bus):
        yield