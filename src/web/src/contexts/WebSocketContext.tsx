import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import websocketService, {
  ConnectionState,
  EditOperation,
  LockResult,
  OperationResult
} from '../../services/websocketService';

// Interface defining the shape of WebSocket context
interface WebSocketContextType {
  connectionState: ConnectionState;
  isConnected: boolean;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  subscribe: (channel: string, resourceId?: string, callback: (data: any) => void) => () => void;
  unsubscribe: (channel: string, resourceId?: string, callback: (data: any) => void) => void;
  sendMessage: (channel: string, data: any) => Promise<boolean>;
  updatePresence: (status: string, currentView: string) => Promise<boolean>;
  updateTypingStatus: (isTyping: boolean, resourceType: string, resourceId: string) => Promise<boolean>;
  acquireEditLock: (resourceType: string, resourceId: string, sectionId?: string) => Promise<LockResult>;
  releaseEditLock: (resourceType: string, resourceId: string, sectionId?: string) => Promise<boolean>;
  submitOperation: (operation: EditOperation, resourceType: string, resourceId: string, version: number) => Promise<OperationResult>;
}

// Props for the WebSocketProvider component
interface WebSocketProviderProps {
  children: ReactNode;
  options?: {
    autoConnect?: boolean;
  };
}

// Create the context with undefined default value
const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children, options = {} }: WebSocketProviderProps) {
  // Track connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  
  // Track subscriptions for cleanup and reconnection
  const subscriptions = useRef(new Map<string, Set<(data: any) => void>>());
  
  // Set up connection state tracking
  useEffect(() => {
    // Subscribe to connection state changes
    const subscription = websocketService.getConnectionState().subscribe(state => {
      const wasConnected = connectionState === ConnectionState.CONNECTED;
      const isNowConnected = state === ConnectionState.CONNECTED;
      
      setConnectionState(state);
      
      // If we just reconnected, resubscribe to all channels
      if (!wasConnected && isNowConnected) {
        subscriptions.current.forEach((_, key) => {
          const [channel, resourceId] = key.includes(':') 
            ? key.split(':') 
            : [key, undefined];
          
          websocketService.subscribe(channel, resourceId)
            .catch(error => console.error(`[WebSocketContext] Error resubscribing to ${key}:`, error));
        });
      }
    });
    
    // Auto-connect if specified
    if (options.autoConnect) {
      websocketService.connect().catch(error => {
        console.error('[WebSocketContext] Error during auto-connect:', error);
      });
    }
    
    return () => {
      // Clean up subscription
      subscription.unsubscribe();
      
      // Disconnect websocket
      websocketService.disconnect();
    };
  }, [options.autoConnect, connectionState]);
  
  // Connect to WebSocket
  const connect = useCallback(async () => {
    try {
      return await websocketService.connect();
    } catch (error) {
      console.error('[WebSocketContext] Error connecting to WebSocket:', error);
      return false;
    }
  }, []);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);
  
  // Helper to get subscription key
  const getSubscriptionKey = useCallback((channel: string, resourceId?: string) => {
    return resourceId ? `${channel}:${resourceId}` : channel;
  }, []);
  
  // Subscribe to a channel
  const subscribe = useCallback((channel: string, resourceId?: string, callback: (data: any) => void) => {
    const key = getSubscriptionKey(channel, resourceId);
    
    // Initialize callback set if needed
    if (!subscriptions.current.has(key)) {
      subscriptions.current.set(key, new Set());
    }
    
    // Add callback to the set
    const callbacks = subscriptions.current.get(key)!;
    callbacks.add(callback);
    
    // Subscribe to the channel if connected
    if (connectionState === ConnectionState.CONNECTED) {
      websocketService.subscribe(channel, resourceId)
        .catch(error => console.error(`[WebSocketContext] Error subscribing to ${key}:`, error));
    }
    
    // Return unsubscribe function
    return () => {
      unsubscribe(channel, resourceId, callback);
    };
  }, [connectionState, getSubscriptionKey]);
  
  // Handle incoming messages
  useEffect(() => {
    // Set up a message handler to route messages to the right callbacks
    const handleMessage = (message: any) => {
      // For each subscription, check if it should receive this message
      subscriptions.current.forEach((callbacks, key) => {
        // Extract channel and resourceId from the key
        const [subChannel, subResourceId] = key.includes(':')
          ? key.split(':')
          : [key, undefined];
        
        // If the message is for this channel
        if (message.channel === subChannel) {
          // If no resourceId specified or it matches the message
          if (!subResourceId || message.resourceId === subResourceId) {
            // Notify all callbacks
            callbacks.forEach(callback => {
              try {
                callback(message.data);
              } catch (error) {
                console.error(`[WebSocketContext] Error in callback for ${key}:`, error);
              }
            });
          }
        }
      });
    };
    
    // Listen for all messages and route them
    const unsubscribe = websocketService.on('*', handleMessage);
    
    return () => {
      // Remove message handler
      unsubscribe();
    };
  }, []);
  
  // Unsubscribe from a channel
  const unsubscribe = useCallback((channel: string, resourceId?: string, callback: (data: any) => void) => {
    const key = getSubscriptionKey(channel, resourceId);
    const callbacks = subscriptions.current.get(key);
    
    if (callbacks) {
      // Remove callback from set
      callbacks.delete(callback);
      
      // If no more callbacks, unsubscribe from channel
      if (callbacks.size === 0) {
        subscriptions.current.delete(key);
        
        if (connectionState === ConnectionState.CONNECTED) {
          websocketService.unsubscribe(channel, resourceId)
            .catch(error => console.error(`[WebSocketContext] Error unsubscribing from ${key}:`, error));
        }
      }
    }
  }, [connectionState, getSubscriptionKey]);
  
  // Send a message
  const sendMessage = useCallback(async (channel: string, data: any) => {
    try {
      return await websocketService.publish(channel, data);
    } catch (error) {
      console.error(`[WebSocketContext] Error sending message to ${channel}:`, error);
      return false;
    }
  }, []);
  
  // Update presence
  const updatePresence = useCallback(async (status: string, currentView: string) => {
    try {
      return await websocketService.updatePresence(status, { currentView });
    } catch (error) {
      console.error('[WebSocketContext] Error updating presence:', error);
      return false;
    }
  }, []);
  
  // Update typing status
  const updateTypingStatus = useCallback(async (isTyping: boolean, resourceType: string, resourceId: string) => {
    try {
      return await websocketService.updateTypingStatus(isTyping, resourceType, resourceId);
    } catch (error) {
      console.error('[WebSocketContext] Error updating typing status:', error);
      return false;
    }
  }, []);
  
  // Acquire edit lock
  const acquireEditLock = useCallback(async (resourceType: string, resourceId: string, sectionId?: string) => {
    try {
      return await websocketService.acquireEditLock(resourceType, resourceId, sectionId);
    } catch (error) {
      console.error('[WebSocketContext] Error acquiring edit lock:', error);
      return { success: false, error: 'Failed to acquire lock due to an error' };
    }
  }, []);
  
  // Release edit lock
  const releaseEditLock = useCallback(async (resourceType: string, resourceId: string, sectionId?: string) => {
    try {
      return await websocketService.releaseEditLock(resourceType, resourceId, sectionId);
    } catch (error) {
      console.error('[WebSocketContext] Error releasing edit lock:', error);
      return false;
    }
  }, []);
  
  // Submit operation
  const submitOperation = useCallback(async (operation: EditOperation, resourceType: string, resourceId: string, version: number) => {
    try {
      return await websocketService.submitOperation(operation, resourceType, resourceId, version);
    } catch (error) {
      console.error('[WebSocketContext] Error submitting operation:', error);
      return { success: false, error: 'Failed to submit operation due to an error' };
    }
  }, []);
  
  // Compute derived state
  const isConnected = connectionState === ConnectionState.CONNECTED;
  
  // Compile context value
  const contextValue: WebSocketContextType = {
    connectionState,
    isConnected,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    updatePresence,
    updateTypingStatus,
    acquireEditLock,
    releaseEditLock,
    submitOperation
  };
  
  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Custom hook for consuming the WebSocket context
export function useWebSocketContext(): WebSocketContextType {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

export default WebSocketContext;