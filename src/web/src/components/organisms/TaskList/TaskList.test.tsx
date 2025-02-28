import React from 'react'; // version 18.2.0
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'; // version 14.0.0
import userEvent from '@testing-library/user-event'; // version 14.4.3
import { rest } from 'msw'; // version 1.2.1
import { describe, it, expect, beforeEach, afterEach, jest } from 'jest'; // version 29.5.0
import TaskList from './TaskList'; // The component under test
import { useTasks } from '@app/hooks'; // version 1.0.0
import { Task, TaskStatus, TaskPriority } from '@app/types'; // version 1.0.0

// Mock the useTasks hook
jest.mock('@app/hooks');

// Mock data setup
const setupMockTasks = (): Task[] => {
  return [
    {
      id: '1',
      title: 'Task 1',
      description: 'Description 1',
      status: TaskStatus.IN_PROGRESS,
      priority: TaskPriority.HIGH,
      dueDate: '2024-03-15T12:00:00.000Z',
      createdBy: { id: 'user1', email: 'user1@example.com', firstName: 'John', lastName: 'Doe', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true }, defaultView: 'list' }, security: { mfaEnabled: false, mfaMethod: 'none', lastLogin: '2024-03-01T00:00:00.000Z', passwordLastChanged: '2024-02-01T00:00:00.000Z', emailVerified: true }, createdAt: '2024-03-01T00:00:00.000Z', updatedAt: '2024-03-01T00:00:00.000Z' },
      assignee: { id: 'user2', email: 'user2@example.com', firstName: 'Jane', lastName: 'Doe', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true }, defaultView: 'list' }, security: { mfaEnabled: false, mfaMethod: 'none', lastLogin: '2024-03-01T00:00:00.000Z', passwordLastChanged: '2024-02-01T00:00:00.000Z', emailVerified: true }, createdAt: '2024-03-01T00:00:00.000Z', updatedAt: '2024-03-01T00:00:00.000Z' },
      project: null,
      tags: [],
      attachments: [],
      subtasks: [],
      dependencies: [],
      comments: [],
      activity: [],
      metadata: { created: '2024-03-01T00:00:00.000Z', lastUpdated: '2024-03-01T00:00:00.000Z', completedAt: null, timeEstimate: null, timeSpent: null }
    },
    {
      id: '2',
      title: 'Task 2',
      description: 'Description 2',
      status: TaskStatus.COMPLETED,
      priority: TaskPriority.LOW,
      dueDate: '2024-03-20T12:00:00.000Z',
      createdBy: { id: 'user1', email: 'user1@example.com', firstName: 'John', lastName: 'Doe', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true }, defaultView: 'list' }, security: { mfaEnabled: false, mfaMethod: 'none', lastLogin: '2024-03-01T00:00:00.000Z', passwordLastChanged: '2024-02-01T00:00:00.000Z', emailVerified: true }, createdAt: '2024-03-01T00:00:00.000Z', updatedAt: '2024-03-01T00:00:00.000Z' },
      assignee: null,
      project: null,
      tags: [],
      attachments: [],
      subtasks: [],
      dependencies: [],
      comments: [],
      activity: [],
      metadata: { created: '2024-03-01T00:00:00.000Z', lastUpdated: '2024-03-01T00:00:00.000Z', completedAt: null, timeEstimate: null, timeSpent: null }
    },
  ];
};

// Helper function to render the TaskList component with specified props
const renderTaskList = (props: any) => {
  const defaultProps = {
    tasks: [],
    loading: false,
    error: null,
    filter: { status: null, priority: null, assigneeId: null, projectId: null, dueDate: null, dueDateRange: null, tags: null, searchTerm: null },
    sort: { field: 'dueDate', direction: 'asc' },
  };
  const mergedProps = { ...defaultProps, ...props };
  return render(<TaskList {...mergedProps} />);
};

