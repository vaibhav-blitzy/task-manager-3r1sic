import React, { useState, useEffect, useMemo, useCallback } from 'react'; // react ^18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.0
import classNames from 'classnames'; // classnames ^2.3.0
import { FaChevronLeft, FaChevronRight, FaPlus } from 'react-icons/fa'; // react-icons/fa ^4.10.0

import DashboardLayout from '../../components/templates/DashboardLayout/DashboardLayout';
import TaskCard from '../../components/molecules/TaskCard/TaskCard';
import StatusBadge from '../../components/molecules/StatusBadge/StatusBadge';
import Button from '../../components/atoms/Button/Button';
import SearchBar from '../../components/molecules/SearchBar/SearchBar';
import { Task, TasksFilter } from '../../types/task';
import { useTasks } from '../../api/hooks/useTasks';
import { useProjects } from '../../api/hooks/useProjects';
import { formatDate, getMonthDays, isSameDay, isToday } from '../../utils/date';
import { PATHS } from '../../routes/paths';

/**
 * Helper function to get all days in a month including padding from previous/next months
 * @param year 
 * @param month 
 * @returns {Date[]} Array of date objects representing all days in the calendar view
 */
const getDaysInMonth = (year: number, month: number): Date[] => {
  // Use getMonthDays utility to get days in the specified month
  const monthDays = getMonthDays(year, month);
  
  // Add padding days from previous month to start from Sunday
  // Add padding days from next month to complete the last week
  // Return complete array of date objects for calendar grid
  return monthDays;
};

/**
 * Helper function to organize tasks by their due dates
 * @param {Task[]} tasks
 * @returns {Record<string, Task[]>} Map of date strings to arrays of tasks
 */
const groupTasksByDate = (tasks: Task[]): Record<string, Task[]> => {
  // Initialize empty object to store tasks by date
  const groupedTasks: Record<string, Task[]> = {};

  // Loop through tasks array
  for (const task of tasks) {
    // For each task with a dueDate, format date to YYYY-MM-DD string
    if (task.dueDate) {
      const date = formatDate(task.dueDate, 'YYYY-MM-DD');

      // Group tasks by this formatted date string
      if (groupedTasks[date]) {
        groupedTasks[date].push(task);
      } else {
        groupedTasks[date] = [task];
      }
    }
  }

  // Return the grouped tasks object
  return groupedTasks;
};

/**
 * Component that renders the calendar header with navigation and controls
 * @param {object} props
 * @returns {JSX.Element} Rendered header component
 */
