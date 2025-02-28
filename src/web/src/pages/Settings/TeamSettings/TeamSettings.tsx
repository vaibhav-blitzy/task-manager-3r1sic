import React, { useState, useEffect, useCallback } from 'react';
import { Field, Form, Formik } from 'formik';
import toast from 'react-hot-toast';

import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import { Button } from '../../../components/atoms/Button/Button';
import FormField from '../../../components/molecules/FormField/FormField';
import { useProjects } from '../../../api/hooks/useProjects';
import { useAppSelector, useAppDispatch } from '../../../store/hooks';
import { User } from '../../../types/user';
import { Project, ProjectMember } from '../../../types/project';
import { hasPermission } from '../../../utils/permissions';

/**
 * TeamSettings component provides an interface for managing team members and their roles
 * within projects or organizations in the task management system.
 */
const TeamSettings: React.FC = () => {
  // State for selected project
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  
  // Get the current user from Redux store
  const currentUser = useAppSelector(state => state.auth.user);
  
  // Get user's projects
  const { projects, isLoading: projectsLoading } = useProjects();
  
  // Custom hook for team management
  const { 
    members, 
    isLoading, 
    addMember, 
    updateMemberRole, 
    removeMember 
  } = useTeamManagement(selectedProject);
  
  // Filter projects the user can manage
  const manageableProjects = projects.filter(project => {
    if (!currentUser) return false;
    
    // User is project owner
    if (project.ownerId === currentUser.id) return true;
    
    // User has admin or manager role
    const userMember = project.members.find(m => m.userId === currentUser.id);
    if (userMember && ['admin', 'manager'].includes(userMember.role)) return true;
    
    // User has team management permission
    return hasPermission(currentUser, 'team', 'update');
  });
  
  // Handle project selection
  const handleProjectChange = (projectId: string) => {
    if (!projectId) {
      setSelectedProject(null);
      return;
    }
    
    const project = projects.find(p => p.id === projectId);
    setSelectedProject(project || null);
  };
  
  return (
    <DashboardLayout title="Team Settings">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Team Management</h2>
        
        {/* Project selection dropdown */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Select Project
          </label>
          <select 
            className="form-select block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            onChange={(e) => handleProjectChange(e.target.value)}
            value={selectedProject?.id || ''}
            disabled={projectsLoading}
          >
            <option value="">Select a project</option>
            {manageableProjects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
        
        {projectsLoading && (
          <div className="text-center py-4">
            <p className="text-gray-600 dark:text-gray-400">Loading projects...</p>
          </div>
        )}
        
        {!projectsLoading && manageableProjects.length === 0 && (
          <div className="text-center py-4">
            <p className="text-gray-600 dark:text-gray-400">
              You don't have any projects where you can manage team members.
            </p>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              To manage team members, you need to be a project owner, admin, or manager.
            </p>
          </div>
        )}
        
        {selectedProject && (
          <>
            {isLoading ? (
              <div className="text-center py-4">
                <p className="text-gray-600 dark:text-gray-400">Loading team members...</p>
              </div>
            ) : (
              <>
                {/* Member list */}
                <MemberList 
                  members={members} 
                  onRoleChange={updateMemberRole}
                  onRemoveMember={removeMember}
                  currentUserId={currentUser?.id}
                />
                
                {/* Add member form */}
                <AddMemberForm onAddMember={addMember} />
              </>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

/**
 * Custom hook that handles team member addition, removal, and role updates
 * 
 * @param selectedProject - The currently selected project
 * @returns Functions and data for team management
 */
function useTeamManagement(selectedProject: Project | null) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use useProjects hook for accessing project data
  const { projects, refetch: refetchProjects } = useProjects();
  
  // Load project members when a project is selected
  useEffect(() => {
    if (selectedProject) {
      setIsLoading(true);
      
      // In a real implementation, we would fetch members from the API
      // Here we're using the members directly from the project object
      setTimeout(() => {
        setMembers(selectedProject.members || []);
        setIsLoading(false);
      }, 500); // Simulate loading
    } else {
      setMembers([]);
    }
  }, [selectedProject]);
  
  // Add a new member to the team
  const addMember = useCallback((email: string, role: string) => {
    if (!selectedProject) return;
    
    setIsLoading(true);
    
    // In a real implementation, this would call an API
    // Here we're simulating success after a delay
    setTimeout(() => {
      // Create a fake new member for demonstration
      const newMember: ProjectMember = {
        userId: `user-${Date.now()}`,
        user: {
          id: `user-${Date.now()}`,
          email,
          firstName: email.split('@')[0],
          lastName: '',
          roles: ['user'],
          organizations: [],
          settings: {
            language: 'en',
            theme: 'light',
            notifications: {
              email: true,
              push: false,
              inApp: true
            }
          },
          security: {
            mfaEnabled: false,
            mfaMethod: '',
            lastLogin: new Date().toISOString(),
            lastPasswordChange: new Date().toISOString(),
            emailVerified: true
          },
          status: 'active',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        } as User,
        role,
        joinedAt: new Date().toISOString(),
        isActive: true
      };
      
      setMembers(prev => [...prev, newMember]);
      setIsLoading(false);
      toast.success(`Added ${email} as ${role}`);
    }, 1000);
  }, [selectedProject]);
  
  // Update a member's role
  const updateMemberRole = useCallback((userId: string, newRole: string) => {
    if (!selectedProject) return;
    
    setIsLoading(true);
    
    // In a real implementation, this would call an API
    setTimeout(() => {
      setMembers(prev => 
        prev.map(member => 
          member.userId === userId 
            ? { ...member, role: newRole } 
            : member
        )
      );
      setIsLoading(false);
      toast.success(`Updated member role to ${newRole}`);
    }, 500);
  }, [selectedProject]);
  
  // Remove a member from the team
  const removeMember = useCallback((userId: string) => {
    if (!selectedProject) return;
    
    setIsLoading(true);
    
    // In a real implementation, this would call an API
    setTimeout(() => {
      setMembers(prev => prev.filter(member => member.userId !== userId));
      setIsLoading(false);
      toast.success('Team member removed');
    }, 500);
  }, [selectedProject]);
  
  return {
    members,
    isLoading,
    error,
    addMember,
    updateMemberRole,
    removeMember
  };
}

// Helper component to display the list of team members
interface MemberListProps {
  members: ProjectMember[];
  onRoleChange: (userId: string, role: string) => void;
  onRemoveMember: (userId: string) => void;
  currentUserId?: string;
}

const MemberList: React.FC<MemberListProps> = ({ 
  members, 
  onRoleChange, 
  onRemoveMember,
  currentUserId
}) => {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">Team Members</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-gray-700 dark:text-gray-300">
          <thead className="text-xs text-gray-700 dark:text-gray-300 uppercase bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.length > 0 ? (
              members.map(member => (
                <tr key={member.userId} className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <td className="px-4 py-3">
                    {member.user.firstName} {member.user.lastName}
                  </td>
                  <td className="px-4 py-3">{member.user.email}</td>
                  <td className="px-4 py-3">
                    <RoleSelector 
                      currentRole={member.role} 
                      onChange={(role) => onRoleChange(member.userId, role)}
                      disabled={member.userId === currentUserId} // Can't change own role
                    />
                  </td>
                  <td className="px-4 py-3">
                    <Button 
                      variant="danger" 
                      size="sm"
                      onClick={() => onRemoveMember(member.userId)}
                      disabled={member.userId === currentUserId} // Can't remove self
                    >
                      Remove
                    </Button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                  No team members found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Role selector dropdown component
interface RoleSelectorProps {
  currentRole: string;
  onChange: (role: string) => void;
  disabled?: boolean;
}

const RoleSelector: React.FC<RoleSelectorProps> = ({ 
  currentRole, 
  onChange, 
  disabled = false 
}) => {
  return (
    <select
      className="form-select block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white py-2 px-3 text-sm"
      value={currentRole}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    >
      <option value="admin">Admin</option>
      <option value="manager">Manager</option>
      <option value="member">Member</option>
      <option value="viewer">Viewer</option>
    </select>
  );
};

// Form to add new team members
interface AddMemberFormProps {
  onAddMember: (email: string, role: string) => void;
}

const AddMemberForm: React.FC<AddMemberFormProps> = ({ onAddMember }) => {
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-6">
      <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">Add Team Member</h3>
      <Formik
        initialValues={{ email: '', role: 'member' }}
        validate={values => {
          const errors: { email?: string } = {};
          if (!values.email) {
            errors.email = 'Required';
          } else if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(values.email)) {
            errors.email = 'Invalid email address';
          }
          return errors;
        }}
        onSubmit={(values, { resetForm, setSubmitting }) => {
          onAddMember(values.email, values.role);
          resetForm();
          // Delay resetting submitting to allow form to complete
          setTimeout(() => setSubmitting(false), 1000);
        }}
      >
        {({ isSubmitting, errors, touched }) => (
          <Form className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <FormField
                  label="Email Address"
                  htmlFor="email"
                  required
                  error={touched.email && errors.email}
                >
                  <Field
                    type="email"
                    name="email"
                    id="email"
                    className="form-input block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="team.member@example.com"
                    disabled={isSubmitting}
                  />
                </FormField>
              </div>
              <div>
                <FormField
                  label="Role"
                  htmlFor="role"
                  required
                >
                  <Field
                    as="select"
                    name="role"
                    id="role"
                    className="form-select block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    disabled={isSubmitting}
                  >
                    <option value="admin">Admin</option>
                    <option value="manager">Manager</option>
                    <option value="member">Member</option>
                    <option value="viewer">Viewer</option>
                  </Field>
                </FormField>
              </div>
            </div>
            <div className="flex justify-end">
              <Button
                type="submit"
                variant="primary"
                isLoading={isSubmitting}
                disabled={isSubmitting}
              >
                Add Member
              </Button>
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
};

export default TeamSettings;