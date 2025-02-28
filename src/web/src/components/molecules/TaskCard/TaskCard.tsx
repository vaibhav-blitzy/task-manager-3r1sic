import React from 'react';
import classNames from 'classnames'; // version 2.3.0
import { FaClock, FaExclamationTriangle } from 'react-icons/fa'; // version 4.10.0
import { Task, TaskPriority, TaskStatus } from '../../../types/task';
import StatusBadge from '../../molecules/StatusBadge/StatusBadge';
import Avatar from '../../atoms/Avatar/Avatar';
import { Badge, BadgeColor } from '../../atoms/Badge/Badge';
import { formatDate, isOverdue, isDueSoon, getRelativeDateLabel } from '../../../utils/date';

interface TaskCardProps {
  /** The task data to display */
  task: Task;
  /** Optional click handler when the card is clicked */
  onClick?: (task: Task) => void;
  /** Additional CSS class names */
  className?: string;
  /** Whether to use compact layout */
  compact?: boolean;
  /** Whether the card is draggable */
  draggable?: boolean;
  /** Whether the card is selected */
  selected?: boolean;
}

/**
 * Maps task priority to appropriate badge color
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
 * Formats the priority value for display
 */
const getPriorityLabel = (priority: TaskPriority): string => {
  return priority.charAt(0).toUpperCase() + priority.slice(1).toLowerCase();
};

/**
 * Formats task due date for display with appropriate indicator
 */
const getDueDateDisplay = (dueDate: string | null | undefined) => {
  if (!dueDate) {
    return { label: '', isOverdue: false, isDueSoon: false };
  }

  const isTaskOverdue = isOverdue(dueDate);
  const isTaskDueSoon = !isTaskOverdue && isDueSoon(dueDate);
  const label = getRelativeDateLabel(dueDate);

  return {
    label,
    isOverdue: isTaskOverdue,
    isDueSoon: isTaskDueSoon
  };
};

/**
 * Component that displays a task card with task information and styling
 */
const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onClick,
  className = '',
  compact = false,
  draggable = false,
  selected = false
}) => {
  const { title, status, priority, dueDate, assignee, project } = task;
  const dueDateDisplay = getDueDateDisplay(dueDate);
  const priorityColor = getPriorityColor(priority);
  const priorityLabel = getPriorityLabel(priority);

  const cardClasses = classNames(
    'task-card',
    'bg-white',
    'border',
    'rounded-md',
    'shadow-sm',
    'transition-all',
    'hover:shadow',
    'relative',
    'overflow-hidden',
    {
      'p-4': !compact,
      'p-2': compact,
      'cursor-pointer': !!onClick,
      'border-primary-500 ring-2 ring-primary-500': selected,
      'border-gray-200': !selected
    },
    className
  );

  return (
    <div 
      className={cardClasses}
      onClick={onClick ? () => onClick(task) : undefined}
      draggable={draggable}
      aria-selected={selected}
    >
      <div className={classNames('flex flex-col', { 'gap-3': !compact, 'gap-1': compact })}>
        {/* Task Title */}
        <h3 
          className={classNames(
            'font-semibold text-neutral-900 truncate', 
            { 'text-sm': compact, 'text-base': !compact }
          )} 
          title={title}
        >
          {title}
        </h3>
        
        {/* Status and metadata */}
        <div className={classNames('flex flex-wrap', { 'gap-2': !compact, 'gap-1': compact })}>
          <StatusBadge 
            status={status} 
            size={compact ? 'sm' : 'md'} 
          />
          
          <Badge 
            color={priorityColor} 
            size={compact ? 'sm' : 'md'}
          >
            {priorityLabel}
          </Badge>
          
          {project && (
            <Badge 
              color={BadgeColor.NEUTRAL} 
              size={compact ? 'sm' : 'md'}
            >
              {project.name}
            </Badge>
          )}
        </div>
        
        {/* Footer: Due date and assignee */}
        <div className="flex items-center justify-between mt-auto">
          {dueDateDisplay.label && (
            <div className={classNames(
              'flex items-center text-xs',
              {
                'text-red-600': dueDateDisplay.isOverdue,
                'text-amber-600': dueDateDisplay.isDueSoon,
                'text-gray-500': !dueDateDisplay.isOverdue && !dueDateDisplay.isDueSoon
              }
            )}>
              {dueDateDisplay.isOverdue ? (
                <FaExclamationTriangle className="mr-1" size={12} />
              ) : (
                <FaClock className="mr-1" size={12} />
              )}
              <span>{dueDateDisplay.label}</span>
            </div>
          )}
          
          {assignee && (
            <Avatar 
              user={assignee}
              size={compact ? 'sm' : 'md'}
              className="ml-auto"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskCard;
export type { TaskCardProps };