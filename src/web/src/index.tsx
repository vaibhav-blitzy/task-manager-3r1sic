import React from 'react'; // react ^18.2.x
import ReactDOM from 'react-dom/client'; // react-dom/client ^18.2.x
import { Provider } from 'react-redux'; // react-redux ^8.1.x

import App from './App';
import store from './store';
import './assets/styles/index.css';

/**
 * Reference to the root DOM element where the React app will be mounted
 */
const rootElement: HTMLElement | null = document.getElementById('root');

/**
 * Renders the main application with all necessary providers
 */
const renderApp = (): void => {
  // LD1: Get the root element from the DOM using document.getElementById('root')
  if (!rootElement) {
    console.error('Root element not found in the DOM');
    return;
  }

  // LD1: Create a React 18 root using createRoot API
  const root = ReactDOM.createRoot(rootElement);

  // LD1: Render the App component wrapped with Redux Provider
  // LD1: Implement strict mode for development quality checks
  root.render(
    <React.StrictMode>
      <Provider store={store}>
        <App />
      </Provider>
    </React.StrictMode>
  );
};

// Call the renderApp function to start the application
renderApp();