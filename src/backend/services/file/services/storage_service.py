"""
Service responsible for handling file storage operations using AWS S3, including generating secure URLs, uploading, downloading, and deleting files.
"""
# Third-party imports
import boto3  # version: ^1.26.0 AWS SDK for Python to interact with S3 storage
import botocore  # version: ^1.29.0 Core functionalities for AWS SDK including exceptions
import typing  # standard library Type hints for better code documentation
import os  # standard library Operating system interfaces for path operations
import uuid  # standard library Generate unique identifiers for files

# Internal imports
from ..config import config  # Import service configuration settings
from ..config import get_config  # Import service configuration settings
from ....common.logging.logger import get_logger  # Logging functionality for tracking storage operations
from ....common.exceptions.api_exceptions import ApiException  # Exception handling for storage-related errors
from . import models  # File data model for metadata operations
from ....common.utils.security import generate_secure_token  # Generate secure tokens for file operations

# Initialize logger
logger = get_logger('storage_service')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}

# Maximum file size from config
MAX_FILE_SIZE = config.MAX_FILE_SIZE


def get_s3_client():
    """
    Creates and returns an authenticated S3 client using AWS credentials from configuration.

    Returns:
        object: Configured boto3 S3 client instance
    """
    # Read AWS credentials from configuration
    s3_config = config.get_storage_config()['s3']
    access_key = s3_config['access_key']
    secret_key = s3_config['secret_key']
    region = s3_config['region']
    endpoint_url = s3_config['endpoint_url']

    # Initialize boto3 S3 client with credentials
    s3_client = boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url
    )

    # Return the S3 client instance
    return s3_client


def validate_file_size(file_size):
    """
    Validates that the file size is within the allowed limit.

    Args:
        file_size (int): Size of the file in bytes

    Returns:
        bool: True if file size is valid, raises exception otherwise
    """
    # Check if file_size exceeds MAX_FILE_SIZE
    if file_size > MAX_FILE_SIZE:
        # If exceeded, raise ApiException with appropriate error message
        raise ApiException(message=f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE} bytes",
                             status_code=400, error_code="invalid_file_size")

    # Return True if size is valid
    return True


def validate_file_extension(filename):
    """
    Validates that the file extension is in the list of allowed extensions.

    Args:
        filename (str): Name of the file

    Returns:
        bool: True if file extension is allowed, raises exception otherwise
    """
    # Extract file extension from filename
    extension = filename.split('.')[-1].lower()

    # Check if extension is in ALLOWED_EXTENSIONS
    if extension not in ALLOWED_EXTENSIONS:
        # If not allowed, raise ApiException with appropriate error message
        raise ApiException(message=f"File extension '{extension}' is not allowed",
                             status_code=400, error_code="invalid_file_extension")

    # Return True if extension is allowed
    return True


def generate_unique_filename(original_filename):
    """
    Generates a unique filename for storage to prevent collisions.

    Args:
        original_filename (str): Original filename of the file

    Returns:
        str: Unique filename with original extension
    """
    # Generate a UUID for uniqueness
    unique_id = uuid.uuid4()

    # Extract the extension from original_filename
    extension = original_filename.split('.')[-1]

    # Combine UUID with original extension
    unique_filename = f"{unique_id}.{extension}"

    # Return the unique filename
    return unique_filename


def generate_storage_key(user_id, filename):
    """
    Generates a storage key (path) for organizing files in storage.

    Args:
        user_id (str): ID of the user uploading the file
        filename (str): Unique filename of the file

    Returns:
        str: Storage key path string
    """
    # Create a nested path structure using user_id for organization
    storage_key = f"user_uploads/{user_id}/{filename}"

    # Return the complete storage key
    return storage_key


def generate_presigned_upload_url(user_id, filename, file_size, content_type):
    """
    Generates a pre-signed URL for secure client-side file uploads.

    Args:
        user_id (str): ID of the user uploading the file
        filename (str): Original filename of the file
        file_size (int): Size of the file in bytes
        content_type (str): Content type of the file

    Returns:
        dict: Upload details including URL, storage key, and fields
    """
    # Validate file size using validate_file_size
    validate_file_size(file_size)

    # Validate file extension using validate_file_extension
    validate_file_extension(filename)

    # Generate a unique filename
    unique_filename = generate_unique_filename(filename)

    # Generate storage key using user_id and unique filename
    storage_key = generate_storage_key(user_id, unique_filename)

    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Generate presigned POST URL with appropriate conditions
    fields = {"acl": "private", "Content-Type": content_type}
    conditions = [
        {"acl": "private"},
        {"Content-Type": content_type},
        ["content-length-range", 0, file_size]
    ]
    presigned_url = s3_client.generate_presigned_post(
        bucket_name,
        storage_key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=config.UPLOAD_URL_EXPIRY
    )

    # Return upload details dictionary with URL, fields, and storage key
    return {
        "url": presigned_url['url'],
        "fields": presigned_url['fields'],
        "storage_key": storage_key
    }


