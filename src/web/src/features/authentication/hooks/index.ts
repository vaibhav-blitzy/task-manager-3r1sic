/**
 * Authentication Hooks
 * 
 * Provides custom React hooks for authentication-related functionality throughout the application,
 * including authentication state management, password validation, redirection based on auth state,
 * and role-based access control.
 * 
 * @version 1.0.0
 */

import { useCallback, useEffect } from 'react'; // react ^18.2.0
import useAuth from '../../../api/hooks/useAuth';
import { validatePassword, getPasswordStrength } from '../utils/index';

/**
 * Custom hook for password validation and strength checking
 * 
 * Provides real-time password validation with comprehensive strength indication,
 * making it easy for components to display password requirements feedback.
 * 
 * @returns Object containing validation functions and password strength indicators
 */
export const usePasswordValidation = () => {
  /**
   * Memoized function that validates a password and provides feedback
   */
  const validatePasswordWithFeedback = useCallback((password: string) => {
    return validatePassword(password);
  }, []);

  /**
   * Memoized function that calculates password strength as a percentage
   */
  const calculatePasswordStrength = useCallback((password: string) => {
    return getPasswordStrength(password);
  }, []);

  return {
    validatePassword: validatePasswordWithFeedback,
    passwordStrength: (password: string) => calculatePasswordStrength(password),
    isValid: (password: string) => validatePasswordWithFeedback(password).valid,
    validationMessage: (password: string) => validatePasswordWithFeedback(password).message
  };
};

/**
 * Custom hook that handles redirection based on authentication state
 * 
 * Automatically redirects users based on their authentication status:
 * - Redirects authenticated users away from auth pages to the dashboard
 * - Redirects unauthenticated users away from protected pages to login
 * 
 * @param redirectPath Optional custom redirect path for authenticated users
 */
export const useAuthRedirect = (redirectPath?: string) => {
  const { isAuthenticated, user } = useAuth();
  const { navigate } = useAuth(); // Using navigate from useAuth

  useEffect(() => {
    // If on auth pages (login, register) and already authenticated, redirect to dashboard or specified path
    if (isAuthenticated && user && window.location.pathname.match(/\/(login|register|reset-password)/)) {
      navigate(redirectPath || '/dashboard');
    }
    
    // If on protected pages and not authenticated, redirect to login
    if (!isAuthenticated && !window.location.pathname.match(/\/(login|register|reset-password|verify)/)) {
      navigate('/login');
    }
  }, [isAuthenticated, user, navigate, redirectPath]);
};

/**
 * Custom hook that simplifies role-based access control in components
 * 
 * Makes it easy to check if the current user has specific roles,
 * with convenient helper methods for common role checks.
 * 
 * @returns Object containing role checking functions
 */
export const useRoleCheck = () => {
  const { hasRole } = useAuth();
  
  // Memoized function to check if user has one of the specified roles
  const checkRole = useCallback((roles: string | string[]) => {
    if (Array.isArray(roles)) {
      return roles.some(role => hasRole(role));
    }
    return hasRole(roles);
  }, [hasRole]);

  return {
    // Check if user has a specific role or any of the roles in an array
    hasRole: checkRole,
    
    // Convenience methods for common role checks
    isAdmin: () => hasRole('admin'),
    isManager: () => hasRole('manager')
  };
};

// Re-export the main authentication hook for convenience
export { useAuth };