import { useState, useEffect, useMemo, useCallback } from 'react'; // react 18.2.x
import { 
  useProjects, 
  useProject, 
  useProjectMutation, 
  useProjectMembers,
  useProjectTaskLists,
  useProjectStatistics
} from '../../../api/hooks/useProjects';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import {
  selectProjects,
  selectSelectedProject,
  selectProjectLoading,
  selectProjectError,
  setSelectedProject
} from '../../../store/slices/projectSlice';
import {
  calculateProjectProgress,
  getStatusColor,
  filterProjects,
  sortProjects,
  getProjectStatusDisplay
} from '../utils';
import { Project, ProjectFilter } from '../../../types/project';

/**
 * Hook for managing the currently selected project in the Redux store
 * 
 * @returns Object containing the selected project and selection functions
 */
export function useProjectSelection() {
  const selectedProject = useAppSelector(selectSelectedProject);
  const dispatch = useAppDispatch();
  
  const selectProject = useCallback((projectId: string) => {
    dispatch(setSelectedProject(projectId));
  }, [dispatch]);
  
  const clearProjectSelection = useCallback(() => {
    dispatch(setSelectedProject(null));
  }, [dispatch]);
  
  return {
    selectedProject,
    selectProject,
    clearProjectSelection
  };
}

/**
 * Hook that combines API data with local filtering and sorting capabilities
 * 
 * @param filters - Filter criteria for projects
 * @param sortOptions - Sort options for projects
 * @returns Filtered and sorted projects with loading state
 */
export function useFilteredProjects(
  filters: ProjectFilter,
  sortOptions: { sortBy: string; direction: string }
) {
  // Use the base hook to fetch all projects
  const { 
    projects, 
    isLoading, 
    error,
    refetch
  } = useProjects();
  
  // Apply filters
  const filteredProjects = useMemo(() => {
    if (!projects || projects.length === 0) return [];
    return filterProjects(projects, filters);
  }, [projects, filters]);
  
  // Apply sorting
  const sortedProjects = useMemo(() => {
    if (!filteredProjects || filteredProjects.length === 0) return [];
    return sortProjects(filteredProjects, sortOptions.sortBy, sortOptions.direction);
  }, [filteredProjects, sortOptions.sortBy, sortOptions.direction]);
  
  return {
    projects,
    isLoading,
    error,
    refetch,
    filteredProjects,
    sortedProjects
  };
}

/**
 * Hook that calculates and monitors project completion progress
 * 
 * @param projectId - ID of the project to monitor
 * @returns Project progress percentage and status color
 */
export function useProjectProgress(projectId: string) {
  const { project, isLoading, error } = useProject(projectId);
  
  const progress = useMemo(() => {
    if (!project) return 0;
    return calculateProjectProgress(project);
  }, [project]);
  
  const progressColor = useMemo(() => {
    if (!project) return '';
    return getStatusColor(project.status).text;
  }, [project]);
  
  return {
    progress,
    progressColor,
    isLoading,
    error
  };
}

/**
 * Hook that provides aggregated project data for dashboard views
 * 
 * @returns Dashboard data including project counts by status
 */
export function useProjectDashboard() {
  const { projects, isLoading, error } = useProjects();
  
  const dashboardData = useMemo(() => {
    if (!projects || projects.length === 0) {
      return {
        totalProjects: 0,
        projectsByStatus: {},
        recentProjects: [],
        upcomingDeadlines: []
      };
    }
    
    // Count projects by status
    const projectsByStatus = projects.reduce((acc, project) => {
      const status = project.status;
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // Get recently updated projects
    const recentProjects = [...projects]
      .sort((a, b) => new Date(b.metadata.lastUpdated).getTime() - new Date(a.metadata.lastUpdated).getTime())
      .slice(0, 5);
    
    // Find projects with approaching deadlines
    const upcomingDeadlines = projects
      .filter(project => {
        if (project.status === 'completed' || project.status === 'archived') {
          return false;
        }
        
        // Calculate project end date based on task due dates
        const hasUpcomingDeadlines = project.metadata.taskCount > 0 && 
          project.metadata.completedTaskCount / project.metadata.taskCount < 0.8;
        
        return hasUpcomingDeadlines;
      })
      .slice(0, 5);
    
    return {
      totalProjects: projects.length,
      projectsByStatus,
      recentProjects,
      upcomingDeadlines
    };
  }, [projects]);
  
  return {
    ...dashboardData,
    isLoading,
    error
  };
}

// Re-export hooks from the API layer
export {
  useProjects,
  useProject,
  useProjectMutation,
  useProjectMembers,
  useProjectTaskLists,
  useProjectStatistics
};