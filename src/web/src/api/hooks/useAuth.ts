import { useCallback, useEffect, useState } from 'react'; // react ^18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.x

// Import Redux hooks for typed dispatch and state selection
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { 
  loginAsync, 
  registerAsync, 
  logoutAsync, 
  refreshTokenAsync, 
  verifyMfaAsync, 
  getCurrentUserAsync, 
  selectAuth, 
  selectIsAuthenticated, 
  selectUser, 
  selectAuthLoading, 
  selectMfaRequired 
} from '../../store/slices/authSlice';

// Import authentication-related types
import { LoginCredentials, RegistrationData, AuthResponse, MfaVerificationData } from '../../types/auth';
import { User } from '../../types/user';

// Import storage utilities for token management
import { isAuthenticated, getAuthTokens } from '../../services/storageService';

/**
 * Custom hook that provides authentication functionality throughout the application.
 * Encapsulates authentication-related state management and API interactions,
 * offering a clean interface for login, registration, logout, and other auth operations.
 * 
 * @returns Authentication methods and state for use in components
 */
const useAuth = () => {
  const dispatch = useAppDispatch();
  
  // Select auth state from Redux store
  const { user, error } = useAppSelector(selectAuth);
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const loading = useAppSelector(selectAuthLoading);
  const mfaRequired = useAppSelector(selectMfaRequired);
  
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);

  /**
   * Handles user login with provided credentials
   * 
   * @param credentials - User login credentials (email, password, rememberMe)
   * @returns Promise resolving to the authentication response
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<AuthResponse> => {
    setFormError(null);
    try {
      const resultAction = await dispatch(loginAsync(credentials));
      // Handle successful login
      if (loginAsync.fulfilled.match(resultAction)) {
        const response = resultAction.payload;
        // Only navigate to dashboard if MFA is not required
        if (!response.mfaRequired) {
          navigate('/dashboard');
        }
        return response;
      } else {
        // Handle login failure
        const errorMsg = resultAction.error.message || 'Login failed. Please try again.';
        setFormError(errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred during login.';
      setFormError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [dispatch, navigate]);

  /**
   * Handles user registration with provided data
   * 
   * @param data - User registration data
   * @returns Promise resolving to the authentication response
   */
  const register = useCallback(async (data: RegistrationData): Promise<AuthResponse> => {
    setFormError(null);
    try {
      // Client-side validation
      if (data.password !== data.confirmPassword) {
        const errorMsg = 'Passwords do not match';
        setFormError(errorMsg);
        throw new Error(errorMsg);
      }
      
      const resultAction = await dispatch(registerAsync(data));
      // Handle successful registration
      if (registerAsync.fulfilled.match(resultAction)) {
        navigate('/dashboard');
        return resultAction.payload;
      } else {
        // Handle registration failure
        const errorMsg = resultAction.error.message || 'Registration failed. Please try again.';
        setFormError(errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred during registration.';
      setFormError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [dispatch, navigate]);

  /**
   * Logs the current user out
   */
  const logout = useCallback(async (): Promise<void> => {
    try {
      await dispatch(logoutAsync());
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
      // Force client-side logout even if API call fails
      navigate('/login');
    }
  }, [dispatch, navigate]);

  /**
   * Verifies MFA code during authentication
   * 
   * @param mfaData - MFA verification data (code and method)
   * @returns Promise resolving to the authentication response
   */
  const verifyMfa = useCallback(async (mfaData: MfaVerificationData): Promise<AuthResponse> => {
    setFormError(null);
    try {
      const resultAction = await dispatch(verifyMfaAsync(mfaData));
      // Handle successful MFA verification
      if (verifyMfaAsync.fulfilled.match(resultAction)) {
        navigate('/dashboard');
        return resultAction.payload;
      } else {
        // Handle MFA verification failure
        const errorMsg = resultAction.error.message || 'MFA verification failed. Please try again.';
        setFormError(errorMsg);
        throw new Error(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred during MFA verification.';
      setFormError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [dispatch, navigate]);

  /**
   * Manually refreshes the authentication token
   * 
   * @returns Promise resolving to the refreshed token data
   */
  const refreshToken = useCallback(async () => {
    try {
      const tokens = getAuthTokens();
      if (tokens?.refreshToken) {
        const resultAction = await dispatch(refreshTokenAsync(tokens.refreshToken));
        if (refreshTokenAsync.fulfilled.match(resultAction)) {
          return resultAction.payload;
        }
        throw new Error('Token refresh failed');
      }
      throw new Error('No refresh token available');
    } catch (err) {
      console.error('Token refresh error:', err);
      throw err;
    }
  }, [dispatch]);

  /**
   * Checks if the user is authenticated and loads user data if needed
   */
  const checkAuth = useCallback(async (): Promise<void> => {
    if (isAuthenticated() && !user) {
      try {
        await dispatch(getCurrentUserAsync());
      } catch (err) {
        console.error('Authentication check error:', err);
      }
    }
  }, [dispatch, user]);

  /**
   * Clears any authentication errors
   */
  const clearError = useCallback((): void => {
    setFormError(null);
  }, []);

  /**
   * Checks if the current user has a specific role
   * 
   * @param role - Role to check
   * @returns Boolean indicating whether user has the specified role
   */
  const hasRole = useCallback((role: string): boolean => {
    return !!user && user.roles.includes(role);
  }, [user]);

  // Check for existing authentication on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Set up token refresh interval when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Refresh token every 14 minutes (assuming 15-minute token validity)
      const refreshInterval = setInterval(() => {
        refreshToken().catch(err => {
          console.error('Automatic token refresh failed:', err);
          // If token refresh fails, force logout
          logout();
        });
      }, 14 * 60 * 1000); // 14 minutes in milliseconds

      return () => clearInterval(refreshInterval);
    }
  }, [isAuthenticated, refreshToken, logout]);

  return {
    // Auth state
    isAuthenticated,
    user,
    loading,
    error,
    formError,
    mfaRequired,
    
    // Auth methods
    login,
    register,
    logout,
    verifyMfa,
    refreshToken,
    checkAuth,
    clearError,
    hasRole
  };
};

export default useAuth;