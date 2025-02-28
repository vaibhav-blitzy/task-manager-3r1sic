import React, { useState, useEffect, useCallback, useMemo, ReactNode } from 'react'; // react ^18.2.0
import { useParams, useNavigate, useLocation } from 'react-router-dom'; // react-router-dom ^6.15.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.3
import classNames from 'classnames'; // classnames ^2.3.2
import { FiEdit2, FiTrash2, FiPlus, FiCheck } from 'react-icons/fi'; // react-icons/fi ^4.10.0

import {
  useTask,
  useTaskStatusUpdate,
  useTaskAssignment,
  useTaskMutations,
  useTaskComments
} from '../../../api/hooks/useTasks';
import {
  Task,
  TaskStatus,
  TaskPriority,
  TaskComment,
  Subtask
} from '../../../types/task';
import useAuth from '../../../api/hooks/useAuth';
import CommentSection from '../../../components/organisms/CommentSection/CommentSection';
import FileUploader from '../../../components/organisms/FileUploader/FileUploader';
import FileAttachment from '../../../components/molecules/FileAttachment/FileAttachment';
import Button from '../../../components/atoms/Button/Button';
import Input from '../../../components/atoms/Input/Input';
import Avatar from '../../../components/atoms/Avatar/Avatar';
import StatusBadge from '../../../components/molecules/StatusBadge/StatusBadge';
import DatePicker from '../../../components/atoms/DatePicker/DatePicker';
import Checkbox from '../../../components/atoms/Checkbox/Checkbox';
import { canPerformAction } from '../../../utils/permissions';
import { formatDate } from '../../../utils/date';
import ProjectLayout from '../../../components/templates/ProjectLayout/ProjectLayout';
import { PATHS } from '../../../routes/paths';

interface TaskDetailParams {
  taskId: string;
}

/**
 * Main component for displaying and managing detailed task information
 */
