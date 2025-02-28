import React from 'react'; // react ^18.2.0
import { render, screen, waitFor, fireEvent } from '@testing-library/react'; // @testing-library/react
import userEvent from '@testing-library/user-event'; // @testing-library/user-event
import { rest } from 'msw'; // msw
import CommentSection from './CommentSection';
import server from '../../../__tests__/mocks/server';
import { createMockUser } from '../../../utils/test-utils';
import { API_BASE_URL, TASK_ENDPOINTS } from '../../../api/endpoints';

// Define mock task ID constant for use in tests
const mockTaskId = '123';

// Define mock task comments to be returned by mock API
const mockTaskComments = [
  {
    id: '1',
    content: 'This is a test comment',
    createdBy: createMockUser({ id: 'user1', firstName: 'Test', lastName: 'User' }),
    createdAt: new Date().toISOString(),
    updatedAt: null,
  },
  {
    id: '2',
    content: 'This is another test comment',
    createdBy: createMockUser({ id: 'user2', firstName: 'Another', lastName: 'User' }),
    createdAt: new Date().toISOString(),
    updatedAt: null,
  },
];

// Set up mock API response handlers using MSW
beforeAll(() => server.listen());

// Reset mock handlers after each test
afterEach(() => server.resetHandlers());

// Set up test cases for different component behaviors
describe('CommentSection', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    server.resetHandlers();
    user = userEvent.setup();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  it('displays loading state while fetching comments', async () => {
    // Mock the API to delay response for comments
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.delay(100), ctx.json([]));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Verify that a loading indicator is displayed initially
    expect(screen.getByText('Loading comments...')).toBeInTheDocument();

    // Wait for loading state to disappear when data loads
    await waitFor(() => {
      expect(screen.queryByText('Loading comments...')).not.toBeInTheDocument();
    });
  });

  it('displays list of comments when loaded', async () => {
    // Mock the API to return predefined comment data
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json(mockTaskComments));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for comments to be loaded
    await waitFor(() => {
      expect(screen.getAllByText(/test comment/i).length).toBe(2);
    });

    // Verify that all mock comments are displayed in the component
    expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    expect(screen.getByText('This is another test comment')).toBeInTheDocument();

    // Verify that comment content, author names, and timestamps are displayed correctly
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('Another User')).toBeInTheDocument();
  });

  it('displays empty state when no comments exist', async () => {
    // Mock the API to return an empty comments array
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json([]));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for comments to be loaded
    await waitFor(() => {
      expect(screen.getByText(/no comments yet/i)).toBeInTheDocument();
    });

    // Verify that an empty state message is displayed
    expect(screen.getByText(/no comments yet/i)).toBeInTheDocument();
  });

  it('displays login prompt for unauthenticated users', async () => {
    // Mock authentication state to return not authenticated
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.status(401), ctx.json({ message: 'Unauthorized' }));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByText(/please log in/i)).toBeInTheDocument();
    });

    // Verify that a login prompt message is displayed
    expect(screen.getByText(/please log in/i)).toBeInTheDocument();

    // Verify that the comment form is not displayed
    expect(screen.queryByPlaceholderText(/add a comment/i)).not.toBeInTheDocument();
  });

  it('allows adding a new comment', async () => {
    // Mock the API to handle comment submission
    const addCommentHandler = rest.post(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
      return res(ctx.status(201), ctx.json({ id: '3', content: 'New comment', createdBy: createMockUser(), createdAt: new Date().toISOString() }));
    });
    server.use(addCommentHandler);

    // Mock authentication state to return authenticated user
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json(mockTaskComments));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/add a comment/i)).toBeInTheDocument();
    });

    // Type comment text in the comment input field
    const commentInput = screen.getByPlaceholderText(/add a comment/i);
    await user.type(commentInput, 'New comment');

    // Click the submit button to add the comment
    const submitButton = screen.getByRole('button', { name: /post comment/i });
    await user.click(submitButton);

    // Verify that the addComment API was called with correct parameters
    await waitFor(() => {
      expect(addCommentHandler).toHaveBeenCalled();
    });

    // Verify that the comment input is cleared after submission
    await waitFor(() => {
      expect(commentInput).toHaveValue('');
    });

    // Verify that success message is displayed
    await waitFor(() => {
      expect(screen.getByText(/comment added/i)).toBeInTheDocument();
    });
  });

  it('handles comment submission errors', async () => {
    // Mock the API to return an error on comment submission
    server.use(
      rest.post(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'Failed to add comment' }));
      })
    );

    // Mock authentication state to return authenticated user
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json(mockTaskComments));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/add a comment/i)).toBeInTheDocument();
    });

    // Type comment text in the comment input field
    const commentInput = screen.getByPlaceholderText(/add a comment/i);
    await user.type(commentInput, 'New comment');

    // Click the submit button to add the comment
    const submitButton = screen.getByRole('button', { name: /post comment/i });
    await user.click(submitButton);

    // Verify that an error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to add comment/i)).toBeInTheDocument();
    });

    // Verify that the comment input field still contains the text
    expect(commentInput).toHaveValue('New comment');
  });

  it('prevents submission of empty comments', async () => {
    // Mock authentication state to return authenticated user
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json(mockTaskComments));
      })
    );

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/add a comment/i)).toBeInTheDocument();
    });

    // Verify that the submit button is initially disabled
    const submitButton = screen.getByRole('button', { name: /post comment/i });
    expect(submitButton).toBeDisabled();

    // Type spaces or empty string in the comment input field
    const commentInput = screen.getByPlaceholderText(/add a comment/i);
    await user.type(commentInput, '   ');

    // Verify that the submit button remains disabled
    expect(submitButton).toBeDisabled();

    // Verify that no API calls are made when clicking the disabled button
    expect(server.listHandlers().length).toBeGreaterThan(0);
  });

  it('allows editing an existing comment by the comment author', async () => {
    // Mock authentication state to return the same user as a comment author
    const mockUser = createMockUser({ id: 'user1', firstName: 'Test', lastName: 'User' });
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json([{ ...mockTaskComments[0], createdBy: mockUser }, mockTaskComments[1]]));
      })
    );

    // Mock the API to return comments and handle edit requests
    const updateCommentHandler = rest.put(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}/1`, (req, res, ctx) => {
      const { content } = req.body as { content: string };
      return res(ctx.status(200), ctx.json({ ...mockTaskComments[0], content, updatedAt: new Date().toISOString() }));
    });
    server.use(updateCommentHandler);

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for comments to load
    await waitFor(() => {
      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    });

    // Click the edit button on a comment
    const editButton = screen.getByLabelText('Edit comment');
    await user.click(editButton);

    // Verify that the comment enters edit mode with editable text
    const commentInput = await screen.findByRole('textbox', { name: 'Edit comment' });
    expect(commentInput).toHaveValue('This is a test comment');

    // Change the comment text
    await user.type(commentInput, ' - Edited');

    // Click the save button
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    // Verify that the API was called with updated content
    await waitFor(() => {
      expect(updateCommentHandler).toHaveBeenCalled();
    });

    // Verify that the comment displays the updated text
    await waitFor(() => {
      expect(screen.getByText('This is a test comment - Edited')).toBeInTheDocument();
    });
  });

  it('allows deleting a comment by the comment author', async () => {
    // Mock authentication state to return the same user as a comment author
    const mockUser = createMockUser({ id: 'user1', firstName: 'Test', lastName: 'User' });
    server.use(
      rest.get(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}`, (req, res, ctx) => {
        return res(ctx.json([{ ...mockTaskComments[0], createdBy: mockUser }, mockTaskComments[1]]));
      })
    );

    // Mock the API to return comments and handle delete requests
    const deleteCommentHandler = rest.delete(`${API_BASE_URL}${TASK_ENDPOINTS.COMMENTS(mockTaskId)}/1`, (req, res, ctx) => {
      return res(ctx.status(204));
    });
    server.use(deleteCommentHandler);

    // Render the CommentSection component with a task ID
    render(<CommentSection taskId={mockTaskId} />);

    // Wait for comments to load
    await waitFor(() => {
      expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    });

    // Click the delete button on a comment
    const deleteButton = screen.getByLabelText('Delete comment');
    await user.click(deleteButton);

    // Mock the window.confirm method
    window.confirm = jest.fn(() => true);

    // Confirm deletion in the confirmation dialog
    (window.confirm as jest.Mock).mockImplementation(() => true);

    // Verify that the API was called with correct comment ID
    await waitFor(() => {
      expect(deleteCommentHandler).toHaveBeenCalled();
    });

    // Verify that the comment is removed from the display
    await waitFor(() => {
      expect(screen.queryByText('This is a test comment')).not.toBeInTheDocument();
    });
  });
});