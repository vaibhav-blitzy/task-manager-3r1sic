# Task Management API

The Task Management API provides comprehensive endpoints for creating, retrieving, updating, and deleting tasks, as well as specialized operations like task assignment, status changes, subtask management, and dependency tracking.

## Base URL

All task endpoints are relative to: `/api/v1/tasks`

## Authentication

All task endpoints require authentication using a valid JWT token (except where noted).

Include the token in the Authorization header: `Authorization: Bearer {access_token}`

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Task Object

The Task object has the following structure:

| Field | Description |
|-------|-------------|
| id | string - Unique task identifier |
| title | string - Task title |
| description | string - Task description (may contain markdown) |
| status | string - Task status (created, assigned, in_progress, on_hold, in_review, completed, cancelled) |
| priority | string - Task priority (low, medium, high, urgent) |
| dueDate | string (ISO 8601) - Task due date |
| createdBy | object - User who created the task |
| createdBy.id | string - User ID of creator |
| createdBy.name | string - Display name of creator |
| assignee | object - User assigned to the task |
| assignee.id | string - User ID of assignee |
| assignee.name | string - Display name of assignee |
| project | object - Project the task belongs to |
| project.id | string - Project ID |
| project.name | string - Project name |
| tags | array of strings - Task tags |
| subtasks | array of objects - Subtasks associated with the task |
| dependencies | array of objects - Task dependencies |
| attachments | array of objects - Task attachments |
| metadata | object - Task metadata |
| completionPercentage | number - Task completion percentage (0-100) |

### Example Task Object

```json
{
  "id": "task_01234567890abcdef",
  "title": "Create wireframes for dashboard",
  "description": "Design wireframes for the main dashboard view including all widgets and responsive layouts.",
  "status": "in_progress",
  "priority": "high",
  "dueDate": "2023-06-15T23:59:59Z",
  "createdBy": {
    "id": "user_abcdef1234567890",
    "name": "John Doe"
  },
  "assignee": {
    "id": "user_bcdef1234567890a",
    "name": "Sarah Johnson"
  },
  "project": {
    "id": "project_cdef1234567890ab",
    "name": "Website Redesign"
  },
  "tags": ["design", "ui", "dashboard"],
  "subtasks": [
    {
      "id": "subtask_def1234567890abc",
      "title": "Research dashboard patterns",
      "completed": true,
      "assignee": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson"
      }
    },
    {
      "id": "subtask_ef1234567890abcd",
      "title": "Create mobile wireframes",
      "completed": false,
      "assignee": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson"
      }
    }
  ],
  "dependencies": [
    {
      "taskId": "task_f1234567890abcde",
      "type": "blocked_by"
    }
  ],
  "attachments": [
    {
      "id": "file_1234567890abcdef",
      "name": "dashboard-inspiration.jpg",
      "size": 2048576,
      "type": "image/jpeg",
      "uploadedBy": {
        "id": "user_abcdef1234567890",
        "name": "John Doe"
      },
      "uploadedAt": "2023-06-01T14:30:00Z"
    }
  ],
  "metadata": {
    "createdAt": "2023-06-01T10:00:00Z",
    "updatedAt": "2023-06-05T15:30:00Z",
    "completedAt": null,
    "timeEstimate": 480,
    "timeSpent": 240
  },
  "completionPercentage": 50
}
```

## Task Status Flow

Tasks follow a specific state workflow with allowed transitions:

| Status | Description | Allowed Transitions |
|--------|-------------|---------------------|
| created | Initial status when a task is created but not yet assigned or started | assigned, in_progress, cancelled |
| assigned | Task has been assigned to a user but work has not started | in_progress, on_hold, cancelled |
| in_progress | Work on the task has begun | on_hold, in_review, completed, cancelled |
| on_hold | Task work has been paused temporarily | in_progress, cancelled |
| in_review | Task implementation is complete and awaiting review | in_progress, completed, cancelled |
| completed | Task has been fully completed and verified | (none) |
| cancelled | Task has been cancelled and will not be completed | (none) |

## Endpoints

### List Tasks

> `GET /api/v1/tasks`

