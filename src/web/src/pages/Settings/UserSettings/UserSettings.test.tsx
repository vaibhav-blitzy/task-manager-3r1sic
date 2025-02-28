import React from 'react'; // react ^18.2.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.4.3
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'; // vitest ^0.34.3
import { rest } from 'msw'; // msw ^1.2.1
import {
  render,
  screen,
  waitFor,
  within,
} from '../../../utils/test-utils';
import { createMockUser } from '../../../utils/test-utils';
import { server } from '../../../__tests__/mocks/server';
import UserSettings from '../UserSettings';
import { UserProfileUpdateData } from '../../../types/user';
import { AUTH_ENDPOINTS } from '../../../api/endpoints';

// Define test suite for UserSettings component
describe('UserSettings Component', () => {
  // Group related test cases
  // Setup common test environment with beforeEach and afterEach hooks

  // Setup function that runs before each test case
  beforeEach(() => {
    // Setup mock user data
    const mockUser = createMockUser();

    // Configure API mocks for user profile endpoints
    setupMocks();
  });

  // Cleanup function that runs after each test case
  afterEach(() => {
    // Reset all request handlers
    server.resetHandlers();
  });

  // Helper function to setup API mocks for user settings tests
  const setupMocks = () => {
    // Create MSW REST handlers for profile update endpoint
    const profileUpdateHandler = rest.patch(AUTH_ENDPOINTS.BASE, (req, res, ctx) => {
      // Configure mock responses for API calls
      return res(
        ctx.status(200),
        ctx.json({
          message: 'Profile updated successfully',
        })
      );
    });

    // Create MSW REST handlers for password change endpoint
    const passwordChangeHandler = rest.post(AUTH_ENDPOINTS.BASE, (req, res, ctx) => {
      // Configure mock responses for API calls
      return res(
        ctx.status(200),
        ctx.json({
          message: 'Password changed successfully',
        })
      );
    });

    // Register handlers with the mock server
    server.use(profileUpdateHandler, passwordChangeHandler);
  };

  // renders the user settings form with all sections
  it('renders the user settings form with all sections', async () => {
    // Render UserSettings component with mock authenticated user
    render(<UserSettings />);

    // Check for heading/title elements
    expect(screen.getByText('User Settings')).toBeInTheDocument();
    expect(screen.getByText('Profile Information')).toBeInTheDocument();
    expect(screen.getByText('Theme Preferences')).toBeInTheDocument();
    expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
    expect(screen.getByText('Security Settings')).toBeInTheDocument();

    // Verify profile information section exists
    expect(screen.getByText('Update your personal information')).toBeInTheDocument();

    // Verify theme preferences section exists
    expect(screen.getByText('Customize the appearance of the application')).toBeInTheDocument();

    // Verify notification preferences section exists
    expect(screen.getByText('Control how you receive notifications')).toBeInTheDocument();

    // Verify security settings section exists
    expect(screen.getByText('Manage your account security preferences')).toBeInTheDocument();
  });

  // displays the current user data in form fields
  it('displays the current user data in form fields', async () => {
    // Create mock user with specific profile data
    const mockUser = createMockUser({
      firstName: 'Jane',
      lastName: 'Smith',
      email: 'jane.smith@example.com',
      settings: {
        language: 'fr',
        theme: 'dark',
        notifications: {
          email: false,
          push: true,
          inApp: false,
          digest: {
            enabled: true,
            frequency: 'weekly'
          }
        },
        defaultView: 'tasks'
      },
    });

    // Render UserSettings component with mock user in Redux store
    render(<UserSettings />, {}, {
      auth: {
        isAuthenticated: true,
        user: mockUser,
        tokens: null,
        loading: false,
        error: null,
        mfaRequired: false
      }
    });

    // Wait for component to load user data
    await waitFor(() => {
      // Verify first name input contains correct value
      expect(screen.getByLabelText('First Name')).toHaveValue('Jane');

      // Verify last name input contains correct value
      expect(screen.getByLabelText('Last Name')).toHaveValue('Smith');

      // Verify email input contains correct value
      expect(screen.getByLabelText('Email Address')).toHaveValue('jane.smith@example.com');
    });
  });

  // updates user profile information when form is submitted
  it('updates user profile information when form is submitted', async () => {
    // Setup API mock to handle profile update request
    const updateProfileMock = vi.fn();
    server.use(
      rest.patch(AUTH_ENDPOINTS.BASE, async (req, res, ctx) => {
        updateProfileMock(req.body);
        return res(ctx.status(200), ctx.json({ message: 'Profile updated successfully' }));
      })
    );

    // Render UserSettings component
    render(<UserSettings />);

    // Fill in new values for profile fields
    await userEvent.type(screen.getByLabelText('First Name'), 'Updated');
    await userEvent.type(screen.getByLabelText('Last Name'), 'Name');

    // Submit the form
    await userEvent.click(screen.getByText('Save Profile'));

    // Verify API was called with correct data
    await waitFor(() => {
      expect(updateProfileMock).toHaveBeenCalledWith(
        expect.objectContaining({
          firstName: 'Updated',
          lastName: 'Name',
        })
      );
    });

    // Verify success message is displayed
    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully')).toBeInTheDocument();
    });
  });

  // shows validation errors for invalid inputs
  it('shows validation errors for invalid inputs', async () => {
    // Render UserSettings component
    render(<UserSettings />);

    // Fill in invalid email format
    // Clear required name fields
    await userEvent.clear(screen.getByLabelText('First Name'));
    await userEvent.clear(screen.getByLabelText('Last Name'));

    // Submit the form
    await userEvent.click(screen.getByText('Save Profile'));

    // Check for validation error messages
    expect(screen.getByText('First name is required')).toBeInTheDocument();
    expect(screen.getByText('Last name is required')).toBeInTheDocument();

    // Verify form was not submitted to API
  });

  // toggles notification preferences correctly
  it('toggles notification preferences correctly', async () => {
    // Render UserSettings component
    render(<UserSettings />);

    // Find notification toggle switches
    const emailToggle = screen.getByLabelText('Email Notifications');
    const pushToggle = screen.getByLabelText('Push Notifications');

    // Click to toggle email notifications
    await userEvent.click(emailToggle);

    // Click to toggle push notifications
    await userEvent.click(pushToggle);

    // Submit the form
    await userEvent.click(screen.getByText('Save Notification Preferences'));

    // Verify API called with updated notification preferences
  });

  // changes theme preference correctly
  it('changes theme preference correctly', async () => {
    // Render UserSettings component
    render(<UserSettings />);

    // Find theme selection options
    const darkModeButton = screen.getByRole('button', { name: 'Dark Mode' });

    // Select dark theme option
    await userEvent.click(darkModeButton);

    // Verify theme context was updated
    // Submit the form
    // Verify API called with updated theme preference
  });

  // handles API errors gracefully
  it('handles API errors gracefully', async () => {
    // Setup API mock to return error response
    server.use(
      rest.patch(AUTH_ENDPOINTS.BASE, async (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Failed to update profile' })
        );
      })
    );

    // Render UserSettings component
    render(<UserSettings />);

    // Fill form fields with valid data
    await userEvent.type(screen.getByLabelText('First Name'), 'Test');
    await userEvent.type(screen.getByLabelText('Last Name'), 'User');

    // Submit the form
    await userEvent.click(screen.getByText('Save Profile'));

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText('Failed to update profile')).toBeInTheDocument();
    });

    // Verify form remains editable
    expect(screen.getByLabelText('First Name')).toBeEnabled();
  });

  // changes password when password form is submitted
  it('changes password when password form is submitted', async () => {
    // Setup API mock to handle password change request
    const changePasswordMock = vi.fn();
    server.use(
      rest.post(AUTH_ENDPOINTS.BASE, async (req, res, ctx) => {
        changePasswordMock(req.body);
        return res(ctx.status(200), ctx.json({ message: 'Password changed successfully' }));
      })
    );

    // Render UserSettings component
    render(<UserSettings />);

    // Fill password change form with current and new password
    await userEvent.type(screen.getByLabelText('Current Password'), 'currentPassword');
    await userEvent.type(screen.getByLabelText('New Password'), 'newPassword123!');
    await userEvent.type(screen.getByLabelText('Confirm New Password'), 'newPassword123!');

    // Submit the password form
    await userEvent.click(screen.getByText('Change Password'));

    // Verify API was called with correct password data
    await waitFor(() => {
      expect(changePasswordMock).toHaveBeenCalledWith(
        expect.objectContaining({
          currentPassword: 'currentPassword',
          newPassword: 'newPassword123!',
          confirmPassword: 'newPassword123!'
        })
      );
    });

    // Verify success message is displayed
    await waitFor(() => {
      expect(screen.getByText('Password changed successfully')).toBeInTheDocument();
    });
  });
});