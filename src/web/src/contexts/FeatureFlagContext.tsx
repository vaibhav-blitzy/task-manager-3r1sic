import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'; // react@18.2.0
import { 
  FeatureFlag, 
  FeatureFlags, 
  getFeatureFlags, 
  isFeatureEnabled,
  defaultFeatureFlags 
} from '../config/featureFlags';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { USER_ROLES } from '../config/constants';

// Storage key for feature flag overrides in localStorage
export const FEATURE_FLAGS_STORAGE_KEY = 'task_management_feature_flags';

/**
 * Interface defining the structure and methods available in the feature flag context
 */
interface FeatureFlagContextType {
  /**
   * Current state of all feature flags
   */
  featureFlags: FeatureFlags;
  
  /**
   * Sets the enabled state of a specific feature flag
   * @param flag - The feature flag to update
   * @param enabled - Whether the feature should be enabled
   */
  setFeatureFlag: (flag: FeatureFlag, enabled: boolean) => void;
  
  /**
   * Checks if a specific feature is enabled
   * @param flag - The feature flag to check
   * @returns Whether the feature is enabled
   */
  isEnabled: (flag: FeatureFlag) => boolean;
  
  /**
   * Resets all feature flags to their default values
   */
  resetFeatureFlags: () => void;
}

/**
 * Creates and initializes the feature flag context with type safety
 */
function createFeatureFlagContext() {
  return createContext<FeatureFlagContextType | null>(null);
}

// Create the context
const FeatureFlagContext = createFeatureFlagContext();

/**
 * Context provider component that manages feature flag state and provides context to child components
 */
const FeatureFlagProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Get the base feature flags from the config
  const baseFeatureFlags = getFeatureFlags();
  
  // Use localStorage to persist user overrides
  const [userOverrides, setUserOverrides] = useLocalStorage<Record<string, boolean>>(
    FEATURE_FLAGS_STORAGE_KEY,
    {}
  );
  
  // Merge base flags with user overrides
  const [featureFlags, setFeatureFlags] = useState<FeatureFlags>({
    flags: {
      ...baseFeatureFlags.flags,
      ...userOverrides,
    },
  });
  
  // Update the merged flags when base flags or overrides change
  useEffect(() => {
    setFeatureFlags({
      flags: {
        ...baseFeatureFlags.flags,
        ...userOverrides,
      },
    });
  }, [baseFeatureFlags, userOverrides]);
  
  // Function to update a specific feature flag
  const setFeatureFlag = (flag: FeatureFlag, enabled: boolean) => {
    // Update user overrides in localStorage
    setUserOverrides({
      ...userOverrides,
      [flag]: enabled,
    });
    
    // Update the current state
    setFeatureFlags(prevFlags => ({
      flags: {
        ...prevFlags.flags,
        [flag]: enabled,
      },
    }));
  };
  
  // Check if a feature is enabled
  const isEnabled = (flag: FeatureFlag): boolean => {
    return featureFlags.flags[flag] === true;
  };
  
  // Reset all feature flags to default values
  const resetFeatureFlags = () => {
    setUserOverrides({});
    setFeatureFlags(baseFeatureFlags);
  };
  
  // Create the context value
  const contextValue: FeatureFlagContextType = {
    featureFlags,
    setFeatureFlag,
    isEnabled,
    resetFeatureFlags,
  };
  
  return (
    <FeatureFlagContext.Provider value={contextValue}>
      {children}
    </FeatureFlagContext.Provider>
  );
};

/**
 * Custom hook that provides access to the feature flag context
 */
const useFeatureFlags = (): FeatureFlagContextType => {
  const context = useContext(FeatureFlagContext);
  
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider');
  }
  
  return context;
};

/**
 * Simplified hook for checking if a specific feature is enabled
 * @param featureKey - The feature flag to check
 * @returns Whether the feature is enabled
 */
const useFeature = (featureKey: FeatureFlag): boolean => {
  const { isEnabled } = useFeatureFlags();
  return isEnabled(featureKey);
};

/**
 * Higher-order component that conditionally renders based on feature flag status
 * @param featureKey - The feature flag to check
 * @param Component - The component to render if the feature is enabled
 * @param FallbackComponent - Optional component to render if the feature is disabled
 * @returns A component that will conditionally render based on the feature flag
 */
const withFeatureFlag = <P extends object>(
  featureKey: FeatureFlag,
  Component: React.ComponentType<P>,
  FallbackComponent: React.ComponentType<P> | null = null
): React.FC<P> => {
  return (props: P) => {
    const isEnabled = useFeature(featureKey);
    
    if (isEnabled) {
      return <Component {...props} />;
    }
    
    if (FallbackComponent) {
      return <FallbackComponent {...props} />;
    }
    
    return null;
  };
};

export { 
  FeatureFlagProvider, 
  useFeatureFlags, 
  useFeature, 
  withFeatureFlag,
  FeatureFlagContext,
  type FeatureFlagContextType
};