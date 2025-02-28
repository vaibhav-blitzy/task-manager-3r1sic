/**
 * Custom React hooks for task management using React Query
 * 
 * Provides hooks for fetching, creating, updating, and managing tasks with
 * efficient data fetching, caching, and mutation capabilities.
 * 
 * @version 1.0.0
 */

import { useState, useCallback, useMemo } from 'react'; // react ^18.2.0
import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from 'react-query'; // react-query ^3.39.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.0

import { 
  Task, 
  TasksResponse, 
  TaskCreate, 
  TaskUpdate, 
  TasksFilter, 
  TaskStatusUpdate, 
  TaskAssignmentUpdate, 
  TaskComment, 
  CommentCreate, 
  Subtask, 
  SubtaskCreate, 
  SubtaskStatusUpdate, 
  TaskSort,
  TaskStatistics
} from '../../types/task';

import { 
  getTasks, 
  getTask, 
  createTask, 
  updateTask, 
  deleteTask, 
  updateTaskStatus, 
  assignTask, 
  getTaskComments, 
  addComment, 
  getDueSoonTasks, 
  getOverdueTasks,
  getTaskStatistics
} from '../services/taskService';

import useAuth from './useAuth';

/**
 * Hook for fetching a paginated list of tasks with optional filtering and sorting
 * 
 * @param filters - Optional filters to apply to the task list
 * @param sort - Optional sorting criteria
 * @param options - Additional React Query options
 * @returns Query result with tasks data, loading state, pagination controls, and refetch function
 */
export const useTasks = (
  filters?: TasksFilter,
  sort?: TaskSort,
  options?: UseQueryOptions<TasksResponse>
) => {
  // Local state for pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  // Get authentication state to check if the user is authenticated
  const { isAuthenticated } = useAuth();
  
  // Create a query key that includes all dependencies
  const queryKey = useMemo(() => 
    ['tasks', { filters, sort, page, pageSize }], 
    [filters, sort, page, pageSize]
  );
  
  // Use React Query's useQuery hook to fetch tasks
  const { 
    data, 
    isLoading, 
    isError, 
    error, 
    refetch 
  } = useQuery<TasksResponse>(
    queryKey,
    () => getTasks(filters || null, sort || null, page, pageSize),
    {
      // Only fetch when authenticated
      enabled: isAuthenticated,
      // Keep previous data while loading new data
      keepPreviousData: true,
      // Provide default values for the data
      placeholderData: { 
        items: [], 
        total: 0, 
        page: 1, 
        pageSize: 20, 
        totalPages: 1 
      },
      // Merge with any user-provided options
      ...options
    }
  );
  
  // Pagination control functions
  const nextPage = useCallback(() => {
    if (data && page < data.totalPages) {
      setPage(prevPage => prevPage + 1);
    }
  }, [data, page]);
  
  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(prevPage => prevPage - 1);
    }
  }, [page]);
  
  // Return everything needed to render and control the task list
  return {
    tasks: data?.items || [],
    totalTasks: data?.total || 0,
    page: data?.page || 1,
    pageSize: data?.pageSize || 20,
    totalPages: data?.totalPages || 1,
    isLoading,
    isError,
    error,
    refetch,
    // Pagination controls
    nextPage,
    prevPage,
    setPage,
    setPageSize,
  };
};

/**
 * Hook for fetching a single task by ID
 * 
 * @param taskId - ID of the task to fetch
 * @param options - Additional React Query options
 * @returns Query result with single task data, loading state, and error
 */
export const useTask = (
  taskId: string,
  options?: UseQueryOptions<Task>
) => {
  // Create a query key based on the task ID
  const queryKey = useMemo(() => ['task', taskId], [taskId]);
  
  // Use React Query to fetch the task
  return useQuery<Task>(
    queryKey,
    () => getTask(taskId),
    {
      // Only fetch if taskId is provided
      enabled: !!taskId,
      // Don't refetch on window focus for individual task details
      refetchOnWindowFocus: false,
      ...options
    }
  );
};

/**
 * Hook providing mutation functions for task CRUD operations
 * 
 * @returns Mutation functions: createTask, updateTask, deleteTask with loading and error states
 */
