/**
 * Analytics utility functions for processing, formatting, and analyzing analytics data
 * in the Task Management System. Provides calculations for metrics, data transformations,
 * and chart visualization preparations.
 * 
 * @version 1.0.0
 */

import { formatDate, getDateRangeForPeriod } from '../../../utils/date';
import { TaskStatus, TaskPriority, Task, TaskStatistics } from '../../../types/task';
import { ProjectStatus, Project, ProjectStatistics } from '../../../types/project';
import { Dashboard, Widget, Metric } from '../../../api/services/analyticsService';

/**
 * Calculates the percentage of completed tasks relative to total tasks
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Percentage of completed tasks (0-100)
 */
export function calculateTaskCompletionRate(tasks: Task[]): number {
  if (!tasks.length) return 0;
  
  const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED);
  return (completedTasks.length / tasks.length) * 100;
}

/**
 * Calculates the percentage of tasks completed before or on their due date
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Percentage of on-time task completions (0-100)
 */
export function calculateOnTimeCompletionRate(tasks: Task[]): number {
  const completedTasks = tasks.filter(task => task.status === TaskStatus.COMPLETED);
  const completedTasksWithDueDate = completedTasks.filter(task => task.dueDate !== null);
  
  if (!completedTasksWithDueDate.length) return 0;
  
  const onTimeTasks = completedTasksWithDueDate.filter(task => {
    const dueDate = new Date(task.dueDate as string);
    const completedDate = new Date(task.metadata.completedAt as string);
    return completedDate <= dueDate;
  });
  
  return (onTimeTasks.length / completedTasksWithDueDate.length) * 100;
}

/**
 * Calculates the average age of tasks in days from creation to now or completion
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Average task age in days
 */
export function calculateAverageTaskAge(tasks: Task[]): number {
  if (!tasks.length) return 0;
  
  const now = new Date();
  const totalAgeDays = tasks.reduce((sum, task) => {
    const creationDate = new Date(task.metadata.created);
    const endDate = task.status === TaskStatus.COMPLETED 
      ? new Date(task.metadata.completedAt as string) 
      : now;
    
    const ageInDays = (endDate.getTime() - creationDate.getTime()) / (1000 * 60 * 60 * 24);
    return sum + ageInDays;
  }, 0);
  
  return totalAgeDays / tasks.length;
}

/**
 * Calculates the average time in days from task creation to completion
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Average cycle time in days
 */
export function calculateCycleTime(tasks: Task[]): number {
  const completedTasks = tasks.filter(task => 
    task.status === TaskStatus.COMPLETED && task.metadata.completedAt !== null
  );
  
  if (!completedTasks.length) return 0;
  
  const totalCycleTimeDays = completedTasks.reduce((sum, task) => {
    const creationDate = new Date(task.metadata.created);
    const completionDate = new Date(task.metadata.completedAt as string);
    
    const cycleTimeInDays = (completionDate.getTime() - creationDate.getTime()) / (1000 * 60 * 60 * 24);
    return sum + cycleTimeInDays;
  }, 0);
  
  return totalCycleTimeDays / completedTasks.length;
}

/**
 * Calculates the average time in days from task request to delivery/completion
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Average lead time in days
 */
export function calculateLeadTime(tasks: Task[]): number {
  const completedTasks = tasks.filter(task => 
    task.status === TaskStatus.COMPLETED && task.metadata.completedAt !== null
  );
  
  if (!completedTasks.length) return 0;
  
  const totalLeadTimeDays = completedTasks.reduce((sum, task) => {
    // In a real system, we might have a requestDate field for when the task was requested
    // before it was created in the system. For this implementation, we'll use creation date
    const requestDate = new Date(task.metadata.created);
    const deliveryDate = new Date(task.metadata.completedAt as string);
    
    const leadTimeInDays = (deliveryDate.getTime() - requestDate.getTime()) / (1000 * 60 * 60 * 24);
    return sum + leadTimeInDays;
  }, 0);
  
  return totalLeadTimeDays / completedTasks.length;
}

