import React from 'react'; // react ^18.2.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.0.0
import { TaskCard } from './TaskCard'; // The component being tested
import { Task, TaskStatus, TaskPriority } from '../../../types/task'; // Type definitions for task data
import { User } from '../../../types/user'; // Type definition for user/assignee data
import { Project } from '../../../types/project'; // Type definition for project data
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils'; // Custom testing utilities for rendering components with necessary providers
import userEvent from '@testing-library/user-event'; // Simulates user interactions for testing

/**
 * Mock task data for testing the TaskCard component
 */
const mockTask: Task = {
  id: '123',
  title: 'Test Task',
  description: 'This is a test task',
  status: TaskStatus.IN_PROGRESS,
  priority: TaskPriority.MEDIUM,
  dueDate: '2024-03-15T12:00:00.000Z',
  createdBy: { id: 'user1', firstName: 'John', lastName: 'Doe' } as User,
  assignee: { id: 'user2', firstName: 'Jane', lastName: 'Smith' } as User,
  project: { id: 'project1', name: 'Test Project' } as Project,
  tags: [],
  attachments: [],
  subtasks: [],
  dependencies: [],
  comments: [],
  activity: [],
  metadata: {
    created: '2024-03-01T12:00:00.000Z',
    lastUpdated: '2024-03-05T12:00:00.000Z',
    completedAt: null,
    timeEstimate: 60,
    timeSpent: 30,
  },
};

/**
 * Mock user data for testing the assignee display
 */
