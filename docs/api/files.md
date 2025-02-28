# File Management API

## Introduction

The File Management API provides comprehensive capabilities for managing file attachments within the Task Management System. It enables secure uploading, downloading, and management of files attached to tasks, projects, and comments.

This API follows RESTful principles and supports standard HTTP methods for interacting with file resources. All responses are returned in JSON format except for file downloads, which return the file content with appropriate content types.

## Base URL

All File Management API endpoints are relative to the base URL:

```
https://api.taskmanagementsystem.com/v1
```

## Authentication

All requests to the File Management API require authentication. The API uses JWT (JSON Web Token) for authentication, which should be included in the `Authorization` header of all requests:

```
Authorization: Bearer {your_token}
```

Tokens can be obtained through the Authentication API. Access to file operations is controlled by the permissions of the authenticated user in relation to the associated task, project, or comment.

## File Object Model

### File Object

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier of the file (UUID) |
| name | string | Original filename |
| size | number | File size in bytes |
| type | string | MIME type of the file |
| extension | string | File extension |
| url | string | Temporary URL for file access (expires in 15 minutes) |
| preview | object | Preview information (see Preview Object) |
| metadata | object | Metadata information (see Metadata Object) |
| security | object | Security information (see Security Object) |
| associations | object | Resource associations (see Associations Object) |
| versions | array | Array of previous file versions (see Version Object) |

### Preview Object

| Field | Type | Description |
|-------|------|-------------|
| thumbnail | string | URL to thumbnail image (for supported file types) |
| previewAvailable | boolean | Whether a preview is available |
| previewType | string | Type of preview (image/pdf/document/none) |

### Metadata Object

| Field | Type | Description |
|-------|------|-------------|
| uploadedBy | string | ID of user who uploaded the file |
| uploadedAt | string | ISO 8601 timestamp of upload time |
| lastAccessed | string | ISO 8601 timestamp of last access time |
| accessCount | number | Number of times the file has been accessed |
| md5Hash | string | MD5 checksum of file content |

### Security Object

| Field | Type | Description |
|-------|------|-------------|
| accessLevel | string | Access level (public/private/shared) |
| encryptionType | string | Type of encryption used |
| scanStatus | string | Virus scan status (pending/clean/infected/unknown) |

### Associations Object

| Field | Type | Description |
|-------|------|-------------|
| taskId | string | ID of associated task (if any) |
| projectId | string | ID of associated project (if any) |
| commentId | string | ID of associated comment (if any) |

### Version Object

| Field | Type | Description |
|-------|------|-------------|
| id | string | Version ID |
| storageKey | string | Internal storage identifier |
| size | number | File size in bytes |
| uploadedBy | string | ID of user who uploaded this version |
| uploadedAt | string | ISO 8601 timestamp of version upload time |
| changeNotes | string | Notes describing changes in this version |

## API Endpoints

### List Files

Retrieves a list of files based on query parameters.

```
GET /files
```

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| page | number | Page number for pagination (default: 1) | No |
| limit | number | Number of files per page (default: 20, max: 100) | No |
| taskId | string | Filter by associated task ID | No |
| projectId | string | Filter by associated project ID | No |
| uploadedBy | string | Filter by uploader user ID | No |
| type | string | Filter by file type | No |
| q | string | Search term to filter files by name | No |

