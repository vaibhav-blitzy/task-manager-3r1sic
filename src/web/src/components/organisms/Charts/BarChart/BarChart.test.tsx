import React from 'react'; // react ^18.2.x
import { render, screen } from '../../../../utils/test-utils'; // Provides custom render function that wraps components with necessary providers
import { BarChart } from './BarChart'; // Import the component being tested
import '@testing-library/react'; // Jest testing functions for component tests

// Define mock data for chart
const mockData = [
  { label: 'Jan', value: 10 },
  { label: 'Feb', value: 20 },
  { label: 'Mar', value: 15 },
];

// Define mock bars configuration
const mockBars = [
  { backgroundColor: 'red' },
  { backgroundColor: 'blue' },
  { backgroundColor: 'green' },
];

describe('BarChart component', () => { // Jest test suite for BarChart component
  it('renders without crashing', () => { // Tests basic rendering of the chart component
    render(<BarChart data={mockData} />); // Render BarChart with mockData and mockBars
  });

  it('applies custom class name', () => { // Tests that custom classNames are properly applied
    const { container } = render(<BarChart data={mockData} className="custom-class" />); // Render BarChart with a custom className prop
    expect(container.firstChild).toHaveClass('custom-class'); // Verify using expect(container.firstChild).toHaveClass('custom-class')
  });

  it('renders with custom dimensions', () => { // Tests rendering with custom height and width props
    render(<BarChart data={mockData} height={400} width={600} />); // Render BarChart with height and width props
  });

  it('can render stacked bars', () => { // Tests rendering with stacked bar configuration
    render(<BarChart data={mockData} isStacked={true} />); // Render BarChart with isStacked prop set to true
  });

  it('can hide grid lines', () => { // Tests rendering without grid lines
    render(<BarChart data={mockData} showGrid={false} />); // Render BarChart with showGrid prop set to false
  });

  it('can hide legend', () => { // Tests rendering without legend
    render(<BarChart data={mockData} showLegend={false} />); // Render BarChart with showLegend prop set to false
  });
});