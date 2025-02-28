/**
 * Utility functions for real-time collaboration features, including operation transformation,
 * presence tracking, and WebSocket event handling.
 * 
 * @version 1.0.0
 */

import { isEqual } from 'lodash'; // ^4.17.21
import { Task } from '../../types/task';
import { User } from '../../types/user';

/**
 * Enumeration of WebSocket event types for real-time collaboration
 */
export enum WebSocketEventType {
  TASK_UPDATE = 'task.update',
  PRESENCE_UPDATE = 'user.presence',
  EDIT_LOCK = 'edit.lock',
  CURSOR_UPDATE = 'user.cursor',
  COMMENT_ADDED = 'task.comment'
}

/**
 * Represents a transformation operation in collaborative editing
 */
export interface Operation {
  /** Unique identifier for the operation */
  id: string;
  /** ID of the object being modified */
  objectId: string;
  /** Type of object being modified (task, comment, etc.) */
  objectType: string;
  /** ID of the user who created the operation */
  userId: string;
  /** Timestamp when the operation was created */
  timestamp: number;
  /** Operation-specific data */
  data: any;
}

/**
 * Data specific to text operations
 */
export interface TextOperationData {
  /** Position in the text where the operation is applied */
  position: number;
  /** Text to insert (empty string for deletion only) */
  insertText: string;
  /** Number of characters to delete (0 for insertion only) */
  deleteCount: number;
}

/**
 * Represents a text-specific operation with insertions and deletions
 */
export interface TextOperation extends Operation {
  /** Text operation data */
  data: TextOperationData;
}

/**
 * User presence information for real-time collaboration
 */
export interface PresenceData {
  /** ID of the user */
  userId: string;
  /** Current presence status (online, away, busy, offline) */
  status: string;
  /** Timestamp when the presence was updated */
  timestamp: number;
  /** Additional context-specific data */
  contextData: Record<string, any>;
}

/**
 * Structure for events sent over WebSocket
 */
export interface WebSocketEvent {
  /** Type of the event (from WebSocketEventType enum) */
  type: string;
  /** Event payload */
  payload: any;
  /** ID of the user who sent the event */
  senderId: string;
  /** Timestamp when the event was created */
  timestamp: number;
}

/**
 * Cursor position data for collaborative editing
 */
export interface CursorData {
  /** ID of the user */
  userId: string;
  /** Cursor position in the text */
  position: number;
  /** ID of the object being edited */
  objectId: string;
  /** Timestamp when the cursor position was updated */
  timestamp: number;
}

/**
 * Lock information for collaborative editing
 */
export interface EditLock {
  /** ID of the object being locked */
  objectId: string;
  /** Type of object being locked */
  objectType: string;
  /** ID of the user who acquired the lock */
  userId: string;
  /** Timestamp when the lock was acquired */
  acquiredAt: number;
  /** Timestamp when the lock expires */
  expiresAt: number;
}

/**
 * Creates a new operation object representing a change to a collaborative document
 * 
 * @param objectId - ID of the object being modified
 * @param objectType - Type of object being modified
 * @param data - Operation-specific data
 * @param userId - ID of the user creating the operation
 * @returns A new operation object with unique ID, timestamp, and change data
 */
export const createOperation = (
  objectId: string,
  objectType: string,
  data: any,
  userId: string
): Operation => {
  // Generate a unique ID for the operation using timestamp and random string
  const operationId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  return {
    id: operationId,
    objectId,
    objectType,
    userId,
    timestamp: Date.now(),
    data
  };
};

/**
 * Transforms an operation against another concurrent operation for conflict resolution
 * using Operational Transformation principles
 * 
 * @param incomingOp - The incoming operation to be transformed
 * @param existingOp - The existing operation to transform against
 * @returns A transformed operation that can be applied after the existing one
 */
