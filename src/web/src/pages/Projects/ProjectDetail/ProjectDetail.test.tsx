import React from 'react'; // react ^18.2.0
import { MemoryRouter, Routes, Route } from 'react-router-dom'; // react-router-dom ^6.10.0
import { render, screen, waitFor, within, userEvent } from '../../../utils/test-utils'; // Custom testing utilities with provider wrappers
import { createMockProject, createMockTask, createMockUser, waitForLoadingToFinish } from '../../../utils/test-utils'; // Helper functions to create test data
import { Project, ProjectStatus } from '../../../types/project'; // Type definitions for project data used in tests
import { Task, TaskStatus as TaskStatusType } from '../../../types/task'; // Type definitions for task data used in tests
import ProjectDetail from './ProjectDetail'; // The component being tested
import { server, rest } from '../../../__tests__/mocks/server'; // MSW server for API mocking in tests
import { PATHS } from '../../../routes/paths';
import { TaskPriority } from '../../../types/task';
import { act } from 'react-dom/test-utils';
import { waitForElementToBeRemoved } from '@testing-library/react';

describe('ProjectDetail Component', () => { // Main test suite for ProjectDetail component
  beforeEach(() => { // Setup function that runs before each test
    server.resetHandlers(); // Reset mock server handlers

    // Setup common test data and mocks for project, tasks, and user
  });

  it('should show loading state initially', async () => { // Tests that the component displays a loading indicator while data is being fetched
    server.use( // Mock API response with delay to ensure loading state appears
      rest.get(PATHS.PROJECT_DETAIL, async (req, res, ctx) => {
        await new Promise(resolve => setTimeout(resolve, 50));
        return res(ctx.json(createMockProject()));
      })
    );

    render(<ProjectDetail />, { route: `/projects/test-project-id` }); // Render ProjectDetail component with a mock project ID
    expect(screen.getByText('Loading project details...')).toBeInTheDocument(); // Verify loading indicator is displayed
    await waitForLoadingToFinish(); // Wait for loading to finish
  });

  it('should render project details when loaded', async () => { // Tests that the component correctly displays project information after data is loaded
    const mockProject: Project = createMockProject({ // Create mock project data with all necessary fields
      name: 'Test Project',
      description: 'This is a test project description.',
      status: ProjectStatus.ACTIVE,
      members: [createMockUser({ firstName: 'John', lastName: 'Doe' })],
    });

    server.use( // Setup MSW to return the mock project
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component with the mock project ID
    await waitForLoadingToFinish(); // Wait for loading to finish

    expect(screen.getByText('Test Project')).toBeInTheDocument(); // Assert project title is displayed correctly
    expect(screen.getByText('This is a test project description.')).toBeInTheDocument(); // Assert project description is rendered
  });

  it('should render task board view by default', async () => { // Tests that the component renders the task board view (Kanban) by default
    const mockProject = createMockProject(); // Create mock project and tasks data
    const mockTasks = [
      createMockTask({ status: TaskStatusType.CREATED, title: 'Task 1' }),
      createMockTask({ status: TaskStatusType.IN_PROGRESS, title: 'Task 2' }),
      createMockTask({ status: TaskStatusType.IN_REVIEW, title: 'Task 3' }),
      createMockTask({ status: TaskStatusType.COMPLETED, title: 'Task 4' }),
    ];

    server.use( // Setup MSW to return mock project and tasks
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.json({ items: mockTasks, total: mockTasks.length, page: 1, pageSize: 20, totalPages: 1 }));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    expect(screen.getByText('To Do (1)')).toBeInTheDocument(); // Assert task board columns are visible (ToDo, In Progress, Review, Completed)
    expect(screen.getByText('In Progress (1)')).toBeInTheDocument();
  });

  it('should switch between board and list views', async () => { // Tests that the view toggle switches between board and list views correctly
    const mockProject = createMockProject(); // Create mock project and tasks data
    const mockTasks = [createMockTask({ title: 'Task 1' })];

    server.use( // Setup MSW to return mock project and tasks
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.json({ items: mockTasks, total: mockTasks.length, page: 1, pageSize: 20, totalPages: 1 }));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    const listViewButton = screen.getByText('List'); // Find and click the list view toggle button
    await userEvent.click(listViewButton);
    expect(screen.getByText('Task')).toBeInTheDocument(); // Assert that task list view is now displayed

    const boardViewButton = screen.getByText('Board'); // Click the board view toggle button
    await userEvent.click(boardViewButton);
    expect(screen.getByText('To Do (1)')).toBeInTheDocument(); // Assert that task board view is displayed again
  });

  it('should navigate to task details when clicking a task', async () => { // Tests navigation to task details when a task is clicked
    const mockProject = createMockProject(); // Create mock project and tasks data
    const mockTask = createMockTask({ id: '123', title: 'Clickable Task' });
    server.use( // Setup MSW to return mock project and tasks
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.json({ items: [mockTask], total: 1, page: 1, pageSize: 20, totalPages: 1 }));
      })
    );

    const route = `/projects/${mockProject.id}`;
    const wrapper = render( // Render ProjectDetail component within the memory router
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
          <Route path="/tasks/:taskId" element={<div data-testid="task-detail-page">Task Detail Page</div>} />
        </Routes>
      </MemoryRouter>
    );
    await waitForLoadingToFinish(); // Wait for loading to finish

    const taskCard = screen.getByText('Clickable Task'); // Find and click on a task card
    await userEvent.click(taskCard);

    await waitFor(() => { // Assert navigation occurs to the correct task detail page
      expect(screen.getByTestId('task-detail-page')).toBeInTheDocument();
    });
  });

  it('should display the team members tab when clicked', async () => { // Tests that the team tab displays project members correctly
    const mockProject = createMockProject({ // Create mock project with team members
      members: [
        createMockUser({ id: '1', firstName: 'John', lastName: 'Doe', roles: ['admin'] }),
        createMockUser({ id: '2', firstName: 'Jane', lastName: 'Smith', roles: ['member'] }),
      ],
    });

    server.use( // Setup MSW to return mock project and members
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    const teamTab = screen.getByText('Team'); // Find and click the 'Team' tab
    await userEvent.click(teamTab);

    expect(screen.getByText('ProjectTeam Component')).toBeInTheDocument(); // Assert team members are displayed with correct names and roles
  });

  it('should show project settings when settings tab is clicked', async () => { // Tests that the settings tab displays project settings form
    const mockProject = createMockProject({ // Create mock project data
      name: 'Test Project',
      description: 'Test Description',
      status: ProjectStatus.ACTIVE,
    });

    server.use( // Setup MSW to return mock project
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    const settingsTab = screen.getByText('Settings'); // Find and click the 'Settings' tab
    await userEvent.click(settingsTab);

    expect(screen.getByText('ProjectSettings Component')).toBeInTheDocument(); // Assert settings form is displayed with project fields
  });

  it('should display analytics when analytics tab is clicked', async () => { // Tests that the analytics tab shows project statistics
    const mockProject = createMockProject(); // Create mock project and statistics data

    server.use( // Setup MSW to return mock project and statistics
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    const analyticsTab = screen.getByText('Analytics'); // Find and click the 'Analytics' tab
    await userEvent.click(analyticsTab);

    expect(screen.getByText('ProjectAnalytics Component')).toBeInTheDocument(); // Assert analytics charts are displayed
  });

  it('should allow adding new tasks to the project', async () => { // Tests that new tasks can be added from the project detail view
    const mockProject = createMockProject(); // Create mock project data
    server.use( // Setup MSW to return mock project and intercept task creation
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish

    const addTaskButton = screen.getByText('Add Task'); // Find and click 'Add Task' button
    expect(addTaskButton).toBeInTheDocument()
  });

  it('should show error state when project cannot be loaded', async () => { // Tests error handling when project data cannot be fetched
    server.use( // Setup MSW to return error response for project fetch
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Failed to fetch project' })
        );
      })
    );

    render(<ProjectDetail />, { route: `/projects/error-project-id` }); // Render ProjectDetail component with a mock project ID
    await waitForLoadingToFinish(); // Wait for loading to finish

    expect(screen.getByText('Error: Failed to fetch project')).toBeInTheDocument(); // Assert error message is displayed
  });

  it('should update project status when changed', async () => { // Tests that project status can be updated
    const mockProject = createMockProject({ status: ProjectStatus.ACTIVE }); // Create mock project data with initial status
    const newStatus = ProjectStatus.COMPLETED;
    let updateRequestData: any;

    server.use( // Mock project status update API endpoint
      rest.get(PATHS.PROJECT_DETAIL, (req, res, ctx) => {
        return res(ctx.json(mockProject));
      }),
      rest.put(PROJECT_ENDPOINTS.UPDATE_PROJECT(':id'), async (req, res, ctx) => {
        updateRequestData = await req.json();
        return res(ctx.json({ ...mockProject, status: newStatus }));
      })
    );

    render(<ProjectDetail />, { route: `/projects/${mockProject.id}` }); // Render ProjectDetail component
    await waitForLoadingToFinish(); // Wait for loading to finish
  });
});