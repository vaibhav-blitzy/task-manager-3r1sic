/**
 * Real-Time Collaboration Hooks
 * 
 * This module exports React hooks for enabling real-time collaboration features
 * in the Task Management System. These hooks provide integration with the WebSocket
 * connection, presence tracking, collaborative editing, and other real-time features.
 */

// WebSocket Connection Hook
export { useWebSocketConnection } from './useWebSocketConnection';

// User Presence Hooks
export { usePresence } from './usePresence';
export { useUserStatus } from './useUserStatus'; 
export { useOnlineUsers } from './useOnlineUsers';

// Collaborative Editing Hooks
export { useCollaborativeEditing } from './useCollaborativeEditing';
export { useEditLock } from './useEditLock';

// Real-time Event Hooks
export { useTaskUpdates } from './useTaskUpdates';
export { useProjectUpdates } from './useProjectUpdates';
export { useCommentUpdates } from './useCommentUpdates';

// Typing Indicator Hooks
export { useTypingIndicator } from './useTypingIndicator';

// Channel Subscription Hooks
export { useChannelSubscription } from './useChannelSubscription';
export { useTaskChannel } from './useTaskChannel';
export { useProjectChannel } from './useProjectChannel';

// Activity Tracking
export { useUserActivity } from './useUserActivity';
export { useViewingContext } from './useViewingContext';