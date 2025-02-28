import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { rest } from 'msw';

import Login from './Login';
import useAuth from '../../../api/hooks/useAuth';
import AuthLayout from '../../../components/templates/AuthLayout/AuthLayout';
import { server } from '../../../__tests__/mocks/server';
import { handlers } from '../../../__tests__/mocks/handlers';
import { PATHS } from '../../../routes/paths';

// Mock the useAuth hook
jest.mock('../../../api/hooks/useAuth');

// Mock the router hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

// Utility function to render Login with necessary providers
const renderWithProviders = (ui, options = {}) => {
  return render(
    <MemoryRouter>
      {ui}
    </MemoryRouter>,
    options
  );
};

describe('Login component', () => {
  // Mock navigate function
  const mockNavigate = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    server.resetHandlers();
    
    // Mock navigate function
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    
    // Default useAuth mock implementation
    useAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
      error: null,
      mfaRequired: false,
      login: jest.fn(),
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });
  
  test('renders login form with email and password fields', () => {
    renderWithProviders(<Login />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
    expect(screen.getByText(/sign up/i)).toBeInTheDocument();
  });
  
  test('shows validation errors when form is submitted with empty fields', async () => {
    renderWithProviders(<Login />);
    
    // Submit the form without filling any fields
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Check for validation error messages
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });
  
  test('shows validation error for invalid email format', async () => {
    renderWithProviders(<Login />);
    
    // Fill in invalid email and valid password
    userEvent.type(screen.getByLabelText(/email/i), 'invalid-email');
    userEvent.type(screen.getByLabelText(/password/i), 'Password123!');
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Check for validation error message
    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });
  });
  
  test('successfully logs in with valid credentials', async () => {
    // Mock successful login
    const mockLogin = jest.fn().mockResolvedValue({});
    useAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
      error: null,
      mfaRequired: false,
      login: mockLogin,
    });
    
    renderWithProviders(<Login />);
    
    // Fill in valid credentials
    userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'Password123!');
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Check that login function was called with correct credentials
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123!',
        rememberMe: false
      });
    });
  });
  
  test('shows error message on login failure', async () => {
    // Mock error message
    const errorMessage = 'Invalid credentials';
    
    // Mock failed login with error
    const mockLogin = jest.fn().mockRejectedValue(new Error(errorMessage));
    useAuth.mockReturnValue({
      isAuthenticated: false,
      loading: false,
      error: errorMessage,
      mfaRequired: false,
      login: mockLogin,
    });
    
    renderWithProviders(<Login />);
    
    // Fill in credentials
    userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    userEvent.type(screen.getByLabelText(/password/i), 'wrongPassword');
    
    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Wait for login attempt
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
    });
    
    // Check for error message
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
  
  test('navigates to forgot password page when link is clicked', () => {
    renderWithProviders(<Login />);
    
    // Click forgot password link
    fireEvent.click(screen.getByText(/forgot password/i));
    
    // Check navigation
    expect(mockNavigate).toHaveBeenCalledWith(PATHS.FORGOT_PASSWORD);
  });
  
  test('navigates to register page when sign up link is clicked', () => {
    renderWithProviders(<Login />);
    
    // Click sign up link
    fireEvent.click(screen.getByText(/sign up/i));
    
    // Check navigation
    expect(mockNavigate).toHaveBeenCalledWith(PATHS.REGISTER);
  });
});