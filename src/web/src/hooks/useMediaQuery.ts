import { useState, useEffect } from 'react';

/**
 * Custom hook that evaluates a media query string and returns a boolean
 * indicating if it matches the current viewport.
 * 
 * @param query - CSS media query string
 * @returns boolean indicating if the media query matches
 * 
 * @example
 * const isWideScreen = useMediaQuery('(min-width: 1200px)');
 */
export function useMediaQuery(query: string): boolean {
  // Function to get the initial match state
  const getMatches = (): boolean => {
    // Check if window is defined (to handle SSR)
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  };

  // Initialize state with current match value
  const [matches, setMatches] = useState<boolean>(getMatches());

  // Set up event listener to track changes to media query matches
  useEffect(() => {
    // Return early if window is undefined (SSR)
    if (typeof window === 'undefined') {
      return undefined;
    }

    // Create the MediaQueryList
    const mediaQueryList = window.matchMedia(query);

    // Define handler to update state when matches change
    const handler = (event: MediaQueryListEvent): void => {
      setMatches(event.matches);
    };

    // Add event listener for changes
    // Use the modern API if available, fall back to legacy API
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', handler);
    } else {
      // For older browsers that don't support addEventListener
      mediaQueryList.addListener(handler);
    }

    // Update matches if they've changed since hook was initialized
    // This can happen if the query changed
    if (matches !== mediaQueryList.matches) {
      setMatches(mediaQueryList.matches);
    }

    // Clean up function to remove listener when component unmounts
    // or when query changes
    return () => {
      if (mediaQueryList.removeEventListener) {
        mediaQueryList.removeEventListener('change', handler);
      } else {
        // For older browsers
        mediaQueryList.removeListener(handler);
      }
    };
  }, [query, matches]); // Re-run effect if query changes

  return matches;
}

/**
 * Predefined breakpoints based on the application's responsive design specifications.
 * - sm: Mobile screens (<640px)
 * - md: Tablet screens (≥641px)
 * - lg: Desktop screens (≥1025px)
 * - xl: Large Desktop screens (≥1441px)
 */
const breakpoints = {
  sm: '(max-width: 640px)',         // Mobile
  md: '(min-width: 641px)',         // Tablet and above
  lg: '(min-width: 1025px)',        // Desktop and above
  xl: '(min-width: 1441px)',        // Large Desktop
};

type Breakpoint = keyof typeof breakpoints;

/**
 * Utility hook that leverages useMediaQuery to check if the viewport
 * matches specific predefined breakpoints.
 *
 * @param breakpoint - The breakpoint to check ('sm', 'md', 'lg', 'xl')
 * @returns boolean indicating if the current viewport matches or exceeds the specified breakpoint
 * 
 * @example
 * const isDesktop = useBreakpoint('lg');
 * const isMobile = useBreakpoint('sm');
 */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  const query = breakpoints[breakpoint];
  return useMediaQuery(query);
}