Retrieves a paginated list of tasks with filtering options.

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| page | integer | Page number (starting from 1) | 1 | No |
| per_page | integer | Number of items per page (max 100) | 20 | No |
| status | string | Filter by task status (comma-separated for multiple) | | No |
| priority | string | Filter by task priority (comma-separated for multiple) | | No |
| assignee_id | string | Filter by assignee | | No |
| project_id | string | Filter by project | | No |
| due_date_start | string (ISO 8601) | Filter by due date range (start) | | No |
| due_date_end | string (ISO 8601) | Filter by due date range (end) | | No |
| tags | string | Filter by tags (comma-separated) | | No |
| sort_by | string | Field to sort by (due_date, priority, created_at, updated_at) | created_at | No |
| sort_dir | string | Sort direction (asc, desc) | desc | No |

#### Response

`200 OK`

```json
{
  "data": [
    {
      "id": "task_01234567890abcdef",
      "title": "Create wireframes for dashboard",
      "status": "in_progress",
      "priority": "high",
      "dueDate": "2023-06-15T23:59:59Z",
      "assignee": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson"
      },
      "project": {
        "id": "project_cdef1234567890ab",
        "name": "Website Redesign"
      },
      "metadata": {
        "createdAt": "2023-06-01T10:00:00Z",
        "updatedAt": "2023-06-05T15:30:00Z"
      },
      "completionPercentage": 50
    }
  ],
  "pagination": {
    "total": 42,
    "pages": 3,
    "page": 1,
    "per_page": 20
  }
}
```

`401 Unauthorized`

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid filter parameters",
    "details": {
      "status": "Invalid status value: 'pending'"
    }
  }
}
```

### Create Task

> `POST /api/v1/tasks`

Creates a new task.

#### Request Body

```json
{
  "title": "Create wireframes for dashboard",
  "description": "Design wireframes for the main dashboard view including all widgets and responsive layouts.",
  "status": "assigned",
  "priority": "high",
  "dueDate": "2023-06-15T23:59:59Z",
  "assigneeId": "user_bcdef1234567890a",
  "projectId": "project_cdef1234567890ab",
  "tags": ["design", "ui", "dashboard"],
  "timeEstimate": 480
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "description": "Design wireframes for the main dashboard view including all widgets and responsive layouts.",
    "status": "assigned",
    "priority": "high",
    "dueDate": "2023-06-15T23:59:59Z",
    "createdBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "project": {
      "id": "project_cdef1234567890ab",
      "name": "Website Redesign"
    },
    "tags": ["design", "ui", "dashboard"],
    "subtasks": [],
    "dependencies": [],
    "attachments": [],
    "metadata": {
      "createdAt": "2023-06-01T10:00:00Z",
      "updatedAt": "2023-06-01T10:00:00Z",
      "completedAt": null,
      "timeEstimate": 480,
      "timeSpent": 0
    },
    "completionPercentage": 0
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Task validation failed",
    "details": {
      "title": ["Title is required"],
      "status": ["Invalid status value"],
      "dueDate": ["Due date must be in the future"]
    }
  }
}
```

### Get Task Details

> `GET /api/v1/tasks/{task_id}`

Retrieves detailed information about a specific task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Response

`200 OK`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "description": "Design wireframes for the main dashboard view including all widgets and responsive layouts.",
    "status": "in_progress",
    "priority": "high",
    "dueDate": "2023-06-15T23:59:59Z",
    "createdBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "project": {
      "id": "project_cdef1234567890ab",
      "name": "Website Redesign"
    },
    "tags": ["design", "ui", "dashboard"],
    "subtasks": [
      {
        "id": "subtask_def1234567890abc",
        "title": "Research dashboard patterns",
        "completed": true,
        "assignee": {
          "id": "user_bcdef1234567890a",
          "name": "Sarah Johnson"
        }
      },
      {
        "id": "subtask_ef1234567890abcd",
        "title": "Create mobile wireframes",
        "completed": false,
        "assignee": {
          "id": "user_bcdef1234567890a",
          "name": "Sarah Johnson"
        }
      }
    ],
    "dependencies": [
      {
        "taskId": "task_f1234567890abcde",
        "type": "blocked_by"
      }
    ],
    "attachments": [
      {
        "id": "file_1234567890abcdef",
        "name": "dashboard-inspiration.jpg",
        "size": 2048576,
        "type": "image/jpeg",
        "uploadedBy": {
          "id": "user_abcdef1234567890",
          "name": "John Doe"
        },
        "uploadedAt": "2023-06-01T14:30:00Z"
      }
    ],
    "metadata": {
      "createdAt": "2023-06-01T10:00:00Z",
      "updatedAt": "2023-06-05T15:30:00Z",
      "completedAt": null,
      "timeEstimate": 480,
      "timeSpent": 240
    },
    "completionPercentage": 50
  }
}
```

