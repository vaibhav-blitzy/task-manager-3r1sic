import React from 'react'; // react ^18.2.0
import { fireEvent, act } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { rest } from 'msw'; // msw ^1.2.1
import {
  describe,
  it,
  expect,
  beforeAll,
  afterEach,
  afterAll,
  jest,
} from '@jest/globals'; // @jest/globals ^29.5.0

import {
  Dashboard,
  render,
  screen,
  waitFor,
  createMockUser,
  createMockTask,
  createMockProject,
} from '../../utils/test-utils';
import { server } from '../../__tests__/mocks/server';
import handlers from '../../__tests__/mocks/handlers';
import { TASK_ENDPOINTS, PROJECT_ENDPOINTS } from '../../api/endpoints';

// Setup function that runs before all tests in this file
beforeAll(() => {
  // Start the Mock Service Worker server to intercept API requests
  server.listen();
  // Configure any global test setup needed for all dashboard tests
});

// Cleanup function that runs after each test
afterEach(() => {
  // Reset any request handlers that may have been modified during tests
  server.resetHandlers();
  // Clear any mocked function calls
  jest.clearAllMocks();
});

// Cleanup function that runs after all tests in this file
afterAll(() => {
  // Close the Mock Service Worker server
  server.close();
});

/**
 * Helper function to create mock API handler for tasks
 * @param tasks Array of tasks
 * @returns MSW request handler
 */
const mockTasksResponse = (tasks: any[]) => {
  // Create a REST handler for the tasks API endpoint
  return rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
    // Configure it to return the provided mock tasks array
    return res(
      ctx.status(200),
      ctx.json({ items: tasks, total: tasks.length, page: 1, pageSize: 20, totalPages: 1 })
    );
  });
};

/**
 * Helper function to create mock API handler for projects
 * @param projects Array of projects
 * @returns MSW request handler
 */
const mockProjectsResponse = (projects: any[]) => {
  // Create a REST handler for the projects API endpoint
  return rest.get(PROJECT_ENDPOINTS.BASE, (req, res, ctx) => {
    // Configure it to return the provided mock projects array
    return res(
      ctx.status(200),
      ctx.json({ items: projects, total: projects.length, page: 1, pageSize: 20, totalPages: 1 })
    );
  });
};

/**
 * Helper function to set up common mock data for dashboard tests
 * @returns Object containing mock user, tasks, and projects
 */
const setupMockData = () => {
  // Create a mock user using createMockUser
  const mockUser = createMockUser({ firstName: 'Test', lastName: 'User' });

  // Create several mock tasks with different statuses and due dates
  const mockTasks = [
    createMockTask({ title: 'Task 1', status: 'in-progress', dueDate: new Date().toISOString() }),
    createMockTask({ title: 'Task 2', status: 'completed', dueDate: new Date(Date.now() + 86400000).toISOString() }),
  ];

  // Create mock projects with varying progress percentages
  const mockProjects = [
    createMockProject({ name: 'Project 1', metadata: { taskCount: 10, completedTaskCount: 3 } }),
    createMockProject({ name: 'Project 2', metadata: { taskCount: 5, completedTaskCount: 5 } }),
  ];

  return { mockUser, mockTasks, mockProjects };
};

