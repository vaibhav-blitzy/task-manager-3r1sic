import React from 'react';
import classNames from 'classnames'; // v2.3.2
import { IconType } from 'react-icons'; // v4.10.0

export interface IconProps {
  /** The icon component to render */
  icon: IconType;
  /** Size of the icon (in pixels if number, or CSS value if string) */
  size?: number | string;
  /** Color of the icon */
  color?: string;
  /** Additional CSS class names */
  className?: string;
  /** Accessibility label for screen readers */
  ariaLabel?: string;
  /** Tooltip text shown on hover */
  title?: string;
  /** Click handler function */
  onClick?(): void;
}

/**
 * Icon component for displaying various icons with customization options.
 * This component provides a standardized way to render icons across the
 * application with consistent styling and proper accessibility attributes.
 */
export const Icon: React.FC<IconProps> = ({
  icon: IconComponent,
  size,
  color,
  className,
  ariaLabel,
  title,
  onClick,
}) => {
  const iconClassName = classNames('icon', className);

  return (
    <IconComponent
      className={iconClassName}
      size={size}
      color={color}
      aria-label={ariaLabel}
      title={title}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-hidden={!ariaLabel}
    />
  );
};

export default Icon;