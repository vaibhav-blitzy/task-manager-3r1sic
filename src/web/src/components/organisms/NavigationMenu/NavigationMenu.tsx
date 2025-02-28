import React, { useState, useEffect, useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import classNames from 'classnames';
import {
  FiHome,
  FiCheckSquare,
  FiFolder,
  FiCalendar,
  FiBarChart2,
  FiUsers,
  FiChevronRight,
  FiChevronDown,
  FiMenu,
} from 'react-icons/fi';

import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { selectSidebarOpen, uiActions } from '../../../store/slices/uiSlice';
import Icon from '../../atoms/Icon/Icon';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import useAuth from '../../../api/hooks/useAuth';
import { PATHS } from '../../../routes/paths';
import { Role, Permission } from '../../../types/auth';

interface NavigationMenuProps {
  className?: string;
}

interface NavItemType {
  label: string;
  icon: React.ReactNode;
  path: string;
  permission?: string;
  roles?: Role[];
}

interface NavSectionType {
  title: string;
  items: NavItemType[];
  collapsible?: boolean;
}

/**
 * Utility function to check if user has permission to view a navigation item
 */
const hasPermission = (
  user: any,
  permission?: string,
  roles?: Role[]
): boolean => {
  // If neither permission nor roles are specified, everyone can access
  if (!permission && !roles) {
    return true;
  }
  
  // If user is not authenticated, deny access
  if (!user) {
    return false;
  }
  
  // Check if user has any of the required roles
  if (roles && roles.length > 0) {
    const hasRole = roles.some(role => user.roles.includes(role));
    if (hasRole) {
      return true;
    }
  }
  
  // Check if user has the specific permission
  if (permission && user.permissions?.some((p: Permission) => p.type === permission)) {
    return true;
  }
  
  return false;
};

/**
 * Component for rendering a collapsible navigation section with a title and items
 */
const NavSection: React.FC<{
  section: NavSectionType;
  isOpen: boolean;
  onToggle: () => void;
  sidebarOpen: boolean;
  user: any;
}> = ({ section, isOpen, onToggle, sidebarOpen, user }) => {
  // Filter items based on user permissions
  const filteredItems = section.items.filter(item => 
    hasPermission(user, item.permission, item.roles)
  );
  
  // Don't render the section if there are no visible items
  if (filteredItems.length === 0) {
    return null;
  }
  
  return (
    <div className="mb-4">
      {section.title && (
        <div 
          className={classNames("px-4 py-2 text-xs font-medium text-gray-500 flex items-center justify-between", {
            "cursor-pointer hover:bg-gray-50": section.collapsible
          })}
          onClick={section.collapsible ? onToggle : undefined}
          role={section.collapsible ? "button" : undefined}
          aria-expanded={section.collapsible ? isOpen : undefined}
        >
          {sidebarOpen && <span>{section.title}</span>}
          {section.collapsible && sidebarOpen && (
            <Icon 
              icon={isOpen ? FiChevronDown : FiChevronRight} 
              size={16} 
              className="text-gray-400" 
              aria-hidden="true"
            />
          )}
        </div>
      )}
      
      {(!section.collapsible || isOpen) && (
        <div className="mt-1">
          {filteredItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                classNames("flex items-center px-4 py-2 text-sm rounded-md mx-2 my-1", {
                  "bg-indigo-50 text-indigo-600": isActive,
                  "text-gray-700 hover:bg-gray-100": !isActive,
                  "justify-center": !sidebarOpen,
                  "justify-start": sidebarOpen
                })
              }
              title={!sidebarOpen ? item.label : undefined}
            >
              <span className="flex-shrink-0">
                {item.icon}
              </span>
              {sidebarOpen && (
                <span className="ml-3 truncate">{item.label}</span>
              )}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Main navigation menu component displaying all application navigation links in a responsive sidebar
 */
const NavigationMenu: React.FC<NavigationMenuProps> = ({ className }) => {
  const { user } = useAuth();
  const sidebarOpen = useAppSelector(selectSidebarOpen);
  const dispatch = useAppDispatch();
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width: 640px)');
  
  // Track expanded sections
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'QUICK ACCESS': true,
    'MY TEAMS': true
  });
  
  // Define main navigation items
  const mainNavItems: NavItemType[] = useMemo(() => [
    {
      label: 'Dashboard',
      icon: <Icon icon={FiHome} size={20} />,
      path: PATHS.DASHBOARD
    },
    {
      label: 'Tasks',
      icon: <Icon icon={FiCheckSquare} size={20} />,
      path: PATHS.TASKS
    },
    {
      label: 'Projects',
      icon: <Icon icon={FiFolder} size={20} />,
      path: PATHS.PROJECTS,
      roles: [Role.ADMIN, Role.MANAGER]
    },
    {
      label: 'Calendar',
      icon: <Icon icon={FiCalendar} size={20} />,
      path: PATHS.CALENDAR
    },
    {
      label: 'Reports',
      icon: <Icon icon={FiBarChart2} size={20} />,
      path: PATHS.REPORTS,
      roles: [Role.ADMIN, Role.MANAGER]
    }
  ], []);
  
  // Quick access projects/tasks (this would be dynamic in a real app)
  const quickAccessItems: NavItemType[] = useMemo(() => [
    {
      label: 'Marketing',
      icon: <Icon icon={FiFolder} size={20} />,
      path: '/projects/marketing'
    },
    {
      label: 'Website',
      icon: <Icon icon={FiFolder} size={20} />,
      path: '/projects/website'
    },
    {
      label: 'Mobile App',
      icon: <Icon icon={FiFolder} size={20} />,
      path: '/projects/mobile-app'
    },
    {
      label: 'Add New',
      icon: <Icon icon={FiFolder} size={20} />,
      path: '/projects/create'
    }
  ], []);
  
  // User's teams (this would be dynamic in a real app)
  const teamItems: NavItemType[] = useMemo(() => [
    {
      label: 'Design',
      icon: <Icon icon={FiUsers} size={20} />,
      path: '/teams/design'
    },
    {
      label: 'Development',
      icon: <Icon icon={FiUsers} size={20} />,
      path: '/teams/development'
    },
    {
      label: 'Marketing',
      icon: <Icon icon={FiUsers} size={20} />,
      path: '/teams/marketing'
    }
  ], []);
  
  // Define sections
  const navSections: NavSectionType[] = useMemo(() => [
    {
      title: 'QUICK ACCESS',
      items: quickAccessItems,
      collapsible: true
    },
    {
      title: 'MY TEAMS',
      items: teamItems,
      collapsible: true
    }
  ], [quickAccessItems, teamItems]);
  
  // Handle toggling the sidebar
  const handleToggleSidebar = () => {
    dispatch(uiActions.toggleSidebar());
  };
  
  // Handle toggling a section's expanded state
  const handleToggleSection = (sectionTitle: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionTitle]: !prev[sectionTitle]
    }));
  };
  
  // Close sidebar on navigation for mobile devices
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      dispatch(uiActions.setSidebarOpen(false));
    }
  }, [location.pathname, isMobile, sidebarOpen, dispatch]);
  
  return (
    <nav 
      className={classNames(
        "navigation-menu h-full bg-white border-r border-gray-200 transition-all duration-300", 
        {
          "w-64": sidebarOpen,
          "w-16": !sidebarOpen
        },
        className
      )}
      aria-label="Main Navigation"
    >
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
        {sidebarOpen && (
          <h2 className="text-sm font-semibold text-gray-800">NAVIGATION</h2>
        )}
        <button 
          className={classNames("p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100", {
            "ml-auto": sidebarOpen
          })}
          onClick={handleToggleSidebar}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          <Icon icon={FiMenu} size={20} aria-hidden="true" />
        </button>
      </div>
      
      <div className="pt-4 overflow-y-auto h-[calc(100vh-4rem)]">
        <div className="mb-6">
          {mainNavItems.map((item) => (
            hasPermission(user, item.permission, item.roles) && (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  classNames("flex items-center px-4 py-2 text-sm rounded-md mx-2 my-1", {
                    "bg-indigo-50 text-indigo-600": isActive,
                    "text-gray-700 hover:bg-gray-100": !isActive,
                    "justify-center": !sidebarOpen,
                    "justify-start": sidebarOpen
                  })
                }
                title={!sidebarOpen ? item.label : undefined}
              >
                <span className="flex-shrink-0">
                  {item.icon}
                </span>
                {sidebarOpen && (
                  <span className="ml-3 truncate">{item.label}</span>
                )}
              </NavLink>
            )
          ))}
        </div>
        
        {navSections.map((section) => (
          <NavSection
            key={section.title}
            section={section}
            isOpen={!!expandedSections[section.title]}
            onToggle={() => handleToggleSection(section.title)}
            sidebarOpen={sidebarOpen}
            user={user}
          />
        ))}
      </div>
    </nav>
  );
};

export default NavigationMenu;