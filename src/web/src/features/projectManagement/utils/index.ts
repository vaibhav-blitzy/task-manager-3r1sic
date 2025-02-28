import {
  Project, ProjectStatus, ProjectRole, ProjectMember, ProjectFormData, TaskList
} from '../../../types/project';
import { formatDate } from '../../../utils/date';
import { checkPermission } from '../../../utils/permissions';

/**
 * Calculates the percentage of completed tasks for a project
 * @param project - The project to calculate progress for
 * @returns Percentage of completed tasks (0-100)
 */
export const calculateProjectProgress = (project: Project): number => {
  if (!project.metadata || project.metadata.taskCount === 0) {
    return 0;
  }
  
  const { completedTaskCount, taskCount } = project.metadata;
  const progress = (completedTaskCount / taskCount) * 100;
  
  // Cap at 100% to avoid progress over 100%
  return Math.min(progress, 100);
};

/**
 * Returns a human-readable display string for project status
 * @param status - The project status enum value
 * @returns User-friendly status name
 */
export const getProjectStatusDisplay = (status: ProjectStatus): string => {
  const statusDisplay: Record<ProjectStatus, string> = {
    [ProjectStatus.PLANNING]: 'Planning',
    [ProjectStatus.ACTIVE]: 'Active',
    [ProjectStatus.ON_HOLD]: 'On Hold',
    [ProjectStatus.COMPLETED]: 'Completed',
    [ProjectStatus.ARCHIVED]: 'Archived'
  };
  
  return statusDisplay[status] || 'Unknown';
};

/**
 * Returns a human-readable display string for project role
 * @param role - The project role enum value
 * @returns User-friendly role name
 */
export const getProjectRoleDisplay = (role: ProjectRole): string => {
  const roleDisplay: Record<ProjectRole, string> = {
    [ProjectRole.ADMIN]: 'Administrator',
    [ProjectRole.MANAGER]: 'Project Manager',
    [ProjectRole.MEMBER]: 'Team Member',
    [ProjectRole.VIEWER]: 'Viewer'
  };
  
  return roleDisplay[role] || 'Unknown';
};

/**
 * Returns appropriate UI color indicators for different project statuses
 * @param status - The project status
 * @returns Object with background, text, and border color classes
 */
export const getStatusColor = (status: ProjectStatus): { bg: string; text: string; border: string } => {
  // Use Tailwind CSS color classes for styling
  switch (status) {
    case ProjectStatus.PLANNING:
      return {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        border: 'border-blue-300'
      };
    case ProjectStatus.ACTIVE:
      return {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-300'
      };
    case ProjectStatus.ON_HOLD:
      return {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        border: 'border-yellow-300'
      };
    case ProjectStatus.COMPLETED:
      return {
        bg: 'bg-purple-100',
        text: 'text-purple-800',
        border: 'border-purple-300'
      };
    case ProjectStatus.ARCHIVED:
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-300'
      };
    default:
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-300'
      };
  }
};

/**
 * Returns appropriate color class based on progress percentage
 * @param progress - The progress percentage (0-100)
 * @returns Tailwind CSS color class
 */
export const getProgressColor = (progress: number): string => {
  if (progress < 25) {
    return 'text-red-500';
  } else if (progress < 50) {
    return 'text-orange-500';
  } else if (progress < 75) {
    return 'text-blue-500';
  } else {
    return 'text-green-500';
  }
};

/**
 * Sorts an array of projects based on specified criteria
 * @param projects - Array of projects to sort
 * @param sortBy - Field to sort by (name, status, dueDate, etc.)
 * @param direction - Sort direction ('asc' or 'desc')
 * @returns Sorted array of projects
 */
export const sortProjects = (
  projects: Project[],
  sortBy: string,
  direction: string
): Project[] => {
  const directionMultiplier = direction === 'desc' ? -1 : 1;
  
  // Create a shallow copy of the projects array
  return [...projects].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return directionMultiplier * a.name.localeCompare(b.name);
      
      case 'status':
        return directionMultiplier * a.status.localeCompare(b.status);
      
      case 'category':
        return directionMultiplier * a.category.localeCompare(b.category);
      
      case 'owner':
        return directionMultiplier * a.owner.firstName.localeCompare(b.owner.firstName);
      
      case 'created':
        return directionMultiplier * (
          new Date(a.metadata.created).getTime() - 
          new Date(b.metadata.created).getTime()
        );
      
      case 'updated':
        return directionMultiplier * (
          new Date(a.metadata.lastUpdated).getTime() - 
          new Date(b.metadata.lastUpdated).getTime()
        );
      
      case 'progress':
        const progressA = calculateProjectProgress(a);
        const progressB = calculateProjectProgress(b);
        return directionMultiplier * (progressA - progressB);
      
      default:
        return 0;
    }
  });
};

/**
 * Filters an array of projects based on various criteria
 * @param projects - Array of projects to filter
 * @param filters - Object containing filter criteria
 * @returns Filtered array of projects
 */
