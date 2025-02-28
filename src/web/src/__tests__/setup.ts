/**
 * Jest setup file for Task Management System frontend tests
 * 
 * This file configures the testing environment before tests run by:
 * - Setting up the Mock Service Worker (MSW) server to intercept API requests
 * - Extending Jest with custom DOM matchers for readable tests
 * - Providing utility functions for common testing needs
 * 
 * @version 1.0.0
 */

// Import MSW server to mock API requests during tests
import { server } from './mocks/server';

// Extend Jest with custom DOM element matchers for improved readability
import '@testing-library/jest-dom'; // v5.16.5

// Set up fetch mocking capabilities for tests that don't use MSW
import 'jest-fetch-mock'; // v3.0.3

// Start the MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset request handlers after each test to maintain test isolation
afterEach(() => server.resetHandlers());

// Clean up after all tests have completed
afterAll(() => server.close());

/**
 * Sets up a mock implementation of localStorage for testing
 * 
 * This function allows tests to interact with localStorage without 
 * actually persisting data to the browser's storage.
 */
export function mockLocalStorage(): void {
  // Create a mock storage object to store values
  const mockStorage: Record<string, string> = {};
  
  // Mock localStorage.getItem to retrieve values from the mock storage
  // Mock localStorage.setItem to store values in the mock storage
  // Mock localStorage.removeItem to remove values from the mock storage
  // Mock localStorage.clear to empty the mock storage
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn((key: string) => mockStorage[key] || null),
      setItem: jest.fn((key: string, value: string) => {
        mockStorage[key] = value;
      }),
      removeItem: jest.fn((key: string) => {
        delete mockStorage[key];
      }),
      clear: jest.fn(() => {
        Object.keys(mockStorage).forEach(key => {
          delete mockStorage[key];
        });
      })
    },
    writable: true
  });
}

/**
 * Suppresses console errors during tests to reduce noise from expected errors
 * 
 * This is useful when testing error conditions where console errors are expected
 * and would otherwise clutter the test output.
 */
export function suppressConsoleErrors(): void {
  // Store the original console.error implementation
  const originalError = console.error;
  
  // Replace console.error with a mock function that does nothing
  console.error = jest.fn();
  
  // Restore the original console.error after tests complete
  afterAll(() => {
    console.error = originalError;
  });
}