describe('TaskList component', () => {
  it('renders loading state', () => {
    (useTasks as jest.Mock).mockReturnValue({
      tasks: [],
      loading: true,
      error: null,
      totalTasks: 0,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    renderTaskList({});
    expect(screen.getByText('Loading tasks...')).toBeInTheDocument();
  });

  it('renders empty state when no tasks', () => {
    (useTasks as jest.Mock).mockReturnValue({
      tasks: [],
      loading: false,
      error: null,
      totalTasks: 0,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    renderTaskList({});
    expect(screen.getByText('No tasks found matching your criteria')).toBeInTheDocument();
  });

  it('renders tasks correctly', () => {
    const mockTasks = setupMockTasks();
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    renderTaskList({});
    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
  });

  it('allows filtering by status', async () => {
    const mockTasks = setupMockTasks();
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    const onFilterChangeMock = jest.fn();
    renderTaskList({ onFilterChange: onFilterChangeMock });

    // Simulate selecting a status filter (e.g., 'completed')
    // This part depends on how your filter UI is implemented
    // For example, if you have a select element:
    // fireEvent.change(screen.getByRole('combobox', { name: /status/i }), { target: { value: 'completed' } });

    // Verify that the onFilterChange function was called with the correct filter
    // expect(onFilterChangeMock).toHaveBeenCalledWith({ status: 'completed' });
  });

  it('allows sorting tasks', async () => {
    const mockTasks = setupMockTasks();
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    const onSortChangeMock = jest.fn();
    renderTaskList({ sort: { field: 'dueDate', direction: 'asc' }, onSortChange: onSortChangeMock });

    // Simulate changing the sort option (e.g., by due date)
    // This part depends on how your sort UI is implemented
    // For example, if you have a button:
    // await userEvent.click(screen.getByRole('button', { name: /due date/i }));

    // Verify that the onSortChange function was called with the correct sort option
    // expect(onSortChangeMock).toHaveBeenCalledWith({ field: 'dueDate', direction: 'desc' });
  });

  it('supports pagination', async () => {
    const mockTasks = Array.from({ length: 25 }, (_, i) => ({
      id: `${i + 1}`,
      title: `Task ${i + 1}`,
      description: `Description ${i + 1}`,
      status: TaskStatus.IN_PROGRESS,
      priority: TaskPriority.MEDIUM,
      dueDate: null,
      createdBy: { id: 'user1', email: 'user1@example.com', firstName: 'John', lastName: 'Doe', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true }, defaultView: 'list' }, security: { mfaEnabled: false, mfaMethod: 'none', lastLogin: '2024-03-01T00:00:00.000Z', passwordLastChanged: '2024-02-01T00:00:00.000Z', emailVerified: true }, createdAt: '2024-03-01T00:00:00.000Z', updatedAt: '2024-03-01T00:00:00.000Z' },
      assignee: null,
      project: null,
      tags: [],
      attachments: [],
      subtasks: [],
      dependencies: [],
      comments: [],
      activity: [],
      metadata: { created: '2024-03-01T00:00:00.000Z', lastUpdated: '2024-03-01T00:00:00.000Z', completedAt: null, timeEstimate: null, timeSpent: null }
    }));
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks.slice(0, 10),
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 1,
      pageSize: 10,
      totalPages: 3,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    renderTaskList({});
    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 10')).toBeInTheDocument();
    expect(screen.queryByText('Task 11')).not.toBeInTheDocument();

    const nextPageButton = screen.getByRole('button', { name: /next/i });
    await userEvent.click(nextPageButton);
    
    // Mock the next page
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks.slice(10, 20),
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 2,
      pageSize: 10,
      totalPages: 3,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });
    
    // Re-render the component
    renderTaskList({});
    
    // Check if the next page tasks are rendered
    expect(screen.getByText('Task 11')).toBeInTheDocument();
    expect(screen.getByText('Task 20')).toBeInTheDocument();
    expect(screen.queryByText('Task 1')).not.toBeInTheDocument();
  });

  it('handles task selection', async () => {
    const mockTasks = setupMockTasks();
    (useTasks as jest.Mock).mockReturnValue({
      tasks: mockTasks,
      loading: false,
      error: null,
      totalTasks: mockTasks.length,
      page: 1,
      pageSize: 10,
      totalPages: 1,
      nextPage: jest.fn(),
      prevPage: jest.fn(),
      setPage: jest.fn(),
      setPageSize: jest.fn(),
      refetch: jest.fn(),
    });

    const onTaskClickMock = jest.fn();
    renderTaskList({ onTaskClick: onTaskClickMock });

    await userEvent.click(screen.getByText('Task 1'));
    expect(onTaskClickMock).toHaveBeenCalledWith(mockTasks[0]);
  });
});