import React, { useState, useEffect, useMemo, useCallback } from 'react'; // react ^18.2.0
import { useParams, useNavigate, Navigate, Outlet } from 'react-router-dom'; // react-router-dom ^6.10.0
import classNames from 'classnames'; // classnames ^2.3.2
import {
  FiPlus,
  FiList,
  FiGrid,
  FiUsers,
  FiSettings,
  FiBarChart2,
} from 'react-icons/fi'; // react-icons/fi ^4.10.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.0

import {
  Project,
  ProjectStatus,
  TaskList,
  ProjectFormData,
} from '../../../types/project';
import { TaskStatus, Task } from '../../../types/task';
import {
  useProject,
  useProjectMutation,
  useProjectMembers,
  useProjectTaskLists,
  useProjectStatistics,
} from '../../../api/hooks/useProjects';
import {
  useProjectTasks,
  useTaskMutations,
  useTaskStatusUpdate,
} from '../../../api/hooks/useTasks';
import useAuth from '../../../api/hooks/useAuth';
import { ProjectLayout } from '../../../components/templates/ProjectLayout/ProjectLayout';
import TaskBoard from '../../../components/organisms/TaskBoard/TaskBoard';
import TaskListComp from '../../../components/organisms/TaskList/TaskList';
import Button from '../../../components/atoms/Button/Button';
import Avatar from '../../../components/atoms/Avatar/Avatar';
import useWebSocket from '../../../hooks/useWebSocket';
import { PATHS } from '../../../routes/paths';
import { canPerformAction } from '../../../utils/permissions';

interface ProjectDetailParams {
  projectId: string;
}

interface ProjectDetailTab {
  id: string;
  label: string;
  icon: React.ReactNode;
}

enum ViewMode {
  BOARD = 'board',
  LIST = 'list',
}

/**
 * Main component for the project detail page that displays project information, tasks, and provides management capabilities
 */
