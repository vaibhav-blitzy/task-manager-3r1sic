import React from 'react'; // react v18.2.x
import {
  render,
  screen,
  waitFor,
  fireEvent,
  within,
  userEvent,
  fillForm,
} from '../../../utils/test-utils';
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.x
import { useProjectMutation } from '../../../api/hooks/useProjects';
import { ProjectStatus } from '../../../types/project';
import { PATHS } from '../../../routes/paths';

// Mock the ProjectCreate component
import ProjectCreate from './ProjectCreate';

// Mock useNavigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

// Mock useProjectMutation
jest.mock('../../../api/hooks/useProjects', () => ({
  useProjectMutation: jest.fn(),
}));

// Define global mocks
const mockNavigate = jest.fn();
const mockCreateProject = jest.fn().mockResolvedValue({ id: 'mock-project-id', name: 'Test Project' });

/**
 * Sets up mocks for navigation and API hooks before each test
 */
const setupMocks = () => {
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
  (useProjectMutation as jest.Mock).mockReturnValue({
    createProject: {
      mutate: mockCreateProject,
      isLoading: false,
      error: null,
    },
  });
};

/**
 * Test suite for ProjectCreate component
 */
describe('ProjectCreate Component', () => {
  beforeEach(() => {
    setupMocks();
  });

  /**
   * Test that renders the project creation form with all fields
   */
  test('renders the project creation form with all fields', () => {
    render(<ProjectCreate />);
    expect(screen.getByText('Create New Project')).toBeInTheDocument();
    expect(screen.getByLabelText('Project Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
    expect(screen.getByLabelText('Tags')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Project' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  /**
   * Test that shows validation errors when submitting empty form
   */
  test('shows validation errors when submitting empty form', async () => {
    render(<ProjectCreate />);
    const submitButton = screen.getByRole('button', { name: 'Create Project' });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText('Project name is required')).toBeInTheDocument();
    });
    expect(mockCreateProject).not.toHaveBeenCalled();
  });

  /**
   * Test that allows entering project information and clears validation errors
   */
  test('allows entering project information and clears validation errors', async () => {
    render(<ProjectCreate />);
    const submitButton = screen.getByRole('button', { name: 'Create Project' });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText('Project name is required')).toBeInTheDocument();
    });
    const nameInput = screen.getByLabelText('Project Name');
    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    await waitFor(() => {
      expect(screen.queryByText('Project name is required')).not.toBeInTheDocument();
    });
  });

  /**
   * Test that submits the form with valid project data
   */
  test('submits the form with valid project data', async () => {
    render(<ProjectCreate />);
    await fillForm({
      'Project Name': 'Test Project',
      'Description': 'Test Description',
      'Category': 'Test Category',
      'Tags': 'tag1, tag2',
    });
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: ProjectStatus.PLANNING } });
    const submitButton = screen.getByRole('button', { name: 'Create Project' });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(mockCreateProject).toHaveBeenCalled();
    });
    expect(mockCreateProject).toHaveBeenCalledWith({
      name: 'Test Project',
      description: 'Test Description',
      status: ProjectStatus.PLANNING,
      category: 'Test Category',
      tags: ['tag1', 'tag2'],
    });
  });

  /**
   * Test that navigates to projects list after successful creation
   */
  test('navigates to projects list after successful creation', async () => {
    render(<ProjectCreate />);
    await fillForm({
      'Project Name': 'Test Project',
      'Description': 'Test Description',
      'Category': 'Test Category',
      'Tags': 'tag1, tag2',
    });
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: ProjectStatus.PLANNING } });
    const submitButton = screen.getByRole('button', { name: 'Create Project' });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(PATHS.PROJECTS);
    });
  });

  /**
   * Test that handles API error on submission
   */
  test('handles API error on submission', async () => {
    (useProjectMutation as jest.Mock).mockReturnValue({
      createProject: {
        mutate: jest.fn().mockRejectedValue(new Error('API error')),
        isLoading: false,
        error: 'API error',
      },
    });
    render(<ProjectCreate />);
    await fillForm({
      'Project Name': 'Test Project',
      'Description': 'Test Description',
      'Category': 'Test Category',
      'Tags': 'tag1, tag2',
    });
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: ProjectStatus.PLANNING } });
    const submitButton = screen.getByRole('button', { name: 'Create Project' });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText('API error')).toBeInTheDocument();
    });
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  /**
   * Test that navigates back to projects list when cancel is clicked
   */
  test('navigates back to projects list when cancel is clicked', () => {
    render(<ProjectCreate />);
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelButton);
    expect(mockNavigate).toHaveBeenCalledWith(PATHS.PROJECTS);
  });
});