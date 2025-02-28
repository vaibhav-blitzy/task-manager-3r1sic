"""
Initializes the realtime service models package and exposes model classes for WebSocket connections
and real-time collaboration features.
"""

from .connection import Connection

class SubscriptionEmbedded:
    """Embedded document for tracking channel subscriptions.
    
    Attributes:
        channel (str): Channel name (e.g., 'task', 'project')
        object_id (str): ID of the object being subscribed to
        joined_at (datetime): When the subscription was created
    """
    def __init__(self, channel=None, object_id=None, joined_at=None):
        self.channel = channel
        self.object_id = object_id
        self.joined_at = joined_at

class ClientInfoEmbedded:
    """Embedded document for client information.
    
    Attributes:
        device (str): Client device information
        browser (str): Browser information
        ip (str): IP address (anonymized)
        location (str): General location
    """
    def __init__(self, device=None, browser=None, ip=None, location=None):
        self.device = device
        self.browser = browser
        self.ip = ip
        self.location = location

class PresenceEmbedded:
    """Embedded document for tracking user presence information.
    
    Attributes:
        status (str): User status ('online', 'away', 'busy', 'offline')
        last_activity (datetime): Timestamp of last activity
        current_view (str): Current view context
        typing (dict): Typing status information with fields:
            isTyping (bool): Whether user is currently typing
            location (str): Where the user is typing
    """
    def __init__(self, status='offline', last_activity=None, current_view=None, typing=None):
        self.status = status
        self.last_activity = last_activity
        self.current_view = current_view
        self.typing = typing or {'isTyping': False, 'location': None}

# Export all classes
__all__ = ["Connection", "SubscriptionEmbedded", "ClientInfoEmbedded", "PresenceEmbedded"]