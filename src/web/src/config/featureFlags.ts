/**
 * Feature Flag Configuration
 *
 * This file defines feature flags for the application, allowing features to be
 * toggled on/off in different environments or for specific user roles.
 */

/**
 * Enum of all feature flag keys for type safety when referencing flags
 */
export enum FeatureFlag {
  REAL_TIME_COLLABORATION = 'realTimeCollaboration',
  ADVANCED_REPORTING = 'advancedReporting',
  FILE_ATTACHMENTS = 'fileAttachments',
  CALENDAR_INTEGRATION = 'calendarIntegration',
  NOTIFICATIONS = 'notifications',
  SEARCH_FUNCTIONALITY = 'searchFunctionality',
  MULTI_FACTOR_AUTHENTICATION = 'multiFactorAuthentication',
  TASK_DEPENDENCIES = 'taskDependencies',
  PROJECT_TEMPLATES = 'projectTemplates',
  DARK_MODE = 'darkMode',
}

/**
 * Interface defining the structure of feature flag settings
 */
export interface FeatureFlags {
  flags: Record<FeatureFlag, boolean>;
}

/**
 * Default values for all feature flags
 * All flags are disabled by default for safety
 */
export const defaultFeatureFlags: FeatureFlags = {
  flags: {
    [FeatureFlag.REAL_TIME_COLLABORATION]: false,
    [FeatureFlag.ADVANCED_REPORTING]: false,
    [FeatureFlag.FILE_ATTACHMENTS]: false,
    [FeatureFlag.CALENDAR_INTEGRATION]: false,
    [FeatureFlag.NOTIFICATIONS]: false,
    [FeatureFlag.SEARCH_FUNCTIONALITY]: false,
    [FeatureFlag.MULTI_FACTOR_AUTHENTICATION]: false,
    [FeatureFlag.TASK_DEPENDENCIES]: false,
    [FeatureFlag.PROJECT_TEMPLATES]: false,
    [FeatureFlag.DARK_MODE]: false,
  },
};

/**
 * Environment-specific feature flag configurations
 */
export const environmentFeatureFlags: Record<string, FeatureFlags> = {
  development: {
    flags: {
      ...defaultFeatureFlags.flags,
      // Enable all features in development for testing
      [FeatureFlag.REAL_TIME_COLLABORATION]: true,
      [FeatureFlag.ADVANCED_REPORTING]: true,
      [FeatureFlag.FILE_ATTACHMENTS]: true,
      [FeatureFlag.CALENDAR_INTEGRATION]: true,
      [FeatureFlag.NOTIFICATIONS]: true,
      [FeatureFlag.SEARCH_FUNCTIONALITY]: true,
      [FeatureFlag.MULTI_FACTOR_AUTHENTICATION]: true,
      [FeatureFlag.TASK_DEPENDENCIES]: true,
      [FeatureFlag.PROJECT_TEMPLATES]: true,
      [FeatureFlag.DARK_MODE]: true,
    },
  },
  staging: {
    flags: {
      ...defaultFeatureFlags.flags,
      // Enable core features in staging, but disable some advanced features
      [FeatureFlag.REAL_TIME_COLLABORATION]: true,
      [FeatureFlag.FILE_ATTACHMENTS]: true,
      [FeatureFlag.NOTIFICATIONS]: true,
      [FeatureFlag.SEARCH_FUNCTIONALITY]: true,
      [FeatureFlag.DARK_MODE]: true,
    },
  },
  production: {
    flags: {
      ...defaultFeatureFlags.flags,
      // Enable only stable features in production
      [FeatureFlag.FILE_ATTACHMENTS]: true,
      [FeatureFlag.NOTIFICATIONS]: true,
      [FeatureFlag.SEARCH_FUNCTIONALITY]: true,
    },
  },
};

/**
 * Returns the appropriate feature flags based on the current environment
 * @returns Feature flag configuration for the current environment
 */
export function getFeatureFlags(): FeatureFlags {
  // Determine the current environment
  const environment = getCurrentEnvironment();
  
  // Apply any overrides from configuration
  const overrides = getFeatureFlagOverrides();
  
  // Get the environment-specific flags or fall back to default
  const envFlags = environmentFeatureFlags[environment] || defaultFeatureFlags;
  
  // Apply any overrides
  return {
    flags: {
      ...envFlags.flags,
      ...overrides,
    },
  };
}

/**
 * Determines the current environment (development, staging, production)
 * @returns The current environment name
 */
function getCurrentEnvironment(): string {
  // For React applications, process.env.NODE_ENV is injected at build time
  // by webpack or other build tools
  let environment = 'development';
  
  try {
    // Use the NODE_ENV from process.env if available
    if (process?.env?.NODE_ENV) {
      environment = process.env.NODE_ENV;
    }
  } catch (e) {
    // Ignore errors - they might occur if process is not defined
  }
  
  // Only accept valid environments
  if (!['development', 'staging', 'production'].includes(environment)) {
    environment = 'development';
  }
  
  return environment;
}

/**
 * Gets any overrides for feature flags from configuration
 * @returns Object containing feature flag overrides
 */
function getFeatureFlagOverrides(): Partial<Record<FeatureFlag, boolean>> {
  const overrides: Partial<Record<FeatureFlag, boolean>> = {};
  
  // Check for local storage overrides if in a browser environment
  try {
    if (typeof localStorage !== 'undefined') {
      const storedOverrides = localStorage.getItem('featureFlags');
      if (storedOverrides) {
        const parsedOverrides = JSON.parse(storedOverrides);
        Object.entries(parsedOverrides).forEach(([key, value]) => {
          if (Object.values(FeatureFlag).includes(key as FeatureFlag)) {
            overrides[key as FeatureFlag] = !!value;
          }
        });
      }
    }
  } catch (e) {
    console.error('Error reading feature flag overrides from localStorage', e);
  }
  
  // Check for environment variable overrides
  // In React, these would be injected at build time as REACT_APP_* variables
  try {
    Object.values(FeatureFlag).forEach(flag => {
      const envVarName = `REACT_APP_FEATURE_${flag.toUpperCase()}`;
      
      // Access process.env safely
      const envVarValue = process?.env?.[envVarName];
      
      if (envVarValue !== undefined) {
        overrides[flag as FeatureFlag] = envVarValue.toLowerCase() === 'true';
      }
    });
  } catch (e) {
    // Ignore errors - they might occur if process is not defined
  }
  
  return overrides;
}

/**
 * Checks if a specific feature is enabled in the current environment
 * @param flagName The feature flag to check
 * @returns Whether the feature is enabled
 */
export function isFeatureEnabled(flagName: string): boolean {
  const featureFlags = getFeatureFlags();
  
  // Make sure the flag is a valid enum value
  const isValidFlag = Object.values(FeatureFlag).includes(flagName as FeatureFlag);
  
  if (isValidFlag) {
    return featureFlags.flags[flagName as FeatureFlag];
  }
  
  // If the flag doesn't exist, return false for safety
  return false;
}