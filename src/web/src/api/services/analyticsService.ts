/**
 * Service module for accessing analytics and reporting functionality in the Task Management System.
 * Provides methods for managing dashboards, retrieving metrics, and generating reports.
 * 
 * @version 1.0.0
 */

import { apiClient } from '../client';
import { ANALYTICS_ENDPOINTS } from '../endpoints';

/**
 * Interface representing a dashboard in the system
 */
export interface Dashboard {
  id: string;
  name: string;
  owner: string;
  type: string; // personal/project/team/organization
  scope: {
    projects: string[];
    users: string[];
    dateRange: {
      start: string | null;
      end: string | null;
      preset: string | null; // today/week/month/quarter/year
    };
  };
  layout: {
    columns: number;
    widgets: Widget[];
  };
  sharing: {
    public: boolean;
    sharedWith: string[];
  };
  metadata: {
    created: string;
    lastUpdated: string;
    lastViewed: string;
  };
}

/**
 * Interface representing a widget within a dashboard
 */
export interface Widget {
  id: string;
  type: string; // task-status, burndown, task-completion, etc.
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  config: {
    title: string;
    dataSource: string;
    refreshInterval: number;
    visualizationType: string;
    filters: Record<string, any>;
    drilldownEnabled: boolean;
  };
}

/**
 * Parameters for listing dashboards
 */
export interface DashboardListParams {
  page?: number;
  limit?: number;
  type?: string;
  ownerId?: string;
}

/**
 * Interface representing dashboard data with widget content
 */
export interface DashboardData {
  widgetData: Record<string, any>;
  lastUpdated: string;
}

/**
 * Interface representing a metric in the system
 */
export interface Metric {
  name: string;
  value: number;
  change: number; // percentage change from previous period
  trend: string; // up/down/stable
  period: string; // time period the metric covers
  data: Array<{
    timestamp: string;
    value: number;
  }>;
}

/**
 * Parameters for retrieving metrics
 */
export interface MetricParams {
  startDate?: string;
  endDate?: string;
  groupBy?: string;
  filter?: Record<string, any>;
  projectId?: string;
  userId?: string;
}

/**
 * Interface representing a report in the system
 */
export interface Report {
  id: string;
  name: string;
  description: string;
  type: string;
  parameters: Record<string, any>;
  schedule: {
    enabled: boolean;
    frequency: string; // daily/weekly/monthly
    dayOfWeek?: number; // 0-6 for weekly
    dayOfMonth?: number; // 1-31 for monthly
    time: string;
    timezone: string;
  };
  format: string; // pdf/csv/excel
  lastRun: string | null;
  nextRun: string | null;
  createdBy: string;
  createdAt: string;
}

/**
 * Parameters for listing reports
 */
export interface ReportListParams {
  page?: number;
  limit?: number;
  type?: string;
  createdBy?: string;
}

/**
 * Parameters for generating a report
 */
export interface ReportGenerationParams {
  reportId: string;
  parameters?: Record<string, any>;
  format?: string; // pdf/csv/excel
}

/**
 * Result of a report generation request
 */
export interface ReportGenerationResult {
  id: string;
  status: string; // pending/processing/completed/failed
  url: string | null;
  createdAt: string;
  completedAt: string | null;
  error: string | null;
}

/**
 * Parameters for scheduling a report
 */
export interface ScheduledReportParams {
  enabled: boolean;
  frequency: string; // daily/weekly/monthly
  dayOfWeek?: number; // 0-6 for weekly
  dayOfMonth?: number; // 1-31 for monthly
  time: string;
  timezone: string;
  recipients: string[];
}

/**
 * Analytics service provides functions for working with dashboards, metrics, and reports
 */
export const analyticsService = {
  /**
   * Retrieves a list of dashboards with optional filtering
   *
   * @param params - Query parameters for filtering dashboards
   * @returns Promise resolving to dashboard list response
   */
  getDashboards: async (params?: DashboardListParams) => {
    return apiClient.get(ANALYTICS_ENDPOINTS.DASHBOARDS, { params });
  },

  /**
   * Retrieves a specific dashboard by ID
   *
   * @param id - Dashboard ID
   * @returns Promise resolving to dashboard details
   */
  getDashboard: async (id: string) => {
    return apiClient.get(ANALYTICS_ENDPOINTS.DASHBOARD(id));
  },

  /**
   * Creates a new dashboard
   *
   * @param dashboard - Dashboard data to create
   * @returns Promise resolving to created dashboard
   */
  createDashboard: async (dashboard: Omit<Dashboard, 'id' | 'metadata'>) => {
    return apiClient.post(ANALYTICS_ENDPOINTS.DASHBOARDS, dashboard);
  },

  /**
   * Updates an existing dashboard
   *
   * @param id - Dashboard ID
   * @param dashboard - Updated dashboard data
   * @returns Promise resolving to updated dashboard
   */
  updateDashboard: async (id: string, dashboard: Partial<Dashboard>) => {
    return apiClient.put(ANALYTICS_ENDPOINTS.DASHBOARD(id), dashboard);
  },

  /**
   * Deletes a dashboard
   *
   * @param id - Dashboard ID
   * @returns Promise resolving to deletion confirmation
   */
  deleteDashboard: async (id: string) => {
    return apiClient.delete(ANALYTICS_ENDPOINTS.DASHBOARD(id));
  },

  /**
   * Retrieves dashboard data with widget content
   *
   * @param id - Dashboard ID
   * @param refresh - Whether to refresh cached data
   * @returns Promise resolving to dashboard data
   */
  getDashboardData: async (id: string, refresh: boolean = false) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.DASHBOARD(id)}/data`, {
      params: { refresh }
    });
  },

  /**
   * Retrieves a specific metric by name
   *
   * @param metricName - Name of the metric to retrieve
   * @param params - Parameters for filtering the metric data
   * @returns Promise resolving to metric data
   */
  getMetric: async (metricName: string, params?: MetricParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.METRICS}/${metricName}`, {
      params
    });
  },

  /**
   * Retrieves task-related metrics
   *
   * @param params - Parameters for filtering task metrics
   * @returns Promise resolving to task metrics
   */
  getTaskMetrics: async (params?: MetricParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.METRICS}/tasks`, {
      params
    });
  },

  /**
   * Retrieves project-related metrics
   *
   * @param params - Parameters for filtering project metrics
   * @returns Promise resolving to project metrics
   */
  getProjectMetrics: async (params?: MetricParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.METRICS}/projects`, {
      params
    });
  },

  /**
   * Retrieves user-related metrics
   *
   * @param params - Parameters for filtering user metrics
   * @returns Promise resolving to user metrics
   */
  getUserMetrics: async (params?: MetricParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.METRICS}/users`, {
      params
    });
  },

  /**
   * Retrieves performance-related metrics
   *
   * @param params - Parameters for filtering performance metrics
   * @returns Promise resolving to performance metrics
   */
  getPerformanceMetrics: async (params?: MetricParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.METRICS}/performance`, {
      params
    });
  },

  /**
   * Retrieves a list of reports with optional filtering
   *
   * @param params - Query parameters for filtering reports
   * @returns Promise resolving to report list response
   */
  getReports: async (params?: ReportListParams) => {
    return apiClient.get(ANALYTICS_ENDPOINTS.REPORTS, { params });
  },

  /**
   * Retrieves a specific report by ID
   *
   * @param id - Report ID
   * @returns Promise resolving to report details
   */
  getReport: async (id: string) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.REPORTS}/${id}`);
  },

  /**
   * Creates a new report
   *
   * @param report - Report data to create
   * @returns Promise resolving to created report
   */
  createReport: async (report: Omit<Report, 'id' | 'createdAt' | 'lastRun' | 'nextRun'>) => {
    return apiClient.post(ANALYTICS_ENDPOINTS.REPORTS, report);
  },

  /**
   * Updates an existing report
   *
   * @param id - Report ID
   * @param report - Updated report data
   * @returns Promise resolving to updated report
   */
  updateReport: async (id: string, report: Partial<Report>) => {
    return apiClient.put(`${ANALYTICS_ENDPOINTS.REPORTS}/${id}`, report);
  },

  /**
   * Deletes a report
   *
   * @param id - Report ID
   * @returns Promise resolving to deletion confirmation
   */
  deleteReport: async (id: string) => {
    return apiClient.delete(`${ANALYTICS_ENDPOINTS.REPORTS}/${id}`);
  },

  /**
   * Generates a report based on parameters
   *
   * @param params - Report generation parameters
   * @returns Promise resolving to report generation result
   */
  generateReport: async (params: ReportGenerationParams) => {
    return apiClient.post(ANALYTICS_ENDPOINTS.GENERATE_REPORT, params);
  },

  /**
   * Checks the status of a report generation
   *
   * @param id - Report generation job ID
   * @returns Promise resolving to report generation status
   */
  getReportStatus: async (id: string) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.GENERATE_REPORT}/status/${id}`);
  },

  /**
   * Gets a download URL for a generated report
   *
   * @param id - Report generation job ID
   * @returns Promise resolving to report download URL
   */
  downloadReport: async (id: string) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.GENERATE_REPORT}/download/${id}`);
  },

  /**
   * Retrieves a list of scheduled reports
   *
   * @param params - Query parameters for filtering scheduled reports
   * @returns Promise resolving to scheduled report list
   */
  getScheduledReports: async (params?: ReportListParams) => {
    return apiClient.get(`${ANALYTICS_ENDPOINTS.REPORTS}/scheduled`, { params });
  },

  /**
   * Schedules a report for automatic generation
   *
   * @param id - Report ID
   * @param scheduleParams - Schedule parameters
   * @returns Promise resolving to scheduled report details
   */
  scheduleReport: async (id: string, scheduleParams: ScheduledReportParams) => {
    return apiClient.post(`${ANALYTICS_ENDPOINTS.REPORTS}/${id}/schedule`, scheduleParams);
  },

  /**
   * Disables scheduling for a report
   *
   * @param id - Report ID
   * @returns Promise resolving to confirmation
   */
  unscheduleReport: async (id: string) => {
    return apiClient.delete(`${ANALYTICS_ENDPOINTS.REPORTS}/${id}/schedule`);
  }
};

export default analyticsService;