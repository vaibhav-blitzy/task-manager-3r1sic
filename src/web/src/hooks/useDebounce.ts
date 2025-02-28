import { useState, useEffect } from 'react'; // React 18.2.x

/**
 * A hook that returns a debounced version of the passed value that only 
 * updates after a specified delay has passed since the last change.
 * 
 * @template T - The type of the value being debounced
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced value that updates after the specified delay
 */
function useDebounce<T>(value: T, delay: number): T {
  // Initialize state with the initial value
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up a timer to update the debounced value after the specified delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timer if the value changes before the delay completes
    // or if the component unmounts
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]); // Re-run the effect when value or delay changes

  // Return the debounced value
  return debouncedValue;
}

export default useDebounce;