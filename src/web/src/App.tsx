import React, { useEffect } from 'react'; // react ^18.2.x
import { Provider } from 'react-redux'; // react-redux ^8.1.x
import { BrowserRouter } from 'react-router-dom'; // react-router-dom ^6.15.x
import { Toaster } from 'react-hot-toast'; // react-hot-toast ^2.4.x
import { QueryClient, QueryClientProvider } from 'react-query'; // react-query ^4.35.x

import AppRoutes from './routes';
import { ThemeProvider } from './contexts/ThemeContext';
import { FeatureFlagProvider } from './contexts/FeatureFlagContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import useAuth from './api/hooks/useAuth';

/**
 * Main application component that wraps the application with necessary providers and routes
 * @returns {JSX.Element} The rendered application
 */
const App = (): JSX.Element => {
  // LD1: Create QueryClient instance for React Query
  const queryClient = new QueryClient();

  // LD1: Use useAuth hook to get authentication functions and state
  const { checkAuth, isAuthenticated } = useAuth();

  // LD1: Execute checkAuth on component mount to verify existing auth tokens
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // LD1: Return the component hierarchy with all providers in the correct order
  return (
    <QueryClientProvider client={queryClient}>
      <Provider store={require('./store').store}>
        <ThemeProvider>
          <FeatureFlagProvider>
            <WebSocketProvider options={{ autoConnect: isAuthenticated }}>
              <BrowserRouter>
                {/* LD1: Set up global toast notifications with Toaster component */}
                <Toaster
                  position="top-right"
                  reverseOrder={false}
                />
                {/* LD1: Render the main application routes through AppRoutes component */}
                <AppRoutes />
              </BrowserRouter>
            </WebSocketProvider>
          </FeatureFlagProvider>
        </ThemeProvider>
      </Provider>
    </QueryClientProvider>
  );
};

export default App;