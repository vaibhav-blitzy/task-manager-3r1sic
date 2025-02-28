import {
  format, parse, isValid, parseISO, isBefore, isAfter, differenceInDays,
  differenceInHours, addDays, isToday, isSameDay, startOfDay, endOfDay,
  startOfWeek, endOfWeek, startOfMonth, endOfMonth
} from 'date-fns';
import {
  DATE_FORMAT, TIME_FORMAT, DATETIME_FORMAT, API_DATE_FORMAT
} from '../config/constants';

/**
 * Formats a date object or string into a human-readable date string
 * @param date - The date to format
 * @param formatString - The format string to use (defaults to DATE_FORMAT)
 * @returns Formatted date string or empty string if date is invalid
 */
export function formatDate(
  date: Date | string | null | undefined,
  formatString: string = DATE_FORMAT
): string {
  if (date == null) {
    return '';
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
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
 * Formats a date object or string into a human-readable time string
 * @param date - The date to format
 * @returns Formatted time string or empty string if date is invalid
 */
export function formatTime(date: Date | string | null | undefined): string {
  if (date == null) {
    return '';
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return '';
    }
    return format(dateObj, TIME_FORMAT);
  } catch (error) {
    console.error('Error formatting time:', error);
    return '';
  }
}

/**
 * Formats a date object or string into a human-readable date and time string
 * @param date - The date to format
 * @returns Formatted date and time string or empty string if date is invalid
 */
export function formatDateTime(date: Date | string | null | undefined): string {
  if (date == null) {
    return '';
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return '';
    }
    return format(dateObj, DATETIME_FORMAT);
  } catch (error) {
    console.error('Error formatting date and time:', error);
    return '';
  }
}

/**
 * Parses a date string into a Date object using the specified format
 * @param dateString - The date string to parse
 * @param formatString - The format string to use (defaults to DATE_FORMAT)
 * @returns Parsed Date object or null if parsing fails
 */
export function parseDate(
  dateString: string | null | undefined,
  formatString: string = DATE_FORMAT
): Date | null {
  if (!dateString) {
    return null;
  }

  try {
    const parsedDate = parse(dateString, formatString, new Date());
    return isValid(parsedDate) ? parsedDate : null;
  } catch (error) {
    console.error('Error parsing date:', error);
    return null;
  }
}

/**
 * Formats a date object or string into ISO format for API requests
 * @param date - The date to format
 * @returns Date in ISO format or null if date is invalid
 */
export function formatDateToISO(date: Date | string | null | undefined): string | null {
  if (date == null) {
    return null;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return null;
    }
    return dateObj.toISOString();
  } catch (error) {
    console.error('Error formatting date to ISO:', error);
    return null;
  }
}

/**
 * Checks if a value is a valid date
 * @param date - The value to check
 * @returns True if date is valid, false otherwise
 */
export function isValidDate(date: any): boolean {
  if (date == null) {
    return false;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isValid(dateObj);
  } catch (error) {
    return false;
  }
}

/**
 * Checks if a date is in the past (overdue)
 * @param date - The date to check
 * @returns True if date is in the past, false otherwise
 */
export function isOverdue(date: Date | string | null | undefined): boolean {
  if (date == null) {
    return false;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return false;
    }
    return isBefore(dateObj, startOfDay(new Date()));
  } catch (error) {
    return false;
  }
}

/**
 * Checks if a date is approaching soon (within specified days)
 * @param date - The date to check
 * @param days - The number of days to check against (defaults to 3)
 * @returns True if date is within the specified days, false otherwise
 */
export function isDueSoon(
  date: Date | string | null | undefined,
  days: number = 3
): boolean {
  if (date == null) {
    return false;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return false;
    }

    const today = startOfDay(new Date());
    if (isBefore(dateObj, today)) {
      return false; // Already overdue
    }

    const daysUntil = differenceInDays(dateObj, today);
    return daysUntil <= days;
  } catch (error) {
    return false;
  }
}

/**
 * Returns a human-readable relative date label (Today, Tomorrow, Yesterday, or formatted date)
 * @param date - The date to get the label for
 * @returns Relative date label or empty string if date is invalid
 */
export function getRelativeDateLabel(date: Date | string | null | undefined): string {
  if (date == null) {
    return '';
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return '';
    }

    const today = new Date();

    if (isToday(dateObj)) {
      return 'Today';
    }

    const tomorrow = addDays(today, 1);
    if (isSameDay(dateObj, tomorrow)) {
      return 'Tomorrow';
    }

    const yesterday = addDays(today, -1);
    if (isSameDay(dateObj, yesterday)) {
      return 'Yesterday';
    }

    return formatDate(dateObj);
  } catch (error) {
    return '';
  }
}

