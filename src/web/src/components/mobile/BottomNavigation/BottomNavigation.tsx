import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import Icon from '../../atoms/Icon/Icon';
import { PATHS } from '../../../routes/paths';
import { useMediaQuery } from '../../../hooks/useMediaQuery';
import { IconType } from 'react-icons';

/**
 * Interface for navigation item configuration
 */
interface NavItem {
  label: string;
  path: string;
  icon: IconType;
}

/**
 * Props for the BottomNavigation component
 */
interface BottomNavigationProps {
  /**
   * Custom navigation items for the bottom bar
   * If not provided, the component won't render
   */
  navItems: NavItem[];
  
  /**
   * CSS media query string for mobile detection
   * @default '(max-width: 640px)'
   */
  mobileBreakpoint?: string;
}

/**
 * A mobile-specific bottom navigation bar component that provides easy access 
 * to primary application routes on small screens.
 * 
 * This component only renders on mobile viewports and displays navigation
 * links with icons for primary application routes.
 */
const BottomNavigation: React.FC<BottomNavigationProps> = ({ 
  navItems,
  mobileBreakpoint = '(max-width: 640px)'
}) => {
  // Get current location to determine active route
  const location = useLocation();
  
  // Check if viewport is mobile size
  const isMobile = useMediaQuery(mobileBreakpoint);
  
  // Function to check if a navigation item is active
  const isActive = (path: string): boolean => {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };
  
  // Only render on mobile viewports
  if (!isMobile) {
    return null;
  }
  
  // Don't render if no navigation items are provided
  if (!navItems || navItems.length === 0) {
    return null;
  }
  
  // Render the bottom navigation bar
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around items-center h-16 z-50">
      {navItems.map((item) => (
        <Link
          key={item.path}
          to={item.path}
          className={`flex flex-col items-center justify-center w-full h-full text-xs ${
            isActive(item.path) 
              ? 'text-primary-600 font-medium' 
              : 'text-gray-500'
          }`}
          aria-current={isActive(item.path) ? 'page' : undefined}
        >
          <Icon 
            icon={item.icon} 
            size={24} 
            className={isActive(item.path) ? 'mb-1 text-primary-600' : 'mb-1 text-gray-500'} 
            ariaLabel={item.label}
          />
          <span>{item.label}</span>
        </Link>
      ))}
    </nav>
  );
};

// Default export of the component
export default BottomNavigation;