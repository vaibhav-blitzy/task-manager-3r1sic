# Real-time Collaboration API

## Introduction

The Task Management System provides comprehensive real-time collaboration functionality that enables multiple users to work simultaneously on tasks and projects with immediate visibility of changes. The Real-time Collaboration Service powers features such as:

- Live updates to tasks and projects
- User presence awareness (who's online, viewing, editing)
- Typing indicators
- Collaborative editing with conflict resolution
- Activity feeds and notifications

This document describes the WebSocket-based API and supporting REST endpoints that power these features.

## WebSocket Connection

### Establishing a Connection

The real-time features use WebSocket connections for bidirectional communication between clients and the server.

**Connection Endpoint:**
```
WebSocket: wss://api.taskmanagementsystem.com/realtime/connect
```

**Connection Process:**
1. Client initiates WebSocket connection with authentication token
2. Server validates the token
3. If valid, connection is established and an acknowledgment is sent
4. Client can then subscribe to channels
5. Server maintains the connection with periodic heartbeats

**Example Client Connection (JavaScript):**
```javascript
const token = "your-auth-jwt-token";
const socket = new WebSocket(`wss://api.taskmanagementsystem.com/realtime/connect?token=${token}`);

socket.onopen = (event) => {
  console.log('Connection established');
  
  // Subscribe to channels after connection
  const subscribeMessage = {
    type: 'subscribe',
    channels: ['task:123', 'project:456']
  };
  socket.send(JSON.stringify(subscribeMessage));
};

socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Message received:', message);
  // Handle different message types
};

socket.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
};

socket.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Heartbeat Mechanism

To maintain connection health and detect disconnections:

- Server sends a ping message every 30 seconds
- Client must respond with a pong message
- If no response is received after 2 ping attempts, the connection is considered stale and closed
- Clients should implement automatic reconnection with exponential backoff

**Heartbeat Example:**
```javascript
// Server sends:
{
  "type": "ping",
  "timestamp": 1633452789
}

// Client responds:
{
  "type": "pong",
  "timestamp": 1633452789
}
```

### Reconnection Strategy

Clients should implement reconnection with exponential backoff:

1. Initial reconnect attempt after 1 second
2. If unsuccessful, wait 2 seconds
3. If still unsuccessful, wait 4 seconds
4. Continue doubling wait time up to a maximum of 60 seconds
5. Keep trying until reconnected or user explicitly disconnects

During reconnection:
- Client should preserve subscription information
- Re-subscribe to channels after connection is re-established
- Request missed events based on last received event ID

## Authentication

### Token-based Authentication

All WebSocket connections require a valid JWT authentication token.

**Authentication Methods:**
1. **Query Parameter**: Include token in the connection URL
   ```
   wss://api.taskmanagementsystem.com/realtime/connect?token=your-jwt-token
   ```

2. **Authorization Header** (for HTTP upgrade to WebSocket):
   ```
   Authorization: Bearer your-jwt-token
   ```

### Authentication Errors

| Error Code | Description | Resolution |
|------------|-------------|------------|
| 401 | Unauthorized (Invalid token) | Provide a valid token |
| 403 | Forbidden (Token valid, but lacks permissions) | Request necessary permissions |
| 429 | Too Many Requests (Rate limit exceeded) | Implement backoff/retry strategy |

### Token Expiration Handling

When a token is expiring:
1. Server sends a `token.expiring` event 5 minutes before expiration
2. Client should obtain a new token and reconnect
3. If token expires during an active connection, server sends `token.expired` event and closes connection

**Token Expiration Event:**
```json
{
  "type": "system",
  "event": "token.expiring",
  "data": {
    "expiresIn": 300,
    "reconnectUrl": "wss://api.taskmanagementsystem.com/realtime/connect"
  }
}
```

## Channels

### Channel Types

The real-time system organizes communications into logical channels based on resource types and IDs:

| Channel Type | Format | Description | Example | 
|--------------|--------|-------------|---------|
| Task | `task:{id}` | Updates for a specific task | `task:123` |
| Project | `project:{id}` | Updates for a specific project | `project:456` |
| User | `user:{id}` | Updates for a specific user | `user:789` |
| Team | `team:{id}` | Updates for a specific team | `team:101` |
| System | `system` | System-wide announcements | `system` |

### Channel Subscription

After establishing a connection, clients can subscribe to channels to receive relevant events.

**Subscribe to Channels:**
```json
{
  "type": "subscribe",
  "channels": ["task:123", "project:456", "user:789"]
}
```

**Successful Subscription Response:**
```json
{
  "type": "subscription",
  "status": "success",
  "channels": ["task:123", "project:456", "user:789"]
}
```

**Unsubscribe from Channels:**
```json
{
  "type": "unsubscribe",
  "channels": ["project:456"]
}
```

**Subscription Error Response:**
```json
{
  "type": "subscription",
  "status": "error",
  "errorCode": "permission_denied",
  "message": "You don't have access to this channel",
  "channels": ["project:789"]
}
```

### Channel Authorization

- Channel access is determined by user permissions
- Subscription requests to unauthorized channels will be rejected
- Token must have appropriate scopes for channel access

### Channel Limitations

- Maximum of 50 concurrent channel subscriptions per connection
- Rate limit of 10 subscription changes per minute

## Presence Tracking

### User Presence

The presence system tracks users' online status, viewing context, and activity to enhance collaboration.

**Presence States:**
- `online`: User is connected and active
- `away`: User is connected but inactive for more than 5 minutes
- `busy`: User has manually set their status to busy
- `offline`: User is disconnected

### Presence Update

**Setting User Presence:**
```json
{
  "type": "presence",
  "action": "update",
  "data": {
    "status": "busy",
    "statusMessage": "In a meeting"
  }
}
```

**Presence Response:**
```json
{
  "type": "presence",
  "event": "updated",
  "data": {
    "userId": "789",
    "status": "busy",
    "statusMessage": "In a meeting",
    "updatedAt": "2023-09-15T14:30:45Z"
  }
}
```

### Viewing Context

Clients can broadcast what resource a user is currently viewing:

**Update Viewing Context:**
```json
{
  "type": "presence",
  "action": "viewing",
  "data": {
    "resourceType": "task",
    "resourceId": "123"
  }
}
```

**Viewing Context Broadcast:**
```json
{
  "type": "presence",
  "event": "viewing",
  "data": {
    "userId": "789",
    "resourceType": "task",
    "resourceId": "123",
    "startedAt": "2023-09-15T14:35:20Z"
  }
}
```

### Typing Indicators

Clients can indicate when a user is typing in a comment or editable field:

**Start Typing:**
```json
{
  "type": "presence",
  "action": "typing",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "comment",
    "isTyping": true
  }
}
```

**Stop Typing:**
```json
{
  "type": "presence",
  "action": "typing",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "comment",
    "isTyping": false
  }
}
```

**Typing Indicator Broadcast:**
```json
{
  "type": "presence",
  "event": "typing",
  "data": {
    "userId": "789",
    "resourceType": "task",
    "resourceId": "123",
    "field": "comment",
    "isTyping": true,
    "timestamp": "2023-09-15T14:36:10Z"
  }
}
```

### Getting Active Users

To retrieve currently active users on a resource:

**REST Endpoint:**
```
GET /realtime/presence?resource=task&id=123
```

**Response:**
```json
{
  "resource": {
    "type": "task",
    "id": "123"
  },
  "activeUsers": [
    {
      "userId": "789",
      "name": "John Doe",
      "avatar": "https://example.com/avatars/john.jpg",
      "status": "online",
      "viewing": true,
      "typing": false,
      "lastActivity": "2023-09-15T14:40:22Z"
    },
    {
      "userId": "456",
      "name": "Jane Smith",
      "avatar": "https://example.com/avatars/jane.jpg",
      "status": "online",
      "viewing": true,
      "typing": true,
      "lastActivity": "2023-09-15T14:41:05Z"
    }
  ]
}
```

