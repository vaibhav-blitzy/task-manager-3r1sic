# Project Management API

The Project Management API provides comprehensive endpoints for creating, retrieving, updating, and deleting projects, as well as managing project members, task lists, and project settings.

## Base URL

All project endpoints are relative to: `/api/v1/projects`

## Authentication

All project endpoints require authentication using a valid JWT token.

Include the token in the Authorization header: `Authorization: Bearer {access_token}`

See the [Authentication API](auth.md) documentation for details on obtaining tokens.

## Project Object

The Project object has the following structure:

| Field | Description |
|-------|-------------|
| id | string - Unique project identifier |
| name | string - Project name |
| description | string - Project description (may contain markdown) |
| status | string - Project status (planning, active, on_hold, completed, archived) |
| category | string - Project category |
| owner | object - User who owns the project |
| owner.id | string - User ID of owner |
| owner.name | string - Display name of owner |
| members | array of objects - Users with access to the project |
| members[].userId | string - User ID |
| members[].user | object - User details |
| members[].role | string - Role (admin, manager, member, viewer) |
| members[].joinedAt | string (ISO 8601) - Timestamp when user joined project |
| members[].isActive | boolean - Whether the member is active |
| settings | object - Project configuration settings |
| settings.workflow | object - Workflow configuration |
| settings.permissions | object - Permission configuration |
| settings.notifications | object - Notification preferences |
| taskLists | array of objects - Lists to organize tasks |
| metadata | object - Project metadata |
| tags | array of strings - Project tags |
| customFields | array of objects - Custom field definitions |
| completionPercentage | number - Project completion percentage (0-100) |

### Example Project Object

```json
{
  "id": "project_01234567890abcdef",
  "name": "Website Redesign",
  "description": "Complete overhaul of company website with new branding and improved UX.",
  "status": "active",
  "category": "Marketing",
  "owner": {
    "id": "user_abcdef1234567890",
    "name": "John Doe"
  },
  "members": [
    {
      "userId": "user_abcdef1234567890",
      "user": {
        "id": "user_abcdef1234567890",
        "name": "John Doe"
      },
      "role": "admin",
      "joinedAt": "2023-05-15T10:00:00Z",
      "isActive": true
    },
    {
      "userId": "user_bcdef1234567890a",
      "user": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson"
      },
      "role": "member",
      "joinedAt": "2023-05-16T14:30:00Z",
      "isActive": true
    }
  ],
  "settings": {
    "workflow": {
      "enableReview": true,
      "allowSubtasks": true,
      "defaultTaskStatus": "created"
    },
    "permissions": {
      "memberInvite": "admin",
      "taskCreate": "member",
      "commentCreate": "member"
    },
    "notifications": {
      "taskCreate": true,
      "taskComplete": true,
      "commentAdd": true
    }
  },
  "taskLists": [
    {
      "id": "tasklist_abcdef1234567890",
      "name": "Design Tasks",
      "description": "UI/UX design tasks for the website",
      "sortOrder": 1,
      "createdAt": "2023-05-15T10:30:00Z"
    },
    {
      "id": "tasklist_bcdef1234567890a",
      "name": "Development Tasks",
      "description": "Frontend and backend implementation tasks",
      "sortOrder": 2,
      "createdAt": "2023-05-15T10:35:00Z"
    }
  ],
  "metadata": {
    "created": "2023-05-15T10:00:00Z",
    "lastUpdated": "2023-06-01T14:25:00Z",
    "completedAt": null,
    "taskCount": 24,
    "completedTaskCount": 10
  },
  "tags": ["website", "design", "marketing"],
  "customFields": [
    {
      "id": "customfield_12345",
      "name": "Client",
      "type": "text",
      "options": []
    },
    {
      "id": "customfield_67890",
      "name": "Priority",
      "type": "select",
      "options": ["Low", "Medium", "High"]
    }
  ],
  "completionPercentage": 42
}
```

## Project Status Flow

Projects follow a specific state workflow with allowed transitions:

| Status | Description | Allowed Transitions |
|--------|-------------|---------------------|
| planning | Initial project setup and planning phase | active, on_hold, archived |
| active | Project is currently in progress with active work | on_hold, completed, archived |
| on_hold | Project work has been temporarily paused | active, archived |
| completed | Project has been successfully completed | archived |
| archived | Project is archived and no longer active | (none) |

