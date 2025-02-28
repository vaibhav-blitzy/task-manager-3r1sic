import React from 'react'; // React ^18.2.0
import { jest } from '@jest/globals'; // jest ^29.0.0
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react ^13.0.0
import { BrowserRouter, MemoryRouter } from 'react-router-dom'; // react-router-dom ^6.0.0
import { TaskList } from './TaskList';
import useTasks from '../../../api/hooks/useTasks';
import { server } from '../../../__tests__/mocks/server';
import { handlers } from '../../../__tests__/mocks/handlers';
import PATHS from '../../../routes/paths';

// Mock the useTasks hook
jest.mock('../../../api/hooks/useTasks');

describe('TaskList component', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('renders the task list with loading state', async () => {
    (useTasks as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: true,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={[]}
          loading={true}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
  });

  it('renders tasks when data is loaded', async () => {
    const mockTasks = [
      { id: '1', title: 'Task 1', status: 'in-progress' },
      { id: '2', title: 'Task 2', status: 'completed' },
    ];

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={mockTasks}
          loading={false}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  it('handles filtering tasks', async () => {
    const mockTasks = [
      { id: '1', title: 'Task 1', status: 'in-progress' },
      { id: '2', title: 'Task 2', status: 'completed' },
    ];

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={mockTasks}
          loading={false}
          error={null}
          filter={{ searchTerm: 'Task 1' }}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.queryByText('Task 2')).not.toBeInTheDocument();
    });
  });

  it('handles sorting tasks', async () => {
    const mockTasks = [
      { id: '1', title: 'Task B', status: 'in-progress' },
      { id: '2', title: 'Task A', status: 'completed' },
    ];

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={mockTasks}
          loading={false}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      const taskTitles = screen.getAllByText(/Task [A|B]/).map(el => el.textContent);
      expect(taskTitles).toEqual(['Task A', 'Task B']);
    });
  });

  it('navigates to task detail when task is clicked', async () => {
    const mockTasks = [
      { id: '1', title: 'Task 1', status: 'in-progress' },
      { id: '2', title: 'Task 2', status: 'completed' },
    ];

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    const navigate = jest.fn();

    render(
      <MemoryRouter>
        <TaskList
          tasks={mockTasks}
          loading={false}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
          onTaskClick={(task) => navigate(PATHS.TASK_DETAIL.replace(':id', task.id))}
        />
      </MemoryRouter>
    );

    await waitFor(() => {
      const taskElement = screen.getByText('Task 1');
      fireEvent.click(taskElement);
      expect(navigate).toHaveBeenCalledWith(PATHS.TASK_DETAIL.replace(':id', '1'));
    });
  });

  it('shows error state when task loading fails', async () => {
    (useTasks as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: false,
      error: 'Failed to load tasks',
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={[]}
          loading={false}
          error="Failed to load tasks"
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Error loading tasks: Failed to load tasks')).toBeInTheDocument();
    });
  });

  it('shows empty state when no tasks are available', async () => {
    (useTasks as jest.Mock).mockReturnValue({
      tasks: [],
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={[]}
          loading={false}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No tasks found matching your criteria')).toBeInTheDocument();
    });
  });

  it('handles pagination correctly', async () => {
    const mockTasks = Array.from({ length: 25 }, (_, i) => ({
      id: `${i + 1}`,
      title: `Task ${i + 1}`,
      status: 'in-progress',
    }));

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks.slice(0, 10),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      page: 1,
      pageSize: 10,
      totalPages: 3,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
    });

    render(
      <BrowserRouter>
        <TaskList
          tasks={mockTasks.slice(0, 10)}
          loading={false}
          error={null}
          filter={{}}
          sort={{ field: 'title', direction: 'asc' }}
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.queryByText('Task 11')).not.toBeInTheDocument();
    });

    const nextPageButton = screen.getByText('Next');
    fireEvent.click(nextPageButton);

    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks.slice(10, 20),
      isLoading: false,
      error: null,
      refetch: jest.fn(),
      page: 2,
      pageSize: 10,
      totalPages: 3,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
    });

    await waitFor(() => {
      expect(screen.queryByText('Task 1')).not.toBeInTheDocument();
      expect(screen.getByText('Task 11')).toBeInTheDocument();
    });
  });
});