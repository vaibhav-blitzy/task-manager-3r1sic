import React from 'react'; // ^18.2.0
import { describe, it, expect } from '@jest/globals'; // ^29.0.0
import Label from './Label';
import { render, screen } from '../../../utils/test-utils';

describe('Label component', () => {
  // Group related tests for the Label component
  it('renders correctly with default props', () => {
    // Tests that the label renders correctly with default props
    // Render a Label component with default props and text content
    render(<Label>Test Label</Label>);

    // Verify label element is in the document
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toBeInTheDocument();

    // Verify label has the correct text content
    expect(labelElement).toHaveTextContent('Test Label');

    // Verify label has the default styling classes
    expect(labelElement).toHaveClass('text-xs');
    expect(labelElement).toHaveClass('font-medium');
  });

  it('renders with htmlFor attribute', () => {
    // Tests that the label correctly sets the htmlFor attribute for accessibility
    // Render a Label component with a specific htmlFor attribute
    render(<Label htmlFor="testInput">Test Label</Label>);

    // Verify the htmlFor attribute is correctly set on the label element
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveAttribute('htmlFor', 'testInput');

    // Confirm accessible association with form elements
    expect(labelElement.getAttribute('htmlFor')).toBe('testInput');
  });

  it('applies error styling when error prop is true', () => {
    // Tests that the label shows error styling when the error prop is provided
    // Render a Label component with error prop set to true
    render(<Label error>Test Label</Label>);

    // Verify that the label has the error styling class (text-red-500)
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveClass('text-red-500');
  });

  it('applies disabled styling when disabled prop is true', () => {
    // Tests that the label shows disabled styling when the disabled prop is provided
    // Render a Label component with disabled prop set to true
    render(<Label disabled>Test Label</Label>);

    // Verify that the label has the disabled styling class (text-gray-400)
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveClass('text-gray-400');
  });

  it('renders required indicator when required prop is true', () => {
    // Tests that the label shows the required indicator asterisk when the required prop is true
    // Render a Label component with required prop set to true
    render(<Label required>Test Label</Label>);

    // Verify that the label includes the required indicator (*) in its content
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveTextContent('Test Label*');

    // Verify the required indicator has the correct styling
    const requiredIndicator = screen.getByText('*');
    expect(requiredIndicator).toHaveClass('ml-1');
    expect(requiredIndicator).toHaveClass('text-red-500');
  });

  it('applies custom className', () => {
    // Tests that custom class names are applied to the label
    // Render a Label component with a custom className prop
    render(<Label className="custom-class">Test Label</Label>);

    // Verify the custom class is applied along with default classes
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveClass('custom-class');
  });
});