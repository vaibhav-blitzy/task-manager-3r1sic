import React from 'react'; // react ^18.2.0
import { describe, it, expect, jest } from '@jest/globals'; // @jest/globals ^29.5.0

import ProjectCard from './ProjectCard';
import { Project, ProjectStatus } from '../../../types/project';
import { render, screen, fireEvent, waitFor, createMockProject } from '../../../utils/test-utils';

describe('ProjectCard', () => {
  // Define a mock project fixture using createMockProject
  const mockProject: Project = createMockProject({
    id: '1',
    name: 'Test Project',
    status: ProjectStatus.ACTIVE,
    description: 'This is a test project description.',
  });

  // Define a mock callback function using jest.fn()
  const mockOnClick = jest.fn();

  // Group tests by related functionality
  it('should render project name and status', async () => {
    // Render the ProjectCard component with a mock project
    render(<ProjectCard project={mockProject} />);

    // Assert that the project name is in the document
    expect(screen.getByText('Test Project')).toBeInTheDocument();

    // Assert that the project status badge is displayed correctly
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('should truncate description when it exceeds maxDescriptionLength', async () => {
    // Create a mock project with a long description
    const longDescriptionProject: Project = createMockProject({
      description: 'This is a very long test project description that exceeds the maximum length.',
    });

    // Render the ProjectCard with maxDescriptionLength set
    render(<ProjectCard project={longDescriptionProject} maxDescriptionLength={20} />);

    // Assert that the description is truncated to specified length with ellipsis
    expect(screen.getByText('This is a very long ...')).toBeInTheDocument();
  });

  it('should show progress bar when showProgress is true', async () => {
    // Create a mock project with task completion metadata
    const progressProject: Project = createMockProject({
      metadata: {
        created: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        completedAt: null,
        taskCount: 10,
        completedTaskCount: 5,
      },
    });

    // Render the ProjectCard with showProgress set to true
    render(<ProjectCard project={progressProject} showProgress />);

    // Assert that the progress bar is visible in the document
    expect(screen.getByText('Progress')).toBeInTheDocument();
  });

  it('should not show progress bar when showProgress is false', async () => {
    // Render the ProjectCard with showProgress set to false
    render(<ProjectCard project={mockProject} showProgress={false} />);

    // Assert that the progress bar is not in the document
    expect(screen.queryByText('Progress')).not.toBeInTheDocument();
  });

  it('should show team members when showMembers is true', async () => {
    // Create a mock project with team members
    const memberProject: Project = createMockProject({
      members: [
        { userId: '1', user: { id: '1', firstName: 'John', lastName: 'Doe', email: 'john.doe@example.com', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true, digest: { enabled: false, frequency: 'daily' } }, defaultView: 'board' }, security: { mfaEnabled: false, mfaMethod: 'app', lastLogin: new Date().toISOString(), lastPasswordChange: new Date().toISOString(), emailVerified: true }, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }, role: 'admin', joinedAt: new Date().toISOString(), isActive: true },
        { userId: '2', user: { id: '2', firstName: 'Jane', lastName: 'Smith', email: 'jane.smith@example.com', roles: [], status: 'active', organizations: [], settings: { language: 'en', theme: 'light', notifications: { email: true, push: false, inApp: true, digest: { enabled: false, frequency: 'daily' } }, defaultView: 'board' }, security: { mfaEnabled: false, mfaMethod: 'app', lastLogin: new Date().toISOString(), lastPasswordChange: new Date().toISOString(), emailVerified: true }, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }, role: 'member', joinedAt: new Date().toISOString(), isActive: true },
      ],
    });

    // Render the ProjectCard with showMembers set to true
    render(<ProjectCard project={memberProject} showMembers />);

    // Assert that member avatars are visible in the document
    expect(screen.getByAltText('John Doe')).toBeInTheDocument();
    expect(screen.getByAltText('Jane Smith')).toBeInTheDocument();
  });

  it('should not show team members when showMembers is false', async () => {
    // Render the ProjectCard with showMembers set to false
    render(<ProjectCard project={mockProject} showMembers={false} />);

    // Assert that member avatars are not in the document
    expect(screen.queryByAltText('John Doe')).not.toBeInTheDocument();
  });

  it('should show tags when showTags is true', async () => {
    // Create a mock project with tags
    const tagProject: Project = createMockProject({
      tags: ['frontend', 'react', 'ui'],
    });

    // Render the ProjectCard with showTags set to true
    render(<ProjectCard project={tagProject} showTags />);

    // Assert that tags are visible in the document
    expect(screen.getByText('frontend')).toBeInTheDocument();
    expect(screen.getByText('react')).toBeInTheDocument();
    expect(screen.getByText('ui')).toBeInTheDocument();
  });

  it('should not show tags when showTags is false', async () => {
    // Render the ProjectCard with showTags set to false
    render(<ProjectCard project={mockProject} showTags={false} />);

    // Assert that tags are not in the document
    expect(screen.queryByText('frontend')).not.toBeInTheDocument();
  });

  it('should apply selected className when selected prop is true', async () => {
    // Render the ProjectCard with selected set to true
    const { container } = render(<ProjectCard project={mockProject} selected />);

    // Assert that the card element has the selected class
    const cardElement = container.firstChild;
    expect(cardElement).toHaveClass('border-primary-500');
  });

  it('should call onClick when the card is clicked', async () => {
    // Create a mock function for onClick
    const onClick = jest.fn();

    // Render the ProjectCard with the mock onClick handler
    render(<ProjectCard project={mockProject} onClick={onClick} />);

    // Simulate clicking on the card
    fireEvent.click(screen.getByText('Test Project'));

    // Assert that the onClick function was called with the project object
    expect(onClick).toHaveBeenCalledWith(mockProject);
  });
});