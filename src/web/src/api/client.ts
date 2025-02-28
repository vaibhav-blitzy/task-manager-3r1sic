/**
 * API Client for the Task Management System
 * 
 * Configures and exports a centralized HTTP client for making API requests to the
 * backend services with standard error handling, authentication, and retry capabilities.
 * 
 * @version 1.5.x
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosError,
  AxiosResponse,
  InternalAxiosRequestConfig
} from 'axios';

import {
  API_BASE_URL,
  API_TIMEOUT,
  AUTH_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  RETRY_ATTEMPTS,
  DEFAULT_ERROR_MESSAGE
} from '../config/constants';

import { AUTH_ENDPOINTS } from './endpoints';
import { AuthTokens } from '../types/auth';
import { getItem, setItem, removeItem, StorageType } from '../services/storageService';

// Flag to track if a token refresh is in progress
let isRefreshing = false;
// Queue of requests to retry after token refresh
let refreshSubscribers: Array<(token: string) => void> = [];

/**
 * Adds a callback to the refresh queue
 * @param callback Function to call when token is refreshed
 */
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

/**
 * Executes all pending callbacks with the new token
 * @param token New access token
 */
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
}

/**
 * Creates and configures an Axios instance with base URL, default headers,
 * request/response interceptors, and error handling
 * @returns Configured axios instance for making API requests
 */
