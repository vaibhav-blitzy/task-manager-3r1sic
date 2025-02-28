import React from 'react'; // react ^18.2.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.0.0

import { Button } from './Button'; // Button component being tested
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils'; // Custom testing utilities

describe('Button component', () => {
  it('renders correctly with default props', () => {
    // Render a Button component with default props and children text
    render(<Button>Click me</Button>);

    // Verify button element is in the document
    const buttonElement = screen.getByRole('button');
    expect(buttonElement).toBeInTheDocument();

    // Verify button has the correct text content
    expect(buttonElement).toHaveTextContent('Click me');

    // Verify button has the primary variant class by default
    expect(buttonElement).toHaveClass('bg-primary-600');

    // Verify button has the medium size class by default
    expect(buttonElement).toHaveClass('px-4');
  });

  it('renders with different variants', () => {
    // Test primary variant styling
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByText('Primary')).toHaveClass('bg-primary-600');

    // Test secondary variant styling
    render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-secondary-600');

    // Test outline variant styling
    render(<Button variant="outline">Outline</Button>);
    expect(screen.getByText('Outline')).toHaveClass('border');

    // Test danger variant styling
    render(<Button variant="danger">Danger</Button>);
    expect(screen.getByText('Danger')).toHaveClass('bg-red-600');

    // Test text variant styling
    render(<Button variant="text">Text</Button>);
    expect(screen.getByText('Text')).toHaveClass('bg-transparent');
  });

  it('renders with different sizes', () => {
    // Test small size styling
    render(<Button size="sm">Small</Button>);
    expect(screen.getByText('Small')).toHaveClass('px-2.5');

    // Test medium size styling
    render(<Button size="md">Medium</Button>);
    expect(screen.getByText('Medium')).toHaveClass('px-4');

    // Test large size styling
    render(<Button size="lg">Large</Button>);
    expect(screen.getByText('Large')).toHaveClass('px-6');
  });

  it('renders full width when isFullWidth is true', () => {
    // Render button with isFullWidth prop set to true
    render(<Button isFullWidth>Full Width</Button>);

    // Verify button has the full width class
    expect(screen.getByText('Full Width')).toHaveClass('w-full');
  });

  it('displays loading state', () => {
    // Render button with isLoading prop set to true
    render(<Button isLoading>Loading</Button>);

    // Verify loading spinner/indicator is visible
    expect(screen.getByRole('button')).toHaveClass('opacity-50');

    // Verify button is disabled while loading
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders with left and right icons', () => {
    const TestIcon = () => <span>TestIcon</span>;

    // Render button with an icon and iconPosition set to 'left'
    render(<Button icon={<TestIcon />} iconPosition="left">Left Icon</Button>);

    // Verify icon is rendered before text
    expect(screen.getByText('Left Icon').previousSibling).toHaveTextContent('TestIcon');

    // Render button with an icon and iconPosition set to 'right'
    render(<Button icon={<TestIcon />} iconPosition="right">Right Icon</Button>);

    // Verify icon is rendered after text
    expect(screen.getByText('Right Icon').nextSibling).toHaveTextContent('TestIcon');
  });

  it('applies custom className', () => {
    // Render button with a custom className prop
    render(<Button className="custom-class">Custom Class</Button>);

    // Verify the custom class is applied along with default classes
    expect(screen.getByText('Custom Class')).toHaveClass('custom-class');
  });

  it('handles click events', () => {
    // Create a mock onClick handler function
    const handleClick = jest.fn();

    // Render button with the mock handler
    render(<Button onClick={handleClick}>Clickable</Button>);

    // Simulate a click on the button
    fireEvent.click(screen.getByText('Clickable'));

    // Verify the mock handler was called
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not trigger click when disabled', () => {
    // Create a mock onClick handler function
    const handleClick = jest.fn();

    // Render button with the mock handler and disabled prop set to true
    render(<Button onClick={handleClick} disabled>Disabled</Button>);

    // Simulate a click on the button
    fireEvent.click(screen.getByText('Disabled'));

    // Verify the mock handler was not called
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('has proper accessibility attributes', () => {
    // Render button with aria-label
    render(<Button aria-label="Custom label">Accessible Button</Button>);

    // Verify aria-label is applied correctly
    expect(screen.getByRole('button', { name: 'Custom label' })).toBeInTheDocument();

    // Test button with disabled state
    render(<Button disabled>Disabled Button</Button>);

    // Verify aria-disabled is set correctly
    expect(screen.getByRole('button', { name: 'Disabled Button' })).toBeDisabled();

    // Verify loading state has appropriate aria attributes
    render(<Button isLoading>Loading Button</Button>);
    expect(screen.getByRole('button', { name: 'Loading Button' })).toHaveAttribute('aria-busy', 'true');
  });
});