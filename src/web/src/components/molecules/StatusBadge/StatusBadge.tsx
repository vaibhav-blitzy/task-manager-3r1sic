import React from 'react';
import classNames from 'classnames'; // version 2.3.x
import { FaCircle, FaCheck, FaPause, FaEye, FaTimes, FaExclamationTriangle } from 'react-icons/fa'; // version 4.10.x
import { Badge, BadgeColor, BadgeSize } from '../../atoms/Badge/Badge';
import { Icon } from '../../atoms/Icon/Icon';
import { TaskStatus } from '../../../types/task';

interface StatusBadgeProps {
  status: string;
  progressPercent?: number;
  showIcon?: boolean;
  size?: typeof BadgeSize[keyof typeof BadgeSize];
  className?: string;
}

/**
 * Maps task status to appropriate badge color
 */
const getStatusColor = (status: string): BadgeColor => {
  const upperStatus = status.toUpperCase();
  
  switch (upperStatus) {
    case TaskStatus.COMPLETED.toUpperCase():
      return BadgeColor.SUCCESS;
    case TaskStatus.IN_PROGRESS.toUpperCase():
      return BadgeColor.PRIMARY;
    case TaskStatus.ON_HOLD.toUpperCase():
      return BadgeColor.WARNING;
    case TaskStatus.IN_REVIEW.toUpperCase():
      return BadgeColor.INFO;
    case TaskStatus.CANCELLED.toUpperCase():
      return BadgeColor.NEUTRAL;
    case TaskStatus.CREATED.toUpperCase():
    case TaskStatus.ASSIGNED.toUpperCase():
      return BadgeColor.NEUTRAL;
    default:
      return BadgeColor.NEUTRAL;
  }
};

/**
 * Returns the appropriate icon component for a given status
 */
const getStatusIcon = (status: string): React.ElementType => {
  const upperStatus = status.toUpperCase();
  
  switch (upperStatus) {
    case TaskStatus.COMPLETED.toUpperCase():
      return FaCheck;
    case TaskStatus.IN_PROGRESS.toUpperCase():
      return FaCircle;
    case TaskStatus.ON_HOLD.toUpperCase():
      return FaPause;
    case TaskStatus.IN_REVIEW.toUpperCase():
      return FaEye;
    case TaskStatus.CANCELLED.toUpperCase():
      return FaTimes;
    case TaskStatus.CREATED.toUpperCase():
    case TaskStatus.ASSIGNED.toUpperCase():
      return FaExclamationTriangle;
    default:
      return FaCircle;
  }
};

/**
 * Formats the status text for display
 */
const formatStatusText = (status: string): string => {
  // Convert from kebab-case or snake_case to title case
  return status
    .toLowerCase()
    .split(/[-_]/) // Split by either hyphen or underscore
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Component that displays task status with appropriate visual styling
 */
const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  progressPercent,
  showIcon = true,
  size = BadgeSize.MEDIUM,
  className = '',
}) => {
  const color = getStatusColor(status);
  const IconComponent = getStatusIcon(status);
  const formattedStatus = formatStatusText(status);
  
  // Determine if we should show progress indicator
  const isInProgress = status.toUpperCase() === TaskStatus.IN_PROGRESS.toUpperCase();
  const hasValidProgress = progressPercent !== undefined && progressPercent >= 0 && progressPercent <= 100;
  const showProgress = isInProgress && hasValidProgress;
  
  // Determine progress bar height based on badge size
  const progressHeight = size === BadgeSize.SMALL ? 'h-0.5' : size === BadgeSize.LARGE ? 'h-1.5' : 'h-1';

  return (
    <div className={classNames('status-badge-container inline-block', className)}>
      {showProgress && (
        <div className={classNames('w-full bg-gray-200 rounded-full mb-1 overflow-hidden', progressHeight)}>
          <div 
            className={classNames('h-full bg-primary-600 rounded-full', progressHeight)}
            style={{ width: `${progressPercent}%` }}
            aria-label={`${progressPercent}% complete`}
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progressPercent}
          />
        </div>
      )}
      <Badge color={color} size={size}>
        {showIcon && (
          <Icon
            icon={IconComponent}
            size={size === BadgeSize.SMALL ? 10 : size === BadgeSize.LARGE ? 14 : 12}
            className="mr-1"
            aria-hidden="true"
          />
        )}
        {formattedStatus}
      </Badge>
    </div>
  );
};

export default StatusBadge;