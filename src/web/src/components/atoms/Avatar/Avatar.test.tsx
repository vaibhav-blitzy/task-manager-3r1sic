import React from 'react'; // react ^18.2.0
import { render, screen } from '../../../utils/test-utils';
import Avatar from './Avatar';
import { User } from '../../../types/user';
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { vi } from 'vitest'; // vitest ^0.34.0

describe('Avatar component', () => {
  // Define the main test suite for Avatar component
  // Group related tests logically

  test('renders with user image when profileImageUrl is provided', () => {
    // Tests that the Avatar component renders an image when the user has a profileImageUrl
    // Create a mock user with profileImageUrl
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
      profileImageUrl: 'https://example.com/image.jpg',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with the mock user
    render(<Avatar user={mockUser} />);

    // Assert that an img element is in the document
    const imgElement = screen.getByRole('img');
    expect(imgElement).toBeInTheDocument();

    // Verify that the img src matches the profileImageUrl
    expect(imgElement).toHaveAttribute('src', 'https://example.com/image.jpg');

    // Check that proper alt text is provided
    expect(imgElement).toHaveAttribute('alt', 'John Doe');
  });

  test('renders user initials when no profileImageUrl is provided', () => {
    // Tests that the Avatar displays user initials as fallback when profileImageUrl is missing
    // Create a mock user without profileImageUrl but with firstName and lastName
    const mockUser: User = {
      id: '2',
      email: 'test2@example.com',
      firstName: 'Jane',
      lastName: 'Smith',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with the mock user
    render(<Avatar user={mockUser} />);

    // Assert that the initials are displayed (e.g., 'JD' for 'John Doe')
    expect(screen.getByText('JS')).toBeInTheDocument();

    // Verify that no img element is rendered
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  test('renders with different sizes correctly', () => {
    // Tests that the Avatar applies correct sizing classes for each size option
    // Create a mock user
    const mockUser: User = {
      id: '3',
      email: 'test3@example.com',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with size='sm'
    render(<Avatar user={mockUser} size="sm" />);

    // Verify small size classes are applied
    expect(screen.getByText('TU')).toHaveClass('w-8');
    expect(screen.getByText('TU')).toHaveClass('h-8');
    expect(screen.getByText('TU')).toHaveClass('text-xs');

    // Render Avatar with size='md'
    render(<Avatar user={mockUser} size="md" />);

    // Verify medium size classes are applied
    expect(screen.getByText('TU')).toHaveClass('w-10');
    expect(screen.getByText('TU')).toHaveClass('h-10');
    expect(screen.getByText('TU')).toHaveClass('text-sm');

    // Render Avatar with size='lg'
    render(<Avatar user={mockUser} size="lg" />);

    // Verify large size classes are applied
    expect(screen.getByText('TU')).toHaveClass('w-12');
    expect(screen.getByText('TU')).toHaveClass('h-12');
    expect(screen.getByText('TU')).toHaveClass('text-base');
  });

  test('shows status indicator when showStatus is true', () => {
    // Tests that the Avatar displays a status indicator when showStatus prop is true
    // Create a mock user with status
    const mockUser: User = {
      id: '4',
      email: 'test4@example.com',
      firstName: 'Test',
      lastName: 'User',
      status: 'active',
      roles: [],
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with showStatus={true}
    render(<Avatar user={mockUser} showStatus={true} />);

    // Assert that a status indicator element is visible
    const statusIndicator = screen.getByRole('status');
    expect(statusIndicator).toBeVisible();

    // Verify that the indicator has appropriate classes based on status
    expect(statusIndicator).toHaveClass('bg-green-500');
  });

  test('does not show status indicator when showStatus is false', () => {
    // Tests that the Avatar doesn't display a status indicator when showStatus is false
    // Create a mock user with status
    const mockUser: User = {
      id: '5',
      email: 'test5@example.com',
      firstName: 'Test',
      lastName: 'User',
      status: 'active',
      roles: [],
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with showStatus={false} or default
    render(<Avatar user={mockUser} showStatus={false} />);

    // Assert that no status indicator element is rendered
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  test('falls back to initials when image fails to load', () => {
    // Tests that the Avatar displays initials when the image fails to load
    // Create a mock user with profileImageUrl, firstName, and lastName
    const mockUser: User = {
      id: '6',
      email: 'test6@example.com',
      firstName: 'Test',
      lastName: 'User',
      profileImageUrl: 'https://example.com/broken-image.jpg',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with the mock user
    render(<Avatar user={mockUser} />);

    // Simulate an error event on the image
    const imgElement = screen.getByRole('img');
    fireEvent.error(imgElement);

    // Assert that the initials are now displayed
    expect(screen.getByText('TU')).toBeInTheDocument();

    // Verify that the img element is no longer visible
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  test('applies custom className when provided', () => {
    // Tests that the Avatar correctly merges custom className with default classes
    // Create a mock user
    const mockUser: User = {
      id: '7',
      email: 'test7@example.com',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with className='custom-test-class'
    render(<Avatar user={mockUser} className="custom-test-class" />);

    // Assert that the avatar has both default styling classes and the custom class
    expect(screen.getByText('TU').closest('div')).toHaveClass('custom-test-class');
  });

  test('renders placeholder when user is undefined', () => {
    // Tests that the Avatar renders a placeholder when no user is provided
    // Render Avatar without a user prop
    render(<Avatar />);

    // Assert that a placeholder element is rendered
    expect(screen.getByText('•')).toBeInTheDocument();

    // Verify appropriate visual indication of empty state
    expect(screen.getByText('•').closest('div')).toHaveClass('bg-gray-400');
  });

  test('calls onClick handler when clicked', async () => {
    // Tests that the Avatar component calls the onClick handler when clicked
    // Create a mock function with vi.fn()
    const mockFn = vi.fn();

    // Render Avatar with onClick={mockFn}
    render(<Avatar user={{
      id: '8',
      email: 'test8@example.com',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User} onClick={mockFn} />);

    // Simulate a click on the avatar using userEvent
    await userEvent.click(screen.getByText('TU').closest('div')!);

    // Assert that the mock function was called once
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  test('has proper accessibility attributes', () => {
    // Tests that the Avatar has appropriate ARIA attributes for accessibility
    // Create a mock user
    const mockUser: User = {
      id: '9',
      email: 'test9@example.com',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      status: 'active',
      organizations: [],
      settings: {
        language: 'en',
        theme: 'light',
        notifications: {
          email: true,
          push: false,
          inApp: true,
          digest: {
            enabled: false,
            frequency: 'daily',
          },
        },
        defaultView: 'board',
      },
      security: {
        mfaEnabled: false,
        mfaMethod: 'app',
        lastLogin: new Date().toISOString(),
        lastPasswordChange: new Date().toISOString(),
        emailVerified: true,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    } as User;

    // Render Avatar with the mock user
    render(<Avatar user={mockUser} onClick={() => {}} />);

    // Assert that the avatar has appropriate alt text for image or aria-label for initials
    const avatarDiv = screen.getByText('TU').closest('div');
    expect(avatarDiv).toHaveAttribute('aria-label', 'Test User');

    // Verify that interactive avatars (with onClick) have proper keyboard accessibility
    expect(avatarDiv).toHaveAttribute('role', 'button');
    expect(avatarDiv).toHaveAttribute('tabindex', '0');
  });
});