/**
 * Groups tasks by their status and returns counts for each status
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Object with status keys and count values
 */
export function getTasksByStatus(tasks: Task[]): Record<TaskStatus, number> {
  // Initialize counts for all statuses
  const statusCounts: Record<TaskStatus, number> = {
    [TaskStatus.CREATED]: 0,
    [TaskStatus.ASSIGNED]: 0,
    [TaskStatus.IN_PROGRESS]: 0,
    [TaskStatus.ON_HOLD]: 0,
    [TaskStatus.IN_REVIEW]: 0,
    [TaskStatus.COMPLETED]: 0,
    [TaskStatus.CANCELLED]: 0
  };
  
  // Count tasks for each status
  tasks.forEach(task => {
    statusCounts[task.status]++;
  });
  
  return statusCounts;
}

/**
 * Groups tasks by their priority and returns counts for each priority level
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Object with priority keys and count values
 */
export function getTasksByPriority(tasks: Task[]): Record<TaskPriority, number> {
  // Initialize counts for all priorities
  const priorityCounts: Record<TaskPriority, number> = {
    [TaskPriority.LOW]: 0,
    [TaskPriority.MEDIUM]: 0,
    [TaskPriority.HIGH]: 0,
    [TaskPriority.URGENT]: 0
  };
  
  // Count tasks for each priority
  tasks.forEach(task => {
    priorityCounts[task.priority]++;
  });
  
  return priorityCounts;
}

/**
 * Calculates the distribution of active tasks across assignees
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Object with userId keys and task count values
 */
export function getWorkloadDistribution(tasks: Task[]): Record<string, number> {
  // Only consider active tasks (not completed or cancelled)
  const activeTasks = tasks.filter(task => 
    task.status !== TaskStatus.COMPLETED && 
    task.status !== TaskStatus.CANCELLED
  );
  
  // Initialize the workload distribution object
  const workload: Record<string, number> = {};
  
  // Count tasks for each assignee
  activeTasks.forEach(task => {
    if (task.assignee) {
      const assigneeId = task.assignee.id;
      workload[assigneeId] = (workload[assigneeId] || 0) + 1;
    }
  });
  
  return workload;
}

/**
 * Identifies workflow bottlenecks by finding statuses with high task counts and long durations
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Array of potential bottlenecks with status, count, and duration info
 */
export function identifyBottlenecks(tasks: Task[]): Array<{
  status: TaskStatus;
  count: number;
  averageDuration: number;
}> {
  if (!tasks.length) return [];
  
  // Group tasks by status
  const tasksByStatus = getTasksByStatus(tasks);
  
  // Calculate average time spent in each status
  const statusDurations: Record<TaskStatus, number> = {
    [TaskStatus.CREATED]: 0,
    [TaskStatus.ASSIGNED]: 0,
    [TaskStatus.IN_PROGRESS]: 0,
    [TaskStatus.ON_HOLD]: 0,
    [TaskStatus.IN_REVIEW]: 0,
    [TaskStatus.COMPLETED]: 0,
    [TaskStatus.CANCELLED]: 0
  };
  
  // We would need detailed task history for precise calculations
  // This is a simplified approach based on current task statuses and timestamps
  const now = new Date();
  
  tasks.forEach(task => {
    const creationDate = new Date(task.metadata.created);
    const lastUpdated = new Date(task.metadata.lastUpdated);
    
    // For completed tasks, use completion time; for others, use current time or last update
    const endDate = task.status === TaskStatus.COMPLETED 
      ? new Date(task.metadata.completedAt as string) 
      : now;
    
    const durationDays = (endDate.getTime() - creationDate.getTime()) / (1000 * 60 * 60 * 24);
    
    statusDurations[task.status] += durationDays;
  });
  
  // Calculate average duration for each status
  Object.keys(statusDurations).forEach(status => {
    const statusKey = status as TaskStatus;
    const count = tasksByStatus[statusKey];
    if (count > 0) {
      statusDurations[statusKey] /= count;
    }
  });
  
  // Calculate average counts and durations across all statuses
  const statusKeys = Object.keys(tasksByStatus) as TaskStatus[];
  const avgCount = statusKeys.reduce((sum, status) => sum + tasksByStatus[status], 0) / statusKeys.length;
  const avgDuration = statusKeys.reduce((sum, status) => sum + statusDurations[status], 0) / statusKeys.length;
  
  // Identify bottlenecks (statuses with above-average counts and durations)
  const bottlenecks = statusKeys
    .filter(status => 
      // Don't consider completed or cancelled as bottlenecks
      status !== TaskStatus.COMPLETED && 
      status !== TaskStatus.CANCELLED &&
      // Consider statuses with above-average counts or durations
      (tasksByStatus[status] > avgCount || statusDurations[status] > avgDuration)
    )
    .map(status => ({
      status,
      count: tasksByStatus[status],
      averageDuration: statusDurations[status]
    }))
    // Sort by a combined score of count and duration
    .sort((a, b) => 
      (b.count * b.averageDuration) - (a.count * a.averageDuration)
    );
  
  return bottlenecks;
}

