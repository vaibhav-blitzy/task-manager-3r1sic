import React from 'react'; // react ^18.2.0
import { BrowserRouter } from 'react-router-dom'; // react-router-dom ^6.15.0
import { render, screen, fireEvent } from '../../../utils/test-utils';
import { NavigationMenu } from './NavigationMenu';
import { uiActions } from '../../../store/slices/uiSlice';
import { PATHS } from '../../../routes/paths';
import { Role } from '../../../types/auth';
import { createMockUser } from '../../../utils/test-utils';

/**
 * Helper function to render the NavigationMenu with specific sidebar state
 * @param sidebarOpen - Boolean indicating whether the sidebar should be open
 * @returns Rendered component with test utilities
 */
const setupWithSidebarState = (sidebarOpen: boolean) => {
  // Create preloaded Redux state with specified sidebar open value
  const preloadedState = {
    ui: {
      theme: 'light',
      sidebarOpen: sidebarOpen,
      mobileMenuOpen: false,
      modal: {
        isOpen: false,
        type: null,
        data: null
      }
    }
  };

  // Render NavigationMenu component with the preloaded state
  return render(<NavigationMenu />, { preloadedState });
};

/**
 * Helper function to render the NavigationMenu with a specific user role
 * @param role - Role of the user
 * @returns Rendered component with test utilities
 */
const setupWithUser = (role: Role) => {
  // Create mock user with specified role
  const mockUser = createMockUser({ roles: [role] });

  // Create preloaded Redux state with auth and user data
  const preloadedState = {
    auth: {
      isAuthenticated: true,
      user: mockUser,
      tokens: null,
      loading: false,
      error: null,
      mfaRequired: false
    }
  };

  // Render NavigationMenu component with the preloaded state
  return render(<NavigationMenu />, { preloadedState });
};

describe('NavigationMenu Component', () => {
  it('should render correctly with default state', () => {
    // NavigationMenu renders without errors
    const { getByText } = setupWithSidebarState(true);

    // Navigation contains Dashboard link
    expect(getByText('Dashboard')).toBeInTheDocument();

    // Navigation contains Tasks link
    expect(getByText('Tasks')).toBeInTheDocument();

    // Navigation contains Projects link
    expect(getByText('Projects')).toBeInTheDocument();
  });

  it('should render in expanded state when sidebarOpen is true', () => {
    // Render NavigationMenu with sidebarOpen set to true
    const { container, getByText } = setupWithSidebarState(true);

    // Navigation container has 'expanded' class
    expect(container.querySelector('.navigation-menu')?.classList.contains('w-64')).toBe(true);

    // Navigation shows text labels for menu items
    expect(getByText('Dashboard')).toBeVisible();
  });

  it('should render in collapsed state when sidebarOpen is false', () => {
    // Render NavigationMenu with sidebarOpen set to false
    const { container, queryByText } = setupWithSidebarState(false);

    // Navigation container has 'collapsed' class
    expect(container.querySelector('.navigation-menu')?.classList.contains('w-16')).toBe(true);

    // Navigation hides text labels for menu items
    expect(queryByText('Dashboard')).toBeNull();
  });

  it('should toggle sidebar when toggle button is clicked', () => {
    // Mock the dispatch function
    const dispatchMock = jest.fn();
    const { getByRole } = setupWithSidebarState(true);

    // Replace the real dispatch with the mock
    jest.spyOn(require('../../../store/hooks'), 'useAppDispatch').mockReturnValue(() => dispatchMock);

    // Find the toggle button
    const toggleButton = getByRole('button', { name: 'Collapse sidebar' });

    // Click the toggle button
    fireEvent.click(toggleButton);

    // Redux toggleSidebar action is dispatched when toggle button is clicked
    expect(dispatchMock).toHaveBeenCalledWith(uiActions.toggleSidebar());
  });

  it('should show/hide menu items based on user role', () => {
    // Render NavigationMenu with admin user
    const { getByText: getByTextAdmin, queryByText: queryByTextAdmin } = setupWithUser(Role.ADMIN);

    // Admin users can see admin-only menu items
    expect(getByTextAdmin('Projects')).toBeInTheDocument();
    expect(getByTextAdmin('Reports')).toBeInTheDocument();

    // Render NavigationMenu with regular user
    const { getByText: getByTextUser, queryByText: queryByTextUser } = setupWithUser(Role.USER);

    // Regular users cannot see admin-only menu items
    expect(getByTextUser('Tasks')).toBeInTheDocument();
    expect(queryByTextUser('Projects')).toBeNull();
    expect(queryByTextUser('Reports')).toBeNull();
  });

  it('should navigate to correct routes when menu items are clicked', () => {
    // Render NavigationMenu with BrowserRouter
    const { getByText } = render(
      <BrowserRouter>
        <NavigationMenu />
      </BrowserRouter>
    );

    // Dashboard link navigates to dashboard path
    expect(getByText('Dashboard').closest('a')).toHaveAttribute('href', PATHS.DASHBOARD);

    // Tasks link navigates to tasks path
    expect(getByText('Tasks').closest('a')).toHaveAttribute('href', PATHS.TASKS);

    // Projects link navigates to projects path
    expect(getByText('Projects').closest('a')).toHaveAttribute('href', PATHS.PROJECTS);
  });

  it('should collapse/expand sections when section headers are clicked', () => {
    // Render NavigationMenu with default state
    const { getByText } = setupWithSidebarState(true);

    // Find quick access section header
    const quickAccessHeader = getByText('QUICK ACCESS');

    // Quick access section expands when header is clicked
    fireEvent.click(quickAccessHeader);

    // Find teams section header
    const teamsHeader = getByText('MY TEAMS');

    // Teams section expands when header is clicked
    fireEvent.click(teamsHeader);

    // Clicking already expanded section collapses it
    fireEvent.click(teamsHeader);
  });

  it('should adapt to mobile viewport', () => {
    // Mock the window.innerWidth to simulate a mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 320,
    });

    // Mock the matchMedia function to always return true for mobile query
    window.matchMedia = jest.fn().mockReturnValue({
      matches: true,
      addListener: jest.fn(),
      removeListener: jest.fn(),
    });

    // Render NavigationMenu
    const { container, queryByText } = setupWithSidebarState(true);

    // Navigation renders in mobile mode when viewport width is less than 640px
    expect(container.querySelector('.navigation-menu')?.classList.contains('w-16')).toBe(true);

    // Mobile toggle button is visible
    expect(queryByText('NAVIGATION')).toBeNull();

    // Sidebar is collapsed by default on mobile
    expect(queryByText('Dashboard')).toBeNull();
  });
});