function createApiClient(): AxiosInstance {
  // Create axios instance with base configuration
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });

  // Request interceptor to add authorization token
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Get the token from session storage
      const token = getItem<string>(AUTH_TOKEN_KEY, StorageType.SESSION);
      
      // If token exists, add it to the Authorization header
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for successful responses and error handling
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
      
      // If the error is due to an expired token (401) and we haven't tried to refresh yet
      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        originalRequest.url !== AUTH_ENDPOINTS.REFRESH_TOKEN
      ) {
        if (!isRefreshing) {
          isRefreshing = true;
          originalRequest._retry = true;

          try {
            // Attempt to refresh the token
            const success = await refreshAuthToken();
            
            if (success) {
              // Get the new token
              const newToken = getItem<string>(AUTH_TOKEN_KEY, StorageType.SESSION);
              
              if (newToken) {
                // Notify all subscribers that the token has been refreshed
                onTokenRefreshed(newToken);
                
                // Retry the original request with the new token
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${newToken}`;
                } else {
                  originalRequest.headers = { Authorization: `Bearer ${newToken}` };
                }
                
                return instance.request(originalRequest);
              }
            }
          } catch (refreshError) {
            // If token refresh fails, proceed with the error
            console.error('Token refresh failed:', refreshError);
          } finally {
            isRefreshing = false;
          }
        } else {
          // If a token refresh is already in progress, add this request to the queue
          return new Promise((resolve) => {
            subscribeTokenRefresh((token: string) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              } else {
                originalRequest.headers = { Authorization: `Bearer ${token}` };
              }
              resolve(instance.request(originalRequest));
            });
          });
        }
      }

      // For all other errors, or if token refresh failed, handle the error
      return handleApiError(error);
    }
  );

  return instance;
}

// Create the API client instance
const apiClient = createApiClient();

/**
 * Stores authentication tokens and updates the authorization header for future API requests
 * @param tokens Object containing access and refresh tokens
 */
export function setAuthToken(tokens: AuthTokens): void {
  if (tokens.accessToken) {
    // Store access token in session storage (cleared on browser close)
    setItem(AUTH_TOKEN_KEY, tokens.accessToken, StorageType.SESSION);
    
    // Update authorization header for future requests
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${tokens.accessToken}`;
  }
  
  if (tokens.refreshToken) {
    // Store refresh token in local storage (persists across sessions)
    setItem(REFRESH_TOKEN_KEY, tokens.refreshToken, StorageType.LOCAL);
  }
}

/**
 * Removes authentication tokens and clears the authorization header
 */
export function clearAuthToken(): void {
  // Remove tokens from storage
  removeItem(AUTH_TOKEN_KEY, StorageType.SESSION);
  removeItem(REFRESH_TOKEN_KEY, StorageType.LOCAL);
  
  // Remove Authorization header from future requests
  delete apiClient.defaults.headers.common['Authorization'];
}

/**
 * Attempts to refresh the access token using the stored refresh token
 * @returns Promise resolving to true if token refresh was successful, false otherwise
 */
export async function refreshAuthToken(): Promise<boolean> {
  try {
    // Get the refresh token from storage
    const refreshToken = getItem<string>(REFRESH_TOKEN_KEY, StorageType.LOCAL);
    
    if (!refreshToken) {
      return false;
    }
    
    // Make a request to the refresh token endpoint
    // Use axios directly to avoid potential circular dependencies with interceptors
    const response = await axios.post(AUTH_ENDPOINTS.REFRESH_TOKEN, {
      refreshToken: refreshToken
    });
    
    if (response.data && response.data.accessToken) {
      // Update tokens with the new ones
      setAuthToken({
        accessToken: response.data.accessToken,
        refreshToken: response.data.refreshToken || refreshToken,
        expiresAt: typeof response.data.expiresAt === 'string' 
          ? new Date(response.data.expiresAt).getTime()
          : response.data.expiresAt || 0
      });
      
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Error refreshing token:', error);
    clearAuthToken();
    return false;
  }
}

/**
 * Standardized error handling for API requests with specific error types and messages
 * @param error AxiosError object
 * @returns Promise rejected with standardized error object
 */
export function handleApiError(error: AxiosError): Promise<never> {
  // Extract error details
  const status = error.response?.status;
  const data = error.response?.data as any;
  const errorMessage = data?.message || error.message || DEFAULT_ERROR_MESSAGE;
  
  // Construct a standardized error object
  const standardError = {
    status: status || 0,
    message: errorMessage,
    code: data?.code || 'UNKNOWN_ERROR',
    details: data?.details || null,
    originalError: process.env.NODE_ENV === 'development' ? error : undefined
  };
  
  // Handle specific error types
  if (error.response) {
    // Server responded with an error status
    switch (status) {
      case 401:
        standardError.code = 'UNAUTHORIZED';
        standardError.message = 'Authentication required. Please log in again.';
        break;
      case 403:
        standardError.code = 'FORBIDDEN';
        standardError.message = 'You do not have permission to perform this action.';
        break;
      case 404:
        standardError.code = 'NOT_FOUND';
        standardError.message = 'The requested resource was not found.';
        break;
      case 429:
        standardError.code = 'RATE_LIMITED';
        standardError.message = 'Too many requests. Please try again later.';
        break;
      default:
        if (status && status >= 500) {
          standardError.code = 'SERVER_ERROR';
          standardError.message = 'An unexpected server error occurred. Please try again later.';
        }
    }
  } else if (error.request) {
    // Request was made but no response received
    standardError.code = 'NETWORK_ERROR';
    standardError.message = 'Network error. Please check your internet connection.';
  } else if (error.code === 'ECONNABORTED') {
    // Request timed out
    standardError.code = 'TIMEOUT';
    standardError.message = 'Request timed out. Please try again later.';
  }
  
  // Log errors in development mode
  if (process.env.NODE_ENV === 'development') {
    console.error('API Error:', standardError);
  }
  
  // Check if the error is retryable and retry attempts are specified
  if (isRetryableError(error) && error.config && RETRY_ATTEMPTS > 0) {
    return retryRequest(error, RETRY_ATTEMPTS);
  }
  
  return Promise.reject(standardError);
}

/**
 * Attempts to retry a failed request with exponential backoff
 * @param error The original error
 * @param retries Number of retry attempts remaining
 * @returns Promise resolving to the API response or rejecting with an error after all retries
 */
async function retryRequest(error: AxiosError, retries: number): Promise<any> {
  // If no more retries or error is not retryable, throw the error
  if (retries <= 0 || !isRetryableError(error) || !error.config) {
    return Promise.reject(error);
  }
  
  // Calculate backoff delay: 2^(RETRY_ATTEMPTS - retries) * 1000ms + random jitter
  const delay = Math.pow(2, RETRY_ATTEMPTS - retries) * 1000 + Math.random() * 1000;
  
  try {
    // Wait for the calculated delay
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // Make a new request with the same config
    return await apiClient.request(error.config);
  } catch (retryError) {
    // If the retry fails, try again with one less retry attempt
    if (axios.isAxiosError(retryError)) {
      return retryRequest(retryError, retries - 1);
    }
    return Promise.reject(retryError);
  }
}

/**
 * Determines if an error should trigger a retry attempt
 * @param error The error to evaluate
 * @returns True if the error is retryable, false otherwise
 */
function isRetryableError(error: AxiosError): boolean {
  // Network errors (no response) are retryable
  if (!error.response) {
    return true;
  }
  
  const status = error.response.status;
  
  // Retry on request timeout, too many requests, or server errors
  return (
    status === 408 || // Request Timeout
    status === 429 || // Too Many Requests
    status === 500 || // Internal Server Error
    status === 502 || // Bad Gateway
    status === 503 || // Service Unavailable
    status === 504    // Gateway Timeout
  );
}

// Default export for the configured axios instance
export default apiClient;