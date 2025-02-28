# Task Management System - Frontend

This repository contains the frontend code for the Task Management System, a comprehensive web application designed to streamline the organization, tracking, and collaboration on tasks and projects for both individuals and teams.

## Technology Stack

The frontend is built using the following technologies:

| Technology | Version | Purpose |
|------------|---------|---------|
| [React](https://reactjs.org/) | 18.2.x | Component-based UI framework |
| [TypeScript](https://www.typescriptlang.org/) | 5.2.x | Static typing for JavaScript |
| [Redux Toolkit](https://redux-toolkit.js.org/) | 1.9.x | State management with reduced boilerplate |
| [React Router](https://reactrouter.com/) | 6.15.x | Client-side routing |
| [TailwindCSS](https://tailwindcss.com/) | 3.3.x | Utility-first CSS framework |
| [Axios](https://axios-http.com/) | 1.5.x | Promise-based HTTP client |
| [React Query](https://tanstack.com/query/) | 4.35.x | Data fetching and caching |
| [Chart.js](https://www.chartjs.org/) | 4.4.x | Data visualization |
| [DnD Kit](https://dndkit.com/) | 6.0.x | Drag and drop functionality |
| [React Hook Form](https://react-hook-form.com/) | 7.46.x | Form handling |
| [Jest](https://jestjs.io/) | 29.x | Testing framework |
| [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) | Latest | Component testing |

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm (v7 or higher) or yarn (v1.22 or higher)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/task-management-system.git
   cd task-management-system/src/web
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env.local`:
     ```bash
     cp .env.example .env.local
     ```
   - Update the values in `.env.local` to match your development environment

4. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. The application will be available at `http://localhost:3000`

## Development Workflow

### Branch Naming Convention

- Feature branches: `feature/short-description`
- Bug fix branches: `fix/issue-description`
- Refactor branches: `refactor/description`
- Documentation branches: `docs/description`

### Code Style

We use ESLint and Prettier to maintain code quality and consistent style:

- Run linting:
  ```bash
  npm run lint
  # or
  yarn lint
  ```

- Fix linting issues automatically:
  ```bash
  npm run lint:fix
  # or
  yarn lint:fix
  ```

- Format code with Prettier:
  ```bash
  npm run format
  # or
  yarn format
  ```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

Example:
```
feat(auth): add login form validation

Implement client-side validation for the login form
- Email format validation
- Password strength requirements
- Error message display

Closes #123
```

Common types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Changes that do not affect code (formatting, etc.)
- `refactor`: Code refactoring without functionality changes
- `test`: Adding or updating tests
- `chore`: Changes to build process, dependencies, etc.

## Project Structure

```
src/web/
├── public/             # Static assets
├── src/
│   ├── api/            # API client and service definitions
│   ├── assets/         # Images, fonts, and other assets
│   ├── components/     # Reusable components
│   │   ├── atoms/      # Basic building blocks
│   │   ├── molecules/  # Simple component combinations
│   │   ├── organisms/  # Complex functional units
│   │   ├── templates/  # Page layouts without content
│   │   └── ui/         # UI library components
│   ├── constants/      # Application constants
│   ├── context/        # React context definitions
│   ├── features/       # Feature-based modules
│   ├── hooks/          # Custom React hooks
│   ├── layouts/        # Layout components
│   ├── pages/          # Page components
│   ├── router/         # Route definitions
│   ├── services/       # Business logic and services
│   ├── store/          # Redux store setup and slices
│   ├── styles/         # Global styles and Tailwind config
│   ├── types/          # TypeScript types and interfaces
│   ├── utils/          # Utility functions
│   ├── App.tsx         # Main application component
│   ├── index.tsx       # Application entry point
│   └── vite-env.d.ts   # Vite type definitions
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
├── .env.example        # Example environment variables
├── .eslintrc.js        # ESLint configuration
├── .prettierrc         # Prettier configuration
├── jest.config.js      # Jest configuration
├── package.json        # Package dependencies
├── tailwind.config.js  # Tailwind CSS configuration
├── tsconfig.json       # TypeScript configuration
└── vite.config.ts      # Vite configuration
```

## Building for Production

To build the application for production:

```bash
npm run build
# or
yarn build
```

The build artifacts will be stored in the `dist/` directory.

To preview the production build locally:

```bash
npm run preview
# or
yarn preview
```

### Deployment

Our CI/CD pipeline automatically deploys the application when changes are merged to specific branches:

- `develop` branch: Deploys to the development environment
- `staging` branch: Deploys to the staging environment
- `main` branch: Deploys to the production environment

## Testing

We use Jest and React Testing Library for testing our application.

### Running Tests

- Run all tests:
  ```bash
  npm test
  # or
  yarn test
  ```

- Run tests in watch mode (for development):
  ```bash
  npm test:watch
  # or
  yarn test:watch
  ```

- Generate test coverage report:
  ```bash
  npm test:coverage
  # or
  yarn test:coverage
  ```

### Test Structure

- **Unit Tests**: Test individual components and functions in isolation
- **Integration Tests**: Test interactions between components
- **E2E Tests**: Test complete user flows using Cypress

### Test File Naming Convention

- Unit tests: `ComponentName.test.tsx`
- Integration tests: `ComponentName.integration.test.tsx`
- E2E tests: `feature-name.spec.ts`

### Test Example

```tsx
import { render, screen } from '@testing-library/react';
import { TaskCard } from './TaskCard';

describe('TaskCard', () => {
  it('should display task details when task is provided', () => {
    // Arrange
    const task = { id: '123', title: 'Test Task', status: 'in-progress' };
    
    // Act
    render(<TaskCard task={task} />);
    
    // Assert
    expect(screen.getByText('Test Task')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
  });
});
```

## Style Guide

### Component Structure

```tsx
// Import statements
import React from 'react';
import { useTaskState } from '@/hooks/useTaskState';
import { TaskStatus } from '@/components/TaskStatus';

// Interface definitions
interface TaskCardProps {
  id: string;
  title: string;
  status: string;
  dueDate?: string;
  onStatusChange?: (id: string, status: string) => void;
}

// Component definition
export const TaskCard: React.FC<TaskCardProps> = ({
  id,
  title,
  status,
  dueDate,
  onStatusChange,
}) => {
  // Hooks
  const { isOverdue } = useTaskState(dueDate);
  
  // Event handlers
  const handleStatusChange = (newStatus: string) => {
    if (onStatusChange) {
      onStatusChange(id, newStatus);
    }
  };
  
  // Render
  return (
    <div className="p-4 border rounded shadow">
      <h3 className="text-lg font-medium">{title}</h3>
      <TaskStatus status={status} onChange={handleStatusChange} />
      {dueDate && (
        <p className={`text-sm ${isOverdue ? 'text-red-500' : 'text-gray-500'}`}>
          Due: {new Date(dueDate).toLocaleDateString()}
        </p>
      )}
    </div>
  );
};
```

### CSS / Styling

We use TailwindCSS for styling. Follow these guidelines:

1. Use Tailwind utility classes whenever possible
2. Create custom components for complex or repeated UI patterns
3. Use CSS modules (`.module.css`) only when necessary for complex styling that can't be achieved with Tailwind
4. Follow a mobile-first approach for responsive design

### TypeScript Guidelines

1. Use explicit typing instead of `any` wherever possible
2. Create interfaces for props, state, and API responses
3. Use type guards to narrow types when necessary
4. Export types/interfaces that are used across multiple files
5. Use descriptive names for types and interfaces

## Contributing

### Getting Started with Development

1. Find an issue to work on or create a new one
2. Discuss the approach if it's a significant change
3. Create a branch from `develop` following our naming convention
4. Implement your changes with appropriate tests
5. Submit a pull request to the `develop` branch

### Pull Request Process

1. Ensure your code adheres to our style guidelines
2. Update the README or documentation if necessary
3. Include tests that verify your changes
4. Make sure all tests pass and your code is linted
5. Obtain approval from at least one code owner
6. Once approved, a maintainer will merge your pull request

### Code Review Guidelines

- Be respectful and constructive in reviews
- Focus on code quality, maintainability, and adherence to project standards
- Check for test coverage and documentation
- Verify that the code meets acceptance criteria

### Reporting Bugs

When reporting bugs, please include:

1. A clear and descriptive title
2. Steps to reproduce the bug
3. Expected behavior
4. Actual behavior
5. Screenshots if applicable
6. Environment information (browser, OS, etc.)
7. Any additional context that might be helpful

## License

This project is licensed under the [MIT License](LICENSE).