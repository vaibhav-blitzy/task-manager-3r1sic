import { useEffect, useCallback, RefObject } from 'react';

/**
 * Hook that handles clicks outside of a specified element.
 * Use this hook to detect when a user clicks outside a specific DOM element.
 * Commonly used for closing dropdowns, modals, or other UI elements.
 * 
 * @param ref - React ref object pointing to the element to monitor
 * @param callback - Function to call when a click outside occurs
 */
const useOutsideClick = (ref: RefObject<HTMLElement | null>, callback: () => void): void => {
  // Create a memoized handler function that will check if the click is outside the ref
  const handleClickOutside = useCallback(
    (event: MouseEvent) => {
      // If the ref exists and the click target is not inside the ref element
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    },
    [ref, callback] // Dependencies: re-create if ref or callback changes
  );

  useEffect(() => {
    // Add event listener when the component mounts
    document.addEventListener('mousedown', handleClickOutside);
    
    // Cleanup function to remove event listener when component unmounts
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [handleClickOutside]); // Re-run if handleClickOutside changes
};

export default useOutsideClick;