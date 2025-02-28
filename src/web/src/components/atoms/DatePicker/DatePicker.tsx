import React, { useState, useRef, useEffect } from 'react';
import classNames from 'classnames';
import {
  format,
  addMonths,
  subMonths,
  isAfter,
  isBefore,
  isValid,
  isSameMonth,
  isSameDay,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  getDay,
} from 'date-fns'; // v2.30.0
import useOutsideClick from '../../../hooks/useOutsideClick';
import { formatDate, parseDate, isValidDate } from '../../../utils/date';

/**
 * Generates a matrix of dates representing a calendar month view
 * @param currentMonth The month to generate calendar for
 * @returns Two-dimensional array of dates representing weeks and days
 */
function generateCalendar(currentMonth: Date): Date[][] {
  const firstDayOfMonth = startOfMonth(currentMonth);
  const lastDayOfMonth = endOfMonth(currentMonth);
  const startDate = startOfWeek(firstDayOfMonth);
  const endDate = endOfWeek(lastDayOfMonth);

  const calendar: Date[][] = [];
  let week: Date[] = [];
  let day = startDate;

  while (day <= endDate) {
    week.push(day);
    if (week.length === 7) {
      calendar.push(week);
      week = [];
    }
    day = addDays(day, 1);
  }

  return calendar;
}

/**
 * Determines if a date should be enabled for selection based on min and max date constraints
 * @param date The date to check
 * @param minDate The minimum selectable date
 * @param maxDate The maximum selectable date
 * @returns Whether the date is selectable
 */
function isDateEnabled(date: Date, minDate?: Date, maxDate?: Date): boolean {
  if (minDate && isBefore(date, minDate)) {
    return false;
  }
  if (maxDate && isAfter(date, maxDate)) {
    return false;
  }
  return true;
}

/**
 * Props interface for the DatePicker component
 */
interface DatePickerProps {
  /** The selected date value */
  value: Date | string | null;
  /** Callback when date changes */
  onChange: (date: Date | null) => void;
  /** Optional label for the date input */
  label?: string;
  /** Placeholder text when no date is selected */
  placeholder?: string;
  /** Minimum selectable date */
  minDate?: Date;
  /** Maximum selectable date */
  maxDate?: Date;
  /** Whether the date picker is disabled */
  disabled?: boolean;
  /** Additional CSS class names */
  className?: string;
  /** ID attribute for the input element */
  id?: string;
  /** Name attribute for the input element */
  name?: string;
  /** Error message to display */
  error?: string;
  /** Whether the field is required */
  required?: boolean;
  /** ARIA attributes for accessibility */
  aria?: React.AriaAttributes;
}

/**
 * A reusable date picker component that displays an input field and calendar dropdown.
 * Allows users to select dates either by typing or clicking.
 */