## Project Endpoints

### List Projects

> `GET /api/v1/projects`

Retrieves a paginated list of projects with filtering options.

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| page | integer | Page number (starting from 1) | 1 | No |
| per_page | integer | Number of items per page | 20 | No |
| status | string | Filter by project status (comma-separated for multiple) | | No |
| category | string | Filter by project category | | No |
| tags | string | Filter by tags (comma-separated) | | No |
| sort_by | string | Field to sort by (name, created_at, updated_at, status) | updated_at | No |
| sort_dir | string | Sort direction (asc, desc) | desc | No |

#### Response

`200 OK`

```json
{
  "data": [
    {
      "id": "project_01234567890abcdef",
      "name": "Website Redesign",
      "description": "Complete overhaul of company website",
      "status": "active",
      "category": "Marketing",
      "owner": {
        "id": "user_abcdef1234567890",
        "name": "John Doe"
      },
      "metadata": {
        "created": "2023-05-15T10:00:00Z",
        "lastUpdated": "2023-06-01T14:25:00Z"
      },
      "completionPercentage": 42
    },
    {
      "id": "project_12345678901234567",
      "name": "Mobile App Development",
      "description": "Create mobile app for customers",
      "status": "planning",
      "category": "Development",
      "owner": {
        "id": "user_abcdef1234567890",
        "name": "John Doe"
      },
      "metadata": {
        "created": "2023-06-01T09:00:00Z",
        "lastUpdated": "2023-06-01T09:00:00Z"
      },
      "completionPercentage": 0
    }
  ],
  "pagination": {
    "total": 12,
    "pages": 1,
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

### Create Project

> `POST /api/v1/projects`

Creates a new project.

#### Request Body

```json
{
  "name": "Website Redesign",
  "description": "Complete overhaul of company website with new branding and improved UX.",
  "status": "planning",
  "category": "Marketing",
  "tags": ["website", "design", "marketing"]
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "id": "project_01234567890abcdef",
    "name": "Website Redesign",
    "description": "Complete overhaul of company website with new branding and improved UX.",
    "status": "planning",
    "category": "Marketing",
    "owner": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "members": [
      {
        "userId": "user_abcdef1234567890",
        "user": {
          "id": "user_abcdef1234567890",
          "name": "John Doe"
        },
        "role": "admin",
        "joinedAt": "2023-05-15T10:00:00Z",
        "isActive": true
      }
    ],
    "settings": {
      "workflow": {
        "enableReview": true,
        "allowSubtasks": true,
        "defaultTaskStatus": "created"
      },
      "permissions": {
        "memberInvite": "admin",
        "taskCreate": "member",
        "commentCreate": "member"
      },
      "notifications": {
        "taskCreate": true,
        "taskComplete": true,
        "commentAdd": true
      }
    },
    "taskLists": [],
    "metadata": {
      "created": "2023-05-15T10:00:00Z",
      "lastUpdated": "2023-05-15T10:00:00Z",
      "completedAt": null,
      "taskCount": 0,
      "completedTaskCount": 0
    },
    "tags": ["website", "design", "marketing"],
    "customFields": [],
    "completionPercentage": 0
  }
}
```

`400 Bad Request`

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Project validation failed",
    "details": {
      "name": ["Name is required"],
      "status": ["Invalid status value"]
    }
  }
}
```

### Get Project Details

> `GET /api/v1/projects/{project_id}`

Retrieves detailed information about a specific project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Response

`200 OK` - Returns the complete project object as shown in the Project Object section

`404 Not Found`

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project not found"
  }
}
```

`403 Forbidden`

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions to access this project"
  }
}
```

### Update Project

> `PUT /api/v1/projects/{project_id}`

Updates an existing project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Request Body

```json
{
  "name": "Website Redesign and Migration",
  "description": "Updated project description with migration details",
  "category": "Marketing",
  "tags": ["website", "design", "marketing", "migration"]
}
```

#### Response

`200 OK` - Returns the updated project object

`400 Bad Request` - If validation fails with detailed errors

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to update the project

### Delete Project

> `DELETE /api/v1/projects/{project_id}`

Deletes a project (archives it rather than permanent deletion).

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Response

`200 OK`

```json
{
  "success": true,
  "message": "Project archived successfully"
}
```

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to delete the project

### Update Project Status

