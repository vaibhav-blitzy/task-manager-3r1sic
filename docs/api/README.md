# Task Management System API Documentation

Welcome to the Task Management System API documentation. This comprehensive guide provides detailed information on available endpoints, authentication methods, request/response formats, and best practices for integrating with our system.

## Introduction

The Task Management System provides a comprehensive set of RESTful APIs that enable developers to integrate with and extend the system's functionality. This documentation provides details on available endpoints, authentication methods, request/response formats, and best practices for integration.

## API Overview

The Task Management System exposes the following API services:

- **Authentication API**: User registration, authentication, and authorization
  [Authentication API Documentation](auth.md)
  
- **Task Management API**: Create, update, and manage tasks with comments, subtasks, and dependencies
  [Task Management API Documentation](tasks.md)
  
- **Project Management API**: Create and manage projects, team members, and task organization
  [Project Management API Documentation](projects.md)
  
- **Notification API**: User notifications and preference management
  [Notification API Documentation](notifications.md)
  
- **File Management API**: File uploads, attachments, and storage management
  [File Management API Documentation](files.md)
  
- **Analytics API**: Reports, dashboards, and metrics
  [Analytics API Documentation](analytics.md)
  
- **Real-time API**: WebSocket-based real-time updates and collaboration
  [Real-time API Documentation](realtime.md)

## Base URLs

The Task Management System API is available at the following base URLs:

- **Production**: https://api.taskmanagementsystem.com/api/v1
- **Staging**: https://api-staging.taskmanagementsystem.com/api/v1
- **Development**: https://api-dev.taskmanagementsystem.com/api/v1

## Authentication

The Task Management System supports several authentication methods:

- **JWT Authentication**: Standard API authentication using JSON Web Tokens (JWT)
  ```
  Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
  ```

- **OAuth 2.0**: Authentication for third-party applications using the Authorization Code flow with PKCE
  Supported flows: Authorization Code, PKCE

- **API Keys**: Service-to-service communication using UUID-based API keys
  ```
  X-API-Key: api_key_12345abcdef...
  ```

For detailed information on authentication flows, token management, and security recommendations, see the [Authentication API Documentation](auth.md).

## API Versioning

The Task Management System uses URI-based API versioning to ensure backward compatibility:

- Current API version: v1
- Version is specified in the URI path: /api/v1/
- Breaking changes are introduced in new API versions
- Previous API versions remain supported for at least 12 months after a new version is released
- Deprecated endpoints will return warning headers before being removed

## Request & Response Formats

All API endpoints follow these conventions:

The API accepts JSON request bodies and form data for file uploads
Content-Type: application/json for most requests; multipart/form-data for file uploads

All responses are returned in JSON format with consistent structure:

Success response:
```json
{
  "data": {
    "id": "123",
    "name": "Example resource"
  }
}
```

List response:
```json
{
  "data": [
    {
      "id": "123",
      "name": "First resource"
    },
    {
      "id": "456",
      "name": "Second resource"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

Error response:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource could not be found.",
    "details": "Additional information about the error"
  }
}
```

## Error Handling

The API uses standard HTTP status codes and provides consistent error responses:

| Code | Description |
|------|-------------|
| 200 OK | The request was successful |
| 201 Created | The resource was successfully created |
| 204 No Content | The request was successful but no content is returned |
| 400 Bad Request | The request was invalid or contains incorrect parameters |
| 401 Unauthorized | Authentication failed or token is invalid |
| 403 Forbidden | The authenticated user doesn't have permission |
| 404 Not Found | The requested resource could not be found |
| 409 Conflict | The request conflicts with the current state |
| 422 Unprocessable Entity | The request was well-formed but contains semantic errors |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | An unexpected error occurred on the server |

