import { useState, useCallback, useMemo } from 'react'; // react 18.2.x
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query'; // react-query 3.39.x
import { toast } from 'react-toastify'; // react-toastify 9.1.x

import {
  Project,
  ProjectsResponse,
  ProjectFormData,
  ProjectFilter,
  ProjectMember,
  ProjectStatusUpdate,
  ProjectMemberUpdate,
  TaskList,
  TaskListCreate,
  TaskListUpdate,
  ProjectStatistics
} from '../../types/project';

import {
  getProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  updateProjectStatus,
  getProjectMembers,
  addProjectMember,
  updateProjectMember,
  removeProjectMember,
  getProjectTaskLists,
  createTaskList,
  updateTaskList,
  deleteTaskList,
  getProjectStatistics
} from '../services/projectService';

import useAuth from './useAuth';

// Query keys for React Query caching
const QUERY_KEYS = {
  projects: 'projects',
  project: (id: string) => ['project', id],
  members: (id: string) => ['project', id, 'members'],
  taskLists: (id: string) => ['project', id, 'taskLists'],
  statistics: (id: string) => ['project', id, 'statistics']
};

/**
 * Hook for listing and filtering projects with pagination
 * 
 * @param filters Optional filters to apply to project list
 * @param options Optional React Query options
 * @returns Projects data, loading state, error state, and pagination controls
 */
export function useProjects(
  filters: ProjectFilter = {},
  options?: UseQueryOptions<ProjectsResponse, Error>
) {
  const { isAuthenticated } = useAuth();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  const queryClient = useQueryClient();
  
  // Build query function with current pagination and filters
  const queryFn = useCallback(() => {
    if (!isAuthenticated) {
      throw new Error('User must be authenticated to fetch projects');
    }
    return getProjects(page, pageSize, filters);
  }, [isAuthenticated, page, pageSize, filters]);
  
  // Use React Query to fetch projects
  const {
    data,
    isLoading,
    error,
    refetch
  } = useQuery<ProjectsResponse, Error>(
    [QUERY_KEYS.projects, filters, page, pageSize],
    queryFn,
    {
      enabled: isAuthenticated,
      keepPreviousData: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      ...options
    }
  );
  
  // Pagination controls
  const nextPage = useCallback(() => {
    if (data && page < data.totalPages) {
      setPage(page + 1);
    }
  }, [data, page]);
  
  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(page - 1);
    }
  }, [page]);
  
  const goToPage = useCallback((pageNumber: number) => {
    if (data && pageNumber >= 1 && pageNumber <= data.totalPages) {
      setPage(pageNumber);
    }
  }, [data]);
  
  const changePageSize = useCallback((size: number) => {
    setPageSize(size);
    setPage(1); // Reset to first page when changing page size
  }, []);
  
  // Prefetch next page for smoother pagination
  useMemo(() => {
    if (data && page < data.totalPages) {
      queryClient.prefetchQuery(
        [QUERY_KEYS.projects, filters, page + 1, pageSize],
        () => getProjects(page + 1, pageSize, filters)
      );
    }
  }, [queryClient, data, page, pageSize, filters]);
  
  return {
    projects: data?.items || [],
    totalProjects: data?.total || 0,
    currentPage: page,
    totalPages: data?.totalPages || 0,
    pageSize,
    isLoading,
    error,
    refetch,
    pagination: {
      nextPage,
      prevPage,
      goToPage,
      changePageSize
    }
  };
}

/**
 * Hook for fetching and managing a single project
 * 
 * @param projectId The ID of the project to fetch
 * @param options Optional React Query options
 * @returns Project data, loading state, error state, and refetch function
 */
export function useProject(
  projectId: string,
  options?: UseQueryOptions<Project, Error>
) {
  const { isAuthenticated } = useAuth();
  
  const queryFn = useCallback(() => {
    if (!projectId) {
      throw new Error('Project ID is required');
    }
    return getProject(projectId);
  }, [projectId]);
  
  const {
    data: project,
    isLoading,
    error,
    refetch
  } = useQuery<Project, Error>(
    QUERY_KEYS.project(projectId),
    queryFn,
    {
      enabled: !!projectId && isAuthenticated,
      staleTime: 5 * 60 * 1000, // 5 minutes
      ...options
    }
  );
  
  return {
    project,
    isLoading,
    error,
    refetch
  };
}

