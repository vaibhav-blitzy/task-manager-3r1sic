import React from 'react';
import classNames from 'classnames'; // version 2.3.0
import { FaClock, FaExclamationTriangle } from 'react-icons/fa'; // version 4.10.0

import { Task, TaskStatus, TaskPriority } from '../../../types/task';
import StatusBadge from '../../molecules/StatusBadge/StatusBadge';
import Avatar from '../../atoms/Avatar/Avatar';
import { Badge, BadgeColor } from '../../atoms/Badge/Badge';
import { formatDate, isOverdue, isDueSoon, getRelativeDateLabel } from '../../../utils/date';

interface MobileTaskCardProps {
  task: Task;
  onClick?: (task: Task) => void;
  className?: string;
}

/**
 * Maps task priority to appropriate badge color for mobile display
 */
const getPriorityColor = (priority: TaskPriority): BadgeColor => {
  switch (priority) {
    case TaskPriority.HIGH:
    case TaskPriority.URGENT:
      return BadgeColor.ERROR;
    case TaskPriority.MEDIUM:
      return BadgeColor.WARNING;
    case TaskPriority.LOW:
      return BadgeColor.INFO;
    default:
      return BadgeColor.NEUTRAL;
  }
};

/**
 * Formats task due date for mobile display with appropriate indicator
 */
const getDueDateDisplay = (dueDate: string | null | undefined) => {
  if (!dueDate) {
    return { label: '', isOverdue: false, isDueSoon: false };
  }

  const overdue = isOverdue(dueDate);
  const dueSoon = !overdue && isDueSoon(dueDate, 2); // Due within 2 days
  const label = getRelativeDateLabel(dueDate);

  return { label, isOverdue: overdue, isDueSoon: dueSoon };
};

/**
 * Mobile-optimized card component for displaying task information on smaller screens
 */
const MobileTaskCard: React.FC<MobileTaskCardProps> = ({ task, onClick, className }) => {
  const { title, status, priority, dueDate, assignee } = task;
  const { label: dueDateLabel, isOverdue: isTaskOverdue, isDueSoon: isTaskDueSoon } = getDueDateDisplay(dueDate);
  const priorityColor = getPriorityColor(priority);

  return (
    <div 
      className={classNames(
        'mobile-task-card p-4 bg-white rounded-lg shadow-sm border border-gray-100 mb-3',
        'min-h-[5rem]', // Minimum height for better touch target
        { 'active:bg-gray-50 cursor-pointer': !!onClick }, // Touch feedback when clickable
        className
      )}
      onClick={onClick ? () => onClick(task) : undefined}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={onClick ? `View task: ${title}` : undefined}
    >
      <div className="flex flex-col">
        {/* Task title */}
        <h3 className="text-base font-medium text-gray-900 truncate mb-2">{title}</h3>
        
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {/* Status badge */}
          <StatusBadge status={status} size="sm" showIcon={true} />
          
          {/* Priority badge */}
          <Badge color={priorityColor} size="sm">
            {priority.charAt(0).toUpperCase() + priority.slice(1).toLowerCase()}
          </Badge>
        </div>
        
        <div className="flex justify-between items-center mt-2">
          {/* Due date with warning icon if needed */}
          {dueDateLabel && (
            <div className={classNames(
              'flex items-center text-sm py-1', // Increase touch target height
              { 'text-red-500': isTaskOverdue },
              { 'text-amber-500': isTaskDueSoon && !isTaskOverdue },
              { 'text-gray-500': !isTaskOverdue && !isTaskDueSoon }
            )}>
              {isTaskOverdue ? (
                <FaExclamationTriangle className="mr-1" size={12} aria-hidden="true" />
              ) : (
                <FaClock className="mr-1" size={12} aria-hidden="true" />
              )}
              <span className={isTaskOverdue ? 'font-medium' : ''}>
                {dueDateLabel}
              </span>
            </div>
          )}
          
          {/* Assignee avatar */}
          {assignee && (
            <Avatar 
              user={assignee} 
              size="sm" 
              className="ml-auto"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default MobileTaskCard;
export type { MobileTaskCardProps };