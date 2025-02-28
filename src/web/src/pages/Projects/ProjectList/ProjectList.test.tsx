import React from 'react'; // react ^18.2.0
import { render, screen, waitFor, fireEvent, within } from '../../../utils/test-utils';
import { createMockProject } from '../../../utils/test-utils';
import ProjectList from './ProjectList';
import { useProjects } from '../../../api/hooks/useProjects';
import useAuth from '../../../api/hooks/useAuth';
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.x
import jest from 'jest'; // jest ^29.0.0

// Mock the useAuth hook
jest.mock('../../../api/hooks/useAuth');
// Mock the useProjects hook
jest.mock('../../../api/hooks/useProjects');
// Mock the useNavigate hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

// Before each test, reset the mocks
beforeEach(() => {
  // Description: Setup function that runs before each test to reset mocks
  // Steps:
  // 1. Reset all mock implementations
  jest.clearAllMocks();
  // 2. Set up default mock implementations for useAuth and useProjects
  mockUseAuth();
  mockUseProjects();
});

// Helper function to mock the useAuth hook
const mockUseAuth = (customValues = {}) => {
  // Description: Helper function to mock the useAuth hook with custom return values
  // Parameters:
  // 1. customValues: object - Object containing custom return values
  // Returns:
  // void - No return value
  // Steps:
  // 1. Create default mock values for authenticated user
  const defaultValues = {
    isAuthenticated: true,
    user: {
      id: 'test-user-id',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      permissions: [],
    },
    loading: false,
    error: null,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    clearError: jest.fn(),
    hasRole: jest.fn(),
  };
  // 2. Override with any custom values provided
  const mockValues = { ...defaultValues, ...customValues };
  // 3. Set the mock implementation for useAuth
  (useAuth as jest.Mock).mockReturnValue(mockValues);
};

// Helper function to mock the useProjects hook
const mockUseProjects = (customValues = {}) => {
  // Description: Helper function to mock the useProjects hook with custom return values
  // Parameters:
  // 1. customValues: object - Object containing custom return values
  // Returns:
  // void - No return value
  // Steps:
  // 1. Create default mock values for projects data
  const defaultValues = {
    projects: [],
    totalProjects: 0,
    currentPage: 1,
    totalPages: 1,
    pageSize: 10,
    isLoading: false,
    error: null,
    refetch: jest.fn(),
    pagination: {
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      goToPage: jest.fn(),
      changePageSize: jest.fn(),
    },
  };
  // 2. Override with any custom values provided
  const mockValues = { ...defaultValues, ...customValues };
  // 3. Set the mock implementation for useProjects
  (useProjects as jest.Mock).mockReturnValue(mockValues);
};

it('renders loading state when projects are being fetched', () => {
  // Description: renders loading state when projects are being fetched
  // Steps:
  // 1. Mock useProjects to return isLoading: true and empty projects array
  mockUseProjects({ isLoading: true, projects: [] });
  // 2. Render the ProjectList component
  render(<ProjectList />);
  // 3. Verify loading indicator is displayed
  expect(screen.getByText('Loading projects...')).toBeInTheDocument();
});

it('renders empty state when no projects are found', () => {
  // Description: renders empty state when no projects are found
  // Steps:
  // 1. Mock useProjects to return isLoading: false and empty projects array
  mockUseProjects({ isLoading: false, projects: [] });
  // 2. Render the ProjectList component
  render(<ProjectList />);
  // 3. Verify empty state message is displayed
  expect(screen.getByText('No projects found.')).toBeInTheDocument();
  // 4. Verify create project button is present if user has permission
  mockUseAuth({
    user: {
      id: 'test-user-id',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      permissions: [{ type: 'project:create' }],
    },
  });
  render(<ProjectList />);
  expect(screen.getByText('Create New Project')).toBeInTheDocument();
});