const mockUser: User = {
  id: 'user2',
  firstName: 'Jane',
  lastName: 'Smith',
  email: 'test@example.com',
  roles: [],
  status: 'active',
  organizations: [],
  settings: {
    language: 'en',
    theme: 'light',
    notifications: {
      email: true,
      push: false,
      inApp: true,
      digest: {
        enabled: false,
        frequency: 'daily',
      },
    },
    defaultView: 'board',
  },
  security: {
    mfaEnabled: false,
    mfaMethod: 'app',
    lastLogin: new Date().toISOString(),
    lastPasswordChange: new Date().toISOString(),
    emailVerified: true,
  },
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

/**
 * Mock project data for testing the project display
 */
const mockProject: Project = {
  id: 'project1',
  name: 'Test Project',
  description: 'This is a test project',
  status: 'active',
  category: 'Test Category',
  owner: { id: 'user1', firstName: 'John', lastName: 'Doe' } as User,
  ownerId: 'user1',
  members: [],
  settings: {
    workflow: {
      enableReview: false,
      allowSubtasks: true,
      defaultTaskStatus: 'created',
    },
    permissions: {
      memberInvite: 'admin',
      taskCreate: 'member',
      commentCreate: 'member',
    },
    notifications: {
      taskCreate: true,
      taskComplete: true,
      commentAdd: true,
    },
  },
  taskLists: [],
  metadata: {
    created: new Date().toISOString(),
    lastUpdated: new Date().toISOString(),
    completedAt: null,
    taskCount: 10,
    completedTaskCount: 5,
  },
  tags: [],
  customFields: [],
};

describe('TaskCard component', () => {
  /**
   * Group related tests for the TaskCard component
   */
  it('renders correctly with task data', () => {
    /**
     * Tests that the TaskCard renders all task information correctly
     */
    // Create mock task with title, status, priority, dueDate, assignee and project
    const task = mockTask;

    // Render TaskCard with mock task data
    render(<TaskCard task={task} />);

    // Verify task title is displayed
    expect(screen.getByText('Test Task')).toBeInTheDocument();

    // Verify task status badge is displayed
    expect(screen.getByText('In Progress')).toBeInTheDocument();

    // Verify priority badge is displayed with correct color
    expect(screen.getByText('Medium')).toBeInTheDocument();

    // Verify project name is displayed
    expect(screen.getByText('Test Project')).toBeInTheDocument();

    // Verify assignee avatar and name are displayed
    expect(screen.getByAltText('Jane Smith')).toBeInTheDocument();

    // Verify due date information is displayed
    expect(screen.getByText('Today')).toBeInTheDocument();
  });

  it('applies different class based on priority', () => {
    /**
     * Tests that the TaskCard shows correct styling based on task priority
     */
    // Create mock task with HIGH priority
    let task = { ...mockTask, priority: TaskPriority.HIGH };

    // Render TaskCard with mock task
    render(<TaskCard task={task} />);

    // Verify high priority badge is displayed with appropriate color
    expect(screen.getByText('High')).toBeInTheDocument();

    // Update mock task to have MEDIUM priority
    task = { ...mockTask, priority: TaskPriority.MEDIUM };

    // Re-render TaskCard
    render(<TaskCard task={task} />);

    // Verify medium priority badge has appropriate color
    expect(screen.getByText('Medium')).toBeInTheDocument();

    // Repeat for other priority levels
    task = { ...mockTask, priority: TaskPriority.LOW };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Low')).toBeInTheDocument();

    task = { ...mockTask, priority: TaskPriority.URGENT };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Urgent')).toBeInTheDocument();
  });

  it('displays correct status badge', () => {
    /**
     * Tests that the TaskCard shows the correct status badge based on task status
     */
    // Create mock task with IN_PROGRESS status
    let task = { ...mockTask, status: TaskStatus.IN_PROGRESS };

    // Render TaskCard with mock task
    render(<TaskCard task={task} />);

    // Verify status badge shows 'In Progress'
    expect(screen.getByText('In Progress')).toBeInTheDocument();

    // Update mock task to have COMPLETED status
    task = { ...mockTask, status: TaskStatus.COMPLETED };

    // Re-render TaskCard
    render(<TaskCard task={task} />);

    // Verify status badge shows 'Completed'
    expect(screen.getByText('Completed')).toBeInTheDocument();

    // Repeat for other status values
    task = { ...mockTask, status: TaskStatus.ASSIGNED };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Assigned')).toBeInTheDocument();

    task = { ...mockTask, status: TaskStatus.CREATED };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Not Started')).toBeInTheDocument();

    task = { ...mockTask, status: TaskStatus.ON_HOLD };
    render(<TaskCard task={task} />);
    expect(screen.getByText('On Hold')).toBeInTheDocument();

    task = { ...mockTask, status: TaskStatus.IN_REVIEW };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Review')).toBeInTheDocument();

    task = { ...mockTask, status: TaskStatus.CANCELLED };
    render(<TaskCard task={task} />);
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('shows overdue indicator for past due dates', () => {
    /**
     * Tests that the TaskCard displays overdue indicator for tasks with due dates in the past
     */
    // Create mock task with due date in the past
    let task = { ...mockTask, dueDate: '2024-01-01T12:00:00.000Z' };

    // Render TaskCard with mock task
    render(<TaskCard task={task} />);

    // Verify overdue indicator/icon is displayed
    expect(screen.getByText('Overdue')).toBeInTheDocument();

    // Verify overdue text has appropriate styling (e.g., error color)
    expect(screen.getByText('Overdue')).toHaveClass('text-red-600');

    // Update mock task with future due date
    task = { ...mockTask, dueDate: '2024-12-31T12:00:00.000Z' };

    // Re-render TaskCard
    render(<TaskCard task={task} />);

    // Verify overdue indicator is not present
    expect(screen.queryByText('Overdue')).not.toBeInTheDocument();
  });

  it('applies selected styling when selected prop is true', () => {
    /**
     * Tests that the TaskCard shows a selected state when the selected prop is true
     */
    // Create mock task data
    const task = mockTask;

    // Render TaskCard with selected prop set to true
    render(<TaskCard task={task} selected={true} />);

    // Verify TaskCard has appropriate selected state styling
    const taskCardElement = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElement).toHaveClass('border-primary-500');
    expect(taskCardElement).toHaveClass('ring-2');
    expect(taskCardElement).toHaveClass('ring-primary-500');

    // Render TaskCard with selected prop set to false
    render(<TaskCard task={task} selected={false} />);

    // Verify TaskCard does not have selected state styling
    const taskCardElementNotSelected = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElementNotSelected).toHaveClass('border-gray-200');
  });

  it('applies draggable attribute when draggable prop is true', () => {
    /**
     * Tests that the TaskCard has the HTML draggable attribute when the draggable prop is true
     */
    // Create mock task data
    const task = mockTask;

    // Render TaskCard with draggable prop set to true
    render(<TaskCard task={task} draggable={true} />);

    // Verify TaskCard has HTML draggable attribute set to true
    const taskCardElement = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElement).toHaveAttribute('draggable', 'true');

    // Render TaskCard with draggable prop set to false or undefined
    render(<TaskCard task={task} draggable={false} />);

    // Verify TaskCard does not have HTML draggable attribute set to true
    const taskCardElementNotDraggable = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElementNotDraggable).not.toHaveAttribute('draggable', 'true');
  });

  it('calls onClick handler when clicked', () => {
    /**
     * Tests that the TaskCard calls the provided onClick handler when clicked
     */
    // Create a mock onClick handler function
    const onClick = jest.fn();

    // Create mock task data
    const task = mockTask;

    // Render TaskCard with mock task and onClick handler
    render(<TaskCard task={task} onClick={onClick} />);

    // Simulate a click on the TaskCard
    const taskCardElement = screen.getByText('Test Task').closest('.task-card');
    fireEvent.click(taskCardElement);

    // Verify onClick handler was called
    expect(onClick).toHaveBeenCalled();

    // Verify onClick handler was called with the task object
    expect(onClick).toHaveBeenCalledWith(task);
  });

  it('renders in compact mode when compact prop is true', () => {
    /**
     * Tests that the TaskCard renders in a more compact layout when the compact prop is true
     */
    // Create mock task data
    const task = mockTask;

    // Render TaskCard with compact prop set to true
    render(<TaskCard task={task} compact={true} />);

    // Verify TaskCard has compact layout styling
    const taskCardElement = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElement).toHaveClass('p-2');

    // Compare with regular layout to ensure differences
    render(<TaskCard task={task} compact={false} />);
    const taskCardElementRegular = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElementRegular).toHaveClass('p-4');

    // Verify compact layout still contains essential information
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('displays due soon indicator for tasks due within 2 days', () => {
    /**
     * Tests that the TaskCard shows a due soon indicator for tasks with approaching deadlines
     */
    // Create mock task with due date 1 day in the future
    let task = { ...mockTask, dueDate: '2024-03-16T12:00:00.000Z' };

    // Render TaskCard with mock task
    render(<TaskCard task={task} />);

    // Verify due soon indicator/icon is displayed
    expect(screen.getByText('Tomorrow')).toBeInTheDocument();
    expect(screen.getByText('Tomorrow')).toHaveClass('text-amber-600');

    // Update mock task with due date 4 days in the future
    task = { ...mockTask, dueDate: '2024-03-19T12:00:00.000Z' };

    // Re-render TaskCard
    render(<TaskCard task={task} />);

    // Verify due soon indicator is not present
    expect(screen.queryByText('Tomorrow')).not.toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    /**
     * Tests that the TaskCard applies custom classNames when provided
     */
    // Create mock task data
    const task = mockTask;

    // Render TaskCard with a custom className prop
    render(<TaskCard task={task} className="custom-class" />);

    // Verify the custom class is applied along with default classes
    const taskCardElement = screen.getByText('Test Task').closest('.task-card');
    expect(taskCardElement).toHaveClass('custom-class');
  });
});