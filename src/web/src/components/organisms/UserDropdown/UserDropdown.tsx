import React, { useState, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.0
import classNames from 'classnames'; // classnames ^2.3.2
import { FaUser, FaCog, FaSun, FaMoon, FaSignOutAlt } from 'react-icons/fa'; // react-icons v4.10.0
import { IconType } from 'react-icons';

import { Avatar } from '../../atoms/Avatar/Avatar';
import { Button } from '../../atoms/Button/Button';
import { Icon } from '../../atoms/Icon/Icon';
import useOutsideClick from '../../../hooks/useOutsideClick';
import useAuth from '../../../api/hooks/useAuth';
import { User } from '../../../types/user';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { selectUser, logout } from '../../../store/slices/authSlice';
import { hasPermission } from '../../../utils/permissions';
import { PATHS } from '../../../routes/paths';
import { useTheme } from '../../../contexts/ThemeContext';

interface UserDropdownProps {
  className?: string;
}

interface MenuItem {
  id: string;
  label: string;
  icon: IconType;
  path?: string;
  onClick?: () => void;
  permission?: string;
  divider?: boolean;
}

/**
 * A dropdown component that shows user information and menu options
 */
const UserDropdown: React.FC<UserDropdownProps> = ({ className }) => {
  // Get user data from Redux store
  const user = useAppSelector(selectUser);
  const dispatch = useAppDispatch();
  
  // Get theme toggle function
  const { theme, toggleTheme } = useTheme();
  
  // Get navigation function
  const navigate = useNavigate();
  
  // State to track if dropdown is open
  const [isOpen, setIsOpen] = useState<boolean>(false);
  
  // Ref for dropdown container
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Setup outside click detection to close dropdown
  useOutsideClick(dropdownRef, () => {
    if (isOpen) {
      setIsOpen(false);
    }
  });
  
  // Toggle dropdown visibility
  const toggleDropdown = useCallback(() => {
    setIsOpen(prevState => !prevState);
  }, []);
  
  // Handle logout
  const handleLogout = useCallback(() => {
    dispatch(logout());
    navigate(PATHS.LOGIN);
  }, [dispatch, navigate]);
  
  // Handle theme toggle
  const handleThemeToggle = useCallback(() => {
    toggleTheme();
  }, [toggleTheme]);
  
  // Define menu items with proper icon components
  const menuItems: MenuItem[] = [
    {
      id: 'profile',
      label: 'My Profile',
      icon: FaUser,
      path: PATHS.USER_SETTINGS,
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: FaCog,
      path: PATHS.USER_SETTINGS,
      divider: true,
    },
    {
      id: 'theme',
      label: theme === 'dark' ? 'Light Mode' : 'Dark Mode',
      icon: theme === 'dark' ? FaSun : FaMoon,
      onClick: handleThemeToggle,
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: FaSignOutAlt,
      onClick: handleLogout,
    },
  ];
  
  // Filter menu items based on permissions
  const filteredMenuItems = menuItems.filter(item => {
    if (item.permission && user) {
      return hasPermission(user, item.permission);
    }
    return true;
  });
  
  return (
    <div className={classNames('relative', className)}>
      {/* Avatar button to toggle dropdown */}
      <button
        type="button"
        className="flex items-center focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 rounded-full"
        onClick={toggleDropdown}
        aria-expanded={isOpen}
        aria-controls="user-dropdown"
      >
        <Avatar user={user} size="md" className="cursor-pointer" />
      </button>
      
      {/* Dropdown menu */}
      {isOpen && (
        <div
          ref={dropdownRef}
          id="user-dropdown"
          className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 z-10"
          role="menu"
          aria-orientation="vertical"
          aria-labelledby="user-menu"
        >
          {/* User profile section */}
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center">
              <Avatar user={user} size="sm" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user?.firstName} {user?.lastName}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
          
          {/* Menu items */}
          <div className="py-1" role="none">
            {filteredMenuItems.map((item) => (
              <React.Fragment key={item.id}>
                {item.path ? (
                  <Link
                    to={item.path}
                    className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    role="menuitem"
                    onClick={() => setIsOpen(false)}
                  >
                    <Icon icon={item.icon} className="mr-2 text-gray-500 dark:text-gray-400" size={16} />
                    {item.label}
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    role="menuitem"
                    onClick={() => {
                      item.onClick?.();
                      setIsOpen(false);
                    }}
                  >
                    <Icon icon={item.icon} className="mr-2 text-gray-500 dark:text-gray-400" size={16} />
                    {item.label}
                  </button>
                )}
                {item.divider && (
                  <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserDropdown;