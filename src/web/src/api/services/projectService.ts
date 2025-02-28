/**
 * Project Service
 * 
 * Service layer module that provides functions for interacting with the project management API endpoints.
 * Handles project CRUD operations, member management, task list organization, and project statistics.
 * 
 * @version 1.0.0
 */

import { AxiosResponse } from 'axios'; // v1.5.x
import apiClient from '../client';
import { PROJECT_ENDPOINTS } from '../endpoints';
import {
  Project,
  ProjectsResponse,
  ProjectFormData,
  ProjectMember,
  ProjectStatusUpdate,
  ProjectMemberUpdate,
  TaskList,
  TaskListCreate,
  TaskListUpdate,
  ProjectFilter,
  ProjectStatistics
} from '../../types/project';

/**
 * Fetches a paginated list of projects with optional filtering
 * 
 * @param page - Page number for pagination
 * @param pageSize - Number of items per page
 * @param filters - Optional filters for projects
 * @returns Promise resolving to a paginated list of projects
 */
export async function getProjects(
  page: number = 1,
  pageSize: number = 20,
  filters: ProjectFilter = {}
): Promise<ProjectsResponse> {
  // Construct query parameters
  const params: Record<string, any> = {
    page,
    pageSize,
  };
  
  // Add filters if provided
  if (filters.status) {
    params.status = Array.isArray(filters.status) ? filters.status.join(',') : filters.status;
  }
  
  if (filters.category) {
    params.category = Array.isArray(filters.category) ? filters.category.join(',') : filters.category;
  }
  
  if (filters.tags && filters.tags.length > 0) {
    params.tags = filters.tags.join(',');
  }
  
  if (filters.searchTerm) {
    params.search = filters.searchTerm;
  }
  
  const response: AxiosResponse<ProjectsResponse> = await apiClient.get(
    PROJECT_ENDPOINTS.BASE,
    { params }
  );
  
  return response.data;
}

/**
 * Fetches a single project by its ID
 * 
 * @param id - The ID of the project to fetch
 * @returns Promise resolving to the requested project
 */
export async function getProject(id: string): Promise<Project> {
  const response: AxiosResponse<Project> = await apiClient.get(
    PROJECT_ENDPOINTS.GET_PROJECT(id)
  );
  
  return response.data;
}

/**
 * Creates a new project with the provided data
 * 
 * @param projectData - Data for the new project
 * @returns Promise resolving to the newly created project
 */
export async function createProject(projectData: ProjectFormData): Promise<Project> {
  const response: AxiosResponse<Project> = await apiClient.post(
    PROJECT_ENDPOINTS.BASE,
    projectData
  );
  
  return response.data;
}

/**
 * Updates an existing project with the provided data
 * 
 * @param id - The ID of the project to update
 * @param projectData - Updated project data
 * @returns Promise resolving to the updated project
 */
export async function updateProject(id: string, projectData: ProjectFormData): Promise<Project> {
  const response: AxiosResponse<Project> = await apiClient.put(
    PROJECT_ENDPOINTS.UPDATE_PROJECT(id),
    projectData
  );
  
  return response.data;
}

/**
 * Deletes a project by its ID
 * 
 * @param id - The ID of the project to delete
 * @returns Promise resolving when deletion is complete
 */
export async function deleteProject(id: string): Promise<void> {
  await apiClient.delete(PROJECT_ENDPOINTS.DELETE_PROJECT(id));
}

/**
 * Updates the status of a project
 * 
 * @param id - The ID of the project to update
 * @param statusUpdate - Object containing the new status
 * @returns Promise resolving to the updated project
 */
export async function updateProjectStatus(
  id: string,
  statusUpdate: ProjectStatusUpdate
): Promise<Project> {
  const response: AxiosResponse<Project> = await apiClient.patch(
    PROJECT_ENDPOINTS.UPDATE_STATUS(id),
    statusUpdate
  );
  
  return response.data;
}

/**
 * Fetches the members of a project
 * 
 * @param projectId - The ID of the project
 * @returns Promise resolving to an array of project members
 */
