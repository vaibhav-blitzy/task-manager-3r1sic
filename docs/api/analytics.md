# Analytics API

## Introduction

The Analytics API provides endpoints for creating and managing dashboards, generating reports, and accessing performance metrics. These endpoints enable data visualization, insights generation, and performance tracking within the Task Management System.

## Authentication

All Analytics API endpoints require authentication using JWT tokens. Include the token in the Authorization header of your requests using the format: `Authorization: Bearer {token}`.

## API Base URLs

The Analytics API is organized into three main components:

- Dashboard API: `/api/dashboards`
- Reports API: `/api/reports`
- Metrics API: `/api/metrics`

## Dashboards API

The Dashboards API allows you to create, manage, and retrieve dashboard configurations and their data.

### List Dashboards

```http
GET /api/dashboards
```

Retrieve a paginated list of dashboards with optional filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `type`: Filter by dashboard type (optional)
- `project_id`: Filter by project (optional)

**Response:**
```json
{
  "dashboards": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "string",
      "owner": {
        "id": "string",
        "name": "string"
      },
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

### Create Dashboard

```http
POST /api/dashboards
```

Create a new dashboard.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "type": "string",
  "layout": {
    "columns": 4
  }
}
```

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "owner": {
    "id": "string",
    "name": "string"
  },
  "layout": {
    "columns": 4,
    "widgets": []
  },
  "widgets": [],
  "scope": {
    "projects": [],
    "users": [],
    "dateRange": null
  },
  "sharing": {
    "public": false,
    "sharedWith": []
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Get Dashboard

```http
GET /api/dashboards/{dashboard_id}
```

Retrieve a specific dashboard by ID.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard to retrieve

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "owner": {
    "id": "string",
    "name": "string"
  },
  "layout": {
    "columns": 4,
    "widgets": [
      {
        "id": "string",
        "position": {
          "x": 0,
          "y": 0,
          "width": 2,
          "height": 2
        }
      }
    ]
  },
  "widgets": [
    {
      "id": "string",
      "type": "string",
      "title": "string",
      "config": {
        "dataSource": "string",
        "refreshInterval": 300,
        "visualizationType": "string",
        "filters": {},
        "drilldownEnabled": false
      }
    }
  ],
  "scope": {
    "projects": ["string"],
    "users": ["string"],
    "dateRange": {
      "start": "timestamp",
      "end": "timestamp",
      "preset": "string"
    }
  },
  "sharing": {
    "public": false,
    "sharedWith": ["string"]
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Update Dashboard

```http
PUT /api/dashboards/{dashboard_id}
```

Update a dashboard's details.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard to update

**Request Body:**
```json
{
  "name": "string",
  "description": "string"
}
```

**Response:**
Returns the updated dashboard object.

### Delete Dashboard

```http
DELETE /api/dashboards/{dashboard_id}
```

Delete a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard to delete

**Response:**
```json
{
  "success": true,
  "message": "Dashboard deleted successfully"
}
```

### Get Dashboard Data

```http
GET /api/dashboards/{dashboard_id}/data
```

Retrieve data for all widgets in a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard

**Query Parameters:**
- `refresh`: Force refresh of data (default: false)

**Response:**
```json
{
  "widgets": {
    "widget-id-1": {
      "data": {},
      "lastUpdated": "timestamp"
    },
    "widget-id-2": {
      "data": {},
      "lastUpdated": "timestamp"
    }
  }
}
```

### Add Dashboard Widget

```http
POST /api/dashboards/{dashboard_id}/widgets
```

Add a new widget to a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard

**Request Body:**
```json
{
  "type": "string",
  "title": "string",
  "config": {
    "dataSource": "string",
    "refreshInterval": 300,
    "visualizationType": "string",
    "filters": {},
    "drilldownEnabled": false
  }
}
```

**Response:**
Returns the updated dashboard object including the new widget.

### Update Dashboard Widget

```http
PUT /api/dashboards/{dashboard_id}/widgets/{widget_id}
```

Update an existing widget in a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard
- `widget_id`: The ID of the widget to update

**Request Body:**
```json
{
  "title": "string",
  "config": {
    "visualizationType": "string",
    "filters": {}
  }
}
```

**Response:**
Returns the updated dashboard object.

### Delete Dashboard Widget

```http
DELETE /api/dashboards/{dashboard_id}/widgets/{widget_id}
```

Remove a widget from a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard
- `widget_id`: The ID of the widget to delete

**Response:**
```json
{
  "success": true,
  "message": "Widget removed successfully"
}
```

### Update Dashboard Layout

```http
PUT /api/dashboards/{dashboard_id}/layout
```

Update the layout configuration of a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard

**Request Body:**
```json
{
  "columns": 4,
  "widgets": [
    {
      "id": "string",
      "position": {
        "x": 0,
        "y": 0,
        "width": 2,
        "height": 2
      }
    }
  ]
}
```

**Response:**
Returns the updated dashboard object.

### Update Dashboard Scope

```http
PUT /api/dashboards/{dashboard_id}/scope
```

Update the data scope of a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard

**Request Body:**
```json
{
  "projects": ["string"],
  "users": ["string"],
  "dateRange": {
    "start": "timestamp",
    "end": "timestamp",
    "preset": "string"
  }
}
```

**Response:**
Returns the updated dashboard object.

### Update Dashboard Sharing

```http
PUT /api/dashboards/{dashboard_id}/sharing
```

Update the sharing settings of a dashboard.

**Path Parameters:**
- `dashboard_id`: The ID of the dashboard

**Request Body:**
```json
{
  "public": false,
  "sharedWith": ["string"]
}
```

**Response:**
Returns the updated dashboard object.

### List Dashboard Templates

```http
GET /api/dashboards/templates
```

Retrieve a list of available dashboard templates.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `type`: Filter by dashboard type (optional)
- `category`: Filter by template category (optional)

**Response:**
```json
{
  "templates": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "string",
      "category": "string",
      "isSystem": true
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "pages": 1
  }
}
```

### Get Dashboard Template

```http
GET /api/dashboards/templates/{template_id}
```

Retrieve a specific dashboard template.

**Path Parameters:**
- `template_id`: The ID of the template to retrieve

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "definition": {
    "layout": {},
    "widgets": [],
    "defaultScope": {}
  },
  "category": "string",
  "isSystem": true,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Create Dashboard from Template

```http
POST /api/dashboards/templates/{template_id}/create
```

Create a new dashboard based on a template.

**Path Parameters:**
- `template_id`: The ID of the template to use

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "scope": {
    "projects": ["string"],
    "users": ["string"],
    "dateRange": {
      "preset": "string"
    }
  }
}
```

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "widgets": [],
  "layout": {},
  "scope": {},
  "created_at": "timestamp"
}
```

## Reports API

The Reports API enables generating and scheduling analytical reports in various formats.

### List Reports

```http
GET /api/reports
```

Retrieve a paginated list of reports with optional filtering.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `type`: Filter by report type (optional)

**Response:**
```json
{
  "reports": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "string",
      "owner_id": "string",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15,
    "pages": 1
  }
}
```

### Get Report

```http
GET /api/reports/{report_id}
```

Retrieve a specific report by ID.

**Path Parameters:**
- `report_id`: The ID of the report to retrieve

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "owner_id": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "value": "any",
      "display_name": "string",
      "description": "string"
    }
  ],
  "filters": {},
  "output_format": "pdf",
  "schedule": {
    "enabled": false,
    "frequency": "daily",
    "next_run": "timestamp",
    "settings": {},
    "last_run": "timestamp"
  },
  "delivery": {
    "email_enabled": false,
    "email_recipients": [],
    "email_subject_template": "string",
    "storage_enabled": false,
    "storage_path": "string"
  },
  "execution_history": [
    {
      "execution_id": "string",
      "started_at": "timestamp",
      "completed_at": "timestamp",
      "status": "completed",
      "output_format": "pdf",
      "output_url": "string",
      "size_bytes": 12345,
      "triggered_by": "string"
    }
  ],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Generate Report

