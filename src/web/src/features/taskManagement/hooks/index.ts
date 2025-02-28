/**
 * Task Management Custom Hooks
 * 
 * This file exports custom React hooks for task management functionality,
 * providing specialized behavior on top of the base API hooks for creating,
 * updating, filtering, and organizing tasks.
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.2.x
import { useForm } from 'react-hook-form'; // react-hook-form ^7.46.x

// Import base API hooks
import {
  useGetTasks,
  useGetTask,
  useCreateTask,
  useUpdateTask,
  useDeleteTask,
  useAssignTask
} from '../../api/hooks/useTasks';

// Import file management hooks
import {
  useUploadFile,
  useDeleteFile
} from '../../api/hooks/useFiles';

// Import types
import {
  Task,
  TaskStatus,
  TaskPriority,
  TaskFilter,
  TaskSortField
} from '../../types/task';

// Import Redux hooks
import {
  useAppDispatch,
  useAppSelector
} from '../../store/hooks';

// Import task slice
import {
  selectTasks,
  taskActions
} from '../../store/slices/taskSlice';

// Import WebSocket hook for real-time updates
import { useWebSocket } from '../../hooks/useWebSocket';

/**
 * Hook for creating a new task with validation and state handling
 * 
 * @returns Object containing task creation functions and state
 */
export function useTaskCreation() {
  const { register, handleSubmit, reset, formState: { errors } } = useForm();
  const { createTask: createTaskMutation } = useCreateTask();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Create task submission handler
  const createTask = useCallback(async (data: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await createTaskMutation.mutate(data);
      reset();
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [createTaskMutation, reset]);
  
  return {
    createTask,
    isLoading,
    error,
    reset: () => {
      reset();
      setError(null);
    },
    register,
    handleSubmit,
    formErrors: errors
  };
}

/**
 * Hook for fetching and managing detailed task information
 * 
 * @param taskId - ID of the task to fetch details for
 * @returns Object containing task data and state
 */
export function useTaskDetails(taskId: string) {
  const { data: task, isLoading, error, refetch } = useGetTask(taskId);
  const dispatch = useAppDispatch();
  
  // Set up WebSocket for real-time updates
  const { subscribe, unsubscribe, isConnected } = useWebSocket();
  
  useEffect(() => {
    if (taskId && isConnected) {
      // Subscribe to task updates
      subscribe(`task.${taskId}`, (data) => {
        if (data.task) {
          // Update local state when we receive a WebSocket update
          dispatch(taskActions.updateTask(data.task));
          refetch();
        }
      });
      
      // Cleanup subscription on unmount or taskId change
      return () => {
        unsubscribe(`task.${taskId}`);
      };
    }
  }, [taskId, isConnected, subscribe, unsubscribe, dispatch, refetch]);
  
  return { 
    task, 
    isLoading, 
    error, 
    refetch 
  };
}

/**
 * Hook for managing a Kanban-style task board with columns for different statuses
 * 
 * @param options - Configuration options for the task board
 * @returns Object containing board data and functions
 */
export function useTaskBoard(options: { 
  projectId?: string;
  assigneeId?: string;
  filter?: TaskFilter;
}) {
  const filters = useMemo(() => {
    return {
      projectId: options.projectId || null,
      assigneeId: options.assigneeId || null,
      status: null,
      priority: null,
      dueDate: null,
      dueDateRange: null,
      tags: null,
      searchTerm: null,
      ...(options.filter || {})
    };
  }, [options.projectId, options.assigneeId, options.filter]);

  const { tasks, isLoading, refetch } = useGetTasks(filters);
  const { updateTask } = useUpdateTask();
  const { subscribe, unsubscribe, isConnected } = useWebSocket();
  
  // Group tasks by status into columns
  const columns = useMemo(() => {
    if (!tasks || !tasks.length) return {};
    
    const grouped: Record<string, Task[]> = {
      [TaskStatus.CREATED]: [],
      [TaskStatus.ASSIGNED]: [],
      [TaskStatus.IN_PROGRESS]: [],
      [TaskStatus.ON_HOLD]: [],
      [TaskStatus.IN_REVIEW]: [],
      [TaskStatus.COMPLETED]: [],
      [TaskStatus.CANCELLED]: []
    };
    
    tasks.forEach(task => {
      if (grouped[task.status]) {
        grouped[task.status].push(task);
      }
    });
    
    return grouped;
  }, [tasks]);
  
  // Function to move a task between columns (change status)
  const moveTask = useCallback(async (taskId: string, newStatus: TaskStatus) => {
    try {
      await updateTask.mutate({
        taskId,
        taskData: { status: newStatus }
      });
      return true;
    } catch (error) {
      console.error('Error moving task:', error);
      return false;
    }
  }, [updateTask]);
  
  // Subscribe to task updates for the board
  useEffect(() => {
    if (isConnected) {
      // Subscribe to relevant channels based on options
      let channel = 'task.updates';
      if (options.projectId) {
        channel = `project.${options.projectId}.tasks`;
      } else if (options.assigneeId) {
        channel = `user.${options.assigneeId}.tasks`;
      }
      
      subscribe(channel, () => {
        // Refresh task list when changes occur
        refetch();
      });
      
      return () => {
        unsubscribe(channel);
      };
    }
  }, [options.projectId, options.assigneeId, isConnected, subscribe, unsubscribe, refetch]);
  
  return {
    columns,
    tasks,
    moveTask,
    isLoading
  };
}

/**
 * Hook for filtering tasks by various criteria like status, assignee, due date
 * 
 * @param initialFilters - Initial filter values
 * @returns Object containing filter functions and filtered tasks
 */
export function useTaskFiltering(initialFilters: TaskFilter = {}) {
  const [filters, setFilters] = useState<TaskFilter>(initialFilters);
  const { tasks, isLoading, refetch } = useGetTasks();
  
  // Apply filters to tasks
  const filteredTasks = useMemo(() => {
    if (!tasks || !tasks.length) return [];
    
    return tasks.filter(task => {
      // Status filter
      if (filters.status && task.status !== filters.status) {
        return false;
      }
      
      // Priority filter
      if (filters.priority && task.priority !== filters.priority) {
        return false;
      }
      
      // Assignee filter
      if (filters.assigneeId && (!task.assignee || task.assignee.id !== filters.assigneeId)) {
        return false;
      }
      
      // Project filter
      if (filters.projectId && (!task.project || task.project.id !== filters.projectId)) {
        return false;
      }
      
      // Due date filter (range)
      if (filters.dueDateRange && task.dueDate) {
        const taskDate = new Date(task.dueDate);
        const startDate = new Date(filters.dueDateRange.startDate);
        const endDate = new Date(filters.dueDateRange.endDate);
        
        if (taskDate < startDate || taskDate > endDate) {
          return false;
        }
      }
      
      // Specific due date
      if (filters.dueDate && task.dueDate !== filters.dueDate) {
        return false;
      }
      
      // Tag filter
      if (filters.tags && filters.tags.length > 0) {
        if (!task.tags || !filters.tags.some(tag => task.tags.includes(tag))) {
          return false;
        }
      }
      
      // Text search
      if (filters.searchTerm) {
        const term = filters.searchTerm.toLowerCase();
        return (
          task.title.toLowerCase().includes(term) ||
          (task.description && task.description.toLowerCase().includes(term))
        );
      }
      
      return true;
    });
  }, [tasks, filters]);
  
  // Update a specific filter
  const setFilter = useCallback((key: keyof TaskFilter, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);
  
  // Reset filters to initial values
  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
  }, [initialFilters]);
  
  return {
    filters,
    setFilter,
    resetFilters,
    filteredTasks,
    isLoading
  };
}

