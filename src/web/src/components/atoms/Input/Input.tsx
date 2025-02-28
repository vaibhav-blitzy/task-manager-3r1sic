import React, { useState } from 'react';
import classNames from 'classnames'; // v2.3.2

interface InputProps {
  id?: string;
  name?: string;
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'tel' | 'url';
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  error?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  maxLength?: number;
  ariaLabel?: string;
}

const Input: React.FC<InputProps> = ({
  id,
  name,
  type = 'text',
  placeholder,
  value,
  defaultValue,
  onChange,
  onBlur,
  onFocus,
  disabled = false,
  readOnly = false,
  required = false,
  error,
  className = '',
  size = 'md',
  maxLength,
  ariaLabel,
}) => {
  // Track focus state for styling
  const [isFocused, setIsFocused] = useState(false);

  // Define handlers for input events
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) onChange(e);
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    if (onFocus) onFocus(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    if (onBlur) onBlur(e);
  };

  // Compose CSS classes based on component state
  const inputClasses = classNames(
    // Base styles
    'w-full border rounded outline-none transition-colors',
    
    // Apply design system typography (Inter font, 14px size, 400 weight as per section 7.2.1)
    'font-sans',
    
    // Size variations
    {
      'px-2 py-1 text-xs': size === 'sm',
      'px-3 py-2 text-sm': size === 'md', // 14px as per design system
      'px-4 py-3 text-base': size === 'lg',
    },
    
    // Apply design system colors (border: Neutral-200, text: Neutral-700, focus: Primary)
    {
      'border-neutral-200 hover:border-neutral-300 text-neutral-700': !error && !isFocused && !disabled,
      'border-primary ring-1 ring-primary ring-opacity-30 text-neutral-700': isFocused && !error && !disabled,
      'border-error text-neutral-700': !!error && !disabled,
      'bg-neutral-100 text-neutral-400 cursor-not-allowed': disabled,
    },
    
    // Custom class
    className
  );

  // Render input element with appropriate attributes and event handlers
  return (
    <div className="input-wrapper">
      <input
        id={id}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        defaultValue={defaultValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        disabled={disabled}
        readOnly={readOnly}
        required={required}
        maxLength={maxLength}
        aria-label={ariaLabel || name}
        aria-invalid={!!error}
        aria-required={required}
        className={inputClasses}
      />
      
      {/* Conditionally render error message with error styling */}
      {error && (
        <p className="mt-1 text-sm text-error" id={`${id || name}-error`}>
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;