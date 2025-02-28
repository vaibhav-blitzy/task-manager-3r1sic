/**
 * StorageService
 * 
 * Advanced browser storage utilities extending basic localStorage/sessionStorage
 * with features like caching, offline data persistence, and file handling.
 * 
 * This service provides:
 * - Client-side caching with expiration times
 * - File metadata storage
 * - Offline operation tracking
 * - Storage usage estimation
 * 
 * @version 1.0.0
 */

import { getItem, setItem, removeItem, clearStorage, StorageType } from '../utils/storage';
import { FILE_UPLOAD_MAX_SIZE, ALLOWED_FILE_TYPES } from '../config/constants';
import { File } from '../types/file';

// Cache keys to ensure consistent usage
const CACHE_KEYS = {
  TASK_LIST: 'cache_task_list',
  PROJECT_LIST: 'cache_project_list',
  USER_PROFILE: 'cache_user_profile',
  FILE_METADATA: 'cache_file_metadata_',
  OFFLINE_OPERATIONS: 'offline_operations'
};

// Default cache expiration time (15 minutes in milliseconds)
const DEFAULT_CACHE_EXPIRY = 15 * 60 * 1000;

/**
 * Interface representing an item stored in cache with expiration time
 */
interface CachedItem<T> {
  value: T;
  expiry: number;
}

/**
 * Interface representing operations performed while offline that need to be synchronized
 */
export interface OfflineOperation {
  id: string;
  type: string;
  entity: string;
  data: any;
  timestamp: number;
}

/**
 * Retrieves an item from the cache with expiration validation
 * 
 * @param key - The cache key
 * @returns The cached value with the specified type or null if not found or expired
 */
export function getCacheItem<T>(key: string): T | null {
  const cached = getItem<CachedItem<T>>(key, StorageType.LOCAL);
  
  if (!cached) {
    return null;
  }
  
  // Check if the cached item has expired
  if (cached.expiry < Date.now()) {
    // Remove expired item
    removeCacheItem(key);
    return null;
  }
  
  return cached.value;
}

/**
 * Stores an item in the cache with expiration time
 * 
 * @param key - The cache key
 * @param value - The value to cache
 * @param expiryMs - Expiration time in milliseconds (defaults to 15 minutes)
 * @returns True if the operation succeeded, false otherwise
 */
export function setCacheItem<T>(key: string, value: T, expiryMs: number = DEFAULT_CACHE_EXPIRY): boolean {
  const expiryTime = Date.now() + expiryMs;
  const cacheObj: CachedItem<T> = {
    value,
    expiry: expiryTime
  };
  
  return setItem<CachedItem<T>>(key, cacheObj, StorageType.LOCAL);
}

/**
 * Removes an item from the cache
 * 
 * @param key - The cache key
 * @returns True if the operation succeeded, false otherwise
 */
export function removeCacheItem(key: string): boolean {
  return removeItem(key, StorageType.LOCAL);
}

/**
 * Clears all cached items
 * 
 * @returns True if the operation succeeded, false otherwise
 */
export function clearCache(): boolean {
  // Get all cache keys as an array
  const cacheKeys = Object.values(CACHE_KEYS);
  
  // Remove each cache item
  let success = true;
  for (const key of cacheKeys) {
    if (!removeCacheItem(key)) {
      success = false;
    }
  }
  
  return success;
}

/**
 * Stores file metadata in the cache for efficient retrieval
 * 
 * @param file - The file metadata to store
 * @returns True if the operation succeeded, false otherwise
 */
export function storeFileMetadata(file: File): boolean {
  const key = `${CACHE_KEYS.FILE_METADATA}${file.id}`;
  return setCacheItem<File>(key, file);
}

/**
 * Retrieves file metadata from the cache if available
 * 
 * @param fileId - The ID of the file to retrieve
 * @returns The file metadata or null if not found in cache
 */
export function getFileMetadata(fileId: string): File | null {
  const key = `${CACHE_KEYS.FILE_METADATA}${fileId}`;
  return getCacheItem<File>(key);
}

/**
 * Generic function to cache any data with a specified key and expiration
 * 
 * @param key - The cache key
 * @param data - The data to cache
 * @param expiryMs - Expiration time in milliseconds (defaults to 15 minutes)
 * @returns True if the operation succeeded, false otherwise
 */
