import React from 'react'; // react ^18.2.0
import { vi, describe, it, expect, beforeEach } from 'vitest'; // vitest ^0.34.0

import Notification from './Notification'; // The component being tested
import { 
  Notification as NotificationInterface,
  NotificationType, 
  NotificationPriority 
} from '../../../types/notification'; // Type definition for the notification object
import { render, screen, fireEvent } from '../../../utils/test-utils'; // Custom testing utilities

/**
 * Main test suite for the Notification component
 */
describe('Notification Component', () => {
  /**
   * Creates mock notification objects for testing with default values that can be overridden
   * @param overrides - Partial notification object to override
   * @returns Complete notification object with defaults and provided overrides
   */
  const createMockNotification = (overrides: Partial<NotificationInterface> = {}): NotificationInterface => {
    // Define default notification properties (id, type, title, content, etc.)
    const defaultNotification: NotificationInterface = {
      id: 'test-notification-id',
      recipientId: 'test-user-id',
      type: NotificationType.TASK_ASSIGNED,
      title: 'Test Notification',
      content: 'This is a test notification',
      priority: NotificationPriority.NORMAL,
      read: false,
      actionUrl: '/tasks/123',
      metadata: {
        created: new Date().toISOString(),
        readAt: null,
        deliveryStatus: {
          inApp: 'delivered',
          email: 'pending',
          push: 'disabled'
        },
        sourceEvent: {
          type: 'task_assigned',
          objectId: 'task-123',
          objectType: 'task'
        }
      }
    };

    // Merge provided overrides with default values
    return { ...defaultNotification, ...overrides };
  };

  /**
   * Setup function that runs before each test to reset mock functions
   */
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Individual test cases for specific component behaviors
   */
  it('should render notification title and content', () => {
    // Arrange
    const notification = createMockNotification({ title: 'Test Title', content: 'Test Content' });

    // Act
    render(<Notification notification={notification} />);

    // Assert
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should display "Mark as read" button when notification is unread and onRead is provided', () => {
    // Arrange
    const onRead = vi.fn();
    const notification = createMockNotification({ read: false });

    // Act
    render(<Notification notification={notification} onRead={onRead} />);

    // Assert
    expect(screen.getByRole('button', { name: 'Mark as read' })).toBeInTheDocument();
  });

  it('should not display "Mark as read" button when notification is read', () => {
    // Arrange
    const notification = createMockNotification({ read: true });

    // Act
    render(<Notification notification={notification} />);

    // Assert
    expect(screen.queryByRole('button', { name: 'Mark as read' })).not.toBeInTheDocument();
  });

  it('should call onRead when "Mark as read" button is clicked', () => {
    // Arrange
    const onRead = vi.fn();
    const notification = createMockNotification({ read: false, id: 'test-id' });
    render(<Notification notification={notification} onRead={onRead} />);

    // Act
    fireEvent.click(screen.getByRole('button', { name: 'Mark as read' }));

    // Assert
    expect(onRead).toHaveBeenCalledTimes(1);
    expect(onRead).toHaveBeenCalledWith('test-id');
  });

  it('should display "Dismiss" button when onDismiss is provided', () => {
    // Arrange
    const onDismiss = vi.fn();
    const notification = createMockNotification();

    // Act
    render(<Notification notification={notification} onDismiss={onDismiss} />);

    // Assert
    expect(screen.getByRole('button', { name: 'Dismiss notification' })).toBeInTheDocument();
  });

  it('should call onDismiss when "Dismiss" button is clicked', () => {
    // Arrange
    const onDismiss = vi.fn();
    const notification = createMockNotification({ id: 'test-id' });
    render(<Notification notification={notification} onDismiss={onDismiss} />);

    // Act
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss notification' }));

    // Assert
    expect(onDismiss).toHaveBeenCalledTimes(1);
    expect(onDismiss).toHaveBeenCalledWith('test-id');
  });

  it('should apply different background color based on read status', () => {
    // Arrange
    const unreadNotification = createMockNotification({ read: false });
    const readNotification = createMockNotification({ read: true });

    // Act
    const { container: unreadContainer } = render(<Notification notification={unreadNotification} />);
    const { container: readContainer } = render(<Notification notification={readNotification} />);

    // Assert
    expect(unreadContainer.firstChild).toHaveClass('bg-blue-50');
    expect(readContainer.firstChild).toHaveClass('bg-white');
  });

  it('should display priority badge for high and urgent priorities', () => {
    // Arrange
    const highPriorityNotification = createMockNotification({ priority: NotificationPriority.HIGH });
    const urgentPriorityNotification = createMockNotification({ priority: NotificationPriority.URGENT });
    const normalPriorityNotification = createMockNotification({ priority: NotificationPriority.NORMAL });

    // Act
    render(<Notification notification={highPriorityNotification} />);
    render(<Notification notification={urgentPriorityNotification} />);
    render(<Notification notification={normalPriorityNotification} />);

    // Assert
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.queryByText('normal')).not.toBeInTheDocument();
  });

  it('should call onClick when notification is clicked', () => {
    // Arrange
    const onClick = vi.fn();
    const notification = createMockNotification();
    render(<Notification notification={notification} onClick={onClick} />);

    // Act
    fireEvent.click(screen.getByRole('button', { name: `Notification: ${notification.title}` }));

    // Assert
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(onClick).toHaveBeenCalledWith(notification);
  });

  it('should navigate to actionUrl when notification is clicked and onClick is not provided', () => {
    // Arrange
    const notification = createMockNotification({ actionUrl: 'https://example.com' });
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { href: 'http://localhost', assign: vi.fn() },
    });

    // Act
    render(<Notification notification={notification} />);
    fireEvent.click(screen.getByRole('button', { name: `Notification: ${notification.title}` }));

    // Assert
    expect(window.location.href).toBe('https://example.com');
  });

  it('should handle Enter key press on notification', () => {
    // Arrange
    const onClick = vi.fn();
    const notification = createMockNotification();
    render(<Notification notification={notification} onClick={onClick} />);

    // Act
    fireEvent.keyDown(screen.getByRole('button', { name: `Notification: ${notification.title}` }), { key: 'Enter' });

    // Assert
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should handle Space key press on notification', () => {
    // Arrange
    const onClick = vi.fn();
    const notification = createMockNotification();
    render(<Notification notification={notification} onClick={onClick} />);

    // Act
    fireEvent.keyDown(screen.getByRole('button', { name: `Notification: ${notification.title}` }), { key: ' ' });

    // Assert
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});