```http
POST /api/reports/generate
```

Generate a report from a template.

**Request Body:**
```json
{
  "template_id": "string",
  "parameters": [
    {
      "name": "string",
      "value": "any"
    }
  ],
  "filters": {},
  "output_format": "pdf"
}
```

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "execution_id": "string",
  "status": "running",
  "started_at": "timestamp"
}
```

### Schedule Report

```http
POST /api/reports/schedule
```

Schedule periodic report generation.

**Request Body:**
```json
{
  "template_id": "string",
  "name": "string",
  "description": "string",
  "parameters": [
    {
      "name": "string",
      "value": "any"
    }
  ],
  "filters": {},
  "output_format": "pdf",
  "schedule": {
    "frequency": "daily",
    "settings": {
      "time": "08:00",
      "days": ["Monday", "Wednesday", "Friday"]
    }
  },
  "delivery": {
    "email_enabled": true,
    "email_recipients": ["user@example.com"],
    "email_subject_template": "{{report_name}} - {{date}}",
    "storage_enabled": true,
    "storage_path": "reports/{{date}}/{{report_name}}"
  }
}
```

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "schedule": {
    "enabled": true,
    "frequency": "daily",
    "next_run": "timestamp",
    "settings": {}
  },
  "created_at": "timestamp"
}
```

