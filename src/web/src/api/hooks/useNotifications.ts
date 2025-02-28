/**
 * Custom React hook that provides notification management functionality
 * for components in the Task Management System
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback } from 'react'; // react v18.2.x
import notificationService from '../services/notificationService';
import { Notification, NotificationPreferences, GetNotificationsRequest } from '../../types/notification';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import {
  fetchNotificationsAsync,
  markAsReadAsync,
  markAllAsReadAsync,
  fetchUnreadCountAsync,
  fetchPreferencesAsync,
  updatePreferencesAsync,
  selectNotifications,
  selectUnreadCount,
  selectNotificationLoading,
  selectNotificationError,
  selectNotificationPreferences
} from '../../store/slices/notificationSlice';
import { handleApiError } from '../client';

/**
 * Custom hook for managing notifications in the Task Management System.
 * Provides an interface for fetching, marking as read, and managing notification
 * preferences using Redux state management.
 * 
 * @returns Object containing notification state and methods for interacting with notifications
 */
const useNotifications = () => {
  const dispatch = useAppDispatch();
  
  // Get notification state from Redux store
  const notifications = useAppSelector(selectNotifications);
  const unreadCount = useAppSelector(selectUnreadCount);
  const loading = useAppSelector(selectNotificationLoading);
  const error = useAppSelector(selectNotificationError);
  const preferences = useAppSelector(selectNotificationPreferences);

  /**
   * Fetches notifications from the server with optional filtering
   * 
   * @param params - Request parameters including pagination and filters
   * @returns The fetched notifications response or null if an error occurred
   */
  const fetchNotifications = useCallback(async (params: GetNotificationsRequest) => {
    try {
      return await dispatch(fetchNotificationsAsync(params)).unwrap();
    } catch (error) {
      handleApiError(error);
      return null;
    }
  }, [dispatch]);

  /**
   * Marks a specific notification as read
   * 
   * @param notificationId - ID of the notification to mark as read
   * @returns The updated notification or null if an error occurred
   */
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      return await dispatch(markAsReadAsync(notificationId)).unwrap();
    } catch (error) {
      handleApiError(error);
      return null;
    }
  }, [dispatch]);

  /**
   * Marks all notifications as read for the current user
   * 
   * @returns True if successful, false otherwise
   */
  const markAllAsRead = useCallback(async () => {
    try {
      await dispatch(markAllAsReadAsync()).unwrap();
      return true;
    } catch (error) {
      handleApiError(error);
      return false;
    }
  }, [dispatch]);

  /**
   * Gets the count of unread notifications
   * 
   * @returns The number of unread notifications or null if an error occurred
   */
  const getUnreadCount = useCallback(async () => {
    try {
      const result = await dispatch(fetchUnreadCountAsync()).unwrap();
      return result.count;
    } catch (error) {
      handleApiError(error);
      return null;
    }
  }, [dispatch]);

  /**
   * Gets the notification preferences for the current user
   * 
   * @returns The user's notification preferences or null if an error occurred
   */
  const getPreferences = useCallback(async () => {
    try {
      return await dispatch(fetchPreferencesAsync()).unwrap();
    } catch (error) {
      handleApiError(error);
      return null;
    }
  }, [dispatch]);

  /**
   * Updates the notification preferences for the current user
   * 
   * @param newPreferences - Updated notification preferences
   * @returns The updated notification preferences or null if an error occurred
   */
  const updatePreferences = useCallback(async (newPreferences: NotificationPreferences) => {
    try {
      return await dispatch(updatePreferencesAsync(newPreferences)).unwrap();
    } catch (error) {
      handleApiError(error);
      return null;
    }
  }, [dispatch]);

  // Fetch notifications on initial mount if none exist
  useEffect(() => {
    if (notifications.length === 0 && !loading && !error) {
      fetchNotifications({ page: 1, limit: 20 });
    }
  }, [notifications.length, loading, error, fetchNotifications]);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    preferences,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    getUnreadCount,
    getPreferences,
    updatePreferences
  };
};

export default useNotifications;