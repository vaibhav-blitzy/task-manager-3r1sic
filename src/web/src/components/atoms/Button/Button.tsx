import React from 'react'; // react ^18.2.0
import classNames from 'classnames'; // classnames ^2.3.2

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * The visual style of the button
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'text';
  
  /**
   * The size of the button
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
  
  /**
   * Whether the button should take up the full width of its container
   * @default false
   */
  isFullWidth?: boolean;
  
  /**
   * Whether the button is in a loading state
   * @default false
   */
  isLoading?: boolean;
  
  /**
   * Optional icon to display within the button
   */
  icon?: React.ReactNode;
  
  /**
   * Position of the icon within the button
   * @default 'left'
   */
  iconPosition?: 'left' | 'right';
  
  /**
   * Additional CSS classes to apply to the button
   */
  className?: string;
}

/**
 * A versatile button component supporting various styles, sizes, and states
 * for use throughout the task management application.
 */
const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isFullWidth = false,
  isLoading = false,
  icon,
  iconPosition = 'left',
  className,
  disabled,
  ...props
}) => {
  // Generate variant-specific classes
  const variantClasses = {
    'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus:ring-primary-500': 
      variant === 'primary',
    'bg-secondary-600 text-white hover:bg-secondary-700 active:bg-secondary-800 focus:ring-secondary-500': 
      variant === 'secondary',
    'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:bg-gray-100 focus:ring-primary-500': 
      variant === 'outline',
    'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus:ring-red-500': 
      variant === 'danger',
    'bg-transparent text-gray-700 hover:bg-gray-100 active:bg-gray-200 focus:ring-primary-500': 
      variant === 'text',
  };

  // Generate size-specific classes
  const sizeClasses = {
    'px-2.5 py-1.5 text-xs': size === 'sm',
    'px-4 py-2 text-sm': size === 'md',
    'px-6 py-3 text-base': size === 'lg',
  };

  // Additional conditional classes
  const additionalClasses = {
    'w-full': isFullWidth,
    'opacity-50 cursor-not-allowed': disabled || isLoading,
    'flex items-center justify-center': true, // Always use flex for consistent alignment
  };

  // Combine all classes with potential custom className
  const buttonClasses = classNames(
    'font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200',
    variantClasses,
    sizeClasses,
    additionalClasses,
    className
  );

  // Loading spinner SVG component
  const loadingSpinner = (
    <svg 
      className={classNames(
        'animate-spin h-4 w-4 mr-2', 
        { 'text-white': ['primary', 'secondary', 'danger'].includes(variant) },
        { 'text-primary-500': ['outline', 'text'].includes(variant) }
      )}
      xmlns="http://www.w3.org/2000/svg" 
      fill="none" 
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle 
        className="opacity-25" 
        cx="12" 
        cy="12" 
        r="10" 
        stroke="currentColor" 
        strokeWidth="4"
      />
      <path 
        className="opacity-75" 
        fill="currentColor" 
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  return (
    <button
      type="button"
      disabled={disabled || isLoading}
      className={buttonClasses}
      aria-busy={isLoading}
      {...props}
    >
      {/* Show loading spinner when in loading state */}
      {isLoading && loadingSpinner}
      
      {/* Show left-positioned icon when not loading */}
      {!isLoading && icon && iconPosition === 'left' && (
        <span className="mr-2" aria-hidden="true">
          {icon}
        </span>
      )}
      
      {/* Button text/children */}
      {children}
      
      {/* Show right-positioned icon when not loading */}
      {!isLoading && icon && iconPosition === 'right' && (
        <span className="ml-2" aria-hidden="true">
          {icon}
        </span>
      )}
    </button>
  );
};

export { Button };