/**
 * Calculates burndown chart data showing remaining work over time
 * 
 * @param tasks - Array of tasks to analyze
 * @param startDate - ISO string representing the start date
 * @param endDate - ISO string representing the end date
 * @returns Daily data points for burndown chart
 */
export function calculateBurndownData(
  tasks: Task[],
  startDate: string,
  endDate: string
): Array<{ date: string; remainingTasks: number; idealLine: number }> {
  // Parse dates
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  // Count total tasks at the beginning
  const totalTasks = tasks.length;
  
  // Generate date points for each day between start and end
  const datePoints: Array<{ date: string; remainingTasks: number; idealLine: number }> = [];
  const daysDifference = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  
  for (let i = 0; i <= daysDifference; i++) {
    const currentDate = new Date(start.getTime());
    currentDate.setDate(start.getDate() + i);
    const currentDateString = currentDate.toISOString().split('T')[0];
    
    // Count tasks completed on or before this date
    const completedTasksCount = tasks.filter(task => {
      if (task.status !== TaskStatus.COMPLETED || !task.metadata.completedAt) {
        return false;
      }
      
      const completedDate = new Date(task.metadata.completedAt);
      return completedDate <= currentDate;
    }).length;
    
    // Calculate remaining tasks
    const remainingTasks = totalTasks - completedTasksCount;
    
    // Calculate ideal burndown line (linear progression from start to end)
    const idealTasksRemaining = Math.max(0, totalTasks - (totalTasks * (i / daysDifference)));
    
    // Add data point
    datePoints.push({
      date: currentDateString,
      remainingTasks,
      idealLine: Math.round(idealTasksRemaining)
    });
  }
  
  return datePoints;
}

/**
 * Transforms raw analytics data into a format suitable for chart visualization
 * 
 * @param data - Raw data to transform
 * @param chartType - Type of chart to prepare data for
 * @returns Formatted data ready for chart components
 */
