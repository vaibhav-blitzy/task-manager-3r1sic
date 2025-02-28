import React, { useState, useEffect } from 'react';
import classNames from 'classnames'; // v2.3.2
import { FiEdit2, FiTrash2 } from 'react-icons/fi'; // v4.10.0

import Avatar from '../../atoms/Avatar/Avatar';
import Button from '../../atoms/Button/Button';
import Icon from '../../atoms/Icon/Icon';
import { TaskComment } from '../../../types/task';
import { User } from '../../../types/user';
import { formatDate } from '../../../utils/date';
import useAuth from '../../../api/hooks/useAuth';

/**
 * Props interface for the CommentItem component
 */
interface CommentItemProps {
  /** The comment data to display */
  comment: TaskComment;
  /** Optional callback for updating the comment */
  onUpdate?: (id: string, content: string) => void;
  /** Optional callback for deleting the comment */
  onDelete?: (id: string) => void;
  /** Optional additional CSS class name */
  className?: string;
}

/**
 * A component that displays an individual comment with author information,
 * content, and action buttons for editing and deleting.
 */
const CommentItem: React.FC<CommentItemProps> = ({
  comment,
  onUpdate,
  onDelete,
  className
}) => {
  const { user: currentUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(comment.content);
  
  // Reset edited content when comment changes
  useEffect(() => {
    setEditedContent(comment.content);
    setIsEditing(false);
  }, [comment.id, comment.content]);
  
  // Check if current user is the author of the comment
  const isAuthor = currentUser?.id === comment.createdBy.id;
  
  // Format the comment timestamp
  const formattedDate = formatDate(comment.createdAt);
  const wasEdited = comment.updatedAt && comment.createdAt !== comment.updatedAt;
  
  /**
   * Handle edit button click
   */
  const handleEditClick = () => {
    if (!onUpdate) return;
    setEditedContent(comment.content);
    setIsEditing(true);
  };
  
  /**
   * Handle cancel edit button click
   */
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedContent(comment.content);
  };
  
  /**
   * Handle save edit button click
   */
  const handleSaveEdit = () => {
    if (onUpdate && editedContent.trim() !== '' && editedContent !== comment.content) {
      onUpdate(comment.id, editedContent);
    }
    setIsEditing(false);
  };
  
  /**
   * Handle delete button click with confirmation
   */
  const handleDeleteClick = () => {
    if (!onDelete) return;
    
    if (typeof window !== 'undefined' && window.confirm('Are you sure you want to delete this comment?')) {
      onDelete(comment.id);
    }
  };
  
  return (
    <div className={classNames(
      'flex space-x-3 p-4 rounded-md bg-white border border-gray-200',
      'hover:border-gray-300 transition-all duration-200',
      className
    )}>
      {/* User avatar */}
      <div className="flex-shrink-0">
        <Avatar user={comment.createdBy} size="sm" />
      </div>
      
      {/* Comment content */}
      <div className="flex-1 min-w-0">
        {/* Comment header with author and timestamp */}
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-gray-900">
            {comment.createdBy.firstName} {comment.createdBy.lastName}
          </div>
          <div className="text-xs text-gray-500 flex items-center">
            {formattedDate}
            {wasEdited && (
              <span className="ml-1 text-gray-400 italic">(edited)</span>
            )}
          </div>
        </div>
        
        {/* Comment content - editable when in edit mode */}
        {isEditing ? (
          <div className="mt-2">
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              rows={3}
              autoFocus
              aria-label="Edit comment"
            />
            <div className="mt-2 flex justify-end space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleCancelEdit}
              >
                Cancel
              </Button>
              <Button 
                variant="primary" 
                size="sm" 
                onClick={handleSaveEdit}
                disabled={editedContent.trim() === '' || editedContent === comment.content}
              >
                Save
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap break-words">
            {comment.content}
          </div>
        )}
      </div>
      
      {/* Action buttons - only shown if user is the author and not in edit mode */}
      {isAuthor && !isEditing && (
        <div className="flex-shrink-0 flex space-x-2">
          {onUpdate && (
            <button
              type="button"
              className="text-gray-400 hover:text-primary-500 focus:outline-none focus:text-primary-500 transition-colors"
              onClick={handleEditClick}
              aria-label="Edit comment"
              title="Edit comment"
            >
              <Icon icon={FiEdit2} size={16} />
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              className="text-gray-400 hover:text-red-500 focus:outline-none focus:text-red-500 transition-colors"
              onClick={handleDeleteClick}
              aria-label="Delete comment"
              title="Delete comment"
            >
              <Icon icon={FiTrash2} size={16} />
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default CommentItem;