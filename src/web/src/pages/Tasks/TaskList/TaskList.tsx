import React, { useState, useEffect, useMemo, useCallback } from 'react'; // react ^18.2.0
import classNames from 'classnames';
import { 
  Task, 
  TaskStatus, 
  TaskPriority, 
  TasksFilter, 
  TaskSort, 
  SortDirection, 
  TasksSortField 
} from '../../../types/task';
import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import TaskList from '../../../components/organisms/TaskList/TaskList';
import Button from '../../../components/atoms/Button/Button';
import SearchBar from '../../../components/molecules/SearchBar/SearchBar';
import { useTasks, useTaskStatusUpdate, useTaskAssignment } from '../../../api/hooks/useTasks';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { selectTaskListFilter, selectTaskListSort } from '../../../store/slices/uiSlice';
import { setTaskListFilter, setTaskListSort } from '../../../store/slices/uiSlice';
import { PATHS } from '../../../routes/paths';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'; // react-router-dom ^6.15.0
import { FaPlus } from 'react-icons/fa'; // react-icons/fa ^4.10.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.0

/**
 * Custom hook to sync URL search parameters with task filters
 */
const useURLFilters = (initialFilter: TasksFilter | undefined): [TasksFilter, (filter: TasksFilter) => void] => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filter, setFilter] = useState<TasksFilter>(initialFilter || {
    status: null,
    priority: null,
    assigneeId: null,
    projectId: null,
    dueDate: null,
    dueDateRange: null,
    tags: null,
    searchTerm: null
  });

  useEffect(() => {
    // Sync URL parameters to filter state on component mount
    const status = searchParams.get('status');
    const priority = searchParams.get('priority');
    const assigneeId = searchParams.get('assigneeId');
    const projectId = searchParams.get('projectId');
    const dueDate = searchParams.get('dueDate');
    const searchTerm = searchParams.get('searchTerm');

    setFilter(prevFilter => ({
      ...prevFilter,
      status: status ? status.split(',') : null,
      priority: priority ? priority.split(',') : null,
      assigneeId: assigneeId || null,
      projectId: projectId || null,
      dueDate: dueDate || null,
      searchTerm: searchTerm || null
    }));
  }, [searchParams]);

  const updateFilter = useCallback((filter: TasksFilter) => {
    // Update both state and URL parameters
    setFilter(filter);

    const params = new URLSearchParams();
    if (filter.status) {
      params.set('status', Array.isArray(filter.status) ? filter.status.join(',') : filter.status);
    }
    if (filter.priority) {
      params.set('priority', Array.isArray(filter.priority) ? filter.priority.join(',') : filter.priority);
    }
    if (filter.assigneeId) {
      params.set('assigneeId', filter.assigneeId);
    }
    if (filter.projectId) {
      params.set('projectId', filter.projectId);
    }
    if (filter.dueDate) {
      params.set('dueDate', filter.dueDate);
    }
    if (filter.searchTerm) {
      params.set('searchTerm', filter.searchTerm);
    }

    setSearchParams(params);
  }, [setSearchParams]);

  return [filter, updateFilter];
};

/**
 * Main task list page component that displays the task management interface with filters, search, and task list
 */
const TaskListPage: React.FC = () => {
  // Get navigation function
  const navigate = useNavigate();

  // Get Redux dispatch and selectors for saved filters and sort preferences
  const dispatch = useAppDispatch();
  const savedFilter = useAppSelector(selectTaskListFilter);
  const savedSort = useAppSelector(selectTaskListSort);

  // Initialize filter state with URL parameters using useURLFilters hook
  const [filter, setFilter] = useURLFilters(savedFilter || undefined);

  // Set up state for search term and sort configuration
  const [searchTerm, setSearchTerm] = useState('');
  const [sort, setSort] = useState(savedSort || { field: TasksSortField.DUE_DATE, direction: SortDirection.ASC });

  // Call useTasks hook with current filter and sort parameters
  const { 
    tasks, 
    isLoading, 
    error,
    refetch
  } = useTasks(filter, sort);

  // Set up task status update mutation
  const { updateStatus, isLoading: isUpdatingStatus } = useTaskStatusUpdate();

  // Set up task assignment mutation
  const { assignTask, isLoading: isAssigningTask } = useTaskAssignment();

  // Create handler for navigating to task detail page
  const handleTaskClick = useCallback((taskId: string) => {
    navigate(PATHS.TASK_DETAIL.replace(':id', taskId));
  }, [navigate]);

  // Create handler for navigating to create task page
  const handleCreateTaskClick = useCallback(() => {
    navigate(PATHS.TASK_CREATE);
  }, [navigate]);

  // Create handlers for filter changes, search term changes, and sort changes
  const handleFilterChange = useCallback((newFilter: TasksFilter) => {
    dispatch(setTaskListFilter(newFilter));
    setFilter(newFilter);
  }, [dispatch, setFilter]);

  const handleSearchTermChange = useCallback((term: string) => {
    setSearchTerm(term);
  }, []);

  const handleSortChange = useCallback((newSort: TaskSort) => {
    dispatch(setTaskListSort(newSort));
    setSort(newSort);
  }, [dispatch]);

  // Update Redux store when filters or sort preferences change
  useEffect(() => {
    dispatch(setTaskListFilter(filter));
  }, [filter, dispatch]);

  useEffect(() => {
    dispatch(setTaskListSort(sort));
  }, [sort, dispatch]);

  return (
    <DashboardLayout title="Tasks">
      {/* Page header with title, search bar, and create task button */}
      <div className="flex justify-between items-center mb-4">
        <SearchBar 
          placeholder="Search tasks..." 
          onSearch={handleSearchTermChange} 
        />
        <Button variant="primary" onClick={handleCreateTaskClick}>
          <FaPlus className="mr-2" />
          Create Task
        </Button>
      </div>

      {/* TaskList organism component with tasks data and handlers */}
      <TaskList
        tasks={tasks}
        loading={isLoading || isUpdatingStatus || isAssigningTask}
        error={error as string}
        onTaskClick={handleTaskClick}
        onStatusChange={(taskId, status) => updateStatus({ taskId, status: { status } })}
        onAssigneeChange={(taskId, assigneeId) => assignTask({ taskId, assigneeId: { assigneeId } })}
        filter={filter}
        onFilterChange={handleFilterChange}
        sort={sort}
        onSortChange={handleSortChange}
      />
    </DashboardLayout>
  );
};

export default TaskListPage;