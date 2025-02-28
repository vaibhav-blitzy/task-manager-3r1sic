import React from 'react'; // react ^18.2.x
import { render, screen, fireEvent, userEvent } from '../../../utils/test-utils'; // Custom testing utilities
import FormField from './FormField'; // Component under test
import Input from '../../atoms/Input/Input'; // Child component to be used inside FormField for testing

describe('FormField component', () => {
  it('renders with label and input', () => {
    // Render FormField with label and Input as child component
    render(
      <FormField label="Test Label" htmlFor="test-input">
        <Input type="text" />
      </FormField>
    );

    // Verify label element is visible
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toBeVisible();

    // Verify input element is accessible
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toBeAccessible();
  });

  it('displays required indicator when field is required', () => {
    // Render FormField with required prop set to true
    render(
      <FormField label="Test Label" htmlFor="test-input" required>
        <Input type="text" />
      </FormField>
    );

    // Verify required indicator (asterisk) is visible
    const requiredIndicator = screen.getByText('*');
    expect(requiredIndicator).toBeVisible();

    // Check that aria-required attribute is set correctly
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveAttribute('aria-required', 'true');
  });

  it('displays error message when error prop is provided', () => {
    // Render FormField with an error message
    render(
      <FormField label="Test Label" htmlFor="test-input" error="This field is required">
        <Input type="text" />
      </FormField>
    );

    // Verify error message is visible
    const errorMessage = screen.getByText('This field is required');
    expect(errorMessage).toBeVisible();

    // Check that aria-invalid attribute is set correctly
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveAttribute('aria-invalid', 'true');

    // Verify aria-describedby connects input to error message
    expect(inputElement).toHaveAttribute('aria-describedby', 'test-input-error');
  });

  it('displays helper text when helperText prop is provided', () => {
    // Render FormField with helper text
    render(
      <FormField label="Test Label" htmlFor="test-input" helperText="Enter your full name">
        <Input type="text" />
      </FormField>
    );

    // Verify helper text is visible
    const helperTextElement = screen.getByText('Enter your full name');
    expect(helperTextElement).toBeVisible();

    // Check that aria-describedby connects input to helper text
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toHaveAttribute('aria-describedby', 'test-input-helper');
  });

  it('applies disabled state to label and input', () => {
    // Render FormField with disabled prop set to true
    render(
      <FormField label="Test Label" htmlFor="test-input" disabled>
        <Input type="text" />
      </FormField>
    );

    // Verify label has disabled styling
    const labelElement = screen.getByText('Test Label');
    expect(labelElement).toHaveClass('text-gray-400');

    // Check that input element has disabled attribute
    const inputElement = screen.getByRole('textbox');
    expect(inputElement).toBeDisabled();

    // Attempt interaction with input and verify it's disabled
    userEvent.type(inputElement, 'test');
    expect(inputElement).toHaveValue('');
  });

  it('passes input events through to onChange handler', () => {
    // Create a mock function for onChange handler
    const onChange = jest.fn();

    // Render FormField with Input child that has the mock handler
    render(
      <FormField label="Test Label" htmlFor="test-input">
        <Input type="text" onChange={onChange} />
      </FormField>
    );

    // Simulate user typing in the input
    const inputElement = screen.getByRole('textbox');
    fireEvent.change(inputElement, { target: { value: 'test' } });

    // Verify that the onChange handler was called correctly
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ target: { value: 'test' } }));
  });
});