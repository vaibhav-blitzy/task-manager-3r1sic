import React from 'react'; // react ^18.2.0
import { rest } from 'msw'; // msw ^1.2.1
import { render, screen, waitFor } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { MemoryRouter } from 'react-router-dom'; // react-router-dom ^6.10.0
import { Provider } from 'react-redux'; // react-redux ^8.0.5

import TeamSettings from './TeamSettings';
import store from '../../../store';
import { server } from '../../../__tests__/mocks/server';
import { useProjects, useProjectMembers } from '../../../api/hooks/useProjects';
import { ProjectRole } from '../../../types/project';

// Define mock data and handlers
const mockProjects = [
  {
    id: '1',
    name: 'Project 1',
    ownerId: 'user1',
    members: [
      { userId: 'user1', role: 'admin', user: { id: 'user1', email: 'user1@example.com', firstName: 'User', lastName: 'One' } as any, joinedAt: new Date().toISOString(), isActive: true },
      { userId: 'user2', role: 'member', user: { id: 'user2', email: 'user2@example.com', firstName: 'User', lastName: 'Two' } as any, joinedAt: new Date().toISOString(), isActive: true },
    ],
  },
  {
    id: '2',
    name: 'Project 2',
    ownerId: 'user3',
    members: [
      { userId: 'user3', role: 'admin', user: { id: 'user3', email: 'user3@example.com', firstName: 'User', lastName: 'Three' } as any, joinedAt: new Date().toISOString(), isActive: true },
    ],
  },
];

const mockTeamMembers = [
  { userId: 'user1', role: 'admin', user: { id: 'user1', email: 'user1@example.com', firstName: 'User', lastName: 'One' } as any, joinedAt: new Date().toISOString(), isActive: true },
  { userId: 'user2', role: 'member', user: { id: 'user2', email: 'user2@example.com', firstName: 'User', lastName: 'Two' } as any, joinedAt: new Date().toISOString(), isActive: true },
];

// Helper function to render component with necessary providers
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <Provider store={store}>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </Provider>
  );
};

