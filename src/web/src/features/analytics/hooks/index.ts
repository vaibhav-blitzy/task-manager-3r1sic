import { useState, useEffect, useMemo, useCallback } from 'react'; // react ^18.2.0
import { useQuery } from 'react-query'; // react-query ^3.39.0

import {
  useTaskMetrics,
  useProjectMetrics,
  useGetMetrics,
  useReportGeneration,
  useDownloadReport
} from '../../../api/hooks/useAnalytics';

import {
  calculateTaskCompletionRate,
  calculateOnTimeCompletionRate,
  calculateCycleTime,
  calculateLeadTime,
  getTasksByStatus,
  getWorkloadDistribution,
  prepareChartData
} from '../utils';

import { TaskStatus, TaskPriority } from '../../../types/task';
import { ProjectStatus } from '../../../types/project';

/**
 * Custom hook for processing dashboard metrics from raw API data
 * 
 * @param metrics - Raw metrics data from API
 * @returns Processed metrics for dashboard visualization
 */
export const useDashboardMetrics = (metrics: any) => {
  const processedMetrics = useMemo(() => {
    if (!metrics) {
      return {
        completionRate: 0,
        onTimeRate: 0,
        averageTaskAge: 0,
        tasksByStatus: {},
        tasksByPriority: {},
        activeProjects: 0,
        overdueTasksCount: 0
      };
    }

    // Extract tasks data if available
    const tasks = metrics.tasks || [];
    
    // Calculate core metrics
    const completionRate = calculateTaskCompletionRate(tasks);
    const onTimeRate = calculateOnTimeCompletionRate(tasks);
    
    // Calculate task distribution
    const tasksByStatus = getTasksByStatus(tasks);
    const tasksByPriority = tasks.reduce((acc: Record<string, number>, task: any) => {
      const priority = task.priority || TaskPriority.MEDIUM;
      acc[priority] = (acc[priority] || 0) + 1;
      return acc;
    }, {});
    
    // Count active projects
    const projects = metrics.projects || [];
    const activeProjects = projects.filter((project: any) => 
      project.status === ProjectStatus.ACTIVE
    ).length;
    
    // Count overdue tasks
    const now = new Date();
    const overdueTasksCount = tasks.filter((task: any) => {
      if (!task.dueDate || task.status === TaskStatus.COMPLETED || task.status === TaskStatus.CANCELLED) {
        return false;
      }
      return new Date(task.dueDate) < now;
    }).length;
    
    return {
      completionRate,
      onTimeRate,
      tasksByStatus,
      tasksByPriority,
      activeProjects,
      overdueTasksCount
    };
  }, [metrics]);
  
  return processedMetrics;
};

/**
 * Custom hook for calculating advanced performance metrics for projects and tasks
 * 
 * @param projectId - Optional project ID to filter metrics
 * @param timeRange - Time range to analyze
 * @returns Performance metrics including cycle time, lead time, and bottlenecks
 */
export const usePerformanceMetrics = (projectId?: string, timeRange?: string) => {
  // Fetch raw performance metrics data
  const { metrics, isLoading, error } = useGetMetrics(
    'performance',
    { projectId, timeRange }
  );
  
  // Process the metrics data
  const performanceData = useMemo(() => {
    if (!metrics || isLoading) {
      return {
        cycleTime: 0,
        leadTime: 0,
        taskCompletionTrend: [],
        bottlenecks: []
      };
    }
    
    // Calculate cycle time (time from in-progress to completion)
    const cycleTime = calculateCycleTime(metrics.tasks || []);
    
    // Calculate lead time (time from creation to completion)
    const leadTime = calculateLeadTime(metrics.tasks || []);
    
    // Process task completion trend data
    const taskCompletionTrend = metrics.completionTrend || [];
    
    // Identify workflow bottlenecks
    const bottlenecks = metrics.tasks ? metrics.tasks
      .filter((task: any) => 
        task.status !== TaskStatus.COMPLETED && 
        task.status !== TaskStatus.CANCELLED
      )
      .reduce((acc: Record<string, any>, task: any) => {
        const status = task.status || TaskStatus.CREATED;
        if (!acc[status]) {
          acc[status] = { count: 0, avgDuration: 0, totalDuration: 0 };
        }
        
        // Calculate task duration in current status
        const createdDate = new Date(task.metadata?.created || Date.now());
        const lastUpdated = new Date(task.metadata?.lastUpdated || Date.now());
        const duration = Math.floor((lastUpdated.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24));
        
        acc[status].count++;
        acc[status].totalDuration += duration;
        acc[status].avgDuration = acc[status].totalDuration / acc[status].count;
        
        return acc;
      }, {}) : {};
    
    // Convert bottlenecks to array format
    const bottlenecksArray = Object.entries(bottlenecks).map(([status, data]: [string, any]) => ({
      status,
      count: data.count,
      avgDuration: data.avgDuration
    })).sort((a, b) => b.avgDuration - a.avgDuration);
    
    return {
      cycleTime,
      leadTime,
      taskCompletionTrend,
      bottlenecks: bottlenecksArray
    };
  }, [metrics, isLoading]);
  
  return {
    ...performanceData,
    isLoading,
    error
  };
};

