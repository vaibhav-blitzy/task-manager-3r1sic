import React, { useState, useEffect, useMemo, useCallback } from 'react';
import classNames from 'classnames'; // v2.3.2
import { 
  Task, 
  TaskStatus, 
  TaskPriority, 
  TasksFilter, 
  TaskSort, 
  SortDirection, 
  TasksSortField 
} from '../../../types/task';
import TaskCard from '../../molecules/TaskCard/TaskCard';
import SearchBar from '../../molecules/SearchBar/SearchBar';
import StatusBadge from '../../molecules/StatusBadge/StatusBadge';
import Button from '../../atoms/Button/Button';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { setTaskListFilter, setTaskListSort } from '../../../store/slices/uiSlice';
import { useTasks, useTaskStatusUpdate, useTaskAssignment } from '../../../api/hooks/useTasks';

interface TaskListProps {
  tasks: Task[];
  loading: boolean;
  error: string;
  onTaskClick?: (task: Task) => void;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
  onAssigneeChange?: (taskId: string, assigneeId: string | null) => void;
  filter: TasksFilter;
  onFilterChange?: (filter: TasksFilter) => void;
  view?: string;
  sort: TaskSort;
  onSortChange?: (sort: TaskSort) => void;
  className?: string;
  showFilters?: boolean;
  emptyStateMessage?: string;
}

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  loading,
  error,
  onTaskClick,
  onStatusChange,
  onAssigneeChange,
  filter,
  onFilterChange,
  view = 'list',
  sort,
  onSortChange,
  className = '',
  showFilters = true,
  emptyStateMessage = 'No tasks found matching your criteria'
}) => {
  // Local state
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [localFilter, setLocalFilter] = useState<TasksFilter>(filter);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  
  // Redux
  const dispatch = useAppDispatch();
  
  // Set up mutation handlers
  const { updateStatus } = useTaskStatusUpdate();
  const { assignTask } = useTaskAssignment();
  
  // Sync local filter with props and reset pagination when filter changes
  useEffect(() => {
    setLocalFilter(filter);
    setCurrentPage(1);
  }, [filter]);
  
  // Handle task selection
  const handleTaskClick = useCallback((task: Task) => {
    setSelectedTaskId(task.id);
    if (onTaskClick) {
      onTaskClick(task);
    }
  }, [onTaskClick]);
  
  // Handle status change
  const handleStatusChange = useCallback((taskId: string, newStatus: TaskStatus) => {
    updateStatus({ 
      taskId, 
      status: { status: newStatus } 
    });
    
    if (onStatusChange) {
      onStatusChange(taskId, newStatus);
    }
  }, [updateStatus, onStatusChange]);
  
  // Handle assignee change
  const handleAssigneeChange = useCallback((taskId: string, newAssigneeId: string | null) => {
    assignTask({ 
      taskId, 
      assigneeId: { assigneeId: newAssigneeId } 
    });
    
    if (onAssigneeChange) {
      onAssigneeChange(taskId, newAssigneeId);
    }
  }, [assignTask, onAssigneeChange]);
  
  // Handle filter change
  const handleFilterChange = useCallback((newFilter: TasksFilter) => {
    setLocalFilter(newFilter);
    setCurrentPage(1); // Reset to first page when filter changes
    
    if (onFilterChange) {
      onFilterChange(newFilter);
    }
  }, [onFilterChange]);
  
  // Handle search
  const handleSearch = useCallback((searchTerm: string) => {
    const newFilter = {
      ...localFilter,
      searchTerm: searchTerm || null
    };
    handleFilterChange(newFilter);
  }, [localFilter, handleFilterChange]);
  
  // Handle sort change
  const handleSortChange = useCallback((field: TasksSortField) => {
    const newDirection = 
      sort.field === field && sort.direction === SortDirection.ASC
        ? SortDirection.DESC
        : SortDirection.ASC;
    
    const newSort: TaskSort = {
      field,
      direction: newDirection
    };
    
    if (onSortChange) {
      onSortChange(newSort);
    }
  }, [sort, onSortChange]);
  
  // Apply client-side filtering/sorting if needed
  const filteredAndSortedTasks = useMemo(() => {
    // Apply client-side sorting
    return [...tasks].sort((a, b) => {
      switch (sort.field) {
        case TasksSortField.TITLE:
          return sort.direction === SortDirection.ASC
            ? a.title.localeCompare(b.title)
            : b.title.localeCompare(a.title);
            
        case TasksSortField.DUE_DATE:
          if (!a.dueDate && !b.dueDate) return 0;
          if (!a.dueDate) return sort.direction === SortDirection.ASC ? 1 : -1;
          if (!b.dueDate) return sort.direction === SortDirection.ASC ? -1 : 1;
          return sort.direction === SortDirection.ASC
            ? new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime()
            : new Date(b.dueDate).getTime() - new Date(a.dueDate).getTime();
            
        case TasksSortField.PRIORITY:
          const priorityValues = {
            [TaskPriority.URGENT]: 3,
            [TaskPriority.HIGH]: 2,
            [TaskPriority.MEDIUM]: 1,
            [TaskPriority.LOW]: 0
          };
          return sort.direction === SortDirection.ASC
            ? priorityValues[a.priority] - priorityValues[b.priority]
            : priorityValues[b.priority] - priorityValues[a.priority];
            
        case TasksSortField.STATUS:
          return sort.direction === SortDirection.ASC
            ? a.status.localeCompare(b.status)
            : b.status.localeCompare(a.status);
            
        default:
          return 0;
      }
    });
  }, [tasks, sort]);
  
  // Apply pagination
  const paginatedTasks = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredAndSortedTasks.slice(startIndex, endIndex);
  }, [filteredAndSortedTasks, currentPage, itemsPerPage]);
  
  // Calculate total pages
  const totalPages = Math.ceil(filteredAndSortedTasks.length / itemsPerPage);
  
  // Handle page change
  const handlePageChange = useCallback((newPage: number) => {
    setCurrentPage(newPage);
  }, []);
  
  // Render loading state
  if (loading) {
    return (
      <div className={classNames('p-4 flex justify-center items-center', className)}>
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-6 w-24 bg-gray-200 rounded mb-2"></div>
          <div className="text-gray-500">Loading tasks...</div>
        </div>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className={classNames('p-4 text-error', className)}>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p>Error loading tasks: {error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className={classNames('task-list', className)}>
      {/* Header with search and filters */}
      <div className="task-list-header mb-4 flex flex-wrap justify-between items-center gap-2">
        {showFilters && (
          <>
            <SearchBar 
              onSearch={handleSearch}
              placeholder="Search tasks..."
              showResults={false}
              size="md"
            />
            
            <div className="flex flex-wrap gap-2 items-center">
              <div className="text-sm text-gray-500">
                Showing {filteredAndSortedTasks.length} tasks
              </div>
            </div>
          </>
        )}
      </div>
      
      {/* Task list */}
      {filteredAndSortedTasks.length > 0 ? (
        <>
          {view === 'card' ? (
            // Card view
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {paginatedTasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onClick={() => handleTaskClick(task)}
                  selected={selectedTaskId === task.id}
                />
              ))}
            </div>
          ) : (
            // List view
            <div className="task-list-table overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th 
                      className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                      onClick={() => handleSortChange(TasksSortField.TITLE)}
                    >
                      <div className="flex items-center">
                        Task
                        {sort.field === TasksSortField.TITLE && (
                          <span className="ml-1">
                            {sort.direction === SortDirection.ASC ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Assignee
                    </th>
                    <th 
                      className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                      onClick={() => handleSortChange(TasksSortField.DUE_DATE)}
                    >
                      <div className="flex items-center">
                        Due Date
                        {sort.field === TasksSortField.DUE_DATE && (
                          <span className="ml-1">
                            {sort.direction === SortDirection.ASC ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                    <th 
                      className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                      onClick={() => handleSortChange(TasksSortField.PRIORITY)}
                    >
                      <div className="flex items-center">
                        Priority
                        {sort.field === TasksSortField.PRIORITY && (
                          <span className="ml-1">
                            {sort.direction === SortDirection.ASC ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {paginatedTasks.map(task => (
                    <tr 
                      key={task.id} 
                      className={classNames(
                        'hover:bg-gray-50 transition-colors cursor-pointer',
                        { 'bg-primary-50': selectedTaskId === task.id }
                      )}
                      onClick={() => handleTaskClick(task)}
                    >
                      <td className="px-4 py-2 whitespace-nowrap">
                        <StatusBadge status={task.status} />
                      </td>
                      <td className="px-4 py-2">
                        <div className="font-medium text-gray-900">{task.title}</div>
                        {task.project && (
                          <div className="text-sm text-gray-500">{task.project.name}</div>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        {task.assignee ? (
                          <div className="flex items-center">
                            <div className="ml-2 text-sm font-medium text-gray-900">
                              {task.assignee.firstName} {task.assignee.lastName}
                            </div>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">Unassigned</span>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm">
                        {task.dueDate ? (
                          <span className={classNames({
                            'text-red-600': task.dueDate && new Date(task.dueDate) < new Date(),
                            'text-yellow-600': task.dueDate && 
                              new Date(task.dueDate) >= new Date() && 
                              new Date(task.dueDate) <= new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
                            'text-gray-700': task.dueDate && 
                              new Date(task.dueDate) > new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
                          })}>
                            {new Date(task.dueDate).toLocaleDateString()}
                          </span>
                        ) : (
                          <span className="text-gray-500">No due date</span>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap">
                        {task.priority === TaskPriority.URGENT ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                            Urgent
                          </span>
                        ) : task.priority === TaskPriority.HIGH ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-red-50 text-red-700">
                            High
                          </span>
                        ) : task.priority === TaskPriority.MEDIUM ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
                            Medium
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-blue-50 text-blue-700">
                            Low
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 px-4 py-2 border-t">
              <div className="text-sm text-gray-500">
                Showing {Math.min((currentPage - 1) * itemsPerPage + 1, filteredAndSortedTasks.length)} to {Math.min(currentPage * itemsPerPage, filteredAndSortedTasks.length)} of {filteredAndSortedTasks.length} tasks
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  variant="outline"
                  size="sm"
                >
                  Previous
                </Button>
                <div className="flex items-center mx-2">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    // Show pages around current page
                    let pageToShow = i + 1;
                    if (totalPages > 5) {
                      if (currentPage > 3) {
                        pageToShow = currentPage - 3 + i;
                      }
                      if (pageToShow > totalPages) {
                        pageToShow = totalPages - (4 - i);
                      }
                    }
                    
                    return (
                      <Button
                        key={i}
                        onClick={() => handlePageChange(pageToShow)}
                        variant={currentPage === pageToShow ? "primary" : "outline"}
                        size="sm"
                        className="mx-1 min-w-[32px]"
                      >
                        {pageToShow}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  variant="outline"
                  size="sm"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      ) : (
        // Empty state
        <div className="p-8 text-center">
          <div className="inline-block p-4 rounded-full bg-gray-100 mb-4">
            <svg 
              className="h-12 w-12 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={1.5} 
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No tasks found</h3>
          <p className="text-gray-500">{emptyStateMessage}</p>
        </div>
      )}
    </div>
  );
};

export default TaskList;