def generate_presigned_download_url(storage_key, expiration_seconds=3600):
    """
    Generates a pre-signed URL for secure file downloads.

    Args:
        storage_key (str): Storage key of the file
        expiration_seconds (int): Expiration time in seconds (default: 3600)

    Returns:
        str: Presigned download URL
    """
    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Generate presigned URL for GET operation with specified expiration
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': storage_key},
        ExpiresIn=expiration_seconds
    )

    # Return the presigned URL
    return presigned_url


def check_file_exists(storage_key):
    """
    Checks if a file exists in the storage.

    Args:
        storage_key (str): Storage key of the file

    Returns:
        bool: True if file exists, False otherwise
    """
    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Try to head_object with storage_key
    try:
        s3_client.head_object(Bucket=bucket_name, Key=storage_key)
        # Return True if successful
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # Return False if 404 error
            return False
        else:
            # Re-raise any other exceptions
            raise


def delete_file(storage_key):
    """
    Deletes a file from storage.

    Args:
        storage_key (str): Storage key of the file

    Returns:
        bool: True if deletion was successful
    """
    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Check if file exists using check_file_exists
    if check_file_exists(storage_key):
        # If file exists, delete object with storage_key
        s3_client.delete_object(Bucket=bucket_name, Key=storage_key)
        logger.info(f"Deleted file from S3 bucket: {storage_key}")
        # Return True if successful
        return True
    else:
        logger.warning(f"File not found in S3 bucket: {storage_key}")
        return False


def copy_file(source_key, destination_key):
    """
    Creates a copy of a file within the storage.

    Args:
        source_key (str): Storage key of the source file
        destination_key (str): Storage key of the destination file

    Returns:
        bool: True if copy was successful
    """
    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Check if source file exists using check_file_exists
    if check_file_exists(source_key):
        # Copy object from source_key to destination_key
        copy_source = {'Bucket': bucket_name, 'Key': source_key}
        s3_client.copy_object(CopySource=copy_source, Bucket=bucket_name, Key=destination_key)
        logger.info(f"Copied file from {source_key} to {destination_key} in S3 bucket")
        # Return True if successful
        return True
    else:
        logger.warning(f"Source file not found in S3 bucket: {source_key}")
        return False


def move_file_to_quarantine(storage_key):
    """
    Moves a potentially unsafe file to a quarantine location.

    Args:
        storage_key (str): Storage key of the file to quarantine

    Returns:
        str: Quarantine storage key
    """
    # Get config
    storage_config = config.get_storage_config()

    # Get bucket name from config
    bucket_name = storage_config['bucket_name']
    quarantine_bucket = storage_config['quarantine_bucket']

    # Generate quarantine storage key
    quarantine_storage_key = f"quarantine/{storage_key}"

    # Copy file to quarantine using copy_file
    if copy_file(storage_key, quarantine_storage_key):
        # Delete original file using delete_file
        if delete_file(storage_key):
            logger.info(f"Moved file {storage_key} to quarantine: {quarantine_storage_key}")
            # Return the quarantine storage key
            return quarantine_storage_key
        else:
            logger.error(f"Failed to delete original file {storage_key} after copying to quarantine")
            return None
    else:
        logger.error(f"Failed to copy file {storage_key} to quarantine")
        return None


def get_file_metadata(storage_key):
    """
    Retrieves metadata about a stored file.

    Args:
        storage_key (str): Storage key of the file

    Returns:
        dict: File metadata including size, content type, and last modified
    """
    # Get S3 client
    s3_client = get_s3_client()

    # Get bucket name from config
    bucket_name = config.get_storage_config()['bucket_name']

    # Check if file exists using check_file_exists
    if check_file_exists(storage_key):
        # Get object metadata using head_object
        response = s3_client.head_object(Bucket=bucket_name, Key=storage_key)

        # Extract and return relevant metadata
        metadata = {
            'size': response['ContentLength'],
            'contentType': response['ContentType'],
            'lastModified': response['LastModified']
        }
        return metadata
    else:
        logger.warning(f"File not found in S3 bucket: {storage_key}")
        return None