export const useTaskMutations = () => {
  const queryClient = useQueryClient();
  
  // Create task mutation
  const createTaskMutation = useMutation(
    (newTask: TaskCreate) => createTask(newTask),
    {
      onSuccess: (createdTask) => {
        // Invalidate tasks query to refetch the list
        queryClient.invalidateQueries('tasks');
        toast.success('Task created successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to create task: ${error.message}`);
      }
    }
  );
  
  // Update task mutation
  const updateTaskMutation = useMutation(
    ({ taskId, taskData }: { taskId: string; taskData: TaskUpdate }) => 
      updateTask(taskId, taskData),
    {
      onSuccess: (updatedTask) => {
        // Invalidate the specific task query
        queryClient.invalidateQueries(['task', updatedTask.id]);
        // Invalidate the tasks list
        queryClient.invalidateQueries('tasks');
        toast.success('Task updated successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to update task: ${error.message}`);
      }
    }
  );
  
  // Delete task mutation
  const deleteTaskMutation = useMutation(
    (taskId: string) => deleteTask(taskId),
    {
      onSuccess: (_, taskId) => {
        // Invalidate the tasks list
        queryClient.invalidateQueries('tasks');
        // Remove the specific task from the cache
        queryClient.removeQueries(['task', taskId]);
        toast.success('Task deleted successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to delete task: ${error.message}`);
      }
    }
  );
  
  return {
    createTask: {
      mutate: createTaskMutation.mutate,
      isLoading: createTaskMutation.isLoading,
      error: createTaskMutation.error
    },
    updateTask: {
      mutate: updateTaskMutation.mutate,
      isLoading: updateTaskMutation.isLoading,
      error: updateTaskMutation.error
    },
    deleteTask: {
      mutate: deleteTaskMutation.mutate,
      isLoading: deleteTaskMutation.isLoading,
      error: deleteTaskMutation.error
    }
  };
};

/**
 * Hook for updating a task's status
 * 
 * @returns Mutation function and state for updating task status
 */
export const useTaskStatusUpdate = () => {
  const queryClient = useQueryClient();
  
  // Status update mutation
  const statusMutation = useMutation(
    ({ taskId, status }: { taskId: string; status: TaskStatusUpdate }) => 
      updateTaskStatus(taskId, status),
    {
      onSuccess: (updatedTask) => {
        // Update the task in the cache
        queryClient.setQueryData(['task', updatedTask.id], updatedTask);
        
        // Update the task in the tasks list cache if it exists
        queryClient.setQueriesData('tasks', (old: any) => {
          if (!old) return old;
          
          return {
            ...old,
            items: old.items.map((task: Task) => 
              task.id === updatedTask.id ? updatedTask : task
            )
          };
        });
        
        toast.success(`Task status updated to ${updatedTask.status}`);
      },
      onError: (error: any) => {
        toast.error(`Failed to update task status: ${error.message}`);
      }
    }
  );
  
  return {
    updateStatus: statusMutation.mutate,
    isLoading: statusMutation.isLoading,
    error: statusMutation.error
  };
};

/**
 * Hook for assigning a task to a user
 * 
 * @returns Mutation function and state for task assignment
 */
export const useTaskAssignment = () => {
  const queryClient = useQueryClient();
  
  // Assignment mutation
  const assignMutation = useMutation(
    ({ taskId, assigneeId }: { taskId: string; assigneeId: TaskAssignmentUpdate }) => 
      assignTask(taskId, assigneeId),
    {
      onSuccess: (updatedTask) => {
        // Update the task in the cache
        queryClient.setQueryData(['task', updatedTask.id], updatedTask);
        
        // Update the task in the tasks list cache if it exists
        queryClient.setQueriesData('tasks', (old: any) => {
          if (!old) return old;
          
          return {
            ...old,
            items: old.items.map((task: Task) => 
              task.id === updatedTask.id ? updatedTask : task
            )
          };
        });
        
        toast.success(
          updatedTask.assignee 
            ? `Task assigned to ${updatedTask.assignee.firstName} ${updatedTask.assignee.lastName}` 
            : 'Task unassigned'
        );
      },
      onError: (error: any) => {
        toast.error(`Failed to assign task: ${error.message}`);
      }
    }
  );
  
  return {
    assignTask: assignMutation.mutate,
    isLoading: assignMutation.isLoading,
    error: assignMutation.error
  };
};

/**
 * Hook for fetching and managing comments on a task
 * 
 * @param taskId - ID of the task to fetch comments for
 * @param options - Additional React Query options
 * @returns Comments data, loading state, and addComment function
 */
export const useTaskComments = (
  taskId: string,
  options?: UseQueryOptions<TaskComment[]>
) => {
  const queryClient = useQueryClient();
  
  // Query for fetching comments
  const commentsQuery = useQuery<TaskComment[]>(
    ['taskComments', taskId],
    () => getTaskComments(taskId),
    {
      enabled: !!taskId,
      ...options
    }
  );
  
  // Mutation for adding a comment
  const addCommentMutation = useMutation(
    (commentData: CommentCreate) => addComment(taskId, commentData),
    {
      onSuccess: (newComment) => {
        // Update the comments in the cache
        queryClient.setQueryData(['taskComments', taskId], (old: TaskComment[] = []) => 
          [...old, newComment]
        );
        
        toast.success('Comment added');
      },
      onError: (error: any) => {
        toast.error(`Failed to add comment: ${error.message}`);
      }
    }
  );
  
  return {
    comments: commentsQuery.data || [],
    isLoading: commentsQuery.isLoading,
    error: commentsQuery.error,
    addComment: addCommentMutation.mutate,
    isAddingComment: addCommentMutation.isLoading
  };
};

/**
 * Hook for fetching tasks due within a specified number of days
 * 
 * @param days - Number of days to look ahead
 * @param options - Additional React Query options
 * @returns Query result with tasks due soon, loading state, and error
 */
export const useDueSoonTasks = (
  days: number = 3,
  options?: UseQueryOptions<Task[]>
) => {
  // Create a memoized query key
  const queryKey = useMemo(() => ['tasks', 'dueSoon', days], [days]);
  
  // Use React Query to fetch the due soon tasks
  return useQuery<Task[]>(
    queryKey,
    () => getDueSoonTasks(days),
    {
      // Keep the data fresh, but don't refetch too often
      staleTime: 5 * 60 * 1000, // 5 minutes
      ...options
    }
  );
};

/**
 * Hook for fetching overdue tasks
 * 
 * @param options - Additional React Query options
 * @returns Query result with overdue tasks, loading state, and error
 */
export const useOverdueTasks = (
  options?: UseQueryOptions<Task[]>
) => {
  // Use React Query to fetch the overdue tasks
  return useQuery<Task[]>(
    ['tasks', 'overdue'],
    getOverdueTasks,
    {
      // Keep the data fresh, but don't refetch too often
      staleTime: 5 * 60 * 1000, // 5 minutes
      ...options
    }
  );
};

/**
 * Hook for searching tasks based on text input
 * 
 * @param searchTerm - Term to search for
 * @param options - Additional React Query options
 * @returns Query result with matching tasks, loading state, and error
 */
export const useTaskSearch = (
  searchTerm: string,
  options?: UseQueryOptions<Task[]>
) => {
  // Create a memoized query key
  const queryKey = useMemo(() => ['tasks', 'search', searchTerm], [searchTerm]);
  
  // Note: In a production app, we would implement proper debouncing here
  // This is a simplified version that will trigger for each search term change
  const searchFunction = useCallback(
    () => searchTasks(searchTerm),
    [searchTerm]
  );
  
  // Use React Query to fetch the search results
  return useQuery<Task[]>(
    queryKey,
    searchFunction,
    {
      // Only search if there's a search term
      enabled: searchTerm.length > 2,
      // Don't keep old data when search term changes
      keepPreviousData: false,
      ...options
    }
  );
};

/**
 * Hook for fetching task statistics, optionally filtered by project
 * 
 * @param projectId - Optional project ID to filter statistics
 * @param options - Additional React Query options
 * @returns Query result with task statistics, loading state, and error
 */
export const useTaskStatistics = (
  projectId?: string,
  options?: UseQueryOptions<TaskStatistics>
) => {
  // Create a query key based on the project ID
  const queryKey = useMemo(
    () => projectId ? ['taskStatistics', projectId] : ['taskStatistics'],
    [projectId]
  );
  
  // Use React Query to fetch the statistics
  return useQuery<TaskStatistics>(
    queryKey,
    () => getTaskStatistics(projectId),
    {
      // Cache statistics for a moderate amount of time
      staleTime: 10 * 60 * 1000, // 10 minutes
      ...options
    }
  );
};

/**
 * Hook for fetching tasks assigned to the current user
 * 
 * @param options - Additional React Query options
 * @returns Query result with user's assigned tasks, loading state, and error
 */
export const useMyTasks = (
  options?: UseQueryOptions<TasksResponse>
) => {
  const { user, isAuthenticated } = useAuth();
  
  // Create a filter with the current user's ID as the assignee
  const filter: TasksFilter = useMemo(() => ({
    assigneeId: user?.id || null,
    status: null,
    priority: null,
    projectId: null,
    dueDate: null,
    dueDateRange: null,
    tags: null,
    searchTerm: null
  }), [user?.id]);
  
  // Use the useTasks hook with the filter
  return useTasks(filter, undefined, {
    ...options,
    // Only fetch when user is authenticated
    enabled: isAuthenticated && !!user?.id && (options?.enabled !== false)
  });
};

/**
 * Hook for fetching tasks belonging to a specific project
 * 
 * @param projectId - ID of the project to fetch tasks for
 * @param options - Additional React Query options
 * @returns Query result with project's tasks, loading state, and error
 */
export const useProjectTasks = (
  projectId: string,
  options?: UseQueryOptions<TasksResponse>
) => {
  // Create a filter with the project ID
  const filter: TasksFilter = useMemo(() => ({
    projectId,
    assigneeId: null,
    status: null,
    priority: null,
    dueDate: null,
    dueDateRange: null,
    tags: null,
    searchTerm: null
  }), [projectId]);
  
  // Use the useTasks hook with the filter
  return useTasks(filter, undefined, {
    ...options,
    // Only fetch when projectId is provided
    enabled: !!projectId && (options?.enabled !== false)
  });
};