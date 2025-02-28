import React, { createContext, useState, useContext, useEffect, useMemo, ReactNode } from 'react';
import { themeColors, defaultTheme, getThemeColors, ThemeType, Theme, ColorPalette } from '../config/themes';
import { getThemePreference, setThemePreference } from '../utils/storage';
import { useMediaQuery } from '../hooks/useMediaQuery';

// Define the shape of our theme context
interface ThemeContextType {
  theme: ThemeType;
  colors: ColorPalette;
  toggleTheme: () => void;
  setTheme: (theme: ThemeType) => void;
}

// Create the context with undefined as default value
export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Custom hook that provides access to the theme context
 * @returns ThemeContextType object with theme state and control functions
 * @throws Error if used outside of a ThemeProvider
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
}

interface ThemeProviderProps {
  children: ReactNode;
  initialTheme?: ThemeType;
}

/**
 * Theme provider component that manages theme state and provides theme switching functionality
 * Theme priority: 1) initialTheme prop, 2) localStorage preference, 3) system preference, 4) default theme
 * 
 * @param children - React children to render within the provider
 * @param initialTheme - Optional initial theme to override saved preferences
 * @returns ThemeContext.Provider wrapping the children
 */
export function ThemeProvider({ children, initialTheme }: ThemeProviderProps): JSX.Element {
  // Media query for system dark mode preference
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  
  // Initialize theme based on priority: prop > localStorage > system > default
  const [theme, setThemeState] = useState<ThemeType>(() => {
    if (initialTheme && (initialTheme === 'light' || initialTheme === 'dark')) {
      return initialTheme;
    }
    
    const savedTheme = getThemePreference();
    if (savedTheme === 'light' || savedTheme === 'dark') {
      return savedTheme as ThemeType;
    }
    
    return prefersDarkMode ? 'dark' : defaultTheme;
  });
  
  // Memoize colors based on current theme to avoid unnecessary re-renders
  const colors = useMemo(() => getThemeColors(theme), [theme]);
  
  // Toggle between light and dark themes
  const toggleTheme = (): void => {
    setThemeState(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };
  
  // Set a specific theme
  const setTheme = (newTheme: ThemeType): void => {
    if (newTheme === 'light' || newTheme === 'dark') {
      setThemeState(newTheme);
    }
  };
  
  // Update document body when theme changes
  useEffect(() => {
    // Remove previous theme class and add new one
    document.body.classList.remove('theme-light', 'theme-dark');
    document.body.classList.add(`theme-${theme}`);
    
    // Set data attribute for CSS selectors
    document.documentElement.setAttribute('data-theme', theme);
    
    // Optional: Set color-scheme for browser UI elements like scrollbars
    document.documentElement.style.colorScheme = theme;
  }, [theme]);
  
  // Persist theme preference to localStorage when it changes
  useEffect(() => {
    setThemePreference(theme);
  }, [theme]);
  
  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      theme,
      colors,
      toggleTheme,
      setTheme,
    }),
    [theme, colors]
  );
  
  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}