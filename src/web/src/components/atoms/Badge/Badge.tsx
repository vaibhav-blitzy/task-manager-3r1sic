import React from 'react';
import classnames from 'classnames'; // version 2.3.x

export enum BadgeColor {
  PRIMARY = 'primary',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
  INFO = 'info',
  NEUTRAL = 'neutral'
}

export enum BadgeSize {
  SMALL = 'sm',
  MEDIUM = 'md',
  LARGE = 'lg'
}

export interface BadgeProps {
  children: React.ReactNode;
  color?: BadgeColor;
  size?: BadgeSize;
  outlined?: boolean;
  rounded?: boolean;
  className?: string;
  onClick?: () => void;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  color = BadgeColor.NEUTRAL,
  size = BadgeSize.MEDIUM,
  outlined = false,
  rounded = true,
  className = '',
  onClick
}) => {
  // Determine color classes based on color prop and outlined state
  const colorClasses = {
    [BadgeColor.PRIMARY]: outlined 
      ? 'text-primary-700 bg-transparent border border-primary-700' 
      : 'text-white bg-primary-700',
    [BadgeColor.SUCCESS]: outlined 
      ? 'text-green-600 bg-transparent border border-green-600' 
      : 'text-white bg-green-600',
    [BadgeColor.WARNING]: outlined 
      ? 'text-amber-600 bg-transparent border border-amber-600' 
      : 'text-white bg-amber-600',
    [BadgeColor.ERROR]: outlined 
      ? 'text-red-600 bg-transparent border border-red-600' 
      : 'text-white bg-red-600',
    [BadgeColor.INFO]: outlined 
      ? 'text-blue-600 bg-transparent border border-blue-600' 
      : 'text-white bg-blue-600',
    [BadgeColor.NEUTRAL]: outlined 
      ? 'text-gray-700 bg-transparent border border-gray-700' 
      : 'text-gray-700 bg-gray-200',
  };

  // Determine size classes
  const sizeClasses = {
    [BadgeSize.SMALL]: 'text-xs px-1.5 py-0.5',
    [BadgeSize.MEDIUM]: 'text-sm px-2 py-1',
    [BadgeSize.LARGE]: 'text-base px-2.5 py-1.5',
  };

  // Determine rounded classes
  const roundedClasses = rounded ? 'rounded-full' : 'rounded';

  // Combine all classes
  const classes = classnames(
    'inline-flex items-center justify-center font-medium',
    colorClasses[color],
    sizeClasses[size],
    roundedClasses,
    {
      'cursor-pointer hover:opacity-80 transition-opacity': !!onClick,
    },
    className
  );

  return (
    <span className={classes} onClick={onClick}>
      {children}
    </span>
  );
};

/**
 * Helper function that returns appropriate badge props based on task status
 */
export const getStatusBadgeProps = (status: string) => {
  let color: BadgeColor;
  let text: string;

  // Format the status for display and set appropriate color
  switch (status.toUpperCase()) {
    case 'COMPLETED':
      color = BadgeColor.SUCCESS;
      text = 'Completed';
      break;
    case 'IN_PROGRESS':
    case 'IN-PROGRESS':
      color = BadgeColor.PRIMARY;
      text = 'In Progress';
      break;
    case 'ON_HOLD':
    case 'ON-HOLD':
      color = BadgeColor.WARNING;
      text = 'On Hold';
      break;
    case 'CANCELLED':
      color = BadgeColor.NEUTRAL;
      text = 'Cancelled';
      break;
    case 'REVIEW':
    case 'IN_REVIEW':
    case 'IN-REVIEW':
      color = BadgeColor.INFO;
      text = 'Review';
      break;
    case 'OVERDUE':
      color = BadgeColor.ERROR;
      text = 'Overdue';
      break;
    default:
      color = BadgeColor.NEUTRAL;
      text = status.charAt(0).toUpperCase() + status.slice(1).toLowerCase().replace('_', ' ');
  }

  return { color, text };
};

/**
 * Helper function that returns appropriate badge props based on task priority
 */
export const getPriorityBadgeProps = (priority: string) => {
  let color: BadgeColor;
  let text: string;

  // Format the priority for display and set appropriate color
  switch (priority.toUpperCase()) {
    case 'HIGH':
    case 'URGENT':
      color = BadgeColor.ERROR;
      text = priority.charAt(0).toUpperCase() + priority.slice(1).toLowerCase();
      break;
    case 'MEDIUM':
      color = BadgeColor.WARNING;
      text = 'Medium';
      break;
    case 'LOW':
      color = BadgeColor.INFO;
      text = 'Low';
      break;
    default:
      color = BadgeColor.NEUTRAL;
      text = priority.charAt(0).toUpperCase() + priority.slice(1).toLowerCase();
  }

  return { color, text };
};

/**
 * Helper function that returns appropriate badge props based on project status
 */
export const getProjectStatusBadgeProps = (status: string) => {
  let color: BadgeColor;
  let text: string;

  // Format the status for display and set appropriate color
  switch (status.toUpperCase()) {
    case 'ACTIVE':
      color = BadgeColor.PRIMARY;
      text = 'Active';
      break;
    case 'COMPLETED':
      color = BadgeColor.SUCCESS;
      text = 'Completed';
      break;
    case 'ON_HOLD':
    case 'ON-HOLD':
      color = BadgeColor.WARNING;
      text = 'On Hold';
      break;
    case 'PLANNING':
      color = BadgeColor.INFO;
      text = 'Planning';
      break;
    case 'CANCELLED':
      color = BadgeColor.NEUTRAL;
      text = 'Cancelled';
      break;
    case 'ARCHIVED':
      color = BadgeColor.NEUTRAL;
      text = 'Archived';
      break;
    default:
      color = BadgeColor.NEUTRAL;
      text = status.charAt(0).toUpperCase() + status.slice(1).toLowerCase().replace('_', ' ');
  }

  return { color, text };
};

export default Badge;