All error responses follow a consistent format with error code, message, and optional details:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters",
    "details": {
      "title": ["Title is required"],
      "dueDate": ["Due date must be in the future"]
    }
  }
}
```

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: Page number (starting from 1)
- `per_page`: Number of items per page (default: 20, max: 100)

Paginated responses include pagination metadata:

```json
{
  "data": ["// Resource objects"],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20,
    "pages": 3
  }
}
```

## Filtering and Sorting

List endpoints support filtering and sorting through query parameters:

Filter query parameters are specific to each resource type:
```
GET /api/v1/tasks?status=in-progress&assigneeId=user123
```

Sort using the sort_by and sort_dir parameters:
```
GET /api/v1/tasks?sort_by=dueDate&sort_dir=asc
```

## Rate Limiting

The API implements rate limiting to ensure stability and prevent abuse:

| Endpoint Type | Limit |
|---------------|-------|
| List/Search Endpoints | 60 requests per minute |
| Individual Resource Operations | 30 requests per minute |
| Creation Endpoints | 20 requests per minute |
| Authentication Endpoints | 10 attempts per minute per IP address |

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1623456789
```

When limits are exceeded:
```
Status: 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": "Rate limit will reset in 35 seconds"
  }
}
```

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) with the following configurations:

- Allowed origins: Production domains, Registered application domains
- Allowed methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Allowed headers: Content-Type, Authorization, X-API-Key

## API Services

The Task Management System API is organized into the following services:

| Service | Description | Base URL |
|---------|-------------|----------|
| Authentication Service | User registration, login, token management, and authorization | [Authentication API](auth.md) - `/api/v1/auth` |
| Task Management Service | Core task operations including creation, updates, assignments, and related entities | [Task Management API](tasks.md) - `/api/v1/tasks` |
| Project Management Service | Project organization, team management, and task grouping | [Project Management API](projects.md) - `/api/v1/projects` |
| Notification Service | User notifications, preferences, and delivery settings | [Notification API](notifications.md) - `/api/v1/notifications` |
| File Management Service | File uploads, attachment management, and storage | [File Management API](files.md) - `/api/v1/files` |
| Analytics Service | Reporting, dashboards, and metrics | [Analytics API](analytics.md) - `/api/v1/analytics` |
| Real-time Service | WebSocket connections for live updates and collaboration | [Real-time API](realtime.md) - `/api/v1/realtime` |

## Webhook Integration

The Task Management System supports webhook integration for real-time event notifications:

Supported events:
- task.created
- task.updated
- task.status_changed
- task.assigned
- task.completed
- project.created
- project.updated
- project.member_added
- project.status_changed
- comment.created

Webhook endpoints can be configured in the account settings or via the API.

Webhook payloads contain event type, timestamp, and relevant data:
```json
{
  "event": "task.status_changed",
  "timestamp": "2023-03-01T12:00:00Z",
  "data": {
    "taskId": "task123",
    "previousStatus": "in-progress",
    "newStatus": "completed",
    "changedBy": {
      "id": "user456",
      "name": "John Doe"
    }
  }
}
```

Webhooks include a signature header (X-Webhook-Signature) for verifying authenticity.

## Client Libraries & SDKs

The following client libraries are available for integrating with the Task Management System API:

- **JavaScript/TypeScript SDK**
  - Repository: github.com/task-management-system/js-sdk
  - Supported environments: Browser, Node.js

- **Python SDK**
  - Repository: github.com/task-management-system/python-sdk
  - Supported environments: Python 3.6+

- **Java SDK**
  - Repository: github.com/task-management-system/java-sdk
  - Supported environments: Java 11+

## API Change Policy

Our API change and deprecation policy ensures a stable developer experience:

- Breaking changes are only introduced in new API versions
- Backwards-compatible additions may be made to existing API versions
- APIs are versioned in the URI path (e.g., /api/v1/)
- Previous API versions are supported for at least 12 months after a new version
- Deprecated endpoints will return warning headers before removal
- API changes are documented in the changelog

## Support & Feedback

For questions, issues, or feedback about the API, please contact us:

- Developer Forum: forum.taskmanagementsystem.com
- GitHub Issues: github.com/task-management-system/api/issues
- Email Support: api-support@taskmanagementsystem.com