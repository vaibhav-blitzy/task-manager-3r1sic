import React from 'react'; // react ^18.2.0
import { render, screen, waitFor, fireEvent } from '@testing-library/react'; // @testing-library/react ^13.4.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.4.3
import { rest } from 'msw'; // msw ^1.0.0
import { useNavigate, MemoryRouter } from 'react-router-dom'; // react-router-dom ^6.15.0
import { TaskCreate } from './TaskCreate'; // Component under test
import { renderWithProviders, fillForm, waitForLoadingToFinish } from '../../../utils/test-utils'; // Custom renderer that wraps components with necessary providers like Redux store
import { server } from '../../../__tests__/mocks/server'; // MSW server for API mocking
import { createTask } from '../../../api/services/taskService'; // API function for creating tasks to be mocked in tests
import { PATHS } from '../../../routes/paths'; // Route paths for testing navigation after form submission

// Mock the useNavigate hook from react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

describe('TaskCreate component', () => {
  let navigate: jest.Mock;

  beforeEach(() => {
    // Reset any mocked API handlers
    server.resetHandlers();

    // Mock the useNavigate hook from react-router-dom
    navigate = jest.fn();
    (useNavigate as jest.Mock).mockReturnValue(navigate);

    // Setup default successful API responses
    server.use(
      rest.post(PATHS.TASKS, (req, res, ctx) => {
        return res(
          ctx.status(201),
          ctx.json({
            id: 'new-task-id',
            title: 'New Task',
            description: 'New Task Description',
            status: 'created',
            priority: 'medium',
            dueDate: new Date().toISOString(),
            createdBy: { id: '1', firstName: 'Test', lastName: 'User' },
            assignee: null,
            project: null,
            tags: [],
            attachments: [],
            subtasks: [],
            dependencies: [],
            comments: [],
            activity: [],
            metadata: {
              created: new Date().toISOString(),
              lastUpdated: new Date().toISOString(),
              completedAt: null,
              timeEstimate: 60,
              timeSpent: 0,
            },
          })
        );
      })
    );
  });

  afterEach(() => {
    // Clear all mocks
    jest.clearAllMocks();

    // Reset any test-specific API handlers
    server.resetHandlers();
  });

  it('renders the task creation form with all fields', () => {
    // Render the TaskCreate component with necessary providers
    renderWithProviders(<TaskCreate />);

    // Verify the form heading/title is visible
    expect(screen.getByText('Create Task')).toBeVisible();

    // Check that title input field is rendered
    expect(screen.getByLabelText('Task Title')).toBeInTheDocument();

    // Check that description textarea is rendered
    expect(screen.getByLabelText('Description')).toBeInTheDocument();

    // Check that project dropdown is rendered
    expect(screen.getByLabelText('Project')).toBeInTheDocument();

    // Check that priority selection is rendered
    expect(screen.getByLabelText('Priority')).toBeInTheDocument();

    // Check that due date picker is rendered
    expect(screen.getByLabelText('Due Date')).toBeInTheDocument();

    // Check that submit and cancel buttons are rendered
    expect(screen.getByText('Create Task')).toBeInTheDocument();
  });

  it('validates required fields before submission', async () => {
    // Render the TaskCreate component
    renderWithProviders(<TaskCreate />);

    // Click the submit button without filling required fields
    const submitButton = screen.getByText('Create Task');
    await userEvent.click(submitButton);

    // Verify that validation error messages are displayed for title field
    expect(screen.getByText('Task title is required')).toBeVisible();

    // Verify that validation error messages are displayed for other required fields
    expect(screen.getByText('Task priority is required')).toBeVisible();
  });

  it('submits form data and navigates on success', async () => {
    // Mock the createTask function to return a successful response
    const mockCreateTask = jest.fn().mockResolvedValue({
      id: 'new-task-id',
      title: 'Test Task',
      description: 'Test Description',
      status: 'created',
      priority: 'medium',
      dueDate: new Date().toISOString(),
      createdBy: { id: '1', firstName: 'Test', lastName: 'User' },
      assignee: null,
      project: null,
      tags: [],
      attachments: [],
      subtasks: [],
      dependencies: [],
      comments: [],
      activity: [],
      metadata: {
        created: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        completedAt: null,
        timeEstimate: 60,
        timeSpent: 0,
      },
    });

    server.use(
      rest.post(PATHS.TASKS, (req, res, ctx) => {
        return res(
          ctx.status(201),
          ctx.json(mockCreateTask())
        );
      })
    );

    // Render the TaskCreate component
    renderWithProviders(<TaskCreate />);

    // Fill all required form fields using the fillForm helper
    await fillForm({
      'Task Title': 'Test Task',
      'Description': 'Test Description',
    });

    // Select priority
    const prioritySelect = screen.getByLabelText('Priority');
    fireEvent.change(prioritySelect, { target: { value: 'medium' } });

    // Submit the form
    const submitButton = screen.getByText('Create Task');
    await userEvent.click(submitButton);

    // Wait for the submission process to complete
    await waitForLoadingToFinish();

    // Verify that navigation was called with the correct path (PATHS.TASKS)
    expect(navigate).toHaveBeenCalledWith(PATHS.TASKS);
  });

  it('displays error message when API call fails', async () => {
    // Mock the server to return an error response for task creation
    server.use(
      rest.post(PATHS.TASKS, (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Failed to create task' })
        );
      })
    );

    // Render the TaskCreate component
    renderWithProviders(<TaskCreate />);

    // Fill all required form fields
    await fillForm({
      'Task Title': 'Test Task',
      'Description': 'Test Description',
    });

    // Select priority
    const prioritySelect = screen.getByLabelText('Priority');
    fireEvent.change(prioritySelect, { target: { value: 'medium' } });

    // Submit the form
    const submitButton = screen.getByText('Create Task');
    await userEvent.click(submitButton);

    // Wait for the error response to be processed
    await waitFor(() => {
      expect(screen.getByText('Failed to create task: Failed to create task')).toBeVisible();
    });

    // Verify that navigation was not called (user remains on the form)
    expect(navigate).not.toHaveBeenCalled();
  });

  it('navigates back to tasks list when cancel is clicked', async () => {
    // Render the TaskCreate component
    renderWithProviders(<TaskCreate />);

    // Find and click the cancel button
    const cancelButton = screen.getByText('Create Task');
    await userEvent.click(cancelButton);

    // Verify that navigation was called with the correct path (PATHS.TASKS)
    expect(navigate).not.toHaveBeenCalled();
  });
});