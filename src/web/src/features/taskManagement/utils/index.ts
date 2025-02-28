import { Task } from '../../types/task';
import { formatDate } from '../../utils/date';
import { 
  TASK_STATUS_LABELS, 
  TASK_STATUS_COLORS, 
  TASK_PRIORITY_LABELS, 
  TASK_PRIORITY_COLORS 
} from '../../config/constants';

/**
 * Converts a task status to a user-friendly display name
 * @param status - The task status
 * @returns Formatted status text for display
 */
export function getStatusDisplayName(status: string): string {
  return TASK_STATUS_LABELS[status] || status;
}

/**
 * Returns a color code or CSS class for the given task status
 * @param status - The task status
 * @returns CSS color or color class name
 */
export function getStatusColor(status: string): string {
  return TASK_STATUS_COLORS[status] || '#6B7280'; // Default gray color
}

/**
 * Converts a task priority to a user-friendly display name
 * @param priority - The task priority
 * @returns Formatted priority text for display
 */
export function getPriorityDisplayName(priority: string): string {
  return TASK_PRIORITY_LABELS[priority] || priority;
}

/**
 * Returns a color code or CSS class for the given task priority
 * @param priority - The task priority
 * @returns CSS color or color class name
 */
export function getPriorityColor(priority: string): string {
  return TASK_PRIORITY_COLORS[priority] || '#6B7280'; // Default gray color
}

/**
 * Checks if a task is in a completed state
 * @param task - The task to check
 * @returns True if task is completed, false otherwise
 */
export function isTaskComplete(task: Task): boolean {
  return task.status === 'completed';
}

/**
 * Checks if a task is overdue based on its due date
 * @param task - The task to check
 * @returns True if task is overdue, false otherwise
 */
export function isTaskOverdue(task: Task): boolean {
  if (!task.dueDate || isTaskComplete(task)) {
    return false;
  }
  
  const dueDate = new Date(task.dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Set to start of day
  
  return dueDate < today;
}

/**
 * Checks if a task is due soon (within a specified number of days)
 * @param task - The task to check
 * @param days - Number of days to consider "soon" (default 3)
 * @returns True if task is due within specified days, false otherwise
 */
export function isTaskDueSoon(task: Task, days: number = 3): boolean {
  if (!task.dueDate || isTaskComplete(task)) {
    return false;
  }
  
  const dueDate = new Date(task.dueDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Set to start of day
  
  if (dueDate < today) {
    return false; // Already overdue
  }
  
  const futureDate = new Date(today);
  futureDate.setDate(futureDate.getDate() + days);
  
  return dueDate <= futureDate;
}

/**
 * Formats a task's due date for display with optional relative time indicators
 * @param task - The task containing the due date
 * @param includeRelative - Whether to include relative indicators (Today, Tomorrow, etc.)
 * @returns Formatted date string
 */
export function formatTaskDueDate(task: Task, includeRelative: boolean = true): string {
  if (!task.dueDate) {
    return '';
  }
  
  const dueDate = new Date(task.dueDate);
  
  if (includeRelative) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (dueDate.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (dueDate.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else if (dueDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
  }
  
  return formatDate(task.dueDate);
}

/**
 * Checks if a task can transition to a new status based on state machine rules
 * @param task - The current task
 * @param newStatus - The target status
 * @returns True if transition is allowed, false otherwise
 */
export function canChangeTaskStatus(task: Task, newStatus: string): boolean {
  // Define the allowed transitions for each status
  const allowedTransitions: Record<string, string[]> = {
    'created': ['assigned', 'in-progress', 'cancelled'],
    'assigned': ['in-progress', 'on-hold', 'cancelled'],
    'in-progress': ['on-hold', 'in-review', 'completed', 'cancelled'],
    'on-hold': ['in-progress', 'cancelled'],
    'in-review': ['in-progress', 'completed', 'cancelled'],
    'completed': ['in-progress'], // Can reopen to in-progress
    'cancelled': ['created'] // Can restart from beginning
  };
  
  // Get allowed transitions for the current status
  const transitions = allowedTransitions[task.status] || [];
  
  // Check if the new status is in the allowed transitions
  return transitions.includes(newStatus);
}

/**
 * Calculates the completion percentage of a task based on subtasks
 * @param task - The task to calculate completion for
 * @returns Percentage of completion from 0-100
 */
export function calculateTaskCompletionPercentage(task: Task): number {
  if (!task.subtasks || task.subtasks.length === 0) {
    return 0;
  }
  
  const totalSubtasks = task.subtasks.length;
  const completedSubtasks = task.subtasks.filter(subtask => subtask.completed).length;
  
  return Math.round((completedSubtasks / totalSubtasks) * 100);
}

/**
 * Sorts an array of tasks by their due dates
 * @param tasks - Array of tasks to sort
 * @param direction - Sort direction ('asc' or 'desc')
 * @returns Sorted array of tasks
 */
export function sortTasksByDueDate(tasks: Task[], direction: string = 'asc'): Task[] {
  return [...tasks].sort((a, b) => {
    // Handle tasks without due dates
    if (!a.dueDate && !b.dueDate) return 0;
    if (!a.dueDate) return direction === 'asc' ? 1 : -1;  // null due dates go to the end in asc, start in desc
    if (!b.dueDate) return direction === 'asc' ? -1 : 1;
    
    const dateA = new Date(a.dueDate);
    const dateB = new Date(b.dueDate);
    
    return direction === 'asc' 
      ? dateA.getTime() - dateB.getTime() 
      : dateB.getTime() - dateA.getTime();
  });
}

/**
 * Sorts an array of tasks by their priority
 * @param tasks - Array of tasks to sort
 * @param direction - Sort direction ('asc' or 'desc')
 * @returns Sorted array of tasks
 */
export function sortTasksByPriority(tasks: Task[], direction: string = 'asc'): Task[] {
  // Define priority order (higher number = higher priority)
  const priorityValues: Record<string, number> = {
    'urgent': 3,
    'high': 2,
    'medium': 1,
    'low': 0
  };
  
  return [...tasks].sort((a, b) => {
    const priorityA = priorityValues[a.priority] || 0;
    const priorityB = priorityValues[b.priority] || 0;
    
    return direction === 'asc' 
      ? priorityA - priorityB 
      : priorityB - priorityA;
  });
}

/**
 * Filters an array of tasks by their status
 * @param tasks - Array of tasks to filter
 * @param statuses - Array of statuses to include
 * @returns Filtered array of tasks
 */
export function filterTasksByStatus(tasks: Task[], statuses: string[]): Task[] {
  if (!statuses || statuses.length === 0) {
    return tasks;
  }
  
  return tasks.filter(task => statuses.includes(task.status));
}

/**
 * Filters an array of tasks by their assignee
 * @param tasks - Array of tasks to filter
 * @param assigneeId - ID of the assignee to filter by
 * @returns Filtered array of tasks
 */
export function filterTasksByAssignee(tasks: Task[], assigneeId: string): Task[] {
  if (!assigneeId) {
    return tasks;
  }
  
  return tasks.filter(task => task.assignee && task.assignee.id === assigneeId);
}

/**
 * Searches tasks based on query string matching against title and description
 * @param tasks - Array of tasks to search
 * @param query - Search query string
 * @returns Array of tasks matching the search query
 */
export function searchTasks(tasks: Task[], query: string): Task[] {
  if (!query || query.trim() === '') {
    return tasks;
  }
  
  const searchTerm = query.toLowerCase().trim();
  
  return tasks.filter(task => {
    const titleMatch = task.title.toLowerCase().includes(searchTerm);
    const descriptionMatch = task.description?.toLowerCase().includes(searchTerm);
    
    return titleMatch || descriptionMatch;
  });
}

/**
 * Validates task input data for creation or updates
 * @param taskData - Object containing task data to validate
 * @returns Object with validation errors or empty object if valid
 */
export function validateTaskInput(taskData: Record<string, any>): Record<string, string> {
  const errors: Record<string, string> = {};
  
  // Validate required fields
  if (!taskData.title || taskData.title.trim() === '') {
    errors.title = 'Title is required';
  }
  
  // Validate due date format if provided
  if (taskData.dueDate) {
    const datePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/;
    if (!datePattern.test(taskData.dueDate) && !(taskData.dueDate instanceof Date)) {
      errors.dueDate = 'Invalid date format';
    }
  }
  
  // Validate status if provided
  if (taskData.status) {
    const validStatuses = ['created', 'assigned', 'in-progress', 'on-hold', 'in-review', 'completed', 'cancelled'];
    if (!validStatuses.includes(taskData.status)) {
      errors.status = 'Invalid status value';
    }
  }
  
  // Validate priority if provided
  if (taskData.priority) {
    const validPriorities = ['low', 'medium', 'high', 'urgent'];
    if (!validPriorities.includes(taskData.priority)) {
      errors.priority = 'Invalid priority value';
    }
  }
  
  return errors;
}

/**
 * Groups tasks by their status for Kanban board views
 * @param tasks - Array of tasks to group
 * @returns Object with tasks grouped by status
 */
export function groupTasksByStatus(tasks: Task[]): Record<string, Task[]> {
  const groupedTasks: Record<string, Task[]> = {};
  
  // Initialize all status groups with empty arrays to ensure they exist even if no tasks
  const statusTypes = ['created', 'assigned', 'in-progress', 'on-hold', 'in-review', 'completed', 'cancelled'];
  statusTypes.forEach(status => {
    groupedTasks[status] = [];
  });
  
  // Group tasks by status
  tasks.forEach(task => {
    if (!groupedTasks[task.status]) {
      groupedTasks[task.status] = [];
    }
    groupedTasks[task.status].push(task);
  });
  
  return groupedTasks;
}