### List Scheduled Reports

```http
GET /api/reports/scheduled
```

Retrieve a list of scheduled reports.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Response:**
```json
{
  "reports": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "schedule": {
        "enabled": true,
        "frequency": "daily",
        "next_run": "timestamp",
        "last_run": "timestamp"
      },
      "owner_id": "string",
      "created_at": "timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "pages": 1
  }
}
```

### Cancel Scheduled Report

```http
POST /api/reports/scheduled/{report_id}/cancel
```

Cancel a scheduled report.

**Path Parameters:**
- `report_id`: The ID of the scheduled report to cancel

**Response:**
```json
{
  "success": true,
  "message": "Scheduled report cancelled successfully"
}
```

### Export Report

```http
GET /api/reports/{report_id}/export
```

Export a report in a specified format.

**Path Parameters:**
- `report_id`: The ID of the report to export

**Query Parameters:**
- `format`: Output format (pdf, html, csv, excel, json)

**Response:**
File download response with appropriate content type and filename.

### List Report Templates

```http
GET /api/reports/templates
```

Retrieve a list of available report templates.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `type`: Filter by report type (optional)

**Response:**
```json
{
  "templates": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "string",
      "is_system": true,
      "category": "string",
      "created_at": "timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 8,
    "pages": 1
  }
}
```

### Get Report Template

```http
GET /api/reports/templates/{template_id}
```

Retrieve a specific report template.

**Path Parameters:**
- `template_id`: The ID of the template to retrieve

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "string",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "display_name": "string",
      "description": "string"
    }
  ],
  "default_filters": {},
  "default_output_format": "pdf",
  "is_system": true,
  "category": "string",
  "owner_id": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Get Report Types

```http
GET /api/reports/types
```

Retrieve a list of supported report types.

**Response:**
```json
{
  "types": [
    "task_status",
    "completion_rate",
    "workload_distribution",
    "bottleneck_identification",
    "burndown",
    "performance_metrics",
    "user_productivity",
    "project_health"
  ]
}
```

### Get Report Formats

```http
GET /api/reports/formats
```

Retrieve a list of supported report output formats.

**Response:**
```json
{
  "formats": [
    "html",
    "pdf",
    "csv",
    "excel",
    "json"
  ]
}
```

## Metrics API

The Metrics API provides access to performance indicators and analytics data for tasks, projects, and users.

### Task Completion Rate

```http
GET /api/metrics/task-completion-rate
```

Retrieve task completion rate metrics.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "completion_rate": 75.5,
  "completed_tasks": 151,
  "total_tasks": 200,
  "time_period": "month",
  "comparison": {
    "previous_rate": 70.2,
    "change": 5.3,
    "trend": "increasing"
  }
}
```

### On-Time Completion Rate

```http
GET /api/metrics/on-time-completion-rate
```

Retrieve on-time task completion rate metrics.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "on_time_rate": 82.1,
  "on_time_tasks": 124,
  "completed_tasks": 151,
  "time_period": "month",
  "comparison": {
    "previous_rate": 78.5,
    "change": 3.6,
    "trend": "increasing"
  }
}
```

### Average Task Age

```http
GET /api/metrics/average-task-age
```

Retrieve average age of tasks.

**Query Parameters:**
- `status`: Filter by task status (optional)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "average_age_days": 12.5,
  "oldest_task_days": 45,
  "newest_task_days": 0.5,
  "task_count": 200,
  "breakdown_by_status": {
    "not_started": 8.2,
    "in_progress": 15.7,
    "review": 5.3
  }
}
```

### Cycle Time

```http
GET /api/metrics/cycle-time
```

Retrieve average cycle time from task creation to completion.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "average_cycle_time_days": 4.2,
  "min_cycle_time_days": 0.5,
  "max_cycle_time_days": 30.1,
  "median_cycle_time_days": 3.5,
  "task_count": 151,
  "time_period": "month"
}
```

### Lead Time

```http
GET /api/metrics/lead-time
```