const TaskDetail: React.FC = () => {
  // Extract taskId from URL parameters using useParams hook
  const { taskId } = useParams<TaskDetailParams>();

  // Initialize React Router navigation hooks for page navigation
  const navigate = useNavigate();
  const location = useLocation();

  // Fetch detailed task data using useTask hook
  const {
    data: task,
    isLoading,
    error,
    refetch
  } = useTask(taskId || '');

  // Initialize task mutation hooks for updating status, assignment, and other operations
  const { updateStatus, isLoading: isUpdatingStatus } = useTaskStatusUpdate();
  const { assignTask, isLoading: isAssigningTask } = useTaskAssignment();
  const { updateTask, deleteTask, isUpdating: isUpdatingTask, isDeleting: isDeletingTask } = useTaskMutations();

  // Get current user and authentication state using useAuth hook
  const { user, isAuthenticated } = useAuth();

  // Set up state variables for edit mode, form values, and UI state
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState<Date | null>(null);

  // Check user permissions to determine editable elements
  const canEdit = useMemo(() => {
    return isAuthenticated && user && task && canPerformAction(user, 'update', task);
  }, [isAuthenticated, user, task]);

  // Create functions for handling form submissions and action buttons
  const handleStatusChange = useCallback(
    (newStatus: TaskStatus) => {
      if (taskId) {
        updateStatus({ taskId, status: newStatus });
      }
    },
    [taskId, updateStatus]
  );

  const handleAssigneeChange = useCallback(
    (assigneeId: string | null) => {
      if (taskId) {
        assignTask({ taskId, assigneeId });
      }
    },
    [taskId, assignTask]
  );

  const handleEditSubmit = useCallback(async () => {
    if (!taskId) return;

    try {
      await updateTask({
        taskId,
        taskData: {
          title,
          description,
          dueDate: dueDate ? dueDate.toISOString() : null,
          status: task?.status || TaskStatus.CREATED, // Ensure status is always provided
          priority: task?.priority || TaskPriority.MEDIUM, // Ensure priority is always provided
          assigneeId: task?.assignee?.id || null, // Ensure assigneeId is always provided
          tags: task?.tags || [], // Ensure tags is always provided
        },
      });
      setIsEditing(false);
    } catch (error: any) {
      toast.error(`Failed to update task: ${error.message}`);
    }
  }, [taskId, title, description, dueDate, task, updateTask]);

  const handleDeleteTask = useCallback(async () => {
    if (!taskId) return;

    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(taskId);
        navigate(PATHS.TASKS);
      } catch (error: any) {
        toast.error(`Failed to delete task: ${error.message}`);
      }
    }
  }, [taskId, deleteTask, navigate]);

  // Implement subtask management functions for creating, updating, and deleting subtasks
  const handleSubtaskToggle = useCallback(
    async (subtaskId: string, completed: boolean) => {
      // Implementation for toggling subtask completion status
      console.log(`Toggling subtask ${subtaskId} to ${completed}`);
    },
    []
  );

  const handleAddSubtask = useCallback(async (title: string) => {
    // Implementation for adding a new subtask
    console.log(`Adding subtask with title: ${title}`);
  }, []);

  const handleFileUploadComplete = useCallback((files: any) => {
    // Implementation for handling file uploads
    console.log('Uploaded files:', files);
    toast.success(`${files.length} file(s) uploaded successfully`);
    refetch();
  }, [refetch]);

  // Render loading state while task data is being fetched
  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Loading task details...</div>;
  }

  // Render error state if task fetch fails
  if (error) {
    return <div className="flex justify-center items-center h-screen text-red-500">Error: {error.message}</div>;
  }

  // Initialize form values when task data is loaded
  useEffect(() => {
    if (task) {
      setTitle(task.title);
      setDescription(task.description);
      setDueDate(task.dueDate ? new Date(task.dueDate) : null);
    }
  }, [task]);

  // Render task details within appropriate layout (ProjectLayout if task has a project)
  return task?.project ? (
    <ProjectLayout
      backLink={PATHS.PROJECT_DETAIL.replace(':id', task.project.id)}
      title={task.title}
      actions={
        <>
          {canEdit && (
            <Button variant="primary" size="sm" onClick={() => setIsEditing(true)}>
              <FiEdit2 className="mr-2" />
              Edit
            </Button>
          )}
          <Button variant="danger" size="sm" onClick={handleDeleteTask} disabled={isDeletingTask}>
            <FiTrash2 className="mr-2" />
            {isDeletingTask ? 'Deleting...' : 'Delete'}
          </Button>
        </>
      }
    >
      <TaskDetailContent
        task={task}
        isEditing={isEditing}
        onCancelEdit={() => setIsEditing(false)}
        onSaveEdit={handleEditSubmit}
        onStatusChange={handleStatusChange}
        onAssigneeChange={handleAssigneeChange}
        onSubtaskToggle={handleSubtaskToggle}
        onAddSubtask={handleAddSubtask}
        onFileUploadComplete={handleFileUploadComplete}
        title={title}
        setTitle={setTitle}
        description={description}
        setDescription={setDescription}
        dueDate={dueDate}
        setDueDate={setDueDate}
        isUpdatingStatus={isUpdatingStatus}
        isAssigningTask={isAssigningTask}
        isUpdatingTask={isUpdatingTask}
        canEdit={canEdit}
      />
    </ProjectLayout>
  ) : (
    <div className="container mx-auto mt-8 p-4">
      <div className="bg-white shadow rounded-lg p-4">
        <h1 className="text-2xl font-bold mb-4">Task Details</h1>
        <TaskDetailContent
          task={task}
          isEditing={isEditing}
          onCancelEdit={() => setIsEditing(false)}
          onSaveEdit={handleEditSubmit}
          onStatusChange={handleStatusChange}
          onAssigneeChange={handleAssigneeChange}
          onSubtaskToggle={handleSubtaskToggle}
          onAddSubtask={handleAddSubtask}
          onFileUploadComplete={handleFileUploadComplete}
          title={title}
          setTitle={setTitle}
          description={description}
          setDescription={setDescription}
          dueDate={dueDate}
          setDueDate={setDueDate}
          isUpdatingStatus={isUpdatingStatus}
          isAssigningTask={isAssigningTask}
          isUpdatingTask={isUpdatingTask}
          canEdit={canEdit}
        />
      </div>
    </div>
  );
};

