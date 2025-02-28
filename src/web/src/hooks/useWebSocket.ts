import { useState, useEffect, useRef, useCallback } from 'react';
import websocketService, { ConnectionState } from '../services/websocketService';

/**
 * Options for configuring the WebSocket hook
 */
interface WebSocketOptions {
  /**
   * Whether to automatically connect on mount
   * @default true
   */
  autoConnect?: boolean;
  
  /**
   * Whether to keep connection alive on component unmount
   * @default false
   */
  persistent?: boolean;
  
  /**
   * Callback when connection is established
   */
  onConnect?: () => void;
  
  /**
   * Callback when connection is closed
   */
  onDisconnect?: () => void;
  
  /**
   * Callback when connection error occurs
   */
  onError?: (error: any) => void;
}

/**
 * Custom React hook for managing WebSocket connections and real-time event handling
 * for Task Management System collaboration features.
 * 
 * Provides WebSocket connection lifecycle management, event subscription, and message
 * handling with automatic reconnection and presence tracking.
 * 
 * @param url Optional WebSocket URL override
 * @param options Optional configuration options
 * @returns Object containing connection state and WebSocket methods
 */
export function useWebSocket(url?: string, options: WebSocketOptions = {}) {
  // Default options merged with provided options
  const defaultOptions: WebSocketOptions = {
    autoConnect: true,
    persistent: false
  };
  
  const mergedOptions = { ...defaultOptions, ...options };
  
  // Connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  
  // Refs to store values that shouldn't trigger re-renders
  const optionsRef = useRef(mergedOptions);
  const subscriptionsRef = useRef<Map<string, Array<{ callback: (data: any) => void, cleanup: () => void }>>>(new Map());
  
  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = { ...optionsRef.current, ...options };
  }, [options]);
  
  /**
   * Connect to the WebSocket server
   * @returns Promise resolving to true if connection successful
   */
  const connect = useCallback(async (): Promise<boolean> => {
    try {
      const connected = await websocketService.connect();
      if (connected && optionsRef.current.onConnect) {
        optionsRef.current.onConnect();
      }
      return connected;
    } catch (error) {
      console.error('Error connecting to WebSocket server:', error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  /**
   * Disconnect from the WebSocket server
   */
  const disconnect = useCallback((): void => {
    try {
      websocketService.disconnect();
      if (optionsRef.current.onDisconnect) {
        optionsRef.current.onDisconnect();
      }
    } catch (error) {
      console.error('Error disconnecting from WebSocket server:', error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
    }
  }, []);
  
  /**
   * Subscribe to a channel or event
   * @param channel The channel to subscribe to
   * @param callback The callback function to call when an event occurs
   * @param resourceId Optional resource ID for specific resource updates
   * @returns Promise resolving to true if subscription successful
   */
  const subscribe = useCallback(async (
    channel: string,
    callback: (data: any) => void,
    resourceId?: string
  ): Promise<boolean> => {
    try {
      // Setup event listener
      const cleanup = websocketService.on(channel, callback);
      
      // Add to subscriptions map
      if (!subscriptionsRef.current.has(channel)) {
        subscriptionsRef.current.set(channel, []);
      }
      
      subscriptionsRef.current.get(channel)!.push({
        callback,
        cleanup
      });
      
      // Subscribe to the channel
      const success = await websocketService.subscribe(channel, resourceId);
      
      return success;
    } catch (error) {
      console.error(`Error subscribing to channel ${channel}:`, error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  /**
   * Unsubscribe from a channel or event
   * @param channel The channel to unsubscribe from
   * @param callback Optional callback to remove (if not provided, all callbacks are removed)
   * @param resourceId Optional resource ID for specific resource
   * @returns Promise resolving to true if unsubscription successful
   */
  const unsubscribe = useCallback(async (
    channel: string,
    callback?: (data: any) => void,
    resourceId?: string
  ): Promise<boolean> => {
    try {
      if (!subscriptionsRef.current.has(channel)) {
        return true; // Already unsubscribed
      }
      
      const handlers = subscriptionsRef.current.get(channel)!;
      
      if (callback) {
        // Find and remove the specific callback
        const handlerIndex = handlers.findIndex(h => h.callback === callback);
        
        if (handlerIndex >= 0) {
          // Call cleanup function (unsubscribe)
          handlers[handlerIndex].cleanup();
          // Remove from array
          handlers.splice(handlerIndex, 1);
        }
        
        // If no callbacks left, unsubscribe from the channel
        if (handlers.length === 0) {
          subscriptionsRef.current.delete(channel);
          return await websocketService.unsubscribe(channel, resourceId);
        }
        
        return true;
      } else {
        // Remove all callbacks for this channel
        handlers.forEach(handler => {
          handler.cleanup();
        });
        
        // Clear from map
        subscriptionsRef.current.delete(channel);
        
        // Unsubscribe from the channel
        return await websocketService.unsubscribe(channel, resourceId);
      }
    } catch (error) {
      console.error(`Error unsubscribing from channel ${channel}:`, error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  /**
   * Send a message to a channel
   * @param channel The channel to send the message to
   * @param data The data to send
   * @returns Promise resolving to true if message sent successfully
   */
  const sendMessage = useCallback(async (
    channel: string,
    data: any
  ): Promise<boolean> => {
    try {
      return await websocketService.publish(channel, data);
    } catch (error) {
      console.error(`Error sending message to channel ${channel}:`, error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  /**
   * Update user presence status
   * @param status The presence status (online, away, busy, etc.)
   * @param additionalData Additional presence information
   * @returns Promise resolving to true if presence update sent successfully
   */
  const updatePresence = useCallback(async (
    status: string,
    additionalData: Record<string, any> = {}
  ): Promise<boolean> => {
    try {
      return await websocketService.updatePresence(status, additionalData);
    } catch (error) {
      console.error('Error updating presence:', error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  /**
   * Update typing status for collaborative editing
   * @param isTyping Whether the user is currently typing
   * @param resourceType The type of resource being edited
   * @param resourceId The ID of the resource being edited
   * @returns Promise resolving to true if typing status sent successfully
   */
  const updateTypingStatus = useCallback(async (
    isTyping: boolean,
    resourceType: string,
    resourceId: string
  ): Promise<boolean> => {
    try {
      return await websocketService.updateTypingStatus(isTyping, resourceType, resourceId);
    } catch (error) {
      console.error('Error updating typing status:', error);
      if (optionsRef.current.onError) {
        optionsRef.current.onError(error);
      }
      return false;
    }
  }, []);
  
  // Set up connection state monitoring
  useEffect(() => {
    // Subscribe to connection state changes
    const subscription = websocketService.getConnectionState().subscribe(state => {
      setConnectionState(state);
      
      // Call appropriate callbacks
      if (state === ConnectionState.CONNECTED && optionsRef.current.onConnect) {
        optionsRef.current.onConnect();
      } else if (state === ConnectionState.DISCONNECTED && optionsRef.current.onDisconnect) {
        optionsRef.current.onDisconnect();
      } else if ((state === ConnectionState.ERROR || state === ConnectionState.FAILED) && 
                 optionsRef.current.onError) {
        optionsRef.current.onError(new Error(`WebSocket connection ${state}`));
      }
    });
    
    return () => {
      // Unsubscribe from connection state changes
      subscription.unsubscribe();
    };
  }, []);
  
  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (optionsRef.current.autoConnect) {
      connect();
    }
    
    // Clean up on unmount
    return () => {
      // Clean up all subscriptions
      subscriptionsRef.current.forEach((handlers, channel) => {
        handlers.forEach(handler => {
          handler.cleanup();
        });
        
        // Unsubscribe from channel on server
        websocketService.unsubscribe(channel);
      });
      
      // Clear subscriptions map
      subscriptionsRef.current.clear();
      
      // Disconnect if not persistent
      if (!optionsRef.current.persistent) {
        disconnect();
      }
    };
  }, [connect, disconnect]);
  
  // Return connection state and methods
  return {
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    updatePresence,
    updateTypingStatus
  };
}

export default useWebSocket;