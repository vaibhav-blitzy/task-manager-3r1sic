/**
 * Mock Service Worker server setup for intercepting API requests in tests
 *
 * This file configures a mock server instance that intercepts network requests during tests
 * and responds with predefined mock data, allowing frontend components to be tested
 * without actual backend dependencies.
 * 
 * @version 1.0.0
 */

import { setupServer } from 'msw/node'; // msw/node version: ^1.0.0
import handlers from './handlers';

// Create and configure the mock server with the handlers
const server = setupServer(...handlers);

// Export the server to be used in Jest's setup and teardown hooks
export { server };