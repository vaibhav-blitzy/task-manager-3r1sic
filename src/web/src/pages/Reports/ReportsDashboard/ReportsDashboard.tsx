import React, { useState, useEffect, useCallback } from 'react'; // react ^18.2.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.0

import useAnalytics from '../../../api/hooks/useAnalytics';
import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import BarChart from '../../../components/organisms/Charts/BarChart/BarChart';
import LineChart from '../../../components/organisms/Charts/LineChart/LineChart';
import PieChart from '../../../components/organisms/Charts/PieChart/PieChart';
import FormField from '../../../components/molecules/FormField/FormField';
import Button from '../../../components/atoms/Button/Button';
import useProjects from '../../../api/hooks/useProjects';
import { formatDate } from '../../../utils/date';

/**
 * Main dashboard page component for analytics and reporting, displaying various metrics and charts about task and project performance
 */
const ReportsDashboard: React.FC = () => {
  // Initialize state for selectedProject, selectedPeriod, and loading status
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('Last 30 Days');
  const [loading, setLoading] = useState<boolean>(false);

  // Initialize state for chart data: taskStatusData, projectProgressData, taskCompletionData, workloadData, etc.
  const [taskStatusData, setTaskStatusData] = useState<Array<{ label: string; value: number }>>([]);
  const [projectProgressData, setProjectProgressData] = useState<Array<{ label: string; value: number }>>([]);
  const [taskCompletionData, setTaskCompletionData] = useState<Array<{ label: string; value: number; date: Date }>>([]);
  const [workloadData, setWorkloadData] = useState<Array<{ label: string; value: number }>>([]);
  const [overdueTasks, setOverdueTasks] = useState<Array<{ title: string; dueDate: string }>>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<{ avgCompletionTime: number; onTimeCompletionRate: number; tasksCreated: number; tasksCompleted: number }>({
    avgCompletionTime: 0,
    onTimeCompletionRate: 0,
    tasksCreated: 0,
    tasksCompleted: 0,
  });

  // Fetch projects list using useProjects hook for filter dropdown
  const { projects } = useProjects();

  // Import analytics hooks
  const { useTaskMetrics, useProjectMetrics, useUserMetrics, usePerformanceMetrics, useReportGeneration, useDownloadReport } = useAnalytics;

  /**
   * Handles changes to the selected project filter
   * @param {React.ChangeEvent<HTMLSelectElement>} event
   */
  const handleProjectChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    // Extract selected project ID from event.target.value
    const projectId = event.target.value;

    // Update selectedProject state with new value
    setSelectedProject(projectId === 'all' ? null : projectId);
  }, []);

  /**
   * Handles changes to the time period filter
   * @param {React.ChangeEvent<HTMLSelectElement>} event
   */
  const handlePeriodChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    // Extract selected period from event.target.value
    const period = event.target.value;

    // Update selectedPeriod state with new value
    setSelectedPeriod(period);
  }, []);

  /**
   * Handles report export functionality in different formats
   * @param {string} format
   */
  const exportReport = useCallback(async (format: string) => {
    // Call generateReport from useReportGeneration hook with current filters and format
    // Show loading notification while report is being generated
    // When complete, call downloadReport to trigger file download
    // Show success notification when export is complete
    // Handle any errors with appropriate error notifications
    console.log('Exporting report in format:', format);
  }, []);

  /**
   * Fetches all dashboard data based on current filters
   */
  const fetchDashboardData = useCallback(async () => {
    // Set loading state to true
    setLoading(true);

    try {
      // Prepare filter parameters based on selectedProject and selectedPeriod
      const filterParams = {
        projectId: selectedProject || undefined,
        period: selectedPeriod,
      };

      // Fetch task metrics using useTaskMetrics hook
      const taskMetricsHook = useTaskMetrics(filterParams);
      const taskMetrics = taskMetricsHook.metrics;

      // Fetch project metrics using useProjectMetrics hook
      const projectMetricsHook = useProjectMetrics(filterParams);
      const projectMetrics = projectMetricsHook.metrics;

      // Fetch user metrics using useUserMetrics hook
      const userMetricsHook = useUserMetrics(filterParams);
      const userMetrics = userMetricsHook.metrics;

      // Fetch performance metrics using usePerformanceMetrics hook
      const performanceMetricsHook = usePerformanceMetrics(filterParams);
      const performanceMetricsData = performanceMetricsHook.metrics;

      // Process and format the fetched data for charts
      if (taskMetrics) {
        setTaskStatusData([
          { label: 'To Do', value: taskMetrics.byStatus.created },
          { label: 'In Progress', value: taskMetrics.byStatus['in-progress'] },
          { label: 'Review', value: taskMetrics.byStatus['in-review'] },
          { label: 'Completed', value: taskMetrics.byStatus.completed },
        ]);
      }

      if (projectMetrics) {
        setProjectProgressData([
          { label: 'Project A', value: 60 },
          { label: 'Project B', value: 85 },
          { label: 'Project C', value: 45 },
        ]);
      }

      setTaskCompletionData([
        { label: 'Week 1', value: 10, date: new Date() },
        { label: 'Week 2', value: 15, date: new Date() },
        { label: 'Week 3', value: 8, date: new Date() },
        { label: 'Week 4', value: 22, date: new Date() },
      ]);

      if (userMetrics) {
        setWorkloadData([
          { label: 'John', value: 8 },
          { label: 'Sarah', value: 6 },
          { label: 'Mike', value: 5 },
        ]);
      }

      setOverdueTasks([
        { title: 'Design Sign-off', dueDate: '2024-01-29' },
        { title: 'Client Meeting Notes', dueDate: '2024-01-30' },
      ]);

      if (performanceMetricsData) {
        setPerformanceMetrics({
          avgCompletionTime: 2.3,
          onTimeCompletionRate: 78,
          tasksCreated: 45,
          tasksCompleted: 32,
        });
      }
    } catch (error) {
      // Handle any errors with appropriate error display
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to fetch dashboard data. Please try again.');
    } finally {
      // Set loading state to false when complete
      setLoading(false);
    }
  }, [selectedProject, selectedPeriod, useTaskMetrics, useProjectMetrics, useUserMetrics, usePerformanceMetrics]);

  // Use useEffect to fetch dashboard data on initial load and when filters change
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return (
    <DashboardLayout title="Reports & Analytics">
      {/* Filter controls section with project and time period selectors */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <FormField label="Project" htmlFor="project-filter">
            <select
              id="project-filter"
              className="w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              onChange={handleProjectChange}
            >
              <option value="all">All Projects</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </FormField>
        </div>
        <div>
          <FormField label="Period" htmlFor="period-filter">
            <select
              id="period-filter"
              className="w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              onChange={handlePeriodChange}
            >
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
              <option>Last 90 Days</option>
              <option>This Year</option>
            </select>
          </FormField>
        </div>
      </div>

      {/* Main dashboard grid with chart widgets, each containing appropriate chart components */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* TaskStatus widget with PieChart showing task distribution by status */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Task Status</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <PieChart data={taskStatusData} />
          )}
        </div>

        {/* ProjectProgress widget with BarChart showing project completion percentages */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Project Progress</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <BarChart data={projectProgressData} xAxisLabel="Project" yAxisLabel="Completion (%)" />
          )}
        </div>

        {/* TaskCompletion widget with LineChart showing tasks completed over time */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Task Completion</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <LineChart
              labels={taskCompletionData.map((item) => formatDate(item.date))}
              datasets={[
                {
                  label: 'Tasks Completed',
                  data: taskCompletionData.map((item) => item.value),
                  borderColor: 'rgb(75, 192, 192)',
                  tension: 0.1,
                },
              ]}
              xAxisLabel="Week"
              yAxisLabel="Tasks"
            />
          )}
        </div>

        {/* Workload widget with BarChart showing task distribution by assignee */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Workload</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <BarChart data={workloadData} xAxisLabel="Assignee" yAxisLabel="Tasks" />
          )}
        </div>

        {/* OverdueTasks widget with task list of overdue items */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Overdue Tasks</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <ul>
              {overdueTasks.map((task) => (
                <li key={task.title} className="py-2 border-b border-gray-200 dark:border-gray-700">
                  {task.title} - Due: {task.dueDate}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* PerformanceMetrics widget with key metrics in card format */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-md p-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Performance Metrics</h3>
          {loading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Average Completion Time: {performanceMetrics.avgCompletionTime} days
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                On-Time Completion Rate: {performanceMetrics.onTimeCompletionRate}%
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tasks Created: {performanceMetrics.tasksCreated}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tasks Completed: {performanceMetrics.tasksCompleted}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Export controls section with buttons for different export formats */}
      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">Export Report</h3>
        <Button variant="primary" onClick={() => exportReport('pdf')}>
          Export as PDF
        </Button>
        <Button variant="secondary" className="ml-4" onClick={() => exportReport('csv')}>
          Export as CSV
        </Button>
      </div>
    </DashboardLayout>
  );
};

export default ReportsDashboard;