describe('TeamSettings component', () => {
  beforeEach(() => {
    // Reset MSW handlers
    server.resetHandlers();

    // Set up default API mocks for projects and members
    server.use(
      rest.get('/api/projects', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockProjects));
      }),
      rest.get('/api/projects/1/members', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockTeamMembers));
      })
    );
  });

  afterEach(() => {
    // Clean up any mounted components
  });

  it('renders_team_settings_page', async () => {
    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Assert that the page heading is visible and correct
    expect(screen.getByText('Team Management')).toBeVisible();

    // Assert that the project selector is displayed
    expect(screen.getByLabelText('Select Project')).toBeVisible();

    // Assert that the team members section is present
    expect(screen.getByText('Team Members')).toBeVisible();
  });

  it('displays_loading_state', () => {
    // Override the default project mock to simulate loading
    server.use(
      rest.get('/api/projects', (req, res, ctx) => {
        return res(ctx.delay(100), ctx.status(200), ctx.json(mockProjects));
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Assert that a loading spinner or text is displayed initially
    expect(screen.getByText('Loading projects...')).toBeVisible();
  });

  it('displays_team_members', async () => {
    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Wait for the team members to load
    await waitFor(() => {
      expect(screen.getByText('User One')).toBeVisible();
      expect(screen.getByText('user1@example.com')).toBeVisible();
      expect(screen.getByText('Admin')).toBeVisible();

      expect(screen.getByText('User Two')).toBeVisible();
      expect(screen.getByText('user2@example.com')).toBeVisible();
      expect(screen.getByText('Member')).toBeVisible();
    });
  });

  it('allows_adding_team_member', async () => {
    // Mock the API endpoint for adding a team member
    server.use(
      rest.post('/api/projects/1/members', (req, res, ctx) => {
        const { email, role } = req.body as any;
        return res(ctx.status(200), ctx.json({ userId: 'newuser', role, user: { email } }));
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Select a project to enable the add member form
    const selectElement = screen.getByLabelText('Select Project');
    userEvent.selectOptions(selectElement, ['1']);

    // Wait for the component to update after project selection
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeVisible();
    });

    // Assert that the add member button is present
    expect(screen.getByText('Add Member')).toBeVisible();

    // Enter an email address
    const emailInput = screen.getByLabelText('Email Address');
    userEvent.type(emailInput, 'new.member@example.com');

    // Select a role from the dropdown
    const roleSelect = screen.getByLabelText('Role');
    userEvent.selectOptions(roleSelect, ['member']);

    // Submit the form
    const addButton = screen.getByText('Add Member');
    userEvent.click(addButton);

    // Wait for the new member to appear in the list
    await waitFor(() => {
      expect(screen.getByText('new.member@example.com')).toBeVisible();
    });
  });

  it('allows_changing_member_role', async () => {
    // Mock the API endpoint for updating a team member's role
    server.use(
      rest.put('/api/projects/1/members/user2', (req, res, ctx) => {
        const { role } = req.body as any;
        return res(ctx.status(200), ctx.json({ userId: 'user2', role }));
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Select a project to enable the member list
    const selectElement = screen.getByLabelText('Select Project');
    userEvent.selectOptions(selectElement, ['1']);

    // Wait for the component to update after project selection
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeVisible();
    });

    // Find the role selector for a member and change the role
    const roleSelect = await screen.findByDisplayValue('Member');
    userEvent.selectOptions(roleSelect, ['Admin']);

    // Wait for the UI to update and reflect the new role
    await waitFor(() => {
      expect(screen.getByDisplayValue('Admin')).toBeVisible();
    });
  });

  it('allows_removing_team_member', async () => {
    // Mock the API endpoint for removing a team member
    server.use(
      rest.delete('/api/projects/1/members/user2', (req, res, ctx) => {
        return res(ctx.status(204));
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Select a project to enable the member list
    const selectElement = screen.getByLabelText('Select Project');
    userEvent.selectOptions(selectElement, ['1']);

    // Wait for the component to update after project selection
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeVisible();
    });

    // Find the remove button for a member and click it
    const removeButton = await screen.findByRole('button', { name: 'Remove' });
    userEvent.click(removeButton);

    // Wait for the member to be removed from the list
    await waitFor(() => {
      expect(screen.queryByText('user2@example.com')).toBeNull();
    });
  });

  it('shows_error_messages', async () => {
    // Mock the API endpoint for adding a team member to simulate an error
    server.use(
      rest.post('/api/projects/1/members', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Failed to add team member' })
        );
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Select a project to enable the add member form
    const selectElement = screen.getByLabelText('Select Project');
    userEvent.selectOptions(selectElement, ['1']);

    // Wait for the component to update after project selection
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeVisible();
    });

    // Enter an invalid email address
    const emailInput = screen.getByLabelText('Email Address');
    userEvent.type(emailInput, 'invalid-email');

    // Select a role from the dropdown
    const roleSelect = screen.getByLabelText('Role');
    userEvent.selectOptions(roleSelect, ['member']);

    // Submit the form
    const addButton = screen.getByText('Add Member');
    userEvent.click(addButton);

    // Wait for the error message to appear
    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeVisible();
    });

    // Clear the email and submit the form without an email
    userEvent.clear(emailInput);
    userEvent.click(addButton);

    // Wait for the "required" error message to appear
    await waitFor(() => {
      expect(screen.getByText('Required')).toBeVisible();
    });

    // Enter a valid email and simulate API failure
    userEvent.type(emailInput, 'valid@example.com');
    server.use(
      rest.post('/api/projects/1/members', (req, res, ctx) => {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Failed to add team member' })
        );
      })
    );
    userEvent.click(addButton);

    // Wait for the API error message to appear
    await waitFor(() => {
      expect(screen.getByText('Failed to add team member')).toBeVisible();
    });
  });

  it('respects_permissions', async () => {
    // Mock the API endpoint for getting projects
    server.use(
      rest.get('/api/projects', (req, res, ctx) => {
        // Simulate a non-admin user
        const nonAdminProjects = mockProjects.filter(project => project.ownerId === 'user3');
        return res(ctx.status(200), ctx.json(nonAdminProjects));
      })
    );

    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Check that the project selector only shows projects the user has access to
    await waitFor(() => {
      expect(screen.queryByText('Project 1')).toBeNull();
      expect(screen.getByText('Project 2')).toBeVisible();
    });
  });

  it("can't_remove_yourself_from_team", async () => {
    // Render the TeamSettings component
    renderWithProviders(<TeamSettings />);

    // Select a project to enable the member list
    const selectElement = screen.getByLabelText('Select Project');
    userEvent.selectOptions(selectElement, ['1']);

    // Wait for the component to update after project selection
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeVisible();
    });

    // Find the remove button for the current user and check if it's disabled
    const removeButton = await screen.findByRole('button', { name: 'Remove' });
    expect(removeButton).toBeDisabled();
  });
});