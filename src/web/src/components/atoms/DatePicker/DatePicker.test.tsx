import React from 'react'; // react ^18.2.0
import { format, addDays, subDays } from 'date-fns'; // date-fns ^2.30.0
import {
  render,
  screen,
  fireEvent,
  waitFor,
  userEvent,
} from '../../../utils/test-utils';
import DatePicker from './DatePicker';
import { isValidDate } from '../../../utils/date';

/**
 * Helper function to set up the component under test with common props
 */
const setup = (customProps = {}) => {
  // Create a mock onChange function using jest.fn()
  const onChange = jest.fn();

  // Define default props for the DatePicker
  const defaultProps = {
    value: null,
    onChange: onChange,
    label: 'Select a date',
    placeholder: 'Choose date',
  };

  // Merge customProps with default props
  const props = { ...defaultProps, ...customProps };

  // Render the DatePicker component with combined props
  const { ...utils } = render(<DatePicker {...props} />);

  // Return rendered component, onChange mock, and utility functions
  return { ...utils, onChange };
};

describe('DatePicker component', () => {
  it('should render with label and placeholder', () => {
    // Render DatePicker with label and placeholder props
    const { getByText, getByPlaceholderText } = setup({
      label: 'Appointment Date',
      placeholder: 'Select your appointment date',
    });

    // Verify label text is visible in the document
    expect(getByText('Appointment Date')).toBeVisible();

    // Verify input has the correct placeholder text
    expect(getByPlaceholderText('Select your appointment date')).toBeInTheDocument();
  });

  it('should display the provided date value', () => {
    // Create a test date
    const testDate = new Date(2023, 9, 20); // October 20, 2023

    // Render DatePicker with the test date as value
    const { getByDisplayValue } = setup({ value: testDate });

    // Verify input displays the formatted date value
    expect(getByDisplayValue(format(testDate, 'MMM D, YYYY'))).toBeInTheDocument();
  });

  it('should toggle calendar visibility when clicking the input', async () => {
    // Render DatePicker component
    const { container, getByRole } = setup({});

    // Verify calendar is not initially visible
    expect(getByRole('dialog', { hidden: true })).toBeInTheDocument();

    // Click on the input element
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    fireEvent.click(inputElement);

    // Verify calendar becomes visible
    expect(getByRole('dialog', { hidden: false })).toBeInTheDocument();

    // Click on the input again
    fireEvent.click(inputElement);

    // Verify calendar is hidden again
    await waitFor(() => {
      expect(getByRole('dialog', { hidden: true })).toBeInTheDocument();
    });
  });

  it('should call onChange when selecting a date from calendar', async () => {
    // Render DatePicker component
    const { container, onChange } = setup({});

    // Click on the input to show calendar
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    fireEvent.click(inputElement);

    // Click on a date in the calendar
    const dayButton = screen.getByRole('gridcell', {
      name: format(addDays(new Date(), 2), 'MMMM d, yyyy'),
    });
    fireEvent.click(dayButton);

    // Verify onChange was called with the selected date
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.any(Date));

    // Verify calendar is closed after selection
    expect(screen.getByRole('dialog', { hidden: true })).toBeInTheDocument();

    // Verify input value is updated with the selected date
    expect(inputElement.value).toBe(format(addDays(new Date(), 2), 'MMM D, YYYY'));
  });

  it('should handle manual date input', async () => {
    // Render DatePicker component
    const { container, onChange } = setup({});

    // Type a valid date string in the input
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    await userEvent.type(inputElement, '10/25/2023');

    // Trigger blur event on the input
    fireEvent.blur(inputElement);

    // Verify onChange was called with the parsed date
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.any(Date));

    // Verify input value shows the formatted date
    expect(inputElement.value).toBe('Oct 25, 2023');
  });

  it('should validate date input on blur', async () => {
    // Render DatePicker component
    const { container, onChange } = setup({});

    // Type an invalid date string in the input
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    await userEvent.type(inputElement, 'invalid date');

    // Trigger blur event on the input
    fireEvent.blur(inputElement);

    // Verify input value is reset or shows an error state
    expect(inputElement.value).toBe('');

    // Verify onChange is not called with invalid date
    expect(onChange).not.toHaveBeenCalled();
  });

  it('should navigate between months', async () => {
    // Render DatePicker component
    const { container } = setup({});

    // Click on the input to show calendar
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    fireEvent.click(inputElement);

    // Get the current month heading text
    const initialMonth = screen.getByText(format(new Date(), 'MMMM yyyy'));

    // Click on next month button
    const nextMonthButton = screen.getByLabelText('Next month');
    fireEvent.click(nextMonthButton);

    // Verify month heading has changed to next month
    expect(screen.getByText(format(addDays(new Date(), 31), 'MMMM yyyy'))).toBeVisible();

    // Click on previous month button
    const prevMonthButton = screen.getByLabelText('Previous month');
    fireEvent.click(prevMonthButton);

    // Verify month heading has returned to original month
    expect(initialMonth).toBeVisible();
  });

  it('should respect min and max date constraints', async () => {
    // Create minDate (today) and maxDate (today + 30 days)
    const minDate = new Date();
    const maxDate = addDays(new Date(), 30);

    // Render DatePicker with minDate and maxDate props
    const { container, onChange } = setup({ minDate, maxDate });

    // Click on the input to show calendar
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    fireEvent.click(inputElement);

    // Try to select a date before minDate
    const beforeMinDate = subDays(minDate, 1);
    const beforeMinDateName = format(beforeMinDate, 'MMMM d, yyyy');
    const beforeMinDateButton = screen.queryByRole('gridcell', { name: beforeMinDateName });

    // Verify that date is disabled or not selectable
    if (beforeMinDateButton) {
      expect(beforeMinDateButton).toHaveAttribute('disabled');
    }

    // Try to select a date after maxDate
    const afterMaxDate = addDays(maxDate, 1);
    const afterMaxDateName = format(afterMaxDate, 'MMMM d, yyyy');
    const afterMaxDateButton = screen.queryByRole('gridcell', { name: afterMaxDateName });

    // Verify that date is disabled or not selectable
    if (afterMaxDateButton) {
      expect(afterMaxDateButton).toHaveAttribute('disabled');
    }

    // Select a date within the allowed range
    const validDate = addDays(minDate, 10);
    const validDateName = format(validDate, 'MMMM d, yyyy');
    const validDateButton = screen.getByRole('gridcell', { name: validDateName });
    fireEvent.click(validDateButton);

    // Verify onChange was called with the selected date
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.any(Date));
  });

  it('should support keyboard navigation', async () => {
    // Render DatePicker component
    const { container, onChange } = setup({});

    // Focus the input element
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    inputElement.focus();

    // Press down arrow key to open calendar
    fireEvent.keyDown(inputElement, { key: 'ArrowDown' });

    // Verify calendar becomes visible
    expect(screen.getByRole('dialog', { hidden: false })).toBeInTheDocument();

    // Test arrow keys to navigate between dates
    const initialDate = new Date();
    const nextDate = addDays(initialDate, 1);
    const prevDate = subDays(initialDate, 1);

    // Press right arrow key
    fireEvent.keyDown(inputElement, { key: 'ArrowRight' });
    expect(screen.getByRole('gridcell', { name: format(nextDate, 'MMMM d, yyyy') })).toHaveFocus();

    // Press left arrow key
    fireEvent.keyDown(inputElement, { key: 'ArrowLeft' });
    expect(screen.getByRole('gridcell', { name: format(initialDate, 'MMMM d, yyyy') })).toHaveFocus();

    // Press Enter key to select focused date
    fireEvent.keyDown(inputElement, { key: 'Enter' });

    // Verify onChange was called with selected date
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.any(Date));

    // Render DatePicker again
    const { container: container2 } = setup({});
    const inputElement2 = container2.querySelector('.date-picker__input') as HTMLInputElement;
    inputElement2.focus();

    // Open calendar and press Escape key
    fireEvent.click(inputElement2);
    fireEvent.keyDown(inputElement2, { key: 'Escape' });

    // Verify calendar is closed
    await waitFor(() => {
      expect(screen.getByRole('dialog', { hidden: true })).toBeInTheDocument();
    });
  });

  it('should close calendar when clicking outside', async () => {
    // Render DatePicker and a separate button outside the component
    const { container } = setup({});
    const button = document.createElement('button');
    button.textContent = 'Outside Button';
    document.body.appendChild(button);

    // Click on the input to show calendar
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    fireEvent.click(inputElement);

    // Verify calendar is visible
    expect(screen.getByRole('dialog', { hidden: false })).toBeInTheDocument();

    // Click on the separate button outside DatePicker
    fireEvent.click(button);

    // Verify calendar is closed
    await waitFor(() => {
      expect(screen.getByRole('dialog', { hidden: true })).toBeInTheDocument();
    });

    // Clean up the button
    document.body.removeChild(button);
  });

  it('should handle disabled state', () => {
    // Render DatePicker with disabled=true
    const { container } = setup({ disabled: true });

    // Verify input has disabled attribute
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    expect(inputElement).toHaveAttribute('disabled');

    // Try to click on the input
    fireEvent.click(inputElement);

    // Verify calendar does not open
    expect(screen.queryByRole('dialog')).toBeNull();

    // Try to type in the input
    fireEvent.change(inputElement, { target: { value: 'test' } });

    // Verify input value does not change
    expect(inputElement.value).toBe('');
  });

  it('should show error state', () => {
    // Render DatePicker with error prop
    const { container, getByText } = setup({ error: 'Invalid date' });

    // Verify error message is displayed
    expect(getByText('Invalid date')).toBeVisible();

    // Verify input has appropriate error styling
    const inputContainer = container.querySelector('.date-picker__input-container') as HTMLDivElement;
    expect(inputContainer).toHaveClass('date-picker--error');
  });

  it('should handle required attribute', () => {
    // Render DatePicker with required=true
    const { container } = setup({ required: true });

    // Verify input has required attribute
    const inputElement = container.querySelector('.date-picker__input') as HTMLInputElement;
    expect(inputElement).toHaveAttribute('aria-required', 'true');

    // Verify appropriate aria attributes for accessibility
    const labelElement = container.querySelector('.date-picker__label') as HTMLLabelElement;
    expect(labelElement).toHaveTextContent('*');
  });

  it('should apply custom class names', () => {
    // Render DatePicker with custom className
    const { container } = setup({ className: 'custom-class' });

    // Verify component container has the custom class applied
    const datePickerContainer = container.querySelector('.date-picker') as HTMLDivElement;
    expect(datePickerContainer).toHaveClass('custom-class');
  });
});