export const transformOperation = (
  incomingOp: Operation,
  existingOp: Operation
): Operation => {
  // If operations are on different objects, no transform needed
  if (incomingOp.objectId !== existingOp.objectId) {
    return incomingOp;
  }
  
  // Clone the incoming operation to avoid mutation
  const transformedOp: Operation = { ...incomingOp };
  
  // Check if both are text operations
  if (
    incomingOp.data.hasOwnProperty('position') &&
    existingOp.data.hasOwnProperty('position')
  ) {
    // Get text operation data
    const incomingData = incomingOp.data as TextOperationData;
    const existingData = existingOp.data as TextOperationData;
    
    // Clone data for the transformed operation
    const transformedData: TextOperationData = { ...incomingData };
    
    // Apply OT algorithm for text operations
    if (existingData.position < incomingData.position) {
      // Existing operation is before incoming operation position
      // Adjust position based on characters inserted/deleted by existing operation
      const netChange = existingData.insertText.length - existingData.deleteCount;
      transformedData.position = Math.max(0, incomingData.position + netChange);
    } else if (
      existingData.position === incomingData.position &&
      incomingData.deleteCount > 0 &&
      existingData.insertText.length > 0
    ) {
      // Conflicting operations at the same position
      // If incoming deletes and existing inserts, adjust position for the deletion
      transformedData.position += existingData.insertText.length;
    }
    
    transformedOp.data = transformedData;
  } else if (
    // For simple scalar values, use last-writer-wins strategy based on timestamp
    !isEqual(incomingOp.data, existingOp.data) &&
    typeof incomingOp.data === 'object' &&
    typeof existingOp.data === 'object'
  ) {
    // For non-text operations on the same property, use timestamp to determine winner
    if (existingOp.timestamp > incomingOp.timestamp) {
      // Existing operation wins, no change needed
      return incomingOp;
    }
  }
  
  return transformedOp;
};

/**
 * Applies an operation to the current state of an object
 * 
 * @param currentState - The current state of the object
 * @param operation - The operation to apply
 * @returns The new state after applying the operation
 */
export const applyOperation = (
  currentState: any,
  operation: Operation
): any => {
  // Clone the current state to avoid mutation
  const newState = JSON.parse(JSON.stringify(currentState));
  
  // Handle different operation types
  if (operation.objectType === 'task') {
    // Handle task operations
    const task = newState as Task;
    
    // Task title update
    if (operation.data.field === 'title') {
      task.title = operation.data.value;
    }
    // Task description text operation
    else if (operation.data.field === 'description' && operation.data.hasOwnProperty('position')) {
      const textOp = operation.data as TextOperationData;
      if (!task.description) {
        task.description = '';
      }
      
      const before = task.description.substring(0, textOp.position);
      const after = task.description.substring(textOp.position + textOp.deleteCount);
      task.description = before + textOp.insertText + after;
    }
    // Other field updates
    else if (operation.data.field && operation.data.value !== undefined) {
      (task as any)[operation.data.field] = operation.data.value;
    }
  } else if (operation.objectType === 'comment') {
    // Handle comment operations (similar pattern)
    if (operation.data.field === 'content' && operation.data.hasOwnProperty('position')) {
      const textOp = operation.data as TextOperationData;
      const comment = newState;
      
      if (!comment.content) {
        comment.content = '';
      }
      
      const before = comment.content.substring(0, textOp.position);
      const after = comment.content.substring(textOp.position + textOp.deleteCount);
      comment.content = before + textOp.insertText + after;
    } else if (operation.data.field && operation.data.value !== undefined) {
      (newState as any)[operation.data.field] = operation.data.value;
    }
  }
  
  return newState;
};

/**
 * Formats user presence data for transmission over WebSocket
 * 
 * @param userId - ID of the user
 * @param status - Presence status (online, away, busy, offline)
 * @param contextData - Additional context-specific data
 * @returns Formatted presence data ready for transmission
 */
export const formatPresenceData = (
  userId: string,
  status: string,
  contextData: Record<string, any> = {}
): PresenceData => {
  return {
    userId,
    status,
    timestamp: Date.now(),
    contextData
  };
};

/**
 * Parses a WebSocket message into a structured event object
 * 
 * @param message - JSON string message from WebSocket
 * @returns Parsed event object
 * @throws Error if message is invalid
 */
export const parseWebSocketMessage = (message: string): WebSocketEvent => {
  try {
    const parsed = JSON.parse(message);
    
    // Validate required fields
    if (!parsed.type || !parsed.senderId) {
      throw new Error('Invalid WebSocket message: missing required fields');
    }
    
    // Convert to strongly typed event object
    const event: WebSocketEvent = {
      type: parsed.type,
      payload: parsed.payload || {},
      senderId: parsed.senderId,
      timestamp: parsed.timestamp || Date.now()
    };
    
    return event;
  } catch (error) {
    // Re-throw with clearer message
    throw new Error(`Failed to parse WebSocket message: ${(error as Error).message}`);
  }
};

/**
 * Formats an event object into a string for WebSocket transmission
 * 
 * @param event - Event object to format
 * @returns JSON string ready for transmission
 */
