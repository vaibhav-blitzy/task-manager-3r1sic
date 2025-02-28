/**
 * Utility functions for validating user inputs, form data, and object properties
 * in the Task Management System frontend
 */

/**
 * Validates if a string is a properly formatted email address
 *
 * @param email - The email string to validate
 * @returns True if the email format is valid, false otherwise
 */
export const isEmailValid = (email: string): boolean => {
  if (!email) return false;
  
  // Regular expression for validating email format
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email);
};

/**
 * Validates if a password meets the required security criteria
 * 
 * @param password - The password string to validate
 * @returns True if the password meets all security requirements, false otherwise
 */
export const isPasswordValid = (password: string): boolean => {
  if (!password || password.length < 8) return false;
  
  // Check for at least one uppercase letter
  const hasUppercase = /[A-Z]/.test(password);
  
  // Check for at least one lowercase letter
  const hasLowercase = /[a-z]/.test(password);
  
  // Check for at least one number
  const hasNumber = /[0-9]/.test(password);
  
  // Check for at least one special character
  const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  
  return hasUppercase && hasLowercase && hasNumber && hasSpecialChar;
};

/**
 * Checks if a value is present and not empty
 * 
 * @param value - The value to check
 * @returns True if the value exists and is not empty, false otherwise
 */
export const isRequired = (value: any): boolean => {
  if (value === null || value === undefined) {
    return false;
  }
  
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  
  if (typeof value === 'object') {
    return Object.keys(value).length > 0;
  }
  
  return true;
};

/**
 * Validates if a date string is in a valid format and represents a valid date
 * 
 * @param dateStr - The date string to validate
 * @returns True if the date is valid, false otherwise
 */
export const isDateValid = (dateStr: string): boolean => {
  if (!dateStr) return false;
  
  const date = new Date(dateStr);
  
  // Check if the date is valid (not Invalid Date)
  return !isNaN(date.getTime());
};

/**
 * Checks if a date is in the future
 * 
 * @param date - The date to check, either as a Date object or a string
 * @returns True if the date is in the future, false otherwise
 */
export const isDateInFuture = (date: Date | string): boolean => {
  // Convert to Date object if it's a string
  const dateToCheck = typeof date === 'string' ? new Date(date) : date;
  
  // Check if the converted date is valid
  if (isNaN(dateToCheck.getTime())) {
    return false;
  }
  
  const now = new Date();
  return dateToCheck > now;
};

/**
 * Checks if a string has at least the minimum required length
 * 
 * @param value - The string to check
 * @param min - The minimum required length
 * @returns True if the string length is equal to or greater than the minimum, false otherwise
 */
export const minLength = (value: string, min: number): boolean => {
  if (typeof value !== 'string') {
    return false;
  }
  
  return value.length >= min;
};

/**
 * Checks if a string does not exceed the maximum allowed length
 * 
 * @param value - The string to check
 * @param max - The maximum allowed length
 * @returns True if the string length is equal to or less than the maximum, false otherwise
 */
export const maxLength = (value: string, max: number): boolean => {
  if (typeof value !== 'string') {
    return false;
  }
  
  return value.length <= max;
};

/**
 * Checks if a number is within a specific range
 * 
 * @param value - The number to check
 * @param min - The minimum allowed value
 * @param max - The maximum allowed value
 * @returns True if the number is within the range (inclusive), false otherwise
 */
export const isNumberInRange = (value: number, min: number, max: number): boolean => {
  if (typeof value !== 'number' || isNaN(value)) {
    return false;
  }
  
  return value >= min && value <= max;
};

/**
 * Validates if a status value is one of the allowed task statuses
 * 
 * @param status - The status string to validate
 * @returns True if the status is valid, false otherwise
 */
export const isValidTaskStatus = (status: string): boolean => {
  const validStatuses = ['created', 'assigned', 'in-progress', 'on-hold', 'in-review', 'completed', 'cancelled'];
  return validStatuses.includes(status);
};

/**
 * Validates if a priority value is one of the allowed priority levels
 * 
 * @param priority - The priority string to validate
 * @returns True if the priority is valid, false otherwise
 */
export const isValidPriority = (priority: string): boolean => {
  const validPriorities = ['low', 'medium', 'high', 'urgent'];
  return validPriorities.includes(priority);
};

/**
 * Type definition for task input validation
 */
interface TaskInput {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  dueDate?: string;
  assigneeId?: string;
  projectId?: string;
}

/**
 * Type definition for validation result
 */
interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

