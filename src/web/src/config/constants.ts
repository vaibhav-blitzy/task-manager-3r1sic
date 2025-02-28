/**
 * constants.ts
 * 
 * Centralized configuration constants for the Task Management System frontend application.
 * This file contains application-wide constants, including API configuration, authentication settings,
 * pagination defaults, display formats, and UI-related constants.
 */

// Application information
export const APP_NAME = 'Task Management System';
export const APP_VERSION = '1.0.0';

// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
export const API_TIMEOUT = 30000; // 30 seconds
export const API_DATE_FORMAT = 'YYYY-MM-DDTHH:mm:ss.SSSZ'; // ISO 8601 format
export const RETRY_ATTEMPTS = 3;
export const RETRY_DELAY = 1000; // 1 second
export const DEFAULT_ERROR_MESSAGE = 'An unexpected error occurred. Please try again later.';

// Authentication settings
export const AUTH_TOKEN_KEY = 'tms_auth_token';
export const REFRESH_TOKEN_KEY = 'tms_refresh_token';
export const ACCESS_TOKEN_EXPIRY = 15 * 60; // 15 minutes in seconds
export const REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60; // 7 days in seconds
export const SESSION_STORAGE_KEY = 'tms_session';

// User roles
export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  MEMBER: 'member',
  VIEWER: 'viewer'
};

// MFA methods
export const MFA_METHODS = {
  APP: 'app',
  SMS: 'sms',
  EMAIL: 'email'
};

// Pagination defaults
export const DEFAULT_PAGINATION_LIMIT = 20;
export const MAX_PAGINATION_LIMIT = 100;

// Date and time formats
export const DATE_FORMAT = 'MMM D, YYYY'; // Example: Jan 1, 2023
export const TIME_FORMAT = 'h:mm A'; // Example: 3:30 PM
export const DATETIME_FORMAT = 'MMM D, YYYY h:mm A'; // Example: Jan 1, 2023 3:30 PM

// File upload constraints
export const FILE_UPLOAD_MAX_SIZE = 25 * 1024 * 1024; // 25MB in bytes
export const ALLOWED_FILE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/plain',
  'text/csv'
];

// Task status labels and colors
export const TASK_STATUS_LABELS: Record<string, string> = {
  'created': 'Not Started',
  'assigned': 'Assigned',
  'in-progress': 'In Progress',
  'on-hold': 'On Hold',
  'in-review': 'In Review',
  'completed': 'Completed',
  'cancelled': 'Cancelled'
};

export const TASK_STATUS_COLORS: Record<string, string> = {
  'created': '#6B7280', // Gray
  'assigned': '#3B82F6', // Blue
  'in-progress': '#8B5CF6', // Purple
  'on-hold': '#F59E0B', // Amber
  'in-review': '#10B981', // Green
  'completed': '#22C55E', // Emerald
  'cancelled': '#EF4444'  // Red
};

// Task priority labels and colors
export const TASK_PRIORITY_LABELS: Record<string, string> = {
  'low': 'Low',
  'medium': 'Medium',
  'high': 'High',
  'urgent': 'Urgent'
};

export const TASK_PRIORITY_COLORS: Record<string, string> = {
  'low': '#6B7280', // Gray
  'medium': '#3B82F6', // Blue
  'high': '#F59E0B', // Amber
  'urgent': '#EF4444'  // Red
};

// Default task filter and sort settings
export const DEFAULT_TASK_FILTER = {
  status: ['created', 'assigned', 'in-progress', 'on-hold', 'in-review'],
  assignedTo: null,
  dueDate: null,
  project: null
};

export const DEFAULT_TASK_SORT = {
  field: 'dueDate',
  direction: 'asc'
};

// Local storage keys
export const LOCAL_STORAGE_KEYS = {
  THEME: 'tms_theme',
  LANGUAGE: 'tms_language',
  TASK_VIEW: 'tms_task_view'
};

// WebSocket event types
export const WEBSOCKET_EVENTS = {
  TASK_UPDATED: 'task.update',
  TASK_CREATED: 'task.create',
  COMMENT_ADDED: 'task.comment',
  USER_PRESENCE: 'user.presence'
};

// Notification types
export const NOTIFICATION_TYPES = {
  TASK_ASSIGNED: 'task.assigned',
  TASK_DUE_SOON: 'task.due_soon',
  COMMENT_ADDED: 'comment.added',
  MENTION: 'user.mention'
};