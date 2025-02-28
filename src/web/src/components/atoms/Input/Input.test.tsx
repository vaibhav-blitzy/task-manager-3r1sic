import React from 'react'; // react ^18.2.0
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils'; // Custom testing utilities
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { describe, it, expect, jest } from '@jest/globals'; // Jest testing framework functions
import Input from './Input'; // The Input component being tested

describe('Input component', () => {
  it('should render with default props', () => {
    // Render an Input component with default props
    render(<Input />);

    // Verify input element is in the document
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toBeInTheDocument();

    // Verify input has the default type (text)
    expect(inputElement).toHaveAttribute('type', 'text');
  });

  it('should render with different types', () => {
    // Render an Input component with type='password'
    render(<Input type="password" />);

    // Verify input has type='password' attribute
    const passwordInput = screen.getByRole('textbox', { type: 'password' });
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Render an Input component with type='email'
    render(<Input type="email" />);

    // Verify input has type='email' attribute
    const emailInput = screen.getByRole('textbox', { type: 'email' });
    expect(emailInput).toHaveAttribute('type', 'email');

    // Render an Input component with type='number'
    render(<Input type="number" />);

    // Verify input has type='number' attribute
    const numberInput = screen.getByRole('spinbutton');
    expect(numberInput).toHaveAttribute('type', 'number');
  });

  it('should render with placeholder text', () => {
    // Render an Input component with a placeholder prop
    render(<Input placeholder="Enter your name" />);

    // Verify input element has the correct placeholder attribute
    const inputElement = screen.getByPlaceholderText('Enter your name');
    expect(inputElement).toBeInTheDocument();
  });

  it('should handle value changes', async () => {
    // Create a mock function for onChange handler
    const onChange = jest.fn();

    // Render an Input component with the mock handler
    render(<Input onChange={onChange} />);

    // Type text in the input field using userEvent
    const inputElement = screen.getByRole('textbox');
    await userEvent.type(inputElement, 'test');

    // Verify the onChange handler was called with the expected values
    expect(onChange).toHaveBeenCalledTimes(4);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({
      target: expect.objectContaining({
        value: 'test'
      })
    }));
  });

  it('should display error state correctly', () => {
    // Render an Input component with an error prop
    render(<Input error="This field is required" id="test-input" />);

    // Verify input has error styling classes
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveClass('border-error');

    // Verify error message is displayed
    const errorMessage = screen.getByText('This field is required');
    expect(errorMessage).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    // Render an Input component with disabled={true}
    render(<Input disabled={true} />);

    // Verify input has the disabled attribute
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toBeDisabled();

    // Verify input has disabled styling classes
    expect(inputElement).toHaveClass('bg-neutral-100');
  });

  it('should handle focus and blur events', () => {
    // Create mock functions for onFocus and onBlur handlers
    const onFocus = jest.fn();
    const onBlur = jest.fn();

    // Render an Input component with the mock handlers
    render(<Input onFocus={onFocus} onBlur={onBlur} />);

    // Trigger focus event on the input
    const inputElement = screen.getByRole('textbox');
    fireEvent.focus(inputElement);

    // Verify onFocus handler was called
    expect(onFocus).toHaveBeenCalledTimes(1);

    // Trigger blur event on the input
    fireEvent.blur(inputElement);

    // Verify onBlur handler was called
    expect(onBlur).toHaveBeenCalledTimes(1);
  });

  it('should apply custom className', () => {
    // Render an Input component with a custom className prop
    render(<Input className="custom-input-class" />);

    // Verify input has both default and custom classes
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveClass('custom-input-class');
  });

  it('should render with different sizes', () => {
    // Render an Input component with size='sm'
    render(<Input size="sm" />);

    // Verify input has small size class
    const inputElementSm = screen.getByRole('textbox');
    expect(inputElementSm).toHaveClass('px-2');
    expect(inputElementSm).toHaveClass('py-1');
    expect(inputElementSm).toHaveClass('text-xs');

    // Render an Input component with size='md'
    render(<Input size="md" />);

    // Verify input has medium size class
    const inputElementMd = screen.getByRole('textbox');
    expect(inputElementMd).toHaveClass('px-3');
    expect(inputElementMd).toHaveClass('py-2');
    expect(inputElementMd).toHaveClass('text-sm');

    // Render an Input component with size='lg'
    render(<Input size="lg" />);

    // Verify input has large size class
    const inputElementLg = screen.getByRole('textbox');
    expect(inputElementLg).toHaveClass('px-4');
    expect(inputElementLg).toHaveClass('py-3');
    expect(inputElementLg).toHaveClass('text-base');
  });

  it('should have proper accessibility attributes', () => {
    // Render an Input component with ariaLabel prop
    render(<Input ariaLabel="Test Input" />);

    // Verify aria-label attribute is set correctly
    const inputElementAria = screen.getByRole('textbox');
    expect(inputElementAria).toHaveAttribute('aria-label', 'Test Input');

    // Render an Input with required={true}
    render(<Input required={true} />);

    // Verify aria-required attribute is set to true
    const inputElementRequired = screen.getByRole('textbox');
    expect(inputElementRequired).toHaveAttribute('aria-required', 'true');

    // Render an Input with id and associated label
    render(
      <>
        <label htmlFor="test-id">Test Label</label>
        <Input id="test-id" />
      </>
    );

    // Verify input is properly associated with label element
    const inputElementLabel = screen.getByRole('textbox');
    expect(inputElementLabel).toHaveAttribute('id', 'test-id');
  });

  it('should handle maxLength property', async () => {
    // Render an Input component with maxLength={10}
    render(<Input maxLength={10} />);

    // Verify input has maxLength attribute set to 10
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveAttribute('maxlength', '10');

    // Type text longer than maxLength
    await userEvent.type(inputElement, 'This is a very long text');

    // Verify input value is truncated to maxLength
    await waitFor(() => {
      expect(inputElement).toHaveValue('This is a v');
    });
  });
});