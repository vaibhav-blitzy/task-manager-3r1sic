/**
 * TypeScript type definitions for user-related entities including user profiles, roles,
 * organizations, permissions, and settings. Used throughout the application for type-safe 
 * handling of user data.
 * 
 * @version 1.0.0
 */

/**
 * Enumeration of possible user account statuses
 */
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending'
}

/**
 * Interface representing a user's membership in an organization
 */
export interface UserOrganization {
  /**
   * Unique identifier for the organization
   */
  orgId: string;
  
  /**
   * Name of the organization
   */
  name: string;
  
  /**
   * User's role within the organization
   */
  role: string;
  
  /**
   * ISO date string when the user joined the organization
   */
  joinedAt: string;
}

/**
 * Interface for user notification digest preferences
 */
export interface UserDigestSettings {
  /**
   * Whether digest notifications are enabled
   */
  enabled: boolean;
  
  /**
   * Frequency of digest notifications (daily, weekly, etc.)
   */
  frequency: string;
}

/**
 * Interface for user notification preferences
 */
export interface UserNotificationSettings {
  /**
   * Whether email notifications are enabled
   */
  email: boolean;
  
  /**
   * Whether push notifications are enabled
   */
  push: boolean;
  
  /**
   * Whether in-app notifications are enabled
   */
  inApp: boolean;
  
  /**
   * Digest notification settings
   */
  digest: UserDigestSettings;
}

/**
 * Interface for user application settings and preferences
 */
export interface UserSettings {
  /**
   * User's preferred language (ISO code)
   */
  language: string;
  
  /**
   * User's preferred theme
   */
  theme: string;
  
  /**
   * User's notification preferences
   */
  notifications: UserNotificationSettings;
  
  /**
   * User's default view when logging in
   */
  defaultView: string;
}

/**
 * Interface for user security-related information
 */
export interface UserSecurity {
  /**
   * Whether multi-factor authentication is enabled
   */
  mfaEnabled: boolean;
  
  /**
   * MFA method (app, sms, email)
   */
  mfaMethod: string;
  
  /**
   * ISO date string of the user's last login
   */
  lastLogin: string;
  
  /**
   * ISO date string of the user's last password change
   */
  lastPasswordChange: string;
  
  /**
   * Whether the user's email is verified
   */
  emailVerified: boolean;
}

/**
 * Core user interface representing a user in the system
 */
export interface User {
  /**
   * Unique identifier for the user
   */
  id: string;
  
  /**
   * User's email address
   */
  email: string;
  
  /**
   * User's first name
   */
  firstName: string;
  
  /**
   * User's last name
   */
  lastName: string;
  
  /**
   * List of role identifiers assigned to the user
   */
  roles: string[];
  
  /**
   * User's account status
   */
  status: UserStatus;
  
  /**
   * List of organizations the user belongs to
   */
  organizations: UserOrganization[];
  
  /**
   * User's application settings
   */
  settings: UserSettings;
  
  /**
   * User's security information
   */
  security: UserSecurity;
  
  /**
   * ISO date string when the user was created
   */
  createdAt: string;
  
  /**
   * ISO date string when the user was last updated
   */
  updatedAt: string;
}

/**
 * Interface for updating user profile information
 */
export interface UserProfileUpdateData {
  /**
   * Updated first name
   */
  firstName: string;
  
  /**
   * Updated last name
   */
  lastName: string;
  
  /**
   * Updated user settings
   */
  settings: Partial<UserSettings>;
}

/**
 * Interface for changing user password
 */
export interface UserPasswordChangeData {
  /**
   * User's current password
   */
  currentPassword: string;
  
  /**
   * User's new password
   */
  newPassword: string;
  
  /**
   * Confirmation of user's new password
   */
  confirmPassword: string;
}

/**
 * Type representing user roles within the system
 */
export type UserRole = {
  /**
   * The type of role
   */
  type: string;
};

/**
 * Interface representing a specific user permission
 */
export interface UserPermission {
  /**
   * The resource the permission applies to
   */
  resource: string;
  
  /**
   * The action the permission allows
   */
  action: string;
  
  /**
   * Additional conditions for the permission
   */
  conditions: object[];
}

/**
 * Extended user interface that includes permissions information
 */
export interface UserWithPermissions extends User {
  /**
   * List of specific permissions assigned to the user
   */
  permissions: UserPermission[];
}