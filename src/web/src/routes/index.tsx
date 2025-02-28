import React, { Suspense, lazy } from 'react'; // react ^18.2.x
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'; // react-router-dom ^6.15.x
import { paths, PATHS } from './paths'; // Path constants for all application routes
import PrivateRoute from './PrivateRoute'; // Component that protects routes requiring authentication
import AuthLayout from '../components/templates/AuthLayout/AuthLayout'; // Layout component for authentication screens
import DashboardLayout from '../components/templates/DashboardLayout/DashboardLayout'; // Layout component for application dashboard
import ProjectLayout from '../components/templates/ProjectLayout/ProjectLayout'; // Layout component for project-related screens

/**
 * Main routing component that defines all application routes with lazy-loaded components and layout wrappers
 * @returns Routes component with nested route definitions for the entire application
 */
const AppRoutes = (): JSX.Element => {
  // Define lazy-loaded page components using React.lazy for code splitting
  const Login = lazy(() => import('../pages/Login'));
  const Register = lazy(() => import('../pages/Register'));
  const ForgotPassword = lazy(() => import('../pages/ForgotPassword'));
  const Dashboard = lazy(() => import('../pages/Dashboard'));
  const Tasks = lazy(() => import('../pages/Tasks'));
  const TaskDetail = lazy(() => import('../pages/TaskDetail'));
  const TaskCreate = lazy(() => import('../pages/TaskCreate'));
  const Projects = lazy(() => import('../pages/Projects'));
  const ProjectDetail = lazy(() => import('../pages/ProjectDetail'));
  const ProjectCreate = lazy(() => import('../pages/ProjectCreate'));
  const Calendar = lazy(() => import('../pages/Calendar'));
  const Reports = lazy(() => import('../pages/Reports'));
  const Notifications = lazy(() => import('../pages/Notifications'));
  const UserSettings = lazy(() => import('../pages/UserSettings'));
  const TeamSettings = lazy(() => import('../pages/TeamSettings'));
  const NotFound = lazy(() => import('../pages/NotFound'));

  // Create a loading fallback for Suspense
  const LoadingFallback = () => <div>Loading...</div>;

  // Define the root Routes component to contain all route definitions
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Create auth routes (login, register, forgot password) with AuthLayout wrapper */}
          <Route path={PATHS.LOGIN} element={<AuthLayout title="Login"><Login /></AuthLayout>} />
          <Route path={PATHS.REGISTER} element={<AuthLayout title="Register"><Register /></AuthLayout>} />
          <Route path={PATHS.FORGOT_PASSWORD} element={<AuthLayout title="Forgot Password"><ForgotPassword /></AuthLayout>} />

          {/* Implement protected application routes using PrivateRoute and DashboardLayout */}
          <Route element={<PrivateRoute />}>
            <Route element={<DashboardLayout />} >
              {/* Define routes for all main features (dashboard, tasks, projects, calendar, reports, etc.) */}
              <Route path={PATHS.DASHBOARD} element={<Dashboard />} />
              <Route path={PATHS.TASKS} element={<Tasks />} />
              <Route path={PATHS.TASK_CREATE} element={<TaskCreate />} />
              <Route path={PATHS.PROJECTS} element={<Projects />} />
              <Route path={PATHS.CALENDAR} element={<Calendar />} />
              <Route path={PATHS.REPORTS} element={<Reports />} />
              <Route path={PATHS.NOTIFICATIONS} element={<Notifications />} />
              <Route path={PATHS.USER_SETTINGS} element={<UserSettings />} />
              <Route path={PATHS.TEAM_SETTINGS} element={<TeamSettings />} />
            </Route>

            {/* Project Routes with ProjectLayout */}
            <Route path={PATHS.PROJECT_DETAIL} element={<ProjectLayout><ProjectDetail /></ProjectLayout>} />
            <Route path={PATHS.PROJECT_CREATE} element={<ProjectLayout><ProjectCreate /></ProjectLayout>} />

            {/* Task Routes with DashboardLayout */}
            <Route path={PATHS.TASK_DETAIL} element={<DashboardLayout><TaskDetail /></DashboardLayout>} />
          </Route>

          {/* Add redirects for convenient navigation patterns */}
          <Route path="/" element={<Navigate to={PATHS.DASHBOARD} replace />} />

          {/* Include a 404 catch-all route for unmatched paths */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default AppRoutes;