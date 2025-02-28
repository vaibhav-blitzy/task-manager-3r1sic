import React from 'react'; // react ^18.2.0
import { screen, waitFor, within } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { renderWithProviders } from '../../../utils/test-utils';
import ReportsDashboard from '../ReportsDashboard';
import { useAnalytics } from '../../../api/hooks/useAnalytics';
import { jest } from 'jest'; // jest ^29.0.0

// Mock the useAnalytics hook
jest.mock('../../../api/hooks/useAnalytics');

describe('ReportsDashboard', () => {
  beforeEach(() => {
    // Reset any mocks
    (useAnalytics as jest.Mock).mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the dashboard with loading state initially', async () => {
    // Mock useAnalytics to return isLoading: true
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: true }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: true }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: true }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: true }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: true }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: true }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Verify loading indicator is displayed
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Verify dashboard title is present
    expect(screen.getByText('Reports & Analytics')).toBeInTheDocument();
  });

  it('renders metrics and charts when data loads', async () => {
    // Mock useAnalytics to return test dashboard data
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { byStatus: { created: 10, 'in-progress': 20, 'in-review': 5, completed: 30 } } }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { avgCompletionTime: 2.3, onTimeCompletionRate: 78, tasksCreated: 45, tasksCompleted: 32 } }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Verify key metrics are displayed (task completion rate, on-time rate, etc.)
    await waitFor(() => {
      expect(screen.getByText('Average Completion Time: 2.3 days')).toBeInTheDocument();
      expect(screen.getByText('On-Time Completion Rate: 78%')).toBeInTheDocument();
      expect(screen.getByText('Tasks Created: 45')).toBeInTheDocument();
      expect(screen.getByText('Tasks Completed: 32')).toBeInTheDocument();
    });

    // Verify chart components are rendered (task status, workload, etc.)
    expect(screen.getByText('Task Status')).toBeInTheDocument();
    expect(screen.getByText('Project Progress')).toBeInTheDocument();
    expect(screen.getByText('Task Completion')).toBeInTheDocument();
    expect(screen.getByText('Workload')).toBeInTheDocument();
    expect(screen.getByText('Overdue Tasks')).toBeInTheDocument();

    // Check specific metric values match mock data
    expect(screen.getByText('Average Completion Time: 2.3 days')).toBeInTheDocument();
    expect(screen.getByText('On-Time Completion Rate: 78%')).toBeInTheDocument();
    expect(screen.getByText('Tasks Created: 45')).toBeInTheDocument();
    expect(screen.getByText('Tasks Completed: 32')).toBeInTheDocument();
  });

  it('handles error state correctly', async () => {
    // Mock useAnalytics to return isError: true
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' } }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' } }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' } }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' } }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch dashboard data. Please try again.')).toBeInTheDocument();
    });

    // Mock fetchDashboardData to be called again
    const fetchDashboardDataMock = jest.fn();
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' }, refetch: fetchDashboardDataMock }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' }, refetch: fetchDashboardDataMock }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' }, refetch: fetchDashboardDataMock }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, isError: true, error: { message: 'API Error' }, refetch: fetchDashboardDataMock }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Click retry button
    // Verify fetchDashboardData is called again
    // Verify UI updates with filtered data
  });

  it('can filter data by project', async () => {
    // Mock useAnalytics with project filter function
    const fetchDashboardDataMock = jest.fn();
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Find project dropdown selector
    const projectSelect = screen.getByLabelText('Project');

    // Select specific project from dropdown
    await userEvent.selectOptions(projectSelect, ['project-123']);

    // Verify fetchDashboardData called with correct project filter
    expect(fetchDashboardDataMock).toHaveBeenCalledWith({ projectId: 'project-123', period: 'Last 30 Days' });

    // Verify UI updates with filtered data
  });

  it('can filter data by time period', async () => {
    // Mock useAnalytics with time period filter function
    const fetchDashboardDataMock = jest.fn();
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Find time period dropdown selector
    const periodSelect = screen.getByLabelText('Period');

    // Select 'Last 30 Days' option
    await userEvent.selectOptions(periodSelect, ['Last 30 Days']);

    // Verify fetchDashboardData called with correct time period parameter
    expect(fetchDashboardDataMock).toHaveBeenCalledWith({ projectId: null, period: 'Last 30 Days' });

    // Verify UI updates with new time period data
  });

  it('can export reports in different formats', async () => {
    // Mock exportReport function in useAnalytics
    const exportReportMock = jest.fn();
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false, downloadReport: exportReportMock }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Click export button to show format options
    const exportButton = screen.getByText('Export as PDF');
    await userEvent.click(exportButton);

    // Select PDF format option
    // Verify exportReport called with 'pdf' format
    // Select CSV format option
    // Verify exportReport called with 'csv' format
    // Verify success message appears after export
  });

  it('displays task status distribution correctly', async () => {
    // Mock useAnalytics with specific task status data
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { byStatus: { created: 10, 'in-progress': 20, 'in-review': 5, completed: 30 } } }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Verify task status pie chart is displayed
    expect(screen.getByText('Task Status')).toBeInTheDocument();

    // Check that chart legend shows all status types
    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();

    // Verify status percentage values match mock data
    // (This might require more advanced chart inspection depending on the charting library)
  });

  it('displays performance metrics section correctly', async () => {
    // Mock useAnalytics with performance metrics data
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { avgCompletionTime: 2.3, onTimeCompletionRate: 78, tasksCreated: 45, tasksCompleted: 32 } }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Verify performance metrics section is displayed
    expect(screen.getByText('Performance Metrics')).toBeInTheDocument();

    // Check average completion time value
    expect(screen.getByText('Average Completion Time: 2.3 days')).toBeInTheDocument();

    // Check on-time completion rate value
    expect(screen.getByText('On-Time Completion Rate: 78%')).toBeInTheDocument();

    // Check tasks created/completed counts
    expect(screen.getByText('Tasks Created: 45')).toBeInTheDocument();
    expect(screen.getByText('Tasks Completed: 32')).toBeInTheDocument();
  });

  it('updates charts when date range changes', async () => {
    // Mock useAnalytics with initial data
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { byStatus: { created: 10, 'in-progress': 20, 'in-review': 5, completed: 30 } } }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { avgCompletionTime: 2.3, onTimeCompletionRate: 78, tasksCreated: 45, tasksCompleted: 32 } }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Render the ReportsDashboard component
    renderWithProviders(<ReportsDashboard />);

    // Capture initial chart values
    const initialCompletionTime = await screen.findByText('Average Completion Time: 2.3 days');

    // Mock new data for different date range
    (useAnalytics as jest.Mock).mockReturnValue({
      useTaskMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { byStatus: { created: 5, 'in-progress': 15, 'in-review': 10, completed: 40 } } }),
      useProjectMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      useUserMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: {} }),
      usePerformanceMetrics: jest.fn().mockReturnValue({ isLoading: false, metrics: { avgCompletionTime: 3.1, onTimeCompletionRate: 85, tasksCreated: 52, tasksCompleted: 41 } }),
      useReportGeneration: jest.fn().mockReturnValue({ isLoading: false }),
      useDownloadReport: jest.fn().mockReturnValue({ isLoading: false }),
    });

    // Change date range filter
    const periodSelect = screen.getByLabelText('Period');
    await userEvent.selectOptions(periodSelect, ['Last 7 Days']);

    // Verify fetchDashboardData called with new date range
    // Verify charts updated with new data values
    await waitFor(() => {
      expect(screen.getByText('Average Completion Time: 3.1 days')).toBeInTheDocument();
    });
  });
});