/**
 * Custom hook for transforming analytics data into formats suitable for different chart types
 * 
 * @param data - Raw data to transform
 * @param chartType - Type of chart (pie, bar, line, etc.)
 * @param options - Additional options for chart formatting
 * @returns Transformed data ready for chart visualization
 */
export const useChartData = (data: any, chartType: string, options: any = {}) => {
  // Transform the data for the specified chart type
  const chartData = useMemo(() => {
    if (!data) {
      return {
        labels: [],
        datasets: []
      };
    }
    
    // Use the utility function to prepare chart data
    return prepareChartData(data, chartType);
  }, [data, chartType]);
  
  // Apply any additional formatting based on options
  const formattedData = useMemo(() => {
    if (!chartData || !options) {
      return chartData;
    }
    
    // Apply sorting if specified
    if (options.sort) {
      const { field, direction } = options.sort;
      
      // Since chartData structure varies by chart type, handle sorting appropriately
      if (chartType === 'bar' || chartType === 'pie') {
        const sortedIndices = [...chartData.labels].map((_, i) => i)
          .sort((a, b) => {
            const valA = chartData.datasets[0].data[a];
            const valB = chartData.datasets[0].data[b];
            return direction === 'asc' ? valA - valB : valB - valA;
          });
        
        return {
          labels: sortedIndices.map(i => chartData.labels[i]),
          datasets: chartData.datasets.map(dataset => ({
            ...dataset,
            data: sortedIndices.map(i => dataset.data[i]),
            backgroundColor: Array.isArray(dataset.backgroundColor) 
              ? sortedIndices.map(i => dataset.backgroundColor[i])
              : dataset.backgroundColor
          }))
        };
      }
    }
    
    // Apply limit if specified
    if (options.limit && chartData.labels?.length > options.limit) {
      const limitedLabels = chartData.labels.slice(0, options.limit);
      const otherLabel = 'Other';
      
      if (chartType === 'pie' || chartType === 'bar') {
        const limitedData = chartData.datasets[0].data.slice(0, options.limit);
        const otherValue = chartData.datasets[0].data
          .slice(options.limit)
          .reduce((sum: number, val: number) => sum + val, 0);
        
        const newLabels = [...limitedLabels];
        const newData = [...limitedData];
        
        if (otherValue > 0) {
          newLabels.push(otherLabel);
          newData.push(otherValue);
        }
        
        return {
          labels: newLabels,
          datasets: chartData.datasets.map(dataset => ({
            ...dataset,
            data: newData,
            backgroundColor: Array.isArray(dataset.backgroundColor)
              ? [...dataset.backgroundColor.slice(0, options.limit), '#999999']
              : dataset.backgroundColor
          }))
        };
      }
    }
    
    return chartData;
  }, [chartData, chartType, options]);
  
  return formattedData;
};

/**
 * Custom hook for analyzing workload distribution across team members
 * 
 * @param projectId - Optional project ID to filter tasks
 * @returns Workload distribution analysis and overallocated team members
 */
