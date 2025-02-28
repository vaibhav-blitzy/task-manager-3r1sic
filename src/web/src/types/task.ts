/**
 * TypeScript type definitions for tasks and related entities in the Task Management System
 * 
 * @version 1.0.0
 */

import { User } from '../types/user';
import { Project } from '../types/project';
import { FileAttachment } from '../types/file';

/**
 * Enumeration of possible task statuses
 */
export enum TaskStatus {
  CREATED = 'created',
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in-progress',
  ON_HOLD = 'on-hold',
  IN_REVIEW = 'in-review',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Enumeration of possible task priorities
 */
export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

/**
 * Enumeration of task dependency relationship types
 */
export enum DependencyType {
  BLOCKS = 'blocks',
  IS_BLOCKED_BY = 'is-blocked-by'
}

/**
 * Interface for subtask data structure
 */
export interface Subtask {
  /**
   * Unique identifier for the subtask
   */
  id: string;
  
  /**
   * Title of the subtask
   */
  title: string;
  
  /**
   * Whether the subtask is completed
   */
  completed: boolean;
  
  /**
   * ID of the user assigned to the subtask
   */
  assigneeId: string;
}

/**
 * Interface for task dependency relationship
 */
export interface TaskDependency {
  /**
   * ID of the related task
   */
  taskId: string;
  
  /**
   * Type of dependency relationship
   */
  type: DependencyType;
}

/**
 * Interface for task comments
 */
export interface TaskComment {
  /**
   * Unique identifier for the comment
   */
  id: string;
  
  /**
   * Text content of the comment
   */
  content: string;
  
  /**
   * User who created the comment
   */
  createdBy: User;
  
  /**
   * ISO date string when the comment was created
   */
  createdAt: string;
  
  /**
   * ISO date string when the comment was last updated, if applicable
   */
  updatedAt: string;
}

/**
 * Interface for task activity logs
 */
export interface TaskActivity {
  /**
   * Type of activity (e.g., status-change, comment, assignment)
   */
  type: string;
  
  /**
   * User who performed the activity
   */
  user: User;
  
  /**
   * ISO date string when the activity occurred
   */
  timestamp: string;
  
  /**
   * Additional details about the activity
   */
  details: Record<string, any>;
}

/**
 * Interface for task metadata
 */
export interface TaskMetadata {
  /**
   * ISO date string when the task was created
   */
  created: string;
  
  /**
   * ISO date string when the task was last updated
   */
  lastUpdated: string;
  
  /**
   * ISO date string when the task was completed, if applicable
   */
  completedAt: string | null;
  
  /**
   * Estimated time to complete the task in minutes
   */
  timeEstimate: number | null;
  
  /**
   * Actual time spent on the task in minutes
   */
  timeSpent: number | null;
}

/**
 * Main interface for task data structure
 */
export interface Task {
  /**
   * Unique identifier for the task
   */
  id: string;
  
  /**
   * Title of the task
   */
  title: string;
  
  /**
   * Description of the task, may include markdown
   */
  description: string;
  
  /**
   * Current status of the task
   */
  status: TaskStatus;
  
  /**
   * Priority level of the task
   */
  priority: TaskPriority;
  
  /**
   * ISO date string for when the task is due
   */
  dueDate: string | null;
  
  /**
   * User who created the task
   */
  createdBy: User;
  
  /**
   * User assigned to the task, if any
   */
  assignee: User | null;
  
  /**
   * Project the task belongs to, if any
   */
  project: Project | null;
  
  /**
   * Tags associated with the task
   */
  tags: string[];
  
  /**
   * File attachments associated with the task
   */
  attachments: FileAttachment[];
  
  /**
   * Subtasks within this task
   */
  subtasks: Subtask[];
  
  /**
   * Task dependencies
   */
  dependencies: TaskDependency[];
  
  /**
   * Comments on the task
   */
  comments: TaskComment[];
  
  /**
   * Activity history for the task
   */
  activity: TaskActivity[];
  
  /**
   * Task metadata
   */
  metadata: TaskMetadata;
}

/**
 * Interface for task creation payload
 */
export interface TaskCreate {
  /**
   * Title of the task
   */
  title: string;
  
  /**
   * Description of the task
   */
  description: string;
  
  /**
   * Initial status of the task
   */
  status: TaskStatus;
  
