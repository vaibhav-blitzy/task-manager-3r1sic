import React from 'react';
import classNames from 'classnames';
import { useTheme } from '../../contexts/ThemeContext';
import { useMediaQuery } from '../../hooks/useMediaQuery';

/**
 * Props for the AuthLayout component
 */
interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
}

/**
 * A template component that provides a consistent layout for authentication-related pages
 * such as login, registration, and password recovery. It includes branded elements and
 * a responsive design that adapts to different screen sizes.
 *
 * @param children - The authentication form or content to display
 * @param title - Optional title to display above the authentication form
 * @returns A responsive authentication layout component
 */
const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title }) => {
  // Access the current theme context
  const { theme, colors } = useTheme();
  
  // Check if the viewport is mobile sized
  const isMobile = useMediaQuery('(max-width: 640px)');
  
  return (
    <div 
      className={classNames(
        'min-h-screen w-full flex items-center justify-center p-4',
        theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      )}
      style={{ backgroundColor: colors.background.primary }}
    >
      <div 
        className={classNames(
          'w-full max-w-6xl mx-auto shadow-lg rounded-lg overflow-hidden',
          'flex', isMobile ? 'flex-col' : 'flex-row',
          theme === 'dark' ? 'bg-gray-800' : 'bg-white'
        )}
        style={{ backgroundColor: colors.background.secondary }}
      >
        {/* Branding section */}
        <div 
          className={classNames(
            isMobile ? 'w-full py-8' : 'w-2/5 p-10',
            'flex flex-col items-center justify-center',
            'text-white'
          )}
          style={{ backgroundColor: colors.primary }}
        >
          <div className="text-center">
            {/* Logo placeholder */}
            <div className="mb-6">
              <div className="inline-block w-16 h-16 rounded-full bg-white bg-opacity-20 flex items-center justify-center">
                <span className="text-2xl font-bold">TMS</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold mb-2">Task Management System</h1>
            <p className="mt-2 text-white text-opacity-80">
              Streamline your workflow, boost productivity
            </p>
          </div>
        </div>
        
        {/* Form container section */}
        <div 
          className={classNames(
            isMobile ? 'w-full py-6 px-4' : 'w-3/5 p-10',
            'flex flex-col'
          )}
        >
          {title && (
            <h2 
              className="text-xl font-semibold mb-6 text-center"
              style={{ color: colors.text.primary }}
            >
              {title}
            </h2>
          )}
          {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;