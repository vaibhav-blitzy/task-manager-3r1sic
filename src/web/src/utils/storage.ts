/**
 * storage.ts
 * 
 * Utility functions for browser storage operations (localStorage and sessionStorage)
 * with type safety and error handling.
 */

import { AUTH_TOKEN_KEY, LOCAL_STORAGE_KEYS } from '../config/constants';

/**
 * Enum for selecting the storage type (localStorage or sessionStorage)
 */
export enum StorageType {
  LOCAL = 'localStorage',
  SESSION = 'sessionStorage'
}

/**
 * Interface for user settings stored in browser storage
 */
export interface UserSettings {
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
  theme: string;
}

// User settings storage key (not defined in constants.ts)
const USER_SETTINGS_KEY = 'tms_user_settings';

/**
 * Checks if a specific storage type is available in the browser
 * 
 * @param storage - The storage type to check
 * @returns True if storage is available, false otherwise
 */
export function isStorageAvailable(storage: StorageType): boolean {
  try {
    const testKey = '__storage_test__';
    const storageObj = getStorage(storage);
    
    if (!storageObj) {
      return false;
    }
    
    storageObj.setItem(testKey, 'test');
    storageObj.removeItem(testKey);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Returns the appropriate Storage object based on the specified type
 * 
 * @param type - The storage type
 * @returns The storage object or null if not available
 */
export function getStorage(type: StorageType): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }
  
  try {
    if (type === StorageType.LOCAL) {
      return window.localStorage;
    } else if (type === StorageType.SESSION) {
      return window.sessionStorage;
    }
  } catch (e) {
    console.error('Storage access error:', e);
  }
  
  return null;
}

/**
 * Retrieves an item from storage by key with type safety
 * 
 * @param key - The storage key
 * @param storage - The storage type
 * @returns The stored value with the specified type or null if not found
 */
export function getItem<T>(key: string, storage: StorageType = StorageType.LOCAL): T | null {
  const storageObj = getStorage(storage);
  
  if (!storageObj) {
    return null;
  }
  
  try {
    const item = storageObj.getItem(key);
    
    if (item === null) {
      return null;
    }
    
    return JSON.parse(item) as T;
  } catch (e) {
    console.error(`Error retrieving item with key ${key}:`, e);
    return null;
  }
}

/**
 * Stores an item in storage with the specified key
 * 
 * @param key - The storage key
 * @param value - The value to store
 * @param storage - The storage type
 * @returns True if the operation succeeded, false otherwise
 */
export function setItem<T>(key: string, value: T, storage: StorageType = StorageType.LOCAL): boolean {
  const storageObj = getStorage(storage);
  
  if (!storageObj) {
    return false;
  }
  
  try {
    const serializedValue = JSON.stringify(value);
    storageObj.setItem(key, serializedValue);
    return true;
  } catch (e) {
    console.error(`Error storing item with key ${key}:`, e);
    return false;
  }
}

/**
 * Removes an item from storage by key
 * 
 * @param key - The storage key
 * @param storage - The storage type
 * @returns True if the operation succeeded, false otherwise
 */
export function removeItem(key: string, storage: StorageType = StorageType.LOCAL): boolean {
  const storageObj = getStorage(storage);
  
  if (!storageObj) {
    return false;
  }
  
  try {
    storageObj.removeItem(key);
    return true;
  } catch (e) {
    console.error(`Error removing item with key ${key}:`, e);
    return false;
  }
}

/**
 * Clears all items from the specified storage type
 * 
 * @param storage - The storage type
 * @returns True if the operation succeeded, false otherwise
 */
export function clearStorage(storage: StorageType = StorageType.LOCAL): boolean {
  const storageObj = getStorage(storage);
  
  if (!storageObj) {
    return false;
  }
  
  try {
    storageObj.clear();
    return true;
  } catch (e) {
    console.error('Error clearing storage:', e);
    return false;
  }
}

/**
 * Convenience method to retrieve the authentication token
 * 
 * @returns The auth token or null if not found
 */
export function getAuthToken(): string | null {
  return getItem<string>(AUTH_TOKEN_KEY, StorageType.LOCAL);
}

/**
 * Convenience method to store the authentication token
 * 
 * @param token - The authentication token
 * @returns True if the operation succeeded, false otherwise
 */
export function setAuthToken(token: string): boolean {
  return setItem<string>(AUTH_TOKEN_KEY, token, StorageType.LOCAL);
}

/**
 * Convenience method to remove the authentication token
 * 
 * @returns True if the operation succeeded, false otherwise
 */
export function removeAuthToken(): boolean {
  return removeItem(AUTH_TOKEN_KEY, StorageType.LOCAL);
}

/**
 * Retrieves user settings from storage
 * 
 * @returns The user settings or null if not found
 */
export function getUserSettings(): UserSettings | null {
  return getItem<UserSettings>(USER_SETTINGS_KEY, StorageType.LOCAL);
}

/**
 * Stores user settings in storage
 * 
 * @param settings - The user settings
 * @returns True if the operation succeeded, false otherwise
 */
export function setUserSettings(settings: UserSettings): boolean {
  return setItem<UserSettings>(USER_SETTINGS_KEY, settings, StorageType.LOCAL);
}

/**
 * Retrieves the user's theme preference from storage
 * 
 * @returns The theme preference or null if not found
 */
export function getThemePreference(): string | null {
  return getItem<string>(LOCAL_STORAGE_KEYS.THEME, StorageType.LOCAL);
}

/**
 * Stores the user's theme preference in storage
 * 
 * @param theme - The theme preference
 * @returns True if the operation succeeded, false otherwise
 */
export function setThemePreference(theme: string): boolean {
  return setItem<string>(LOCAL_STORAGE_KEYS.THEME, theme, StorageType.LOCAL);
}