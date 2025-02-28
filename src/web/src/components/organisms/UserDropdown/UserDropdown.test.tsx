import React from 'react'; // react ^18.2.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.5.0
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils'; // Custom testing utilities
import { createMockUser } from '../../../utils/test-utils'; // Helper function to create mock user data
import UserDropdown from './UserDropdown'; // The component under test
import useAuth from '../../../api/hooks/useAuth'; // Authentication hook used by the component
import { PATHS } from '../../../routes/paths'; // Route paths used in the component
import { useOutsideClick } from '../../../hooks/useOutsideClick'; // Hook used by the component to detect outside clicks
import { User } from '../../../types/user'; // Type definition for user data

// Mock react-router-dom's useNavigate hook
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(() => mockedNavigate),
}));

// Mock the useTheme hook for theme toggle testing
const mockedToggleTheme = jest.fn();
jest.mock('../../../contexts/ThemeContext', () => ({
  useTheme: jest.fn(() => ({
    theme: 'light',
    colors: {
      primary: '#4F46E5',
      secondary: '#9333EA',
      success: '#22C55E',
      warning: '#F59E0B',
      error: '#EF4444',
      neutral: {
        100: '#F3F4F6',
        200: '#E5E7EB',
        700: '#374151',
        900: '#111827',
      },
      background: {
        primary: '#FFFFFF',
        secondary: '#F9FAFB',
      },
      text: {
        primary: '#111827',
        secondary: '#6B7280',
        disabled: '#9CA3AF',
      },
    },
    toggleTheme: mockedToggleTheme,
    setTheme: jest.fn(),
  })),
}));

// Mock the useAuth hook to control authentication state
const mockLogout = jest.fn();
jest.mock('../../../api/hooks/useAuth', () => ({
  __esModule: true,
  default: jest.fn(),
}));

// Type-safe mock implementation for useAuth
const mockUseAuth = useAuth as jest.Mock;

/**
 * Set up all required mocks for testing the UserDropdown component
 */
const setupMocks = () => {
  // Mock react-router-dom's useNavigate hook
  (useAuth as jest.Mock).mockImplementation(() => ({
    user: createMockUser(),
    logout: mockLogout,
    isAuthenticated: true,
  }));
};

describe('UserDropdown', () => {
  it('renders user information and menu options', () => {
    setupMocks();
    render(<UserDropdown />);

    // Check if the avatar is rendered
    const avatar = screen.getByRole('button', { name: /user avatar/i });
    expect(avatar).toBeInTheDocument();

    // Open the dropdown
    fireEvent.click(avatar);

    // Check if menu items are rendered
    expect(screen.getByText(/my profile/i)).toBeInTheDocument();
    expect(screen.getByText(/settings/i)).toBeInTheDocument();
    expect(screen.getByText(/logout/i)).toBeInTheDocument();
  });

  it('toggles the dropdown menu when the avatar is clicked', async () => {
    setupMocks();
    render(<UserDropdown />);

    // Get the avatar button
    const avatar = screen.getByRole('button', { name: /user avatar/i });

    // Check if the dropdown is initially closed
    expect(screen.queryByText(/my profile/i)).not.toBeInTheDocument();

    // Open the dropdown
    fireEvent.click(avatar);
    await waitFor(() => {
      expect(screen.getByText(/my profile/i)).toBeInTheDocument();
    });

    // Close the dropdown
    fireEvent.click(avatar);
    await waitFor(() => {
      expect(screen.queryByText(/my profile/i)).not.toBeInTheDocument();
    });
  });

  it('navigates to the profile page when "My Profile" is clicked', async () => {
    setupMocks();
    render(<UserDropdown />);

    // Open the dropdown
    const avatar = screen.getByRole('button', { name: /user avatar/i });
    fireEvent.click(avatar);
    await waitFor(() => {
      expect(screen.getByText(/my profile/i)).toBeInTheDocument();
    });

    // Click the "My Profile" link
    fireEvent.click(screen.getByText(/my profile/i));

    // Check if the navigate function was called with the correct path
    expect(mockedNavigate).toHaveBeenCalledWith(PATHS.USER_SETTINGS);
  });

  it('calls the logout function when "Logout" is clicked', async () => {
    setupMocks();
    render(<UserDropdown />);

    // Open the dropdown
    const avatar = screen.getByRole('button', { name: /user avatar/i });
    fireEvent.click(avatar);
    await waitFor(() => {
      expect(screen.getByText(/logout/i)).toBeInTheDocument();
    });

    // Click the "Logout" button
    fireEvent.click(screen.getByText(/logout/i));

    // Check if the logout function was called
    expect(mockLogout).toHaveBeenCalled();

    // Check if the navigate function was called with the correct path
    expect(mockedNavigate).toHaveBeenCalledWith(PATHS.LOGIN);
  });

  it('toggles the theme when "Dark Mode" or "Light Mode" is clicked', async () => {
    setupMocks();
    render(<UserDropdown />);

    // Open the dropdown
    const avatar = screen.getByRole('button', { name: /user avatar/i });
    fireEvent.click(avatar);
    await waitFor(() => {
      expect(screen.getByText(/dark mode/i)).toBeInTheDocument();
    });

    // Click the "Dark Mode" button
    fireEvent.click(screen.getByText(/dark mode/i));

    // Check if the toggleTheme function was called
    expect(mockedToggleTheme).toHaveBeenCalled();
  });
});