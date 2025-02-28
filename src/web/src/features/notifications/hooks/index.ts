/**
 * Notification hooks for the Task Management System
 * 
 * This file exports a collection of custom React hooks for notification functionality.
 * These hooks provide a unified API for components to interact with notifications,
 * including real-time updates, preference management, and badge display.
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback } from 'react'; // react v18.2.x
import useNotifications from '../../../api/hooks/useNotifications';
import { useWebSocketContext } from '../../../contexts/WebSocketContext';
import { NotificationType } from '../../../types/notification';

/**
 * Custom hook that integrates API-based notifications with real-time WebSocket updates.
 * Combines notifications from both REST API calls and WebSocket events to provide
 * a unified notification system.
 * 
 * @returns Combined notification state and operations with real-time capabilities
 */
export const useRealTimeNotifications = () => {
  // Get base notification functionality from API hook
  const {
    notifications: apiNotifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    fetchNotifications,
    updatePreferences
  } = useNotifications();

  // Get WebSocket functionality for real-time updates
  const { subscribe, isConnected, sendMessage } = useWebSocketContext();

  // State for real-time notifications that haven't been synced with the API yet
  const [realTimeNotifications, setRealTimeNotifications] = useState<any[]>([]);

  // Combine API notifications with real-time notifications
  const notifications = [...realTimeNotifications, ...apiNotifications];

  /**
   * Acknowledges a real-time notification and removes it from the local state
   * 
   * @param notificationId ID of the notification to acknowledge
   */
  const acknowledgeRealTimeNotification = useCallback((notificationId: string) => {
    setRealTimeNotifications(prev => 
      prev.filter(notification => notification.id !== notificationId)
    );
    
    // Inform the server that this notification was acknowledged
    if (isConnected) {
      sendMessage('notification.acknowledge', { id: notificationId });
    }
  }, [isConnected, sendMessage]);
  
  /**
   * Handles new notifications received via WebSocket
   */
  const handleNewNotification = useCallback((data: any) => {
    // Add the notification to our real-time list if it's not already there
    setRealTimeNotifications(prev => {
      // Check if notification already exists to prevent duplicates
      if (prev.some(n => n.id === data.id)) {
        return prev;
      }
      return [data, ...prev];
    });
  }, []);

  // Subscribe to notification events when component mounts or connection changes
  useEffect(() => {
    if (isConnected) {
      // Subscribe to personal notifications
      const unsubscribe = subscribe('notifications', undefined, handleNewNotification);
      
      // Clean up subscription when component unmounts or connection changes
      return unsubscribe;
    }
  }, [isConnected, subscribe, handleNewNotification]);

  // Refresh notifications from API when real-time notifications change
  // This ensures we eventually sync with the server state
  useEffect(() => {
    if (realTimeNotifications.length > 0) {
      const timer = setTimeout(() => {
        fetchNotifications({ page: 1, limit: 20 });
      }, 5000); // 5 second delay before syncing
      
      return () => clearTimeout(timer);
    }
  }, [realTimeNotifications, fetchNotifications]);

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    fetchNotifications,
    realTimeNotifications,
    acknowledgeRealTimeNotification
  };
};

/**
 * Custom hook for managing user notification preferences with enhanced utilities.
 * Provides functions for toggling different types of notification preferences.
 * 
 * @returns Notification preference state and management functions
 */