/**
 * Calculates the number of days between today and a future date
 * @param date - The future date
 * @returns Number of days until the date or -1 if date is invalid or in the past
 */
export function getDaysUntil(date: Date | string | null | undefined): number {
  if (date == null) {
    return -1;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return -1;
    }

    const today = startOfDay(new Date());
    if (isBefore(dateObj, today)) {
      return -1; // Date is in the past
    }

    return differenceInDays(dateObj, today);
  } catch (error) {
    return -1;
  }
}

/**
 * Calculates the number of days a date is overdue
 * @param date - The date to check
 * @returns Number of days overdue or 0 if date is invalid or not overdue
 */
export function getDaysOverdue(date: Date | string | null | undefined): number {
  if (date == null) {
    return 0;
  }

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) {
      return 0;
    }

    const today = startOfDay(new Date());
    if (!isBefore(dateObj, today)) {
      return 0; // Not overdue
    }

    return Math.abs(differenceInDays(dateObj, today));
  } catch (error) {
    return 0;
  }
}

/**
 * Returns start and end dates for a specified period (day, week, month, etc.)
 * @param period - The period type ('day', 'week', 'month', 'quarter', 'year')
 * @param baseDate - The base date to calculate the range from (defaults to today)
 * @returns Date range object with start and end dates
 */
export function getDateRangeForPeriod(
  period: string,
  baseDate: Date = new Date()
): { startDate: Date; endDate: Date } {
  const date = isValid(baseDate) ? baseDate : new Date();

  switch (period.toLowerCase()) {
    case 'day':
      return {
        startDate: startOfDay(date),
        endDate: endOfDay(date),
      };
    
    case 'week':
      return {
        startDate: startOfWeek(date, { weekStartsOn: 1 }), // Monday as start of week
        endDate: endOfWeek(date, { weekStartsOn: 1 }),
      };
    
    case 'month':
      return {
        startDate: startOfMonth(date),
        endDate: endOfMonth(date),
      };
    
    case 'quarter': {
      const currentMonth = date.getMonth();
      const quarterStartMonth = Math.floor(currentMonth / 3) * 3;
      const quarterStart = new Date(date.getFullYear(), quarterStartMonth, 1);
      const quarterEnd = new Date(date.getFullYear(), quarterStartMonth + 3, 0);
      
      return {
        startDate: startOfDay(quarterStart),
        endDate: endOfDay(quarterEnd),
      };
    }
    
    case 'year': {
      const yearStart = new Date(date.getFullYear(), 0, 1);
      const yearEnd = new Date(date.getFullYear(), 11, 31);
      
      return {
        startDate: startOfDay(yearStart),
        endDate: endOfDay(yearEnd),
      };
    }
    
    default:
      return {
        startDate: startOfDay(date),
        endDate: endOfDay(date),
      };
  }
}

/**
 * Compares two dates for ascending sort order
 * @param dateA - The first date
 * @param dateB - The second date
 * @returns Comparison result (-1, 0, or 1)
 */
export function compareAscending(
  dateA: Date | string | null | undefined,
  dateB: Date | string | null | undefined
): number {
  // Handle null cases (null values come after non-null values)
  if (dateA == null && dateB == null) {
    return 0;
  }
  if (dateA == null) {
    return 1;
  }
  if (dateB == null) {
    return -1;
  }

  try {
    const parsedDateA = typeof dateA === 'string' ? parseISO(dateA) : dateA;
    const parsedDateB = typeof dateB === 'string' ? parseISO(dateB) : dateB;

    if (!isValid(parsedDateA) && !isValid(parsedDateB)) {
      return 0;
    }
    if (!isValid(parsedDateA)) {
      return 1;
    }
    if (!isValid(parsedDateB)) {
      return -1;
    }

    if (parsedDateA < parsedDateB) {
      return -1;
    }
    if (parsedDateA > parsedDateB) {
      return 1;
    }
    return 0;
  } catch (error) {
    console.error('Error comparing dates:', error);
    return 0;
  }
}

/**
 * Compares two dates for descending sort order
 * @param dateA - The first date
 * @param dateB - The second date
 * @returns Comparison result (-1, 0, or 1)
 */
export function compareDescending(
  dateA: Date | string | null | undefined,
  dateB: Date | string | null | undefined
): number {
  return -compareAscending(dateA, dateB);
}