it('renders projects in a grid when data is loaded', () => {
  // Description: renders projects in a grid when data is loaded
  // Steps:
  // 1. Create array of mock projects
  const mockProjects = [
    createMockProject({ name: 'Project 1', status: 'active' }),
    createMockProject({ name: 'Project 2', status: 'completed' }),
  ];
  // 2. Mock useProjects to return the mock projects
  mockUseProjects({ isLoading: false, projects: mockProjects });
  // 3. Render the ProjectList component
  render(<ProjectList />);
  // 4. Verify each project is rendered with correct information
  expect(screen.getByText('Project 1')).toBeInTheDocument();
  expect(screen.getByText('Project 2')).toBeInTheDocument();
  // 5. Check for project name, status, and other details in each card
  expect(screen.getByText('Active')).toBeInTheDocument();
  expect(screen.getByText('Completed')).toBeInTheDocument();
});

it('navigates to project detail when a project card is clicked', () => {
  // Description: navigates to project detail when a project card is clicked
  // Steps:
  // 1. Mock useNavigate from react-router
  const mockNavigate = jest.fn();
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
  // 2. Mock useProjects with mock projects
  const mockProjects = [createMockProject({ id: '1', name: 'Project 1' })];
  mockUseProjects({ isLoading: false, projects: mockProjects });
  // 3. Render the ProjectList component
  render(<ProjectList />);
  // 4. Click on a project card
  fireEvent.click(screen.getByText('Project 1'));
  // 5. Verify navigate was called with correct project URL
  expect(mockNavigate).toHaveBeenCalledWith('/projects/1');
});

it('navigates to project creation page when create button is clicked', () => {
  // Description: navigates to project creation page when create button is clicked
  // Steps:
  // 1. Mock useNavigate from react-router
  const mockNavigate = jest.fn();
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
  // 2. Mock useAuth to give create permission
  mockUseAuth({
    user: {
      id: 'test-user-id',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      permissions: [{ type: 'project:create' }],
    },
  });
  // 3. Render the ProjectList component
  render(<ProjectList />);
  // 4. Click on create project button
  fireEvent.click(screen.getByText('Create Project'));
  // 5. Verify navigate was called with project creation URL
  expect(mockNavigate).toHaveBeenCalledWith('/projects/create');
});

it('filters projects when search is used', async () => {
  // Description: filters projects when search is used
  // Steps:
  // 1. Mock useProjects with mock projects
  const mockProjects = [
    createMockProject({ name: 'Project 1', description: 'Description 1' }),
    createMockProject({ name: 'Project 2', description: 'Description 2' }),
  ];
  const mockSearch = jest.fn();
  mockUseProjects({ isLoading: false, projects: mockProjects, refetch: mockSearch });
  // 2. Set up search function mock to track calls
  // 3. Render the ProjectList component
  render(<ProjectList />);
  // 4. Type search term in search input
  const searchInput = screen.getByPlaceholderText('Search projects...');
  fireEvent.change(searchInput, { target: { value: 'Project 1' } });
  await waitFor(() => {
    // 5. Verify useProjects was called with correct search parameter
    expect(mockSearch).toHaveBeenCalled();
  });
});

it('displays error message when project fetching fails', () => {
  // Description: displays error message when project fetching fails
  // Steps:
  // 1. Mock useProjects to return error state
  mockUseProjects({ isLoading: false, error: new Error('Failed to fetch projects') });
  // 2. Render the ProjectList component
  render(<ProjectList />);
  // 3. Verify error message is displayed
  expect(screen.getByText('Error: Failed to fetch projects')).toBeInTheDocument();
});

it("hides create button when user doesn't have permission", () => {
  // Description: hides create button when user doesn't have permission
  // Steps:
  // 1. Mock useAuth to return user without create project permission
  mockUseAuth({
    user: {
      id: 'test-user-id',
      firstName: 'Test',
      lastName: 'User',
      roles: [],
      permissions: [],
    },
  });
  // 2. Render the ProjectList component
  render(<ProjectList />);
  // 3. Verify create project button is not present
  expect(screen.queryByText('Create Project')).not.toBeInTheDocument();
});