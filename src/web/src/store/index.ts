import { configureStore, getDefaultMiddleware, createSlice, PayloadAction } from '@reduxjs/toolkit'; // v1.9.x

// Import reducers from slices
import authReducer from './slices/authSlice';
import projectReducer from './slices/projectSlice';
import taskReducer from './slices/taskSlice';
import uiReducer from './slices/uiSlice';

/**
 * Creates a notification slice directly within the store file to avoid circular dependency
 */
const createNotificationsSlice = () => {
  // Define the interface for notification objects
  interface NotificationType {
    id: string;
    type: string;
    title: string;
    message: string;
    read: boolean;
    createdAt: string;
    actionUrl?: string;
    data?: {
      taskId?: string;
      projectId?: string;
      commentId?: string;
      userId?: string;
      [key: string]: any;
    };
  }

  // Define the state interface for the notifications slice
  interface NotificationState {
    notifications: NotificationType[];
  }

  // Initial state with empty notifications array
  const initialState: NotificationState = {
    notifications: [],
  };

  // Create the notifications slice
  const notificationsSlice = createSlice({
    name: 'notifications',
    initialState,
    reducers: {
      // Add a new notification
      addNotification: (state, action: PayloadAction<Omit<NotificationType, 'id' | 'read' | 'createdAt'>>) => {
        const id = Date.now().toString();
        state.notifications.unshift({
          ...action.payload,
          id,
          read: false,
          createdAt: new Date().toISOString(),
        });
      },
      
      // Remove a notification by ID
      removeNotification: (state, action: PayloadAction<string>) => {
        state.notifications = state.notifications.filter(
          (notification) => notification.id !== action.payload
        );
      },
      
      // Mark a notification as read
      markAsRead: (state, action: PayloadAction<string>) => {
        const notification = state.notifications.find(
          (notification) => notification.id === action.payload
        );
        if (notification) {
          notification.read = true;
        }
      },
      
      // Clear all notifications
      clearAll: (state) => {
        state.notifications = [];
      },
    },
  });

  return {
    reducer: notificationsSlice.reducer,
    actions: notificationsSlice.actions,
  };
};

// Create the notifications slice
const { reducer: notificationsReducer, actions: notificationActions } = createNotificationsSlice();

// Configure the Redux store
export const store = configureStore({
  reducer: {
    auth: authReducer,
    project: projectReducer,
    task: taskReducer,
    ui: uiReducer,
    notifications: notificationsReducer,
  },
  middleware: (getDefaultMiddleware) => 
    getDefaultMiddleware({
      serializableCheck: {
        // We could configure ignored actions/paths here if needed
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

// Export types for state and dispatch
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export notification actions and type
export { notificationActions };
export interface NotificationType {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  actionUrl?: string;
  data?: {
    taskId?: string;
    projectId?: string;
    commentId?: string;
    userId?: string;
    [key: string]: any;
  };
}

export default store;