const CalendarHeader: React.FC<{
  currentDate: Date;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onToday: () => void;
  onSearchChange: (searchTerm: string) => void;
  projectFilter: string | null;
  projects: any[];
  onProjectFilterChange: (projectId: string | null) => void;
}> = ({
  currentDate,
  onPrevMonth,
  onNextMonth,
  onToday,
  onSearchChange,
  projectFilter,
  projects,
  onProjectFilterChange,
}) => {
  // Format current month and year for display
  const monthYear = formatDate(currentDate, 'MMMM YYYY');

  // Render header container with flexbox layout
  return (
    <div className="flex items-center justify-between mb-4">
      {/* Month/Year Title */}
      <h2 className="text-xl font-semibold">{monthYear}</h2>

      {/* Navigation Buttons */}
      <div>
        <Button variant="text" size="sm" onClick={onPrevMonth} icon={<FaChevronLeft />}>
          Previous
        </Button>
        <Button variant="text" size="sm" onClick={onToday}>
          Today
        </Button>
        <Button variant="text" size="sm" onClick={onNextMonth} icon={<FaChevronRight />} iconPosition="right">
          Next
        </Button>
      </div>

      {/* Project Filter Dropdown (Placeholder) */}
      <div>
        <select
          value={projectFilter || ''}
          onChange={(e) => onProjectFilterChange(e.target.value || null)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="">All Projects</option>
          {projects.map((project: any) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* Search Input */}
      <SearchBar placeholder="Search tasks..." onSearch={onSearchChange} size="sm" />

      {/* Create Task Button */}
      <Button variant="primary" size="sm">
        <FaPlus className="mr-2" />
        Create Task
      </Button>
    </div>
  );
};

/**
 * Component that renders a single day cell in the calendar
 * @param {object} props
 * @returns {JSX.Element} Rendered day cell component
 */
const CalendarDay: React.FC<{
  date: Date;
  tasks: Task[];
  isCurrentMonth: boolean;
  onClick: (date: Date) => void;
  onTaskClick: (task: Task) => void;
}> = ({ date, tasks, isCurrentMonth, onClick, onTaskClick }) => {
  // Determine day styling based on isCurrentMonth, isToday, etc.
  const dayClasses = classNames(
    'calendar-day',
    'p-2',
    'border',
    'flex',
    'flex-col',
    'h-32',
    'overflow-hidden',
    'transition-colors',
    {
      'bg-gray-50 border-gray-200': isCurrentMonth,
      'bg-gray-100 border-gray-300': !isCurrentMonth,
      'bg-blue-100': isToday(date),
      'cursor-pointer hover:bg-blue-200': isCurrentMonth,
    }
  );

  // Sort tasks by priority
  const sortedTasks = [...tasks].sort((a, b) => a.priority.localeCompare(b.priority));

  // Limit displayed tasks with 'more' indicator if needed
  const visibleTasks = sortedTasks.slice(0, 3);
  const hasMoreTasks = sortedTasks.length > 3;

  // Render day container with appropriate styling
  return (
    <div className={dayClasses} onClick={() => onClick(date)}>
      {/* Day Number in Header */}
      <div className="text-sm font-medium text-gray-700 mb-1">{date.getDate()}</div>

      {/* Render Tasks as Compact TaskCard Components */}
      {visibleTasks.map((task) => (
        <TaskCard key={task.id} task={task} compact onClick={() => onTaskClick(task)} />
      ))}

      {/* Add '+more' Text if Tasks Exceed Display Limit */}
      {hasMoreTasks && <div className="text-xs text-gray-500">+ more</div>}
    </div>
  );
};

/**
 * Main calendar component that displays a monthly view with tasks
 * @returns {JSX.Element} Rendered calendar component
 */
const Calendar: React.FC = () => {
  // Initialize state for current date (month/year view)
  const [currentDate, setCurrentDate] = useState(new Date());

  // Initialize state for selected project filter
  const [projectFilter, setProjectFilter] = useState<string | null>(null);

  // Initialize state for task search query
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize state for selected date (for task creation)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Get navigator function using useNavigate hook
  const navigate = useNavigate();

  // Calculate first and last day of current month view
  const firstDayOfMonth = useMemo(() => new Date(currentDate.getFullYear(), currentDate.getMonth(), 1), [currentDate]);
  const lastDayOfMonth = useMemo(() => new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0), [currentDate]);

  // Build task filter with date range and optional project filter
  const taskFilter: TasksFilter = useMemo(() => ({
    dueDateRange: {
      startDate: formatDate(firstDayOfMonth, API_DATE_FORMAT) || '',
      endDate: formatDate(lastDayOfMonth, API_DATE_FORMAT) || '',
    },
    projectId: projectFilter,
    status: null,
    priority: null,
    assigneeId: null,
    tags: null,
    searchTerm: searchQuery,
    dueDate: null,
  }), [firstDayOfMonth, lastDayOfMonth, projectFilter, searchQuery]);

  // Fetch tasks using useTasks hook with filter
  const { tasks, isLoading } = useTasks(taskFilter);

  // Fetch projects using useProjects hook for filter dropdown
  const { projects } = useProjects();

  // Use useMemo to generate days array for current month
  const days = useMemo(() => getDaysInMonth(currentDate.getFullYear(), currentDate.getMonth()), [currentDate]);

  // Use useMemo to group tasks by date
  const groupedTasks = useMemo(() => groupTasksByDate(tasks), [tasks]);

  // Define handler for navigating to previous month
  const handlePrevMonth = useCallback(() => {
    setCurrentDate((prevDate) => new Date(prevDate.getFullYear(), prevDate.getMonth() - 1, 1));
  }, []);

  // Define handler for navigating to next month
  const handleNextMonth = useCallback(() => {
    setCurrentDate((prevDate) => new Date(prevDate.getFullYear(), prevDate.getMonth() + 1, 1));
  }, []);

  // Define handler for returning to current month
  const handleToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  // Define handler for day click (select date for task creation)
  const handleDayClick = useCallback((date: Date) => {
    setSelectedDate(date);
  }, []);

  // Define handler for task click (navigate to task details)
  const handleTaskClick = useCallback((task: Task) => {
    navigate(PATHS.TASK_DETAIL.replace(':id', task.id));
  }, [navigate]);

  // Define handler for project filter change
  const handleProjectFilterChange = useCallback((projectId: string | null) => {
    setProjectFilter(projectId);
  }, []);

  // Define handler for search query change
  const handleSearchChange = useCallback((searchTerm: string) => {
    setSearchQuery(searchTerm);
  }, []);

  // Define handler for creating a new task with pre-filled date
  const handleCreateTask = useCallback(() => {
    if (selectedDate) {
      // Navigate to task creation page with pre-filled date
      navigate(PATHS.TASKS_CREATE + `?dueDate=${formatDateToISO(selectedDate)}`);
    } else {
      // Navigate to task creation page without pre-filled date
      navigate(PATHS.TASKS_CREATE);
    }
  }, [navigate, selectedDate]);

  // Render DashboardLayout wrapper
  return (
    <DashboardLayout title="Calendar">
      {/* Render CalendarHeader component with navigation controls */}
      <CalendarHeader
        currentDate={currentDate}
        onPrevMonth={handlePrevMonth}
        onNextMonth={handleNextMonth}
        onToday={handleToday}
        onSearchChange={handleSearchChange}
        projectFilter={projectFilter}
        projects={projects}
        onProjectFilterChange={handleProjectFilterChange}
      />

      {/* Render weekday headers (Sun, Mon, Tue, etc.) */}
      <div className="grid grid-cols-7 gap-2 mb-2 text-center">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div key={day} className="text-sm font-medium text-gray-500">
            {day}
          </div>
        ))}
      </div>

      {/* Render calendar grid with CalendarDay components */}
      <div className="grid grid-cols-7 gap-2">
        {days.map((date) => {
          const dateString = formatDate(date, 'YYYY-MM-DD');
          const tasksForDate = groupedTasks[dateString] || [];
          return (
            <CalendarDay
              key={date.toISOString()}
              date={date}
              tasks={tasksForDate}
              isCurrentMonth={date.getMonth() === currentDate.getMonth()}
              onClick={handleDayClick}
              onTaskClick={handleTaskClick}
            />
          );
        })}
      </div>

      {/* Apply loading state visual treatment if tasks are loading */}
      {isLoading && (
        <div className="absolute top-0 left-0 w-full h-full bg-gray-100 opacity-50 flex items-center justify-center">
          Loading...
        </div>
      )}
    </DashboardLayout>
  );
};

export default Calendar;