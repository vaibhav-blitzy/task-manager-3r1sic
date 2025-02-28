import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

import { 
  AuthState, 
  User, 
  LoginCredentials, 
  RegistrationData, 
  AuthResponse,
  AuthTokens 
} from '../../types/auth';

import { 
  login as loginService, 
  register as registerService, 
  logout as logoutService, 
  refreshToken as refreshTokenService,
  checkAuthStatus as checkAuthStatusService
} from '../../api/services/authService';

import { 
  getAuthToken, 
  setAuthToken, 
  removeAuthToken 
} from '../../utils/storage';

/**
 * Initial authentication state
 */
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  tokens: null,
  loading: false,
  error: null,
  mfaRequired: false
};

/**
 * Async thunk for user login
 */
export const login = createAsyncThunk<AuthResponse, LoginCredentials>(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await loginService(credentials);
      
      // If MFA is not required, tokens already stored in service layer
      
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to login. Please try again.');
    }
  }
);

/**
 * Async thunk for user registration
 */
export const register = createAsyncThunk<AuthResponse, RegistrationData>(
  'auth/register',
  async (data, { rejectWithValue }) => {
    try {
      const response = await registerService(data);
      
      // Tokens already stored in service layer
      
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Registration failed. Please try again.');
    }
  }
);

/**
 * Async thunk for user logout
 */
export const logout = createAsyncThunk<void, void>(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await logoutService();
      
      // Remove tokens in all cases to ensure client-side logout
      removeAuthToken();
      
    } catch (error: any) {
      // Still remove token even if the API call fails
      removeAuthToken();
      
      return rejectWithValue(error.message || 'Failed to logout properly.');
    }
  }
);

/**
 * Async thunk for refreshing the auth token
 */
export const refreshToken = createAsyncThunk<AuthTokens, string>(
  'auth/refreshToken',
  async (refreshToken, { rejectWithValue }) => {
    try {
      const tokens = await refreshTokenService(refreshToken);
      
      // Store the new tokens
      setAuthToken(tokens.accessToken);
      
      return tokens;
    } catch (error: any) {
      // If token refresh fails, log the user out
      removeAuthToken();
      
      return rejectWithValue(error.message || 'Session expired. Please log in again.');
    }
  }
);

/**
 * Async thunk to check if the user is authenticated (on app startup)
 */
export const checkAuthState = createAsyncThunk<User | null, void>(
  'auth/checkAuthState',
  async (_, { rejectWithValue }) => {
    try {
      // Check if we have a token
      const token = getAuthToken();
      
      if (!token) {
        return null;
      }
      
      // Verify if the token is valid by checking auth status
      const response = await checkAuthStatusService();
      
      return response.user;
    } catch (error: any) {
      // If auth check fails, clear tokens
      removeAuthToken();
      
      return rejectWithValue(error.message || 'Authentication verification failed.');
    }
  }
);

/**
 * Auth slice containing reducers and actions
 */
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /**
     * Manually set authentication credentials
     */
    setCredentials: (state, action: PayloadAction<{ user: User; tokens: AuthTokens }>) => {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.tokens = action.payload.tokens;
      state.error = null;
      state.loading = false;
    },
    
    /**
     * Clear authentication state
     */
    clearCredentials: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.tokens = null;
      state.mfaRequired = false;
      state.loading = false;
    },
    
    /**
     * Clear authentication error
     */
    clearAuthError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    // Login thunk reducers
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        if (action.payload.mfaRequired) {
          // MFA required, don't authenticate yet but save the state
          state.mfaRequired = true;
          state.loading = false;
        } else {
          // Login successful, set the auth state
          state.isAuthenticated = true;
          state.user = action.payload.user;
          state.tokens = action.payload.tokens;
          state.mfaRequired = false;
        }
        state.loading = false;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
    
    // Register thunk reducers
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.loading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
    
    // Logout thunk reducers
      .addCase(logout.pending, (state) => {
        state.loading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
        state.tokens = null;
        state.loading = false;
        state.error = null;
        state.mfaRequired = false;
      })
      .addCase(logout.rejected, (state, action) => {
        // Still clear auth state even if API call fails
        state.isAuthenticated = false;
        state.user = null;
        state.tokens = null;
        state.loading = false;
        state.error = action.payload as string;
        state.mfaRequired = false;
      })
    
    // Refresh token thunk reducers
      .addCase(refreshToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.tokens = action.payload;
        state.loading = false;
        state.error = null;
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.user = null;
        state.tokens = null;
        state.loading = false;
        state.error = action.payload as string;
      })
    
    // Check auth state thunk reducers
      .addCase(checkAuthState.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(checkAuthState.fulfilled, (state, action) => {
        if (action.payload) {
          state.isAuthenticated = true;
          state.user = action.payload;
          // Note: tokens are already in localStorage, handled by the auth service
        } else {
          state.isAuthenticated = false;
          state.user = null;
          state.tokens = null;
        }
        state.loading = false;
        state.error = null;
      })
      .addCase(checkAuthState.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.user = null;
        state.tokens = null;
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

// Export actions
export const { setCredentials, clearCredentials, clearAuthError } = authSlice.actions;

// Export the reducer
export default authSlice.reducer;