import {
  render,
  screen,
  waitFor,
  fireEvent,
  within,
  RenderOptions,
} from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import React, { ReactElement, PropsWithChildren } from 'react'; // react ^18.2.0
import {
  configureStore,
  PreloadedState,
} from '@reduxjs/toolkit'; // @reduxjs/toolkit ^1.9.0
import { rest } from 'msw'; // msw ^1.0.0
import { Provider } from '../store';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../contexts/ThemeContext';
import { WebSocketProvider } from '../contexts/WebSocketContext';
import { FeatureFlagProvider } from '../contexts/FeatureFlagContext';
import store, { RootState } from '../store';
import { User } from '../types/user';
import { Task } from '../types/task';
import { Project } from '../types/project';

/**
 * Custom render function that wraps components with all necessary providers (Redux, Router, Theme, etc.)
 * @param ui - The UI component to render
 * @param options - Additional options for the render function
 * @param preloadedState - Optional preloaded state for the Redux store
 * @returns Rendered component with additional helpers from React Testing Library
 */
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
  preloadedState?: PreloadedState<RootState>
) => {
  // Create test store with optional preloaded state if provided
  const testStore = configureStore({
    ...store,
    preloadedState: preloadedState,
  });

  // Create AllProviders component that wraps children with all necessary context providers
  const AllProviders: React.FC<PropsWithChildren<{}>> = ({ children }) => {
    return (
      <Provider store={testStore}>
        <BrowserRouter>
          <ThemeProvider>
            <WebSocketProvider>
              <FeatureFlagProvider>
                {children}
              </FeatureFlagProvider>
            </WebSocketProvider>
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  };

  // Call the original render function with the UI component and AllProviders
  return render(ui, { wrapper: AllProviders, ...options });
};

// Re-export testing utilities from React Testing Library for convenience
export { screen, waitFor, fireEvent, within, userEvent };

// Override React Testing Library's render with our customRender
export * from '@testing-library/react';
export { customRender as render };

/**
 * Creates a mock user object for testing
 * @param overrides - Partial user object to override default values
 * @returns Complete user object with default values and any provided overrides
 */
export const createMockUser = (overrides: Partial<User> = {}): User => {
  // Define default user properties (id, email, name, etc.)
  const defaultUser: User = {
    id: 'test-user-id',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    roles: [],
    status: 'active',
    organizations: [],
    settings: {
      language: 'en',
      theme: 'light',
      notifications: {
        email: true,
        push: false,
        inApp: true,
        digest: {
          enabled: false,
          frequency: 'daily',
        },
      },
      defaultView: 'board',
    },
    security: {
      mfaEnabled: false,
      mfaMethod: 'app',
      lastLogin: new Date().toISOString(),
      lastPasswordChange: new Date().toISOString(),
      emailVerified: true,
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  // Merge provided overrides with defaults
  return { ...defaultUser, ...overrides };
};

/**
 * Creates a mock task object for testing
 * @param overrides - Partial task object to override default values
 * @returns Complete task object with default values and any provided overrides
 */
export const createMockTask = (overrides: Partial<Task> = {}): Task => {
  // Define default task properties (id, title, status, etc.)
  const defaultTask: Task = {
    id: 'test-task-id',
    title: 'Test Task',
    description: 'Test Description',
    status: 'created',
    priority: 'medium',
    dueDate: new Date().toISOString(),
    createdBy: createMockUser(),
    assignee: createMockUser(),
    project: null,
    tags: [],
    attachments: [],
    subtasks: [],
    dependencies: [],
    comments: [],
    activity: [],
    metadata: {
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      completedAt: null,
      timeEstimate: 60,
      timeSpent: 30,
    },
  };

  // Merge provided overrides with defaults
  return { ...defaultTask, ...overrides };
};

/**
 * Creates a mock project object for testing
 * @param overrides - Partial project object to override default values
 * @returns Complete project object with default values and any provided overrides
 */
export const createMockProject = (overrides: Partial<Project> = {}): Project => {
  // Define default project properties (id, name, status, etc.)
  const defaultProject: Project = {
    id: 'test-project-id',
    name: 'Test Project',
    description: 'Test Project Description',
    status: 'active',
    category: 'Test Category',
    owner: createMockUser(),
    ownerId: 'test-user-id',
    members: [],
    settings: {
      workflow: {
        enableReview: false,
        allowSubtasks: true,
        defaultTaskStatus: 'created',
      },
      permissions: {
        memberInvite: 'admin',
        taskCreate: 'member',
        commentCreate: 'member',
      },
      notifications: {
        taskCreate: true,
        taskComplete: true,
        commentAdd: true,
      },
    },
    taskLists: [],
    metadata: {
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      completedAt: null,
      taskCount: 10,
      completedTaskCount: 5,
    },
    tags: [],
    customFields: [],
  };

  // Merge provided overrides with defaults
  return { ...defaultProject, ...overrides };
};

/**
 * Creates a Redux store for testing with optional preloaded state
 * @param preloadedState - Optional preloaded state for the Redux store
 * @returns Configured Redux store instance for testing
 */
export const createTestStore = (preloadedState?: PreloadedState<RootState>) => {
  // Import store configuration from Redux toolkit
  return configureStore({
    ...store,
    preloadedState: preloadedState,
  });
};

/**
 * Utility to wait for loading indicators to disappear
 * @returns Promise that resolves when loading is complete
 */
export const waitForLoadingToFinish = async () => {
  // Use waitFor to check for absence of loading indicators
  await waitFor(() => {
    const loadingIndicators = screen.queryAllByTestId('loading-indicator');
    expect(loadingIndicators).toHaveLength(0);
  });
};

/**
 * Helper function to fill out form fields in tests
 * @param fieldsData - Object containing field names and values
 * @returns Promise that resolves when form is filled
 */
export const fillForm = async (fieldsData: Record<string, string>) => {
  // Loop through the provided fields data
  for (const [fieldName, fieldValue] of Object.entries(fieldsData)) {
    // For each field, find the input element and enter the value using userEvent
    const inputElement = screen.getByLabelText(fieldName);
    await userEvent.type(inputElement, fieldValue);
  }
};