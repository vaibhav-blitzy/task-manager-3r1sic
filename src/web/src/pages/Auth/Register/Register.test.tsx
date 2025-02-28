import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { rest } from 'msw';

import Register from './Register';
import useAuth from '../../../api/hooks/useAuth';
import AuthLayout from '../../../components/templates/AuthLayout/AuthLayout';
import { server } from '../../../__tests__/mocks/server';
import handlers from '../../../__tests__/mocks/handlers';
import store from '../../../store';

// Mock the useAuth hook
jest.mock('../../../api/hooks/useAuth');

/**
 * Utility function to render components with Redux store and router providers for testing
 */
const renderWithProviders = (ui, options = {}) => {
  return render(
    <Provider store={store}>
      <MemoryRouter>
        <Routes>
          <Route path="/" element={ui} />
          <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
          <Route path="/dashboard" element={<div data-testid="dashboard-page">Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </Provider>,
    options
  );
};

describe('Register Component', () => {
  // Mock register function
  const mockRegister = jest.fn();
  
  beforeEach(() => {
    // Reset handlers before each test
    server.resetHandlers();
    
    // Default mock implementation
    (useAuth as jest.Mock).mockReturnValue({
      register: mockRegister,
      loading: false,
      error: null
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders registration form', () => {
    renderWithProviders(<Register />);
    
    // Check that all form elements are present
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
    
    // Check that link to login page is present
    expect(screen.getByText(/Already have an account\?/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Sign in/i })).toBeInTheDocument();
  });

  test('shows validation errors for empty fields', async () => {
    renderWithProviders(<Register />);
    
    // Submit form without filling any fields
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    // Check that validation errors are displayed
    await waitFor(() => {
      expect(screen.getByText(/First name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Last name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Please confirm your password/i)).toBeInTheDocument();
    });
  });

  test('shows error when passwords do not match', async () => {
    renderWithProviders(<Register />);
    
    // Fill form with different passwords
    userEvent.type(screen.getByLabelText(/First Name/i), 'John');
    userEvent.type(screen.getByLabelText(/Last Name/i), 'Doe');
    userEvent.type(screen.getByLabelText(/Email Address/i), 'john.doe@example.com');
    userEvent.type(screen.getByLabelText(/^Password/i), 'Password123!');
    userEvent.type(screen.getByLabelText(/Confirm Password/i), 'DifferentPassword123!');
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    // Check that password mismatch error is displayed
    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  test('shows error for invalid email format', async () => {
    renderWithProviders(<Register />);
    
    // Fill form with invalid email
    userEvent.type(screen.getByLabelText(/First Name/i), 'John');
    userEvent.type(screen.getByLabelText(/Last Name/i), 'Doe');
    userEvent.type(screen.getByLabelText(/Email Address/i), 'invalid-email');
    userEvent.type(screen.getByLabelText(/^Password/i), 'Password123!');
    userEvent.type(screen.getByLabelText(/Confirm Password/i), 'Password123!');
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    // Check that email validation error is displayed
    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument();
    });
  });

  test('calls register function with form data when validation passes', async () => {
    // Configure mock to resolve successfully
    mockRegister.mockResolvedValue({});
    
    renderWithProviders(<Register />);
    
    // Fill form with valid data
    userEvent.type(screen.getByLabelText(/First Name/i), 'John');
    userEvent.type(screen.getByLabelText(/Last Name/i), 'Doe');
    userEvent.type(screen.getByLabelText(/Email Address/i), 'john.doe@example.com');
    userEvent.type(screen.getByLabelText(/^Password/i), 'Password123!');
    userEvent.type(screen.getByLabelText(/Confirm Password/i), 'Password123!');
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    // Check that register function was called with correct data
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@example.com',
        password: 'Password123!',
        confirmPassword: 'Password123!',
      });
    });
  });

  test('shows error message when registration fails', async () => {
    // Mock an error response
    const errorMessage = 'A user with this email already exists';
    mockRegister.mockRejectedValue(new Error(errorMessage));
    
    // Mock useAuth to return an error state
    (useAuth as jest.Mock).mockReturnValue({
      register: mockRegister,
      loading: false,
      error: errorMessage
    });
    
    renderWithProviders(<Register />);
    
    // Fill form with valid data
    userEvent.type(screen.getByLabelText(/First Name/i), 'John');
    userEvent.type(screen.getByLabelText(/Last Name/i), 'Doe');
    userEvent.type(screen.getByLabelText(/Email Address/i), 'existing@example.com');
    userEvent.type(screen.getByLabelText(/^Password/i), 'Password123!');
    userEvent.type(screen.getByLabelText(/Confirm Password/i), 'Password123!');
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    // Check that the form submission is attempted
    await waitFor(() => expect(mockRegister).toHaveBeenCalled());
    
    // Render again with error state to check error display
    renderWithProviders(<Register />);
    
    // Check that error message is displayed
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('disables form elements during submission', async () => {
    // Mock loading state
    (useAuth as jest.Mock).mockReturnValue({
      register: mockRegister,
      loading: true,
      error: null
    });
    
    renderWithProviders(<Register />);
    
    // Check that form fields and button are disabled
    expect(screen.getByLabelText(/First Name/i)).toBeDisabled();
    expect(screen.getByLabelText(/Last Name/i)).toBeDisabled();
    expect(screen.getByLabelText(/Email Address/i)).toBeDisabled();
    expect(screen.getByLabelText(/^Password/i)).toBeDisabled();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeDisabled();
  });

  test('navigates to login page when clicking the Sign in link', async () => {
    renderWithProviders(<Register />);
    
    // Click the sign in link
    fireEvent.click(screen.getByRole('link', { name: /Sign in/i }));
    
    // Check that the login page is displayed
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });
});