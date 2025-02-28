/**
 * Utility function to build dynamic paths with parameters
 * @param basePath - The base path with placeholders (e.g., '/tasks/:id')
 * @param params - Object containing parameter values to replace placeholders
 * @returns Constructed path with parameters replaced
 */
export const buildPath = (basePath: string, params: Record<string, string> = {}): string => {
  let constructedPath = basePath;
  
  // Replace each parameter in the path
  Object.entries(params).forEach(([key, value]) => {
    constructedPath = constructedPath.replace(`:${key}`, value);
  });
  
  return constructedPath;
};

/**
 * Centralized route paths for application navigation
 * Provides a single source of truth for all route URLs
 */
export const PATHS = {
  // Root path
  ROOT: '/',
  
  // Authentication paths
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  
  // Main navigation paths
  DASHBOARD: '/dashboard',
  TASKS: '/tasks',
  TASK_DETAIL: '/tasks/:id',
  TASK_CREATE: '/tasks/create',
  PROJECTS: '/projects',
  PROJECT_DETAIL: '/projects/:id',
  PROJECT_CREATE: '/projects/create',
  CALENDAR: '/calendar',
  NOTIFICATIONS: '/notifications',
  REPORTS: '/reports',
  
  // Settings paths
  USER_SETTINGS: '/settings/user',
  TEAM_SETTINGS: '/settings/team',
};