  /**
   * Priority level of the task
   */
  priority: TaskPriority;
  
  /**
   * ISO date string for when the task is due
   */
  dueDate: string | null;
  
  /**
   * ID of the user to assign the task to
   */
  assigneeId: string | null;
  
  /**
   * ID of the project to associate the task with
   */
  projectId: string | null;
  
  /**
   * Tags to associate with the task
   */
  tags: string[];
  
  /**
   * Initial subtasks to create
   */
  subtasks: Omit<Subtask, 'id'>[];
}

/**
 * Interface for task update payload
 */
export interface TaskUpdate {
  /**
   * Updated title of the task
   */
  title: string;
  
  /**
   * Updated description of the task
   */
  description: string;
  
  /**
   * Updated status of the task
   */
  status: TaskStatus;
  
  /**
   * Updated priority level of the task
   */
  priority: TaskPriority;
  
  /**
   * Updated due date
   */
  dueDate: string | null;
  
  /**
   * ID of the user to assign the task to
   */
  assigneeId: string | null;
  
  /**
   * ID of the project to associate the task with
   */
  projectId: string | null;
  
  /**
   * Updated tags
   */
  tags: string[];
}

/**
 * Interface for task status update payload
 */
export interface TaskStatusUpdate {
  /**
   * New status for the task
   */
  status: TaskStatus;
}

/**
 * Interface for task assignment update payload
 */
export interface TaskAssignmentUpdate {
  /**
   * ID of the user to assign the task to, or null to unassign
   */
  assigneeId: string | null;
}

/**
 * Interface for subtask creation payload
 */
export interface SubtaskCreate {
  /**
   * Title of the subtask
   */
  title: string;
  
  /**
   * ID of the user to assign the subtask to
   */
  assigneeId: string | null;
}

/**
 * Interface for subtask status update payload
 */
export interface SubtaskStatusUpdate {
  /**
   * Whether the subtask is completed
   */
  completed: boolean;
}

/**
 * Interface for comment creation payload
 */
export interface CommentCreate {
  /**
   * Text content of the comment
   */
  content: string;
}

/**
 * Interface for paginated tasks response
 */
export interface TasksResponse {
  /**
   * Array of tasks in the current page
   */
  items: Task[];
  
  /**
   * Total number of tasks matching the filter
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
 * Interface for task filtering parameters
 */
export interface TasksFilter {
  /**
   * Filter by task status
   */
  status: TaskStatus | TaskStatus[] | null;
  
  /**
   * Filter by task priority
   */
  priority: TaskPriority | TaskPriority[] | null;
  
  /**
   * Filter by assignee ID
   */
  assigneeId: string | null;
  
  /**
   * Filter by project ID
   */
  projectId: string | null;
  
  /**
   * Filter by specific due date
   */
  dueDate: string | null;
  
  /**
   * Filter by due date range
   */
  dueDateRange: {startDate: string, endDate: string} | null;
  
  /**
   * Filter by tags
   */
  tags: string[] | null;
  
  /**
   * Search term for filtering tasks by title or description
   */
  searchTerm: string | null;
}

/**
 * Enum for task sorting field options
 */
export enum TasksSortField {
  TITLE = 'title',
  STATUS = 'status',
  PRIORITY = 'priority',
  DUE_DATE = 'dueDate',
  CREATED_AT = 'created',
  UPDATED_AT = 'lastUpdated'
}

/**
 * Enum for sort direction options
 */
export enum SortDirection {
  ASC = 'asc',
  DESC = 'desc'
}

/**
 * Interface for task sorting parameters
 */
export interface TaskSort {
  /**
   * Field to sort by
   */
  field: TasksSortField;
  
  /**
   * Sort direction
   */
  direction: SortDirection;
}

/**
 * Interface for task statistics data
 */
export interface TaskStatistics {
  /**
   * Total number of tasks
   */
  total: number;
  
  /**
   * Number of tasks by status
   */
  byStatus: Record<TaskStatus, number>;
  
  /**
   * Number of tasks by priority
   */
  byPriority: Record<TaskPriority, number>;
  
  /**
   * Number of tasks completed in the last 7 days
   */
  completedLast7Days: number;
  
  /**
   * Number of tasks due soon (next 3 days)
   */
  dueSoon: number;
  
  /**
   * Number of overdue tasks
   */
  overdue: number;
}