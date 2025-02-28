import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Import the component to test
import ForgotPassword from './ForgotPassword';

// Setup MSW server for API mocking
const server = setupServer(
  rest.post('/auth/password/reset', (req, res, ctx) => {
    // Default success response
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: 'Password reset instructions sent to your email'
      })
    );
  })
);

// Start server before all tests
beforeAll(() => server.listen());
// Reset handlers after each test
afterEach(() => server.resetHandlers());
// Close server after all tests
afterAll(() => server.close());

// Utility function to render with providers
const renderWithProviders = (
  ui: React.ReactElement,
  { 
    route = '/', 
    initialEntries = [route],
    useMemoryRouter = false,
    ...renderOptions 
  } = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    if (useMemoryRouter) {
      return (
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/" element={children} />
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );
    }
    return <BrowserRouter>{children}</BrowserRouter>;
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

describe('ForgotPassword Component', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
  });

  it('should render the forgot password form', async () => {
    renderWithProviders(<ForgotPassword />);
    
    expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument();
    expect(screen.getByText(/back to login/i)).toBeInTheDocument();
  });

  it('should show error for empty email submission', async () => {
    renderWithProviders(<ForgotPassword />);
    
    const submitButton = screen.getByRole('button', { name: /reset password/i });
    await user.click(submitButton);
    
    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });

  it('should show error for invalid email format', async () => {
    renderWithProviders(<ForgotPassword />);
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'invalid-email');
    
    const submitButton = screen.getByRole('button', { name: /reset password/i });
    await user.click(submitButton);
    
    expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
  });

  it('should submit form successfully with valid email', async () => {
    renderWithProviders(<ForgotPassword />);
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'test@example.com');
    
    const submitButton = screen.getByRole('button', { name: /reset password/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/password reset instructions sent to your email/i)).toBeInTheDocument();
    });
  });

  it('should handle API error response', async () => {
    // Setup error response
    server.use(
      rest.post('/auth/password/reset', (req, res, ctx) => {
        return res(
          ctx.status(404),
          ctx.json({
            success: false,
            message: 'User not found'
          })
        );
      })
    );

    renderWithProviders(<ForgotPassword />);
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'nonexistent@example.com');
    
    const submitButton = screen.getByRole('button', { name: /reset password/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/user not found/i)).toBeInTheDocument();
    });
  });

  it('should navigate to login page when clicking back link', async () => {
    renderWithProviders(<ForgotPassword />, { useMemoryRouter: true });
    
    const backLink = screen.getByText(/back to login/i);
    await user.click(backLink);
    
    await waitFor(() => {
      expect(screen.getByText(/login page/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during form submission', async () => {
    // Setup delayed response
    server.use(
      rest.post('/auth/password/reset', (req, res, ctx) => {
        return res(
          ctx.delay(500), // Add delay
          ctx.status(200),
          ctx.json({
            success: true,
            message: 'Password reset instructions sent to your email'
          })
        );
      })
    );

    renderWithProviders(<ForgotPassword />);
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'test@example.com');
    
    const submitButton = screen.getByRole('button', { name: /reset password/i });
    await user.click(submitButton);
    
    // Check for loading state - button should be disabled or loading spinner should be visible
    expect(submitButton).toBeDisabled();
    // Alternatively, if there's a loading spinner:
    // expect(screen.getByRole('status')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText(/password reset instructions sent to your email/i)).toBeInTheDocument();
    });
  });
});