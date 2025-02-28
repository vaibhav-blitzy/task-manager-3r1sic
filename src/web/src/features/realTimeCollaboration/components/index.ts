/**
 * Real-Time Collaboration Components
 * 
 * This file exports components that provide real-time collaboration features,
 * allowing users to see who is online, who is typing, and receive real-time
 * updates as changes are made to tasks and projects.
 */

// Presence indicators for showing users currently viewing/editing content
export { default as UserPresenceIndicator } from './UserPresenceIndicator';
export { default as PresenceBadge } from './PresenceBadge';
export { default as OnlineUsersList } from './OnlineUsersList';

// Typing notification components
export { default as TypingIndicator } from './TypingIndicator';
export { default as CommentTypingIndicator } from './CommentTypingIndicator';

// Edit lock components for managing collaborative editing
export { default as EditLockIndicator } from './EditLockIndicator';
export { default as LockAcquisition } from './LockAcquisition';
export { default as EditingConflictModal } from './EditingConflictModal';

// Real-time update components
export { default as RealtimeUpdateProvider } from './RealtimeUpdateProvider';
export { default as RealtimeListener } from './RealtimeListener';
export { default as CollaborationContext } from './CollaborationContext';

// Custom hooks for real-time features
export { default as usePresence } from './usePresence';
export { default as useEditLock } from './useEditLock';
export { default as useTypingNotification } from './useTypingNotification';
export { default as useRealtimeUpdates } from './useRealtimeUpdates';

// Types for real-time collaboration
export type { 
  PresenceStatus, 
  UserPresence, 
  EditLockState, 
  TypingState, 
  CollaborationContextType 
} from './types';