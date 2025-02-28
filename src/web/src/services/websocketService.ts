/**
 * WebSocket Service for Task Management System
 * 
 * Provides real-time communication capabilities for collaborative features including:
 * - Connection lifecycle management
 * - Channel subscriptions
 * - Real-time event handling
 * - Presence tracking
 * - Collaborative editing support
 * - Automatic reconnection with exponential backoff
 * 
 * @version 1.0.0
 */

import { refreshAuthToken } from '../api/client';
import { 
  WEBSOCKET_URL, 
  WEBSOCKET_EVENTS, 
  RETRY_ATTEMPTS, 
  ACCESS_TOKEN_EXPIRY,
  AUTH_TOKEN_KEY
} from '../config/constants';
import { getItem } from './storageService';
import { Subject, BehaviorSubject, Observable } from 'rxjs';

/**
 * Enum for tracking WebSocket connection states
 */
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  FAILED = 'failed'
}

/**
 * Interface defining operations for collaborative editing
 */
export interface EditOperation {
  type: string;
  position: number;
  insert?: string;
  delete?: number;
}

/**
 * Interface for lock acquisition results
 */
export interface LockResult {
  success: boolean;
  lockId?: string;
  error?: string;
  lockedBy?: string;
  expiresAt?: number;
}

/**
 * Interface for operation submission results
 */
export interface OperationResult {
  success: boolean;
  error?: string;
  version?: number;
  operations?: EditOperation[];
}

/**
 * Manages WebSocket connections and provides real-time event handling for collaborative features
 */
export class WebSocketService {
  private socket: WebSocket | null = null;
  private connectionState: BehaviorSubject<ConnectionState> = new BehaviorSubject<ConnectionState>(ConnectionState.DISCONNECTED);
  private presenceData: BehaviorSubject<Record<string, any>> = new BehaviorSubject<Record<string, any>>({});
  private eventListeners: Map<string, Set<Function>> = new Map();
  private authToken: string | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = RETRY_ATTEMPTS || 5;
  private reconnectDelay: number = 1000; // Base delay in ms
  private reconnecting: boolean = false;
  private subscribedChannels: Set<string> = new Set();
  private channelResources: Map<string, string[]> = new Map();
  private tokenRefreshTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;

  /**
   * Establishes a WebSocket connection to the server with authentication
   * @returns Promise resolving to true if connection is successful, false otherwise
   */
  public async connect(): Promise<boolean> {
    // If already connected, return true
    if (this.isConnected()) {
      return true;
    }

    this.connectionState.next(ConnectionState.CONNECTING);

    // Get authentication token from storage
    this.authToken = getItem<string>(AUTH_TOKEN_KEY);
    
    if (!this.authToken) {
      console.error('No authentication token available for WebSocket connection');
      this.connectionState.next(ConnectionState.DISCONNECTED);
      return false;
    }

    // Create a promise that will resolve when connection is established or fails
    return new Promise<boolean>((resolve) => {
      try {
        // Create WebSocket with auth token
        const wsUrl = `${WEBSOCKET_URL}?token=${this.authToken}`;
        this.socket = new WebSocket(wsUrl);

        // Set up event handlers
        this.socket.onopen = () => {
          console.log('WebSocket connection established');
          this.connectionState.next(ConnectionState.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.setupTokenRefresh();
          resolve(true);
        };

        this.socket.onmessage = (event: MessageEvent) => {
          this.handleMessage(event);
        };

        this.socket.onclose = (event: CloseEvent) => {
          this.handleClose(event);
          if (!event.wasClean && event.code !== 1000) {
            resolve(false);
          }
        };

        this.socket.onerror = (event: Event) => {
          this.handleError(event);
          resolve(false);
        };
      } catch (error) {
        console.error('Error establishing WebSocket connection:', error);
        this.connectionState.next(ConnectionState.ERROR);
        resolve(false);
      }
    });
  }

  /**
   * Gracefully closes the WebSocket connection
   */
  public disconnect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      this.socket.close(1000, 'Normal closure');
    }