export function prepareChartData(data: any, chartType: string): object {
  // Status colors from constants
  const statusColors = {
    'created': '#6B7280',
    'assigned': '#3B82F6',
    'in-progress': '#8B5CF6',
    'on-hold': '#F59E0B',
    'in-review': '#10B981',
    'completed': '#22C55E',
    'cancelled': '#EF4444'
  };
  
  // Priority colors from constants
  const priorityColors = {
    'low': '#6B7280',
    'medium': '#3B82F6',
    'high': '#F59E0B',
    'urgent': '#EF4444'
  };
  
  // Default color palette for other chart types
  const defaultColors = [
    '#4F46E5', '#9333EA', '#22C55E', '#F59E0B', '#EF4444',
    '#3B82F6', '#14B8A6', '#8B5CF6', '#EC4899', '#10B981'
  ];
  
  switch(chartType) {
    case 'pie': {
      // For pie charts, we need labels and data points with colors
      const labels: string[] = [];
      const values: number[] = [];
      const colors: string[] = [];
      
      // Determine if we're dealing with status or priority data
      if (data.hasOwnProperty(TaskStatus.CREATED) || data.hasOwnProperty('created')) {
        // Status data
        Object.entries(data).forEach(([status, count]) => {
          labels.push(status);
          values.push(count as number);
          colors.push(statusColors[status as keyof typeof statusColors] || defaultColors[0]);
        });
      } else if (data.hasOwnProperty(TaskPriority.LOW) || data.hasOwnProperty('low')) {
        // Priority data
        Object.entries(data).forEach(([priority, count]) => {
          labels.push(priority);
          values.push(count as number);
          colors.push(priorityColors[priority as keyof typeof priorityColors] || defaultColors[0]);
        });
      } else {
        // Generic data
        Object.entries(data).forEach(([key, value], index) => {
          labels.push(key);
          values.push(value as number);
          colors.push(defaultColors[index % defaultColors.length]);
        });
      }
      
      return {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderWidth: 1
        }]
      };
    }
    
    case 'bar': {
      // For bar charts
      const labels: string[] = [];
      const values: number[] = [];
      const colors: string[] = [];
      
      // Determine data type and format accordingly
      if (data.hasOwnProperty(TaskStatus.CREATED) || data.hasOwnProperty('created')) {
        // Status data
        Object.entries(data).forEach(([status, count]) => {
          labels.push(status);
          values.push(count as number);
          colors.push(statusColors[status as keyof typeof statusColors] || defaultColors[0]);
        });
      } else if (data.hasOwnProperty(TaskPriority.LOW) || data.hasOwnProperty('low')) {
        // Priority data
        Object.entries(data).forEach(([priority, count]) => {
          labels.push(priority);
          values.push(count as number);
          colors.push(priorityColors[priority as keyof typeof priorityColors] || defaultColors[0]);
        });
      } else {
        // Generic data (e.g., workload distribution)
        Object.entries(data).forEach(([key, value], index) => {
          labels.push(key);
          values.push(value as number);
          colors.push(defaultColors[index % defaultColors.length]);
        });
      }
      
      return {
        labels,
        datasets: [{
          label: 'Count',
          data: values,
          backgroundColor: colors,
          borderWidth: 1
        }]
      };
    }
    
    case 'line': {
      // For line charts (often time series data)
      if (Array.isArray(data)) {
        // Assume data is an array of points with date and value properties
        const labels = data.map(point => formatDate(point.date));
        
        // For burndown charts with multiple lines
        if (data[0] && data[0].hasOwnProperty('idealLine')) {
          return {
            labels,
            datasets: [
              {
                label: 'Actual',
                data: data.map(point => point.remainingTasks),
                borderColor: '#4F46E5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                fill: true
              },
              {
                label: 'Ideal',
                data: data.map(point => point.idealLine),
                borderColor: '#22C55E',
                backgroundColor: 'transparent',
                borderDashed: [5, 5],
                fill: false
              }
            ]
          };
        }
        
        // For simple line charts
        return {
          labels,
          datasets: [{
            label: 'Value',
            data: data.map(point => point.value),
            borderColor: '#4F46E5',
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            fill: true
          }]
        };
      }
      
      // For multiple data series
      const datasets = Object.entries(data).map(([key, values], index) => ({
        label: key,
        data: (values as any[]).map(v => v.value),
        borderColor: defaultColors[index % defaultColors.length],
        backgroundColor: `${defaultColors[index % defaultColors.length]}20`,
        fill: true
      }));
      
      // Assume all series have the same x-values
      const labels = data[Object.keys(data)[0]]
        ? (data[Object.keys(data)[0]] as any[]).map(point => formatDate(point.date))
        : [];
      
      return {
        labels,
        datasets
      };
    }
    
    default:
      // Return data as-is if chart type is not recognized
      return data;
  }
}

/**
 * Calculates comprehensive task statistics for analytics
 * 
 * @param tasks - Array of tasks to analyze
 * @returns Object containing various task statistics
 */
