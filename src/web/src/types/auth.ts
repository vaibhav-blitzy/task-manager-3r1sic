/**
 * TypeScript type definitions for authentication-related entities, including
 * credentials, tokens, responses, and state management interfaces used throughout
 * the authentication flow.
 * 
 * @version 1.0.0
 */

import { User } from './user';

/**
 * Enumeration of user roles in the system
 */
export enum Role {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user'
}

/**
 * Enumeration of MFA verification methods
 */
export enum MfaType {
  APP = 'app',
  SMS = 'sms',
  EMAIL = 'email'
}

/**
 * Interface for login request data
 */
export interface LoginCredentials {
  /**
   * User's email address
   */
  email: string;
  
  /**
   * User's password
   */
  password: string;
  
  /**
   * Whether to persist login session
   */
  rememberMe: boolean;
}

/**
 * Interface for user registration data
 */
export interface RegistrationData {
  /**
   * User's email address
   */
  email: string;
  
  /**
   * User's chosen password
   */
  password: string;
  
  /**
   * Password confirmation to prevent typos
   */
  confirmPassword: string;
  
  /**
   * User's first name
   */
  firstName: string;
  
  /**
   * User's last name
   */
  lastName: string;
}

/**
 * Interface for authentication tokens
 */
export interface AuthTokens {
  /**
   * JWT access token for API authorization
   */
  accessToken: string;
  
  /**
   * Refresh token to obtain new access tokens
   */
  refreshToken: string;
  
  /**
   * Timestamp when the access token expires
   */
  expiresAt: number;
}

/**
 * Interface for API authentication response
 */
export interface AuthResponse {
  /**
   * User profile information
   */
  user: User;
  
  /**
   * Authentication tokens
   */
  tokens: AuthTokens;
  
  /**
   * Whether MFA verification is required
   */
  mfaRequired: boolean;
}

/**
 * Interface for MFA verification request data
 */
export interface MfaVerificationData {
  /**
   * Verification code provided by the user
   */
  code: string;
  
  /**
   * MFA method used for verification
   */
  method: MfaType;
}

/**
 * Interface for authentication state in the application
 */
export interface AuthState {
  /**
   * Whether the user is authenticated
   */
  isAuthenticated: boolean;
  
  /**
   * Current user information or null if not authenticated
   */
  user: User | null;
  
  /**
   * Authentication tokens or null if not authenticated
   */
  tokens: AuthTokens | null;
  
  /**
   * Whether authentication is in progress
   */
  loading: boolean;
  
  /**
   * Error message if authentication failed
   */
  error: string | null;
  
  /**
   * Whether MFA verification is required
   */
  mfaRequired: boolean;
}

/**
 * Interface for password reset request data
 */
export interface PasswordResetRequest {
  /**
   * Email address for which to reset password
   */
  email: string;
}

/**
 * Interface for password reset confirmation data
 */
export interface PasswordResetConfirm {
  /**
   * Reset token received via email
   */
  token: string;
  
  /**
   * New password chosen by the user
   */
  newPassword: string;
  
  /**
   * Confirmation of the new password to prevent typos
   */
  confirmPassword: string;
}

/**
 * Interface for refresh token request data
 */
export interface RefreshTokenRequest {
  /**
   * Refresh token used to obtain new access token
   */
  refreshToken: string;
}

/**
 * Type definition for user permissions
 */
export type Permission = {
  /**
   * The type of permission
   */
  type: string;
};