// Test suite for dashboard rendering behavior
describe('Dashboard Rendering', () => {
  // Test that Dashboard initially shows loading states before data loads
  it('Renders dashboard with loading states', () => {
    // Render Dashboard component using render from test-utils
    render(<Dashboard />);

    // Verify loading indicators are visible for tasks and projects sections
    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
    expect(screen.getByText('Loading projects...')).toBeInTheDocument();

    // Confirm Dashboard layout and structure is properly formed even during loading
    expect(screen.getByText('Welcome back,')).toBeInTheDocument();
  });

  // Test that Dashboard shows personalized welcome message
  it('Renders welcome message with user name', async () => {
    // Set up mock user data with specific name
    const mockUser = createMockUser({ firstName: 'Test', lastName: 'User' });

    // Mock API responses to include the user information
    server.use(
      rest.get(/\/api\/v1\/auth\/status/, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ isAuthenticated: true, user: mockUser }));
      })
    );

    // Render Dashboard component
    render(<Dashboard />);

    // Verify welcome message includes the user's name
    await waitFor(() => {
      expect(screen.getByText('Welcome back, Test')).toBeInTheDocument();
    });
  });

  // Test that tasks due today are properly displayed
  it('Displays tasks due today widget', async () => {
    // Set up mock task data with some tasks due today
    const mockTasks = [createMockTask({ title: 'Task Due Today', dueDate: new Date().toISOString() })];

    // Mock API response for due soon tasks endpoint
    server.use(mockTasksResponse(mockTasks));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Tasks Due Soon')).toBeInTheDocument();
    });

    // Verify 'Tasks Due Today' widget is present
    expect(screen.getByText('Tasks Due Soon')).toBeInTheDocument();

    // Confirm that due tasks are displayed with correct information
    expect(screen.getByText('Task Due Today')).toBeInTheDocument();
  });

  // Test that project progress widget shows correctly
  it('Displays project progress widget', async () => {
    // Set up mock project data with progress information
    const mockProjects = [createMockProject({ name: 'Project in Progress', metadata: { taskCount: 10, completedTaskCount: 5 } })];

    // Mock API response for projects endpoint
    server.use(mockProjectsResponse(mockProjects));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Project Progress')).toBeInTheDocument();
    });

    // Verify 'Project Progress' widget is present
    expect(screen.getByText('Project Progress')).toBeInTheDocument();

    // Confirm projects are displayed with progress bars showing correct percentages
    expect(screen.getByText('Project in Progress')).toBeInTheDocument();
  });

  // Test that task statistics chart renders properly
  it('Renders task statistics with chart', async () => {
    // Set up mock task statistics data
    const mockTaskStats = {
      total: 100,
      byStatus: {
        created: 20,
        'in-progress': 30,
        completed: 50,
      },
    };

    // Mock API response for task statistics endpoint
    server.use(
      rest.get(/\/api\/v1\/tasks\/statistics/, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTaskStats));
      })
    );

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Task Status')).toBeInTheDocument();
    });

    // Verify task status chart is present
    expect(screen.getByText('Task Status')).toBeInTheDocument();

    // Confirm chart displays correct statistics data
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  // Test that recent activity widget shows correctly
  it('Displays activity widget', async () => {
    // Set up mock activity data
    const mockActivity = [{ id: '1', type: 'task-created', description: 'Task created' }];

    // Mock API response for activity endpoint
    server.use(
      rest.get(/\/api\/v1\/activity/, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockActivity));
      })
    );

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Activity')).toBeInTheDocument();
    });

    // Verify 'My Activity' widget is present
    expect(screen.getByText('Activity')).toBeInTheDocument();

    // Confirm activity items are displayed with timestamps
    expect(screen.getByText('Recent activity items will be displayed here.')).toBeInTheDocument();
  });
});

// Test suite for interactive elements on the dashboard
describe('Dashboard Interactions', () => {
  // Test navigation when clicking a task item
  it('Navigates to task detail when clicking task', async () => {
    // Set up mock task data
    const mockTask = createMockTask({ id: '123', title: 'Test Task' });

    // Mock API responses
    server.use(mockTasksResponse([mockTask]));

    // Set up mock router and navigation tracking
    const navigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    // Find and click a task item
    const taskElement = screen.getByText('Test Task');
    act(() => {
      fireEvent.click(taskElement);
    });

    // Verify navigation was triggered to the task detail page with correct task ID
    expect(navigate).toHaveBeenCalledWith('/tasks/123');
  });

  // Test navigation when clicking a project card
  it('Navigates to project detail when clicking project', async () => {
    // Set up mock project data
    const mockProject = createMockProject({ id: '456', name: 'Test Project' });

    // Mock API responses
    server.use(mockProjectsResponse([mockProject]));

    // Set up mock router and navigation tracking
    const navigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    // Find and click a project card
    const projectElement = screen.getByText('Test Project');
    act(() => {
      fireEvent.click(projectElement);
    });

    // Verify navigation was triggered to the project detail page with correct project ID
    expect(navigate).toHaveBeenCalledWith('/projects/456');
  });

  // Test navigation to task creation from dashboard
  it('Navigates to task creation when clicking create task button', async () => {
    // Set up mock API responses
    server.use(mockTasksResponse([]));
    server.use(mockProjectsResponse([]));

    // Set up mock router and navigation tracking
    const navigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    // Render Dashboard component
    render(<Dashboard />);

    // Find and click the 'Create New Task' button
    const createTaskButton = screen.getByText('Create New Task');
    act(() => {
      fireEvent.click(createTaskButton);
    });

    // Verify navigation was triggered to the task creation page
    expect(navigate).toHaveBeenCalledWith('/tasks/create');
  });

  // Test navigation to project creation from dashboard
  it('Navigates to project creation when clicking create project button', async () => {
    // Set up mock API responses
    server.use(mockTasksResponse([]));
    server.use(mockProjectsResponse([]));

    // Set up mock router and navigation tracking
    const navigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    // Render Dashboard component
    render(<Dashboard />);

    // Find and click the 'Create New Project' button
    const createProjectButton = screen.getByText('Create New Project');
    act(() => {
      fireEvent.click(createProjectButton);
    });

    // Verify navigation was triggered to the project creation page
    expect(navigate).toHaveBeenCalledWith('/projects/create');
  });

  // Test that 'View All Tasks' button navigates correctly
  it("View all tasks button navigates to task list", async () => {
    // Set up mock API responses
    server.use(mockTasksResponse([]));
    server.use(mockProjectsResponse([]));

    // Set up mock router and navigation tracking
    const navigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    // Render Dashboard component
    render(<Dashboard />);

    // Find and click the 'View All Tasks' button
    const viewAllTasksButton = screen.getByText('View All Tasks');
    act(() => {
      fireEvent.click(viewAllTasksButton);
    });

    // Verify navigation was triggered to the task list page
    expect(navigate).toHaveBeenCalledWith('/tasks');
  });
});