export const useNotificationSettings = () => {
  // Get preference management from base notifications hook
  const {
    preferences,
    loading,
    updatePreferences
  } = useNotifications();

  /**
   * Toggles a specific notification channel (e.g., email, push, in-app)
   * 
   * @param channel The channel to toggle (inApp, email, push)
   * @returns Promise resolving to updated preferences or null if an error occurred
   */
  const toggleChannelPreference = useCallback(async (channel: 'inApp' | 'email' | 'push') => {
    if (!preferences) return null;
    
    const newPreferences = {
      ...preferences,
      globalSettings: {
        ...preferences.globalSettings,
        [channel]: !preferences.globalSettings[channel]
      }
    };
    
    return await updatePreferences(newPreferences);
  }, [preferences, updatePreferences]);

  /**
   * Toggles notification preferences for a specific notification type
   * 
   * @param type The notification type to toggle
   * @param channel The channel to toggle (inApp, email, push)
   * @returns Promise resolving to updated preferences or null if an error occurred
   */
  const toggleTypePreference = useCallback(async (
    type: NotificationType, 
    channel: 'inApp' | 'email' | 'push'
  ) => {
    if (!preferences) return null;
    
    const currentTypeSettings = preferences.typeSettings[type] || { 
      inApp: preferences.globalSettings.inApp,
      email: preferences.globalSettings.email,
      push: preferences.globalSettings.push
    };
    
    const newPreferences = {
      ...preferences,
      typeSettings: {
        ...preferences.typeSettings,
        [type]: {
          ...currentTypeSettings,
          [channel]: !currentTypeSettings[channel]
        }
      }
    };
    
    return await updatePreferences(newPreferences);
  }, [preferences, updatePreferences]);

  /**
   * Toggles notification preferences for a specific project
   * 
   * @param projectId The ID of the project
   * @param channel The channel to toggle (inApp, email, push)
   * @returns Promise resolving to updated preferences or null if an error occurred
   */
  const toggleProjectPreference = useCallback(async (
    projectId: string, 
    channel: 'inApp' | 'email' | 'push'
  ) => {
    if (!preferences) return null;
    
    const currentProjectSettings = preferences.projectSettings[projectId] || {
      inApp: preferences.globalSettings.inApp,
      email: preferences.globalSettings.email,
      push: preferences.globalSettings.push
    };
    
    const newPreferences = {
      ...preferences,
      projectSettings: {
        ...preferences.projectSettings,
        [projectId]: {
          ...currentProjectSettings,
          [channel]: !currentProjectSettings[channel]
        }
      }
    };
    
    return await updatePreferences(newPreferences);
  }, [preferences, updatePreferences]);

  /**
   * Updates quiet hours configuration
   * 
   * @param quietHours The new quiet hours configuration
   * @returns Promise resolving to updated preferences or null if an error occurred
   */
  const updateQuietHours = useCallback(async (quietHours: {
    enabled: boolean;
    start: string;
    end: string;
    timezone: string;
    excludeUrgent: boolean;
  }) => {
    if (!preferences) return null;
    
    const newPreferences = {
      ...preferences,
      quietHours: {
        ...preferences.quietHours,
        ...quietHours
      }
    };
    
    return await updatePreferences(newPreferences);
  }, [preferences, updatePreferences]);

  return {
    preferences,
    loading,
    updatePreferences,
    toggleChannelPreference,
    toggleTypePreference,
    toggleProjectPreference,
    updateQuietHours
  };
};

/**
 * Custom hook for managing notification count badges in the UI.
 * Provides functions to control the visibility of notification badges
 * with seen/unseen state tracking.
 * 
 * @returns Badge state and visibility controls
 */
export const useNotificationBadge = () => {
  // Get unread count from main notifications hook
  const { unreadCount } = useNotifications();
  
  // Track whether badge has been visually acknowledged without reading notifications
  const [seen, setSeen] = useState(false);
  
  // Reset seen state when unread count changes
  useEffect(() => {
    if (unreadCount > 0) {
      setSeen(false);
    }
  }, [unreadCount]);

  /**
   * Marks the notification badge as seen without marking notifications as read
   */
  const markSeen = useCallback(() => {
    setSeen(true);
  }, []);

  /**
   * Resets the badge seen state to make it visible again
   */
  const resetSeen = useCallback(() => {
    setSeen(false);
  }, []);
  
  // Determine if badge should be shown (has unread notifications and not marked as seen)
  const showBadge = unreadCount > 0 && !seen;

  return {
    count: unreadCount,
    showBadge,
    markSeen,
    resetSeen
  };
};

// Re-export the base notification hook for direct access
export { useNotifications };