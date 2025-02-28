import React, { useCallback } from 'react'; // react ^18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.8.0
import { useForm, SubmitHandler } from 'react-hook-form'; // react-hook-form ^7.43.0
import { toast } from 'react-hot-toast'; // react-hot-toast ^2.4.0

import { PATHS } from '../../../routes/paths';
import { TaskCreate, TaskPriority, TaskStatus } from '../../../types/task';
import { useTaskMutations } from '../../../api/hooks/useTasks';
import { useProjects } from '../../../api/hooks/useProjects';
import useAuth from '../../../api/hooks/useAuth';
import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import FormField from '../../../components/molecules/FormField/FormField';
import Button from '../../../components/atoms/Button/Button';
import DatePicker from '../../../components/atoms/DatePicker/DatePicker';
import FileUploader from '../../../components/organisms/FileUploader/FileUploader';

/**
 * Default form values for task creation
 */
const defaultFormValues = {
  title: '',
  description: '',
  dueDate: null,
  priority: TaskPriority.MEDIUM,
  projectId: '',
  assigneeId: ''
};

/**
 * Component for creating a new task with form validation and submission
 */
const TaskCreate: React.FC = () => {
  // Set up form handling with react-hook-form and default values
  const { register, handleSubmit, formState: { errors }, setValue } = useForm<TaskCreate>({
    defaultValues: defaultFormValues
  });

  // Initialize navigation hook for redirecting after task creation
  const navigate = useNavigate();

  // Get current authenticated user with useAuth hook
  const { user } = useAuth();

  // Fetch available projects with useProjects hook
  const { projects, isLoading: isProjectsLoading } = useProjects();

  // Get task creation mutation function with useTaskMutations
  const { createTask, isLoading: isCreating } = useTaskMutations();

  /**
   * Define form submission handler to create new task
   * @param data Form data from react-hook-form
   */
  const onSubmit: SubmitHandler<TaskCreate> = async (data: TaskCreate) => {
    try {
      // Ensure that the status is always 'created' when creating a task
      const taskData: TaskCreate = {
        ...data,
        status: TaskStatus.CREATED, // Set initial status to 'created'
        tags: [] // Initialize tags as an empty array
      };
      
      // Call the createTask mutation to create the task
      createTask.mutate(taskData);

      // Show success toast notification after successful creation
      toast.success('Task created successfully!');

      // Navigate to tasks list page after successful submission
      navigate(PATHS.TASKS);
    } catch (error: any) {
      // Handle errors during task creation
      toast.error(`Failed to create task: ${error.message}`);
    }
  };

  // Handle validation with required fields (title, priority)
  const titleError = errors.title ? 'Task title is required' : undefined;
  const priorityError = errors.priority ? 'Task priority is required' : undefined;

  // Set up file attachment handling logic
  const handleFileUpload = (file: File) => {
    // Implement file upload logic here
    console.log('Uploaded file:', file);
  };

  // Render task creation form inside DashboardLayout
  return (
    <DashboardLayout title="Create Task">
      <form onSubmit={handleSubmit(onSubmit)} className="max-w-lg mx-auto">
        {/* Task Title */}
        <FormField
          label="Task Title"
          htmlFor="title"
          required
          error={titleError}
        >
          <input
            type="text"
            id="title"
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register("title", { required: true })}
          />
        </FormField>

        {/* Task Description */}
        <FormField label="Description" htmlFor="description">
          <textarea
            id="description"
            rows={3}
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register("description")}
          />
        </FormField>

        {/* Due Date */}
        <FormField label="Due Date" htmlFor="dueDate">
          <DatePicker
            id="dueDate"
            name="dueDate"
            placeholder="Select due date"
            onChange={(date: Date | null) => setValue('dueDate', date ? date.toISOString() : null)}
          />
        </FormField>

        {/* Priority */}
        <FormField label="Priority" htmlFor="priority" required error={priorityError}>
          <select
            id="priority"
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register("priority", { required: true })}
          >
            <option value={TaskPriority.LOW}>Low</option>
            <option value={TaskPriority.MEDIUM}>Medium</option>
            <option value={TaskPriority.HIGH}>High</option>
            <option value={TaskPriority.URGENT}>Urgent</option>
          </select>
        </FormField>

        {/* Project */}
        <FormField label="Project" htmlFor="projectId">
          <select
            id="projectId"
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register("projectId")}
            disabled={isProjectsLoading}
          >
            <option value="">No Project</option>
            {projects &&
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
          </select>
        </FormField>

        {/* Assignee */}
        <FormField label="Assignee" htmlFor="assigneeId">
          <select
            id="assigneeId"
            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
            {...register("assigneeId")}
          >
            <option value="">Unassigned</option>
            {/* Implement user list fetching and mapping here */}
          </select>
        </FormField>

        {/* File Upload */}
        <FormField label="Attachments" htmlFor="attachments">
          <FileUploader
            taskId={undefined}
            projectId={undefined}
            commentId={undefined}
            onUploadComplete={handleFileUpload}
          />
        </FormField>

        {/* Form Submission */}
        <div className="flex justify-end mt-6">
          <Button
            type="submit"
            variant="primary"
            isLoading={isCreating}
          >
            Create Task
          </Button>
        </div>
      </form>
    </DashboardLayout>
  );
};

export default TaskCreate;