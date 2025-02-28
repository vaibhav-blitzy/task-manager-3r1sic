import React from 'react'; // 18.2.x
import classNames from 'classnames'; // 2.3.x
import Label from '../../atoms/Label/Label';

interface FormFieldProps {
  id?: string;
  label: string;
  htmlFor: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  className?: string;
  disabled?: boolean;
  children: React.ReactNode;
}

/**
 * A reusable form field component that combines a label, form control, error message,
 * and helper text with consistent styling and accessibility features according to the design system.
 */
const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  htmlFor,
  required = false,
  error,
  helperText,
  className,
  disabled = false,
  children,
}) => {
  // Generate IDs for accessibility connections
  const errorId = error ? `${htmlFor}-error` : undefined;
  const helperId = helperText ? `${htmlFor}-helper` : undefined;
  
  // Build aria-describedby value from available IDs
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined;
  
  // Apply container classes
  const fieldContainerClasses = classNames(
    'mb-4', // Bottom margin for spacing between form fields
    className
  );

  // Clone children to add accessibility attributes while respecting existing props
  const childrenWithProps = React.isValidElement(children)
    ? React.cloneElement(children, {
        ...children.props,
        id: children.props.id || htmlFor,
        'aria-invalid': children.props['aria-invalid'] !== undefined 
          ? children.props['aria-invalid'] 
          : (error ? true : undefined),
        'aria-describedby': children.props['aria-describedby'] || describedBy,
        disabled: children.props.disabled !== undefined 
          ? children.props.disabled 
          : disabled,
      })
    : children;

  return (
    <div className={fieldContainerClasses}>
      <Label 
        htmlFor={htmlFor} 
        required={required} 
        disabled={disabled}
        error={!!error}
      >
        {label}
      </Label>
      
      <div className="mt-1">
        {childrenWithProps}
      </div>
      
      {error && (
        <p 
          id={errorId}
          className="mt-1 text-xs text-red-500" 
          aria-live="assertive"
        >
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p 
          id={helperId}
          className="mt-1 text-xs text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
};

export default FormField;