/**
 * Hook for sorting tasks by different fields like due date, priority, status
 * 
 * @param initialSortField - Initial field to sort by
 * @param initialSortDirection - Initial sort direction (true for ascending)
 * @returns Object containing sort functions and sorted tasks
 */
export function useTaskSorting(
  initialSortField: TaskSortField = TaskSortField.DUE_DATE,
  initialSortDirection: boolean = true
) {
  const [sortField, setSortField] = useState<TaskSortField>(initialSortField);
  const [sortDirection, setSortDirection] = useState<boolean>(initialSortDirection);
  const tasks = useAppSelector(selectTasks);
  
  // Apply sorting to tasks
  const sortedTasks = useMemo(() => {
    if (!tasks || !tasks.length) return [];
    
    return [...tasks].sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case TaskSortField.TITLE:
          comparison = a.title.localeCompare(b.title);
          break;
        case TaskSortField.STATUS:
          comparison = a.status.localeCompare(b.status);
          break;
        case TaskSortField.PRIORITY:
          comparison = a.priority.localeCompare(b.priority);
          break;
        case TaskSortField.DUE_DATE:
          if (!a.dueDate && !b.dueDate) {
            comparison = 0;
          } else if (!a.dueDate) {
            comparison = 1; // No due date comes last
          } else if (!b.dueDate) {
            comparison = -1; // No due date comes last
          } else {
            comparison = new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
          }
          break;
        case TaskSortField.CREATED_AT:
          comparison = new Date(a.metadata.created).getTime() - new Date(b.metadata.created).getTime();
          break;
        case TaskSortField.UPDATED_AT:
          comparison = new Date(a.metadata.lastUpdated).getTime() - new Date(b.metadata.lastUpdated).getTime();
          break;
        default:
          comparison = 0;
      }
      
      return sortDirection ? comparison : -comparison;
    });
  }, [tasks, sortField, sortDirection]);
  
  // Toggle sort direction
  const toggleSortDirection = useCallback(() => {
    setSortDirection(prev => !prev);
  }, []);
  
  return {
    sortField,
    sortDirection,
    setSortField,
    toggleSortDirection,
    sortedTasks
  };
}

/**
 * Hook for managing task status transitions with validation
 * 
 * @returns Object containing status change functions and state
 */
export function useTaskStatusManagement() {
  const { updateStatus, isLoading, error } = useTaskStatusUpdate();
  
  // Define valid transitions between task statuses
  const statusTransitions: Record<TaskStatus, TaskStatus[]> = {
    [TaskStatus.CREATED]: [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
    [TaskStatus.ASSIGNED]: [TaskStatus.IN_PROGRESS, TaskStatus.ON_HOLD, TaskStatus.CANCELLED],
    [TaskStatus.IN_PROGRESS]: [TaskStatus.ON_HOLD, TaskStatus.IN_REVIEW, TaskStatus.COMPLETED, TaskStatus.CANCELLED],
    [TaskStatus.ON_HOLD]: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
    [TaskStatus.IN_REVIEW]: [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELLED],
    [TaskStatus.COMPLETED]: [TaskStatus.IN_PROGRESS], // Can reopen a completed task
    [TaskStatus.CANCELLED]: [TaskStatus.CREATED] // Can reactivate a cancelled task
  };
  
  // Function to get available next statuses for a task
  const getAvailableStatuses = useCallback((currentStatus: TaskStatus): TaskStatus[] => {
    return statusTransitions[currentStatus] || [];
  }, []);
  
  // Function to change a task's status with validation
  const changeStatus = useCallback(async (
    taskId: string,
    newStatus: TaskStatus,
    currentStatus: TaskStatus
  ) => {
    // Validate status transition
    const availableStatuses = getAvailableStatuses(currentStatus);
    if (!availableStatuses.includes(newStatus)) {
      return {
        success: false,
        error: `Cannot change status from ${currentStatus} to ${newStatus}`
      };
    }
    
    try {
      await updateStatus({
        taskId,
        status: { status: newStatus }
      });
      
      return {
        success: true
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update task status';
      return {
        success: false,
        error: message
      };
    }
  }, [updateStatus, getAvailableStatuses]);
  
  return {
    changeStatus,
    availableStatuses: getAvailableStatuses,
    isLoading,
    error
  };
}

/**
 * Hook for assigning tasks to users
 * 
 * @returns Object containing assignment functions and state
 */
export function useTaskAssignment() {
  const { assignTask: assignTaskMutation, isLoading, error } = useAssignTask();
  
  // Assign task to a user
  const assignTask = useCallback(async (
    taskId: string,
    userId: string
  ) => {
    try {
      await assignTaskMutation({
        taskId,
        assigneeId: { assigneeId: userId }
      });
      
      return {
        success: true
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to assign task';
      return {
        success: false,
        error: message
      };
    }
  }, [assignTaskMutation]);
  
  // Unassign task (remove assignment)
  const unassignTask = useCallback(async (
    taskId: string
  ) => {
    try {
      await assignTaskMutation({
        taskId,
        assigneeId: { assigneeId: null }
      });
      
      return {
        success: true
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to unassign task';
      return {
        success: false,
        error: message
      };
    }
  }, [assignTaskMutation]);
  
  return {
    assignTask,
    unassignTask,
    isLoading,
    error
  };
}

/**
 * Hook for managing comments on a task
 * 
 * @param taskId - ID of the task
 * @returns Object containing comment functions and data
 */
export function useTaskComments(taskId: string) {
  const { data: task, refetch } = useGetTask(taskId);
  const { updateTask } = useUpdateTask();
  const { subscribe, unsubscribe, isConnected } = useWebSocket();
  const [isLoading, setIsLoading] = useState(false);
  
  // Set up real-time comment updates
  useEffect(() => {
    if (taskId && isConnected) {
      subscribe(`task.${taskId}.comments`, () => {
        // Refresh comments when changes occur
        refetch();
      });
      
      return () => {
        unsubscribe(`task.${taskId}.comments`);
      };
    }
  }, [taskId, isConnected, subscribe, unsubscribe, refetch]);
  
  // Add a new comment
  const addComment = useCallback(async (
    content: string
  ) => {
    if (!taskId || !task) return false;
    
    setIsLoading(true);
    try {
      const newComment = {
        id: Date.now().toString(),
        content,
        createdBy: {
          id: 'current-user-id', // This would come from auth context
          firstName: 'Current',
          lastName: 'User',
          email: 'user@example.com'
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      const updatedComments = [...(task.comments || []), newComment];
      
      await updateTask.mutate({
        taskId,
        taskData: { 
          ...task,
          comments: updatedComments
        }
      });
      
      return true;
    } catch (error) {
      console.error('Error adding comment:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [taskId, task, updateTask]);
  
  // Edit an existing comment
  const editComment = useCallback(async (
    commentId: string,
    content: string
  ) => {
    if (!taskId || !task || !task.comments) return false;
    
    setIsLoading(true);
    try {
      const updatedComments = task.comments.map(comment => 
        comment.id === commentId 
          ? { ...comment, content, updatedAt: new Date().toISOString() }
          : comment
      );
      
      await updateTask.mutate({
        taskId,
        taskData: {
          ...task,
          comments: updatedComments
        }
      });
      
      return true;
    } catch (error) {
      console.error('Error editing comment:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [taskId, task, updateTask]);
  
  // Delete a comment
  const deleteComment = useCallback(async (
    commentId: string
  ) => {
    if (!taskId || !task || !task.comments) return false;
    
    setIsLoading(true);
    try {
      const updatedComments = task.comments.filter(comment => 
        comment.id !== commentId
      );
      
      await updateTask.mutate({
        taskId,
        taskData: {
          ...task,
          comments: updatedComments
        }
      });
      
      return true;
    } catch (error) {
      console.error('Error deleting comment:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [taskId, task, updateTask]);
  
  return {
    comments: task?.comments || [],
    addComment,
    editComment,
    deleteComment,
    isLoading
  };
}

/**
 * Hook for managing file attachments on a task
 * 
 * @param taskId - ID of the task
 * @returns Object containing attachment functions and data
 */
export function useTaskAttachments(taskId: string) {
  const { attachments, isLoading, addAttachment, removeAttachment } = useAttachments({ taskId });
  const { uploadFile } = useUploadFile();
  const { deleteFile } = useFileDeletion();
  
  // Upload a file attachment
  const uploadAttachment = useCallback(async (
    file: File
  ) => {
    if (!taskId) return false;
    
    try {
      // First upload the file
      const fileData = await uploadFile(file);
      
      // Then associate it with the task
      if (fileData) {
        await addAttachment(fileData.id);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error uploading attachment:', error);
      return false;
    }
  }, [taskId, uploadFile, addAttachment]);
  
  // Delete a file attachment
  const deleteAttachment = useCallback(async (
    fileId: string
  ) => {
    if (!taskId) return false;
    
    try {
      // First remove the association with the task
      await removeAttachment(fileId);
      
      // Then delete the file itself
      await deleteFile(fileId);
      
      return true;
    } catch (error) {
      console.error('Error deleting attachment:', error);
      return false;
    }
  }, [taskId, removeAttachment, deleteFile]);
  
  return {
    attachments,
    uploadAttachment,
    deleteAttachment,
    isLoading
  };
}

/**
 * Hook for managing and calculating task due dates
 * 
 * @returns Object containing due date utilities and functions
 */
export function useTaskDueDates() {
  const { updateTask } = useUpdateTask();
  
  // Set a task's due date
  const setDueDate = useCallback(async (
    taskId: string,
    dueDate: string | null
  ) => {
    try {
      await updateTask.mutate({
        taskId,
        taskData: { dueDate }
      });
      
      return {
        success: true
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update due date';
      return {
        success: false,
        error: message
      };
    }
  }, [updateTask]);
  
  // Check if a task is due today
  const isDueToday = useCallback((dueDate: string | null): boolean => {
    if (!dueDate) return false;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const taskDueDate = new Date(dueDate);
    taskDueDate.setHours(0, 0, 0, 0);
    
    return today.getTime() === taskDueDate.getTime();
  }, []);
  
  // Check if a task is overdue
  const isOverdue = useCallback((dueDate: string | null): boolean => {
    if (!dueDate) return false;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const taskDueDate = new Date(dueDate);
    taskDueDate.setHours(0, 0, 0, 0);
    
    return today.getTime() > taskDueDate.getTime();
  }, []);
  
  // Calculate days remaining until due date
  const daysRemaining = useCallback((dueDate: string | null): number => {
    if (!dueDate) return Infinity;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const taskDueDate = new Date(dueDate);
    taskDueDate.setHours(0, 0, 0, 0);
    
    const timeDiff = taskDueDate.getTime() - today.getTime();
    return Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
  }, []);
  
  return {
    setDueDate,
    isDueToday,
    isOverdue,
    daysRemaining
  };
}

export {
  useTaskCreation,
  useTaskDetails,
  useTaskBoard,
  useTaskFiltering,
  useTaskSorting,
  useTaskStatusManagement,
  useTaskAssignment,
  useTaskComments,
  useTaskAttachments,
  useTaskDueDates
};