export function cacheData<T>(key: string, data: T, expiryMs: number = DEFAULT_CACHE_EXPIRY): boolean {
  return setCacheItem<T>(key, data, expiryMs);
}

/**
 * Generic function to retrieve cached data by key
 * 
 * @param key - The cache key
 * @returns The cached data or null if not found or expired
 */
export function getCachedData<T>(key: string): T | null {
  return getCacheItem<T>(key);
}

/**
 * Stores operations performed while offline for later synchronization
 * 
 * @param operation - The offline operation to store
 * @returns True if the operation succeeded, false otherwise
 */
export function storeOfflineOperation(operation: OfflineOperation): boolean {
  // Get existing offline operations
  const operations = getItem<OfflineOperation[]>(CACHE_KEYS.OFFLINE_OPERATIONS, StorageType.LOCAL) || [];
  
  // Add the new operation
  operations.push({
    ...operation,
    timestamp: Date.now()
  });
  
  // Store updated operations
  return setItem<OfflineOperation[]>(CACHE_KEYS.OFFLINE_OPERATIONS, operations, StorageType.LOCAL);
}

/**
 * Retrieves all operations performed while offline
 * 
 * @returns Array of offline operations or empty array if none found
 */
export function getOfflineOperations(): OfflineOperation[] {
  return getItem<OfflineOperation[]>(CACHE_KEYS.OFFLINE_OPERATIONS, StorageType.LOCAL) || [];
}

/**
 * Clears all stored offline operations after successful synchronization
 * 
 * @returns True if the operation succeeded, false otherwise
 */
export function clearOfflineOperations(): boolean {
  return removeItem(CACHE_KEYS.OFFLINE_OPERATIONS, StorageType.LOCAL);
}

/**
 * Validates a file against size and type restrictions before storage
 * 
 * @param file - The file to validate
 * @returns Validation result with error message if invalid
 */
export function validateFileForStorage(file: File): { valid: boolean; error?: string } {
  // Check file size
  if (file.size > FILE_UPLOAD_MAX_SIZE) {
    return {
      valid: false,
      error: `File size exceeds the maximum allowed size of ${FILE_UPLOAD_MAX_SIZE / (1024 * 1024)}MB`
    };
  }
  
  // Check file type
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'File type is not supported'
    };
  }
  
  return { valid: true };
}

/**
 * Estimates the current usage of browser storage
 * 
 * @returns Promise resolving to storage usage statistics
 */
export async function estimateStorageUsage(): Promise<{ used: number; available: number; percentage: number }> {
  // Try to use the Storage Manager API if available
  if (navigator.storage && navigator.storage.estimate) {
    try {
      const estimate = await navigator.storage.estimate();
      const used = estimate.usage || 0;
      const available = estimate.quota || 0;
      const percentage = available > 0 ? (used / available) * 100 : 0;
      
      return {
        used,
        available,
        percentage
      };
    } catch (error) {
      console.error('Error estimating storage usage:', error);
    }
  }
  
  // Fallback: manual calculation based on localStorage
  try {
    let totalSize = 0;
    const storage = window.localStorage;
    
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (key) {
        const value = storage.getItem(key);
        if (value) {
          totalSize += key.length + value.length;
        }
      }
    }
    
    // Rough estimate of available space (varies by browser)
    // Most browsers have 5-10MB limit for localStorage
    const estimatedAvailable = 5 * 1024 * 1024; // 5MB as conservative estimate
    
    return {
      used: totalSize,
      available: estimatedAvailable,
      percentage: (totalSize / estimatedAvailable) * 100
    };
  } catch (error) {
    console.error('Error calculating storage usage:', error);
    
    // Return default values if calculation fails
    return {
      used: 0,
      available: 5 * 1024 * 1024, // Assuming 5MB
      percentage: 0
    };
  }
}

// Also export the cache keys as an enum for type safety
export enum CacheKeys {
  TASK_LIST = CACHE_KEYS.TASK_LIST,
  PROJECT_LIST = CACHE_KEYS.PROJECT_LIST,
  USER_PROFILE = CACHE_KEYS.USER_PROFILE,
  FILE_METADATA = CACHE_KEYS.FILE_METADATA,
  OFFLINE_OPERATIONS = CACHE_KEYS.OFFLINE_OPERATIONS
}