import React, { useState, useEffect, ReactNode, useMemo } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import classNames from 'classnames';
import { FiChevronLeft } from 'react-icons/fi';

import NavigationMenu from '../../organisms/NavigationMenu/NavigationMenu';
import UserDropdown from '../../organisms/UserDropdown/UserDropdown';
import BottomNavigation from '../../mobile/BottomNavigation/BottomNavigation';
import { Button } from '../../atoms/Button/Button';
import Avatar from '../../atoms/Avatar/Avatar';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { useProject } from '../../../api/hooks/useProjects';
import useAuth from '../../../api/hooks/useAuth';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { selectSidebarOpen, uiActions } from '../../../store/slices/uiSlice';
import { PATHS } from '../../../routes/paths';

interface ProjectLayoutProps {
  children: ReactNode;
  backLink?: string;
  title?: string;
  actions?: ReactNode;
}

/**
 * Helper function to calculate the completion percentage of a project
 */
const calculateProgress = (project: any): number => {
  if (!project?.metadata) return 0;
  
  const { completedTaskCount, taskCount } = project.metadata;
  
  if (!taskCount || taskCount === 0) return 0;
  
  const percentage = (completedTaskCount / taskCount) * 100;
  
  // Ensure percentage doesn't exceed 100%
  return Math.min(percentage, 100);
};

/**
 * Main project layout template component that renders the project-specific frame with
 * navigation, header with project info, and content area
 */
const ProjectLayout: React.FC<ProjectLayoutProps> = ({
  children,
  backLink,
  title,
  actions
}) => {
  // Get project ID from URL params
  const { projectId } = useParams<{ projectId: string }>();
  
  // Get media query hooks for responsive design
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(max-width: 1024px)');
  
  // Get sidebar state from Redux
  const sidebarOpen = useAppSelector(selectSidebarOpen);
  const dispatch = useAppDispatch();
  
  // Get auth and user data
  const { user } = useAuth();
  
  // Get project data
  const { project, isLoading, error } = useProject(projectId || '');
  
  // Get navigation functions
  const navigate = useNavigate();
  const location = useLocation();
  
  // Calculate project progress
  const progress = useMemo(() => {
    return calculateProgress(project);
  }, [project]);
  
  // Handle back navigation
  const handleBack = () => {
    if (backLink) {
      navigate(backLink);
    } else {
      navigate(PATHS.PROJECTS); // Default fallback to projects list
    }
  };
  
  // Handle sidebar toggle
  const handleToggleSidebar = () => {
    dispatch(uiActions.toggleSidebar());
  };
  
  // Auto-collapse sidebar on mobile
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(uiActions.setSidebarOpen(false));
    }
  }, [isMobile, sidebarOpen, dispatch]);
  
  // When routes change, collapse sidebar on mobile
  useEffect(() => {
    if (isMobile) {
      dispatch(uiActions.setSidebarOpen(false));
    }
  }, [location.pathname, isMobile, dispatch]);
  
  // Render loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h2 className="text-xl font-semibold text-red-600">Error loading project</h2>
        <p className="text-gray-600 mt-2">{error.message}</p>
        <Button 
          onClick={() => navigate(PATHS.PROJECTS)}
          className="mt-4"
        >
          Return to Projects
        </Button>
      </div>
    );
  }
  
  // Render not found state if project doesn't exist
  if (!project && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h2 className="text-xl font-semibold text-red-600">Project not found</h2>
        <p className="text-gray-600 mt-2">The project you're looking for doesn't exist or you don't have permission to view it.</p>
        <Button 
          onClick={() => navigate(PATHS.PROJECTS)}
          className="mt-4"
        >
          Return to Projects
        </Button>
      </div>
    );
  }
  
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Navigation Menu - Hidden on mobile */}
      {!isMobile && (
        <NavigationMenu className={classNames({
          'opacity-100': sidebarOpen,
          'opacity-95': !sidebarOpen
        })} />
      )}
      
      {/* Main Content */}
      <div 
        className={classNames(
          'flex-1 flex flex-col overflow-hidden transition-all duration-300',
          {
            'md:ml-16': !sidebarOpen && !isMobile,
            'md:ml-64': sidebarOpen && !isMobile
          }
        )}
      >
        {/* Header with project info */}
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="px-4 py-4 flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="text"
                onClick={handleBack}
                icon={<FiChevronLeft />}
                aria-label="Go back"
              />
              
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {title || (project?.name) || 'Project View'}
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <UserDropdown />
            </div>
          </div>
          
          {/* Project information bar - only show if project data is available */}
          {project && (
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-200 dark:border-gray-600">
              <div className="flex flex-col mb-2 md:mb-0">
                <div className="flex items-center">
                  <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">Progress:</span>
                  <div className="w-40 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary-600 dark:bg-primary-500 rounded-full" 
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <span className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    {Math.round(progress)}%
                  </span>
                </div>
              </div>
              
              <div className="flex items-center">
                {/* Only show team members if there are any */}
                {project.members && project.members.length > 0 && (
                  <div className="flex -space-x-2 mr-4">
                    {project.members.slice(0, 5).map((member) => (
                      <Avatar 
                        key={member.userId}
                        user={member.user}
                        size="sm"
                        className="border-2 border-white dark:border-gray-800"
                      />
                    ))}
                    
                    {project.members.length > 5 && (
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 text-xs font-medium text-gray-700 dark:text-gray-300 border-2 border-white dark:border-gray-800">
                        +{project.members.length - 5}
                      </div>
                    )}
                  </div>
                )}
                
                {/* Actions slot for additional buttons or controls */}
                {actions && (
                  <div className="flex space-x-2">
                    {actions}
                  </div>
                )}
              </div>
            </div>
          )}
        </header>
        
        {/* Main Content */}
        <main className={classNames('flex-1 overflow-auto p-4 md:p-6')}>
          {children}
        </main>
        
        {/* Mobile Bottom Navigation - Visible only on mobile */}
        {isMobile && (
          <BottomNavigation 
            navItems={[
              { 
                label: 'Home', 
                path: PATHS.DASHBOARD, 
                icon: FiChevronLeft
              },
              { 
                label: 'Tasks', 
                path: PATHS.TASKS, 
                icon: FiChevronLeft
              },
              { 
                label: 'Projects', 
                path: PATHS.PROJECTS, 
                icon: FiChevronLeft
              },
              { 
                label: 'Profile', 
                path: '/profile', 
                icon: FiChevronLeft
              }
            ]}
          />
        )}
      </div>
    </div>
  );
};

export default ProjectLayout;