#### Response

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "project_plan.pdf",
      "size": 2458765,
      "type": "application/pdf",
      "extension": "pdf",
      "url": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/download?token=xyz",
      "preview": {
        "thumbnail": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/thumbnail",
        "previewAvailable": true,
        "previewType": "pdf"
      },
      "metadata": {
        "uploadedBy": "user123",
        "uploadedAt": "2023-06-15T14:30:00Z",
        "lastAccessed": "2023-06-16T09:15:30Z",
        "accessCount": 5,
        "md5Hash": "a1b2c3d4e5f6g7h8i9j0"
      },
      "security": {
        "accessLevel": "private",
        "encryptionType": "AES-256",
        "scanStatus": "clean"
      },
      "associations": {
        "taskId": "task789",
        "projectId": "proj456",
        "commentId": null
      }
    }
    // More file objects...
  ],
  "pagination": {
    "total": 143,
    "page": 1,
    "limit": 20,
    "pages": 8
  }
}
```

### Get File Metadata

Retrieves metadata for a specific file.

```
GET /files/{id}
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "project_plan.pdf",
  "size": 2458765,
  "type": "application/pdf",
  "extension": "pdf",
  "url": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/download?token=xyz",
  "preview": {
    "thumbnail": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/thumbnail",
    "previewAvailable": true,
    "previewType": "pdf"
  },
  "metadata": {
    "uploadedBy": "user123",
    "uploadedAt": "2023-06-15T14:30:00Z",
    "lastAccessed": "2023-06-16T09:15:30Z",
    "accessCount": 5,
    "md5Hash": "a1b2c3d4e5f6g7h8i9j0"
  },
  "security": {
    "accessLevel": "private",
    "encryptionType": "AES-256", 
    "scanStatus": "clean"
  },
  "associations": {
    "taskId": "task789",
    "projectId": "proj456",
    "commentId": null
  },
  "versions": [
    {
      "id": "version123",
      "storageKey": "internal-key-789",
      "size": 2355678,
      "uploadedBy": "user123",
      "uploadedAt": "2023-06-14T10:15:00Z", 
      "changeNotes": "Initial version"
    }
  ]
}
```

### Request Upload URL

Initiates the file upload process by requesting a pre-signed URL. This endpoint creates a file metadata record and returns a URL for uploading the file content directly.

```
POST /files/upload
```

#### Request Body

```json
{
  "name": "design_mockup.png",
  "size": 1243567,
  "type": "image/png",
  "associations": {
    "taskId": "task789",
    "projectId": "proj456"
  },
  "accessLevel": "private"
}
```

#### Response

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "uploadUrl": "https://storage.taskmanagementsystem.com/uploads/550e8400-e29b-41d4-a716-446655440000?signature=abc123",
  "uploadMethod": "PUT",
  "expiresAt": "2023-06-15T15:00:00Z",
  "requiredHeaders": {
    "Content-Type": "image/png"
  },
  "maxSize": 26214400,
  "callbackUrl": "https://api.taskmanagementsystem.com/v1/files/upload/complete"
}
```

### Confirm Upload Completion

Confirms that a file has been successfully uploaded to the storage service. This endpoint should be called after uploading the file content to the provided upload URL.

```
POST /files/upload/complete
```

#### Request Body

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "uploadToken": "abc123xyz"
}
```

#### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "design_mockup.png",
  "size": 1243567,
  "type": "image/png",
  "extension": "png",
  "url": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/download?token=xyz",
  "status": "uploaded",
  "scanStatus": "pending"
}
```

### Get Download URL

Generates a temporary URL for downloading the file. This URL is valid for 15 minutes.

```
GET /files/{id}/download
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Response

```json
{
  "url": "https://storage.taskmanagementsystem.com/download/550e8400-e29b-41d4-a716-446655440000?signature=xyz123&expires=1686891600",
  "expiresAt": "2023-06-15T15:00:00Z",
  "filename": "design_mockup.png",
  "size": 1243567,
  "type": "image/png"
}
```

### Get File Preview

Generates a preview for supported file types (images, PDFs, documents).

```
GET /files/{id}/preview
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| width | number | Desired width of preview (for images) | No |
| height | number | Desired height of preview (for images) | No |
| page | number | Page number for multi-page documents (default: 1) | No |

#### Response

The response is the preview content with the appropriate Content-Type header.

### Get File Thumbnail

Retrieves a thumbnail image for the file (for supported file types).

```
GET /files/{id}/thumbnail
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| size | string | Thumbnail size (small/medium/large) | No |

#### Response

The response is the thumbnail image with the appropriate Content-Type header.

### Delete File

Deletes a file and its content.

```
DELETE /files/{id}
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Query Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| force | boolean | Force permanent deletion (default: false) | No |

#### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "deleted"
}
```

### List File Versions

Retrieves the version history of a file.

```
GET /files/{id}/versions
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Response

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "fileName": "project_plan.pdf",
  "currentVersion": "version456",
  "versions": [
    {
      "id": "version456",
      "storageKey": "internal-key-456",
      "size": 2458765,
      "uploadedBy": "user123",
      "uploadedAt": "2023-06-15T14:30:00Z",
      "changeNotes": "Updated with client feedback"
    },
    {
      "id": "version123",
      "storageKey": "internal-key-789",
      "size": 2355678,
      "uploadedBy": "user123",
      "uploadedAt": "2023-06-14T10:15:00Z",
      "changeNotes": "Initial version"
    }
  ]
}
```

### Upload New Version

Uploads a new version of an existing file.

```
POST /files/{id}/versions
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |

#### Request Body

```json
{
  "size": 2458765,
  "changeNotes": "Updated with client feedback"
}
```

#### Response

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "versionId": "version456",
  "uploadUrl": "https://storage.taskmanagementsystem.com/uploads/version456?signature=def456",
  "uploadMethod": "PUT",
  "expiresAt": "2023-06-15T15:00:00Z",
  "requiredHeaders": {
    "Content-Type": "application/pdf"
  },
  "maxSize": 26214400,
  "callbackUrl": "https://api.taskmanagementsystem.com/v1/files/{id}/versions/complete"
}
```

### Restore Previous Version

Restores a file to a previous version.

```
POST /files/{id}/versions/{versionId}/restore
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| id | string | File ID | Yes |
| versionId | string | Version ID to restore | Yes |

