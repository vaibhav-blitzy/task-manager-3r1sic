import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react'; // v14.0.x
import userEvent from '@testing-library/user-event'; // v14.0.x
import { Checkbox } from './Checkbox';

describe('Checkbox', () => {
  it('renders unchecked by default', () => {
    render(<Checkbox />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
  });

  it('renders checked when checked prop is true', () => {
    render(<Checkbox checked={true} />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  it('calls onChange when clicked', async () => {
    const handleChange = jest.fn();
    render(<Checkbox onChange={handleChange} />);
    
    const checkbox = screen.getByRole('checkbox');
    await userEvent.click(checkbox);
    
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Checkbox disabled={true} />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  it('displays the label correctly', () => {
    const testLabel = 'Test Label';
    render(<Checkbox label={testLabel} />);
    expect(screen.getByText(testLabel)).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    const testLabel = 'Accessibility Test';
    render(<Checkbox label={testLabel} />);
    
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveAttribute('aria-checked', 'false');
    
    // Ensure checkbox has an id
    expect(checkbox).toHaveAttribute('id');
    
    // Ensure label is associated with input via id
    const id = checkbox.getAttribute('id');
    const label = screen.getByText(testLabel);
    expect(label).toHaveAttribute('for', id);
  });

  it('indicates indeterminate state with aria-checked', () => {
    render(<Checkbox indeterminate={true} />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toHaveAttribute('aria-checked', 'mixed');
  });
});