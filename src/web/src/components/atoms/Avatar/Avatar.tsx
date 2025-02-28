import React, { useState } from 'react';
import classNames from 'classnames'; // Version 2.3.x
import { User } from '../../../types/user';

/**
 * Props for the Avatar component
 */
export interface AvatarProps {
  /**
   * User data to display
   */
  user?: User;
  
  /**
   * Size of the avatar
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
  
  /**
   * Whether to show the user's status indicator
   * @default false
   */
  showStatus?: boolean;
  
  /**
   * Additional CSS classes to apply
   */
  className?: string;
  
  /**
   * Optional click handler
   */
  onClick?: () => void;
}

/**
 * Get initials from user's first and last name
 * 
 * @param firstName The user's first name
 * @param lastName The user's last name
 * @returns Initials or a fallback character
 */
const getInitials = (firstName?: string, lastName?: string): string => {
  let initials = '';
  
  if (firstName) {
    initials += firstName.charAt(0);
  }
  
  if (lastName) {
    initials += lastName.charAt(0);
  }
  
  if (initials) {
    return initials.toUpperCase();
  }
  
  return '•'; // Fallback if no name is provided
};

/**
 * Avatar component that displays a user's profile image or initials
 * with optional status indicator
 */
const Avatar = ({
  user,
  size = 'md',
  showStatus = false,
  className = '',
  onClick
}: AvatarProps): JSX.Element => {
  // Track image loading errors to show fallback
  const [imageError, setImageError] = useState(false);
  
  // Determine size classes
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base'
  };
  
  // Determine status indicator position
  const statusPositionClasses = {
    sm: 'w-2 h-2 right-0 bottom-0',
    md: 'w-2.5 h-2.5 right-0 bottom-0',
    lg: 'w-3 h-3 right-0.5 bottom-0.5'
  };
  
  // Get user initials if available
  const initials = user ? getInitials(user.firstName, user.lastName) : '•';
  
  // Handle image loading error
  const handleImageError = () => {
    setImageError(true);
  };
  
  // Determine status color based on user status
  const getStatusColor = (status?: string) => {
    if (!status) return 'bg-gray-400'; // Default gray for unknown status
    
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-500'; // Green for active
      case 'inactive':
        return 'bg-gray-400'; // Gray for inactive
      case 'suspended':
        return 'bg-red-500'; // Red for suspended
      case 'pending':
        return 'bg-yellow-500'; // Yellow for pending
      default:
        return 'bg-gray-400'; // Default gray for unknown status
    }
  };
  
  // Generate a deterministic color based on user name for the fallback avatar
  const getAvatarColor = () => {
    if (!user) return 'bg-gray-400';
    
    const name = `${user.firstName}${user.lastName}`;
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-red-500', 'bg-indigo-500', 'bg-pink-500'];
    
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    return colors[Math.abs(hash % colors.length)];
  };
  
  return (
    <div 
      className={classNames(
        'relative flex items-center justify-center rounded-full overflow-hidden',
        sizeClasses[size],
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={user ? `${user.firstName} ${user.lastName}` : 'User avatar'}
    >
      {user?.profileImageUrl && !imageError ? (
        <img
          src={user.profileImageUrl}
          alt={`${user.firstName} ${user.lastName}`}
          className="w-full h-full object-cover"
          onError={handleImageError}
        />
      ) : (
        <div 
          className={classNames(
            'w-full h-full flex items-center justify-center text-white font-medium',
            getAvatarColor()
          )}
        >
          {initials}
        </div>
      )}
      
      {showStatus && user?.status && (
        <span 
          className={classNames(
            'absolute rounded-full border-2 border-white',
            statusPositionClasses[size],
            getStatusColor(user.status)
          )}
          aria-hidden="true"
        />
      )}
    </div>
  );
};

export default Avatar;