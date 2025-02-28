import { useState, useEffect, Dispatch, SetStateAction } from 'react'; // react@18.2.x

/**
 * A custom hook that uses localStorage to persist state between page reloads.
 * 
 * @param key - The localStorage key to store the value under
 * @param initialValue - The initial value to use if no value is found in localStorage
 * @returns A stateful value and a function to update it, similar to useState but persisted in localStorage
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, Dispatch<SetStateAction<T>>] {
  // Function to safely retrieve and parse the value from localStorage
  const getStoredValue = (): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    
    try {
      // Get from localStorage by key
      const item = window.localStorage.getItem(key);
      // Parse stored json or return initialValue if null
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      // If error also return initialValue
      console.error(`Error reading from localStorage key "${key}":`, error);
      return initialValue;
    }
  };

  // Initialize state with useState<T>, using the value from getStoredValue()
  const [storedValue, setStoredValue] = useState<T>(getStoredValue);

  // Define a setValue function that updates both React state and localStorage
  const setValue: Dispatch<SetStateAction<T>> = (value) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore =
        value instanceof Function ? value(storedValue) : value;
      
      // Save state
      setStoredValue(valueToStore);
      
      // Save to localStorage using JSON.stringify
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      // Handle any errors like quota exceeded
      console.error(`Error writing to localStorage key "${key}":`, error);
    }
  };

  // Add an event listener for the 'storage' event to sync state across tabs
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const handleStorageChange = (event: StorageEvent) => {
      // Check if the updated key matches our key
      if (event.key === key && event.newValue !== null) {
        try {
          // Update state if needed
          setStoredValue(JSON.parse(event.newValue));
        } catch (error) {
          console.error(`Error parsing localStorage change for key "${key}":`, error);
        }
      }
    };

    // Add event listener
    window.addEventListener('storage', handleStorageChange);

    // Clean up the event listener in the useEffect cleanup function
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [key]); // Only re-run effect if key changes

  // Return [storedValue, setValue] tuple matching React's useState pattern
  return [storedValue, setValue];
}