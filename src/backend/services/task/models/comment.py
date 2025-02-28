"""
Defines the Comment model for task-related comments in the Task Management System.

This module implements the MongoDB document model for comments on tasks,
supporting user collaboration and discussion through comments with features
like @mentions.
"""

from datetime import datetime
import re
from typing import List, Dict, Any, Optional, Union

import bson

from ...common.database.mongo.models import (
    TimestampedDocument, 
    DocumentQuery,
    str_to_object_id,
    object_id_to_str
)
from ...common.logging.logger import get_logger
from ...common.utils.validators import (
    validate_required,
    validate_string_length,
    validate_object_id
)

# Configure logger
logger = get_logger(__name__)

# Constants
COMMENT_COLLECTION = "comments"
MAX_CONTENT_LENGTH = 5000  # Maximum comment content length

class Comment(TimestampedDocument):
    """MongoDB document model representing comments on tasks."""
    
    collection_name = COMMENT_COLLECTION
    schema = {
        "task_id": {"type": "ObjectId", "required": True},
        "user_id": {"type": "ObjectId", "required": True},
        "content": {"type": "str", "required": True},
        "created_at": {"type": "datetime", "required": True},
        "updated_at": {"type": "datetime", "required": True}
    }
    use_schema_validation = True
    
    def __init__(self, data=None, is_new=True):
        """Initialize a new Comment instance."""
        super().__init__(data, is_new)
    
    def validate(self) -> bool:
        """Validates the comment document against schema rules."""
        super().validate()
        
        # Validate task_id
        task_id = self.get("task_id")
        if task_id:
            validate_object_id(str(task_id), "task_id")
        else:
            raise ValueError("task_id is required")
        
        # Validate user_id
        user_id = self.get("user_id")
        if user_id:
            validate_object_id(str(user_id), "user_id")
        else:
            raise ValueError("user_id is required")
        
        # Validate content
        content = self.get("content")
        if not content:
            raise ValueError("content is required")
        if len(content) > MAX_CONTENT_LENGTH:
            raise ValueError(f"content exceeds maximum length of {MAX_CONTENT_LENGTH} characters")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the comment document to a dictionary representation."""
        data = super().to_dict()
        
        # Convert ObjectId fields to strings
        if "task_id" in data and isinstance(data["task_id"], bson.ObjectId):
            data["task_id"] = object_id_to_str(data["task_id"])
        
        if "user_id" in data and isinstance(data["user_id"], bson.ObjectId):
            data["user_id"] = object_id_to_str(data["user_id"])
        
        # Format datetime fields
        if "created_at" in data and isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        
        if "updated_at" in data and isinstance(data["updated_at"], datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        
        return data
    
    def update_content(self, new_content: str) -> 'Comment':
        """Updates the comment content."""
        if not new_content:
            raise ValueError("content cannot be empty")
        
        if len(new_content) > MAX_CONTENT_LENGTH:
            raise ValueError(f"content exceeds maximum length of {MAX_CONTENT_LENGTH} characters")
        
        self.set("content", new_content)
        return self
    
    @classmethod
    def from_task_user(cls, task_id, user_id, content: str) -> 'Comment':
        """Factory method to create a comment for a task by a user."""
        # Convert to ObjectId if string
        if isinstance(task_id, str):
            task_id = str_to_object_id(task_id)
        
        if isinstance(user_id, str):
            user_id = str_to_object_id(user_id)
        
        # Create the comment data
        data = {
            "task_id": task_id,
            "user_id": user_id,
            "content": content
        }
        
        return cls(data=data, is_new=True)
    
    @classmethod
    def find_by_task(cls, task_id, sort=None, limit=None, skip=None) -> List['Comment']:
        """Finds comments related to a specific task."""
        # Convert to ObjectId if string
        if isinstance(task_id, str):
            task_id = str_to_object_id(task_id)
        
        # Default sort by creation date descending
        if sort is None:
            sort = {"created_at": -1}
        
        query = {"task_id": task_id}
        
        return cls.find(query=query, sort=sort, limit=limit, skip=skip)
    
    def has_mentions(self) -> bool:
        """Checks if the comment mentions any users with @username syntax."""
        content = self.get("content", "")
        return bool(re.search(r'@\w+', content))
    
    def get_mentions(self) -> List[str]:
        """Extracts user mentions from the comment content."""
        if not self.has_mentions():
            return []
        
        content = self.get("content", "")
        # Extract all usernames (without the @ symbol)
        mentions = re.findall(r'@(\w+)', content)
        return list(set(mentions))


def get_task_comments(task_id: str, limit: int = None, skip: int = None) -> List[Comment]:
    """Retrieves comments for a specific task."""
    # Convert to ObjectId if string
    if isinstance(task_id, str):
        task_id = str_to_object_id(task_id)
    
    # Create query
    query = DocumentQuery(Comment)
    query.filter({"task_id": task_id})
    query.sort("created_at", -1)  # Newest first
    
    if limit is not None:
        query.limit(limit)
    
    if skip is not None:
        query.skip(skip)
    
    return query.execute()


def count_task_comments(task_id: str) -> int:
    """Counts the number of comments for a specific task."""
    # Convert to ObjectId if string
    if isinstance(task_id, str):
        task_id = str_to_object_id(task_id)
    
    # Create an instance to access the collection
    comment = Comment()
    return comment.collection().count_documents({"task_id": task_id})


def get_user_comments(user_id: str, limit: int = None, skip: int = None) -> List[Comment]:
    """Retrieves comments created by a specific user."""
    # Convert to ObjectId if string
    if isinstance(user_id, str):
        user_id = str_to_object_id(user_id)
    
    # Create query
    query = DocumentQuery(Comment)
    query.filter({"user_id": user_id})
    query.sort("created_at", -1)  # Newest first
    
    if limit is not None:
        query.limit(limit)
    
    if skip is not None:
        query.skip(skip)
    
    return query.execute()