export function calculateTaskStatistics(tasks: Task[]): TaskStatistics {
  // Calculate total task count
  const total = tasks.length;
  
  // Calculate counts by status
  const byStatus = getTasksByStatus(tasks);
  
  // Calculate counts by priority
  const byPriority = getTasksByPriority(tasks);
  
  // Calculate completed tasks in last 7 days
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  
  const completedLast7Days = tasks.filter(task => {
    if (task.status !== TaskStatus.COMPLETED || !task.metadata.completedAt) {
      return false;
    }
    
    const completedDate = new Date(task.metadata.completedAt);
    return completedDate >= sevenDaysAgo;
  }).length;
  
  // Calculate tasks due soon (next 3 days)
  const now = new Date();
  const threeDaysFromNow = new Date();
  threeDaysFromNow.setDate(now.getDate() + 3);
  
  const dueSoon = tasks.filter(task => {
    if (!task.dueDate || task.status === TaskStatus.COMPLETED || task.status === TaskStatus.CANCELLED) {
      return false;
    }
    
    const dueDate = new Date(task.dueDate);
    return dueDate >= now && dueDate <= threeDaysFromNow;
  }).length;
  
  // Calculate overdue tasks
  const overdue = tasks.filter(task => {
    if (!task.dueDate || task.status === TaskStatus.COMPLETED || task.status === TaskStatus.CANCELLED) {
      return false;
    }
    
    const dueDate = new Date(task.dueDate);
    return dueDate < now;
  }).length;
  
  return {
    total,
    byStatus,
    byPriority,
    completedLast7Days,
    dueSoon,
    overdue
  };
}

/**
 * Calculates comprehensive project statistics for analytics
 * 
 * @param project - Project to analyze
 * @param projectTasks - Tasks belonging to the project
 * @returns Object containing various project statistics
 */
export function calculateProjectStatistics(project: Project, projectTasks: Task[]): ProjectStatistics {
  // Calculate task completion rate
  const taskCompletionRate = calculateTaskCompletionRate(projectTasks);
  
  // Calculate on-time completion rate
  const onTimeCompletionRate = calculateOnTimeCompletionRate(projectTasks);
  
  // Group tasks by status
  const tasksByStatus = getTasksByStatus(projectTasks);
  
  // Calculate tasks by assignee
  const tasksByAssignee = getWorkloadDistribution(projectTasks);
  
  // Count activities in the last week
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  
  // We would count activities from task.activity field
  // This is a simplified approach counting activities based on last update
  const activitiesLastWeek = projectTasks.reduce((count, task) => {
    const lastUpdated = new Date(task.metadata.lastUpdated);
    const activityCount = task.activity.filter(a => {
      const activityDate = new Date(a.timestamp);
      return activityDate >= sevenDaysAgo;
    }).length;
    
    return count + activityCount;
  }, 0);
  
  // Count overdue tasks
  const now = new Date();
  const overdueTasks = projectTasks.filter(task => {
    if (!task.dueDate || task.status === TaskStatus.COMPLETED || task.status === TaskStatus.CANCELLED) {
      return false;
    }
    
    const dueDate = new Date(task.dueDate);
    return dueDate < now;
  }).length;
  
  return {
    taskCompletionRate,
    onTimeCompletionRate,
    tasksByStatus,
    tasksByAssignee,
    activitiesLastWeek,
    overdueTasks
  };
}

/**
 * Generates a human-readable label for a time range
 * 
 * @param startDate - ISO string representing the start date
 * @param endDate - ISO string representing the end date
 * @returns Formatted time range label
 */
export function getTimeRangeLabel(startDate: string, endDate: string): string {
  const formattedStart = formatDate(startDate);
  const formattedEnd = formatDate(endDate);
  
  return `${formattedStart} - ${formattedEnd}`;
}

/**
 * Calculates date range for predefined time periods
 * 
 * @param period - Predefined period (day, week, month, quarter, year)
 * @returns Object with ISO formatted start and end dates
 */
export function getTimePeriodRange(period: string): { startDate: string; endDate: string } {
  const { startDate, endDate } = getDateRangeForPeriod(period);
  
  return {
    startDate: startDate.toISOString(),
    endDate: endDate.toISOString()
  };
}