export const filterProjects = (
  projects: Project[],
  filters: {
    status?: ProjectStatus | ProjectStatus[];
    category?: string | string[];
    tags?: string[];
    searchTerm?: string;
  }
): Project[] => {
  return projects.filter(project => {
    // Filter by status if specified
    if (filters.status) {
      const statuses = Array.isArray(filters.status) ? filters.status : [filters.status];
      if (!statuses.includes(project.status)) {
        return false;
      }
    }
    
    // Filter by category if specified
    if (filters.category) {
      const categories = Array.isArray(filters.category) ? filters.category : [filters.category];
      if (!categories.includes(project.category)) {
        return false;
      }
    }
    
    // Filter by tags if specified
    if (filters.tags && filters.tags.length > 0) {
      if (!filters.tags.some(tag => project.tags.includes(tag))) {
        return false;
      }
    }
    
    // Filter by search term if specified
    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase();
      const matchesName = project.name.toLowerCase().includes(term);
      const matchesDescription = project.description.toLowerCase().includes(term);
      
      if (!matchesName && !matchesDescription) {
        return false;
      }
    }
    
    return true;
  });
};

/**
 * Truncates project description to specified length with ellipsis
 * @param description - The description to truncate
 * @param maxLength - Maximum length before truncation (default: 100)
 * @returns Truncated description
 */
export const truncateProjectDescription = (
  description: string,
  maxLength: number = 100
): string => {
  if (!description) {
    return '';
  }
  
  if (description.length <= maxLength) {
    return description;
  }
  
  return `${description.substring(0, maxLength).trim()}...`;
};

/**
 * Groups projects by their status for kanban-style displays
 * @param projects - Array of projects to group
 * @returns Record with ProjectStatus keys and arrays of projects
 */
export const groupProjectsByStatus = (
  projects: Project[]
): Record<ProjectStatus, Project[]> => {
  const result: Record<ProjectStatus, Project[]> = {
    [ProjectStatus.PLANNING]: [],
    [ProjectStatus.ACTIVE]: [],
    [ProjectStatus.ON_HOLD]: [],
    [ProjectStatus.COMPLETED]: [],
    [ProjectStatus.ARCHIVED]: []
  };
  
  projects.forEach(project => {
    if (result[project.status]) {
      result[project.status].push(project);
    }
  });
  
  return result;
};

/**
 * Groups projects by their category
 * @param projects - Array of projects to group
 * @returns Record with category keys and arrays of projects
 */
export const groupProjectsByCategory = (
  projects: Project[]
): Record<string, Project[]> => {
  const result: Record<string, Project[]> = {};
  
  projects.forEach(project => {
    if (!result[project.category]) {
      result[project.category] = [];
    }
    result[project.category].push(project);
  });
  
  return result;
};

/**
 * Validates project form data before submission
 * @param formData - Project form data to validate
 * @returns Object with isValid flag and errors
 */
export const validateProjectForm = (
  formData: ProjectFormData
): { isValid: boolean; errors: Record<string, string> } => {
  const errors: Record<string, string> = {};
  
  // Validate required fields
  if (!formData.name || formData.name.trim() === '') {
    errors.name = 'Project name is required';
  } else if (formData.name.length > 100) {
    errors.name = 'Project name cannot exceed 100 characters';
  }
  
  // Validate description length if provided
  if (formData.description && formData.description.length > 2000) {
    errors.description = 'Description cannot exceed 2000 characters';
  }
  
  // Validate status if provided
  if (formData.status && !Object.values(ProjectStatus).includes(formData.status)) {
    errors.status = 'Invalid project status';
  }
  
  // Return validation result
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

/**
 * Checks if a user has permission to edit a project
 * @param project - The project to check permissions for
 * @param userId - ID of the user to check
 * @returns True if user can edit the project
 */
export const canEditProject = (project: Project, userId: string): boolean => {
  // Check if user is the owner
  if (project.ownerId === userId) {
    return true;
  }
  
  // Check if user is a member with admin or manager role
  const userMembership = project.members.find(member => member.userId === userId);
  if (userMembership && (
    userMembership.role === ProjectRole.ADMIN || 
    userMembership.role === ProjectRole.MANAGER
  )) {
    return true;
  }
  
  // Use the checkPermission utility to verify user has edit permission
  return checkPermission(userId, 'project', 'update');
};

/**
 * Returns the count of active members in a project
 * @param project - The project to count members for
 * @returns Number of active members
 */
export const getProjectMembersCount = (project: Project): number => {
  return project.members.filter(member => member.isActive).length;
};

/**
 * Calculates the duration of a project in days
 * @param project - The project to calculate duration for
 * @returns Duration in days
 */
export const getProjectDuration = (project: Project): number => {
  const startDate = new Date(project.metadata.created);
  let endDate: Date;
  
  if (project.status === ProjectStatus.COMPLETED && project.metadata.completedAt) {
    endDate = new Date(project.metadata.completedAt);
  } else {
    endDate = new Date(); // Current date if not completed
  }
  
  // Calculate difference in days
  const durationMs = endDate.getTime() - startDate.getTime();
  return Math.ceil(durationMs / (1000 * 60 * 60 * 24));
};

/**
 * Formats project dates for display
 * @param project - The project containing dates to format
 * @returns Object with formatted dates
 */
export const formatProjectDates = (
  project: Project
): { created: string; updated: string; completed: string } => {
  return {
    created: formatDate(project.metadata.created),
    updated: formatDate(project.metadata.lastUpdated),
    completed: project.metadata.completedAt ? formatDate(project.metadata.completedAt) : '-'
  };
};