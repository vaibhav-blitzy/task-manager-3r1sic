import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Task, TaskStatus, TaskPriority, TasksFilter, TaskSort } from '../../types/task';

/**
 * Interface defining the shape of the task state in Redux store
 */
interface TaskState {
  /**
   * Array of tasks
   */
  tasks: Task[];
  
  /**
   * Loading state indicator
   */
  isLoading: boolean;
  
  /**
   * Error message, if any
   */
  error: string | null;
  
  /**
   * Current filter criteria
   */
  currentFilter: TasksFilter | null;
  
  /**
   * Current sort criteria
   */
  currentSort: TaskSort | null;
}

/**
 * Initial state for the task slice
 */
const initialState: TaskState = {
  tasks: [],
  isLoading: false,
  error: null,
  currentFilter: null,
  currentSort: null
};

/**
 * Redux slice for task state management
 */
const taskSlice = createSlice({
  name: 'task',
  initialState,
  reducers: {
    /**
     * Updates state with a list of tasks
     */
    setTasks: (state, action: PayloadAction<Task[]>) => {
      state.tasks = action.payload;
    },
    
    /**
     * Adds a new task to the state
     */
    addTask: (state, action: PayloadAction<Task>) => {
      state.tasks.unshift(action.payload);
    },
    
    /**
     * Updates an existing task in the state
     */
    updateTask: (state, action: PayloadAction<Task>) => {
      const index = state.tasks.findIndex(task => task.id === action.payload.id);
      if (index !== -1) {
        state.tasks[index] = action.payload;
      }
    },
    
    /**
     * Removes a task from the state
     */
    deleteTask: (state, action: PayloadAction<string>) => {
      state.tasks = state.tasks.filter(task => task.id !== action.payload);
    },
    
    /**
     * Updates the status of a specific task
     */
    setTaskStatus: (state, action: PayloadAction<{ id: string; status: TaskStatus }>) => {
      const { id, status } = action.payload;
      const task = state.tasks.find(task => task.id === id);
      if (task) {
        task.status = status;
      }
    },
    
    /**
     * Updates the assignee of a specific task
     * Note: This is a simplified implementation. In a real application, 
     * you would likely need a thunk action that first fetches the complete 
     * user data before updating the task assignee.
     */
    setTaskAssignee: (state, action: PayloadAction<{ id: string; assigneeId: string | null }>) => {
      const { id, assigneeId } = action.payload;
      const task = state.tasks.find(task => task.id === id);
      if (task) {
        if (assigneeId === null) {
          task.assignee = null;
        } else {
          // This is a placeholder. In a real app, you would:
          // 1. Either have the full User object already in the action payload
          // 2. Or use a thunk to fetch the User data based on assigneeId
          task.assignee = { id: assigneeId } as any;
        }
      }
    },
    
    /**
     * Updates the priority of a specific task
     */
    setTaskPriority: (state, action: PayloadAction<{ id: string; priority: TaskPriority }>) => {
      const { id, priority } = action.payload;
      const task = state.tasks.find(task => task.id === id);
      if (task) {
        task.priority = priority;
      }
    },
    
    /**
     * Sets the loading state
     */
    setTaskLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    
    /**
     * Sets the error state
     */
    setTaskError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    /**
     * Clears any error messages
     */
    clearTaskErrors: (state) => {
      state.error = null;
    },
    
    /**
     * Updates the current filter criteria
     */
    setTaskFilter: (state, action: PayloadAction<TasksFilter | null>) => {
      state.currentFilter = action.payload;
    },
    
    /**
     * Updates the current sort criteria
     */
    setTaskSort: (state, action: PayloadAction<TaskSort | null>) => {
      state.currentSort = action.payload;
    },
  },
});

// Extract action creators
export const { 
  setTasks, 
  addTask, 
  updateTask, 
  deleteTask, 
  setTaskStatus, 
  setTaskAssignee, 
  setTaskPriority,
  setTaskLoading,
  setTaskError,
  clearTaskErrors,
  setTaskFilter,
  setTaskSort
} = taskSlice.actions;

/**
 * Selector to get all tasks from state
 */
export const selectTasks = (state: { task: TaskState }): Task[] => state.task.tasks;

/**
 * Selector to get a specific task by ID
 */
export const selectTaskById = (state: { task: TaskState }, id: string): Task | undefined => {
  return state.task.tasks.find(task => task.id === id);
};

/**
 * Selector to get tasks loading state
 */
export const selectTasksLoading = (state: { task: TaskState }): boolean => state.task.isLoading;

/**
 * Selector to get tasks error state
 */
export const selectTasksError = (state: { task: TaskState }): string | null => state.task.error;

/**
 * Selector for filtering tasks by criteria
 * This applies all specified filter criteria to return matching tasks
 */
export const selectFilteredTasks = (state: { task: TaskState }, filter: TasksFilter): Task[] => {
  return state.task.tasks.filter(task => {
    // Skip undefined tasks
    if (!task) return false;
    
    // If status filter is applied
    if (filter.status) {
      if (Array.isArray(filter.status)) {
        if (!filter.status.includes(task.status)) return false;
      } else {
        if (task.status !== filter.status) return false;
      }
    }
    
    // If priority filter is applied
    if (filter.priority) {
      if (Array.isArray(filter.priority)) {
        if (!filter.priority.includes(task.priority)) return false;
      } else {
        if (task.priority !== filter.priority) return false;
      }
    }
    
    // If assignee filter is applied
    if (filter.assigneeId !== null) {
      if (!task.assignee || task.assignee.id !== filter.assigneeId) {
        return false;
      }
    }
    
    // If project filter is applied
    if (filter.projectId !== null) {
      if (!task.project || task.project.id !== filter.projectId) {
        return false;
      }
    }
    
    // If due date filter is applied
    if (filter.dueDate !== null) {
      if (task.dueDate !== filter.dueDate) {
        return false;
      }
    }
    
    // If due date range filter is applied
    if (filter.dueDateRange && task.dueDate) {
      const taskDate = new Date(task.dueDate);
      const startDate = new Date(filter.dueDateRange.startDate);
      const endDate = new Date(filter.dueDateRange.endDate);
      
      if (taskDate < startDate || taskDate > endDate) {
        return false;
      }
    }
    
    // If tags filter is applied
    if (filter.tags && filter.tags.length > 0) {
      // Check if any of the required tags are present in the task's tags
      const hasMatchingTag = filter.tags.some(tag => task.tags.includes(tag));
      if (!hasMatchingTag) return false;
    }
    
    // If search term is applied, check in title and description
    if (filter.searchTerm) {
      const term = filter.searchTerm.toLowerCase();
      const titleMatch = task.title.toLowerCase().includes(term);
      const descriptionMatch = task.description && task.description.toLowerCase().includes(term);
      if (!titleMatch && !descriptionMatch) return false;
    }
    
    // If all filters pass, include the task
    return true;
  });
};

// Export the task slice reducer as default
export default taskSlice.reducer;