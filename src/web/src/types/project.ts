/**
 * TypeScript type definitions for project-related entities in the Task Management System,
 * including project data structures, roles, and settings.
 * 
 * @version 1.0.0
 */

import { User } from './user';

/**
 * Enumeration of possible project statuses
 */
export enum ProjectStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  ON_HOLD = 'on-hold',
  COMPLETED = 'completed',
  ARCHIVED = 'archived'
}

/**
 * Enumeration of possible project member roles
 */
export enum ProjectRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  MEMBER = 'member',
  VIEWER = 'viewer'
}

/**
 * Interface representing a task list within a project
 */
export interface TaskList {
  /**
   * Unique identifier for the task list
   */
  id: string;

  /**
   * Name of the task list
   */
  name: string;

  /**
   * Description of the task list
   */
  description: string;

  /**
   * Sort order of the task list within the project
   */
  sortOrder: number;

  /**
   * ISO date string when the task list was created
   */
  createdAt: string;
}

/**
 * Interface representing a member of a project with their role
 */
export interface ProjectMember {
  /**
   * User ID of the project member
   */
  userId: string;

  /**
   * User details of the project member
   */
  user: User;

  /**
   * Role of the user in the project
   */
  role: ProjectRole;

  /**
   * ISO date string when the user joined the project
   */
  joinedAt: string;

  /**
   * Whether the member is currently active in the project
   */
  isActive: boolean;
}

/**
 * Interface representing project settings and configuration
 */
export interface ProjectSettings {
  /**
   * Workflow-related settings
   */
  workflow: {
    /**
     * Whether tasks require review before completion
     */
    enableReview: boolean;

    /**
     * Whether tasks can have subtasks
     */
    allowSubtasks: boolean;

    /**
     * Default status for newly created tasks
     */
    defaultTaskStatus: string;
  };

  /**
   * Permission-related settings
   */
  permissions: {
    /**
     * Role required to invite members
     */
    memberInvite: string;

    /**
     * Role required to create tasks
     */
    taskCreate: string;

    /**
     * Role required to add comments
     */
    commentCreate: string;
  };

  /**
   * Notification settings
   */
  notifications: {
    /**
     * Whether to notify on task creation
     */
    taskCreate: boolean;

    /**
     * Whether to notify on task completion
     */
    taskComplete: boolean;

    /**
     * Whether to notify on comment addition
     */
    commentAdd: boolean;
  };
}

/**
 * Interface representing a custom field for projects
 */
export interface CustomField {
  /**
   * Unique identifier for the custom field
   */
  id: string;

  /**
   * Name of the custom field
   */
  name: string;

  /**
   * Type of the custom field (text, number, date, select)
   */
  type: string;

  /**
   * Available options for select-type fields
   */
  options: string[];
}

/**
 * Interface representing project metadata
 */
export interface ProjectMetadata {
  /**
   * ISO date string when the project was created
   */
  created: string;

  /**
   * ISO date string when the project was last updated
   */
  lastUpdated: string;

  /**
   * ISO date string when the project was completed (if applicable)
   */
  completedAt: string | null;

  /**
   * Total number of tasks in the project
   */
  taskCount: number;

  /**
   * Number of completed tasks in the project
   */
  completedTaskCount: number;
}

/**
 * Main interface representing a project in the system
 */
export interface Project {
  /**
   * Unique identifier for the project
   */
  id: string;

  /**
   * Name of the project
   */
  name: string;

  /**
   * Description of the project
   */
  description: string;

  /**
   * Current status of the project
   */
  status: ProjectStatus;

  /**
   * Category of the project
   */
  category: string;

  /**
   * Owner user object
   */
  owner: User;

  /**
   * ID of the project owner
   */
  ownerId: string;

  /**
   * Array of project members
   */
  members: ProjectMember[];

  /**
   * Project configuration settings
   */
  settings: ProjectSettings;

  /**
   * Array of task lists in the project
   */
  taskLists: TaskList[];

  /**
   * Project metadata including dates and statistics
   */
  metadata: ProjectMetadata;

  /**
   * Array of tags associated with the project
   */
  tags: string[];

  /**
   * Array of custom fields defined for the project
   */
  customFields: CustomField[];
}

/**
 * Interface for project creation/update form data
 */
export interface ProjectFormData {
  /**
   * Name of the project
   */
  name: string;

  /**
   * Description of the project
   */
  description: string;

  /**
   * Status of the project
   */
  status: ProjectStatus;

  /**
   * Category of the project
   */
  category: string;

  /**
   * Tags associated with the project
   */
  tags: string[];
}

/**
 * Interface for project filtering criteria
 */
export interface ProjectFilter {
  /**
   * Filter by project status
   */
  status: ProjectStatus | ProjectStatus[] | null;

  /**
   * Filter by project category
   */
  category: string | string[] | null;

  /**
   * Filter by project tags
   */
  tags: string[] | null;

  /**
   * Search term for filtering projects
   */
  searchTerm: string | null;
}

/**
 * Interface for updating a project member's role
 */
export interface ProjectMemberUpdate {
  /**
   * New role for the project member
   */
  role: ProjectRole;
}

/**
 * Interface for updating a project's status
 */
export interface ProjectStatusUpdate {
  /**
   * New status for the project
   */
  status: ProjectStatus;
}

/**
 * Interface for creating a new task list
 */
export interface TaskListCreate {
  /**
   * Name of the new task list
   */
  name: string;

  /**
   * Description of the new task list
   */
  description: string;
}

/**
 * Interface for updating a task list
 */
export interface TaskListUpdate {
  /**
   * Updated name of the task list
   */
  name: string;

  /**
   * Updated description of the task list
   */
  description: string;

  /**
   * Updated sort order of the task list
   */
  sortOrder: number;
}

/**
 * Interface for paginated project list response
 */
export interface ProjectsResponse {
  /**
   * Array of projects in the current page
   */
  items: Project[];

  /**
   * Total number of projects matching the filter
   */
  total: number;

  /**
   * Current page number
   */
  page: number;

  /**
   * Number of items per page
   */
  pageSize: number;

  /**
   * Total number of pages
   */
  totalPages: number;
}

/**
 * Interface for project statistics and metrics
 */
export interface ProjectStatistics {
  /**
   * Percentage of completed tasks in the project
   */
  taskCompletionRate: number;

  /**
   * Percentage of tasks completed on time
   */
  onTimeCompletionRate: number;

  /**
   * Distribution of tasks by status
   */
  tasksByStatus: Record<string, number>;

  /**
   * Distribution of tasks by assignee
   */
  tasksByAssignee: Record<string, number>;

  /**
   * Number of activities in the last week
   */
  activitiesLastWeek: number;

  /**
   * Number of overdue tasks
   */
  overdueTasks: number;
}