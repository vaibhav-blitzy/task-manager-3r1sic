// react v18.2.x
import React from 'react'; // Import React
import { lazy } from 'react'; // react v18.2.x

// Define RouteConfig interface for type safety
interface RouteConfig {
  path: string;
  component: React.ComponentType<any>;
  exact?: boolean;
  auth?: boolean;
  roles?: string[];
}

// Lazy load components for code splitting
const Login = lazy(() => import('../pages/Auth/Login/Login'));
const Register = lazy(() => import('../pages/Auth/Register/Register'));
const ForgotPassword = lazy(() => import('../pages/Auth/ForgotPassword/ForgotPassword'));
const Dashboard = lazy(() => import('../pages/Dashboard/Dashboard'));
const TaskList = lazy(() => import('../pages/Tasks/TaskList/TaskList'));
const TaskDetail = lazy(() => import('../pages/Tasks/TaskDetail/TaskDetail'));
const TaskCreate = lazy(() => import('../pages/Tasks/TaskCreate/TaskCreate'));
const ProjectList = lazy(() => import('../pages/Projects/ProjectList/ProjectList'));
const ProjectDetail = lazy(() => import('../pages/Projects/ProjectDetail/ProjectDetail'));
const ProjectCreate = lazy(() => import('../pages/Projects/ProjectCreate/ProjectCreate'));
const Calendar = lazy(() => import('../pages/Calendar/Calendar'));
const NotificationCenter = lazy(() => import('../pages/NotificationCenter/NotificationCenter'));
const ReportsDashboard = lazy(() => import('../pages/Reports/ReportsDashboard/ReportsDashboard'));
const UserSettings = lazy(() => import('../pages/Settings/UserSettings/UserSettings'));
const TeamSettings = lazy(() => import('../pages/Settings/TeamSettings/TeamSettings'));

// Public routes accessible to all users
export const publicRoutes: RouteConfig[] = [
  {
    path: '/login',
    component: Login,
    exact: true,
  },
  {
    path: '/register',
    component: Register,
    exact: true,
  },
  {
    path: '/forgot-password',
    component: ForgotPassword,
    exact: true,
  },
];

// Private routes accessible only to authenticated users
export const privateRoutes: RouteConfig[] = [
  {
    path: '/dashboard',
    component: Dashboard,
    exact: true,
    auth: true,
  },
  {
    path: '/tasks',
    component: TaskList,
    exact: true,
    auth: true,
  },
  {
    path: '/tasks/:id',
    component: TaskDetail,
    exact: true,
    auth: true,
  },
  {
    path: '/tasks/create',
    component: TaskCreate,
    exact: true,
    auth: true,
  },
  {
    path: '/projects',
    component: ProjectList,
    exact: true,
    auth: true,
  },
  {
    path: '/projects/:id',
    component: ProjectDetail,
    exact: true,
    auth: true,
  },
  {
    path: '/projects/create',
    component: ProjectCreate,
    exact: true,
    auth: true,
  },
  {
    path: '/calendar',
    component: Calendar,
    exact: true,
    auth: true,
  },
  {
    path: '/notifications',
    component: NotificationCenter,
    exact: true,
    auth: true,
  },
  {
    path: '/reports',
    component: ReportsDashboard,
    exact: true,
    auth: true,
    roles: ['admin', 'manager'],
  },
  {
    path: '/settings/user',
    component: UserSettings,
    exact: true,
    auth: true,
  },
  {
    path: '/settings/team',
    component: TeamSettings,
    exact: true,
    auth: true,
    roles: ['admin', 'manager'],
  },
];

// Export routes for use in the application
const routes = {
  publicRoutes,
  privateRoutes,
};

export default routes;