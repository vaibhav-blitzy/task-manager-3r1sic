import React from 'react'; // react ^18.2.0
import { rest } from 'msw'; // msw ^1.0.0
import { describe, beforeEach, afterEach, it, expect } from '@jest/globals'; // @jest/globals ^29.0.0

import Calendar from './Calendar'; // Component under test
import { render, screen, waitFor, fireEvent, within } from '../../utils/test-utils'; // Custom testing utilities
import server from '../../__tests__/mocks/server'; // Mock server for API calls
import { formatDate } from '../../utils/date'; // Utility for formatting dates
import { Task, TasksResponse, TasksFilter } from '../../types/task'; // Type definitions for task-related data
import { TASK_ENDPOINTS } from '../../api/endpoints'; // API endpoint constants
import { createMockTask, waitForLoadingToFinish } from '../../utils/test-utils'; // Helper function to create mock task data

// Mock tasks for testing calendar display
const mockTasks: Task[] = [
  createMockTask({ id: '1', title: 'Task 1', dueDate: formatDate(new Date(), 'YYYY-MM-DD') }),
  createMockTask({ id: '2', title: 'Task 2', dueDate: formatDate(new Date(), 'YYYY-MM-DD') }),
  createMockTask({ id: '3', title: 'Task 3', dueDate: formatDate(new Date(new Date().setDate(new Date().getDate() + 1)), 'YYYY-MM-DD') }),
];

/**
 * Helper function to create a mock tasks response object
 * @param {Task[]} tasks
 * @returns {TasksResponse} Mock response with pagination info
 */
const createMockTasksResponse = (tasks: Task[]): TasksResponse => {
  return {
    items: tasks,
    total: tasks.length,
    page: 1,
    pageSize: tasks.length,
    totalPages: 1,
  };
};

/**
 * Helper function to set up mock API handler for tasks endpoint
 * @param {Task[]} tasks
 * @returns {void}
 */
const setupTasksHandler = (tasks: Task[]): void => {
  server.use(
    rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
      const tasksResponse = createMockTasksResponse(tasks);
      return res(ctx.status(200), ctx.json(tasksResponse));
    })
  );
};

describe('Calendar Component', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  afterEach(() => {
    // Clear any previous render results
  });

  it('renders the calendar with current month and days', async () => {
    setupTasksHandler([]);
    render(<Calendar />);
    await waitForLoadingToFinish();

    const currentMonthYear = formatDate(new Date(), 'MMMM YYYY');
    expect(screen.getByText(currentMonthYear)).toBeInTheDocument();

    expect(screen.getByText('Sun')).toBeInTheDocument();
    expect(screen.getByText('Mon')).toBeInTheDocument();
    expect(screen.getByText('Tue')).toBeInTheDocument();
    expect(screen.getByText('Wed')).toBeInTheDocument();
    expect(screen.getByText('Thu')).toBeInTheDocument();
    expect(screen.getByText('Fri')).toBeInTheDocument();
    expect(screen.getByText('Sat')).toBeInTheDocument();

    const dayCells = screen.getAllByText(/^[0-9]+$/);
    expect(dayCells.length).toBeGreaterThan(27);
  });

  it('displays loading state while fetching tasks', async () => {
    server.use(
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.delay(150), ctx.status(200), ctx.json(createMockTasksResponse([])));
      })
    );

    render(<Calendar />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    await waitForLoadingToFinish();
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('displays tasks on their corresponding due dates', async () => {
    setupTasksHandler(mockTasks);
    render(<Calendar />);
    await waitForLoadingToFinish();

    mockTasks.forEach(task => {
      const dayCell = screen.getByText(new Date(task.dueDate!).getDate().toString());
      expect(dayCell).toBeInTheDocument();
      expect(dayCell.closest('.calendar-day')).toHaveTextContent(task.title);
    });
  });

  it('allows navigation between months', async () => {
    setupTasksHandler([]);
    render(<Calendar />);
    await waitForLoadingToFinish();

    const nextMonthButton = screen.getByText('Next');
    fireEvent.click(nextMonthButton);
    const nextMonthYear = formatDate(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1), 'MMMM YYYY');
    expect(screen.getByText(nextMonthYear)).toBeInTheDocument();

    const prevMonthButton = screen.getByText('Previous');
    fireEvent.click(prevMonthButton);
    const currentMonthYear = formatDate(new Date(), 'MMMM YYYY');
    expect(screen.getByText(currentMonthYear)).toBeInTheDocument();

    const todayButton = screen.getByText('Today');
    fireEvent.click(todayButton);
    expect(screen.getByText(currentMonthYear)).toBeInTheDocument();
  });

  it('allows searching for tasks in calendar view', async () => {
    setupTasksHandler(mockTasks);
    render(<Calendar />);
    await waitForLoadingToFinish();

    const searchInput = screen.getByPlaceholderText('Search tasks...');
    fireEvent.change(searchInput, { target: { value: 'Task 1' } });
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.queryByText('Task 2')).not.toBeInTheDocument();
    });

    fireEvent.change(searchInput, { target: { value: '' } });
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  it('allows filtering tasks by project', async () => {
    const mockTasksWithProjects: Task[] = [
      createMockTask({ id: '1', title: 'Task 1', project: { id: 'project1', name: 'Project 1', description: 'Description', status: 'active' } }),
      createMockTask({ id: '2', title: 'Task 2', project: { id: 'project2', name: 'Project 2', description: 'Description', status: 'active' } }),
    ];
    setupTasksHandler(mockTasksWithProjects);
    render(<Calendar />);
    await waitForLoadingToFinish();

    const projectFilterDropdown = screen.getByRole('combobox');
    fireEvent.change(projectFilterDropdown, { target: { value: 'project1' } });
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.queryByText('Task 2')).not.toBeInTheDocument();
    });

    fireEvent.change(projectFilterDropdown, { target: { value: '' } });
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });

  it('displays error message when tasks fetch fails', async () => {
    server.use(
      rest.get(TASK_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'Failed to fetch tasks' }));
      })
    );

    render(<Calendar />);
    await waitFor(() => {
      expect(screen.getByText('Error loading tasks')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  });

  it('allows creating a new task from calendar day', async () => {
    setupTasksHandler([]);
    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));
    render(<Calendar />);
    await waitForLoadingToFinish();

    const dayCell = screen.getAllByText(/^[0-9]+$/)[0].closest('.calendar-day');
    fireEvent.click(dayCell!);
    expect(mockNavigate).toHaveBeenCalled();
  });

  it('navigates to task details when clicking on a task', async () => {
    setupTasksHandler(mockTasks);
    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate,
    }));
    render(<Calendar />);
    await waitForLoadingToFinish();

    const taskCard = screen.getByText('Task 1').closest('.task-card');
    fireEvent.click(taskCard!);
    expect(mockNavigate).toHaveBeenCalled();
  });
});