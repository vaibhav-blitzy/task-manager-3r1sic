"""
Implements the search functionality for tasks in the Task Management System, providing advanced filtering, full-text search, and pagination capabilities.
"""

# Standard imports
import typing
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

# Third-party imports
import pymongo  # pymongo-4.3.3
import bson.objectid  # pymongo-4.3.3

# Internal imports
from ..models.task import Task  # Task model for database operations and object mapping
from ...common.database.mongo.connection import get_database  # Access the MongoDB database instance
from ...common.database.mongo.models import str_to_object_id  # Convert string IDs to MongoDB ObjectId format
from ...common.exceptions.api_exceptions import ValidationError  # Exception for invalid search parameters
from ...common.schemas.pagination import PaginationParams, PaginatedResponse  # Standardized pagination parameter handling
from ...common.logging.logger import get_logger  # Initialize module logger
from ...common.utils.datetime import parse_date_range  # Parse date range strings to datetime objects

# Initialize module logger
logger = get_logger(__name__)

# MongoDB collection name
TASK_COLLECTION = "tasks"


def search_tasks(query: Dict, user_id: str, pagination: PaginationParams) -> PaginatedResponse:
    """
    Performs a search for tasks with filtering and pagination

    Args:
        query: Dictionary containing search parameters
        user_id: ID of the user performing the search
        pagination: Pagination parameters

    Returns:
        PaginatedResponse: Paginated response containing matching tasks
    """
    # Build MongoDB query from search parameters
    mongo_query = build_search_query(query)

    # Apply access control filters based on user_id
    access_controlled_query = apply_access_control(mongo_query, user_id)

    # Get MongoDB collection for tasks
    db = get_database()
    tasks_collection = db[TASK_COLLECTION]

    # Count total matching documents for pagination
    total_tasks = count_tasks(query=access_controlled_query, user_id=user_id)

    # Apply pagination (skip and limit) to query
    skip = pagination.get_skip()
    limit = pagination.get_limit()

    # Determine sort options based on query parameters
    sort_options = get_sort_options(query)

    # Execute query with appropriate sorting
    tasks = list(
        tasks_collection.find(access_controlled_query)
        .sort(sort_options)
        .skip(skip)
        .limit(limit)
    )

    # Convert MongoDB documents to Task objects
    task_objects = [Task.from_dict(task) for task in tasks]

    # Convert Task objects to dictionaries
    task_dicts = [task.to_dict() for task in task_objects]

    # Create and return paginated response object
    return PaginatedResponse.from_query(
        items=task_dicts, total=total_tasks, params=pagination
    )


def count_tasks(query: Dict, user_id: str) -> int:
    """
    Counts tasks matching search criteria without retrieving the full results

    Args:
        query: Dictionary containing search parameters
        user_id: ID of the user performing the search

    Returns:
        int: Count of matching tasks
    """
    # Build MongoDB query from search parameters
    mongo_query = build_search_query(query)

    # Apply access control filters based on user_id
    access_controlled_query = apply_access_control(mongo_query, user_id)

    # Get MongoDB collection for tasks
    db = get_database()
    tasks_collection = db[TASK_COLLECTION]

    # Execute count operation on the collection with the query
    count = tasks_collection.count_documents(access_controlled_query)

    # Return the count as an integer
    return count


