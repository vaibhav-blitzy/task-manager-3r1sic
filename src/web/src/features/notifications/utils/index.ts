/**
 * Utility functions for working with notifications in the Task Management System frontend.
 * 
 * This file provides helper functions for notification formatting, filtering,
 * prioritization, and other common operations used across notification-related components.
 * 
 * @module features/notifications/utils
 * @version 1.0.0
 */

import { format } from 'date-fns'; // date-fns v2.30.0
import { 
  Notification, 
  NotificationType, 
  NotificationPriority 
} from '../../../types/notification';
import { formatDateTime, getRelativeDateLabel } from '../../../utils/date';

/**
 * Generates a standardized title for a notification based on its type
 * 
 * @param type - The notification type
 * @returns A standardized title string for the notification type
 */
export function getNotificationTitle(type: NotificationType): string {
  switch (type) {
    case NotificationType.TASK_ASSIGNED:
      return 'Task Assigned';
    case NotificationType.TASK_DUE_SOON:
      return 'Task Due Soon';
    case NotificationType.TASK_OVERDUE:
      return 'Task Overdue';
    case NotificationType.COMMENT_ADDED:
      return 'New Comment';
    case NotificationType.MENTION:
      return 'You Were Mentioned';
    case NotificationType.PROJECT_INVITATION:
      return 'Project Invitation';
    case NotificationType.STATUS_CHANGE:
      return 'Status Changed';
    default:
      return 'Notification';
  }
}

/**
 * Formats notification content with placeholder values replaced with actual data
 * 
 * @param template - Template string with placeholders in {{placeholder}} format
 * @param values - Object containing values to replace in the template
 * @returns Formatted notification content with values inserted
 */
export function getNotificationContent(template: string, values: Record<string, string>): string {
  return Object.entries(values).reduce((result, [key, value]) => {
    // Replace all occurrences of {{key}} with the corresponding value
    const placeholder = new RegExp(`{{${key}}}`, 'g');
    return result.replace(placeholder, value);
  }, template);
}

/**
 * Returns a formatted time label for a notification, using relative time for recent
 * notifications and exact date for older ones
 * 
 * @param timestamp - ISO date string of the notification creation time
 * @returns Formatted time label (e.g., "2 hours ago" or "Jan 15, 2023")
 */
export function getNotificationTimeLabel(timestamp: string): string {
  if (!timestamp) {
    return '';
  }
  
  const notificationDate = new Date(timestamp);
  const currentDate = new Date();
  const hoursAgo = Math.abs(currentDate.getTime() - notificationDate.getTime()) / (1000 * 60 * 60);
  
  // Use relative time for notifications less than 24 hours old
  if (hoursAgo < 24) {
    return getRelativeDateLabel(notificationDate);
  }
  
  // Use exact date for older notifications
  return formatDateTime(notificationDate);
}

/**
 * Sorts an array of notifications by priority (highest first) and then by date (newest first)
 * 
 * @param notifications - Array of notifications to sort
 * @returns New sorted array of notifications
 */
export function sortNotificationsByPriority(notifications: Notification[]): Notification[] {
  // Create a copy of the array to avoid mutating the original
  return [...notifications].sort((a, b) => {
    // First sort by priority (URGENT > HIGH > NORMAL > LOW)
    const priorityOrder = {
      [NotificationPriority.URGENT]: 0,
      [NotificationPriority.HIGH]: 1,
      [NotificationPriority.NORMAL]: 2,
      [NotificationPriority.LOW]: 3
    };
    
    const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
    
    if (priorityDiff !== 0) {
      return priorityDiff;
    }
    
    // For equal priorities, sort by date (newest first)
    const dateA = new Date(a.metadata.created);
    const dateB = new Date(b.metadata.created);
    return dateB.getTime() - dateA.getTime();
  });
}

/**
 * Filters an array of notifications to include only those matching specific types
 * 
 * @param notifications - Array of notifications to filter
 * @param types - Array of notification types to include
 * @returns Filtered array of notifications
 */
export function filterNotificationsByType(
  notifications: Notification[], 
  types: NotificationType[]
): Notification[] {
  if (!types || types.length === 0) {
    return notifications;
  }
  
  return notifications.filter(notification => types.includes(notification.type));
}

/**
 * Groups notifications by date categories (Today, Yesterday, This Week, This Month, Older)
 * 
 * @param notifications - Array of notifications to group
 * @returns Object with notifications grouped by date category
 */
export function groupNotificationsByDate(
  notifications: Notification[]
): Record<string, Notification[]> {
  const result: Record<string, Notification[]> = {
    Today: [],
    Yesterday: [],
    ThisWeek: [],
    ThisMonth: [],
    Older: []
  };
  
  const currentDate = new Date();
  const yesterday = new Date(currentDate);
  yesterday.setDate(currentDate.getDate() - 1);
  
  const oneWeekAgo = new Date(currentDate);
  oneWeekAgo.setDate(currentDate.getDate() - 7);
  
  const oneMonthAgo = new Date(currentDate);
  oneMonthAgo.setMonth(currentDate.getMonth() - 1);
  
  notifications.forEach(notification => {
    const notificationDate = new Date(notification.metadata.created);
    
    // Check which date category this notification belongs to
    if (notificationDate.toDateString() === currentDate.toDateString()) {
      result.Today.push(notification);
    } else if (notificationDate.toDateString() === yesterday.toDateString()) {
      result.Yesterday.push(notification);
    } else if (notificationDate > oneWeekAgo) {
      result.ThisWeek.push(notification);
    } else if (notificationDate > oneMonthAgo) {
      result.ThisMonth.push(notification);
    } else {
      result.Older.push(notification);
    }
  });
  
  return result;
}