> `PATCH /api/v1/projects/{project_id}/status`

Updates the status of a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Request Body

```json
{
  "status": "active"
}
```

#### Response

`200 OK` - Returns the updated project object

`400 Bad Request`

```json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition from 'completed' to 'planning'",
    "details": {
      "currentStatus": "completed",
      "requestedStatus": "planning",
      "allowedTransitions": ["archived"]
    }
  }
}
```

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to update the project's status

### Get Project Statistics

> `GET /api/v1/projects/{project_id}/stats`

Retrieves statistics and metrics for a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Response

`200 OK`

```json
{
  "data": {
    "taskCompletionRate": 42,
    "onTimeCompletionRate": 85,
    "tasksByStatus": {
      "created": 5,
      "assigned": 3,
      "in_progress": 6,
      "completed": 10
    },
    "tasksByAssignee": {
      "user_bcdef1234567890a": 8,
      "user_cdef1234567890ab": 12,
      "unassigned": 4
    },
    "activitiesLastWeek": 37,
    "overdueTasks": 2
  }
}
```

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to access the project

### Search Projects

> `GET /api/v1/projects/search`

Searches for projects by text query.

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| q | string | Search query string | | Yes |
| page | integer | Page number | 1 | No |
| per_page | integer | Items per page | 20 | No |
| status | string | Filter by status | | No |
| category | string | Filter by category | | No |

#### Response

`200 OK` - Returns a paginated list of matching projects

`400 Bad Request` - If search parameters are invalid

## Task List Endpoints

### Add Task List

> `POST /api/v1/projects/{project_id}/tasklists`

Adds a new task list to a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Request Body

```json
{
  "name": "Backend Development",
  "description": "Tasks related to backend API development"
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "id": "tasklist_def1234567890abc",
    "name": "Backend Development",
    "description": "Tasks related to backend API development",
    "sortOrder": 3,
    "createdAt": "2023-06-02T11:00:00Z"
  }
}
```

`400 Bad Request` - If validation fails

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to modify the project

### Update Task List

> `PUT /api/v1/projects/{project_id}/tasklists/{task_list_id}`

Updates an existing task list.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |
| task_list_id | string | Task list identifier | Yes |

#### Request Body

```json
{
  "name": "Backend API Development",
  "description": "Updated description with more details",
  "sortOrder": 2
}
```

#### Response

`200 OK` - Returns the updated task list

`404 Not Found` - If the project or task list doesn't exist

`403 Forbidden` - If user lacks permissions to modify the project

### Delete Task List

> `DELETE /api/v1/projects/{project_id}/tasklists/{task_list_id}`

Removes a task list from a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |
| task_list_id | string | Task list identifier | Yes |

#### Response

`200 OK`

```json
{
  "success": true,
  "message": "Task list removed successfully"
}
```

`404 Not Found` - If the project or task list doesn't exist

`403 Forbidden` - If user lacks permissions to modify the project

## Project Settings Endpoints

### Update Project Settings

> `PUT /api/v1/projects/{project_id}/settings`

Updates project settings.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Request Body

```json
{
  "workflow": {
    "enableReview": true,
    "allowSubtasks": true,
    "defaultTaskStatus": "assigned"
  },
  "permissions": {
    "memberInvite": "admin",
    "taskCreate": "member",
    "commentCreate": "viewer"
  },
  "notifications": {
    "taskCreate": true,
    "taskComplete": false,
    "commentAdd": true
  }
}
```

#### Response

`200 OK` - Returns the updated project settings

`400 Bad Request` - If validation fails

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to modify project settings

## Member Object

The Project Member object has the following structure:

| Field | Description |
|-------|-------------|
| userId | string - ID of the member user |
| user | object - User details |
| user.id | string - User ID |
| user.name | string - User display name |
| user.email | string - User email address |
| role | string - Role in the project (admin, manager, member, viewer) |
| joinedAt | string (ISO 8601) - Timestamp when the user joined |
| isActive | boolean - Whether the member is active in the project |

### Example Member Object

```json
{
  "userId": "user_bcdef1234567890a",
  "user": {
    "id": "user_bcdef1234567890a",
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com"
  },
  "role": "member",
  "joinedAt": "2023-05-16T14:30:00Z",
  "isActive": true
}
```

## Project Member Endpoints

### List Project Members