export const formatWebSocketMessage = (event: WebSocketEvent): string => {
  // Validate the event object
  if (!event.type || !event.senderId) {
    throw new Error('Invalid WebSocket event: missing required fields');
  }
  
  // Ensure timestamp exists
  if (!event.timestamp) {
    event.timestamp = Date.now();
  }
  
  // Convert to JSON string
  return JSON.stringify(event);
};

/**
 * Detects if two operations conflict with each other
 * 
 * @param op1 - First operation
 * @param op2 - Second operation
 * @returns True if the operations conflict, false otherwise
 */
export const detectConflict = (op1: Operation, op2: Operation): boolean => {
  // Different objects don't conflict
  if (op1.objectId !== op2.objectId) {
    return false;
  }
  
  // Different fields don't conflict
  if (
    op1.data.field && 
    op2.data.field && 
    op1.data.field !== op2.data.field
  ) {
    return false;
  }
  
  // Text operations at different positions don't conflict
  if (
    op1.data.hasOwnProperty('position') &&
    op2.data.hasOwnProperty('position')
  ) {
    const pos1 = op1.data.position;
    const pos2 = op2.data.position;
    
    // Non-overlapping operations don't conflict
    if (
      pos1 + (op1.data.deleteCount || 0) <= pos2 ||
      pos2 + (op2.data.deleteCount || 0) <= pos1
    ) {
      return false;
    }
  }
  
  // Check if operations happened within conflict threshold time (500ms)
  const timeDiff = Math.abs(op1.timestamp - op2.timestamp);
  const CONFLICT_THRESHOLD = 500; // ms
  
  return timeDiff < CONFLICT_THRESHOLD;
};

/**
 * Tracks and formats cursor position data for collaborative editing
 * 
 * @param userId - ID of the user
 * @param position - Cursor position in the text
 * @param objectId - ID of the object being edited
 * @returns Formatted cursor position data for transmission
 */
export const trackCursorPosition = (
  userId: string,
  position: number,
  objectId: string
): CursorData => {
  return {
    userId,
    position,
    objectId,
    timestamp: Date.now()
  };
};

/**
 * Updates cursor positions after text operations are applied
 * 
 * @param cursors - Array of current cursor positions
 * @param operation - Text operation that was applied
 * @returns Updated cursor positions
 */
export const updateCursorPosition = (
  cursors: CursorData[],
  operation: TextOperation
): CursorData[] => {
  // Clone cursors to avoid mutation
  const updatedCursors = [...cursors];
  const opData = operation.data;
  
  // Update each cursor based on the operation
  return updatedCursors.map(cursor => {
    // Skip cursors on different objects
    if (cursor.objectId !== operation.objectId) {
      return cursor;
    }
    
    // Skip the cursor of the user who made the change
    if (cursor.userId === operation.userId) {
      return cursor;
    }
    
    // Clone the cursor to avoid mutation
    const updatedCursor = { ...cursor };
    
    // If cursor is after operation position, adjust it
    if (cursor.position > opData.position) {
      // Calculate net change in text length
      const netChange = opData.insertText.length - opData.deleteCount;
      
      // If cursor is within deleted range, move it to operation position
      if (cursor.position < opData.position + opData.deleteCount) {
        updatedCursor.position = opData.position;
      } else {
        // Otherwise adjust by net change
        updatedCursor.position = Math.max(0, cursor.position + netChange);
      }
    }
    
    return updatedCursor;
  });
};

/**
 * Checks if an object is currently locked for editing by another user
 * 
 * @param objectId - ID of the object to check
 * @param objectType - Type of the object to check
 * @param locks - Array of current edit locks
 * @returns True if the object is locked by another user, false otherwise
 */
export const isEditLocked = (
  objectId: string,
  objectType: string,
  locks: EditLock[]
): boolean => {
  // Find a lock for the specified object
  const lock = locks.find(l => 
    l.objectId === objectId && 
    l.objectType === objectType
  );
  
  // Check if lock exists and is not expired
  if (lock && lock.expiresAt > Date.now()) {
    return true;
  }
  
  return false;
};

/**
 * Creates an edit lock object for a collaborative object
 * 
 * @param objectId - ID of the object to lock
 * @param objectType - Type of the object to lock
 * @param userId - ID of the user acquiring the lock
 * @param durationMs - How long the lock should last in milliseconds (default: 5 minutes)
 * @returns A new edit lock object
 */
export const createEditLock = (
  objectId: string,
  objectType: string,
  userId: string,
  durationMs: number = 5 * 60 * 1000
): EditLock => {
  const now = Date.now();
  
  return {
    objectId,
    objectType,
    userId,
    acquiredAt: now,
    expiresAt: now + durationMs
  };
};