# Notification API

The Notification API provides endpoints for managing notification delivery and preferences. It enables applications to retrieve notifications, manage read status, and configure notification preferences across multiple channels.

## Authentication

All notification endpoints require authentication using JWT bearer tokens. Refer to the [Authentication documentation](../auth.md) for details on how to obtain and use authentication tokens.

## Notification Endpoints

### List Notifications

Retrieve a list of notifications for the authenticated user.

- **URL**: `/api/v1/notifications`
- **Method**: `GET`
- **Authentication**: Bearer token required

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number for pagination (default: 1) |
| limit | integer | Number of items per page (default: 20, max: 100) |
| read | boolean | Filter by read status (true/false) |
| type | string | Filter by notification type (e.g., TASK_ASSIGNED, COMMENT_ADDED) |

**Responses**:

`200 OK` - List of notifications with pagination metadata

```json
{
  "data": [
    {
      "id": "60a3d1b4c7d8b92a5c9f1234",
      "recipient": "user_123",
      "type": "TASK_ASSIGNED",
      "title": "New task assigned",
      "content": "You have been assigned to 'Create wireframes'",
      "priority": "normal",
      "read": false,
      "actionUrl": "/tasks/task_456",
      "metadata": {
        "created": "2023-02-15T10:30:00Z",
        "readAt": null,
        "deliveryStatus": {
          "inApp": "delivered",
          "email": "delivered",
          "push": "disabled"
        },
        "sourceEvent": {
          "type": "task.assigned",
          "objectId": "task_456",
          "objectType": "task"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5
  }
}
```

`401 Unauthorized` - Authentication required

### Get Notification

Retrieve a specific notification by ID.

- **URL**: `/api/v1/notifications/{id}`
- **Method**: `GET`
- **Authentication**: Bearer token required

**Path Parameters**:

| Parameter | Description |
|-----------|-------------|
| id | Notification ID |

**Responses**:

`200 OK` - Notification details

`404 Not Found` - Notification not found

### Get Unread Count

Get count of unread notifications, optionally grouped by type.

- **URL**: `/api/v1/notifications/unread/count`
- **Method**: `GET`
- **Authentication**: Bearer token required

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| group_by_type | boolean | Group counts by notification type (true/false, default: false) |

**Responses**:

`200 OK` - Count of unread notifications, optionally by type

```json
{
  "total": 12,
  "byType": {
    "TASK_ASSIGNED": 3,
    "COMMENT_ADDED": 5,
    "TASK_DUE_SOON": 4
  }
}
```

### Mark as Read

Mark a specific notification as read.

- **URL**: `/api/v1/notifications/{id}/read`
- **Method**: `PATCH`
- **Authentication**: Bearer token required

**Path Parameters**:

| Parameter | Description |
|-----------|-------------|
| id | Notification ID |

**Responses**:

`200 OK` - Updated notification

`404 Not Found` - Notification not found

### Mark All as Read

Mark all notifications as read, with optional filtering.

- **URL**: `/api/v1/notifications/read-all`
- **Method**: `POST`
- **Authentication**: Bearer token required

**Request Body**:

```json
{
  "type": "TASK_ASSIGNED"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| type | string | Optional notification type filter | No |

**Responses**:

`200 OK` - Success confirmation with count of affected notifications

```json
{
  "success": true,
  "count": 5,
  "message": "5 notifications marked as read"
}
```

### Get Notification Preferences

Get user's notification preferences.

- **URL**: `/api/v1/notifications/preferences`
- **Method**: `GET`
- **Authentication**: Bearer token required

**Responses**:

`200 OK` - User preferences

```json
{
  "globalSettings": {
    "inApp": true,
    "email": true,
    "push": false,
    "digest": {
      "enabled": true,
      "frequency": "daily"
    }
  },
  "typeSettings": {
    "TASK_ASSIGNED": {
      "inApp": true,
      "email": true,
      "push": true
    },
    "COMMENT_ADDED": {
      "inApp": true,
      "email": false,
      "push": false
    }
  },
  "projectSettings": {
    "project-123": {
      "inApp": true,
      "email": true,
      "push": true
    }
  },
  "quietHours": {
    "enabled": true,
    "start": "18:00",
    "end": "09:00",
    "timezone": "America/New_York",
    "excludeUrgent": true
  }
}
```

### Update Notification Preferences

Update user's notification preferences.

- **URL**: `/api/v1/notifications/preferences`
- **Method**: `PUT`
- **Authentication**: Bearer token required

**Request Body**:

```json
{
  "globalSettings": {
    "inApp": true,
    "email": true,
    "push": false,
    "digest": {
      "enabled": true,
      "frequency": "daily"
    }
  },
  "typeSettings": {
    "TASK_ASSIGNED": {
      "inApp": true,
      "email": true,
      "push": true
    }
  },
  "quietHours": {
    "enabled": true,
    "start": "18:00",
    "end": "09:00",
    "timezone": "America/New_York",
    "excludeUrgent": true
  }
}
```

**Responses**:

`200 OK` - Updated preferences

`400 Bad Request` - Invalid request

### Test Notification

Send a test notification to verify channel delivery.

- **URL**: `/api/v1/notifications/test`
- **Method**: `POST`
- **Authentication**: Bearer token required

**Request Body**:

```json
{
  "channel": "email",
  "message": "This is a test notification"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| channel | string | Notification channel to test (inApp, email, push, all) | Yes |
| message | string | Test message content | Yes |

**Responses**:

`200 OK` - Delivery status

```json
{
  "success": true,
  "deliveryStatus": {
    "inApp": "not_attempted",
    "email": "delivered",
    "push": "not_attempted"
  }
}
```

`400 Bad Request` - Invalid request

## Data Models

### Notification

```json
{
  "id": "string (UUID)",
  "recipient": "string (User reference)",
  "type": "string (enum: TASK_ASSIGNED, TASK_DUE_SOON, TASK_OVERDUE, COMMENT_ADDED, MENTION, PROJECT_INVITATION, STATUS_CHANGE)",
  "title": "string",
  "content": "string",
  "priority": "string (enum: low, normal, high, urgent)",
  "read": "boolean",
  "actionUrl": "string (URL to relevant content)",
  "metadata": {
    "created": "string (ISO date-time)",
    "readAt": "string (ISO date-time) or null",
    "deliveryStatus": {
      "inApp": "string (enum: delivered, failed, pending, disabled)",
      "email": "string (enum: delivered, failed, pending, disabled)",
      "push": "string (enum: delivered, failed, pending, disabled)"
    },
    "sourceEvent": {
      "type": "string (event type)",
      "objectId": "string (related object ID)",
      "objectType": "string (object type)"
    }
  }
}
```

### NotificationPreferences

```json
{
  "globalSettings": {
    "inApp": "boolean",
    "email": "boolean",
    "push": "boolean",
    "digest": {
      "enabled": "boolean",
      "frequency": "string (enum: daily, weekly)"
    }
  },
  "typeSettings": {
    "<notification-type>": {
      "inApp": "boolean",
      "email": "boolean",
      "push": "boolean"
    }
  },
  "projectSettings": {
    "<project-id>": {
      "inApp": "boolean",
      "email": "boolean",
      "push": "boolean"
    }
  },
  "quietHours": {
    "enabled": "boolean",
    "start": "string (time format HH:MM)",
    "end": "string (time format HH:MM)",
    "timezone": "string (IANA timezone format)",
    "excludeUrgent": "boolean"
  }
}
```

### UnreadCount

```json
{
  "total": "integer",
  "byType": {
    "<notification-type>": "integer"
  }
}
```

### TestNotificationRequest

```json
{
  "channel": "string (enum: inApp, email, push, all)",
  "message": "string"
}
```

## Examples

### List Notifications Example

**Request**:

```
GET /api/v1/notifications?page=1&limit=10
Authorization: Bearer {token}
```

**Response**:

```json
{
  "data": [
    {
      "id": "60a3d1b4c7d8b92a5c9f1234",
      "recipient": "user_123",
      "type": "TASK_ASSIGNED",
      "title": "New task assigned",
      "content": "You have been assigned to 'Create wireframes'",
      "priority": "normal",
      "read": false,
      "actionUrl": "/tasks/task_456",
      "metadata": {
        "created": "2023-02-15T10:30:00Z",
        "readAt": null,
        "deliveryStatus": {
          "inApp": "delivered",
          "email": "delivered",
          "push": "disabled"
        },
        "sourceEvent": {
          "type": "task.assigned",
          "objectId": "task_456",
          "objectType": "task"
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5
  }
}
```

### Get Notification Preferences Example

**Request**:

```
GET /api/v1/notifications/preferences
Authorization: Bearer {token}
```

**Response**:

```json
{
  "globalSettings": {
    "inApp": true,
    "email": true,
    "push": false,
    "digest": {
      "enabled": true,
      "frequency": "daily"
    }
  },
  "typeSettings": {
    "TASK_ASSIGNED": {
      "inApp": true,
      "email": true,
      "push": true
    },
    "COMMENT_ADDED": {
      "inApp": true,
      "email": false,
      "push": false
    }
  },
  "projectSettings": {
    "project-123": {
      "inApp": true,
      "email": true,
      "push": true
    }
  },
  "quietHours": {
    "enabled": true,
    "start": "18:00",
    "end": "09:00",
    "timezone": "America/New_York",
    "excludeUrgent": true
  }
}
```

## Error Responses

This API uses conventional HTTP response codes to indicate the success or failure of requests. In general, codes in the 2xx range indicate success, codes in the 4xx range indicate an error that failed given the information provided, and codes in the 5xx range indicate an error with the server.

Common error codes include:

| Code | Description |
|------|-------------|
| 400 | Bad Request - The request was malformed or contains invalid parameters |
| 401 | Unauthorized - Authentication is required or the provided credentials are invalid |
| 403 | Forbidden - The authenticated user does not have permission to access the resource |
| 404 | Not Found - The requested resource does not exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - An unexpected error occurred on the server |

Error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field1": ["Error detail for field1"],
      "field2": ["Error detail for field2"]
    }
  }
}
```