> `GET /api/v1/projects/{project_id}/members`

Retrieves a list of project members.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Query Parameters

| Parameter | Type | Description | Default | Required |
|-----------|------|-------------|---------|----------|
| page | integer | Page number | 1 | No |
| per_page | integer | Items per page | 20 | No |
| role | string | Filter by role | | No |

#### Response

`200 OK`

```json
{
  "data": [
    {
      "userId": "user_abcdef1234567890",
      "user": {
        "id": "user_abcdef1234567890",
        "name": "John Doe",
        "email": "john.doe@example.com"
      },
      "role": "admin",
      "joinedAt": "2023-05-15T10:00:00Z",
      "isActive": true
    },
    {
      "userId": "user_bcdef1234567890a",
      "user": {
        "id": "user_bcdef1234567890a",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@example.com"
      },
      "role": "member",
      "joinedAt": "2023-05-16T14:30:00Z",
      "isActive": true
    }
  ],
  "pagination": {
    "total": 2,
    "pages": 1,
    "page": 1,
    "per_page": 20
  }
}
```

`404 Not Found` - If the project doesn't exist

`403 Forbidden` - If user lacks permissions to access the project

### Add Project Member

> `POST /api/v1/projects/{project_id}/members`

Adds a user as a member to a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Request Body

```json
{
  "userId": "user_cdef1234567890ab",
  "role": "member"
}
```

#### Response

`201 Created`

```json
{
  "data": {
    "userId": "user_cdef1234567890ab",
    "user": {
      "id": "user_cdef1234567890ab",
      "name": "Michael Brown",
      "email": "michael.brown@example.com"
    },
    "role": "member",
    "joinedAt": "2023-06-02T16:45:00Z",
    "isActive": true
  }
}
```

`400 Bad Request` - If validation fails

`404 Not Found` - If the project or user doesn't exist

`409 Conflict`

```json
{
  "error": {
    "code": "MEMBER_ALREADY_EXISTS",
    "message": "User is already a member of this project"
  }
}
```

`403 Forbidden` - If user lacks permissions to manage project members

### Get Project Member

> `GET /api/v1/projects/{project_id}/members/{member_id}`

Retrieves details about a specific project member.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |
| member_id | string | Member identifier | Yes |

#### Response

`200 OK` - Returns the member object

`404 Not Found` - If the project or member doesn't exist

`403 Forbidden` - If user lacks permissions to access the project

### Update Project Member

> `PATCH /api/v1/projects/{project_id}/members/{member_id}`

Updates a project member's role.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |
| member_id | string | Member identifier | Yes |

#### Request Body

```json
{
  "role": "manager"
}
```

#### Response

`200 OK` - Returns the updated member object

`400 Bad Request` - If the role value is invalid

`404 Not Found` - If the project or member doesn't exist

`403 Forbidden` - If user lacks permissions to manage project members

### Remove Project Member

> `DELETE /api/v1/projects/{project_id}/members/{member_id}`

Removes a member from a project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |
| member_id | string | Member identifier | Yes |

#### Response

`200 OK`

```json
{
  "success": true,
  "message": "Member removed successfully"
}
```

`404 Not Found` - If the project or member doesn't exist

`403 Forbidden` - If user lacks permissions to manage project members

### Check Member Status

> `GET /api/v1/projects/{project_id}/members/status`

Checks if the current user is a member of the project.

#### Path Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| project_id | string | Project identifier | Yes |

#### Response

`200 OK`

```json
{
  "data": {
    "isMember": true,
    "role": "member"
  }
}
```

`404 Not Found` - If the project doesn't exist

## Error Handling

The Project API uses standard HTTP status codes and provides detailed error responses. Common error codes include:

| Code | Description | HTTP Status |
|------|-------------|------------|
| VALIDATION_ERROR | Request data failed validation | 400 |
| RESOURCE_NOT_FOUND | Requested project or related resource not found | 404 |
| UNAUTHORIZED | Authentication required or token invalid | 401 |
| FORBIDDEN | User doesn't have permission for the requested operation | 403 |
| INVALID_STATUS_TRANSITION | Attempted status change is not allowed | 400 |
| MEMBER_ALREADY_EXISTS | User is already a member of the project | 409 |
| LAST_ADMIN_REMOVAL | Cannot remove the last admin from a project | 400 |

## Examples

### Create a New Project

```javascript
const createProject = async () => {
  try {
    const response = await fetch('https://api.taskmanagementsystem.com/api/v1/projects', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        name: 'Website Redesign',
        description: 'Complete overhaul of company website with new branding and improved UX.',
        status: 'planning',
        category: 'Marketing',
        tags: ['website', 'design', 'marketing']
      })
    });
    
    const data = await response.json();
    console.log('Project created:', data);
    return data;
  } catch (error) {
    console.error('Error creating project:', error);
  }
};
```

### Add a Member to a Project

```javascript
const addProjectMember = async (projectId, userId, role) => {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/api/v1/projects/${projectId}/members`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        userId: userId,
        role: role
      })
    });
    
    const data = await response.json();
    console.log('Member added:', data);
    return data;
  } catch (error) {
    console.error('Error adding project member:', error);
  }
};
```

### Update Project Status

```javascript
const updateProjectStatus = async (projectId, newStatus) => {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/api/v1/projects/${projectId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        status: newStatus
      })
    });
    
    const data = await response.json();
    console.log('Project status updated:', data);
    return data;
  } catch (error) {
    console.error('Error updating project status:', error);
  }
};
```

### Get Project Statistics

```javascript
const getProjectStats = async (projectId) => {
  try {
    const response = await fetch(`https://api.taskmanagementsystem.com/api/v1/projects/${projectId}/stats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    const data = await response.json();
    console.log('Project statistics:', data);
    return data;
  } catch (error) {
    console.error('Error fetching project statistics:', error);
  }
};
```

## Rate Limiting

The Project API implements rate limiting to prevent abuse and ensure system stability:

| Endpoint | Limit |
|----------|-------|
| GET endpoints | 60 requests per minute per user |
| POST/PUT/PATCH/DELETE endpoints | 30 requests per minute per user |

When rate limits are exceeded, the API returns a 429 Too Many Requests response with a Retry-After header indicating when to retry.

## Webhooks

You can configure webhooks to receive real-time notifications when projects or project membership changes. The following project-related events are available for webhook subscriptions:

### project.created

Triggered when a new project is created.

```json
{
  "event": "project.created",
  "timestamp": "2023-05-15T10:00:00Z",
  "data": {
    "projectId": "project_01234567890abcdef",
    "name": "Website Redesign",
    "createdBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

### project.updated

Triggered when a project is updated.

```json
{
  "event": "project.updated",
  "timestamp": "2023-06-01T14:25:00Z",
  "data": {
    "projectId": "project_01234567890abcdef",
    "name": "Website Redesign",
    "updatedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    },
    "changes": {
      "name": {
        "from": "Website Redesign",
        "to": "Website Redesign and Migration"
      },
      "description": {
        "from": "Complete overhaul of company website",
        "to": "Complete overhaul of company website with migration details"
      }
    }
  }
}
```

### project.status_changed

Triggered when a project's status changes.

```json
{
  "event": "project.status_changed",
  "timestamp": "2023-06-02T10:15:00Z",
  "data": {
    "projectId": "project_01234567890abcdef",
    "name": "Website Redesign",
    "previousStatus": "planning",
    "newStatus": "active",
    "changedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

### project.member_added

Triggered when a member is added to a project.

```json
{
  "event": "project.member_added",
  "timestamp": "2023-05-16T14:30:00Z",
  "data": {
    "projectId": "project_01234567890abcdef",
    "projectName": "Website Redesign",
    "member": {
      "id": "user_bcdef1234567890a",
      "name": "Sarah Johnson"
    },
    "role": "member",
    "addedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

### project.member_removed

Triggered when a member is removed from a project.

```json
{
  "event": "project.member_removed",
  "timestamp": "2023-06-05T11:45:00Z",
  "data": {
    "projectId": "project_01234567890abcdef",
    "projectName": "Website Redesign",
    "member": {
      "id": "user_cdef1234567890ab",
      "name": "Michael Brown"
    },
    "removedBy": {
      "id": "user_abcdef1234567890",
      "name": "John Doe"
    }
  }
}
```

## Related Resources

The following related API documentation may be useful:

- [Authentication API](auth.md) - User authentication and token management
- [Task API](tasks.md) - Task management within projects
- [File Management API](files.md) - File attachments for projects and tasks
- [Notification API](notifications.md) - Notification preferences and delivery