const ProjectDetail: React.FC = () => {
  // Extract projectId from URL params using useParams hook
  const { projectId } = useParams<ProjectDetailParams>();

  // Initialize state for current view mode (board/list) and active tab
  const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.BOARD);
  const [activeTab, setActiveTab] = useState<string>('board');

  // Get navigation function using useNavigate hook
  const navigate = useNavigate();

  // Get authentication state and user info using useAuth hook
  const { user } = useAuth();

  // Fetch project data using useProject hook with projectId
  const {
    project,
    isLoading: isProjectLoading,
    error: projectError,
    refetch: refetchProject,
  } = useProject(projectId || '');

  // Fetch project tasks using useProjectTasks hook with projectId
  const {
    tasks,
    isLoading: isTasksLoading,
    error: tasksError,
    refetch: refetchTasks,
  } = useProjectTasks(projectId || '');

  // Get project mutation functions using useProjectMutation hook
  const {
    updateProject: { mutate: updateProject },
    deleteProject: { mutate: deleteProject },
  } = useProjectMutation();

  // Get task mutation functions using useTaskMutations hook
  const { createTask: { mutate: createTask } } = useTaskMutations();

  // Get task status update function using useTaskStatusUpdate hook
  const { updateStatus } = useTaskStatusUpdate();

  // Fetch project members using useProjectMembers hook
  const {
    members,
    isLoading: isMembersLoading,
    error: membersError,
    refetch: refetchMembers,
  } = useProjectMembers(projectId || '');

  // Fetch project task lists using useProjectTaskLists hook
  const {
    taskLists,
    isLoading: isTaskListsLoading,
    error: taskListsError,
    refetch: refetchTaskLists,
  } = useProjectTaskLists(projectId || '');

  // Fetch project statistics using useProjectStatistics hook
  const {
    statistics,
    isLoading: isStatisticsLoading,
    error: statisticsError,
    refetch: refetchStatistics,
  } = useProjectStatistics(projectId || '');

  // Set up WebSocket connection for real-time updates using useWebSocket hook
  const { subscribe, unsubscribe } = useWebSocket();

  // Define tabs for project navigation (Board/List, Team, Settings, Analytics)
  const tabs: ProjectDetailTab[] = useMemo(
    () => [
      { id: 'board', label: 'Board', icon: <FiGrid /> },
      { id: 'list', label: 'List', icon: <FiList /> },
      { id: 'team', label: 'Team', icon: <FiUsers /> },
      { id: 'settings', label: 'Settings', icon: <FiSettings /> },
      { id: 'analytics', label: 'Analytics', icon: <FiBarChart2 /> },
    ],
    []
  );

  // Create handler for switching between board and list views
  const handleViewModeChange = useCallback(
    (mode: ViewMode) => {
      setViewMode(mode);
    },
    []
  );

  // Create handler for adding new tasks to the project
  const handleAddTask = useCallback(
    (status: TaskStatus) => {
      // Navigate to task creation page with pre-filled project and status
      navigate(`/tasks/create?projectId=${projectId}&status=${status}`);
    },
    [navigate, projectId]
  );

  // Create handler for task click that navigates to task detail page
  const handleTaskClick = useCallback(
    (task: Task) => {
      navigate(`/tasks/${task.id}`);
    },
    [navigate]
  );

  // Create handler for project status change
  const handleStatusChange = useCallback(
    (status: ProjectStatus) => {
      if (project) {
        updateProject({
          id: project.id,
          data: { ...project, status },
        } as any);
      }
    },
    [project, updateProject]
  );

  // Check user permissions for project and task operations
  const canEditProject = useMemo(
    () => user && canPerformAction(user, 'update', { type: 'project' }),
    [user]
  );
  const canCreateTask = useMemo(
    () => user && canPerformAction(user, 'create', { type: 'task' }),
    [user]
  );

  // Handle tab navigation and active tab state
  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId);
  }, []);

  // Render loading state while project data is being fetched
  if (isProjectLoading) {
    return <div>Loading project details...</div>;
  }

  // Render error state if project data fetch fails
  if (projectError) {
    return <div>Error: {projectError.message}</div>;
  }

  return (
    <ProjectLayout title={project?.name}>
      {/* Tab navigation for switching between different project views */}
      <nav className="mb-4">
        <ul className="flex space-x-4">
          {tabs.map((tab) => (
            <li key={tab.id}>
              <button
                className={classNames(
                  'py-2 px-4 rounded-md',
                  activeTab === tab.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
                onClick={() => handleTabChange(tab.id)}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Render active tab content based on current tab selection */}
      {activeTab === 'board' || activeTab === 'list' ? (
        <ProjectTaskManagement
          project={project}
          tasks={tasks}
          viewMode={viewMode}
          handleTaskClick={handleTaskClick}
          handleAddTask={handleAddTask}
        />
      ) : activeTab === 'team' ? (
        <ProjectTeam project={project} refetchMembers={refetchMembers} />
      ) : activeTab === 'settings' ? (
        <ProjectSettings
          project={project}
          updateProject={updateProject}
          deleteProject={deleteProject}
        />
      ) : activeTab === 'analytics' ? (
        <ProjectAnalytics projectId={projectId} statistics={statistics} />
      ) : null}
    </ProjectLayout>
  );
};

interface ProjectTaskManagementProps {
  project: Project;
  tasks: Task[];
  viewMode: ViewMode;
  handleTaskClick: (task: Task) => void;
  handleAddTask: (status: TaskStatus) => void;
}

const ProjectTaskManagement: React.FC<ProjectTaskManagementProps> = ({
  project,
  tasks,
  viewMode,
  handleTaskClick,
  handleAddTask,
}) => {
  return (
    <div>
      {viewMode === ViewMode.BOARD ? (
        <TaskBoard tasks={tasks} onTaskClick={handleTaskClick} onAddTask={handleAddTask} />
      ) : (
        <TaskListComp tasks={tasks} onTaskClick={handleTaskClick} />
      )}
    </div>
  );
};

interface ProjectTeamProps {
  project: Project;
  refetchMembers: () => void;
}

const ProjectTeam: React.FC<ProjectTeamProps> = ({ project, refetchMembers }) => {
  return <div>ProjectTeam Component</div>;
};

interface ProjectSettingsProps {
  project: Project;
  updateProject: (data: any) => void;
  deleteProject: (projectId: string) => void;
}

const ProjectSettings: React.FC<ProjectSettingsProps> = ({ project, updateProject, deleteProject }) => {
  return <div>ProjectSettings Component</div>;
};

interface ProjectAnalyticsProps {
  projectId: string;
  statistics: any;
}

const ProjectAnalytics: React.FC<ProjectAnalyticsProps> = ({ projectId, statistics }) => {
  return <div>ProjectAnalytics Component</div>;
};

export default ProjectDetail;