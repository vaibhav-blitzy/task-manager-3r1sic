import React from 'react'; // react ^18.2.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.5.0
import AuthLayout from './AuthLayout'; // Import the component being tested
import { render, screen } from '../../../utils/test-utils'; // Import custom testing utilities with the necessary providers
import { ThemeContext } from '../../../contexts/ThemeContext'; // Import theme context for testing theme-related behavior

describe('AuthLayout', () => {
  // Test suite for the AuthLayout component
  it('renders children passed to it', () => {
    // Test case for verifying the component renders with children
    // Render the AuthLayout component with test child content
    render(
      <AuthLayout>
        <div>Test Child Content</div>
      </AuthLayout>
    );

    // Verify the child content is visible in the document
    expect(screen.getByText('Test Child Content')).toBeVisible();
    // Check for the presence of brand elements like logo or name
    expect(screen.getByText('Task Management System')).toBeInTheDocument();
  });

  it('displays the title when provided', () => {
    // Test case for verifying the title prop is displayed
    const titleText = 'Custom Title';

    // Render the AuthLayout component with a specific title prop
    render(<AuthLayout title={titleText}><div>Test Content</div></AuthLayout>);

    // Verify the title text is visible in the document
    expect(screen.getByText(titleText)).toBeVisible();
  });

  it('adjusts layout based on screen size', () => {
    // Test case for verifying responsive layout changes
    // Mock the matchMedia API to simulate different viewport sizes
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(max-width: 640px)',
        media: query,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    // Render the AuthLayout component with the mocked viewport size
    render(<AuthLayout><div>Test Content</div></AuthLayout>);

    // Verify layout is in column mode for mobile screens
    const authLayoutElement = screen.getByText('Test Content').closest('div');
    expect(authLayoutElement).toHaveClass('flex-col');

    // Update mocked viewport to desktop size
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query !== '(max-width: 640px)',
        media: query,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });

    // Re-render the component to apply the new viewport size
    render(<AuthLayout><div>Test Content</div></AuthLayout>);

    // Verify layout is in row mode for desktop screens
    expect(authLayoutElement).toHaveClass('flex-row');
  });
  
  it('applies correct theme styles', () => {
    // Test case for verifying theme application
    // Mock the theme context to provide a specific theme
    const mockTheme = {
      theme: 'dark',
      colors: {
        primary: '#000000',
        secondary: '#111111',
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
          primary: '#000000',
          secondary: '#111111',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#D1D5DB',
          disabled: '#9CA3AF',
        },
      },
      toggleTheme: jest.fn(),
      setTheme: jest.fn(),
    };
  
    jest.spyOn(React, 'useContext').mockReturnValue(mockTheme);
  
    // Render the AuthLayout component with the mocked theme
    render(
      <AuthLayout>
        <div>Test Content</div>
      </AuthLayout>
    );
  
    // Verify theme-specific styles are applied correctly
    const authLayoutElement = screen.getByText('Test Content').closest('div');
    expect(authLayoutElement).toHaveStyle('background-color: #111111');
  });
});