## Collaborative Editing

The collaborative editing system enables multiple users to edit the same content simultaneously, with automatic conflict resolution through operational transformation (OT).

### Editing Session

Before collaborative editing, a client must start an editing session:

**Start Editing:**
```json
{
  "type": "edit",
  "action": "start",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "description"
  }
}
```

**Editing Session Response:**
```json
{
  "type": "edit",
  "event": "started",
  "data": {
    "sessionId": "edit-session-456",
    "resourceType": "task",
    "resourceId": "123",
    "field": "description",
    "initialContent": "The task involves creating wireframes...",
    "revision": 5,
    "activeEditors": [
      {
        "userId": "789",
        "name": "John Doe"
      }
    ]
  }
}
```

### Operational Transformation

The system uses Operational Transformation (OT) for managing concurrent edits:

**Send Operation:**
```json
{
  "type": "edit",
  "action": "operation",
  "data": {
    "sessionId": "edit-session-456",
    "revision": 5,
    "operation": {
      "ops": [
        { "retain": 10 },
        { "insert": "updated " },
        { "retain": 20 }
      ]
    }
  }
}
```

**Operation Broadcast:**
```json
{
  "type": "edit",
  "event": "operation",
  "data": {
    "sessionId": "edit-session-456",
    "userId": "789",
    "revision": 6,
    "operation": {
      "ops": [
        { "retain": 10 },
        { "insert": "updated " },
        { "retain": 20 }
      ]
    }
  }
}
```

### Edit Locking

For simpler fields that don't support concurrent editing, a locking mechanism is used:

**Acquire Lock:**
```json
{
  "type": "edit",
  "action": "lock",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "title"
  }
}
```

**Lock Response:**
```json
{
  "type": "edit",
  "event": "locked",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "title",
    "lockId": "lock-789",
    "expiresAt": "2023-09-15T15:00:00Z",
    "lockedBy": {
      "userId": "789",
      "name": "John Doe"
    }
  }
}
```

**Release Lock:**
```json
{
  "type": "edit",
  "action": "unlock",
  "data": {
    "lockId": "lock-789"
  }
}
```

### Save Changes

**Save Edited Content:**
```json
{
  "type": "edit",
  "action": "save",
  "data": {
    "sessionId": "edit-session-456",
    "finalContent": "The task involves creating updated wireframes...",
    "revision": 8
  }
}
```

**Save Confirmation:**
```json
{
  "type": "edit",
  "event": "saved",
  "data": {
    "resourceType": "task",
    "resourceId": "123",
    "field": "description",
    "updatedAt": "2023-09-15T14:55:30Z"
  }
}
```

## REST API Endpoints

In addition to WebSockets, the system provides REST API endpoints for real-time related operations.

### Connection Status

**Check Connection Status:**
```
GET /realtime/status
```

**Response:**
```json
{
  "status": "operational",
  "connections": 1250,
  "uptime": "5d 12h 30m",
  "version": "1.5.2"
}
```

### Channel Management

**List Available Channels:**
```
GET /realtime/channels
```

**Response:**
```json
{
  "channels": [
    {
      "name": "task",
      "description": "Task-related events",
      "subscriptionPattern": "task:{id}"
    },
    {
      "name": "project",
      "description": "Project-related events",
      "subscriptionPattern": "project:{id}"
    },
    {
      "name": "user",
      "description": "User-related events",
      "subscriptionPattern": "user:{id}"
    },
    {
      "name": "team",
      "description": "Team-related events",
      "subscriptionPattern": "team:{id}"
    },
    {
      "name": "system",
      "description": "System-wide announcements",
      "subscriptionPattern": "system"
    }
  ]
}
```

