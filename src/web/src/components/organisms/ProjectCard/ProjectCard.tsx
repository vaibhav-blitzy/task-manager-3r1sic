import React from 'react';
import classNames from 'classnames'; // version 2.3.2
import { FaUsers, FaCalendarAlt, FaTasks } from 'react-icons/fa'; // version 4.10.0

import { Project, ProjectStatus } from '../../../types/project';
import Avatar from '../../atoms/Avatar/Avatar';
import { Badge, getProjectStatusBadgeProps } from '../../atoms/Badge/Badge';
import Icon from '../../atoms/Icon/Icon';
import { formatDate } from '../../../utils/date';

interface ProjectCardProps {
  project: Project;
  onClick?: (project: Project) => void;
  selected?: boolean;
  maxDescriptionLength?: number;
  showMembers?: boolean;
  showProgress?: boolean;
  showTags?: boolean;
  className?: string;
}

/**
 * Truncates a string to a specified length and adds ellipsis if needed
 * 
 * @param text The text to truncate
 * @param maxLength Maximum length before truncation
 * @returns Truncated text with ellipsis if truncated
 */
const truncateText = (text: string, maxLength: number): string => {
  if (text.length > maxLength) {
    return text.slice(0, maxLength) + '...';
  }
  return text;
};

/**
 * Calculates the completion percentage of a project based on task counts
 * 
 * @param project The project data
 * @returns Percentage of completed tasks (0-100)
 */
const calculateProgress = (project: Project): number => {
  if (!project.metadata || 
      project.metadata.completedTaskCount === undefined || 
      project.metadata.taskCount === undefined || 
      project.metadata.taskCount === 0) {
    return 0;
  }
  
  const { completedTaskCount, taskCount } = project.metadata;
  const percentage = (completedTaskCount / taskCount) * 100;
  return Math.min(percentage, 100); // Cap at 100%
};

/**
 * Returns the appropriate color class for progress bar based on completion percentage
 * 
 * @param progress Completion percentage
 * @returns Tailwind CSS color class for the progress bar
 */
const getProgressColorClass = (progress: number): string => {
  if (progress < 25) {
    return 'bg-red-500';
  } else if (progress < 50) {
    return 'bg-orange-500';
  } else if (progress < 75) {
    return 'bg-blue-500';
  } else {
    return 'bg-green-500';
  }
};

/**
 * Component that displays project information in a card format
 * 
 * Shows key details like project name, description, status, progress,
 * and team members. Configurable to show/hide various elements.
 */
const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onClick,
  selected = false,
  maxDescriptionLength = 100,
  showMembers = true,
  showProgress = true,
  showTags = true,
  className = '',
}) => {
  // Calculate project completion progress
  const progress = calculateProgress(project);
  
  // Get badge props for project status
  const statusBadgeProps = getProjectStatusBadgeProps(project.status);
  
  // Truncate description if needed
  const description = truncateText(project.description || '', maxDescriptionLength);
  
  // Determine card classes including selected state
  const cardClasses = classNames(
    'bg-white rounded-lg shadow-sm p-4 border transition-all',
    {
      'border-primary-500 ring-2 ring-primary-200': selected,
      'border-gray-200 hover:border-gray-300': !selected,
      'cursor-pointer hover:shadow': onClick,
    },
    className
  );
  
  return (
    <div 
      className={cardClasses}
      onClick={() => onClick && onClick(project)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900 truncate" title={project.name}>
          {project.name}
        </h3>
        <Badge 
          color={statusBadgeProps.color}
          size="sm"
        >
          {statusBadgeProps.text}
        </Badge>
      </div>
      
      <p className="text-sm text-gray-600 mb-4" title={project.description}>
        {description}
      </p>
      
      {showProgress && (
        <div className="mb-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-500">Progress</span>
            <span className="text-xs font-medium text-gray-700">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${getProgressColorClass(progress)}`} 
              style={{ width: `${progress}%` }}
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
              role="progressbar"
            ></div>
          </div>
        </div>
      )}
      
      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
        {project.metadata?.taskCount !== undefined && (
          <div className="flex items-center">
            <Icon icon={FaTasks} className="mr-1" size={14} />
            <span>{project.metadata.taskCount} tasks</span>
          </div>
        )}
        
        {project.metadata?.created && (
          <div className="flex items-center">
            <Icon icon={FaCalendarAlt} className="mr-1" size={14} />
            <span>{formatDate(project.metadata.created)}</span>
          </div>
        )}
        
        {showMembers && project.members && project.members.length > 0 && (
          <div className="flex items-center">
            <Icon icon={FaUsers} className="mr-1" size={14} />
            <div className="flex -space-x-2">
              {project.members.slice(0, 3).map((member) => (
                <Avatar 
                  key={member.userId}
                  user={member.user}
                  size="sm"
                  className="border border-white"
                />
              ))}
              
              {project.members.length > 3 && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600 border border-white">
                  +{project.members.length - 3}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {showTags && project.tags && project.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {project.tags.slice(0, 3).map((tag) => (
            <Badge 
              key={tag} 
              color="neutral"
              size="sm"
              outlined
            >
              {tag}
            </Badge>
          ))}
          
          {project.tags.length > 3 && (
            <Badge 
              color="neutral"
              size="sm"
              outlined
            >
              +{project.tags.length - 3}
            </Badge>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectCard;