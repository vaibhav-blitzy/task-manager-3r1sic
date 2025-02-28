import { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.2.0
import { 
  useQuery, 
  useMutation, 
  useQueryClient, 
  UseQueryOptions 
} from 'react-query'; // react-query ^3.39.0
import { toast } from 'react-toastify'; // react-toastify ^9.1.0

import analyticsService, {
  Dashboard,
  Widget,
  DashboardListParams,
  Metric,
  MetricParams,
  Report,
  ReportListParams,
  ReportGenerationParams
} from '../services/analyticsService';
import useAuth from './useAuth';

/**
 * Hook for listing and filtering dashboards with pagination
 * 
 * @param params - Query parameters for filtering dashboards
 * @param options - Additional React Query options
 * @returns Dashboards data and pagination controls
 */
const useDashboards = (params?: DashboardListParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // State for pagination
  const [page, setPage] = useState(params?.page || 1);
  const [pageSize, setPageSize] = useState(params?.limit || 20);
  
  // Combine pagination with other params
  const queryParams = useMemo(() => ({
    ...params,
    page,
    limit: pageSize
  }), [params, page, pageSize]);
  
  // Fetch dashboards
  const { data, isLoading, error, refetch } = useQuery(
    ['dashboards', queryParams],
    () => analyticsService.getDashboards(queryParams),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  // Pagination control functions
  const nextPage = useCallback(() => {
    if (data && page < (data.totalPages || 1)) {
      setPage(prevPage => prevPage + 1);
    }
  }, [data, page]);
  
  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(prevPage => prevPage - 1);
    }
  }, [page]);
  
  const goToPage = useCallback((newPage: number) => {
    if (newPage >= 1 && (!data || newPage <= (data.totalPages || 1))) {
      setPage(newPage);
    }
  }, [data]);
  
  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to first page when changing page size
  }, []);
  
  // Return data with pagination controls
  return {
    dashboards: data?.items || [],
    isLoading,
    error,
    refetch,
    pagination: {
      page,
      pageSize,
      totalItems: data?.total || 0,
      totalPages: data?.totalPages || 1,
      nextPage,
      prevPage,
      goToPage,
      changePageSize
    }
  };
};

/**
 * Hook for fetching and managing a single dashboard
 * 
 * @param dashboardId - ID of the dashboard to fetch
 * @param options - Additional React Query options
 * @returns Dashboard data and status
 */
