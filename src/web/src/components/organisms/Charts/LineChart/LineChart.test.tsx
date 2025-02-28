import React from 'react'; // react ^18.2.0
import { render, screen } from '../../../../utils/test-utils';
import { LineChart } from './LineChart'; // Import the LineChart component being tested
import { jest } from '@jest/globals'; // Import Jest testing functions
const { describe, it, expect, beforeEach } = global; // Extract Jest functions for use

// Mock the useMediaQuery hook to control responsive behavior during tests
jest.mock('../../../../hooks/useMediaQuery', () => ({
  useMediaQuery: (query: string) => {
    // Mock implementation to return true for mobile and false for others
    return query === '(max-width: 640px)';
  },
}));

/**
 * Creates mock data for testing the LineChart component
 * @returns Chart data object with labels and datasets
 */
const setupMockChartData = () => {
  const labels = ['January', 'February', 'March', 'April', 'May', 'June', 'July'];
  const datasets = [
    {
      label: 'Dataset 1',
      data: [65, 59, 80, 81, 56, 55, 40],
      borderColor: 'blue',
      backgroundColor: 'rgba(0, 0, 255, 0.2)',
    },
    {
      label: 'Dataset 2',
      data: [28, 48, 40, 19, 86, 27, 90],
      borderColor: 'red',
      backgroundColor: 'rgba(255, 0, 0, 0.2)',
    },
  ];
  return { labels, datasets };
};

/**
 * Creates mock time-series data for testing date-based charts
 * @returns Chart data with Date objects as labels
 */
const setupMockTimeData = () => {
  const startDate = new Date('2024-01-01');
  const labels = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + i);
    return date;
  });
  const datasets = [
    {
      label: 'Time Series Data',
      data: [10, 20, 15, 25, 30, 20, 22],
      borderColor: 'green',
      backgroundColor: 'rgba(0, 255, 0, 0.2)',
    },
  ];
  return { labels, datasets };
};

describe('LineChart component', () => {
  it('renders without crashing', () => {
    const { labels, datasets } = setupMockChartData();
    render(<LineChart labels={labels} datasets={datasets} />);
    expect(screen.getByRole('img', { name: 'Line chart' })).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    const { labels, datasets } = setupMockChartData();
    render(<LineChart labels={labels} datasets={datasets} className="custom-class" />);
    const container = screen.getByRole('img', { name: 'Line chart' }).closest('.line-chart-container');
    expect(container).toHaveClass('custom-class');
  });

  it('renders with custom dimensions', () => {
    const { labels, datasets } = setupMockChartData();
    render(<LineChart labels={labels} datasets={datasets} height={300} width={400} />);
    const container = screen.getByRole('img', { name: 'Line chart' }).closest('.line-chart-container');
    expect(container).toHaveStyle('height: 300px');
    expect(container).toHaveStyle('width: 400px');
  });

  it('handles time-based data correctly', () => {
    const { labels, datasets } = setupMockTimeData();
    render(<LineChart labels={labels} datasets={datasets} xAxisType="time" />);
    expect(screen.getByRole('img', { name: 'Line chart' })).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    render(<LineChart labels={[]} datasets={[]} />);
    expect(screen.getByText('No data available to display')).toBeInTheDocument();
  });

  it('renders with axis labels', () => {
    const { labels, datasets } = setupMockChartData();
    render(<LineChart labels={labels} datasets={datasets} xAxisLabel="X Axis" yAxisLabel="Y Axis" />);
    expect(screen.getByText('X Axis')).toBeInTheDocument();
    expect(screen.getByText('Y Axis')).toBeInTheDocument();
  });

  it('can hide grid lines', () => {
    const { labels, datasets } = setupMockChartData();
    render(<LineChart labels={labels} datasets={datasets} showGridLines={false} />);
    expect(screen.getByRole('img', { name: 'Line chart' })).toBeInTheDocument();
  });
});