    // Clear timers
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }

    this.connectionState.next(ConnectionState.DISCONNECTED);
    this.reconnectAttempts = 0;
    this.reconnecting = false;
  }

  /**
   * Attempts to reconnect to the WebSocket server with exponential backoff
   * @returns Promise resolving to true if reconnection successful
   */
  public async reconnect(): Promise<boolean> {
    if (this.reconnecting) {
      return false;
    }

    this.reconnecting = true;
    this.reconnectAttempts++;

    if (this.reconnectAttempts > this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
      this.connectionState.next(ConnectionState.FAILED);
      this.reconnecting = false;
      return false;
    }

    // Calculate backoff delay with exponential increase and some jitter
    const delay = Math.min(
      30000, // Cap at 30 seconds
      Math.pow(2, this.reconnectAttempts) * this.reconnectDelay +
        Math.random() * 1000
    );

    console.log(`Attempting to reconnect in ${Math.round(delay / 1000)} seconds (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    // Wait for the calculated delay
    await new Promise(resolve => setTimeout(resolve, delay));

    // Try to connect again
    const connected = await this.connect();

    if (connected) {
      // Restore previous subscriptions
      await this.restoreSubscriptions();
      this.reconnecting = false;
      return true;
    } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
      // Try again if we haven't reached max attempts
      this.reconnecting = false;
      return this.reconnect();
    }

    this.reconnecting = false;
    return false;
  }

  /**
   * Subscribes to a specific channel or resource to receive real-time updates
   * @param channel The channel to subscribe to
   * @param resourceId Optional resource ID for specific resource updates
   * @returns Promise resolving to true if subscription successful
   */
  public async subscribe(channel: string, resourceId?: string): Promise<boolean> {
    if (!this.isConnected() && !(await this.connect())) {
      return false;
    }

    return new Promise<boolean>((resolve) => {
      try {
        // Create subscription message
        const subscribeMessage = {
          type: 'subscribe',
          channel: channel,
          resourceId: resourceId
        };

        // Send subscription request
        this.socket!.send(JSON.stringify(subscribeMessage));

        // Track subscriptions locally
        this.subscribedChannels.add(channel);
        
        if (resourceId) {
          if (!this.channelResources.has(channel)) {
            this.channelResources.set(channel, []);
          }
          const resources = this.channelResources.get(channel)!;
          if (!resources.includes(resourceId)) {
            resources.push(resourceId);
          }
        }

        resolve(true);
      } catch (error) {
        console.error('Error subscribing to channel:', error);
        resolve(false);
      }
    });
  }

  /**
   * Unsubscribes from a specific channel or resource
   * @param channel The channel to unsubscribe from
   * @param resourceId Optional resource ID for specific resource
   * @returns Promise resolving to true if unsubscription successful
   */
  public async unsubscribe(channel: string, resourceId?: string): Promise<boolean> {
    if (!this.isConnected()) {
      return true; // Already not subscribed if not connected
    }

    return new Promise<boolean>((resolve) => {
      try {
        // Create unsubscription message
        const unsubscribeMessage = {
          type: 'unsubscribe',
          channel: channel,
          resourceId: resourceId
        };

        // Send unsubscription request
        this.socket!.send(JSON.stringify(unsubscribeMessage));

        // Remove from tracked subscriptions
        if (resourceId) {
          const resources = this.channelResources.get(channel);
          if (resources) {
            const index = resources.indexOf(resourceId);
            if (index > -1) {
              resources.splice(index, 1);
            }
            // If no more resources for this channel, remove the channel
            if (resources.length === 0) {
              this.channelResources.delete(channel);
              this.subscribedChannels.delete(channel);
            }
          }
        } else {
          // If no resourceId, remove entire channel subscription
          this.subscribedChannels.delete(channel);
          this.channelResources.delete(channel);
        }

        resolve(true);
      } catch (error) {
        console.error('Error unsubscribing from channel:', error);
        resolve(false);
      }
    });
  }

  /**
   * Publishes an event to a specific channel
   * @param channel The channel to publish to
   * @param data The data to publish
   * @returns Promise resolving to true if message sent successfully
   */
  public async publish(channel: string, data: any): Promise<boolean> {
    if (!this.isConnected() && !(await this.connect())) {
      return false;
    }

    return new Promise<boolean>((resolve) => {
      try {
        // Create message to publish
        const message = {
          type: 'publish',
          channel: channel,
          data: data
        };

        // Send message
        this.socket!.send(JSON.stringify(message));
        resolve(true);
      } catch (error) {
        console.error('Error publishing message:', error);
        resolve(false);
      }
    });
  }

  /**
   * Registers an event listener for a specific event type
   * @param eventType The type of event to listen for
   * @param listener The callback function to be called when the event occurs
   * @returns Function to remove the listener
   */
  public on(eventType: string, listener: Function): Function {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }

    const listeners = this.eventListeners.get(eventType)!;
    listeners.add(listener);

    // Return a function to remove this listener
    return () => this.off(eventType, listener);
  }

  /**
   * Removes an event listener for a specific event type
   * @param eventType The type of event
   * @param listener The listener function to remove
   * @returns True if the listener was removed, false otherwise
   */
  public off(eventType: string, listener: Function): boolean {
    const listeners = this.eventListeners.get(eventType);
    if (!listeners) {
      return false;
    }

    return listeners.delete(listener);
  }

  /**
   * Updates the user's presence status and information
   * @param status The presence status (online, away, busy, etc.)
   * @param additionalData Additional presence information
   * @returns Promise resolving to true if presence update sent successfully
   */
  public async updatePresence(status: string, additionalData: Record<string, any> = {}): Promise<boolean> {
    if (!this.isConnected() && !(await this.connect())) {
      return false;
    }

    const presenceData = {
      status,
      lastActivity: new Date().toISOString(),
      ...additionalData
    };

    return new Promise<boolean>((resolve) => {
      try {
        // Create presence update message
        const message = {
          type: 'presence',
          data: presenceData
        };

        // Send message
        this.socket!.send(JSON.stringify(message));

        // Update local presence data
        this.presenceData.next({
          ...this.presenceData.value,
          ...presenceData
        });

        resolve(true);
      } catch (error) {
        console.error('Error updating presence:', error);
        resolve(false);
      }
    });
  }

  /**
   * Sends the user's typing status for collaborative editing
   * @param isTyping Whether the user is currently typing
   * @param resourceType The type of resource being edited (task, comment, etc.)
   * @param resourceId The ID of the resource being edited
   * @returns Promise resolving to true if typing status sent successfully
   */
  public async updateTypingStatus(
    isTyping: boolean,
    resourceType: string,
    resourceId: string
  ): Promise<boolean> {
    if (!this.isConnected() && !(await this.connect())) {
      return false;
    }

    return new Promise<boolean>((resolve) => {
      try {
        // Create typing status message
        const message = {
          type: 'typing',
          data: {
            isTyping,
            resourceType,
            resourceId,
            timestamp: new Date().toISOString()
          }
        };

        // Send message
        this.socket!.send(JSON.stringify(message));
        resolve(true);
      } catch (error) {
        console.error('Error updating typing status:', error);
        resolve(false);
      }
    });
  }

  /**
   * Attempts to acquire a lock on a resource for exclusive editing
   * @param resourceType The type of resource to lock (task, comment, etc.)
   * @param resourceId The ID of the resource to lock
   * @param sectionId Optional section identifier for partial resource locking
   * @returns Promise resolving to lock acquisition result
   */
  public async acquireEditLock(
    resourceType: string,
    resourceId: string,
    sectionId?: string
  ): Promise<LockResult> {
    if (!this.isConnected() && !(await this.connect())) {
      return {
        success: false,
        error: 'Not connected to server'
      };
    }

    return new Promise<LockResult>((resolve) => {
      try {
        // Create unique ID to identify the response
        const requestId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;

        // Create lock request message
        const message = {
          type: 'lock.acquire',
          requestId,
          data: {
            resourceType,
            resourceId,
            sectionId
          }
        };

        // One-time event listener for this specific request
        const responseHandler = (event: MessageEvent) => {
          try {
            const response = JSON.parse(event.data);
            if (response.type === 'lock.response' && response.requestId === requestId) {
              this.socket?.removeEventListener('message', responseHandler);
              resolve(response.data as LockResult);
            }
          } catch (e) {
            // Ignore parsing errors for other messages
          }
        };

        // Add temporary listener for the response
        this.socket!.addEventListener('message', responseHandler);

        // Send message
        this.socket!.send(JSON.stringify(message));

        // Set timeout to prevent hanging if no response
        setTimeout(() => {
          this.socket?.removeEventListener('message', responseHandler);
          resolve({
            success: false,
            error: 'Lock request timed out'
          });
        }, 10000); // 10 second timeout
      } catch (error) {
        console.error('Error acquiring edit lock:', error);
        resolve({
          success: false,
          error: 'Internal error acquiring lock'
        });
      }
    });
  }

  /**
   * Releases a previously acquired lock on a resource
   * @param resourceType The type of resource
   * @param resourceId The ID of the resource
   * @param sectionId Optional section identifier for partial resource locking
   * @returns Promise resolving to true if lock released successfully
   */
  public async releaseEditLock(
    resourceType: string,
    resourceId: string,
    sectionId?: string
  ): Promise<boolean> {
    if (!this.isConnected()) {
      return false;
    }

    return new Promise<boolean>((resolve) => {
      try {
        // Create unlock request message
        const message = {
          type: 'lock.release',
          data: {
            resourceType,
            resourceId,
            sectionId
          }
        };

        // Send message
        this.socket!.send(JSON.stringify(message));
        resolve(true);
      } catch (error) {
        console.error('Error releasing edit lock:', error);
        resolve(false);
      }
    });
  }

  /**
   * Submits a collaborative editing operation with operational transformation
   * @param operation The editing operation
   * @param resourceType The type of resource being edited
   * @param resourceId The ID of the resource being edited
   * @param version The current version of the resource
   * @returns Promise resolving to operation result
   */
  public async submitOperation(
    operation: EditOperation,
    resourceType: string,
    resourceId: string,
    version: number
  ): Promise<OperationResult> {
    if (!this.isConnected() && !(await this.connect())) {
      return {
        success: false,
        error: 'Not connected to server'
      };
    }

    return new Promise<OperationResult>((resolve) => {
      try {
        // Create unique ID to identify the response
        const requestId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;

        // Create operation request message
        const message = {
          type: 'operation.submit',
          requestId,
          data: {
            resourceType,
            resourceId,
            version,
            operation
          }
        };

        // One-time event listener for this specific request
        const responseHandler = (event: MessageEvent) => {
          try {
            const response = JSON.parse(event.data);
            if (response.type === 'operation.response' && response.requestId === requestId) {
              this.socket?.removeEventListener('message', responseHandler);
              resolve(response.data as OperationResult);
            }
          } catch (e) {
            // Ignore parsing errors for other messages
          }
        };

        // Add temporary listener for the response
        this.socket!.addEventListener('message', responseHandler);

        // Send message
        this.socket!.send(JSON.stringify(message));

        // Set timeout to prevent hanging if no response
        setTimeout(() => {
          this.socket?.removeEventListener('message', responseHandler);
          resolve({
            success: false,
            error: 'Operation request timed out'
          });
        }, 10000); // 10 second timeout
      } catch (error) {
        console.error('Error submitting operation:', error);
        resolve({
          success: false,
          error: 'Internal error submitting operation'
        });
      }
    });
  }

  /**
   * Gets the current connection state as an observable
   * @returns Observable of connection state changes
   */
  public getConnectionState(): Observable<ConnectionState> {
    return this.connectionState.asObservable();
  }

  /**
   * Gets the current presence data as an observable
   * @returns Observable of presence data changes
   */
  public getPresenceData(): Observable<Record<string, any>> {
    return this.presenceData.asObservable();
  }

  /**
   * Checks if the WebSocket connection is currently established
   * @returns True if connected, false otherwise
   */
  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Processes incoming WebSocket messages and dispatches to listeners
   * @param event The message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data);
      const eventType = message.type;

      // Get listeners for this event type
      const listeners = this.eventListeners.get(eventType);
      if (listeners) {
        listeners.forEach(listener => {
          try {
            listener(message.data);
          } catch (error) {
            console.error(`Error in event listener for ${eventType}:`, error);
          }
        });
      }

      // Special handling for specific event types
      switch (eventType) {
        case 'presence':
          // Update presence data
          this.presenceData.next({
            ...this.presenceData.value,
            ...message.data
          });
          break;

        case 'ping':
          // Respond to ping with pong
          if (this.isConnected()) {
            this.socket!.send(JSON.stringify({
              type: 'pong',
              timestamp: Date.now()
            }));
          }
          break;

        case 'error':
          console.error('WebSocket error received:', message.data);
          // Check if we need to reconnect due to this error
          if (message.data.reconnect === true) {
            this.reconnect();
          }
          break;
      }

      // Forward all events to any listeners registered for ALL events
      const allListeners = this.eventListeners.get('*');
      if (allListeners) {
        allListeners.forEach(listener => {
          try {
            listener(message);
          } catch (error) {
            console.error(`Error in catch-all event listener:`, error);
          }
        });
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  /**
   * Handles WebSocket connection closure
   * @param event The close event
   */
  private handleClose(event: CloseEvent): void {
    // Clear timers
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }

    // Update connection state
    this.connectionState.next(ConnectionState.DISCONNECTED);

    // Log closure with appropriate message
    if (event.wasClean) {
      console.log(`WebSocket closed cleanly, code=${event.code}, reason=${event.reason}`);
    } else {
      console.error(`WebSocket connection died, code=${event.code}, reason=${event.reason}`);
      
      // Attempt to reconnect for unexpected closures
      if (event.code !== 1000) { // 1000 is normal closure
        this.reconnect();
      }
    }
  }

  /**
   * Handles WebSocket connection errors
   * @param event The error event
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.connectionState.next(ConnectionState.ERROR);
    
    // Attempt to reconnect on error
    this.reconnect();
  }

  /**
   * Starts a heartbeat to keep the WebSocket connection alive
   */
  private startHeartbeat(): void {
    // Clear existing heartbeat if any
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    // Send heartbeat ping every 30 seconds
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        try {
          this.socket!.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
          }));
        } catch (error) {
          console.error('Error sending heartbeat ping:', error);
          // If sending ping fails, attempt to reconnect
          this.reconnect();
        }
      } else {
        // If not connected, try to reconnect
        this.reconnect();
      }
    }, 30000); // 30 seconds
  }

  /**
   * Refreshes the authentication token for long-lived connections
   * @returns Promise resolving to true if token refresh successful
   */
  private async refreshToken(): Promise<boolean> {
    try {
      const success = await refreshAuthToken();
      
      if (success) {
        // Get new token from storage
        const newToken = getItem<string>(AUTH_TOKEN_KEY);
        if (newToken) {
          this.authToken = newToken;
          // Reset token refresh timer
          this.setupTokenRefresh();
          return true;
        }
      }
      
      // If refresh failed, try to reconnect with existing token
      this.reconnect();
      return false;
    } catch (error) {
      console.error('Error refreshing WebSocket auth token:', error);
      this.reconnect();
      return false;
    }
  }

  /**
   * Sets up token refresh for long-lived connections
   */
  private setupTokenRefresh(): void {
    // Clear existing refresh timer if any
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
    }

    // Set up refresh before token expires
    // Access tokens typically last 15 minutes, refresh 1 minute before expiry
    const refreshTime = (ACCESS_TOKEN_EXPIRY - 60) * 1000;
    
    this.tokenRefreshTimer = setTimeout(() => {
      this.refreshToken();
    }, refreshTime);
  }

  /**
   * Restores previous channel and resource subscriptions after reconnection
   * @returns Promise that resolves when all subscriptions are restored
   */
  private async restoreSubscriptions(): Promise<void> {
    if (!this.isConnected()) {
      return;
    }

    const subscriptionPromises: Promise<boolean>[] = [];

    // Resubscribe to all channels
    for (const channel of this.subscribedChannels) {
      const resources = this.channelResources.get(channel);
      
      if (resources && resources.length > 0) {
        // If channel has specific resources, subscribe to each resource
        for (const resourceId of resources) {
          subscriptionPromises.push(this.subscribe(channel, resourceId));
        }
      } else {
        // Otherwise subscribe to the entire channel
        subscriptionPromises.push(this.subscribe(channel));
      }
    }

    // Wait for all subscriptions to complete
    await Promise.all(subscriptionPromises);
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

// Export singleton instance as default
export default websocketService;