const DatePicker: React.FC<DatePickerProps> = ({
  value,
  onChange,
  label,
  placeholder = 'Select date',
  minDate,
  maxDate,
  disabled = false,
  className = '',
  id,
  name,
  error,
  required = false,
  aria,
}) => {
  // State for tracking if calendar is open
  const [isOpen, setIsOpen] = useState(false);
  
  // State for tracking current month displayed in calendar
  const [currentMonth, setCurrentMonth] = useState(value && isValidDate(value) 
    ? typeof value === 'string' ? parseDate(value) || new Date() : value 
    : new Date());
  
  // State for tracking input field value
  const [inputValue, setInputValue] = useState(value ? formatDate(value) : '');
  
  // Reference to date picker container for detecting outside clicks
  const datePickerRef = useRef<HTMLDivElement>(null);
  
  // Use the useOutsideClick hook to close the calendar when clicking outside
  useOutsideClick(datePickerRef, () => {
    if (isOpen) {
      setIsOpen(false);
    }
  });

  // Update input value when value prop changes
  useEffect(() => {
    setInputValue(value ? formatDate(value) : '');
  }, [value]);

  /**
   * Toggles the visibility of the calendar dropdown
   */
  const handleToggleCalendar = () => {
    if (disabled) return;
    setIsOpen(!isOpen);
  };

  /**
   * Handles the selection of a date from the calendar
   * @param date The selected date
   */
  const handleDateSelect = (date: Date) => {
    onChange(date);
    setInputValue(formatDate(date));
    setIsOpen(false);
  };

  /**
   * Handles changes to the input field text
   * @param e Change event from input
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    
    // If input is cleared, set value to null
    if (!newValue) {
      onChange(null);
    }
  };

  /**
   * Validates and processes the input value when the field loses focus
   */
  const handleInputBlur = () => {
    if (!inputValue) {
      onChange(null);
      return;
    }
    
    const parsedDate = parseDate(inputValue);
    if (parsedDate && isValid(parsedDate)) {
      // Check if date is within allowed range
      if (isDateEnabled(parsedDate, minDate, maxDate)) {
        onChange(parsedDate);
      } else {
        // If invalid, revert to previous value
        setInputValue(value ? formatDate(value) : '');
      }
    } else {
      // If parsing fails, revert to previous value
      setInputValue(value ? formatDate(value) : '');
    }
  };

  /**
   * Navigates to the previous month in the calendar
   */
  const handlePrevMonth = () => {
    setCurrentMonth(subMonths(currentMonth, 1));
  };

  /**
   * Navigates to the next month in the calendar
   */
  const handleNextMonth = () => {
    setCurrentMonth(addMonths(currentMonth, 1));
  };

  /**
   * Handles keyboard navigation for accessibility
   * @param e Keyboard event
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Close calendar on Escape key
    if (e.key === 'Escape') {
      setIsOpen(false);
      return;
    }
    
    // If calendar isn't open, open it on ArrowDown
    if (!isOpen && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      e.preventDefault();
      setIsOpen(true);
      return;
    }
    
    // Handle keyboard navigation in calendar
    if (isOpen) {
      // Implement keyboard navigation within the calendar
      if (e.key === 'Tab' && !e.shiftKey) {
        // Focus trap within calendar for tab navigation
        e.preventDefault();
        const calendarButtons = datePickerRef.current?.querySelectorAll('button');
        if (calendarButtons && calendarButtons.length > 0) {
          (calendarButtons[0] as HTMLButtonElement).focus();
        }
      }
    }
  };

  // Generate the calendar days
  const calendar = generateCalendar(currentMonth);

  // Format weekday names
  const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Get current selected date object
  const selectedDate = value ? 
    (typeof value === 'string' ? parseDate(value) : value) : 
    null;

  return (
    <div 
      className={classNames('date-picker', className, {
        'date-picker--disabled': disabled,
        'date-picker--error': !!error,
      })}
      ref={datePickerRef}
    >
      {label && (
        <label 
          htmlFor={id} 
          className="date-picker__label"
        >
          {label}
          {required && <span className="date-picker__required">*</span>}
        </label>
      )}
      
      <div className="date-picker__input-container">
        <input
          id={id}
          name={name}
          type="text"
          className="date-picker__input"
          placeholder={placeholder}
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onClick={handleToggleCalendar}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          aria-invalid={!!error}
          aria-required={required}
          aria-haspopup="dialog"
          aria-expanded={isOpen}
          {...aria}
        />
        
        <button
          type="button"
          className="date-picker__toggle"
          onClick={handleToggleCalendar}
          disabled={disabled}
          aria-label="Toggle date picker"
          tabIndex={-1}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 20 20" 
            fill="currentColor" 
            className="date-picker__icon"
            aria-hidden="true"
          >
            <path 
              fillRule="evenodd" 
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" 
              clipRule="evenodd" 
            />
          </svg>
        </button>
      </div>
      
      {error && (
        <div className="date-picker__error-message" aria-live="polite">{error}</div>
      )}
      
      {isOpen && (
        <div 
          className="date-picker__calendar"
          role="dialog"
          aria-label="Date picker calendar"
        >
          <div className="date-picker__calendar-header">
            <button
              type="button"
              className="date-picker__calendar-nav"
              onClick={handlePrevMonth}
              aria-label="Previous month"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 20 20" 
                fill="currentColor" 
                className="date-picker__icon"
                aria-hidden="true"
              >
                <path 
                  fillRule="evenodd" 
                  d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" 
                  clipRule="evenodd" 
                />
              </svg>
            </button>
            
            <div className="date-picker__calendar-title" aria-live="polite">
              {format(currentMonth, 'MMMM yyyy')}
            </div>
            
            <button
              type="button"
              className="date-picker__calendar-nav"
              onClick={handleNextMonth}
              aria-label="Next month"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 20 20" 
                fill="currentColor" 
                className="date-picker__icon"
                aria-hidden="true"
              >
                <path 
                  fillRule="evenodd" 
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" 
                  clipRule="evenodd" 
                />
              </svg>
            </button>
          </div>
          
          <div className="date-picker__calendar-weekdays" role="row">
            {weekdays.map((weekday) => (
              <div 
                key={weekday} 
                className="date-picker__calendar-weekday"
                role="columnheader"
                aria-label={weekday}
              >
                {weekday}
              </div>
            ))}
          </div>
          
          <div className="date-picker__calendar-grid" role="grid">
            {calendar.map((week, weekIndex) => (
              <div 
                key={`week-${weekIndex}`} 
                className="date-picker__calendar-week"
                role="row"
              >
                {week.map((day) => {
                  const isCurrentMonth = isSameMonth(day, currentMonth);
                  const isToday = isSameDay(day, new Date());
                  const isSelected = selectedDate ? isSameDay(day, selectedDate) : false;
                  const isEnabled = isDateEnabled(day, minDate, maxDate);
                  
                  return (
                    <button
                      key={day.toISOString()}
                      type="button"
                      className={classNames('date-picker__calendar-day', {
                        'date-picker__calendar-day--current-month': isCurrentMonth,
                        'date-picker__calendar-day--other-month': !isCurrentMonth,
                        'date-picker__calendar-day--today': isToday,
                        'date-picker__calendar-day--selected': isSelected,
                        'date-picker__calendar-day--disabled': !isEnabled || !isCurrentMonth,
                      })}
                      onClick={() => isEnabled && isCurrentMonth && handleDateSelect(day)}
                      disabled={!isEnabled || !isCurrentMonth}
                      aria-label={format(day, 'MMMM d, yyyy')}
                      aria-current={isToday ? 'date' : undefined}
                      aria-selected={isSelected}
                      role="gridcell"
                    >
                      {format(day, 'd')}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
          
          <div className="date-picker__calendar-footer">
            <button
              type="button"
              className="date-picker__calendar-button"
              onClick={() => handleDateSelect(new Date())}
              aria-label="Select today"
            >
              Today
            </button>
            <button
              type="button"
              className="date-picker__calendar-button"
              onClick={() => {
                setInputValue('');
                onChange(null);
                setIsOpen(false);
              }}
              aria-label="Clear selection"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatePicker;