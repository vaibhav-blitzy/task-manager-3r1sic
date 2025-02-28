import React from 'react';
import classnames from 'classnames';
import { 
  FiBell, 
  FiInfo, 
  FiAlertCircle, 
  FiMessageSquare, 
  FiUserPlus, 
  FiRefreshCw 
} from 'react-icons/fi';

import { 
  Notification as NotificationType, 
  NotificationType as NotificationTypeEnum, 
  NotificationPriority 
} from '../../../types/notification';
import Badge, { BadgeColor } from '../../atoms/Badge/Badge';
import { Button } from '../../atoms/Button/Button';
import Icon from '../../atoms/Icon/Icon';
import { getRelativeDateLabel } from '../../../utils/date';

/**
 * Props for the Notification component
 */
interface NotificationProps {
  /** The notification data to display */
  notification: NotificationType;
  /** Optional callback when marking a notification as read */
  onRead?: (id: string) => void;
  /** Optional callback when dismissing a notification */
  onDismiss?: (id: string) => void;
  /** Optional callback when clicking on a notification */
  onClick?: (notification: NotificationType) => void;
  /** Optional additional CSS class names */
  className?: string;
}

/**
 * Returns the appropriate icon component based on notification type
 */
function getNotificationIcon(type: NotificationTypeEnum) {
  switch (type) {
    case NotificationTypeEnum.TASK_ASSIGNED:
      return FiBell;
    case NotificationTypeEnum.TASK_DUE_SOON:
    case NotificationTypeEnum.TASK_OVERDUE:
      return FiAlertCircle;
    case NotificationTypeEnum.COMMENT_ADDED:
      return FiMessageSquare;
    case NotificationTypeEnum.MENTION:
      return FiInfo;
    case NotificationTypeEnum.PROJECT_INVITATION:
      return FiUserPlus;
    case NotificationTypeEnum.STATUS_CHANGE:
      return FiRefreshCw;
    default:
      return FiBell;
  }
}

/**
 * Maps notification priority to appropriate badge color
 */
function getNotificationPriorityColor(priority: NotificationPriority): BadgeColor {
  switch (priority) {
    case NotificationPriority.LOW:
      return BadgeColor.INFO;
    case NotificationPriority.NORMAL:
      return BadgeColor.PRIMARY;
    case NotificationPriority.HIGH:
      return BadgeColor.WARNING;
    case NotificationPriority.URGENT:
      return BadgeColor.ERROR;
    default:
      return BadgeColor.PRIMARY;
  }
}

/**
 * Notification component displays notification items with customizable
 * appearance based on notification type, priority, and read status.
 * Provides interactive elements for marking notifications as read and dismissing them.
 */
const Notification: React.FC<NotificationProps> = ({
  notification,
  onRead,
  onDismiss,
  onClick,
  className,
}) => {
  const { 
    id, 
    type, 
    title, 
    content, 
    priority, 
    read, 
    actionUrl,
    metadata 
  } = notification;

  // Get appropriate icon for the notification type
  const NotificationIcon = getNotificationIcon(type);
  
  // Get badge color for priority
  const badgeColor = getNotificationPriorityColor(priority);
  
  // Format creation timestamp
  const timeLabel = getRelativeDateLabel(metadata.created);
  
  // Generate class names based on read status and priority
  const notificationClasses = classnames(
    'flex p-4 border-b border-gray-100 transition-colors',
    {
      'bg-white': read,
      'bg-blue-50': !read,
      'hover:bg-gray-50': true,
      'border-l-4 border-l-amber-500': priority === NotificationPriority.HIGH,
      'border-l-4 border-l-red-500': priority === NotificationPriority.URGENT,
    },
    className
  );

  // Handle notification click
  const handleClick = () => {
    if (onClick) {
      onClick(notification);
    } else if (actionUrl) {
      window.location.href = actionUrl;
    }
  };

  // Handle mark as read
  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering onClick
    if (onRead) {
      onRead(id);
    }
  };

  // Handle dismiss
  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering onClick
    if (onDismiss) {
      onDismiss(id);
    }
  };

  return (
    <div 
      className={notificationClasses}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Notification: ${title}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="flex-shrink-0 mr-3 pt-0.5">
        <Icon 
          icon={NotificationIcon} 
          size={20} 
          color={!read ? '#3B82F6' : '#9CA3AF'} 
          aria-hidden="true"
        />
      </div>
      
      <div className="flex-1">
        <div className="flex justify-between items-start mb-1">
          <h4 className={classnames(
            'text-sm font-medium',
            { 'text-gray-900': read, 'text-blue-600': !read }
          )}>
            {title}
          </h4>
          
          {(priority === NotificationPriority.HIGH || priority === NotificationPriority.URGENT) && (
            <Badge 
              color={badgeColor} 
              size="sm"
              className="ml-2"
            >
              {priority.toLowerCase()}
            </Badge>
          )}
        </div>
        
        <p className="text-sm text-gray-600 mb-2">{content}</p>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">{timeLabel}</span>
          
          <div className="flex space-x-2">
            {!read && onRead && (
              <Button
                variant="text"
                size="sm"
                onClick={handleMarkAsRead}
                aria-label="Mark as read"
              >
                Mark as read
              </Button>
            )}
            
            {onDismiss && (
              <Button
                variant="text"
                size="sm"
                onClick={handleDismiss}
                aria-label="Dismiss notification"
              >
                Dismiss
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Notification;