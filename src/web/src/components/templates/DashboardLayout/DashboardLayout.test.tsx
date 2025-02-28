import React from 'react'; // react ^18.2.0
import { DashboardLayout } from '../DashboardLayout';
import { render, screen, fireEvent, waitFor } from '../../utils/test-utils';
import { createMockUser } from '../../utils/test-utils';
import { createTestStore } from '../../utils/test-utils';
import { Provider } from 'react-redux'; // Assuming you have a Redux Provider
import { MemoryRouter } from 'react-router-dom'; // Import MemoryRouter
import { ThemeProvider } from '../../../contexts/ThemeContext'; // Import ThemeProvider
import { WebSocketProvider } from '../../../contexts/WebSocketContext'; // Import WebSocketProvider
import { FeatureFlagProvider } from '../../../contexts/FeatureFlagContext'; // Import FeatureFlagProvider
import { useAppSelector, useAppDispatch } from '../../../store/hooks'; // Import Redux hooks
import { selectSidebarOpen, uiActions } from '../../../store/slices/uiSlice'; // Import uiSlice actions
import { useMediaQuery } from '../../../hooks/useMediaQuery'; // Import useMediaQuery hook

jest.mock('../../../hooks/useMediaQuery');

describe('DashboardLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should render the dashboard layout with navigation and content area', () => {
    const mockUser = createMockUser();
    jest.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: mockUser,
      loading: false,
      error: null,
      formError: null,
      mfaRequired: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      verifyMfa: jest.fn(),
      refreshToken: jest.fn(),
      checkAuth: jest.fn(),
      clearError: jest.fn(),
      hasRole: jest.fn(),
    });

    const testContent = <div>Test Content</div>;
    render(<DashboardLayout>{testContent}</DashboardLayout>);

    expect(screen.getByRole('navigation')).toBeVisible();
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByText('Task Management System')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /user menu/i })).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should render desktop navigation when screen is large', () => {
    (useMediaQuery as jest.Mock).mockImplementation((query: string) => {
      if (query === '(max-width: 640px)') return false;
      if (query === '(min-width: 641px) and (max-width: 1024px)') return false;
      return true;
    });

    render(<DashboardLayout><div>Desktop Content</div></DashboardLayout>);

    expect(screen.getByRole('navigation')).toBeVisible();
    expect(screen.queryByRole('navigation', { name: 'bottom' })).not.toBeInTheDocument();
  });

  it('should render bottom navigation when screen is small', () => {
    (useMediaQuery as jest.Mock).mockImplementation((query: string) => query === '(max-width: 640px)');

    render(<DashboardLayout><div>Mobile Content</div></DashboardLayout>);

    expect(screen.getByRole('navigation', { name: 'bottom' })).toBeVisible();
    expect(screen.queryByRole('navigation', { name: 'main' })).not.toBeInTheDocument();
  });

  it('should toggle sidebar when menu button is clicked', async () => {
    const mockStore = createTestStore({
      ui: {
        theme: 'light',
        sidebarOpen: false,
        mobileMenuOpen: false,
        modal: {
          isOpen: false,
          type: null,
          data: null
        }
      }
    });

    const mockDispatch = jest.fn();
    jest.spyOn(mockStore, 'dispatch').mockImplementation(mockDispatch);

    (useAppSelector as jest.Mock).mockImplementation(selector => selector(mockStore.getState()));
    (useAppDispatch as jest.Mock).mockReturnValue(mockDispatch);

    render(
      <Provider store={mockStore}>
        <MemoryRouter>
          <ThemeProvider>
            <WebSocketProvider>
              <FeatureFlagProvider>
                <DashboardLayout><div>Test Content</div></DashboardLayout>
              </FeatureFlagProvider>
            </WebSocketProvider>
          </ThemeProvider>
        </MemoryRouter>
      </Provider>
    );

    const toggleButton = screen.getByRole('button', { name: /expand sidebar/i });
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(mockDispatch).toHaveBeenCalledWith(uiActions.toggleSidebar());
    });
  });

  it('should display user information when authenticated', () => {
    const mockUser = createMockUser({ firstName: 'John', lastName: 'Doe', email: 'john.doe@example.com' });
    jest.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: mockUser,
      loading: false,
      error: null,
      formError: null,
      mfaRequired: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      verifyMfa: jest.fn(),
      refreshToken: jest.fn(),
      checkAuth: jest.fn(),
      clearError: jest.fn(),
      hasRole: jest.fn(),
    });

    render(<DashboardLayout><div>Test Content</div></DashboardLayout>);

    const userDropdownButton = screen.getByRole('button', { name: /user menu/i });
    expect(userDropdownButton).toBeInTheDocument();

    fireEvent.click(userDropdownButton);
  });

  it('should render children in the main content area', () => {
    render(<DashboardLayout><div data-testid="child-content">Test Children Content</div></DashboardLayout>);
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('should render custom title when provided', () => {
    render(<DashboardLayout title="Custom Title"><div>Test Content</div></DashboardLayout>);
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });
});