/**
 * Task Service
 * 
 * Service responsible for handling all API requests related to tasks in the Task Management System.
 * Provides functions for creating, reading, updating, and deleting tasks, as well as
 * managing task status, assignments, comments, subtasks, and dependencies.
 *
 * @version 1.0.0
 */

import apiClient from '../client';
import { handleApiError } from '../client';
import { 
  TASK_ENDPOINTS 
} from '../endpoints';
import { 
  Task, 
  TaskCreate, 
  TaskUpdate, 
  TasksFilter, 
  TaskSort, 
  TaskComment, 
  CommentCreate, 
  TasksResponse, 
  Subtask,
  SubtaskCreate,
  SubtaskStatusUpdate,
  TaskAssignmentUpdate,
  TaskStatusUpdate,
  TaskStatistics
} from '../../types/task';
import { AxiosResponse } from 'axios';

/**
 * Retrieves a paginated list of tasks with optional filtering and sorting
 * 
 * @param filters - Optional filters to apply to the task list
 * @param sort - Optional sorting criteria
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @returns Promise resolving to paginated task list response
 */
export const getTasks = async (
  filters: TasksFilter | null = null,
  sort: TaskSort | null = null,
  page: number = 1,
  pageSize: number = 20
): Promise<TasksResponse> => {
  try {
    // Construct query parameters
    const params: Record<string, any> = { page, pageSize };
    
    // Add filters if provided
    if (filters) {
      if (filters.status) params.status = Array.isArray(filters.status) 
        ? filters.status.join(',') 
        : filters.status;
      
      if (filters.priority) params.priority = Array.isArray(filters.priority) 
        ? filters.priority.join(',') 
        : filters.priority;
      
      if (filters.assigneeId) params.assigneeId = filters.assigneeId;
      if (filters.projectId) params.projectId = filters.projectId;
      if (filters.dueDate) params.dueDate = filters.dueDate;
      
      if (filters.dueDateRange) {
        params.dueDateStart = filters.dueDateRange.startDate;
        params.dueDateEnd = filters.dueDateRange.endDate;
      }
      
      if (filters.tags && filters.tags.length > 0) {
        params.tags = filters.tags.join(',');
      }
      
      if (filters.searchTerm) params.q = filters.searchTerm;
    }
    
    // Add sorting if provided
    if (sort) {
      params.sortBy = sort.field;
      params.sortDir = sort.direction;
    }
    
    // Make API request
    const response: AxiosResponse<TasksResponse> = await apiClient.get(
      TASK_ENDPOINTS.BASE,
      { params }
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves a single task by its ID
 * 
 * @param taskId - ID of the task to retrieve
 * @returns Promise resolving to task details
 */
export const getTask = async (taskId: string): Promise<Task> => {
  try {
    const response: AxiosResponse<Task> = await apiClient.get(
      TASK_ENDPOINTS.GET_TASK(taskId)
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Creates a new task
 * 
 * @param taskData - Task data for creation
 * @returns Promise resolving to the created task
 */
export const createTask = async (taskData: TaskCreate): Promise<Task> => {
  try {
    const response: AxiosResponse<Task> = await apiClient.post(
      TASK_ENDPOINTS.BASE,
      taskData
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Updates an existing task
 * 
 * @param taskId - ID of the task to update
 * @param taskData - Updated task data
 * @returns Promise resolving to the updated task
 */
export const updateTask = async (
  taskId: string,
  taskData: TaskUpdate
): Promise<Task> => {
  try {
    const response: AxiosResponse<Task> = await apiClient.put(
      TASK_ENDPOINTS.UPDATE_TASK(taskId),
      taskData
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Deletes a task by its ID
 * 
 * @param taskId - ID of the task to delete
 * @returns Promise that resolves when deletion is successful
 */
export const deleteTask = async (taskId: string): Promise<void> => {
  try {
    await apiClient.delete(TASK_ENDPOINTS.DELETE_TASK(taskId));
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Updates the status of a task
 * 
 * @param taskId - ID of the task to update
 * @param statusUpdate - New status information
 * @returns Promise resolving to the updated task
 */
export const updateTaskStatus = async (
  taskId: string,
  statusUpdate: TaskStatusUpdate
): Promise<Task> => {
  try {
    const response: AxiosResponse<Task> = await apiClient.patch(
      TASK_ENDPOINTS.UPDATE_STATUS(taskId),
      statusUpdate
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Assigns a task to a user or removes assignment
 * 
 * @param taskId - ID of the task to update
 * @param assignmentUpdate - Assignment update information
 * @returns Promise resolving to the updated task
 */
export const assignTask = async (
  taskId: string,
  assignmentUpdate: TaskAssignmentUpdate
): Promise<Task> => {
  try {
    const response: AxiosResponse<Task> = await apiClient.patch(
      TASK_ENDPOINTS.ASSIGN_TASK(taskId),
      assignmentUpdate
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves comments for a specific task
 * 
 * @param taskId - ID of the task
 * @returns Promise resolving to array of task comments
 */
export const getTaskComments = async (taskId: string): Promise<TaskComment[]> => {
  try {
    const response: AxiosResponse<TaskComment[]> = await apiClient.get(
      TASK_ENDPOINTS.COMMENTS(taskId)
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Adds a new comment to a task
 * 
 * @param taskId - ID of the task
 * @param commentData - Comment data for creation
 * @returns Promise resolving to the created comment
 */
export const addComment = async (
  taskId: string,
  commentData: CommentCreate
): Promise<TaskComment> => {
  try {
    const response: AxiosResponse<TaskComment> = await apiClient.post(
      TASK_ENDPOINTS.COMMENTS(taskId),
      commentData
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves subtasks for a specific task
 * 
 * @param taskId - ID of the task
 * @returns Promise resolving to array of subtasks
 */
export const getSubtasks = async (taskId: string): Promise<Subtask[]> => {
  try {
    const response: AxiosResponse<Subtask[]> = await apiClient.get(
      TASK_ENDPOINTS.SUBTASKS(taskId)
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Creates a new subtask for a task
 * 
 * @param taskId - ID of the parent task
 * @param subtaskData - Subtask data for creation
 * @returns Promise resolving to the created subtask
 */
export const createSubtask = async (
  taskId: string,
  subtaskData: SubtaskCreate
): Promise<Subtask> => {
  try {
    const response: AxiosResponse<Subtask> = await apiClient.post(
      TASK_ENDPOINTS.SUBTASKS(taskId),
      subtaskData
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Updates the status of a subtask
 * 
 * @param taskId - ID of the parent task
 * @param subtaskId - ID of the subtask to update
 * @param statusUpdate - Status update information
 * @returns Promise resolving to the updated subtask
 */
export const updateSubtaskStatus = async (
  taskId: string,
  subtaskId: string,
  statusUpdate: SubtaskStatusUpdate
): Promise<Subtask> => {
  try {
    const response: AxiosResponse<Subtask> = await apiClient.patch(
      TASK_ENDPOINTS.SUBTASK(taskId, subtaskId),
      statusUpdate
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Deletes a subtask
 * 
 * @param taskId - ID of the parent task
 * @param subtaskId - ID of the subtask to delete
 * @returns Promise that resolves when deletion is successful
 */
export const deleteSubtask = async (
  taskId: string,
  subtaskId: string
): Promise<void> => {
  try {
    await apiClient.delete(TASK_ENDPOINTS.SUBTASK(taskId, subtaskId));
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Searches for tasks based on search term
 * 
 * @param searchTerm - Term to search for
 * @returns Promise resolving to array of matching tasks
 */
export const searchTasks = async (searchTerm: string): Promise<Task[]> => {
  try {
    const response: AxiosResponse<Task[]> = await apiClient.get(
      TASK_ENDPOINTS.SEARCH,
      { params: { q: searchTerm } }
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves tasks that are due soon within the specified days
 * 
 * @param days - Number of days to look ahead
 * @returns Promise resolving to array of tasks due soon
 */
export const getDueSoonTasks = async (days: number = 3): Promise<Task[]> => {
  try {
    const response: AxiosResponse<Task[]> = await apiClient.get(
      TASK_ENDPOINTS.DUE_SOON,
      { params: { days } }
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves overdue tasks
 * 
 * @returns Promise resolving to array of overdue tasks
 */
export const getOverdueTasks = async (): Promise<Task[]> => {
  try {
    const response: AxiosResponse<Task[]> = await apiClient.get(
      TASK_ENDPOINTS.OVERDUE
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves task statistics, optionally filtered by project
 * 
 * @param projectId - Optional project ID to filter statistics
 * @returns Promise resolving to task statistics
 */
export const getTaskStatistics = async (
  projectId?: string
): Promise<TaskStatistics> => {
  try {
    const params: Record<string, any> = {};
    if (projectId) {
      params.projectId = projectId;
    }
    
    const response: AxiosResponse<TaskStatistics> = await apiClient.get(
      `${TASK_ENDPOINTS.BASE}/statistics`,
      { params }
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};