`404 Not Found`

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Task not found"
  }
}
```

### Update Task

> `PUT /api/v1/tasks/{task_id}`

Updates an existing task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "title": "Create wireframes for dashboard (updated)",
  "description": "Updated description with more details about responsive design requirements",
  "priority": "urgent",
  "dueDate": "2023-06-20T23:59:59Z",
  "tags": ["design", "ui", "dashboard", "responsive"],
  "timeEstimate": 600
}
```

#### Response

`200 OK`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard (updated)",
    "description": "Updated description with more details about responsive design requirements",
    "status": "in_progress",
    "priority": "urgent",
    "dueDate": "2023-06-20T23:59:59Z",
    "createdBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "project": {
      "id": "project_cdef1234567890ab",
      "name": "Website Redesign"
    },
    "tags": ["design", "ui", "dashboard", "responsive"],
    "metadata": {
      "createdAt": "2023-06-01T10:00:00Z",
      "updatedAt": "2023-06-05T16:45:00Z",
      "completedAt": null,
      "timeEstimate": 600,
      "timeSpent": 240
    }
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Task validation failed",
    "details": {
      "dueDate": ["Due date must be in the future"]
    }
  }
}
```

### Delete Task

> `DELETE /api/v1/tasks/{task_id}`

Deletes a task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Response

`200 OK`

```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

`404 Not Found`

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Task not found"
  }
}
```

### Update Task Status

> `PATCH /api/v1/tasks/{task_id}/status`

Updates the status of a task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "status": "completed",
  "comment": "All wireframes are finished and approved"
}
```

#### Response

`200 OK`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "status": "completed",
    "priority": "high",
    "dueDate": "2023-06-15T23:59:59Z",
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "metadata": {
      "createdAt": "2023-06-01T10:00:00Z",
      "updatedAt": "2023-06-10T16:30:00Z",
      "completedAt": "2023-06-10T16:30:00Z"
    },
    "completionPercentage": 100
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition from 'completed' to 'in_progress'",
    "details": {
      "currentStatus": "completed",
      "requestedStatus": "in_progress",
      "allowedTransitions": []
    }
  }
}
```

### Assign Task

> `PATCH /api/v1/tasks/{task_id}/assign`

Assigns a task to a user.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "assigneeId": "user_def1234567890abc"
}
```

#### Response

