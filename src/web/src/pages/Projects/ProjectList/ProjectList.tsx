import React, { useState, useCallback, useEffect } from 'react'; // react ^18.2.x
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.x
import { Plus } from 'react-feather'; // react-feather ^2.0.x
import classNames from 'classnames';
import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import Button from '../../../components/atoms/Button/Button';
import SearchBar from '../../../components/molecules/SearchBar/SearchBar';
import ProjectCard from '../../../components/organisms/ProjectCard/ProjectCard';
import { useProjects } from '../../../api/hooks/useProjects';
import useAuth from '../../../api/hooks/useAuth';
import { Project, ProjectFilter } from '../../../types/project';
import { PATHS } from '../../../routes/paths';
import { hasPermission } from '../../../utils/permissions';

/**
 * Component for displaying a list of projects with filtering, searching, and creation capabilities
 */
const ProjectList: React.FC = () => {
  // LD1: Set up state for search query and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<ProjectFilter>({});

  // LD1: Use useNavigate hook for programmatic navigation
  const navigate = useNavigate();

  // LD1: Use useAuth hook to get current user and authentication status
  const { user } = useAuth();

  // LD1: Use useProjects hook to fetch projects with query parameters
  const {
    projects,
    isLoading,
    error,
    pagination,
  } = useProjects(filters);

  // LD1: Check if the user has permission to create projects
  const canCreateProject = hasPermission(user, 'project', 'create');

  // LD1: Handle search input changes and reset pagination when search changes
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setFilters(prevFilters => ({ ...prevFilters, searchTerm: query }));
    pagination.goToPage(1); // Reset to first page when searching
  };

  // LD1: Implement handleCreateProject function to navigate to project creation page
  const handleCreateProject = () => {
    navigate(PATHS.PROJECT_CREATE);
  };

  // LD1: Implement handleProjectClick function to navigate to project details page
  const handleProjectClick = (project: Project) => {
    navigate(PATHS.PROJECT_DETAIL.replace(':id', project.id));
  };

  // LD1: Render empty state component
  const renderEmptyState = () => {
    if (searchQuery) {
      return (
        <div className="text-center mt-8">
          <p className="text-gray-500">No projects found matching your search.</p>
        </div>
      );
    } else {
      return (
        <div className="text-center mt-8">
          <p className="text-gray-500">No projects found.</p>
          {canCreateProject && (
            <Button variant="primary" onClick={handleCreateProject} className="mt-4">
              Create New Project
            </Button>
          )}
        </div>
      );
    }
  };

  // LD1: Include class names for responsive grid layout
  return (
    <DashboardLayout title="Projects">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          {/* LD1: Render header section with search bar and create button (if user has permission) */}
          <SearchBar placeholder="Search projects..." onSearch={handleSearch} className="max-w-md" />
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          {canCreateProject && (
            <Button variant="primary" onClick={handleCreateProject}>
              <Plus className="mr-2" size={16} />
              Create Project
            </Button>
          )}
        </div>
      </div>

      <div className="mt-6">
        {/* LD1: Handle loading state with appropriate loading indicator */}
        {isLoading && <p>Loading projects...</p>}

        {/* LD1: Handle error state with error message */}
        {error && <p className="text-red-500">Error: {error.message}</p>}

        {/* LD1: Render projects grid using ProjectCard components */}
        {!isLoading && !error && projects.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => handleProjectClick(project)}
              />
            ))}
          </div>
        ) : (
          // LD1: Show empty state message when no projects are found
          renderEmptyState()
        )}
      </div>
    </DashboardLayout>
  );
};

export default ProjectList;