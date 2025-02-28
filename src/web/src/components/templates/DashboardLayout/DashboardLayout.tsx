import React, { useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import classNames from 'classnames';
import { FiHome, FiCheckSquare, FiFolder, FiUser, FiMenu } from 'react-icons/fi';

import { NavigationMenu } from '../../organisms/NavigationMenu/NavigationMenu';
import { UserDropdown } from '../../organisms/UserDropdown/UserDropdown';
import { BottomNavigation } from '../../mobile/BottomNavigation/BottomNavigation';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { useTheme } from '../../../contexts/ThemeContext';
import useAuth from '../../../api/hooks/useAuth';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { selectSidebarOpen, uiActions } from '../../../store/slices/uiSlice';
import Icon from '../../atoms/Icon/Icon';
import { PATHS } from '../../../routes/paths';

/**
 * Props for the DashboardLayout component
 */
interface DashboardLayoutProps {
  /**
   * Child components to be rendered in the main content area
   */
  children: ReactNode;
  
  /**
   * Optional title to display in the header
   */
  title?: string;
}

/**
 * A template component that provides the common layout structure for all dashboard pages,
 * including responsive navigation, header with user controls, and main content area.
 * This component adapts to different screen sizes with appropriate navigation patterns.
 */
const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, title }) => {
  // Get current screen size using media queries
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(min-width: 641px) and (max-width: 1024px)');
  
  // Get sidebar state from Redux store
  const sidebarOpen = useAppSelector(selectSidebarOpen);
  const dispatch = useAppDispatch();
  
  // Get user information from auth context
  const { user } = useAuth();
  
  // Get current theme
  const { theme } = useTheme();
  
  // Get current location for route-based sidebar handling
  const location = useLocation();
  
  // Handle sidebar toggle
  const handleToggleSidebar = () => {
    dispatch(uiActions.toggleSidebar());
  };
  
  // Automatically collapse sidebar on mobile screens
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(uiActions.setSidebarOpen(false));
    }
  }, [isMobile, sidebarOpen, dispatch]);
  
  // Close sidebar when changing routes on mobile
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(uiActions.setSidebarOpen(false));
    }
  }, [location.pathname, isMobile, sidebarOpen, dispatch]);
  
  // Mobile navigation items
  const mobileNavItems = [
    { label: 'Home', path: PATHS.DASHBOARD, icon: FiHome },
    { label: 'Tasks', path: PATHS.TASKS, icon: FiCheckSquare },
    { label: 'Projects', path: PATHS.PROJECTS, icon: FiFolder },
    { label: 'Profile', path: PATHS.USER_SETTINGS, icon: FiUser }
  ];

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Desktop/Tablet Navigation Sidebar */}
      {!isMobile && (
        <NavigationMenu />
      )}
      
      {/* Main Content Area */}
      <div className={classNames(
        "flex flex-col flex-1 overflow-hidden transition-all duration-300",
        {
          "ml-64": sidebarOpen && !isMobile,
          "ml-16": !sidebarOpen && !isMobile
        }
      )}>
        {/* Header with User Controls */}
        <header className="bg-white dark:bg-gray-800 shadow-sm h-16 flex items-center px-4 z-10">
          <div className="flex items-center justify-between w-full">
            {/* Left section: Toggle & Title */}
            <div className="flex items-center">
              {/* Sidebar toggle button (not on mobile) */}
              {!isMobile && (
                <button
                  type="button"
                  onClick={handleToggleSidebar}
                  className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-700 mr-3"
                  aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                >
                  <Icon icon={FiMenu} size={20} aria-hidden="true" />
                </button>
              )}
              
              {/* Page title */}
              <h1 className="text-lg font-semibold text-gray-800 dark:text-white truncate">
                {title || "Task Management System"}
              </h1>
            </div>
            
            {/* Right section: Search & User */}
            <div className="flex items-center">
              {/* Search input (desktop only) */}
              {!isMobile && (
                <div className="relative mx-4 hidden md:block">
                  <input
                    type="text"
                    placeholder="Search..."
                    className="bg-gray-100 dark:bg-gray-700 border-none rounded-md py-2 px-4 w-64 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              )}
              
              {/* User dropdown */}
              <UserDropdown />
            </div>
          </div>
        </header>
        
        {/* Main Content */}
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      {/* Mobile Bottom Navigation */}
      {isMobile && <BottomNavigation navItems={mobileNavItems} />}
    </div>
  );
};

export default DashboardLayout;