### Presence Endpoints

**Get User Presence:**
```
GET /realtime/presence/users/{userId}
```

**Response:**
```json
{
  "userId": "789",
  "status": "online",
  "statusMessage": "Working on task #123",
  "lastActivity": "2023-09-15T14:58:20Z",
  "currentlyViewing": {
    "resourceType": "task",
    "resourceId": "123"
  }
}
```

### Send Message to Channel

**Broadcast Message to Channel:**
```
POST /realtime/broadcast
```

**Request Body:**
```json
{
  "channel": "project:456",
  "event": "announcement",
  "data": {
    "message": "Team meeting starting in 5 minutes",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "status": "sent",
  "recipients": 8,
  "timestamp": "2023-09-15T15:00:00Z",
  "messageId": "msg-123456"
}
```

## Event Types

The real-time system uses standardized event types for various collaboration activities.

### Task Events

| Event | Description | Channel |
|-------|-------------|---------|
| `task.created` | New task created | `project:{id}` |
| `task.updated` | Task details updated | `task:{id}`, `project:{id}` |
| `task.status` | Task status changed | `task:{id}`, `project:{id}` |
| `task.assigned` | Task assigned to user | `task:{id}`, `user:{id}` |
| `task.comment` | Comment added to task | `task:{id}` |

### Project Events

| Event | Description | Channel |
|-------|-------------|---------|
| `project.updated` | Project details updated | `project:{id}` |
| `project.member.added` | User added to project | `project:{id}`, `user:{id}` |
| `project.member.removed` | User removed from project | `project:{id}`, `user:{id}` |
| `project.status` | Project status changed | `project:{id}` |

### User Events

| Event | Description | Channel |
|-------|-------------|---------|
| `user.presence` | User presence changed | Relevant resource channels |
| `user.typing` | User typing indicator | Relevant resource channels |

### Editing Events

| Event | Description | Channel |
|-------|-------------|---------|
| `edit.started` | Editing session started | Relevant resource channel |
| `edit.operation` | Edit operation applied | Relevant resource channel |
| `edit.saved` | Edits saved | Relevant resource channel |
| `edit.lock` | Resource field locked | Relevant resource channel |
| `edit.unlock` | Resource field unlocked | Relevant resource channel |

### System Events

| Event | Description | Channel |
|-------|-------------|---------|
| `system.announcement` | System-wide announcement | `system` |
| `system.maintenance` | Upcoming maintenance notification | `system` |

### Event Message Structure

All event messages follow a standard format:

```json
{
  "type": "event",
  "event": "task.updated",
  "channel": "task:123",
  "data": {
    // Event-specific data
  },
  "timestamp": "2023-09-15T15:05:42Z",
  "userId": "789",
  "eventId": "evt-987654"
}
```

- `type`: Always "event" for event messages
- `event`: The specific event type
- `channel`: The channel this event was sent on
- `data`: Event-specific payload
- `timestamp`: ISO 8601 timestamp when the event occurred
- `userId`: ID of the user who triggered the event (if applicable)
- `eventId`: Unique identifier for the event

### Error Handling

Error responses follow a standard format:

```json
{
  "type": "error",
  "code": "rate_limit_exceeded",
  "message": "Too many subscription requests",
  "details": {
    "limit": 10,
    "resetAt": "2023-09-15T15:10:00Z"
  }
}
```

| Error Code | Description |
|------------|-------------|
| `invalid_message` | Malformed message |
| `authentication_failed` | Authentication error |
| `permission_denied` | Insufficient permissions |
| `rate_limit_exceeded` | Rate limit reached |
| `subscription_limit_exceeded` | Too many channel subscriptions |
| `channel_not_found` | Requested channel does not exist |
| `invalid_operation` | Invalid edit operation |
| `resource_locked` | Resource is locked by another user |
| `session_expired` | Editing session has expired |
| `server_error` | Internal server error |