Retrieve average lead time from task creation to delivery.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "average_lead_time_days": 6.8,
  "min_lead_time_days": 1.0,
  "max_lead_time_days": 35.5,
  "median_lead_time_days": 5.2,
  "task_count": 151,
  "time_period": "month"
}
```

### Workload Distribution

```http
GET /api/metrics/workload-distribution
```

Retrieve workload distribution among team members.

**Query Parameters:**
- `project_id`: Filter by project (optional)

**Response:**
```json
{
  "users": [
    {
      "id": "string",
      "name": "string",
      "active_tasks": 15,
      "completed_tasks": 32,
      "overdue_tasks": 3,
      "upcoming_tasks": 5
    }
  ],
  "average_load": 8.3,
  "max_load": 15,
  "min_load": 2
}
```

### Bottleneck Identification

```http
GET /api/metrics/bottlenecks
```

Identify process bottlenecks in task workflow.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)

**Response:**
```json
{
  "bottlenecks": [
    {
      "status": "review",
      "average_time_days": 3.5,
      "task_count": 45,
      "is_bottleneck": true
    },
    {
      "status": "in_progress",
      "average_time_days": 2.1,
      "task_count": 62,
      "is_bottleneck": false
    }
  ],
  "time_period": "month"
}
```

### Burndown Data

```http
GET /api/metrics/burndown
```

Retrieve burndown chart data for project tracking.

**Query Parameters:**
- `project_id`: Project ID (required)
- `start_date`: Start date (optional, ISO format)
- `end_date`: End date (optional, ISO format)

**Response:**
```json
{
  "ideal": [
    {"date": "2023-02-01", "remaining": 50},
    {"date": "2023-02-15", "remaining": 25},
    {"date": "2023-02-28", "remaining": 0}
  ],
  "actual": [
    {"date": "2023-02-01", "remaining": 50},
    {"date": "2023-02-08", "remaining": 42},
    {"date": "2023-02-15", "remaining": 30},
    {"date": "2023-02-22", "remaining": 15},
    {"date": "2023-02-28", "remaining": 5}
  ],
  "scope_changes": [
    {"date": "2023-02-10", "change": 5, "total": 55}
  ],
  "start_date": "2023-02-01",
  "end_date": "2023-02-28",
  "initial_scope": 50,
  "current_scope": 55,
  "completed": 50,
  "remaining": 5
}
```

### Task Status Distribution

```http
GET /api/metrics/task-status-distribution
```

Retrieve distribution of tasks by status.

**Query Parameters:**
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "total": 200,
  "distribution": [
    {"status": "not_started", "count": 45, "percentage": 22.5},
    {"status": "in_progress", "count": 62, "percentage": 31.0},
    {"status": "review", "count": 38, "percentage": 19.0},
    {"status": "completed", "count": 55, "percentage": 27.5}
  ]
}
```

### Task Priority Distribution

```http
GET /api/metrics/task-priority-distribution
```

Retrieve distribution of tasks by priority.

**Query Parameters:**
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "total": 200,
  "distribution": [
    {"priority": "low", "count": 35, "percentage": 17.5},
    {"priority": "medium", "count": 80, "percentage": 40.0},
    {"priority": "high", "count": 65, "percentage": 32.5},
    {"priority": "urgent", "count": 20, "percentage": 10.0}
  ]
}
```

### Project Progress

```http
GET /api/metrics/project-progress
```

Retrieve progress information for projects.

**Query Parameters:**
- `project_ids`: Comma-separated list of project IDs (optional)

**Response:**
```json
{
  "projects": [
    {
      "id": "string",
      "name": "string",
      "completion_percentage": 65.0,
      "tasks_total": 40,
      "tasks_completed": 26,
      "on_track": true,
      "overdue_tasks": 2,
      "start_date": "2023-01-15",
      "end_date": "2023-03-30",
      "days_remaining": 25
    }
  ]
}
```

### User Productivity

```http
GET /api/metrics/user-productivity
```

Retrieve productivity metrics for users.

**Query Parameters:**
- `user_ids`: Comma-separated list of user IDs (optional)
- `time_period`: Analysis period (day, week, month, quarter, year)

**Response:**
```json
{
  "users": [
    {
      "id": "string",
      "name": "string",
      "tasks_completed": 32,
      "tasks_created": 12,
      "on_time_completion_rate": 87.5,
      "average_cycle_time_days": 3.2,
      "activity_level": "high"
    }
  ],
  "time_period": "month"
}
```

### Task Completion Trend

```http
GET /api/metrics/task-completion-trend
```

Retrieve time-series data of task completions.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `interval`: Grouping interval (hour, day, week, month)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "trend": [
    {"date": "2023-02-01", "completed": 5},
    {"date": "2023-02-02", "completed": 3},
    {"date": "2023-02-03", "completed": 7}
  ],
  "time_period": "month",
  "interval": "day",
  "total_completed": 151
}
```

### Overdue Tasks Count

```http
GET /api/metrics/overdue-tasks-count
```

Retrieve count of overdue tasks.

**Query Parameters:**
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "overdue_count": 12,
  "total_tasks": 200,
  "percentage": 6.0,
  "breakdown": [
    {"days_overdue": "1-2", "count": 5},
    {"days_overdue": "3-7", "count": 4},
    {"days_overdue": "8+", "count": 3}
  ]
}
```

### Upcoming Due Tasks

```http
GET /api/metrics/upcoming-due-tasks
```

Retrieve tasks approaching their due dates.

**Query Parameters:**
- `days`: Number of days to look ahead (default: 7)
- `project_id`: Filter by project (optional)
- `user_id`: Filter by user (optional)

**Response:**
```json
{
  "upcoming_count": 15,
  "breakdown": [
    {"days_until_due": "today", "count": 3},
    {"days_until_due": "tomorrow", "count": 4},
    {"days_until_due": "2-3 days", "count": 5},
    {"days_until_due": "4-7 days", "count": 3}
  ],
  "tasks": [
    {
      "id": "string",
      "title": "string",
      "due_date": "2023-02-28",
      "days_until_due": 1,
      "assignee": {
        "id": "string",
        "name": "string"
      },
      "project": {
        "id": "string",
        "name": "string"
      }
    }
  ]
}
```

### Project Completion Percentage

```http
GET /api/metrics/project-completion-percentage/{project_id}
```

Retrieve completion percentage for a project.

**Path Parameters:**
- `project_id`: The ID of the project

**Response:**
```json
{
  "project_id": "string",
  "project_name": "string",
  "completion_percentage": 65.0,
  "tasks_total": 40,
  "tasks_completed": 26,
  "tasks_by_status": {
    "not_started": 5,
    "in_progress": 7,
    "review": 2,
    "completed": 26
  }
}
```

### Metrics Summary

```http
GET /api/metrics/summary
```

Retrieve a comprehensive summary of key metrics.

**Query Parameters:**
- `time_period`: Analysis period (day, week, month, quarter, year)
- `project_id`: Filter by project (optional)

**Response:**
```json
{
  "time_period": "month",
  "task_metrics": {
    "created": 75,
    "completed": 65,
    "overdue": 8,
    "completion_rate": 76.5,
    "on_time_rate": 84.6
  },
  "time_metrics": {
    "average_cycle_time_days": 4.2,
    "average_lead_time_days": 6.8
  },
  "project_metrics": {
    "active_projects": 5,
    "on_track_projects": 4,
    "at_risk_projects": 1
  },
  "comparison": {
    "task_completion": {
      "previous": 58,
      "change": 7,
      "trend": "increasing"
    }
  }
}
```

## Data Types

Common data types used throughout the Analytics API.

### Dashboard Types

```
personal - Personal dashboard for individual user
project - Dashboard specific to a project
team - Dashboard for a team's activity
organization - Organization-wide dashboard
```

### Widget Types

```
task_status - Tasks by status distribution
task_completion - Task completion metrics
workload - Team workload distribution
due_date - Upcoming and overdue tasks
project_progress - Project completion status
activity - Recent user activity
custom_metric - Custom metric visualization
```

### Visualization Types

```
pie_chart - Circular chart for proportions
bar_chart - Vertical or horizontal bars
line_chart - Connected points for trends
progress_bar - Linear progress indicator
calendar - Calendar-based visualization
list - Text-based list view
heat_map - Color-coded data matrix
card - Simple metric display card
```

### Report Types

```
task_status - Task status breakdown
completion_rate - Task completion analysis
workload_distribution - Team workload analysis
bottleneck_identification - Process bottleneck analysis
burndown - Project burndown analysis
performance_metrics - Performance KPI report
user_productivity - User productivity analysis
project_health - Project health and status report
```

### Report Output Formats

```
html - HTML web page format
pdf - PDF document format
csv - Comma-separated values format
excel - Microsoft Excel format
json - JSON data format
```

### Report Frequencies

```
daily - Run every day
weekly - Run every week
monthly - Run every month
quarterly - Run every quarter
```

## Error Handling

The Analytics API uses standard HTTP status codes and provides detailed error responses.

### Error Response Format

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### Common Error Codes

- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Requested resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Unexpected server error