/**
 * Hook for project creation, update, and deletion operations
 * 
 * @returns Mutation functions for project operations
 */
export function useProjectMutation() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  
  // Create project mutation
  const createMutation = useMutation<Project, Error, ProjectFormData>(
    (newProject) => createProject(newProject),
    {
      onSuccess: (createdProject) => {
        // Invalidate projects list queries
        queryClient.invalidateQueries(QUERY_KEYS.projects);
        
        toast.success('Project created successfully');
      },
      onError: (error) => {
        toast.error(`Failed to create project: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Update project mutation
  const updateMutation = useMutation<
    Project, 
    Error, 
    { id: string; data: ProjectFormData }
  >(
    ({ id, data }) => updateProject(id, data),
    {
      onMutate: async ({ id, data }) => {
        // Cancel any outgoing refetches
        await queryClient.cancelQueries(QUERY_KEYS.project(id));
        
        // Snapshot the previous value
        const previousProject = queryClient.getQueryData<Project>(QUERY_KEYS.project(id));
        
        // Optimistically update the cache
        if (previousProject) {
          queryClient.setQueryData(QUERY_KEYS.project(id), {
            ...previousProject,
            ...data
          });
        }
        
        return { previousProject };
      },
      onSuccess: (updatedProject) => {
        queryClient.invalidateQueries(QUERY_KEYS.projects);
        queryClient.invalidateQueries(QUERY_KEYS.project(updatedProject.id));
        
        toast.success('Project updated successfully');
      },
      onError: (error, variables, context) => {
        // Revert to previous value on error
        if (context?.previousProject) {
          queryClient.setQueryData(
            QUERY_KEYS.project(variables.id),
            context.previousProject
          );
        }
        
        toast.error(`Failed to update project: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Delete project mutation
  const deleteMutation = useMutation<void, Error, string>(
    (projectId) => deleteProject(projectId),
    {
      onSuccess: (_, projectId) => {
        queryClient.invalidateQueries(QUERY_KEYS.projects);
        queryClient.removeQueries(QUERY_KEYS.project(projectId));
        
        toast.success('Project deleted successfully');
      },
      onError: (error) => {
        toast.error(`Failed to delete project: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Update project status mutation
  const updateStatusMutation = useMutation<
    Project, 
    Error, 
    { id: string; status: ProjectStatusUpdate }
  >(
    ({ id, status }) => updateProjectStatus(id, status),
    {
      onMutate: async ({ id, status }) => {
        await queryClient.cancelQueries(QUERY_KEYS.project(id));
        
        const previousProject = queryClient.getQueryData<Project>(QUERY_KEYS.project(id));
        
        if (previousProject) {
          queryClient.setQueryData(QUERY_KEYS.project(id), {
            ...previousProject,
            status: status.status
          });
        }
        
        return { previousProject };
      },
      onSuccess: (updatedProject) => {
        queryClient.invalidateQueries(QUERY_KEYS.projects);
        queryClient.invalidateQueries(QUERY_KEYS.project(updatedProject.id));
        
        toast.success('Project status updated successfully');
      },
      onError: (error, variables, context) => {
        if (context?.previousProject) {
          queryClient.setQueryData(
            QUERY_KEYS.project(variables.id),
            context.previousProject
          );
        }
        
        toast.error(`Failed to update project status: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    createProject: {
      mutate: createMutation.mutate,
      isLoading: createMutation.isLoading,
      error: createMutation.error
    },
    updateProject: {
      mutate: updateMutation.mutate,
      isLoading: updateMutation.isLoading,
      error: updateMutation.error
    },
    deleteProject: {
      mutate: deleteMutation.mutate,
      isLoading: deleteMutation.isLoading,
      error: deleteMutation.error
    },
    updateStatus: {
      mutate: updateStatusMutation.mutate,
      isLoading: updateStatusMutation.isLoading,
      error: updateStatusMutation.error
    }
  };
}

/**
 * Hook for managing project team members
 * 
 * @param projectId The ID of the project
 * @returns Project members and member management functions
 */
export function useProjectMembers(projectId: string) {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // Fetch project members
  const {
    data: members = [],
    isLoading,
    error,
    refetch
  } = useQuery<ProjectMember[], Error>(
    QUERY_KEYS.members(projectId),
    () => getProjectMembers(projectId),
    {
      enabled: !!projectId && isAuthenticated,
      staleTime: 5 * 60 * 1000 // 5 minutes
    }
  );
  
  // Add project member mutation
  const addMemberMutation = useMutation<
    ProjectMember, 
    Error, 
    { userId: string; role: string }
  >(
    ({ userId, role }) => addProjectMember(projectId, userId, role),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.members(projectId));
        queryClient.invalidateQueries(QUERY_KEYS.project(projectId));
        
        toast.success('Team member added successfully');
      },
      onError: (error) => {
        toast.error(`Failed to add team member: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Update member role mutation
  const updateMemberMutation = useMutation<
    ProjectMember, 
    Error, 
    { userId: string; updateData: ProjectMemberUpdate }
  >(
    ({ userId, updateData }) => updateProjectMember(projectId, userId, updateData),
    {
      onMutate: async ({ userId, updateData }) => {
        await queryClient.cancelQueries(QUERY_KEYS.members(projectId));
        
        const previousMembers = queryClient.getQueryData<ProjectMember[]>(
          QUERY_KEYS.members(projectId)
        );
        
        if (previousMembers) {
          const updatedMembers = previousMembers.map(member => 
            member.userId === userId
              ? { ...member, role: updateData.role }
              : member
          );
          
          queryClient.setQueryData(
            QUERY_KEYS.members(projectId),
            updatedMembers
          );
        }
        
        return { previousMembers };
      },
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.members(projectId));
        queryClient.invalidateQueries(QUERY_KEYS.project(projectId));
        
        toast.success('Member role updated successfully');
      },
      onError: (error, variables, context) => {
        if (context?.previousMembers) {
          queryClient.setQueryData(
            QUERY_KEYS.members(projectId),
            context.previousMembers
          );
        }
        
        toast.error(`Failed to update member role: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Remove member mutation
  const removeMemberMutation = useMutation<void, Error, string>(
    (userId) => removeProjectMember(projectId, userId),
    {
      onMutate: async (userId) => {
        await queryClient.cancelQueries(QUERY_KEYS.members(projectId));
        
        const previousMembers = queryClient.getQueryData<ProjectMember[]>(
          QUERY_KEYS.members(projectId)
        );
        
        if (previousMembers) {
          const updatedMembers = previousMembers.filter(
            member => member.userId !== userId
          );
          
          queryClient.setQueryData(
            QUERY_KEYS.members(projectId),
            updatedMembers
          );
        }
        
        return { previousMembers };
      },
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.members(projectId));
        queryClient.invalidateQueries(QUERY_KEYS.project(projectId));
        
        toast.success('Team member removed successfully');
      },
      onError: (error, userId, context) => {
        if (context?.previousMembers) {
          queryClient.setQueryData(
            QUERY_KEYS.members(projectId),
            context.previousMembers
          );
        }
        
        toast.error(`Failed to remove team member: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    members,
    isLoading,
    error,
    refetch,
    addMember: addMemberMutation.mutate,
    isAddingMember: addMemberMutation.isLoading,
    updateMemberRole: updateMemberMutation.mutate,
    isUpdatingMember: updateMemberMutation.isLoading,
    removeMember: removeMemberMutation.mutate,
    isRemovingMember: removeMemberMutation.isLoading
  };
}

/**
 * Hook for managing project task lists
 * 
 * @param projectId The ID of the project
 * @returns Project task lists and task list management functions
 */
export function useProjectTaskLists(projectId: string) {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // Fetch project task lists
  const {
    data: taskLists = [],
    isLoading,
    error,
    refetch
  } = useQuery<TaskList[], Error>(
    QUERY_KEYS.taskLists(projectId),
    () => getProjectTaskLists(projectId),
    {
      enabled: !!projectId && isAuthenticated,
      staleTime: 5 * 60 * 1000 // 5 minutes
    }
  );
  
  // Create task list mutation
  const createTaskListMutation = useMutation<TaskList, Error, TaskListCreate>(
    (taskListData) => createTaskList(projectId, taskListData),
    {
      onSuccess: (newTaskList) => {
        queryClient.invalidateQueries(QUERY_KEYS.taskLists(projectId));
        
        toast.success('Task list created successfully');
      },
      onError: (error) => {
        toast.error(`Failed to create task list: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Update task list mutation
  const updateTaskListMutation = useMutation<
    TaskList, 
    Error, 
    { taskListId: string; data: TaskListUpdate }
  >(
    ({ taskListId, data }) => updateTaskList(projectId, taskListId, data),
    {
      onMutate: async ({ taskListId, data }) => {
        await queryClient.cancelQueries(QUERY_KEYS.taskLists(projectId));
        
        const previousTaskLists = queryClient.getQueryData<TaskList[]>(
          QUERY_KEYS.taskLists(projectId)
        );
        
        if (previousTaskLists) {
          const updatedTaskLists = previousTaskLists.map(taskList => 
            taskList.id === taskListId
              ? { ...taskList, ...data }
              : taskList
          );
          
          queryClient.setQueryData(
            QUERY_KEYS.taskLists(projectId),
            updatedTaskLists
          );
        }
        
        return { previousTaskLists };
      },
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.taskLists(projectId));
        
        toast.success('Task list updated successfully');
      },
      onError: (error, variables, context) => {
        if (context?.previousTaskLists) {
          queryClient.setQueryData(
            QUERY_KEYS.taskLists(projectId),
            context.previousTaskLists
          );
        }
        
        toast.error(`Failed to update task list: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Delete task list mutation
  const deleteTaskListMutation = useMutation<void, Error, string>(
    (taskListId) => deleteTaskList(projectId, taskListId),
    {
      onMutate: async (taskListId) => {
        await queryClient.cancelQueries(QUERY_KEYS.taskLists(projectId));
        
        const previousTaskLists = queryClient.getQueryData<TaskList[]>(
          QUERY_KEYS.taskLists(projectId)
        );
        
        if (previousTaskLists) {
          const updatedTaskLists = previousTaskLists.filter(
            taskList => taskList.id !== taskListId
          );
          
          queryClient.setQueryData(
            QUERY_KEYS.taskLists(projectId),
            updatedTaskLists
          );
        }
        
        return { previousTaskLists };
      },
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.taskLists(projectId));
        
        toast.success('Task list deleted successfully');
      },
      onError: (error, taskListId, context) => {
        if (context?.previousTaskLists) {
          queryClient.setQueryData(
            QUERY_KEYS.taskLists(projectId),
            context.previousTaskLists
          );
        }
        
        toast.error(`Failed to delete task list: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    taskLists,
    isLoading,
    error,
    refetch,
    createTaskList: createTaskListMutation.mutate,
    isCreatingTaskList: createTaskListMutation.isLoading,
    updateTaskList: updateTaskListMutation.mutate,
    isUpdatingTaskList: updateTaskListMutation.isLoading,
    deleteTaskList: deleteTaskListMutation.mutate,
    isDeletingTaskList: deleteTaskListMutation.isLoading
  };
}

/**
 * Hook for fetching project statistics and metrics
 * 
 * @param projectId The ID of the project
 * @returns Project statistics data, loading state, and error state
 */
export function useProjectStatistics(projectId: string) {
  const { isAuthenticated } = useAuth();
  
  const {
    data: statistics,
    isLoading,
    error,
    refetch
  } = useQuery<ProjectStatistics, Error>(
    QUERY_KEYS.statistics(projectId),
    () => getProjectStatistics(projectId),
    {
      enabled: !!projectId && isAuthenticated,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchInterval: 15 * 60 * 1000 // Refresh every 15 minutes
    }
  );
  
  return {
    statistics,
    isLoading,
    error,
    refetch
  };
}