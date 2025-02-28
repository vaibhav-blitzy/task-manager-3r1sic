// src/web/src/features/notifications/components/index.ts

// Import the basic Notification component for displaying a single notification
import Notification from '../../../components/molecules/Notification/Notification';
// Import the NotificationCenter component for the notification center page
import NotificationCenter from '../../../pages/NotificationCenter/NotificationCenter';

// Export the Notification component for displaying individual notifications
export { Notification };

// Export the NotificationBadge component for displaying unread notification counts
export { NotificationBadge } from './NotificationBadge';

// Export the NotificationList component for displaying a list of notifications
export { NotificationList } from './NotificationList';

// Export the NotificationCenter component for the full notification center experience
export { NotificationCenter };