/**
 * Notification Service
 * 
 * Service module for managing notifications in the Task Management System frontend.
 * Handles fetching notifications, updating read status, and managing notification
 * preferences based on user settings.
 *
 * @version 1.0.0
 */

import apiClient from '../client';
import { handleApiError } from '../client';
import { NOTIFICATION_ENDPOINTS } from '../endpoints';
import {
  Notification,
  NotificationPreferences,
  GetNotificationsRequest,
  GetNotificationsResponse,
  UpdateNotificationRequest,
  UpdatePreferencesRequest
} from '../../types/notification';

/**
 * Fetches paginated list of notifications for the current user with optional filtering
 * 
 * @param params - Request parameters including pagination and filters
 * @returns Promise resolving to paginated notification list
 */
const getNotifications = async (params: GetNotificationsRequest): Promise<GetNotificationsResponse> => {
  try {
    const response = await apiClient.get(NOTIFICATION_ENDPOINTS.GET_NOTIFICATIONS, {
      params: {
        page: params.page,
        limit: params.limit,
        ...params.filter
      }
    });
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Marks a specific notification as read
 * 
 * @param notificationId - ID of the notification to mark as read
 * @returns Promise resolving to the updated notification
 */
const markAsRead = async (notificationId: string): Promise<Notification> => {
  try {
    const request: UpdateNotificationRequest = {
      read: true
    };
    
    const response = await apiClient.patch(
      NOTIFICATION_ENDPOINTS.MARK_READ(notificationId),
      request
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Marks all notifications as read for the current user
 * 
 * @returns Promise resolving when the operation completes
 */
const markAllAsRead = async (): Promise<void> => {
  try {
    await apiClient.post(NOTIFICATION_ENDPOINTS.MARK_ALL_READ);
    return;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves the count of unread notifications for the current user
 * 
 * @returns Promise resolving to object containing unread count
 */
const getUnreadCount = async (): Promise<{ count: number }> => {
  try {
    const response = await apiClient.get(NOTIFICATION_ENDPOINTS.UNREAD_COUNT);
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Retrieves the notification preferences for the current user
 * 
 * @returns Promise resolving to user's notification preferences
 */
const getPreferences = async (): Promise<NotificationPreferences> => {
  try {
    const response = await apiClient.get(NOTIFICATION_ENDPOINTS.PREFERENCES);
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Updates the notification preferences for the current user
 * 
 * @param preferences - New notification preferences
 * @returns Promise resolving to updated notification preferences
 */
const updatePreferences = async (preferences: NotificationPreferences): Promise<NotificationPreferences> => {
  try {
    const response = await apiClient.put(
      NOTIFICATION_ENDPOINTS.PREFERENCES,
      preferences
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
};

/**
 * Notification service providing notification functionality for the frontend
 */
const notificationService = {
  getNotifications,
  markAsRead,
  markAllAsRead,
  getUnreadCount,
  getPreferences,
  updatePreferences
};

export default notificationService;