#### Response

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "currentVersion": "version123",
  "status": "restored",
  "previousVersion": "version456"
}
```

## Task Attachment Operations

### List Task Attachments

Retrieves all files attached to a specific task.

```
GET /tasks/{taskId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| taskId | string | Task ID | Yes |

#### Response

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "project_plan.pdf",
      "size": 2458765,
      "type": "application/pdf",
      "extension": "pdf",
      "url": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/download?token=xyz",
      "preview": {
        "thumbnail": "https://api.taskmanagementsystem.com/v1/files/550e8400-e29b-41d4-a716-446655440000/thumbnail",
        "previewAvailable": true,
        "previewType": "pdf"
      },
      "metadata": {
        "uploadedBy": "user123",
        "uploadedAt": "2023-06-15T14:30:00Z",
        "lastAccessed": "2023-06-16T09:15:30Z",
        "accessCount": 5
      }
    }
    // More file objects...
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "limit": 20
  }
}
```

### Attach File to Task

Attaches an existing file to a task.

```
POST /tasks/{taskId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| taskId | string | Task ID | Yes |

#### Request Body

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response

```json
{
  "taskId": "task789",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": true
}
```

### Detach File from Task

Removes a file attachment from a task without deleting the file.

```
DELETE /tasks/{taskId}/attachments/{fileId}
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| taskId | string | Task ID | Yes |
| fileId | string | File ID | Yes |

#### Response

```json
{
  "taskId": "task789",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": false
}
```

## Project Attachment Operations

### List Project Attachments

Retrieves all files attached to a specific project.

```
GET /projects/{projectId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| projectId | string | Project ID | Yes |

#### Response

Similar to the task attachments response.

### Attach File to Project

Attaches an existing file to a project.

```
POST /projects/{projectId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| projectId | string | Project ID | Yes |

#### Request Body

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response

```json
{
  "projectId": "proj456",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": true
}
```

### Detach File from Project

Removes a file attachment from a project without deleting the file.

```
DELETE /projects/{projectId}/attachments/{fileId}
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| projectId | string | Project ID | Yes |
| fileId | string | File ID | Yes |

#### Response

```json
{
  "projectId": "proj456",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": false
}
```

## Comment Attachment Operations

### List Comment Attachments

Retrieves all files attached to a specific comment.

```
GET /comments/{commentId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| commentId | string | Comment ID | Yes |

#### Response

Similar to the task attachments response.

### Attach File to Comment

Attaches an existing file to a comment.

```
POST /comments/{commentId}/attachments
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| commentId | string | Comment ID | Yes |

#### Request Body

```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response

```json
{
  "commentId": "comment123",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": true
}
```

### Detach File from Comment

Removes a file attachment from a comment without deleting the file.

```
DELETE /comments/{commentId}/attachments/{fileId}
```

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| commentId | string | Comment ID | Yes |
| fileId | string | File ID | Yes |

#### Response

```json
{
  "commentId": "comment123",
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "attached": false
}
```

## Error Handling

The File Management API uses standard HTTP status codes to indicate the success or failure of a request.

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - The request was successful |
| 201 | Created - The resource was successfully created |
| 400 | Bad Request - The request was invalid or cannot be served |
| 401 | Unauthorized - Authentication is required or has failed |
| 403 | Forbidden - The authenticated user does not have permission |
| 404 | Not Found - The requested resource does not exist |
| 409 | Conflict - The request could not be completed due to a conflict |
| 413 | Payload Too Large - The file exceeds the size limit |
| 415 | Unsupported Media Type - The file type is not supported |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - An error occurred on the server |
| 503 | Service Unavailable - The service is temporarily unavailable |

### Error Response Format

Error responses are returned in a standardized format:

```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "The requested file could not be found",
    "details": "File with ID 550e8400-e29b-41d4-a716-446655440000 does not exist",
    "status": 404,
    "timestamp": "2023-06-15T14:30:00Z",
    "requestId": "req-abc123"
  }
}
```

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| FILE_NOT_FOUND | The requested file does not exist | 404 |
| FILE_TOO_LARGE | The file exceeds the size limit | 413 |
| UNSUPPORTED_FILE_TYPE | The file type is not supported | 415 |
| VIRUS_DETECTED | The file contains malware | 400 |
| UPLOAD_FAILED | The file upload failed | 500 |
| STORAGE_LIMIT_EXCEEDED | The user or organization storage limit has been exceeded | 403 |
| INVALID_FILE_METADATA | The provided file metadata is invalid | 400 |
| PERMISSION_DENIED | The user does not have permission to access the file | 403 |
| VERSION_NOT_FOUND | The requested file version does not exist | 404 |
| CONCURRENT_MODIFICATION | The file was modified by another user | 409 |

## Upload Process

The file upload process follows these steps:

1. **Request Upload URL**: The client requests an upload URL by providing file metadata.
2. **Upload Content**: The client uploads the file content directly to the storage service using the provided URL.
3. **Confirm Upload**: The client confirms the upload completion to the API.
4. **Virus Scanning**: The API scans the uploaded file for viruses and malware.
5. **Processing**: For certain file types, the API generates previews and thumbnails.
6. **File Available**: After processing, the file is available for download and attachment.

### Direct Upload Diagram

```
┌─────────┐          ┌─────────┐         ┌─────────────┐         ┌─────────┐
│ Client  │          │   API   │         │   Storage   │         │  Scan   │
└────┬────┘          └────┬────┘         └──────┬──────┘         └────┬────┘
     │  Request Upload URL │                    │                     │
     │ ─────────────────────>                   │                     │
     │                    │                     │                     │
     │  Upload URL + Token│                     │                     │
     │ <─────────────────────                   │                     │
     │                    │                     │                     │
     │     Upload File    │                     │                     │
     │ ──────────────────────────────────────────>                   │
     │                    │                     │                     │
     │  Upload Successful │                     │                     │
     │ <──────────────────────────────────────────                   │
     │                    │                     │                     │
     │ Confirm Completion │                     │                     │
     │ ─────────────────────>                   │                     │
     │                    │                     │                     │
     │                    │   Trigger Scan      │                     │
     │                    │ ──────────────────────────────────────────>
     │                    │                     │                     │
     │                    │                     │    Scan Results     │
     │                    │ <──────────────────────────────────────────
     │                    │                     │                     │
     │  Upload Processed  │                     │                     │
     │ <─────────────────────                   │                     │
     │                    │                     │                     │
