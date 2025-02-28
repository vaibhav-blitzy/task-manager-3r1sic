import React from 'react'; // react ^18.2.0
import { describe, beforeEach, afterEach, test, expect } from '@jest/globals'; // @jest/globals ^29.5.0
import { rest } from 'msw'; // msw ^1.2.1
import {
  render,
  screen,
  waitFor,
  fireEvent,
  within,
  userEvent,
} from '../../utils/test-utils';
import { server } from '../../__tests__/mocks/server';
import NotificationCenter from './NotificationCenter';
import { NOTIFICATION_ENDPOINTS } from '../../api/endpoints';
import {
  Notification,
  NotificationType,
} from '../../types/notification';
import { createMockUser } from '../../utils/test-utils';

describe('NotificationCenter component', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  test('renders notification center with loading state', async () => {
    server.use(
      rest.get(NOTIFICATION_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.delay(100), ctx.json([]));
      })
    );

    render(<NotificationCenter />);

    expect(screen.getByText('Loading notifications...')).toBeInTheDocument();
  });

  test('displays notifications when loaded', async () => {
    const mockNotifications: Notification[] = createMockNotifications(3);

    mockNotificationsResponse(mockNotifications, {});

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    mockNotifications.forEach((notification) => {
      expect(screen.getByText(notification.title)).toBeInTheDocument();
      expect(screen.getByText(notification.content)).toBeInTheDocument();
    });
  });

  test('displays empty state when no notifications', async () => {
    mockNotificationsResponse([], {});

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    expect(screen.getByText('No notifications found.')).toBeInTheDocument();
  });

  test('handles marking a notification as read', async () => {
    const mockNotifications: Notification[] = createMockNotifications(1);
    mockNotifications[0].read = false;

    mockNotificationsResponse(mockNotifications, {});

    const markReadHandler = rest.patch(
      NOTIFICATION_ENDPOINTS.MARK_READ(mockNotifications[0].id),
      (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ ...mockNotifications[0], read: true }));
      }
    );

    server.use(markReadHandler);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const markAsReadButton = screen.getByRole('button', { name: /mark as read/i });
    fireEvent.click(markAsReadButton);

    await waitFor(() => {
      expect(markReadHandler).toHaveBeenCalled();
    });
  });

  test('handles marking all notifications as read', async () => {
    const mockNotifications: Notification[] = createMockNotifications(2);
    mockNotifications.forEach(notification => notification.read = false);

    mockNotificationsResponse(mockNotifications, {});

    const markAllReadHandler = rest.post(
      NOTIFICATION_ENDPOINTS.MARK_ALL_READ,
      (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({ success: true }));
      }
    );

    server.use(markAllReadHandler);

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const markAllAsReadButton = screen.getByRole('button', { name: /mark all as read/i });
    fireEvent.click(markAllAsReadButton);

    await waitFor(() => {
      expect(markAllReadHandler).toHaveBeenCalled();
    });
  });

  test('allows filtering notifications by type', async () => {
    const mockNotifications: Notification[] = [
      ...createMockNotifications(1, { type: NotificationType.TASK_ASSIGNED }),
      ...createMockNotifications(1, { type: NotificationType.COMMENT_ADDED }),
    ];

    mockNotificationsResponse(mockNotifications, {});

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const typeFilterSelect = screen.getByLabelText(/type:/i);
    fireEvent.change(typeFilterSelect, { target: { value: NotificationType.TASK_ASSIGNED } });

    await waitFor(() => {
      expect(screen.getAllByText(/task assigned to you/i)).toHaveLength(1);
    });
  });

  test('allows filtering notifications by read status', async () => {
    const mockNotifications: Notification[] = [
      ...createMockNotifications(1, { read: true }),
      ...createMockNotifications(1, { read: false }),
    ];

    mockNotificationsResponse(mockNotifications, {});

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const readStatusFilterSelect = screen.getByLabelText(/status:/i);
    fireEvent.change(readStatusFilterSelect, { target: { value: 'unread' } });

    await waitFor(() => {
      expect(screen.getAllByText(/task assigned to you/i)).toHaveLength(1);
    });
  });

  test('implements pagination correctly', async () => {
    const mockNotifications: Notification[] = createMockNotifications(25);

    mockNotificationsResponse(mockNotifications, { total: 25, page: 1, limit: 10, totalPages: 3 });

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const nextPageButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextPageButton);

    await waitFor(() => {
      expect(screen.getAllByText(/task assigned to you/i)).toHaveLength(10);
    });
  });

  test('shows error state on API failure', async () => {
    server.use(
      rest.get(NOTIFICATION_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'API Error' }));
      })
    );

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    expect(screen.getByText(/error:/i)).toBeInTheDocument();
  });

  test('allows navigating to related content from notifications', async () => {
    const mockNotifications: Notification[] = createMockNotifications(1, { actionUrl: '/tasks/123' });

    mockNotificationsResponse(mockNotifications, {});

    render(<NotificationCenter />);

    await waitFor(() => {
      expect(screen.queryByText('Loading notifications...')).not.toBeInTheDocument();
    });

    const notificationElement = screen.getByText(/task assigned to you/i);
    fireEvent.click(notificationElement);
  });

  function createMockNotifications(count: number, overrides: Partial<Notification> = {}): Notification[] {
    return Array.from({ length: count }, (_, i) => ({
      id: `notification-${i + 1}`,
      recipientId: createMockUser().id,
      type: NotificationType.TASK_ASSIGNED,
      title: 'Task Assigned to You',
      content: 'You have been assigned to "Complete project documentation"',
      priority: 'normal',
      read: false,
      actionUrl: '/tasks/123',
      metadata: {
        created: new Date().toISOString(),
        readAt: null,
        deliveryStatus: {
          inApp: 'delivered',
          email: 'delivered',
          push: 'disabled',
        },
        sourceEvent: {
          type: 'task.assigned',
          objectId: '123',
          objectType: 'task',
        },
      },
      ...overrides,
    }));
  }

  function mockNotificationsResponse(notifications: Notification[], paginationInfo: object) {
    server.use(
      rest.get(NOTIFICATION_ENDPOINTS.BASE, (req, res, ctx) => {
        return res(ctx.status(200), ctx.json({
          items: notifications,
          total: notifications.length,
          page: 1,
          limit: 10,
          totalPages: 1,
          ...paginationInfo,
        }));
      })
    );
  }
});