def build_search_query(search_params: Dict) -> Dict:
    """
    Builds a MongoDB query from search parameters

    Args:
        search_params: Dictionary containing search parameters

    Returns:
        dict: MongoDB query document
    """
    # Initialize empty query dictionary
    query = {}

    # Add full-text search if 'q' parameter is provided
    if "q" in search_params and search_params["q"]:
        query.update(build_text_search_query(search_params["q"]))

    # Add status filter if 'status' parameter is provided
    if "status" in search_params and search_params["status"]:
        status_list = parse_filter_list(search_params["status"])
        query["status"] = {"$in": status_list}

    # Add priority filter if 'priority' parameter is provided
    if "priority" in search_params and search_params["priority"]:
        priority_list = parse_filter_list(search_params["priority"])
        query["priority"] = {"$in": priority_list}

    # Add assignee filter if 'assignee_id' parameter is provided
    if "assignee_id" in search_params and search_params["assignee_id"]:
        try:
            assignee_id = str_to_object_id(search_params["assignee_id"])
            query["assigneeId"] = assignee_id
        except ValueError:
            raise ValidationError(
                "Invalid assignee_id", {"assignee_id": "Must be a valid ObjectId"}
            )

    # Add project filter if 'project_id' parameter is provided
    if "project_id" in search_params and search_params["project_id"]:
        try:
            project_id = str_to_object_id(search_params["project_id"])
            query["projectId"] = project_id
        except ValueError:
            raise ValidationError(
                "Invalid project_id", {"project_id": "Must be a valid ObjectId"}
            )

    # Add due date range filter if 'due_date' parameter is provided
    if "due_date" in search_params and search_params["due_date"]:
        try:
            date_range = parse_date_range(search_params["due_date"])
            if date_range:
                start_date, end_date = date_range
                query["dueDate"] = {"$gte": start_date, "$lte": end_date}
        except ValueError as e:
            raise ValidationError("Invalid due_date", {"due_date": str(e)})

    # Add tags filter if 'tags' parameter is provided
    if "tags" in search_params and search_params["tags"]:
        tags_list = parse_filter_list(search_params["tags"])
        query["tags"] = {"$in": tags_list}

    # Add 'deleted' field filter to exclude deleted tasks
    query["deleted_at"] = None

    # Return the constructed query dictionary
    return query


def apply_access_control(query: Dict, user_id: str) -> Dict:
    """
    Applies access control filters to ensure users only see tasks they have permission to access

    Args:
        query: MongoDB query document
        user_id: ID of the user performing the search

    Returns:
        dict: Query with access control filters applied
    """
    # Convert user_id to ObjectId
    try:
        user_id_obj = str_to_object_id(user_id)
    except ValueError:
        raise ValidationError("Invalid user_id", {"user_id": "Must be a valid ObjectId"})

    # Create access control conditions (created by user, assigned to user, or visible to user)
    access_control_conditions = [
        {"createdBy": user_id_obj},
        {"assigneeId": user_id_obj},
    ]

    # Add access control conditions to existing query with $and operator
    if query:
        query = {"$and": [query, {"$or": access_control_conditions}]}
    else:
        query = {"$or": access_control_conditions}

    # Return modified query with access control
    return query


def parse_filter_list(filter_value: str) -> List[str]:
    """
    Parses comma-separated filter values into a list

    Args:
        filter_value: Comma-separated string of filter values

    Returns:
        List: List of filter values
    """
    # Check if filter_value is None or empty
    if not filter_value:
        return []

    # Split filter_value by comma
    values = filter_value.split(",")

    # Trim whitespace from each value
    values = [v.strip() for v in values]

    # Return list of filter values
    return values


def build_text_search_query(search_text: str) -> Dict:
    """
    Builds a text search query for MongoDB

    Args:
        search_text: Text to search for

    Returns:
        dict: MongoDB text search query
    """
    # Check if text search is enabled in database
    db = get_database()
    try:
        db.command("buildInfo")["textSearch"]
        text_search_enabled = True
    except pymongo.errors.OperationFailure:
        text_search_enabled = False

    if text_search_enabled:
        # If text search enabled, create $text search query with $search operator
        return {"$text": {"$search": search_text}}
    else:
        # If text search not enabled, fall back to regex search on title and description
        regex = re.compile(re.escape(search_text), re.IGNORECASE)
        return {"$or": [{"title": regex}, {"description": regex}]}


def get_sort_options(query: Dict) -> List:
    """
    Determines sort options based on query parameters

    Args:
        query: Dictionary containing search parameters

    Returns:
        List: MongoDB sort specification
    """
    sort_options = []

    # Check if text search is being used
    if "$text" in query:
        # If text search, include text score in sort criteria
        sort_options.append(("$meta", "textScore"))

    # Add due date sorting (ascending)
    sort_options.append(("dueDate", pymongo.ASCENDING))

    # Add priority sorting (descending)
    sort_options.append(("priority", pymongo.DESCENDING))

    # Add creation date sorting (descending) as final tiebreaker
    sort_options.append(("metadata.created", pymongo.DESCENDING))

    # Return list of sort specifications
    return sort_options