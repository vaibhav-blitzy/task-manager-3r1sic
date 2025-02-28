import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CommentItem from './CommentItem';

// Mock the useAuth hook
vi.mock('../../../api/hooks/useAuth', () => ({
  default: () => ({
    user: { id: 'current-user-id' } // The current user for testing author-specific functionality
  })
}));

// Mock the dependencies
vi.mock('../../atoms/Avatar/Avatar', () => ({
  default: (props) => <div data-testid="mock-avatar">{props.user.firstName} {props.user.lastName}</div>
}));

vi.mock('../../atoms/Button/Button', () => ({
  default: ({ children, onClick, variant, size, disabled }) => (
    <button 
      onClick={onClick}
      disabled={disabled}
      data-testid="mock-button"
      data-variant={variant}
      data-size={size}
    >
      {children}
    </button>
  )
}));

vi.mock('../../atoms/Icon/Icon', () => ({
  default: ({ icon: Icon, size }) => <div data-testid="mock-icon" data-size={size} />
}));

describe('CommentItem', () => {
  // Sample comment data
  const mockComment = {
    id: 'comment-1',
    content: 'This is a test comment',
    createdBy: {
      id: 'current-user-id', // Same as the mocked current user
      firstName: 'John',
      lastName: 'Doe'
    },
    createdAt: '2023-01-01T10:00:00Z',
    updatedAt: '2023-01-01T10:00:00Z' // Same as created (not edited)
  };

  // Mock update and delete callbacks
  const mockOnUpdate = vi.fn();
  const mockOnDelete = vi.fn();
  
  // Store original window.confirm
  const originalConfirm = window.confirm;

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true); // Mock confirm to return true by default
  });

  afterAll(() => {
    // Restore original window.confirm after all tests
    window.confirm = originalConfirm;
  });

  it('renders comment information correctly', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    expect(screen.getByTestId('mock-avatar')).toBeInTheDocument();
  });

  it('displays edit and delete buttons for comment author', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    expect(screen.getByLabelText('Edit comment')).toBeInTheDocument();
    expect(screen.getByLabelText('Delete comment')).toBeInTheDocument();
  });

  it('does not display edit and delete buttons for non-authors', () => {
    // Create a different user as the comment author
    const nonAuthorComment = {
      ...mockComment,
      createdBy: {
        id: 'different-user-id',
        firstName: 'Jane',
        lastName: 'Smith'
      }
    };
    
    render(<CommentItem comment={nonAuthorComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    expect(screen.queryByLabelText('Edit comment')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Delete comment')).not.toBeInTheDocument();
  });

  it('shows (edited) text when comment was updated', () => {
    const editedComment = {
      ...mockComment,
      updatedAt: '2023-01-01T11:00:00Z' // Different from createdAt
    };
    
    render(<CommentItem comment={editedComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('(edited)')).toBeInTheDocument();
  });

  it('enters edit mode when edit button is clicked', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveValue('This is a test comment');
  });

  it('handles canceling an edit', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Enter edit mode
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    // Change the content
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Updated comment text' } });
    
    // Click cancel
    fireEvent.click(screen.getByText('Cancel'));
    
    // Verify edit mode is exited and content is not changed
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    expect(mockOnUpdate).not.toHaveBeenCalled();
  });

  it('handles saving an edit', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Enter edit mode
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    // Change the content
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Updated comment text' } });
    
    // Click save
    fireEvent.click(screen.getByText('Save'));
    
    // Verify callback was called correctly
    expect(mockOnUpdate).toHaveBeenCalledWith('comment-1', 'Updated comment text');
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('does not call onUpdate if content is unchanged', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Enter edit mode
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    // Don't change the content and save
    fireEvent.click(screen.getByText('Save'));
    
    expect(mockOnUpdate).not.toHaveBeenCalled();
  });

  it('does not call onUpdate if content is empty', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Enter edit mode
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    // Change to empty string
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '' } });
    
    // Click save
    fireEvent.click(screen.getByText('Save'));
    
    expect(mockOnUpdate).not.toHaveBeenCalled();
  });

  it('handles deleting a comment with confirmation', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    fireEvent.click(screen.getByLabelText('Delete comment'));
    
    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this comment?');
    expect(mockOnDelete).toHaveBeenCalledWith('comment-1');
  });

  it('does not delete when confirmation is canceled', () => {
    window.confirm = vi.fn(() => false);
    
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    fireEvent.click(screen.getByLabelText('Delete comment'));
    
    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this comment?');
    expect(mockOnDelete).not.toHaveBeenCalled();
  });

  it('does not show edit button when onUpdate is not provided', () => {
    render(<CommentItem comment={mockComment} onDelete={mockOnDelete} />);
    
    expect(screen.queryByLabelText('Edit comment')).not.toBeInTheDocument();
  });

  it('does not show delete button when onDelete is not provided', () => {
    render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} />);
    
    expect(screen.queryByLabelText('Delete comment')).not.toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    const { container } = render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={mockOnUpdate} 
        onDelete={mockOnDelete} 
        className="custom-class"
      />
    );
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('resets edit state when comment prop changes', () => {
    const { rerender } = render(<CommentItem comment={mockComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Enter edit mode
    fireEvent.click(screen.getByLabelText('Edit comment'));
    
    // Verify edit mode is active
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    
    // Update with new comment
    const newComment = {
      ...mockComment,
      id: 'comment-2',
      content: 'A different comment'
    };
    
    rerender(<CommentItem comment={newComment} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />);
    
    // Verify edit mode is exited
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByText('A different comment')).toBeInTheDocument();
  });
});