import React, { useState, useCallback } from 'react';
import classNames from 'classnames';

import CommentItem from '../../molecules/CommentItem/CommentItem';
import { Button } from '../../atoms/Button/Button';
import Avatar from '../../atoms/Avatar/Avatar';

import useAuth from '../../../api/hooks/useAuth';
import { useTaskComments } from '../../../api/hooks/useTasks';
import { TaskComment, CommentCreate } from '../../../types/task';
import { User } from '../../../types/user';
import { formatDate } from '../../../utils/date';

interface CommentSectionProps {
  taskId: string;
  className?: string;
}

const CommentSection: React.FC<CommentSectionProps> = ({ taskId, className }) => {
  const { user, isAuthenticated } = useAuth();
  const { 
    comments, 
    isLoading, 
    error: commentsError, 
    addComment,
    isAddingComment 
  } = useTaskComments(taskId);
  
  const [commentText, setCommentText] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const handleSubmit = useCallback(async () => {
    if (!commentText.trim() || !isAuthenticated || !user) return;
    
    setError(null);
    
    try {
      const newComment: CommentCreate = {
        content: commentText.trim()
      };
      
      await addComment(newComment);
      setCommentText('');
    } catch (err) {
      setError(typeof err === 'string' ? err : 'Failed to add comment. Please try again.');
      console.error('Error adding comment:', err);
    }
  }, [commentText, addComment, isAuthenticated, user]);
  
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Ctrl+Enter or Command+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);
  
  const handleCommentUpdate = useCallback((id: string, content: string) => {
    // Implementation for updating comments would go here
    // This would call an API endpoint to update the comment
    console.log('Update comment:', id, content);
  }, []);
  
  const handleCommentDelete = useCallback((id: string) => {
    // Implementation for deleting comments would go here
    // This would call an API endpoint to delete the comment
    console.log('Delete comment:', id);
  }, []);
  
  return (
    <div className={classNames('comment-section', className)}>
      <h3 className="text-lg font-medium mb-4">Comments</h3>
      
      {isLoading ? (
        <div className="flex justify-center py-6">
          <div className="animate-pulse text-gray-500">Loading comments...</div>
        </div>
      ) : commentsError ? (
        <div className="bg-red-50 p-4 text-center rounded-md text-red-600">
          Error loading comments: {commentsError instanceof Error ? commentsError.message : String(commentsError)}
        </div>
      ) : !isAuthenticated ? (
        <div className="bg-gray-50 p-4 text-center rounded-md text-gray-600">
          Please log in to view and add comments
        </div>
      ) : (
        <>
          {(!comments || comments.length === 0) ? (
            <div className="bg-gray-50 p-4 text-center rounded-md text-gray-600">
              No comments yet. Be the first to add a comment!
            </div>
          ) : (
            <div className="space-y-4 mb-6">
              {comments.map((comment: TaskComment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onUpdate={handleCommentUpdate}
                  onDelete={handleCommentDelete}
                />
              ))}
            </div>
          )}
          
          {isAuthenticated && user && (
            <div className="mt-6">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <Avatar user={user} size="sm" />
                </div>
                <div className="flex-1">
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Add a comment..."
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={3}
                    aria-label="Comment text"
                  />
                  
                  {error && (
                    <div className="text-red-500 text-sm mt-1">{error}</div>
                  )}
                  
                  <div className="mt-2 flex justify-end">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSubmit}
                      disabled={!commentText.trim() || isAddingComment}
                    >
                      {isAddingComment ? 'Posting...' : 'Post Comment'}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default CommentSection;