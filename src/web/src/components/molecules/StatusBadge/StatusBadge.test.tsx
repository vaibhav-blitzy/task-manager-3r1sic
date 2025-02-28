import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import StatusBadge from './StatusBadge';

describe('StatusBadge', () => {
  it('should render not-started status correctly', () => {
    render(<StatusBadge status="not-started" />);
    expect(screen.getByText('Not Started')).toBeInTheDocument();
  });

  it('should render in-progress status correctly', () => {
    render(<StatusBadge status="in-progress" />);
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });

  it('should render on-hold status correctly', () => {
    render(<StatusBadge status="on-hold" />);
    expect(screen.getByText('On Hold')).toBeInTheDocument();
  });

  it('should render in-review status correctly', () => {
    render(<StatusBadge status="in-review" />);
    expect(screen.getByText('In Review')).toBeInTheDocument();
  });

  it('should render completed status correctly', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('should render cancelled status correctly', () => {
    render(<StatusBadge status="cancelled" />);
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('should handle unknown status correctly', () => {
    render(<StatusBadge status="unknown-status" />);
    expect(screen.getByText('Unknown Status')).toBeInTheDocument();
  });

  it('should display progress bar for in-progress status with percentage', () => {
    render(<StatusBadge status="in-progress" progressPercent={50} />);
    
    // Check for progress bar element
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
  });

  it('should not display progress bar for completed status with percentage', () => {
    render(<StatusBadge status="completed" progressPercent={100} />);
    
    // Progress bar should not be rendered for non-in-progress statuses
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('should render with icon by default', () => {
    render(<StatusBadge status="in-progress" />);
    
    // The Icon component renders with the aria-hidden attribute
    const icon = document.querySelector('[aria-hidden="true"]');
    expect(icon).not.toBeNull();
  });

  it('should not display icon when showIcon is false', () => {
    render(<StatusBadge status="in-progress" showIcon={false} />);
    
    // No icon should be present when showIcon is false
    const icon = document.querySelector('[aria-hidden="true"]');
    expect(icon).toBeNull();
  });
});