import { createSlice, PayloadAction } from '@reduxjs/toolkit'; // v1.9.x
import { Notification } from '../types/notification';
import { RootState } from '../index';

/**
 * Interface for the notification state in the Redux store
 */
interface NotificationState {
  notifications: Notification[];
  loading: boolean;
  error: string | null;
}

/**
 * Initial state for the notification slice
 */
const initialState: NotificationState = {
  notifications: [],
  loading: false,
  error: null
};

/**
 * Notification slice for managing notification state in the Redux store
 */
const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    /**
     * Sets the notifications array (typically after fetching from API)
     */
    setNotifications: (state, action: PayloadAction<Notification[]>) => {
      state.notifications = action.payload;
    },
    
    /**
     * Adds a new notification to the beginning of the array
     */
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload);
    },
    
    /**
     * Marks a specific notification as read by ID
     */
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
        
        // Update readAt in metadata
        if (notification.metadata) {
          notification.metadata.readAt = new Date().toISOString();
        }
      }
    },
    
    /**
     * Marks all notifications as read
     */
    markAllAsRead: (state) => {
      const now = new Date().toISOString();
      state.notifications.forEach(notification => {
        notification.read = true;
        if (notification.metadata) {
          notification.metadata.readAt = now;
        }
      });
    },
    
    /**
     * Clears all notifications from the state
     */
    clearNotifications: (state) => {
      state.notifications = [];
    },
    
    /**
     * Sets the loading state
     */
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    
    /**
     * Sets the error state
     */
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    }
  }
});

// Extract actions and reducer
export const {
  setNotifications,
  addNotification,
  markAsRead,
  markAllAsRead,
  clearNotifications,
  setLoading,
  setError
} = notificationSlice.actions;

/**
 * Selector to get all notifications from the state
 */
export const selectNotifications = (state: RootState) => state.notification.notifications;

/**
 * Selector to get the count of unread notifications
 */
export const selectUnreadCount = (state: RootState) => 
  state.notification.notifications.filter(notification => !notification.read).length;

/**
 * Selector to get a specific notification by ID
 */
export const selectNotificationById = (state: RootState, id: string) =>
  state.notification.notifications.find(notification => notification.id === id);

// Export the reducer as default
export default notificationSlice.reducer;