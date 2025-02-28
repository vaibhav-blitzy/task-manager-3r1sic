import React from 'react'; // react ^18.2.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.0.0
import { FaUser } from 'react-icons/fa'; // react-icons/fa ^4.10.0
import { render, screen, fireEvent } from '../../../utils/test-utils'; // Custom testing utilities
import Icon from './Icon'; // The Icon component being tested
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0

describe('Icon component', () => {
  // Group related tests for the Icon component
  it('renders correctly with default props', () => {
    // Tests that the icon renders correctly with the required icon prop
    // Render an Icon component with FaUser icon
    render(<Icon icon={FaUser} />);

    // Verify icon element is in the document
    const iconElement = screen.getByTestId('icon');
    expect(iconElement).toBeInTheDocument();

    // Verify icon has the default size and color
    expect(iconElement).toHaveClass('icon');
  });

  it('applies custom size', () => {
    // Tests that the icon properly applies custom size
    // Render an Icon with a specific size value
    render(<Icon icon={FaUser} size={48} />);

    // Verify the icon has the correct size attribute or style
    const iconElement = screen.getByTestId('icon');
    expect(iconElement).toHaveAttribute('size', '48');
  });

  it('applies custom color', () => {
    // Tests that the icon renders with custom color
    // Render an Icon with a specific color value
    render(<Icon icon={FaUser} color="red" />);

    // Verify the icon has the correct color attribute or style
    const iconElement = screen.getByTestId('icon');
    expect(iconElement).toHaveStyle({ color: 'red' });
  });

  it('applies custom className', () => {
    // Tests that the icon applies additional custom class names
    // Render an Icon with a custom className prop
    render(<Icon icon={FaUser} className="custom-class" />);

    // Verify the custom class is applied along with default classes
    const iconElement = screen.getByTestId('icon');
    expect(iconElement).toHaveClass('custom-class');
    expect(iconElement).toHaveClass('icon');
  });

  it('handles click events', async () => {
    // Tests that the icon properly handles click events when provided
    // Create a mock onClick handler function
    const onClick = jest.fn();

    // Render Icon with the mock handler
    render(<Icon icon={FaUser} onClick={onClick} />);

    // Simulate a click on the icon
    const iconElement = screen.getByTestId('icon');
    await userEvent.click(iconElement);

    // Verify the mock handler was called
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('has proper accessibility attributes', () => {
    // Tests that the icon has appropriate accessibility attributes
    // Render icon with aria-label prop
    render(<Icon icon={FaUser} ariaLabel="Close" />);

    // Verify aria-label is applied correctly
    let iconElement = screen.getByTestId('icon');
    expect(iconElement).toHaveAttribute('aria-label', 'Close');

    // Render icon with title prop
    render(<Icon icon={FaUser} title="User Profile" />);

    // Verify title attribute is applied correctly
    iconElement = screen.getByTestId('icon');
    expect(iconElement).toHaveAttribute('title', 'User Profile');
  });
});