`200 OK`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "status": "assigned",
    "assignee": {
      "id": "user_def1234567890abc",
      "name": "Michael Brown"
    },
    "metadata": {
      "updatedAt": "2023-06-07T09:15:00Z"
    }
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "INVALID_USER",
    "message": "The specified user does not exist or is not a member of the project"
  }
}
```

### Get Tasks By Project

> `GET /api/v1/tasks/project/{project_id}`

Retrieves tasks belonging to a specific project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| page | integer | Page number | 1 | No |
| per_page | integer | Number of items per page (max 100) | 20 | No |
| status | string | Filter by task status (comma-separated for multiple) | | No |
| sort_by | string | Field to sort by | priority | No |
| sort_dir | string | Sort direction (asc, desc) | asc | No |

#### Response

`200 OK`

```json
{
  "data": [
    {
      "id": "task_01234567890abcdef",
      "title": "Create wireframes for dashboard",
      "status": "in_progress",
      "priority": "high",
      "dueDate": "2023-06-15T23:59:59Z",
      "assignee": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson"
      }
    }
  ],
  "pagination": {
    "total": 15,
    "pages": 1,
    "page": 1,
    "per_page": 20
  }
}
```

### Search Tasks

> `GET /api/v1/tasks/search`

Searches for tasks with complex filtering.

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| q | string | Search query (searches title and description) | | No |
| page | integer | Page number | 1 | No |
| per_page | integer | Number of items per page (max 100) | 20 | No |
| status | string | Filter by task status (comma-separated for multiple) | | No |
| priority | string | Filter by task priority (comma-separated for multiple) | | No |
| assignee_id | string | Filter by assignee | | No |
| created_by | string | Filter by creator | | No |
| tags | string | Filter by tags (comma-separated) | | No |
| created_after | string (ISO 8601) | Filter by creation date (after) | | No |
| created_before | string (ISO 8601) | Filter by creation date (before) | | No |
| updated_after | string (ISO 8601) | Filter by update date (after) | | No |
| updated_before | string (ISO 8601) | Filter by update date (before) | | No |

#### Response

`200 OK`

```json
{
  "data": [
    {
      "id": "task_01234567890abcdef",
      "title": "Create wireframes for dashboard",
      "status": "in_progress",
      "priority": "high",
      "dueDate": "2023-06-15T23:59:59Z"
    }
  ],
  "pagination": {
    "total": 3,
    "pages": 1,
    "page": 1,
    "per_page": 20
  }
}
```

### Add Subtask

> `POST /api/v1/tasks/{task_id}/subtasks`

Adds a subtask to an existing task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "title": "Create mobile wireframes",
  "assigneeId": "user_bcdef1234567890a"
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "id": "subtask_ef1234567890abcd",
    "title": "Create mobile wireframes",
    "completed": false,
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    }
  }
}
```

### Update Subtask

> `PUT /api/v1/tasks/{task_id}/subtasks/{subtask_id}`

Updates an existing subtask.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |
| subtask_id | string | Subtask identifier | Yes |

#### Request Body

```json
{
  "title": "Create mobile wireframes (updated)",
  "completed": true
}
```

#### Response

`200 OK`

```json
{
  "data": {
    "id": "subtask_ef1234567890abcd",
    "title": "Create mobile wireframes (updated)",
    "completed": true,
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    }
  }
}
```

### Add Task Dependency

> `POST /api/v1/tasks/{task_id}/dependencies`

