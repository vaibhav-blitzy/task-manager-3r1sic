import React from 'react'; // ^18.2.0
import classNames from 'classnames'; // ^2.3.2

export interface LabelProps {
  /**
   * The ID of the input element this label is associated with
   */
  htmlFor?: string;
  /**
   * The content of the label
   */
  children: React.ReactNode;
  /**
   * Additional CSS classes to apply to the label
   */
  className?: string;
  /**
   * Whether the associated field is required
   */
  required?: boolean;
  /**
   * Whether the label should appear disabled
   */
  disabled?: boolean;
  /**
   * Whether the label should appear in an error state
   */
  error?: boolean;
}

/**
 * Label component used for form fields and other UI elements requiring text labels.
 * Implements design system styling and accessibility features.
 */
const Label: React.FC<LabelProps> = ({
  htmlFor,
  children,
  className,
  required = false,
  disabled = false,
  error = false,
}) => {
  // Combine class names based on component states
  const labelClasses = classNames(
    'text-xs font-medium', // Base typography from design system
    {
      'text-red-500': error, // Error state
      'text-gray-400': disabled && !error, // Disabled state (error takes precedence)
      'text-gray-700': !disabled && !error, // Default text color
    },
    className // Custom classes passed as props
  );

  return (
    <label 
      htmlFor={htmlFor} 
      className={labelClasses}
      aria-disabled={disabled}
    >
      {children}
      {required && <span className="ml-1 text-red-500" aria-hidden="true">*</span>}
    </label>
  );
};

export default Label;