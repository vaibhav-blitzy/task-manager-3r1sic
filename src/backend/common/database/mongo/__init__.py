"""
Initialization module for MongoDB database integration that serves as the package
entry point, exposing connection management functions and document model classes
for consumption by service modules across the system.
"""

import logging
from .connection import (
    initialize_database,
    get_client,
    get_database,
    get_collection,
    ping_database,
    close_connection,
    reconnect,
    with_retry
)
from .models import (
    BaseDocument,
    TimestampedDocument,
    VersionedDocument,
    AuditableDocument,
    DocumentQuery,
    ConcurrentModificationError,
    generate_id,
    object_id_to_str,
    str_to_object_id
)

# Configure module logger
logger = logging.getLogger(__name__)