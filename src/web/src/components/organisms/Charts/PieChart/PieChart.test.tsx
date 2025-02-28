import React from 'react'; // react ^18.2.0
import { screen, fireEvent } from '@testing-library/react'; // @testing-library/react ^14.0.0
import '@testing-library/jest-dom'; // @testing-library/jest-dom ^5.16.5
import { describe, it, expect, vi } from 'vitest'; // vitest ^0.34.1
import { render } from '../../../../utils/test-utils';
import PieChart from './PieChart';

// Extend Jest matchers for DOM testing

describe('PieChart', () => {
  // Main test suite for PieChart component
  // Groups all tests for the PieChart component

  it('should render the PieChart component', () => {
    // Tests basic rendering of the component
    // Creates mock data with createMockData()
    const mockData = createMockData();
    // Renders PieChart with mock data
    render(<PieChart data={mockData} />);
    // Verifies chart container exists in document
    const chartContainer = screen.getByRole('img', { name: /Pie chart showing data distribution/i });
    expect(chartContainer).toBeInTheDocument();
    // Checks SVG element is rendered
    const svgElement = chartContainer.querySelector('svg');
    expect(svgElement).toBeInTheDocument();
  });

  it('should render the chart title correctly', () => {
    // Tests title rendering
    // Creates test title 'Task Status'
    const title = 'Task Status';
    // Renders PieChart with title prop and mock data
    const mockData = createMockData();
    render(<PieChart data={mockData} title={title} />);
    // Queries for title element
    const titleElement = screen.getByText(title);
    // Checks title text is displayed correctly
    expect(titleElement).toBeInTheDocument();
  });

  it('should render correct number of segments based on data', () => {
    // Tests data segment rendering
    // Creates mock data with known length
    const mockData = createMockData();
    // Renders PieChart with mock data
    render(<PieChart data={mockData} />);
    // Queries for all path elements in SVG
    const pathElements = screen.getAllByRole('img', { name: /Pie chart showing data distribution/i })[0].querySelectorAll('path');
    // Verifies number of paths matches data length
    expect(pathElements.length).toBe(mockData.length);
  });

  it('should render legends with correct labels', () => {
    // Tests legend rendering
    // Creates mock data with specific labels
    const mockData = createMockData();
    // Renders PieChart with mock data
    render(<PieChart data={mockData} />);

    // For each mock data item, checks its label appears in the document
    mockData.forEach(item => {
      const legendLabel = screen.getByText(item.label);
      expect(legendLabel).toBeInTheDocument();
    });
  });

  it('should display message when no data provided', () => {
    // Tests empty data handling
    // Renders PieChart with empty array
    render(<PieChart data={[]} />);
    // Checks for 'No data to display' message in the document
    expect(screen.getByText('No data to display')).toBeInTheDocument();
  });

  it('should call onSegmentClick when segment is clicked', () => {
    // Tests segment click interaction
    // Creates mock click handler with vi.fn()
    const onSegmentClick = vi.fn();
    // Renders PieChart with onSegmentClick prop and mock data
    const mockData = createMockData();
    render(<PieChart data={mockData} onClick={onSegmentClick} />);
    // Queries for a segment element
    const chartContainer = screen.getByRole('img', { name: /Pie chart showing data distribution/i });
    const segment = chartContainer.querySelector('path');
    // Simulates click on the segment
    if (segment) {
      fireEvent.click(segment);
    }
    // Verifies mock handler was called
    expect(onSegmentClick).toHaveBeenCalled();
    // Checks handler was called with correct segment data
    expect(onSegmentClick).toHaveBeenCalledWith(expect.any(Number));
  });

  const createMockData = () => {
    // Helper function to create mock chart data
    // Creates and returns an array of task status data objects
    // Each object has label, value, and color properties
    // Represents typical task status distribution (To Do, In Progress, Completed, etc.)
    return [
      { label: 'To Do', value: 15, color: '#FF6384' },
      { label: 'In Progress', value: 20, color: '#36A2EB' },
      { label: 'Completed', value: 10, color: '#FFCE56' },
      { label: 'On Hold', value: 5, color: '#4BC0C0' }
    ];
  };
});