```

## Security Considerations

### File Upload Security

1. **Content Validation**: All files are validated for correct file type and content.
2. **Size Limits**: File size limits are enforced (25MB standard, 100MB for enterprise accounts).
3. **Virus Scanning**: All uploaded files are scanned for viruses and malware.
4. **Quarantine**: Files with suspicious content are quarantined.
5. **Content Disposition**: Downloaded files use the `Content-Disposition` header to prevent inline execution.

### Access Control

1. **Permission-Based Access**: Access to files is controlled based on user permissions and associations.
2. **Temporary URLs**: Download and preview URLs are temporary and expire after 15 minutes.
3. **Signed URLs**: All URLs include signatures to prevent unauthorized access.
4. **Usage Tracking**: File access is logged for audit purposes.

### Storage Security

1. **Encryption at Rest**: All stored files are encrypted using AES-256.
2. **Secure Transport**: All file transfers use TLS 1.2 or higher.
3. **Access Logging**: All file operations are logged for audit purposes.
4. **Isolated Storage**: Files are stored in isolated containers based on tenancy.

## Code Examples

### Upload a File

```javascript
// Step 1: Request an upload URL
async function initiateFileUpload(fileName, fileSize, fileType, taskId) {
  const response = await fetch('https://api.taskmanagementsystem.com/v1/files/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: fileName,
      size: fileSize,
      type: fileType,
      associations: {
        taskId: taskId
      },
      accessLevel: 'private'
    })
  });
  
  return await response.json();
}

// Step 2: Upload the file to the provided URL
async function uploadFileContent(uploadUrl, fileContent, contentType) {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType
    },
    body: fileContent
  });
  
  return response.ok;
}

// Step 3: Confirm the upload completion
async function confirmUpload(fileId, uploadToken) {
  const response = await fetch('https://api.taskmanagementsystem.com/v1/files/upload/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      fileId: fileId,
      uploadToken: uploadToken
    })
  });
  
  return await response.json();
}

// Combined upload function
async function uploadFile(file, taskId) {
  try {
    // Step 1: Get upload URL
    const uploadInfo = await initiateFileUpload(file.name, file.size, file.type, taskId);
    
    // Step 2: Upload file content
    const uploadSuccess = await uploadFileContent(uploadInfo.uploadUrl, file, file.type);
    
    if (!uploadSuccess) {
      throw new Error('File upload failed');
    }
    
    // Step 3: Confirm upload
    const result = await confirmUpload(uploadInfo.fileId, uploadInfo.uploadToken);
    
    return result;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}
```

### Download a File

```javascript
async function downloadFile(fileId) {
  try {
    // Step 1: Get download URL
    const response = await fetch(`https://api.taskmanagementsystem.com/v1/files/${fileId}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const downloadInfo = await response.json();
    
    // Step 2: Download the file
    const fileResponse = await fetch(downloadInfo.url);
    const blob = await fileResponse.blob();
    
    // Step 3: Create a download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadInfo.filename;
    document.body.appendChild(a);
    a.click();
    
    // Step 4: Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return true;
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
}
```

### List Files for a Task

```javascript
async function getTaskAttachments(taskId, page = 1, limit = 20) {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/v1/tasks/${taskId}/attachments?page=${page}&limit=${limit}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching task attachments:', error);
    throw error;
  }
}
```

### Delete a File

```javascript
async function deleteFile(fileId, forcePermanent = false) {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/v1/files/${fileId}?force=${forcePermanent}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return await response.json();
  } catch (error) {
    console.error('Error deleting file:', error);
    throw error;
  }
}
```

## Rate Limits

The File Management API enforces rate limits to ensure fair usage and system stability:

| Operation | Standard Limit | Enterprise Limit |
|-----------|----------------|------------------|
| GET requests | 120 per minute | 300 per minute |
| POST requests | 60 per minute | 150 per minute |
| DELETE requests | 30 per minute | 75 per minute |
| Upload bandwidth | 100MB per hour | 1GB per hour |
| Download bandwidth | 250MB per hour | 2.5GB per hour |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 115
X-RateLimit-Reset: 1686891600
```

When rate limits are exceeded, the API returns a 429 Too Many Requests status code.