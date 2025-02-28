import React from 'react';
import classNames from 'classnames'; // v2.3.2

export enum CheckboxSize {
  SMALL = 'sm',
  MEDIUM = 'md',
  LARGE = 'lg'
}

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  indeterminate?: boolean;
  size?: CheckboxSize;
  className?: string;
  labelClassName?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  checked,
  indeterminate = false,
  disabled = false,
  size = CheckboxSize.MEDIUM,
  className = '',
  labelClassName = '',
  id,
  onChange,
  ...rest
}) => {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const generatedId = React.useId();
  const checkboxId = id || `checkbox-${generatedId}`;

  // Set indeterminate property through DOM API since it's not controllable through React props
  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  // Generate CSS classes based on component state
  const containerClasses = classNames(
    'checkbox',
    `checkbox-${size}`,
    {
      'checkbox-checked': checked && !indeterminate,
      'checkbox-indeterminate': indeterminate,
      'checkbox-disabled': disabled,
      'checkbox-interactive': !disabled,
    },
    className
  );

  // Label classes vary based on size and disabled state
  const labelClasses = classNames(
    'checkbox-label',
    {
      [`checkbox-label-${size}`]: size,
      'checkbox-label-disabled': disabled,
    },
    labelClassName
  );

  return (
    <div className={containerClasses}>
      <div className="checkbox-control-container">
        <input
          ref={inputRef}
          type="checkbox"
          id={checkboxId}
          checked={checked}
          disabled={disabled}
          onChange={onChange}
          className="checkbox-input"
          aria-checked={indeterminate ? 'mixed' : checked}
          {...rest}
        />
        {/* 
          This empty span is used for custom styling with ::before and ::after
          pseudo-elements for checked and indeterminate states
        */}
        <span 
          className="checkbox-control" 
          aria-hidden="true"
        ></span>
      </div>
      
      {label && (
        <label 
          htmlFor={checkboxId} 
          className={labelClasses}
        >
          {label}
        </label>
      )}
    </div>
  );
};