const useDashboard = (dashboardId: string, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['dashboard', dashboardId],
    () => analyticsService.getDashboard(dashboardId),
    {
      enabled: isAuthenticated && !!dashboardId,
      ...options
    }
  );
  
  return {
    dashboard: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for fetching widget data for a specific dashboard
 * 
 * @param dashboardId - ID of the dashboard
 * @param refresh - Whether to refresh cached data
 * @param options - Additional React Query options
 * @returns Dashboard widget data and status
 */
const useDashboardData = (dashboardId: string, refresh: boolean = false, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['dashboardData', dashboardId, refresh],
    () => analyticsService.getDashboardData(dashboardId, refresh),
    {
      enabled: isAuthenticated && !!dashboardId,
      ...options
    }
  );
  
  return {
    data: data?.widgetData || {},
    lastUpdated: data?.lastUpdated,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for dashboard creation, update, and deletion operations
 * 
 * @returns Mutation functions for dashboard operations
 */
const useDashboardMutation = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // Create dashboard mutation
  const createMutation = useMutation(
    (dashboard: Omit<Dashboard, 'id' | 'metadata'>) => 
      analyticsService.createDashboard(dashboard),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('dashboards');
        toast.success('Dashboard created successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to create dashboard: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Update dashboard mutation
  const updateMutation = useMutation(
    ({ id, dashboard }: { id: string; dashboard: Partial<Dashboard> }) => 
      analyticsService.updateDashboard(id, dashboard),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['dashboard', variables.id]);
        queryClient.invalidateQueries('dashboards');
        toast.success('Dashboard updated successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to update dashboard: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Delete dashboard mutation
  const deleteMutation = useMutation(
    (id: string) => analyticsService.deleteDashboard(id),
    {
      onSuccess: (_, id) => {
        queryClient.invalidateQueries('dashboards');
        queryClient.removeQueries(['dashboard', id]);
        toast.success('Dashboard deleted successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to delete dashboard: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    createDashboard: createMutation.mutateAsync,
    updateDashboard: updateMutation.mutateAsync,
    deleteDashboard: deleteMutation.mutateAsync,
    isCreating: createMutation.isLoading,
    isUpdating: updateMutation.isLoading,
    isDeleting: deleteMutation.isLoading,
    createError: createMutation.error,
    updateError: updateMutation.error,
    deleteError: deleteMutation.error
  };
};

/**
 * Hook for fetching a specific metric by name
 * 
 * @param metricName - Name of the metric to fetch
 * @param params - Parameters for filtering the metric data
 * @param options - Additional React Query options
 * @returns Metric data and status
 */
const useMetric = (metricName: string, params?: MetricParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['metric', metricName, params],
    () => analyticsService.getMetric(metricName, params),
    {
      enabled: isAuthenticated && !!metricName,
      ...options
    }
  );
  
  return {
    metric: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for fetching task-related metrics
 * 
 * @param params - Parameters for filtering task metrics
 * @param options - Additional React Query options
 * @returns Task metrics data and status
 */
const useTaskMetrics = (params?: MetricParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['taskMetrics', params],
    () => analyticsService.getTaskMetrics(params),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  return {
    metrics: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for fetching project-related metrics
 * 
 * @param params - Parameters for filtering project metrics
 * @param options - Additional React Query options
 * @returns Project metrics data and status
 */
const useProjectMetrics = (params?: MetricParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['projectMetrics', params],
    () => analyticsService.getProjectMetrics(params),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  return {
    metrics: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for fetching user productivity metrics
 * 
 * @param params - Parameters for filtering user metrics
 * @param options - Additional React Query options
 * @returns User metrics data and status
 */
const useUserMetrics = (params?: MetricParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['userMetrics', params],
    () => analyticsService.getUserMetrics(params),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  return {
    metrics: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for fetching system performance metrics
 * 
 * @param params - Parameters for filtering performance metrics
 * @param options - Additional React Query options
 * @returns Performance metrics data and status
 */
const usePerformanceMetrics = (params?: MetricParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['performanceMetrics', params],
    () => analyticsService.getPerformanceMetrics(params),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  return {
    metrics: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for listing and filtering reports
 * 
 * @param params - Query parameters for filtering reports
 * @param options - Additional React Query options
 * @returns Reports data and pagination controls
 */
const useReports = (params?: ReportListParams, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // State for pagination
  const [page, setPage] = useState(params?.page || 1);
  const [pageSize, setPageSize] = useState(params?.limit || 20);
  
  // Combine pagination with other params
  const queryParams = useMemo(() => ({
    ...params,
    page,
    limit: pageSize
  }), [params, page, pageSize]);
  
  // Fetch reports
  const { data, isLoading, error, refetch } = useQuery(
    ['reports', queryParams],
    () => analyticsService.getReports(queryParams),
    {
      enabled: isAuthenticated,
      ...options
    }
  );
  
  // Pagination control functions
  const nextPage = useCallback(() => {
    if (data && page < (data.totalPages || 1)) {
      setPage(prevPage => prevPage + 1);
    }
  }, [data, page]);
  
  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(prevPage => prevPage - 1);
    }
  }, [page]);
  
  const goToPage = useCallback((newPage: number) => {
    if (newPage >= 1 && (!data || newPage <= (data.totalPages || 1))) {
      setPage(newPage);
    }
  }, [data]);
  
  const changePageSize = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to first page when changing page size
  }, []);
  
  // Return data with pagination controls
  return {
    reports: data?.items || [],
    isLoading,
    error,
    refetch,
    pagination: {
      page,
      pageSize,
      totalItems: data?.total || 0,
      totalPages: data?.totalPages || 1,
      nextPage,
      prevPage,
      goToPage,
      changePageSize
    }
  };
};

/**
 * Hook for fetching a single report by ID
 * 
 * @param reportId - ID of the report to fetch
 * @param options - Additional React Query options
 * @returns Report data and status
 */
const useReport = (reportId: string, options?: UseQueryOptions) => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  const { data, isLoading, error, refetch } = useQuery(
    ['report', reportId],
    () => analyticsService.getReport(reportId),
    {
      enabled: isAuthenticated && !!reportId,
      ...options
    }
  );
  
  return {
    report: data,
    isLoading,
    error,
    refetch
  };
};

/**
 * Hook for generating reports on demand
 * 
 * @returns Report generation functionality and status
 */
const useReportGeneration = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // State to track generated report ID
  const [generatedReportId, setGeneratedReportId] = useState<string | null>(null);
  
  // Report generation mutation
  const generateMutation = useMutation(
    (params: ReportGenerationParams) => analyticsService.generateReport(params),
    {
      onSuccess: (data) => {
        if (data && data.id) {
          setGeneratedReportId(data.id);
          toast.success('Report generation started');
        }
      },
      onError: (error: any) => {
        toast.error(`Failed to generate report: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Query for report generation status
  const { data: generationStatus, isLoading: isCheckingStatus } = useQuery(
    ['reportStatus', generatedReportId],
    () => analyticsService.getReportStatus(generatedReportId!),
    {
      enabled: isAuthenticated && !!generatedReportId,
      refetchInterval: (data) => {
        if (data && ['completed', 'failed'].includes(data.status)) {
          return false; // Stop polling when generation is complete
        }
        return 3000; // Check every 3 seconds
      },
      onSuccess: (data) => {
        if (data.status === 'completed') {
          toast.success('Report generated successfully');
        } else if (data.status === 'failed') {
          toast.error(`Report generation failed: ${data.error || 'Unknown error'}`);
          setGeneratedReportId(null);
        }
      }
    }
  );
  
  // Reset generated report ID when component unmounts
  useEffect(() => {
    return () => {
      setGeneratedReportId(null);
    };
  }, []);
  
  return {
    generateReport: generateMutation.mutateAsync,
    generationStatus,
    isGenerating: generateMutation.isLoading || isCheckingStatus,
    error: generateMutation.error
  };
};

/**
 * Hook for downloading generated reports
 * 
 * @returns Report download functionality and status
 */
const useDownloadReport = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // Report download mutation
  const downloadMutation = useMutation(
    (reportId: string) => analyticsService.downloadReport(reportId),
    {
      onSuccess: (data) => {
        if (data && data.url) {
          // Create a hidden link and click it to trigger the download
          const a = document.createElement('a');
          a.href = data.url;
          a.download = data.filename || `report-${new Date().toISOString()}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          
          toast.success('Report download started');
        }
      },
      onError: (error: any) => {
        toast.error(`Failed to download report: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    downloadReport: downloadMutation.mutateAsync,
    isDownloading: downloadMutation.isLoading,
    error: downloadMutation.error
  };
};

/**
 * Hook for scheduling periodic report generation
 * 
 * @returns Report scheduling functionality and status
 */
const useScheduleReport = () => {
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  
  // Schedule report mutation
  const scheduleMutation = useMutation(
    ({ id, scheduleParams }: { id: string; scheduleParams: any }) => 
      analyticsService.scheduleReport(id, scheduleParams),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['report', variables.id]);
        queryClient.invalidateQueries('reports');
        toast.success('Report scheduled successfully');
      },
      onError: (error: any) => {
        toast.error(`Failed to schedule report: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  // Unschedule report mutation
  const unscheduleMutation = useMutation(
    (id: string) => analyticsService.unscheduleReport(id),
    {
      onSuccess: (_, id) => {
        queryClient.invalidateQueries(['report', id]);
        queryClient.invalidateQueries('reports');
        toast.success('Report schedule removed');
      },
      onError: (error: any) => {
        toast.error(`Failed to remove report schedule: ${error.message || 'Unknown error'}`);
      }
    }
  );
  
  return {
    scheduleReport: scheduleMutation.mutateAsync,
    unscheduleReport: unscheduleMutation.mutateAsync,
    isScheduling: scheduleMutation.isLoading || unscheduleMutation.isLoading,
    error: scheduleMutation.error || unscheduleMutation.error
  };
};

// Combine all hooks into a single object for default export
const useAnalytics = {
  useDashboards,
  useDashboard,
  useDashboardData,
  useDashboardMutation,
  useMetric,
  useTaskMetrics,
  useProjectMetrics,
  useUserMetrics,
  usePerformanceMetrics,
  useReports,
  useReport,
  useReportGeneration,
  useDownloadReport,
  useScheduleReport
};

// Export individual hooks
export {
  useDashboards,
  useDashboard,
  useDashboardData,
  useDashboardMutation,
  useMetric,
  useTaskMetrics,
  useProjectMetrics,
  useUserMetrics,
  usePerformanceMetrics,
  useReports,
  useReport,
  useReportGeneration,
  useDownloadReport,
  useScheduleReport
};

// Default export for the complete analytics hook
export default useAnalytics;