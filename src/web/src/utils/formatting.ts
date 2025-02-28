/**
 * formatting.ts
 * 
 * Utility functions for formatting various types of data for display in the UI,
 * including dates, statuses, priorities, file sizes, and text truncation.
 */

import { format, isValid } from 'date-fns';
import { TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from '../config/constants';

/**
 * Formats a date to a readable string based on specified format
 * @param date - The date to format
 * @param formatString - The format string to use
 * @returns Formatted date string or fallback value if date is invalid
 */
export function formatDate(
  date: Date | string | number | null,
  formatString: string
): string {
  if (date == null) {
    return '';
  }

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
    if (!isValid(dateObj)) {
      return '';
    }
    return format(dateObj, formatString);
  } catch (error) {
    console.error('Error formatting date:', error);
    return '';
  }
}

/**
 * Formats a date and time to a readable string
 * @param date - The date to format
 * @returns Formatted date and time string
 */
export function formatDateTime(date: Date | string | number | null): string {
  return formatDate(date, 'MMM d, yyyy h:mm a');
}

/**
 * Formats a time value to a readable string
 * @param time - The time to format
 * @returns Formatted time string
 */
export function formatTime(time: Date | string | number | null): string {
  return formatDate(time, 'h:mm a');
}

/**
 * Formats a task status to a user-friendly display string
 * @param status - The status to format
 * @returns Formatted status string
 */
export function formatStatus(status: string): string {
  if (!status) {
    return '';
  }

  // Check if status is in the predefined labels
  if (TASK_STATUS_LABELS[status]) {
    return TASK_STATUS_LABELS[status];
  }

  // Handle snake_case and kebab-case
  const formattedStatus = status
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');

  return formattedStatus;
}

/**
 * Formats a priority level to a user-friendly display string with optional emoji
 * @param priority - The priority level to format
 * @param includeEmoji - Whether to include emoji in the output
 * @returns Formatted priority string
 */
export function formatPriority(priority: string, includeEmoji: boolean = false): string {
  if (!priority) {
    return '';
  }

  // Check if priority is in the predefined labels
  const label = TASK_PRIORITY_LABELS[priority] || priority;

  if (!includeEmoji) {
    return label;
  }

  // Add emoji based on priority
  switch (priority.toLowerCase()) {
    case 'low':
      return `🟢 ${label}`;
    case 'medium':
      return `🔵 ${label}`;
    case 'high':
      return `🟠 ${label}`;
    case 'urgent':
      return `🔴 ${label}`;
    default:
      return label;
  }
}

/**
 * Formats a file size in bytes to a human-readable string with appropriate units
 * @param bytes - The file size in bytes
 * @returns Formatted file size string with units
 */
export function formatFileSize(bytes: number): string {
  if (typeof bytes !== 'number' || isNaN(bytes) || bytes < 0) {
    return '0 B';
  }

  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  
  // Don't go beyond the available units
  const unitIndex = Math.min(i, units.length - 1);
  
  // Convert to the appropriate unit
  const value = bytes / Math.pow(1024, unitIndex);
  
  // Format with appropriate decimal places based on unit
  let decimalPlaces = 0;
  if (unitIndex > 0) {
    decimalPlaces = unitIndex > 2 ? 2 : 1;
  }
  
  return `${value.toFixed(decimalPlaces)} ${units[unitIndex]}`;
}

/**
 * Formats a user's name for display, with options for different formats
 * @param user - User object with first and last name
 * @param format - Format option: 'full' (default), 'firstLast', 'firstInitial', 'lastInitial', 'initials'
 * @returns Formatted user name
 */
export function formatUserName(
  user: { firstName?: string; lastName?: string; email?: string; id?: string },
  format: 'full' | 'firstLast' | 'firstInitial' | 'lastInitial' | 'initials' = 'full'
): string {
  if (!user) {
    return '';
  }

  const firstName = user.firstName || '';
  const lastName = user.lastName || '';
  
  // Fallback to email or id if no name is available
  if (!firstName && !lastName) {
    return user.email || user.id || '';
  }

  switch (format) {
    case 'firstLast':
      return `${firstName} ${lastName}`.trim();
    
    case 'firstInitial':
      if (!firstName) return lastName;
      return `${firstName.charAt(0)}. ${lastName}`.trim();
    
    case 'lastInitial':
      if (!lastName) return firstName;
      return `${firstName} ${lastName.charAt(0)}.`.trim();
    
    case 'initials':
      const firstInitial = firstName ? firstName.charAt(0).toUpperCase() : '';
      const lastInitial = lastName ? lastName.charAt(0).toUpperCase() : '';
      return `${firstInitial}${lastInitial}`.trim();
    
    case 'full':
    default:
      if (!lastName) return firstName;
      if (!firstName) return lastName;
      return `${firstName} ${lastName}`;
  }
}

/**
 * Truncates text to a specified length and adds ellipsis if truncated
 * @param text - The text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text string
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text || typeof text !== 'string') {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Formats a number with thousand separators and specified decimal places
 * @param value - The number to format
 * @param decimalPlaces - Number of decimal places (default: 0)
 * @returns Formatted number string
 */
export function formatNumber(value: number, decimalPlaces: number = 0): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0';
  }

  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces
  });
}

/**
 * Formats a number as a percentage with specified decimal places
 * @param value - The number to format (0.5 = 50%)
 * @param decimalPlaces - Number of decimal places (default: 0)
 * @returns Formatted percentage string
 */
export function formatPercentage(value: number, decimalPlaces: number = 0): string {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0%';
  }

  // If value is a decimal between 0 and 1, multiply by 100
  let percentValue = value;
  if (value >= 0 && value <= 1) {
    percentValue = value * 100;
  }

  return `${percentValue.toFixed(decimalPlaces)}%`;
}

/**
 * Formats a duration in seconds or minutes to a readable time string
 * @param value - The duration value
 * @param unit - The unit of the duration ('seconds' or 'minutes')
 * @returns Formatted duration string
 */
export function formatDuration(value: number, unit: 'seconds' | 'minutes' = 'seconds'): string {
  if (typeof value !== 'number' || isNaN(value) || value < 0) {
    return '0s';
  }

  // Convert to seconds if input is in minutes
  const totalSeconds = unit === 'minutes' ? value * 60 : value;
  
  // Calculate hours, minutes, seconds
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  
  // Format the duration
  const parts: string[] = [];
  
  if (hours > 0) {
    parts.push(`${hours}h`);
  }
  
  if (minutes > 0 || (hours > 0 && seconds > 0)) {
    parts.push(`${minutes}m`);
  }
  
  if (seconds > 0 || parts.length === 0) {
    parts.push(`${seconds}s`);
  }
  
  return parts.join(' ');
}