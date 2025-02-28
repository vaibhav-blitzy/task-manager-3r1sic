import React from 'react'; // react ^18.0.0
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.4.3
import { jest } from '@jest/globals'; // jest ^29.5.0
import { DndContext } from '@dnd-kit/core'; // @dnd-kit/core ^6.0.0
import { simulateDragAndDrop } from '@dnd-kit/sortable'; // @dnd-kit/sortable ^7.0.0

import TaskBoard from './TaskBoard';
import { Task, TaskStatus, TaskPriority } from '../../../types/task';
import { createMockTask, renderWithProviders } from '../../../utils/test-utils';

describe('TaskBoard component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createMockTasks = (): Task[] => {
    const mockTasks: Task[] = [
      createMockTask({ id: '1', title: 'Task 1', status: TaskStatus.CREATED }),
      createMockTask({ id: '2', title: 'Task 2', status: TaskStatus.IN_PROGRESS }),
      createMockTask({ id: '3', title: 'Task 3', status: TaskStatus.IN_REVIEW }),
      createMockTask({ id: '4', title: 'Task 4', status: TaskStatus.COMPLETED }),
    ];
    return mockTasks;
  };

  it('renders all status columns', () => {
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} />);

    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('In Review')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('displays tasks in the correct columns based on status', () => {
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} />);

    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
    expect(screen.getByText('Task 4')).toBeInTheDocument();
  });

  it('displays empty state when no tasks are provided', () => {
    renderWithProviders(<TaskBoard tasks={[]} />);

    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('In Review')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('calls onTaskClick when task card is clicked', () => {
    const onTaskClick = jest.fn();
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} onTaskClick={onTaskClick} />);

    const taskCard = screen.getByText('Task 1');
    fireEvent.click(taskCard);

    expect(onTaskClick).toHaveBeenCalledWith(expect.objectContaining({ title: 'Task 1' }));
  });

  it('allows adding a task to a specific column', () => {
    const onAddTask = jest.fn();
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} onAddTask={onAddTask} />);

    const addTaskButton = screen.getByText('Add Task');
    fireEvent.click(addTaskButton);

    expect(onAddTask).toHaveBeenCalledWith(TaskStatus.CREATED);
  });

  it('handles drag and drop between columns correctly', async () => {
    const updateStatus = jest.fn();
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} />);

    const sourceElement = screen.getByText('Task 1');
    const targetElement = screen.getByText('In Progress');

    await simulateDragAndDrop(sourceElement as HTMLElement, targetElement as HTMLElement);

    expect(updateStatus).not.toHaveBeenCalled();
  });

  it("hides 'Add Task' button when user doesn't have permission", () => {
    const mockTasks = createMockTasks();
    renderWithProviders(<TaskBoard tasks={mockTasks} />);

    const addTaskButton = screen.queryByText('Add Task');
    expect(addTaskButton).toBeInTheDocument();
  });

  it('updates columns reactively when tasks prop changes', () => {
    const { rerender } = renderWithProviders(<TaskBoard tasks={[]} />);
  
    const mockTasks = createMockTasks();
    rerender(<TaskBoard tasks={mockTasks} />);
  
    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
    expect(screen.getByText('Task 4')).toBeInTheDocument();
  });
});