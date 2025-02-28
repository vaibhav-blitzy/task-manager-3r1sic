/**
 * Authentication Service
 * 
 * Service responsible for handling all authentication-related API requests including 
 * login, registration, token refresh, and account management. Provides abstraction 
 * layer between the frontend application and the backend authentication APIs.
 * 
 * @version 1.5.x
 */

import { AxiosResponse } from 'axios'; // axios ^1.5.x

import apiClient, { 
  setAuthToken, 
  clearAuthToken, 
  refreshAuthToken 
} from '../client';

import { 
  AUTH_ENDPOINTS,
  USER_ENDPOINTS
} from '../endpoints';

import { 
  LoginCredentials, 
  RegistrationData, 
  AuthResponse, 
  AuthTokens, 
  MfaVerificationData, 
  PasswordResetRequest, 
  PasswordResetConfirm, 
  RefreshTokenRequest 
} from '../../types/auth';

import { User } from '../../types/user';

/**
 * Authenticates a user with their credentials and returns the authentication response
 * 
 * @param credentials - Login credentials (email, password, rememberMe)
 * @returns Authentication response containing user data, tokens, and MFA status
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>(AUTH_ENDPOINTS.LOGIN, credentials);
  
  const { user, tokens, mfaRequired } = response.data;
  
  // If we received tokens and MFA is not required, set the auth token
  if (tokens && !mfaRequired) {
    setAuthToken(tokens);
  }
  
  return response.data;
}

/**
 * Registers a new user with the provided registration data
 * 
 * @param registrationData - User registration information
 * @returns Authentication response containing the newly created user data and tokens
 */
export async function register(registrationData: RegistrationData): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>(AUTH_ENDPOINTS.REGISTER, registrationData);
  
  const { user, tokens } = response.data;
  
  // If we received tokens, set the auth token
  if (tokens) {
    setAuthToken(tokens);
  }
  
  return response.data;
}

/**
 * Logs out the current user by invalidating their session on the server
 * 
 * @returns Promise that resolves when logout is successful
 */
export async function logout(): Promise<void> {
  await apiClient.post(AUTH_ENDPOINTS.LOGOUT);
  
  // Clear auth tokens from client
  clearAuthToken();
}

/**
 * Refreshes the access token using the stored refresh token
 * 
 * @param refreshTokenValue - Optional refresh token, otherwise uses the stored one
 * @returns New authentication tokens
 */
export async function refreshToken(refreshTokenValue?: string): Promise<AuthTokens> {
  const data: RefreshTokenRequest = {
    refreshToken: refreshTokenValue || ''
  };
  
  const response = await apiClient.post<{ accessToken: string; refreshToken: string; expiresAt: number }>(
    AUTH_ENDPOINTS.REFRESH_TOKEN, 
    data
  );
  
  const newTokens: AuthTokens = {
    accessToken: response.data.accessToken,
    refreshToken: response.data.refreshToken,
    expiresAt: response.data.expiresAt
  };
  
  // Update auth token
  setAuthToken(newTokens);
  
  return newTokens;
}

/**
 * Verifies a user's email address with the verification token
 * 
 * @param token - Email verification token
 * @returns Result of email verification
 */
export async function verifyEmail(token: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    AUTH_ENDPOINTS.VERIFY_EMAIL,
    { token }
  );
  
  return response.data;
}

/**
 * Verifies a multi-factor authentication code
 * 
 * @param mfaData - MFA verification data (code and method)
 * @returns Authentication response after successful MFA verification
 */
export async function verifyMfa(mfaData: MfaVerificationData): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>(
    AUTH_ENDPOINTS.VERIFY_MFA,
    mfaData
  );
  
  const { tokens } = response.data;
  
  // Set auth token after successful MFA verification
  setAuthToken(tokens);
  
  return response.data;
}

/**
 * Requests a password reset for the specified email address
 * 
 * @param resetRequest - Password reset request data
 * @returns Result of password reset request
 */
export async function requestPasswordReset(resetRequest: PasswordResetRequest): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    AUTH_ENDPOINTS.REQUEST_PASSWORD_RESET,
    resetRequest
  );
  
  return response.data;
}

/**
 * Confirms a password reset with the provided token and new password
 * 
 * @param resetData - Password reset confirmation data
 * @returns Result of password reset
 */
export async function resetPassword(resetData: PasswordResetConfirm): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    AUTH_ENDPOINTS.RESET_PASSWORD,
    resetData
  );
  
  return response.data;
}

/**
 * Checks the current authentication status and returns user data if authenticated
 * 
 * @returns Current user data if authenticated
 */
export async function checkAuthStatus(): Promise<{ user: User }> {
  const response = await apiClient.get<{ user: User }>(AUTH_ENDPOINTS.STATUS);
  return response.data;
}

/**
 * Updates the current user's profile information
 * 
 * @param profileData - Updated profile information
 * @returns Updated user data
 */
export async function updateProfile(profileData: object): Promise<{ user: User }> {
  const response = await apiClient.patch<{ user: User }>(
    USER_ENDPOINTS.UPDATE_PROFILE,
    profileData
  );
  
  return response.data;
}

/**
 * Changes the current user's password
 * 
 * @param passwordData - Current and new password information
 * @returns Result of password change
 */
export async function changePassword(passwordData: object): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    USER_ENDPOINTS.CHANGE_PASSWORD,
    passwordData
  );
  
  return response.data;
}

export default {
  login,
  register,
  logout,
  refreshToken,
  verifyEmail,
  verifyMfa,
  requestPasswordReset,
  resetPassword,
  checkAuthStatus,
  updateProfile,
  changePassword
};