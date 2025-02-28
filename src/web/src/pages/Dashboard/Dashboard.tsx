import React, { useState, useEffect, useMemo } from 'react'; // react ^18.2.0
import classNames from 'classnames'; // classnames ^2.3.2
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.4.0

import { DashboardLayout } from '../../components/templates/DashboardLayout/DashboardLayout';
import TaskList from '../../components/organisms/TaskList/TaskList';
import ProjectCard from '../../components/organisms/ProjectCard/ProjectCard';
import Button from '../../components/atoms/Button/Button';
import PieChart from '../../components/organisms/Charts/PieChart/PieChart';
import useAuth from '../../api/hooks/useAuth';
import { 
  useDueSoonTasks, 
  useOverdueTasks, 
  useMyTasks,
  useTaskStatistics
} from '../../api/hooks/useTasks';
import { useProjects } from '../../api/hooks/useProjects';
import { TaskStatus, TaskPriority } from '../../types/task';
import { useMediaQuery } from '../../hooks/useMediaQuery';

/**
 * The main dashboard component displaying the overview of tasks, projects, and activities
 * @returns {JSX.Element} The rendered dashboard page
 */
const Dashboard: React.FC = () => {
  // Initialize navigate function from useNavigate for navigation to detail pages
  const navigate = useNavigate();

  // Get current user data from useAuth hook
  const { user } = useAuth();

  // Get screen size information using useMediaQuery for responsive layout
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(min-width: 641px) and (max-width: 1024px)');

  // Fetch tasks due today and within the next 7 days using useDueSoonTasks hook
  const { 
    tasks: dueSoonTasks, 
    isLoading: isLoadingDueSoon, 
    error: dueSoonError 
  } = useDueSoonTasks(7);

  // Fetch overdue tasks using useOverdueTasks hook
  const { 
    tasks: overdueTasks, 
    isLoading: isLoadingOverdue, 
    error: overdueError 
  } = useOverdueTasks();

  // Fetch assigned tasks for current user using useMyTasks hook
  const { 
    tasks: assignedTasks, 
    isLoading: isLoadingAssigned, 
    error: assignedError 
  } = useMyTasks();

  // Fetch user's projects using useProjects with filter for current user
  const { 
    projects, 
    isLoading: isLoadingProjects, 
    error: projectsError 
  } = useProjects();

  // Fetch task statistics using useTaskStatistics hook
  const { 
    statistics: taskStats, 
    isLoading: isLoadingStats, 
    error: statsError 
  } = useTaskStatistics();

  // Transform task statistics data for pie chart visualization
  const chartData = useMemo(() => {
    if (!taskStats) return [];
    return transformTaskStatsForChart(taskStats);
  }, [taskStats]);

  // Define handlers for task and project click navigation
  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
  };

  const handleProjectClick = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  // Calculate widget layout dimensions based on current screen size
  const widgetColSpan = isMobile ? 'col-span-1' : isTablet ? 'col-span-1' : 'col-span-2';

  // Return DashboardLayout component with welcome message and grid of widgets
  return (
    <DashboardLayout title="Dashboard">
      <div className="grid gap-6">
        {/* Welcome Message */}
        <div className="text-xl font-semibold text-gray-800 dark:text-white">
          Welcome back, {user?.firstName}
        </div>

        {/* Tasks Due Soon widget */}
        <div className={classNames("bg-white dark:bg-gray-800 shadow rounded-md p-4", widgetColSpan)}>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
            Tasks Due Soon
          </h2>
          <TaskList
            tasks={dueSoonTasks}
            loading={isLoadingDueSoon}
            error={dueSoonError?.message || ''}
            onTaskClick={handleTaskClick}
            compact
            showFilters={false}
            emptyStateMessage="No tasks due soon"
          />
          <div className="mt-2 text-right">
            <Button variant="text" size="sm">
              View All Tasks
            </Button>
          </div>
        </div>

        {/* Project Progress widget */}
        <div className={classNames("bg-white dark:bg-gray-800 shadow rounded-md p-4", widgetColSpan)}>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
            Project Progress
          </h2>
          {projects.slice(0, 3).map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => handleProjectClick(project.id)}
              compact
              showMembers={false}
              showTags={false}
            />
          ))}
          <div className="mt-2 text-right">
            <Button variant="text" size="sm">
              View All Projects
            </Button>
          </div>
        </div>

        {/* Task Status widget */}
        <div className={classNames("bg-white dark:bg-gray-800 shadow rounded-md p-4", widgetColSpan)}>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
            Task Status
          </h2>
          {isLoadingStats ? (
            <div>Loading...</div>
          ) : statsError ? (
            <div>Error: {statsError}</div>
          ) : (
            <PieChart data={chartData} showLegend={!isMobile} showLabels={isMobile} />
          )}
        </div>

        {/* Activity widget */}
        <div className={classNames("bg-white dark:bg-gray-800 shadow rounded-md p-4", widgetColSpan)}>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
            Activity
          </h2>
          <div>Recent activity items will be displayed here.</div>
        </div>

        {/* Recent Comments widget */}
        <div className={classNames("bg-white dark:bg-gray-800 shadow rounded-md p-4", widgetColSpan)}>
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-2">
            Recent Comments
          </h2>
          <div>Latest comments from tasks will be displayed here.</div>
        </div>

        {/* Quick Actions */}
        <div className="flex justify-end gap-4">
          <Button variant="primary">Create New Task</Button>
          <Button variant="secondary">Create New Project</Button>
        </div>
      </div>
    </DashboardLayout>
  );
};