Adds a dependency relationship between tasks.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "dependencyTaskId": "task_f1234567890abcde",
  "dependencyType": "blocked_by"
}
```

#### Response

`200 OK`

```json
{
  "data": {
    "id": "task_01234567890abcdef",
    "dependencies": [
      {
        "taskId": "task_f1234567890abcde",
        "type": "blocked_by"
      }
    ]
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "CIRCULAR_DEPENDENCY",
    "message": "Adding this dependency would create a circular reference",
    "details": {
      "path": ["task_01234567890abcdef", "task_f1234567890abcde", "task_01234567890abcdef"]
    }
  }
}
```

### Add Task Attachment

> `POST /api/v1/tasks/{task_id}/attachments`

Adds a file attachment to a task.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| task_id | string | Task identifier | Yes |

#### Request Body

```json
{
  "fileId": "file_1234567890abcdef",
  "fileName": "dashboard-inspiration.jpg"
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "id": "file_1234567890abcdef",
    "name": "dashboard-inspiration.jpg",
    "size": 2048576,
    "type": "image/jpeg",
    "uploadedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "uploadedAt": "2023-06-01T14:30:00Z"
  }
}
```

## Error Handling

The Task API uses standard HTTP status codes and provides detailed error responses. Common error codes include:

| Code | Description | HTTP Status |
|------|-------------|-------------|
| VALIDATION_ERROR | Request data failed validation | 400 |
| RESOURCE_NOT_FOUND | Requested task or related resource not found | 404 |
| UNAUTHORIZED | Authentication required or token invalid | 401 |
| FORBIDDEN | User doesn't have permission for the requested operation | 403 |
| INVALID_STATUS_TRANSITION | Attempted status change is not allowed | 400 |
| CIRCULAR_DEPENDENCY | Requested dependency would create a circular reference | 400 |
| INVALID_USER | Referenced user doesn't exist or lacks required permissions | 400 |

## Examples

### Create a New Task

```javascript
const createTask = async () => {
  try {
    const response = await fetch('https://api.taskmanagementsystem.com/api/v1/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        title: 'Create wireframes for dashboard',
        description: 'Design wireframes for the main dashboard view including all widgets and responsive layouts.',
        priority: 'high',
        dueDate: '2023-06-15T23:59:59Z',
        assigneeId: 'user_bcdef1234567890a',
        projectId: 'project_cdef1234567890ab',
        tags: ['design', 'ui', 'dashboard']
      })
    });
    
    const data = await response.json();
    console.log('Task created:', data);
    return data;
  } catch (error) {
    console.error('Error creating task:', error);
  }
};
```

### Update Task Status

```javascript
const updateTaskStatus = async (taskId, newStatus) => {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/api/v1/tasks/${taskId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        status: newStatus,
        comment: 'Updating task status'
      })
    });
    
    const data = await response.json();
    console.log('Task status updated:', data);
    return data;
  } catch (error) {
    console.error('Error updating task status:', error);
  }
};
```

### Get Tasks for a Project

```javascript
const getProjectTasks = async (projectId, status = '') => {
  try {
    const url = new URL(`https://api.taskmanagementsystem.com/api/v1/tasks/project/${projectId}`);
    
    if (status) {
      url.searchParams.append('status', status);
    }
    
    url.searchParams.append('sort_by', 'dueDate');
    url.searchParams.append('sort_dir', 'asc');
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    const data = await response.json();
    console.log('Project tasks:', data);
    return data;
  } catch (error) {
    console.error('Error fetching project tasks:', error);
  }
};
```

### Add a Subtask

```javascript
const addSubtask = async (taskId, subtaskTitle, assigneeId) => {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/api/v1/tasks/${taskId}/subtasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        title: subtaskTitle,
        assigneeId: assigneeId
      })
    });
    
    const data = await response.json();
    console.log('Subtask added:', data);
    return data;
  } catch (error) {
    console.error('Error adding subtask:', error);
  }
};
```

## Rate Limiting

The Task API implements rate limiting to prevent abuse and ensure system stability:

| Endpoint | Limit |
|----------|-------|
| GET endpoints | 60 requests per minute per user |
| POST/PUT/PATCH/DELETE endpoints | 30 requests per minute per user |

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a Retry-After header indicating when to retry.

## Webhooks

You can configure webhooks to receive real-time notifications when tasks are created, updated, or deleted. The following task-related events are available for webhook subscriptions:

### task.created

Triggered when a new task is created.

```json
{
  "event": "task.created",
  "timestamp": "2023-06-01T10:00:00Z",
  "data": {
    "taskId": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "projectId": "project_cdef1234567890ab",
    "createdBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

### task.updated

Triggered when a task is updated.

```json
{
  "event": "task.updated",
  "timestamp": "2023-06-05T15:30:00Z",
  "data": {
    "taskId": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "updatedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "changes": {
      "priority": {
        "from": "medium",
        "to": "high"
      },
      "dueDate": {
        "from": "2023-06-10T23:59:59Z",
        "to": "2023-06-15T23:59:59Z"
      }
    }
  }
}
```

### task.status_changed

Triggered when a task's status changes.

```json
{
  "event": "task.status_changed",
  "timestamp": "2023-06-07T11:45:00Z",
  "data": {
    "taskId": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "previousStatus": "assigned",
    "newStatus": "in_progress",
    "changedBy": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    }
  }
}
```

### task.assigned

Triggered when a task is assigned.

```json
{
  "event": "task.assigned",
  "timestamp": "2023-06-01T10:30:00Z",
  "data": {
    "taskId": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "assignee": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "assignedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

### task.completed

Triggered when a task is marked as completed.

```json
{
  "event": "task.completed",
  "timestamp": "2023-06-10T16:30:00Z",
  "data": {
    "taskId": "task_01234567890abcdef",
    "title": "Create wireframes for dashboard",
    "completedBy": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "completedAt": "2023-06-10T16:30:00Z"
  }
}
```

## Related Resources

The following related API documentation may be useful:

- [Authentication API](auth.md) - User authentication and token management
- [Project API](projects.md) - Project management and organization
- [Comment API](tasks.md#comments) - Task comments and discussions
- [File Management API](files.md) - File uploads and attachment management