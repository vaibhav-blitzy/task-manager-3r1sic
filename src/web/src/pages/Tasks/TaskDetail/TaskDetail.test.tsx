import React from 'react'; // react ^18.2.0
import { MemoryRouter, Routes, Route } from 'react-router-dom'; // react-router-dom ^6.8.0
import { render, screen, waitFor, fireEvent, within } from '../../../utils/test-utils'; // testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { rest } from 'msw'; // msw ^1.0.0
import { server } from '../../../__tests__/mocks/server'; // Mock server for intercepting API requests during tests
import { handlers } from '../../../__tests__/mocks/handlers'; // Default API request handlers for the mock server
import TaskDetail from './TaskDetail'; // The component being tested
import { TASK_ENDPOINTS } from '../../../api/endpoints'; // API endpoint constants for tasks
import { Task, TaskStatus, TaskPriority } from '../../../types/task'; // Type definitions for task data and enums
import { PATHS } from '../../../routes/paths'; // Route path constants for setting up test routes

// Reset any request handlers that we may add during the tests,
// so they don't accidentally leak over.
beforeEach(() => server.resetHandlers());

describe('TaskDetail', () => {
  beforeEach(() => {
    // Reset any mocks
    jest.clearAllMocks();

    // Setup default MSW handlers
    server.use(...handlers);

    // Setup mock task response
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            id: '1',
            title: 'Test Task',
            description: 'Test Description',
            status: TaskStatus.CREATED,
            priority: TaskPriority.MEDIUM,
            dueDate: new Date().toISOString(),
          })
        );
      })
    );
  });

  afterEach(() => {
    server.resetHandlers();
  });

  it('renders loading state initially', async () => {
    // Setup delayed response for task API
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), async (req, res, ctx) => {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return res(
          ctx.status(200),
          ctx.json({
            id: '1',
            title: 'Test Task',
            description: 'Test Description',
            status: TaskStatus.CREATED,
            priority: TaskPriority.MEDIUM,
            dueDate: new Date().toISOString(),
          })
        );
      })
    );

    // Render the TaskDetail component in a Memory Router
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Check if loading indicator is displayed
    expect(screen.getByText('Loading task details...')).toBeInTheDocument();

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText('Loading task details...')).not.toBeInTheDocument();
    });

    // Verify task details are eventually shown
    expect(screen.getByText('Test Task')).toBeInTheDocument();
  });

  it('renders task details correctly', async () => {
    // Create mock task with known data
    const mockTask: Task = {
      id: '1',
      title: 'Test Task',
      description: 'Test Description',
      status: TaskStatus.CREATED,
      priority: TaskPriority.MEDIUM,
      dueDate: new Date().toISOString(),
      createdBy: { id: '1', firstName: 'John', lastName: 'Doe' } as any,
      assignee: { id: '2', firstName: 'Jane', lastName: 'Smith' } as any,
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
        timeSpent: 30,
      },
    } as any;

    // Setup API to return mock task
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTask));
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    // Verify all task information is displayed correctly
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
    expect(screen.getByText('Not Started')).toBeInTheDocument();
    expect(screen.getByText('Due Date:')).toBeInTheDocument();

    // Verify assignee information is shown
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();

    // Check if subtasks are displayed
    expect(screen.getByText('No subtasks yet.')).toBeInTheDocument();
  });

  it('handles status change correctly', async () => {
    // Create mock task with initial status
    const mockTask: Task = {
      id: '1',
      title: 'Test Task',
      description: 'Test Description',
      status: TaskStatus.CREATED,
      priority: TaskPriority.MEDIUM,
      dueDate: new Date().toISOString(),
    } as any;

    // Setup API mocks for task fetch and status update
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTask));
      }),
      rest.patch(TASK_ENDPOINTS.UPDATE_STATUS(':id'), (req, res, ctx) => {
        const { status } = req.body as { status: TaskStatus };
        return res(ctx.status(200), ctx.json({ ...mockTask, status }));
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Not Started')).toBeInTheDocument();
    });

    // Find and click status dropdown
    fireEvent.click(screen.getByText('Not Started'));

    // Select new status option
    fireEvent.click(screen.getByText('In Progress'));

    // Verify API was called with correct parameters
    await waitFor(() => {
      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });

    // Verify UI updates to reflect new status
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('handles comment submission correctly', async () => {
    // Setup API mocks for task fetch and comment submission
    server.use(
      rest.post(TASK_ENDPOINTS.COMMENTS(':id'), (req, res, ctx) => {
        const { content } = req.body as { content: string };
        return res(
          ctx.status(201),
          ctx.json({
            id: '2',
            content,
            createdBy: { id: '1', firstName: 'John', lastName: 'Doe' },
            createdAt: new Date().toISOString(),
            updatedAt: null,
          })
        );
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Add a comment...')).toBeInTheDocument();
    });

    // Find comment input field
    const commentInput = screen.getByPlaceholderText('Add a comment...');

    // Type a new comment
    await userEvent.type(commentInput, 'This is a test comment');

    // Submit the comment
    fireEvent.click(screen.getByText('Post Comment'));

    // Verify API was called with correct parameters
    await waitFor(() => {
      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    });

    // Verify new comment appears in the UI
    expect(screen.getByText('This is a test comment')).toBeInTheDocument();
  });

  it('handles subtask toggling correctly', async () => {
    // Create mock task with subtasks
    const mockTask: Task = {
      id: '1',
      title: 'Test Task',
      description: 'Test Description',
      status: TaskStatus.CREATED,
      priority: TaskPriority.MEDIUM,
      dueDate: new Date().toISOString(),
      subtasks: [
        { id: '1', title: 'Subtask 1', completed: false, assigneeId: '1' },
        { id: '2', title: 'Subtask 2', completed: true, assigneeId: '1' },
      ],
    } as any;

    // Setup API mocks for task fetch and update
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTask));
      }),
      rest.put(TASK_ENDPOINTS.UPDATE_TASK(':id'), (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTask));
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Subtasks')).toBeInTheDocument();
    });

    // Find a subtask checkbox
    const subtaskCheckbox = screen.getByLabelText('Subtask 1');

    // Click to toggle its state
    await userEvent.click(subtaskCheckbox);

    // Verify API was called with updated subtask data
    await waitFor(() => {
      expect(subtaskCheckbox).toBeChecked();
    });

    // Verify checkbox state is updated in the UI
    expect(subtaskCheckbox).toBeChecked();
  });

  it('handles edit mode correctly', async () => {
    // Setup API mocks for task fetch and update
    server.use(
      rest.put(TASK_ENDPOINTS.UPDATE_TASK(':id'), (req, res, ctx) => {
        const taskData = req.body as any;
        return res(ctx.status(200), ctx.json({ ...taskData, id: '1' }));
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    // Find and click the edit button
    const editButton = screen.getByText('Edit');
    await userEvent.click(editButton);

    // Verify form inputs are displayed with current values
    const titleInput = screen.getByPlaceholderText('Task title');
    expect(titleInput).toHaveValue('Test Task');

    const descriptionInput = screen.getByLabelText('Description');
    expect(descriptionInput).toHaveValue('Test Description');

    // Change task title and description
    await userEvent.type(titleInput, ' Updated');
    await userEvent.type(descriptionInput, ' Updated');

    // Click save button
    const saveButton = screen.getByText('Save');
    await userEvent.click(saveButton);

    // Verify API was called with updated task data
    await waitFor(() => {
      expect(screen.getByText('Test Task Updated')).toBeInTheDocument();
    });

    // Verify UI updates with new task information
    expect(screen.getByText('Test Task Updated')).toBeInTheDocument();
  });

  it('displays error state when task fetch fails', async () => {
    // Setup API mock to return an error
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'ServerError', message: 'Failed to fetch task' })
        );
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Error: Failed to fetch task')).toBeInTheDocument();
    });

    // Verify error message is displayed
    expect(screen.getByText('Error: Failed to fetch task')).toBeInTheDocument();

    // Verify retry button is available
    expect(screen.getByText('Return to Tasks')).toBeInTheDocument();
  });

  it('handles file attachment display correctly', async () => {
    // Create mock task with file attachments
    const mockTask: Task = {
      id: '1',
      title: 'Test Task',
      description: 'Test Description',
      status: TaskStatus.CREATED,
      priority: TaskPriority.MEDIUM,
      dueDate: new Date().toISOString(),
      attachments: [
        {
          id: '1',
          name: 'document.pdf',
          size: 1024 * 1024,
          type: 'application/pdf',
          extension: 'pdf',
          storageKey: 'files/1/document.pdf',
          url: 'https://mock-file-url.example.com/1',
          preview: {
            thumbnail: 'https://mock-thumbnail-url.example.com/1',
            previewAvailable: true,
            previewType: 'pdf',
          },
          metadata: {
            uploadedBy: '1',
            uploadedAt: new Date().toISOString(),
            lastAccessed: new Date().toISOString(),
            accessCount: 0,
            md5Hash: 'test',
          },
          security: {
            accessLevel: 'public',
            encryptionType: 'none',
            scanStatus: 'clean',
          },
          associations: {
            taskId: '1',
            projectId: null,
            commentId: null,
          },
          versions: [],
        },
      ],
    } as any;

    // Setup API response with attachment data
    server.use(
      rest.get(TASK_ENDPOINTS.GET_TASK(':id'), (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTask));
      })
    );

    // Render the TaskDetail component
    render(
      <MemoryRouter initialEntries={['/tasks/1']}>
        <Routes>
          <Route path="/tasks/:taskId" element={<TaskDetail />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Attachments')).toBeInTheDocument();
    });

    // Verify attachments section is displayed
    expect(screen.getByText('Attachments')).toBeInTheDocument();

    // Verify attachment names and icons are shown
    expect(screen.getByText('document.pdf')).toBeInTheDocument();

    // Verify download links are available
    expect(screen.getByRole('button', { name: 'Download document.pdf' })).toBeInTheDocument();
  });
});