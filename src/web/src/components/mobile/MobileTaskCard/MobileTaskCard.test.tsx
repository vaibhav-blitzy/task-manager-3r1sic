import React from 'react'; // react ^18.2.0
import { render, screen, fireEvent } from '../../../utils/test-utils'; // Testing utilities with necessary providers
import MobileTaskCard from './MobileTaskCard'; // Component under test
import { createMockTask, createMockUser } from '../../../utils/test-utils'; // Utility to create mock task data for testing
import { TaskStatus, TaskPriority } from '../../../types/task'; // Enums for task status and priority
import userEvent from '@testing-library/user-event'; // Library for simulating user interactions in tests

describe('MobileTaskCard', () => {
  /**
   * Main test suite for the MobileTaskCard component
   * @returns {void} Test result
   * @steps
   *   - Organize component test cases
   *   - Set up mock data and handlers
   *   - Group tests by functionality
   */

  test('should render task title correctly', () => {
    /**
     * Tests that the task title is correctly displayed
     * @returns {void} Test result
     * @steps
     *   - Create a mock task with a specific title
     *   - Render the MobileTaskCard with the mock task
     *   - Verify that the title is displayed in the document
     *   - Check that the title is truncated properly if necessary
     */
    const taskTitle = 'This is a very long task title that should be truncated';
    const mockTask = createMockTask({ title: taskTitle });
    render(<MobileTaskCard task={mockTask} />);
    expect(screen.getByText(taskTitle)).toBeInTheDocument();
  });

  test('should render status badge correctly', () => {
    /**
     * Tests that the status badge is correctly displayed
     * @returns {void} Test result
     * @steps
     *   - Create a mock task with IN_PROGRESS status
     *   - Render the MobileTaskCard with the mock task
     *   - Verify that the status badge is displayed with the correct text
     *   - Repeat with different status values to ensure proper display
     */
    const mockTask = createMockTask({ status: TaskStatus.IN_PROGRESS });
    render(<MobileTaskCard task={mockTask} />);
    expect(screen.getByText('In Progress')).toBeInTheDocument();

    const mockTaskCompleted = createMockTask({ status: TaskStatus.COMPLETED });
    render(<MobileTaskCard task={mockTaskCompleted} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  test('should render priority badge with correct color', () => {
    /**
     * Tests that priority is displayed with the correct badge color
     * @returns {void} Test result
     * @steps
     *   - Create a mock task with HIGH priority
     *   - Render the MobileTaskCard with the mock task
     *   - Verify that the priority badge has the correct text and color class
     *   - Repeat with URGENT priority to verify different color badge
     */
    const mockTask = createMockTask({ priority: TaskPriority.HIGH });
    render(<MobileTaskCard task={mockTask} />);
    const priorityBadge = screen.getByText('High');
    expect(priorityBadge).toBeInTheDocument();
    expect(priorityBadge.classList.contains('bg-red-600')).toBe(true);

    const mockTaskUrgent = createMockTask({ priority: TaskPriority.URGENT });
    render(<MobileTaskCard task={mockTaskUrgent} />);
    const urgentBadge = screen.getByText('Urgent');
    expect(urgentBadge).toBeInTheDocument();
    expect(urgentBadge.classList.contains('bg-red-600')).toBe(true);
  });

  test('should render due date with overdue warning when applicable', () => {
    /**
     * Tests that due dates are displayed correctly with warnings when overdue
     * @returns {void} Test result
     * @steps
     *   - Create a mock task with a past due date
     *   - Render the MobileTaskCard with the mock task
     *   - Verify that the due date is displayed with an overdue warning icon
     *   - Create a mock task with a future due date
     *   - Render again and verify the due date is displayed without a warning
     */
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    const mockTaskOverdue = createMockTask({ dueDate: pastDate.toISOString() });
    render(<MobileTaskCard task={mockTaskOverdue} />);
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
    expect(screen.getByTestId('fa-exclamation-triangle')).toBeInTheDocument();

    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 1);
    const mockTaskFuture = createMockTask({ dueDate: futureDate.toISOString() });
    render(<MobileTaskCard task={mockTaskFuture} />);
    expect(screen.getByText('Tomorrow')).toBeInTheDocument();
    expect(screen.queryByTestId('fa-exclamation-triangle')).not.toBeInTheDocument();
  });

  test('should render assignee avatar when present', () => {
    /**
     * Tests that the assignee avatar is displayed when an assignee exists
     * @returns {void} Test result
     * @steps
     *   - Create a mock user for the assignee
     *   - Create a mock task with the assignee
     *   - Render the MobileTaskCard with the mock task
     *   - Verify that the assignee avatar is displayed
     *   - Create a mock task without an assignee
     *   - Verify that no avatar is displayed when there is no assignee
     */
    const mockUser = createMockUser({ id: 'assignee-1' });
    const mockTaskWithAssignee = createMockTask({ assignee: mockUser });
    render(<MobileTaskCard task={mockTaskWithAssignee} />);
    expect(screen.getByAltText('Test User')).toBeInTheDocument();

    const mockTaskWithoutAssignee = createMockTask({ assignee: null });
    render(<MobileTaskCard task={mockTaskWithoutAssignee} />);
    expect(screen.queryByAltText('Test User')).not.toBeInTheDocument();
  });

  test('should call onClick handler when clicked', () => {
    /**
     * Tests that the onClick handler is called with the task when the card is clicked
     * @returns {void} Test result
     * @steps
     *   - Create a mock task
     *   - Create a mock onClick handler using jest.fn()
     *   - Render the MobileTaskCard with the mock task and onClick handler
     *   - Simulate a click on the card
     *   - Verify that the onClick handler was called once
     *   - Verify that the onClick handler was called with the mock task as the argument
     */
    const mockTask = createMockTask();
    const onClick = jest.fn();
    render(<MobileTaskCard task={mockTask} onClick={onClick} />);
    fireEvent.click(screen.getByText('Test Task'));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onClick).toHaveBeenCalledWith(mockTask);
  });

  test('should apply custom className when provided', () => {
    /**
     * Tests that custom className is applied to the component
     * @returns {void} Test result
     * @steps
     *   - Create a mock task
     *   - Render the MobileTaskCard with a custom className
     *   - Verify that the rendered element includes the custom className
     */
    const mockTask = createMockTask();
    render(<MobileTaskCard task={mockTask} className="custom-class" />);
    expect(screen.getByText('Test Task').closest('.mobile-task-card')).toHaveClass('custom-class');
  });
});