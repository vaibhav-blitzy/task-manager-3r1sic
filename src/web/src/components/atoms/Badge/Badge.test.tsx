import React from 'react'; // react ^18.2.0
import { render, screen } from '../../../utils/test-utils';
import { vi } from 'vitest'; // vitest ^0.34.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import Badge, { BadgeColor, BadgeSize, getStatusBadgeProps, getPriorityBadgeProps, getProjectStatusBadgeProps } from './Badge';

describe('Badge component', () => {
  // LD1: Tests that the Badge component renders correctly with default props
  test('renders with default props', () => {
    // Arrange
    const childrenText = 'Test Badge';

    // Act
    render(<Badge>{childrenText}</Badge>);

    // Assert
    const badgeElement = screen.getByText(childrenText);
    expect(badgeElement).toBeInTheDocument();
    expect(badgeElement).toHaveClass('text-gray-700');
    expect(badgeElement).toHaveClass('bg-gray-200');
    expect(badgeElement).toHaveClass('text-sm');
    expect(badgeElement).toHaveClass('px-2');
    expect(badgeElement).toHaveClass('py-1');
    expect(badgeElement).toHaveClass('rounded-full');
  });

  // LD1: Tests that the Badge component correctly applies styling for different color variants
  test('applies different colors correctly', () => {
    // Arrange
    const colors = [
      BadgeColor.PRIMARY,
      BadgeColor.SUCCESS,
      BadgeColor.WARNING,
      BadgeColor.ERROR,
      BadgeColor.INFO,
      BadgeColor.NEUTRAL,
    ];
    const colorClasses = {
      [BadgeColor.PRIMARY]: 'text-white bg-primary-700',
      [BadgeColor.SUCCESS]: 'text-white bg-green-600',
      [BadgeColor.WARNING]: 'text-white bg-amber-600',
      [BadgeColor.ERROR]: 'text-white bg-red-600',
      [BadgeColor.INFO]: 'text-white bg-blue-600',
      [BadgeColor.NEUTRAL]: 'text-gray-700 bg-gray-200',
    };

    // Act
    colors.forEach((color) => {
      render(<Badge color={color}>Test Badge</Badge>);
      const badgeElement = screen.getByText('Test Badge');
      expect(badgeElement).toHaveClass(colorClasses[color]);
    });
  });

  // LD1: Tests that the Badge component correctly applies styling for different size variants
  test('applies different sizes correctly', () => {
    // Arrange
    const sizes = [BadgeSize.SMALL, BadgeSize.MEDIUM, BadgeSize.LARGE];
    const sizeClasses = {
      [BadgeSize.SMALL]: 'text-xs px-1.5 py-0.5',
      [BadgeSize.MEDIUM]: 'text-sm px-2 py-1',
      [BadgeSize.LARGE]: 'text-base px-2.5 py-1.5',
    };

    // Act
    sizes.forEach((size) => {
      render(<Badge size={size}>Test Badge</Badge>);
      const badgeElement = screen.getByText('Test Badge');
      expect(badgeElement).toHaveClass(sizeClasses[size]);
    });
  });

  // LD1: Tests that the Badge component applies outlined styling when the outlined prop is true
  test('renders outlined version when outlined prop is true', () => {
    // Act
    render(<Badge outlined={true}>Test Badge</Badge>);

    // Assert
    const badgeElement = screen.getByText('Test Badge');
    expect(badgeElement).not.toHaveClass('bg-primary-700');
    expect(badgeElement).toHaveClass('bg-transparent');
    expect(badgeElement).toHaveClass('border');
  });

  // LD1: Tests that the Badge component renders with square corners when rounded prop is false
  test('renders with square corners when rounded is false', () => {
    // Act
    render(<Badge rounded={false}>Test Badge</Badge>);

    // Assert
    const badgeElement = screen.getByText('Test Badge');
    expect(badgeElement).not.toHaveClass('rounded-full');
    expect(badgeElement).toHaveClass('rounded');
  });

  // LD1: Tests that the Badge component correctly applies additional custom className
  test('applies additional className when provided', () => {
    // Arrange
    const customClassName = 'custom-test-class';

    // Act
    render(<Badge className={customClassName}>Test Badge</Badge>);

    // Assert
    const badgeElement = screen.getByText('Test Badge');
    expect(badgeElement).toHaveClass(customClassName);
    expect(badgeElement).toHaveClass('inline-flex');
  });

  // LD1: Tests that the Badge component calls the onClick handler when clicked
  test('calls onClick handler when clicked', async () => {
    // Arrange
    const mockHandler = vi.fn();

    // Act
    render(<Badge onClick={mockHandler}>Test Badge</Badge>);
    const badgeElement = screen.getByText('Test Badge');
    await userEvent.click(badgeElement);

    // Assert
    expect(mockHandler).toHaveBeenCalledTimes(1);
  });

  // LD1: Tests that getStatusBadgeProps helper returns appropriate badge props for different task statuses
  test('getStatusBadgeProps returns correct props for different statuses', () => {
    // Arrange
    const statusProps = {
      'COMPLETED': { color: BadgeColor.SUCCESS, text: 'Completed' },
      'IN_PROGRESS': { color: BadgeColor.PRIMARY, text: 'In Progress' },
      'ON_HOLD': { color: BadgeColor.WARNING, text: 'On Hold' },
      'CANCELLED': { color: BadgeColor.NEUTRAL, text: 'Cancelled' },
      'REVIEW': { color: BadgeColor.INFO, text: 'Review' },
      'OVERDUE': { color: BadgeColor.ERROR, text: 'Overdue' },
      'UNKNOWN': { color: BadgeColor.NEUTRAL, text: 'Unknown' },
    };

    // Act and Assert
    Object.entries(statusProps).forEach(([status, expectedProps]) => {
      const props = getStatusBadgeProps(status);
      expect(props.color).toBe(expectedProps.color);
    });
  });

  // LD1: Tests that getPriorityBadgeProps helper returns appropriate badge props for different task priorities
  test('getPriorityBadgeProps returns correct props for different priorities', () => {
    // Arrange
    const priorityProps = {
      'HIGH': { color: BadgeColor.ERROR, text: 'High' },
      'MEDIUM': { color: BadgeColor.WARNING, text: 'Medium' },
      'LOW': { color: BadgeColor.INFO, text: 'Low' },
      'UNKNOWN': { color: BadgeColor.NEUTRAL, text: 'Unknown' },
    };

    // Act and Assert
    Object.entries(priorityProps).forEach(([priority, expectedProps]) => {
      const props = getPriorityBadgeProps(priority);
      expect(props.color).toBe(expectedProps.color);
    });
  });

  // LD1: Tests that getProjectStatusBadgeProps helper returns appropriate badge props for different project statuses
  test('getProjectStatusBadgeProps returns correct props for different project statuses', () => {
    // Arrange
    const projectStatusProps = {
      'ACTIVE': { color: BadgeColor.PRIMARY, text: 'Active' },
      'COMPLETED': { color: BadgeColor.SUCCESS, text: 'Completed' },
      'ON_HOLD': { color: BadgeColor.WARNING, text: 'On Hold' },
      'PLANNING': { color: BadgeColor.INFO, text: 'Planning' },
      'CANCELLED': { color: BadgeColor.NEUTRAL, text: 'Cancelled' },
      'ARCHIVED': { color: BadgeColor.NEUTRAL, text: 'Archived' },
      'UNKNOWN': { color: BadgeColor.NEUTRAL, text: 'Unknown' },
    };

    // Act and Assert
    Object.entries(projectStatusProps).forEach(([status, expectedProps]) => {
      const props = getProjectStatusBadgeProps(status);
      expect(props.color).toBe(expectedProps.color);
    });
  });
});