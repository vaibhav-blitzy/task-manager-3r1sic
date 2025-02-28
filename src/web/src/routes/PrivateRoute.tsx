import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuth from '../api/hooks/useAuth';
import { PATHS } from './paths';
import { Role } from '../types/auth';

/**
 * Component that wraps protected routes and redirects unauthenticated users to the login page.
 * Implements route-level access control as part of the RBAC system.
 * 
 * @returns JSX.Element - Either the child routes via Outlet or redirect to login
 */
const PrivateRoute: React.FC = () => {
  // Get authentication state using useAuth hook
  const { isAuthenticated, user } = useAuth();
  
  // Get current location to enable redirect back after login
  const location = useLocation();
  
  // Check if user is authenticated
  if (!isAuthenticated) {
    // If not authenticated, redirect to login page with current location as state
    // This allows redirecting back to the originally requested page after successful login
    return <Navigate to={PATHS.LOGIN} state={{ from: location }} replace />;
  }
  
  // If authenticated, render the child routes using Outlet component
  return <Outlet />;
};

export default PrivateRoute;