import React from 'react'; // react ^18.2.0
import { MemoryRouter, useLocation } from 'react-router-dom'; // react-router-dom ^6.0.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.0.0

import BottomNavigation from './BottomNavigation'; // The component under test
import { render, screen, waitFor } from '../../../utils/test-utils'; // Custom testing utilities
import { PATHS } from '../../../routes/paths'; // Route path constants

/**
 * Mocks the window.matchMedia function to simulate mobile viewport
 * @param matches - Boolean indicating if the media query should match
 */
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: matches,
      media: query,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

/**
 * Creates a test component with the BottomNavigation and access to router location
 * @returns A component with BottomNavigation and current location
 */
const mockComponent = () => {
  const TestComponent: React.FC = () => {
    const location = useLocation();

    return (
      <>
        <BottomNavigation
          navItems={[
            { label: 'Home', path: PATHS.DASHBOARD, icon: () => <svg data-testid="home-icon" /> },
            { label: 'Tasks', path: PATHS.TASKS, icon: () => <svg data-testid="tasks-icon" /> },
            { label: 'Profile', path: '/profile', icon: () => <svg data-testid="profile-icon" /> },
            { label: 'Reports', path: PATHS.REPORTS, icon: () => <svg data-testid="reports-icon" /> },
          ]}
        />
        <div data-testid="location-display">{location.pathname}</div>
      </>
    );
  };
  return TestComponent;
};

describe('BottomNavigation component', () => {
  it('should render navigation items correctly on mobile viewport', () => {
    // Mock matchMedia to return true for mobile viewport
    mockMatchMedia(true);

    // Render the BottomNavigation component
    render(
      <MemoryRouter>
        <BottomNavigation
          navItems={[
            { label: 'Home', path: PATHS.DASHBOARD, icon: () => <svg data-testid="home-icon" /> },
            { label: 'Tasks', path: PATHS.TASKS, icon: () => <svg data-testid="tasks-icon" /> },
            { label: 'Profile', path: '/profile', icon: () => <svg data-testid="profile-icon" /> },
            { label: 'Reports', path: PATHS.REPORTS, icon: () => <svg data-testid="reports-icon" /> },
          ]}
        />
      </MemoryRouter>
    );

    // Verify all expected navigation items are present (Home, Tasks, Profile, Reports)
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();

    // Check that each item has the correct icon and label
    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    expect(screen.getByTestId('tasks-icon')).toBeInTheDocument();
    expect(screen.getByTestId('profile-icon')).toBeInTheDocument();
    expect(screen.getByTestId('reports-icon')).toBeInTheDocument();
  });

  it('should not render on non-mobile viewport', () => {
    // Mock matchMedia to return false for mobile viewport
    mockMatchMedia(false);

    // Render the BottomNavigation component
    render(
      <MemoryRouter>
        <BottomNavigation
          navItems={[
            { label: 'Home', path: PATHS.DASHBOARD, icon: () => <svg data-testid="home-icon" /> },
            { label: 'Tasks', path: PATHS.TASKS, icon: () => <svg data-testid="tasks-icon" /> },
            { label: 'Profile', path: '/profile', icon: () => <svg data-testid="profile-icon" /> },
            { label: 'Reports', path: PATHS.REPORTS, icon: () => <svg data-testid="reports-icon" /> },
          ]}
        />
      </MemoryRouter>
    );

    // Verify the component does not render any navigation items
    expect(screen.queryByText('Home')).not.toBeInTheDocument();
    expect(screen.queryByText('Tasks')).not.toBeInTheDocument();
    expect(screen.queryByText('Profile')).not.toBeInTheDocument();
    expect(screen.queryByText('Reports')).not.toBeInTheDocument();
  });

  it('should highlight the active route', () => {
    // Mock matchMedia to return true for mobile viewport
    mockMatchMedia(true);

    // Define a test component to render the BottomNavigation inside MemoryRouter
    const TestComponent = mockComponent();

    // Render the BottomNavigation inside MemoryRouter with initial location
    render(
      <MemoryRouter initialEntries={[PATHS.TASKS]}>
        <TestComponent />
      </MemoryRouter>
    );

    // Verify the navigation item matching the current route has active styling
    const activeLink = screen.getByText('Tasks');
    expect(activeLink).toHaveClass('text-primary-600');
    expect(activeLink).toHaveClass('font-medium');

    // Verify other navigation items don't have active styling
    expect(screen.getByText('Home')).not.toHaveClass('text-primary-600');
    expect(screen.getByText('Profile')).not.toHaveClass('text-primary-600');
    expect(screen.getByText('Reports')).not.toHaveClass('text-primary-600');
  });

  it('should navigate correctly when links are clicked', async () => {
    // Mock matchMedia to return true for mobile viewport
    mockMatchMedia(true);

    // Define a test component to render the BottomNavigation inside MemoryRouter
    const TestComponent = mockComponent();

    // Render the test component inside MemoryRouter
    render(
      <MemoryRouter initialEntries={[PATHS.DASHBOARD]}>
        <TestComponent />
      </MemoryRouter>
    );

    // Click on a navigation link
    const tasksLink = screen.getByText('Tasks');
    tasksLink.click();

    // Verify the location changes to the expected path
    await waitFor(() => {
      expect(screen.getByTestId('location-display')).toHaveTextContent(PATHS.TASKS);
    });
  });
});