export const useWorkloadDistribution = (projectId?: string) => {
  // Fetch task data for workload analysis
  const { metrics, isLoading, error } = useTaskMetrics(
    { projectId, status: [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW] }
  );
  
  // Calculate workload distribution
  const workloadData = useMemo(() => {
    if (!metrics || isLoading) {
      return {
        distribution: [],
        overallocated: []
      };
    }
    
    const tasks = metrics.tasks || [];
    
    // Get raw workload distribution
    const workloadByUser = getWorkloadDistribution(tasks);
    
    // Convert to array format with user details
    const distributionArray = Object.entries(workloadByUser).map(([userId, taskCount]) => {
      // Find the user in the tasks to get user details
      const userTask = tasks.find((task: any) => task.assignee?.id === userId);
      const user = userTask?.assignee || { id: userId, name: 'Unknown User' };
      
      // Calculate estimated effort (weighted by priority)
      const userTasks = tasks.filter((task: any) => task.assignee?.id === userId);
      const estimatedEffort = userTasks.reduce((total: number, task: any) => {
        // Weight by priority: Urgent = 3, High = 2, Medium = 1, Low = 0.5
        const priorityWeight = {
          [TaskPriority.URGENT]: 3,
          [TaskPriority.HIGH]: 2,
          [TaskPriority.MEDIUM]: 1,
          [TaskPriority.LOW]: 0.5
        };
        return total + (priorityWeight[task.priority] || 1);
      }, 0);
      
      return {
        userId,
        name: `${user.firstName} ${user.lastName}`.trim() || user.email || 'Unknown User',
        taskCount,
        estimatedEffort
      };
    }).sort((a, b) => b.taskCount - a.taskCount);
    
    // Identify potentially overallocated users (simple threshold-based approach)
    // In a real app, this would be more sophisticated
    const overallocated = distributionArray
      .filter(item => item.taskCount > 5 || item.estimatedEffort > 10)
      .map(item => item.userId);
    
    return {
      distribution: distributionArray,
      overallocated
    };
  }, [metrics, isLoading]);
  
  return {
    ...workloadData,
    isLoading,
    error
  };
};

/**
 * Custom hook for analyzing task completion patterns and trends over time
 * 
 * @param timeRange - Time range to analyze
 * @param groupBy - Grouping period (day, week, month)
 * @returns Task completion trend analysis
 */
export const useTaskCompletionTrends = (timeRange: string, groupBy: string = 'day') => {
  // Fetch task data for trend analysis
  const { metrics, isLoading, error } = useTaskMetrics(
    { timeRange, groupBy }
  );
  
  // Process completion trend data
  const trendData = useMemo(() => {
    if (!metrics || isLoading) {
      return {
        completionByTime: [],
        completionRate: 0,
        trend: 'stable'
      };
    }
    
    // Extract time-series data
    const completionByTime = metrics.completionByTime || [];
    
    // Calculate overall completion rate
    const totalTasks = metrics.totalTasks || 0;
    const completedTasks = metrics.completedTasks || 0;
    const completionRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
    
    // Determine trend direction by comparing recent periods to earlier ones
    let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
    
    if (completionByTime.length >= 4) {
      const halfLength = Math.floor(completionByTime.length / 2);
      const recentHalf = completionByTime.slice(-halfLength);
      const earlierHalf = completionByTime.slice(0, halfLength);
      
      const recentAvg = recentHalf.reduce((sum: number, period: any) => sum + period.count, 0) / recentHalf.length;
      const earlierAvg = earlierHalf.reduce((sum: number, period: any) => sum + period.count, 0) / earlierHalf.length;
      
      const difference = recentAvg - earlierAvg;
      
      if (difference > 0.1 * earlierAvg) {
        trend = 'increasing';
      } else if (difference < -0.1 * earlierAvg) {
        trend = 'decreasing';
      }
    }
    
    return {
      completionByTime,
      completionRate,
      trend
    };
  }, [metrics, isLoading]);
  
  return {
    ...trendData,
    isLoading,
    error
  };
};

/**
 * Custom hook for exporting reports in various formats (PDF, CSV, Excel)
 * 
 * @returns Report export functionality and status
 */
export const useReportExport = () => {
  // Local state for tracking export status
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Use the base hooks for report generation and download
  const { generateReport, isGenerating } = useReportGeneration();
  const { downloadReport, isDownloading } = useDownloadReport();
  
  // Combined export function that handles the entire process
  const exportReport = useCallback(async (format: string, reportId: string, filters?: object) => {
    setIsExporting(true);
    setError(null);
    
    try {
      // First generate the report with the specified format
      const generationResult = await generateReport({
        reportId,
        format,
        parameters: filters
      });
      
      // Once generated, initiate the download
      if (generationResult?.id) {
        await downloadReport(generationResult.id);
      } else {
        throw new Error('Failed to generate report: No report ID returned');
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An unknown error occurred during export'));
      throw err;
    } finally {
      setIsExporting(false);
    }
  }, [generateReport, downloadReport]);
  
  return {
    exportReport,
    isExporting: isExporting || isGenerating || isDownloading,
    error
  };
};