/**
 * Validates the task creation/update input object
 * 
 * @param taskInput - The task input object to validate
 * @returns Object containing validation result and any error messages
 */
export const validateTaskInput = (taskInput: TaskInput): ValidationResult => {
  const result: ValidationResult = {
    isValid: true,
    errors: {}
  };
  
  // Validate title
  if (!isRequired(taskInput.title)) {
    result.errors.title = 'Task title is required';
  }
  
  // Validate dueDate if provided
  if (taskInput.dueDate) {
    if (!isDateValid(taskInput.dueDate)) {
      result.errors.dueDate = 'Due date is not a valid date';
    } else if (!isDateInFuture(taskInput.dueDate)) {
      result.errors.dueDate = 'Due date must be in the future';
    }
  }
  
  // Validate priority if provided
  if (taskInput.priority && !isValidPriority(taskInput.priority)) {
    result.errors.priority = 'Invalid priority level';
  }
  
  // Validate status if provided
  if (taskInput.status && !isValidTaskStatus(taskInput.status)) {
    result.errors.status = 'Invalid task status';
  }
  
  // Set isValid to false if any errors exist
  if (Object.keys(result.errors).length > 0) {
    result.isValid = false;
  }
  
  return result;
};

/**
 * Type definition for project input validation
 */
interface ProjectInput {
  name?: string;
  description?: string;
  status?: string;
  category?: string;
}

/**
 * Validates the project creation/update input object
 * 
 * @param projectInput - The project input object to validate
 * @returns Object containing validation result and any error messages
 */
export const validateProjectInput = (projectInput: ProjectInput): ValidationResult => {
  const result: ValidationResult = {
    isValid: true,
    errors: {}
  };
  
  // Validate name
  if (!isRequired(projectInput.name)) {
    result.errors.name = 'Project name is required';
  }
  
  // Validate status if provided
  if (projectInput.status) {
    const validProjectStatuses = ['planning', 'active', 'on-hold', 'completed', 'archived', 'cancelled'];
    if (!validProjectStatuses.includes(projectInput.status)) {
      result.errors.status = 'Invalid project status';
    }
  }
  
  // Set isValid to false if any errors exist
  if (Object.keys(result.errors).length > 0) {
    result.isValid = false;
  }
  
  return result;
};

/**
 * Type definition for login input validation
 */
interface LoginInput {
  email?: string;
  password?: string;
}

/**
 * Validates the login form input
 * 
 * @param loginInput - The login input object to validate
 * @returns Object containing validation result and any error messages
 */
export const validateLoginInput = (loginInput: LoginInput): ValidationResult => {
  const result: ValidationResult = {
    isValid: true,
    errors: {}
  };
  
  // Validate email
  if (!isRequired(loginInput.email)) {
    result.errors.email = 'Email is required';
  } else if (!isEmailValid(loginInput.email!)) {
    result.errors.email = 'Email format is invalid';
  }
  
  // Validate password
  if (!isRequired(loginInput.password)) {
    result.errors.password = 'Password is required';
  }
  
  // Set isValid to false if any errors exist
  if (Object.keys(result.errors).length > 0) {
    result.isValid = false;
  }
  
  return result;
};

/**
 * Type definition for registration input validation
 */
interface RegistrationInput {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

/**
 * Validates the registration form input
 * 
 * @param registrationInput - The registration input object to validate
 * @returns Object containing validation result and any error messages
 */
export const validateRegistrationInput = (registrationInput: RegistrationInput): ValidationResult => {
  const result: ValidationResult = {
    isValid: true,
    errors: {}
  };
  
  // Validate firstName
  if (!isRequired(registrationInput.firstName)) {
    result.errors.firstName = 'First name is required';
  }
  
  // Validate lastName
  if (!isRequired(registrationInput.lastName)) {
    result.errors.lastName = 'Last name is required';
  }
  
  // Validate email
  if (!isRequired(registrationInput.email)) {
    result.errors.email = 'Email is required';
  } else if (!isEmailValid(registrationInput.email!)) {
    result.errors.email = 'Email format is invalid';
  }
  
  // Validate password
  if (!isRequired(registrationInput.password)) {
    result.errors.password = 'Password is required';
  } else if (!isPasswordValid(registrationInput.password!)) {
    result.errors.password = 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character';
  }
  
  // Validate confirmPassword
  if (registrationInput.password !== registrationInput.confirmPassword) {
    result.errors.confirmPassword = 'Passwords do not match';
  }
  
  // Set isValid to false if any errors exist
  if (Object.keys(result.errors).length > 0) {
    result.isValid = false;
  }
  
  return result;
};