/**
 * Transforms task statistics data into format required by PieChart component
 * @param {object} taskStats
 * @returns {array} Array of objects with label, value, and color for chart data
 */
const transformTaskStatsForChart = (taskStats: any) => {
  const statusMap = {
    [TaskStatus.CREATED]: { label: 'Not Started', color: getStatusColor(TaskStatus.CREATED) },
    [TaskStatus.ASSIGNED]: { label: 'Assigned', color: getStatusColor(TaskStatus.ASSIGNED) },
    [TaskStatus.IN_PROGRESS]: { label: 'In Progress', color: getStatusColor(TaskStatus.IN_PROGRESS) },
    [TaskStatus.ON_HOLD]: { label: 'On Hold', color: getStatusColor(TaskStatus.ON_HOLD) },
    [TaskStatus.IN_REVIEW]: { label: 'In Review', color: getStatusColor(TaskStatus.IN_REVIEW) },
    [TaskStatus.COMPLETED]: { label: 'Completed', color: getStatusColor(TaskStatus.COMPLETED) },
    [TaskStatus.CANCELLED]: { label: 'Cancelled', color: getStatusColor(TaskStatus.CANCELLED) },
  };

  return Object.entries(statusMap)
    .map(([status, { label, color }]) => ({
      label,
      value: taskStats.byStatus[status] || 0,
      color,
    }))
    .filter(item => item.value > 0);
};

/**
 * Returns appropriate color for each task status
 * @param {TaskStatus} status
 * @returns {string} Color hex code for the status
 */
const getStatusColor = (status: TaskStatus): string => {
  switch (status) {
    case TaskStatus.COMPLETED:
      return '#22C55E'; // Emerald
    case TaskStatus.IN_PROGRESS:
      return '#8B5CF6'; // Purple
    case TaskStatus.ON_HOLD:
      return '#F59E0B'; // Amber
    case TaskStatus.IN_REVIEW:
      return '#10B981'; // Green
    case TaskStatus.CANCELLED:
      return '#EF4444'; // Red
    case TaskStatus.CREATED:
    case TaskStatus.ASSIGNED:
      return '#6B7280'; // Gray
    default:
      return '#9CA3AF'; // Neutral Gray
  }
};

/**
 * Formats a date string to relative format (Today, Yesterday, etc.)
 * @param {string} dateString
 * @returns {string} Formatted relative date string
 */
const formatDateRelative = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const diffDays = Math.ceil(diff / (1000 * 3600 * 24));

  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Tomorrow';
  } else if (diffDays === -1) {
    return 'Yesterday';
  } else if (diffDays < -1 && diffDays > -7) {
    return `Last ${date.toLocaleDateString(undefined, { weekday: 'long' })}`;
  } else if (diffDays > 1 && diffDays < 7) {
    return `This ${date.toLocaleDateString(undefined, { weekday: 'long' })}`;
  } else {
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
  }
};

export default Dashboard;