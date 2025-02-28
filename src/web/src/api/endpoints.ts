/**
 * endpoints.ts
 * 
 * Centralized collection of API endpoint definitions for the Task Management System frontend.
 * Provides constant URL patterns for all backend service interactions including
 * authentication, tasks, projects, notifications, files, and analytics services.
 */

import { API_BASE_URL } from '../config/constants';

/**
 * Builds a complete API URL from a path
 * @param path The endpoint path
 * @returns The complete URL
 */
export const buildUrl = (path: string): string => {
  // Ensure path has a leading slash
  const formattedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${formattedPath}`;
};

/**
 * Creates a function that builds URLs with path parameters
 * @param path The path pattern with placeholders (e.g., "/tasks/:id")
 * @returns A function that replaces placeholders with provided values
 */
export const buildParamUrl = (path: string) => {
  return (...ids: string[]): string => {
    let formattedPath = path;
    // Replace each placeholder (:id, :anotherId, etc.) with corresponding id
    const placeholders = path.match(/:[a-zA-Z]+/g) || [];
    
    placeholders.forEach((placeholder, index) => {
      if (ids[index]) {
        formattedPath = formattedPath.replace(placeholder, ids[index]);
      }
    });
    
    return buildUrl(formattedPath);
  };
};

// Authentication Service Endpoints
export const AUTH_ENDPOINTS = {
  BASE: buildUrl('/auth'),
  LOGIN: buildUrl('/auth/login'),
  REGISTER: buildUrl('/auth/register'),
  REFRESH_TOKEN: buildUrl('/auth/token/refresh'),
  LOGOUT: buildUrl('/auth/logout'),
  VERIFY_EMAIL: buildUrl('/auth/verify-email'),
  VERIFY_MFA: buildUrl('/auth/mfa/verify'),
  REQUEST_PASSWORD_RESET: buildUrl('/auth/password/reset'),
  RESET_PASSWORD: buildUrl('/auth/password/change'),
  STATUS: buildUrl('/auth/status')
};

// Task Management Service Endpoints
export const TASK_ENDPOINTS = {
  BASE: buildUrl('/tasks'),
  GET_TASK: buildParamUrl('/tasks/:id'),
  UPDATE_TASK: buildParamUrl('/tasks/:id'),
  DELETE_TASK: buildParamUrl('/tasks/:id'),
  ASSIGN_TASK: buildParamUrl('/tasks/:id/assign'),
  UPDATE_STATUS: buildParamUrl('/tasks/:id/status'),
  COMMENTS: buildParamUrl('/tasks/:id/comments'),
  SUBTASKS: buildParamUrl('/tasks/:id/subtasks'),
  SUBTASK: buildParamUrl('/tasks/:id/subtasks/:subtaskId'),
  DEPENDENCIES: buildParamUrl('/tasks/:id/dependencies'),
  SEARCH: buildUrl('/tasks/search'),
  DUE_SOON: buildUrl('/tasks/due-soon'),
  OVERDUE: buildUrl('/tasks/overdue')
};

// Project Management Service Endpoints
export const PROJECT_ENDPOINTS = {
  BASE: buildUrl('/projects'),
  GET_PROJECT: buildParamUrl('/projects/:id'),
  UPDATE_PROJECT: buildParamUrl('/projects/:id'),
  DELETE_PROJECT: buildParamUrl('/projects/:id'),
  UPDATE_STATUS: buildParamUrl('/projects/:id/status'),
  MEMBERS: buildParamUrl('/projects/:id/members'),
  MEMBER: buildParamUrl('/projects/:id/members/:userId'),
  TASK_LISTS: buildParamUrl('/projects/:id/tasklists'),
  STATISTICS: buildParamUrl('/projects/:id/statistics')
};

// File Management Service Endpoints
export const FILE_ENDPOINTS = {
  BASE: buildUrl('/files'),
  UPLOAD: buildUrl('/files/upload'),
  DOWNLOAD: buildParamUrl('/files/:id/download'),
  GET_FILE: buildParamUrl('/files/:id'),
  DELETE_FILE: buildParamUrl('/files/:id'),
  ATTACHMENTS: buildParamUrl('/:entityType/:entityId/attachments')
};

// Notification Service Endpoints
export const NOTIFICATION_ENDPOINTS = {
  BASE: buildUrl('/notifications'),
  GET_NOTIFICATIONS: buildUrl('/notifications'),
  MARK_READ: buildParamUrl('/notifications/:id/read'),
  MARK_ALL_READ: buildUrl('/notifications/read-all'),
  PREFERENCES: buildUrl('/notifications/preferences'),
  UNREAD_COUNT: buildUrl('/notifications/unread/count')
};

// Analytics & Reporting Service Endpoints
export const ANALYTICS_ENDPOINTS = {
  BASE: buildUrl('/analytics'),
  DASHBOARDS: buildUrl('/analytics/dashboards'),
  DASHBOARD: buildParamUrl('/analytics/dashboards/:id'),
  REPORTS: buildUrl('/analytics/reports'),
  GENERATE_REPORT: buildUrl('/analytics/reports/generate'),
  METRICS: buildUrl('/analytics/metrics')
};

// User Management Endpoints
export const USER_ENDPOINTS = {
  BASE: buildUrl('/users'),
  PROFILE: buildUrl('/users/profile'),
  UPDATE_PROFILE: buildUrl('/users/profile'),
  CHANGE_PASSWORD: buildUrl('/users/password'),
  SEARCH: buildUrl('/users/search')
};

// Real-Time Communication Endpoints
export const REALTIME_ENDPOINTS = {
  WEBSOCKET: `${API_BASE_URL.replace('http', 'ws').replace('https', 'wss')}/realtime/connect`,
  CONNECT: buildUrl('/realtime/connect'),
  PRESENCE: buildUrl('/realtime/presence')
};