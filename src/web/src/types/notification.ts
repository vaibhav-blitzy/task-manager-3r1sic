/**
 * TypeScript type definitions for the notification system, including notification objects,
 * preferences, and related enums.
 * 
 * These types support the Notification System feature (F-008) by providing structured
 * definitions for notification data models and user preference settings.
 * 
 * @version 1.0.0
 */

import { User } from '../types/user';
import { Project } from '../types/project';

/**
 * Standard notification types defined in the system
 */
export enum NotificationType {
  /**
   * Sent when a task is assigned to a user
   */
  TASK_ASSIGNED = 'task_assigned',
  
  /**
   * Sent when a task's due date is approaching (typically 24 hours before)
   */
  TASK_DUE_SOON = 'task_due_soon',
  
  /**
   * Sent when a task has passed its due date without completion
   */
  TASK_OVERDUE = 'task_overdue',
  
  /**
   * Sent when someone comments on a task the user is involved with
   */
  COMMENT_ADDED = 'comment_added',
  
  /**
   * Sent when a user is mentioned in a comment
   */
  MENTION = 'mention',
  
  /**
   * Sent when a user is invited to join a project
   */
  PROJECT_INVITATION = 'project_invitation',
  
  /**
   * Sent when a task's status is changed
   */
  STATUS_CHANGE = 'status_change'
}

/**
 * Priority levels for notifications
 */
export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

/**
 * Delivery channels for notifications
 */
export enum NotificationChannel {
  IN_APP = 'in_app',
  EMAIL = 'email',
  PUSH = 'push'
}

/**
 * Status of notification delivery attempts
 */
export enum DeliveryStatus {
  DELIVERED = 'delivered',
  FAILED = 'failed',
  PENDING = 'pending',
  DISABLED = 'disabled'
}

/**
 * Metadata associated with a notification
 */
export interface NotificationMetadata {
  /**
   * ISO date string when the notification was created
   */
  created: string;
  
  /**
   * ISO date string when the notification was read, or null if unread
   */
  readAt: string | null;
  
  /**
   * Delivery status for each channel
   */
  deliveryStatus: {
    [NotificationChannel.IN_APP]: DeliveryStatus;
    [NotificationChannel.EMAIL]: DeliveryStatus;
    [NotificationChannel.PUSH]: DeliveryStatus;
  };
  
  /**
   * Information about the event that triggered this notification
   */
  sourceEvent: {
    /**
     * Type of event that triggered the notification
     */
    type: string;
    
    /**
     * ID of the related object (task, project, comment, etc.)
     */
    objectId: string;
    
    /**
     * Type of the related object
     */
    objectType: string;
  };
}

/**
 * Core notification interface representing a notification in the system
 */
export interface Notification {
  /**
   * Unique identifier for the notification
   */
  id: string;
  
  /**
   * ID of the user receiving the notification
   */
  recipientId: string;
  
  /**
   * Type of notification
   */
  type: NotificationType;
  
  /**
   * Short title/summary of the notification
   */
  title: string;
  
  /**
   * Detailed content of the notification
   */
  content: string;
  
  /**
   * Priority level of the notification
   */
  priority: NotificationPriority;
  
  /**
   * Whether the notification has been read
   */
  read: boolean;
  
  /**
   * URL to the relevant content when clicking the notification
   */
  actionUrl: string;
  
  /**
   * Additional metadata for the notification
   */
  metadata: NotificationMetadata;
}

/**
 * Channel-specific notification preferences
 */
export interface ChannelPreference {
  /**
   * Whether in-app notifications are enabled
   */
  inApp: boolean;
  
  /**
   * Whether email notifications are enabled
   */
  email: boolean;
  
  /**
   * Whether push notifications are enabled
   */
  push: boolean;
}

/**
 * Digest notification preferences
 */
export interface DigestPreference {
  /**
   * Whether digest notifications are enabled
   */
  enabled: boolean;
  
  /**
   * Frequency of digest notifications (daily, weekly, etc.)
   */
  frequency: string;
}

/**
 * Quiet hours notification preferences
 */
export interface QuietHourPreference {
  /**
   * Whether quiet hours are enabled
   */
  enabled: boolean;
  
  /**
   * Start time for quiet hours (HH:MM format)
   */
  start: string;
  
  /**
   * End time for quiet hours (HH:MM format)
   */
  end: string;
  
  /**
   * Timezone for quiet hours (e.g., "America/New_York")
   */
  timezone: string;
  
  /**
   * Whether urgent notifications should bypass quiet hours
   */
  excludeUrgent: boolean;
}

/**
 * User notification preferences at all levels (global, type, project)
 */
export interface NotificationPreferences {
  /**
   * Default settings applied to all notifications
   */
  globalSettings: ChannelPreference & {
    /**
     * Digest notification settings
     */
    digest: DigestPreference;
  };
  
  /**
   * Settings for specific notification types, overriding global settings
   */
  typeSettings: Record<NotificationType, ChannelPreference>;
  
  /**
   * Settings for specific projects, overriding global and type settings
   */
  projectSettings: Record<string, ChannelPreference>;
  
  /**
   * Quiet hours settings
   */
  quietHours: QuietHourPreference;
}

/**
 * Parameters for requesting a list of notifications
 */
export interface GetNotificationsRequest {
  /**
   * Page number for pagination (1-based)
   */
  page: number;
  
  /**
   * Number of items per page
   */
  limit: number;
  
  /**
   * Optional filter criteria
   */
  filter?: {
    /**
     * Filter by read status
     */
    read?: boolean;
    
    /**
     * Filter by notification type
     */
    type?: NotificationType | NotificationType[];
    
    /**
     * Filter by priority
     */
    priority?: NotificationPriority | NotificationPriority[];
    
    /**
     * Filter by date range (start)
     */
    fromDate?: string;
    
    /**
     * Filter by date range (end)
     */
    toDate?: string;
  };
}

/**
 * Response structure for notification list requests
 */
export interface GetNotificationsResponse {
  /**
   * Array of notification items
   */
  items: Notification[];
  
  /**
   * Total number of notifications matching the filter criteria
   */
  total: number;
  
  /**
   * Current page number
   */
  page: number;
  
  /**
   * Number of items per page
   */
  limit: number;
}

/**
 * Request to update a notification (e.g., mark as read)
 */
export interface UpdateNotificationRequest {
  /**
   * Update the read status
   */
  read: boolean;
}

/**
 * Request to update notification preferences
 */
export interface UpdatePreferencesRequest {
  /**
   * Updated notification preferences
   */
  preferences: NotificationPreferences;
}