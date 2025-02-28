/**
 * Authentication utility functions for token management, validation, and auth-related helper functions
 * 
 * This module provides utilities for:
 * - Token storage and retrieval
 * - Authentication status verification
 * - User information extraction from tokens
 * - Role-based permission checks
 * - Password validation and strength assessment
 * 
 * @version 1.0.0
 */

import { getItem, setItem, removeItem } from '../../../services/storageService';
import { User, UserRole, TokenPayload } from '../../../types/auth';
import { CONSTANTS } from '../../../config/constants';
import jwtDecode from 'jwt-decode'; // v3.1.2

/**
 * Retrieves the authentication token from storage
 * 
 * @returns The stored token or null if not found
 */
export function getToken(): string | null {
  return getItem<string>(CONSTANTS.AUTH_TOKEN_KEY);
}

/**
 * Retrieves the refresh token from storage
 * 
 * @returns The stored refresh token or null if not found
 */
export function getRefreshToken(): string | null {
  return getItem<string>(CONSTANTS.REFRESH_TOKEN_KEY);
}

/**
 * Stores the authentication token in storage
 * 
 * @param token - The authentication token to store
 */
export function setToken(token: string): void {
  setItem<string>(CONSTANTS.AUTH_TOKEN_KEY, token);
}

/**
 * Stores the refresh token in storage
 * 
 * @param refreshToken - The refresh token to store
 */
export function setRefreshToken(refreshToken: string): void {
  setItem<string>(CONSTANTS.REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Removes both authentication and refresh tokens from storage
 */
export function removeTokens(): void {
  removeItem(CONSTANTS.AUTH_TOKEN_KEY);
  removeItem(CONSTANTS.REFRESH_TOKEN_KEY);
}

/**
 * Checks if a token is valid (not expired and properly formatted)
 * 
 * @param token - The token to validate
 * @returns True if the token is valid, false otherwise
 */
export function isTokenValid(token: string): boolean {
  if (!token) {
    return false;
  }

  try {
    const decoded = jwtDecode<{ exp: number }>(token);
    
    // Check if token is expired
    const currentTime = Math.floor(Date.now() / 1000);
    if (decoded.exp < currentTime) {
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Error validating token:', error);
    return false;
  }
}

/**
 * Checks if the user is authenticated based on token existence and validity
 * 
 * @returns True if the user is authenticated, false otherwise
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  
  if (!token) {
    return false;
  }
  
  return isTokenValid(token);
}

/**
 * Decodes and returns the JWT token payload
 * 
 * @returns The decoded token payload or null if invalid
 */
export function getTokenPayload(): TokenPayload | null {
  const token = getToken();
  
  if (!token) {
    return null;
  }
  
  try {
    return jwtDecode<TokenPayload>(token);
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
}

/**
 * Extracts user information from the token payload
 * 
 * @returns User object extracted from token or null if invalid
 */
export function getUserFromToken(): User | null {
  const payload = getTokenPayload();
  
  if (!payload) {
    return null;
  }
  
  // Extract and format user information from payload
  const user: User = {
    id: payload.sub,
    email: payload.email,
    firstName: payload.firstName,
    lastName: payload.lastName,
    roles: payload.roles || []
  };
  
  return user;
}

/**
 * Checks if the authenticated user has the specified role
 * 
 * @param role - The role or array of roles to check
 * @returns True if the user has the specified role, false otherwise
 */
export function hasRole(role: UserRole | UserRole[]): boolean {
  const user = getUserFromToken();
  
  if (!user) {
    return false;
  }
  
  // Handle array of roles
  if (Array.isArray(role)) {
    return role.some(r => user.roles.includes(r.toString()));
  }
  
  // Handle single role
  return user.roles.includes(role.toString());
}

/**
 * Creates an Authorization header with the current token
 * 
 * @returns Authorization header object
 */
export function createAuthHeader(): Record<string, string> {
  const token = getToken();
  
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  
  return {};
}

/**
 * Validates password against strength requirements
 * 
 * @param password - The password to validate
 * @returns Validation result with message
 */
export function validatePassword(password: string): { valid: boolean; message: string } {
  // Check password length
  if (password.length < 10) {
    return {
      valid: false,
      message: 'Password must be at least 10 characters long'
    };
  }
  
  // Check for uppercase letter
  if (!/[A-Z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter'
    };
  }
  
  // Check for lowercase letter
  if (!/[a-z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter'
    };
  }
  
  // Check for number
  if (!/[0-9]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one number'
    };
  }
  
  // Check for special character
  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>\/?]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one special character'
    };
  }
  
  return {
    valid: true,
    message: 'Password meets all requirements'
  };
}

/**
 * Calculates password strength score on a scale of 0-100
 * 
 * @param password - The password to evaluate
 * @returns Password strength score (0-100)
 */
export function getPasswordStrength(password: string): number {
  if (!password) {
    return 0;
  }
  
  let score = 0;
  
  // Length contribution (up to 25 points)
  score += Math.min(25, password.length * 2.5);
  
  // Character variety contribution
  if (/[A-Z]/.test(password)) score += 10; // Uppercase
  if (/[a-z]/.test(password)) score += 10; // Lowercase
  if (/[0-9]/.test(password)) score += 10; // Numbers
  if (/[^A-Za-z0-9]/.test(password)) score += 15; // Special characters
  
  // Complexity contribution
  const uniqueChars = new Set(password).size;
  score += Math.min(15, uniqueChars * 2); // Reward for variety of characters
  
  // Pattern detection (penalize common patterns)
  if (/^[A-Za-z]+\d+$/.test(password)) score -= 10; // Simple pattern of letters followed by numbers
  if (/^[A-Za-z]+[^A-Za-z0-9]\d+$/.test(password)) score -= 5; // Letters, 1 special char, numbers
  
  // Sequence detection
  const sequences = ["abcdefghijklmnopqrstuvwxyz", "01234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"];
  for (const seq of sequences) {
    for (let i = 0; i < seq.length - 2; i++) {
      const fragment = seq.substring(i, i + 3);
      if (password.toLowerCase().includes(fragment)) {
        score -= 5;
        break;
      }
    }
  }
  
  // Ensure score is within 0-100 range
  return Math.max(0, Math.min(100, score));
}