interface TaskDetailContentProps {
  task: Task;
  isEditing: boolean;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onStatusChange: (newStatus: TaskStatus) => void;
  onAssigneeChange: (assigneeId: string | null) => void;
  onSubtaskToggle: (subtaskId: string, completed: boolean) => void;
  onAddSubtask: (title: string) => void;
  onFileUploadComplete: (files: any) => void;
  title: string;
  setTitle: (title: string) => void;
  description: string;
  setDescription: (description: string) => void;
  dueDate: Date | null;
  setDueDate: (dueDate: Date | null) => void;
  isUpdatingStatus: boolean;
  isAssigningTask: boolean;
  isUpdatingTask: boolean;
  canEdit: boolean;
}

const TaskDetailContent: React.FC<TaskDetailContentProps> = ({
  task,
  isEditing,
  onCancelEdit,
  onSaveEdit,
  onStatusChange,
  onAssigneeChange,
  onSubtaskToggle,
  onAddSubtask,
  onFileUploadComplete,
  title,
  setTitle,
  description,
  setDescription,
  dueDate,
  setDueDate,
  isUpdatingStatus,
  isAssigningTask,
  isUpdatingTask,
  canEdit
}) => {

  const getStatusOptions = useCallback(() => {
    return Object.values(TaskStatus).map((status) => ({
      value: status,
      label: status.replace(/_/g, ' '),
    }));
  }, []);

  const getPriorityOptions = useCallback(() => {
    return Object.values(TaskPriority).map((priority) => ({
      value: priority,
      label: priority.replace(/_/g, ' '),
    }));
  }, []);

  return (
    <>
      {/* Header Section */}
      <div className="flex items-center justify-between mb-4">
        {isEditing ? (
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Task title"
            className="text-2xl font-bold"
          />
        ) : (
          <h2 className="text-2xl font-bold">{title}</h2>
        )}
        <div>
          {isEditing ? (
            <>
              <Button variant="outline" size="sm" onClick={onCancelEdit}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={onSaveEdit} disabled={isUpdatingTask}>
                {isUpdatingTask ? 'Saving...' : 'Save'}
              </Button>
            </>
          ) : (
            <StatusBadge status={task.status} />
          )}
        </div>
      </div>

      {/* Details Panel */}
      <div className="bg-gray-100 p-4 rounded-md mb-4">
        {isEditing ? (
          <>
            <div className="mb-2">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="task-description">
                Description
              </label>
              <textarea
                id="task-description"
                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="mb-2">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="task-due-date">
                Due Date
              </label>
              <DatePicker
                id="task-due-date"
                value={dueDate}
                onChange={(date) => setDueDate(date)}
                placeholder="Select due date"
              />
            </div>
          </>
        ) : (
          <>
            <p className="text-gray-700">{description}</p>
            <p className="text-gray-500 text-sm">
              Due Date: {task.dueDate ? formatDate(task.dueDate) : 'No due date'}
            </p>
          </>
        )}
      </div>

      {/* Subtasks Section */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Subtasks</h3>
        {task.subtasks && task.subtasks.length > 0 ? (
          <ul>
            {task.subtasks.map((subtask: Subtask) => (
              <li key={subtask.id} className="flex items-center justify-between py-2 border-b border-gray-200">
                <div className="flex items-center">
                  <Checkbox
                    id={`subtask-${subtask.id}`}
                    label={subtask.title}
                    checked={subtask.completed}
                    onChange={(e) => handleSubtaskToggle(subtask.id, e.target.checked)}
                  />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No subtasks yet.</p>
        )}
        <Button variant="text" size="sm" onClick={() => onAddSubtask('New Subtask')}>
          <FiPlus className="mr-2" />
          Add Subtask
        </Button>
      </div>

      {/* File Attachments Section */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">Attachments</h3>
        {task.attachments && task.attachments.length > 0 ? (
          <div className="space-y-2">
            {task.attachments.map((file) => (
              <FileAttachment key={file.id} file={file} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No attachments yet.</p>
        )}
        <FileUploader taskId={task.id} onUploadComplete={onFileUploadComplete} />
      </div>

      {/* Comments Section */}
      <CommentSection taskId={task.id} />
    </>
  );
};

export default TaskDetail;