export async function getProjectMembers(projectId: string): Promise<ProjectMember[]> {
  const response: AxiosResponse<ProjectMember[]> = await apiClient.get(
    PROJECT_ENDPOINTS.MEMBERS(projectId)
  );
  
  return response.data;
}

/**
 * Adds a user to a project with the specified role
 * 
 * @param projectId - The ID of the project
 * @param userId - The ID of the user to add
 * @param role - The role to assign to the user
 * @returns Promise resolving to the newly added project member
 */
export async function addProjectMember(
  projectId: string,
  userId: string,
  role: string
): Promise<ProjectMember> {
  const memberData = {
    userId,
    role
  };
  
  const response: AxiosResponse<ProjectMember> = await apiClient.post(
    PROJECT_ENDPOINTS.MEMBERS(projectId),
    memberData
  );
  
  return response.data;
}

/**
 * Updates the role of a project member
 * 
 * @param projectId - The ID of the project
 * @param userId - The ID of the user to update
 * @param updateData - Object containing the updated role
 * @returns Promise resolving to the updated project member
 */
export async function updateProjectMember(
  projectId: string,
  userId: string,
  updateData: ProjectMemberUpdate
): Promise<ProjectMember> {
  const response: AxiosResponse<ProjectMember> = await apiClient.patch(
    PROJECT_ENDPOINTS.MEMBER(projectId, userId),
    updateData
  );
  
  return response.data;
}

/**
 * Removes a member from a project
 * 
 * @param projectId - The ID of the project
 * @param userId - The ID of the user to remove
 * @returns Promise resolving when member removal is complete
 */
export async function removeProjectMember(
  projectId: string,
  userId: string
): Promise<void> {
  await apiClient.delete(PROJECT_ENDPOINTS.MEMBER(projectId, userId));
}

/**
 * Fetches the task lists for a project
 * 
 * @param projectId - The ID of the project
 * @returns Promise resolving to an array of project task lists
 */
export async function getProjectTaskLists(projectId: string): Promise<TaskList[]> {
  const response: AxiosResponse<TaskList[]> = await apiClient.get(
    PROJECT_ENDPOINTS.TASK_LISTS(projectId)
  );
  
  return response.data;
}

/**
 * Creates a new task list within a project
 * 
 * @param projectId - The ID of the project
 * @param taskListData - Data for the new task list
 * @returns Promise resolving to the newly created task list
 */
export async function createTaskList(
  projectId: string,
  taskListData: TaskListCreate
): Promise<TaskList> {
  const response: AxiosResponse<TaskList> = await apiClient.post(
    PROJECT_ENDPOINTS.TASK_LISTS(projectId),
    taskListData
  );
  
  return response.data;
}

/**
 * Updates an existing task list
 * 
 * @param projectId - The ID of the project
 * @param taskListId - The ID of the task list to update
 * @param taskListData - Updated task list data
 * @returns Promise resolving to the updated task list
 */
export async function updateTaskList(
  projectId: string,
  taskListId: string,
  taskListData: TaskListUpdate
): Promise<TaskList> {
  const response: AxiosResponse<TaskList> = await apiClient.put(
    `${PROJECT_ENDPOINTS.TASK_LISTS(projectId)}/${taskListId}`,
    taskListData
  );
  
  return response.data;
}

/**
 * Deletes a task list from a project
 * 
 * @param projectId - The ID of the project
 * @param taskListId - The ID of the task list to delete
 * @returns Promise resolving when deletion is complete
 */
export async function deleteTaskList(
  projectId: string,
  taskListId: string
): Promise<void> {
  await apiClient.delete(
    `${PROJECT_ENDPOINTS.TASK_LISTS(projectId)}/${taskListId}`
  );
}

/**
 * Fetches statistics and metrics for a project
 * 
 * @param projectId - The ID of the project
 * @returns Promise resolving to the project statistics
 */
export async function getProjectStatistics(projectId: string): Promise<ProjectStatistics> {
  const response: AxiosResponse<ProjectStatistics> = await apiClient.get(
    PROJECT_ENDPOINTS.STATISTICS(projectId)
  );
  
  return response.data;
}