// Test suite for error handling on dashboard
describe('Dashboard Error Handling', () => {
  // Test error handling when tasks API fails
  it('Displays error state for tasks API failure', async () => {
    // Mock tasks API endpoint to return error response
    server.use(
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'ServerError', message: 'Failed to fetch tasks' })
        );
      })
    );

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.getByText('Error loading tasks:')).toBeInTheDocument();
    });

    // Verify error message is displayed in tasks widget
    expect(screen.getByText('Error loading tasks: Failed to fetch tasks')).toBeInTheDocument();

    // Confirm other widgets still function normally
    expect(screen.getByText('Project Progress')).toBeInTheDocument();
  });

  // Test error handling when projects API fails
  it('Displays error state for projects API failure', async () => {
    // Mock projects API endpoint to return error response
    server.use(
      rest.get(PROJECT_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ error: 'ServerError', message: 'Failed to fetch projects' })
        );
      })
    );

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.getByText('Error loading projects:')).toBeInTheDocument();
    });

    // Verify error message is displayed in projects widget
    expect(screen.getByText('Error loading projects: Failed to fetch projects')).toBeInTheDocument();

    // Confirm other widgets still function normally
    expect(screen.getByText('Tasks Due Soon')).toBeInTheDocument();
  });

  // Test empty state handling for tasks
  it('Displays empty state when no tasks available', async () => {
    // Mock tasks API endpoint to return empty array
    server.use(mockTasksResponse([]));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.getByText('No tasks due soon')).toBeInTheDocument();
    });

    // Verify empty state message is displayed in tasks widget
    expect(screen.getByText('No tasks due soon')).toBeInTheDocument();
  });

  // Test empty state handling for projects
  it('Displays empty state when no projects available', async () => {
    // Mock projects API endpoint to return empty array
    server.use(mockProjectsResponse([]));

    // Render Dashboard component
    render(<Dashboard />);

    // Wait for API call to complete
    await waitFor(() => {
      expect(screen.getByText('No projects found')).toBeInTheDocument();
    });

    // Verify empty state message is displayed in projects widget
    expect(screen.getByText('No projects found')).toBeInTheDocument();
  });
});

// Test suite for responsive behavior of dashboard
describe('Dashboard Responsiveness', () => {
  // Test dashboard layout on mobile screen sizes
  it('Adjusts layout for mobile viewport', async () => {
    // Mock API responses
    server.use(mockTasksResponse([]));
    server.use(mockProjectsResponse([]));

    // Mock window size to mobile dimensions
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 320 });
    window.dispatchEvent(new Event('resize'));

    // Render Dashboard component
    render(<Dashboard />);

    // Verify widgets are stacked in a single column
    const tasksWidget = await screen.findByText('Tasks Due Soon');
    const projectsWidget = await screen.findByText('Project Progress');
    expect(tasksWidget).toBeInTheDocument();
    expect(projectsWidget).toBeInTheDocument();

    // Confirm responsive adaptations are correctly applied
    expect(tasksWidget.parentElement?.classList.contains('col-span-1')).toBe(true);
    expect(projectsWidget.parentElement?.classList.contains('col-span-1')).toBe(true);
  });

  // Test dashboard layout on tablet screen sizes
  it('Adjusts layout for tablet viewport', async () => {
    // Mock API responses
    server.use(mockTasksResponse([]));
    server.use(mockProjectsResponse([]));

    // Mock window size to tablet dimensions
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 768 });
    window.dispatchEvent(new Event('resize'));

    // Render Dashboard component
    render(<Dashboard />);

    // Verify widgets are arranged in 1-2 per row
    const tasksWidget = await screen.findByText('Tasks Due Soon');
    const projectsWidget = await screen.findByText('Project Progress');
    expect(tasksWidget).toBeInTheDocument();
    expect(projectsWidget).toBeInTheDocument();

    // Confirm responsive adaptations are correctly applied
    expect(tasksWidget.parentElement?.classList.contains('col-span-1')).toBe(true);
    expect(projectsWidget.parentElement?.classList.contains('col-span-1')).toBe(true);
  });
});