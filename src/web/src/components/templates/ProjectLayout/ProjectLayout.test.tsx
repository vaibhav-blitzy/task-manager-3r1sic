import React from 'react'; // react ^18.2.0
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils';
import { createMockUser, createMockProject, createTestStore } from '../../../utils/test-utils';
import ProjectLayout from '../ProjectLayout';
import { NavigationMenu } from '../../../components/organisms/NavigationMenu/NavigationMenu';
import { BottomNavigation } from '../../../components/mobile/BottomNavigation/BottomNavigation';
import * as reactRouterDom from 'react-router-dom'; // react-router-dom ^6.15.0
import * as useMediaQueryHook from '../../../hooks/useMediaQuery';
import * as useAuthHook from '../../../api/hooks/useAuth';
import * as useProjectHook from '../../../api/hooks/useProjects';

// Mock useParams hook from react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn().mockReturnValue({ projectId: 'test-project-id' }),
  useNavigate: jest.fn(),
  useLocation: jest.fn()
}));

// Mock useMediaQuery hook
jest.mock('../../../hooks/useMediaQuery', () => ({
  useMediaQuery: jest.fn()
}));

// Mock useAuth hook
jest.mock('../../../api/hooks/useAuth', () => ({
  useAuth: jest.fn()
}));

// Mock useProject hook
jest.mock('../../../api/hooks/useProjects', () => ({
  useProject: jest.fn()
}));

// Setup mock implementations before each test
beforeEach(() => {
  (jest.spyOn(reactRouterDom, 'useParams') as jest.SpyInstance).mockReturnValue({ projectId: 'test-project-id' });
  (useMediaQueryHook.useMediaQuery as jest.Mock).mockImplementation(() => false); // Default to desktop viewport
  (useAuthHook.useAuth as jest.Mock).mockReturnValue({
    user: createMockUser(),
    isAuthenticated: true,
  });
  (useProjectHook.useProject as jest.Mock).mockReturnValue({
    project: createMockProject(),
    isLoading: false,
    error: null,
  });
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});

describe('ProjectLayout', () => {
  it('should render the project layout with header and content area', () => {
    const mockProject = createMockProject({ name: 'Test Project' });
    (useProjectHook.useProject as jest.Mock).mockReturnValue({
      project: mockProject,
      isLoading: false,
      error: null,
    });

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByRole('navigation')).toBeVisible();
  });

  it('should render desktop navigation when screen is large', () => {
    (useMediaQueryHook.useMediaQuery as jest.Mock).mockImplementation((query) => query === '(min-width: 641px)');

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByRole('navigation')).toBeVisible();
    expect(screen.queryByTestId('bottom-navigation')).not.toBeInTheDocument();
  });

  it('should render bottom navigation when screen is small', () => {
    (useMediaQueryHook.useMediaQuery as jest.Mock).mockImplementation((query) => query === '(max-width: 640px)');

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByTestId('bottom-navigation')).toBeInTheDocument();
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });

  it('should display loading state when project data is loading', () => {
    (useProjectHook.useProject as jest.Mock).mockReturnValue({
      project: null,
      isLoading: true,
      error: null,
    });

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByText('Test Content')).not.toBeInTheDocument();
  });

  it('should display error message when project data fails to load', () => {
    (useProjectHook.useProject as jest.Mock).mockReturnValue({
      project: null,
      isLoading: false,
      error: new Error('Failed to load project'),
    });

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByText('Error loading project')).toBeInTheDocument();
    expect(screen.getByText('Failed to load project')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Return to Projects' })).toBeInTheDocument();
  });

  it('should toggle sidebar when menu button is clicked', async () => {
    const mockStore = createTestStore({ ui: { theme: 'light', sidebarOpen: false, mobileMenuOpen: false, modal: { isOpen: false, type: null, data: null } } });
    const dispatch = jest.fn();
    (useAppSelector as jest.Mock).mockImplementation((selector) => selector(mockStore.getState()));
    (useAppDispatch as jest.Mock).mockReturnValue(dispatch);

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>, {
      store: mockStore,
    });

    const toggleButton = screen.getByRole('button', { name: 'Expand sidebar' });
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(dispatch).toHaveBeenCalledTimes(1);
    });
  });

  it('should render project members when project has team members', () => {
    const mockProject = createMockProject({
      name: 'Test Project',
      members: [
        { userId: '1', user: createMockUser({ firstName: 'John', lastName: 'Doe' }), role: 'member', joinedAt: new Date().toISOString(), isActive: true },
        { userId: '2', user: createMockUser({ firstName: 'Jane', lastName: 'Smith' }), role: 'admin', joinedAt: new Date().toISOString(), isActive: true },
      ],
    });
    (useProjectHook.useProject as jest.Mock).mockReturnValue({
      project: mockProject,
      isLoading: false,
      error: null,
    });

    render(<ProjectLayout><div>Test Content</div></ProjectLayout>);

    expect(screen.getByAltText('John Doe')).toBeInTheDocument();
    expect(screen.getByAltText('Jane Smith')).toBeInTheDocument();
  });

  it('should render back button when backLink prop is provided', () => {
    const navigate = jest.fn();
    (reactRouterDom.useNavigate as jest.Mock).mockReturnValue(navigate);

    render(<ProjectLayout backLink="/tasks"><div>Test Content</div></ProjectLayout>);

    const backButton = screen.getByRole('button', { name: 'Go back' });
    fireEvent.click(backButton);

    expect(navigate).toHaveBeenCalledWith('/tasks');
  });

  it('should render custom title when title prop is provided', () => {
    render(<ProjectLayout title="Custom Title"><div>Test Content</div></ProjectLayout>);

    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('should render action buttons when actions prop is provided', () => {
    const actionButton = <button>Action</button>;

    render(<ProjectLayout actions={actionButton}><div>Test Content</div></ProjectLayout>);

    expect(screen.getByText('Action')).toBeInTheDocument();
  });
});