from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ListField, DictField, BooleanField


class ChannelType:
    """
    Enumeration of available channel types in the system.
    
    These channel types represent different contexts where real-time
    communication can occur, such as tasks, projects, user-specific
    channels, or system-wide announcements.
    """
    TASK = "task"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"


class Channel(Document):
    """
    MongoDB document model representing a real-time communication channel.
    
    Channels can be associated with specific tasks, projects, or be general channels.
    They manage subscriptions and message routing for real-time updates.
    Each channel contains information about its subscribers and tracks activity
    for efficient cleanup and performance optimization.
    """
    name = StringField(required=True)
    type = StringField(required=True, choices=[
        ChannelType.TASK, ChannelType.PROJECT, 
        ChannelType.USER, ChannelType.SYSTEM
    ])
    object_id = StringField(required=True)
    object_type = StringField(required=True)
    subscribers = ListField(StringField(), default=list)
    metadata = DictField(default=dict)
    is_private = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    last_activity = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'channels',
        'indexes': [
            'type',
            'object_id',
            ('object_type', 'object_id'),
            'subscribers',
            'last_activity'
        ]
    }
    
    def add_subscriber(self, user_id):
        """
        Adds a user as a subscriber to the channel.
        
        Args:
            user_id (str): The ID of the user to add as a subscriber.
            
        Returns:
            bool: True if the user was added, False if already a subscriber.
        """
        if user_id not in self.subscribers:
            self.subscribers.append(user_id)
            self.update_activity()
            self.save()
            return True
        return False
    
    def remove_subscriber(self, user_id):
        """
        Removes a user from the channel's subscribers.
        
        Args:
            user_id (str): The ID of the user to remove.
            
        Returns:
            bool: True if the user was removed, False if not found.
        """
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self.update_activity()
            self.save()
            return True
        return False
    
    def has_subscriber(self, user_id):
        """
        Checks if a user is subscribed to the channel.
        
        Args:
            user_id (str): The ID of the user to check.
            
        Returns:
            bool: True if the user is a subscriber, False otherwise.
        """
        return user_id in self.subscribers
    
    def get_channel_info(self):
        """
        Returns a dictionary with the channel's information.
        
        This method provides a serializable representation of the channel
        that can be used in APIs and for client communication.
        
        Returns:
            dict: Channel information including name, type, subscribers count, etc.
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'type': self.type,
            'object_id': self.object_id,
            'object_type': self.object_type,
            'subscribers_count': len(self.subscribers),
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'metadata': self.metadata
        }
    
    def update_activity(self):
        """
        Updates the last_activity timestamp to the current time.
        
        This helps track active channels and can be used for cleanup
        of inactive channels to optimize performance.
        """
        self.last_activity = datetime.utcnow()
        self.save()