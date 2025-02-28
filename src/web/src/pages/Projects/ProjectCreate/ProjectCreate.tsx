import React, { useState } from 'react'; // react v18.2.x
import { useNavigate } from 'react-router-dom'; // react-router-dom v6.15.x
import { toast } from 'react-toastify'; // react-toastify v9.1.x

import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import FormField from '../../../components/molecules/FormField/FormField';
import Input from '../../../components/atoms/Input/Input';
import Button from '../../../components/atoms/Button/Button';
import { useProjectMutation } from '../../../api/hooks/useProjects';
import { ProjectStatus, ProjectFormData } from '../../../types/project';
import { validateProjectInput } from '../../../utils/validation';
import { PATHS } from '../../../routes/paths';

// Define initial project data
const initialProjectData: ProjectFormData = {
  name: '',
  description: '',
  status: ProjectStatus.PLANNING,
  category: '',
  tags: []
};

/**
 * Component for creating new projects with form validation and submission handling
 */
const ProjectCreate: React.FC = () => {
  // Initialize state for form data
  const [projectData, setProjectData] = useState<ProjectFormData>(initialProjectData);
  
  // Initialize state for validation errors
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  
  // Initialize state for form submission status
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Get navigation function from useNavigate hook
  const navigate = useNavigate();
  
  // Get project mutation functions from useProjectMutation hook
  const { createProject: { mutate: createProjectMutation, isLoading } } = useProjectMutation();

  /**
   * Function to handle input changes and update the form data state
   * @param e - The input change event
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProjectData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  /**
   * Function to handle form submission
   * @param e - The form submit event
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Implement validation using validateProjectInput utility
    const validationResult = validateProjectInput(projectData);

    // Show validation errors if validation fails
    if (!validationResult.isValid) {
      setErrors(validationResult.errors);
      setIsSubmitting(false);
      return;
    }

    // Clear any previous errors
    setErrors({});

    // Call createProject mutation function with validated form data
    createProjectMutation(projectData, {
      onSuccess: () => {
        // Handle success by showing toast notification and navigating to projects list
        toast.success('Project created successfully!');
        navigate(PATHS.PROJECTS);
      },
      onError: (error: any) => {
        // Handle errors by showing error toast notification
        toast.error(`Failed to create project: ${error.message || 'An unexpected error occurred.'}`);
      },
      onSettled: () => {
        setIsSubmitting(false);
      }
    });
  };

  return (
    <DashboardLayout title="Create New Project">
      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
        {/* Project Name */}
        <FormField
          label="Project Name"
          htmlFor="name"
          required
          error={errors.name}
        >
          <Input
            type="text"
            id="name"
            name="name"
            value={projectData.name}
            onChange={handleInputChange}
            placeholder="Enter project name"
            aria-required="true"
          />
        </FormField>

        {/* Project Description */}
        <FormField
          label="Description"
          htmlFor="description"
        >
          <Input
            type="text"
            id="description"
            name="description"
            value={projectData.description}
            onChange={handleInputChange}
            placeholder="Enter project description"
          />
        </FormField>

        {/* Project Status */}
        <FormField
          label="Status"
          htmlFor="status"
        >
          <select
            id="status"
            name="status"
            value={projectData.status}
            onChange={handleInputChange}
            className="w-full border rounded px-3 py-2"
          >
            <option value={ProjectStatus.PLANNING}>Planning</option>
            <option value={ProjectStatus.ACTIVE}>Active</option>
            <option value={ProjectStatus.ON_HOLD}>On Hold</option>
            <option value={ProjectStatus.COMPLETED}>Completed</option>
            <option value={ProjectStatus.ARCHIVED}>Archived</option>
          </select>
        </FormField>

        {/* Project Category */}
        <FormField
          label="Category"
          htmlFor="category"
        >
          <Input
            type="text"
            id="category"
            name="category"
            value={projectData.category}
            onChange={handleInputChange}
            placeholder="Enter project category"
          />
        </FormField>

        {/* Project Tags */}
        <FormField
          label="Tags"
          htmlFor="tags"
        >
          <Input
            type="text"
            id="tags"
            name="tags"
            value={projectData.tags ? projectData.tags.join(', ') : ''}
            onChange={e => {
              const tags = e.target.value.split(',').map(tag => tag.trim());
              setProjectData(prevData => ({ ...prevData, tags }));
            }}
            placeholder="Enter project tags (comma separated)"
          />
        </FormField>

        {/* Submit and Cancel Buttons */}
        <div className="flex justify-end mt-6">
          <Button
            variant="outline"
            onClick={() => navigate(PATHS.PROJECTS)}
            disabled={isSubmitting}
            className="mr-4"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || isLoading}
          >
            {isLoading ? 'Creating...' : 'Create Project'}
          </Button>
        </div>
      </form>
    </DashboardLayout>
  );
};

export default ProjectCreate;