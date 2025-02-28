import { createSlice, PayloadAction } from '@reduxjs/toolkit'; // @reduxjs/toolkit v1.9.x
import { Project, ProjectMember } from '../../types/project';

/**
 * Interface representing the project state in the Redux store
 */
interface ProjectState {
  projects: Project[];
  selectedProjectId: string | null;
  loading: boolean;
  error: string | null;
}

/**
 * Initial state for the project slice
 */
const initialState: ProjectState = {
  projects: [],
  selectedProjectId: null,
  loading: false,
  error: null
};

/**
 * Redux Toolkit slice for managing project state
 */
const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    setProjects: (state, action: PayloadAction<Project[]>) => {
      state.projects = action.payload;
    },
    addProject: (state, action: PayloadAction<Project>) => {
      state.projects.push(action.payload);
    },
    updateProject: (state, action: PayloadAction<Project>) => {
      const index = state.projects.findIndex(p => p.id === action.payload.id);
      if (index !== -1) {
        state.projects[index] = action.payload;
      }
    },
    removeProject: (state, action: PayloadAction<string>) => {
      state.projects = state.projects.filter(p => p.id !== action.payload);
      if (state.selectedProjectId === action.payload) {
        state.selectedProjectId = null;
      }
    },
    setSelectedProject: (state, action: PayloadAction<string | null>) => {
      state.selectedProjectId = action.payload;
    },
    addProjectMember: (state, action: PayloadAction<{ projectId: string; member: ProjectMember }>) => {
      const { projectId, member } = action.payload;
      const project = state.projects.find(p => p.id === projectId);
      if (project) {
        project.members.push(member);
      }
    },
    removeProjectMember: (state, action: PayloadAction<{ projectId: string; userId: string }>) => {
      const { projectId, userId } = action.payload;
      const project = state.projects.find(p => p.id === projectId);
      if (project) {
        project.members = project.members.filter(m => m.user.id !== userId);
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    }
  }
});

// Extract action creators and reducer
export const { 
  setProjects, 
  addProject, 
  updateProject, 
  removeProject, 
  setSelectedProject, 
  addProjectMember, 
  removeProjectMember, 
  setLoading, 
  setError 
} = projectSlice.actions;

// Export the reducer
export const projectReducer = projectSlice.reducer;

/**
 * Selector to get all projects from state
 */
export const selectProjects = (state: RootState) => state.project.projects;

/**
 * Selector to get the currently selected project
 */
export const selectSelectedProject = (state: RootState) => {
  const { selectedProjectId, projects } = state.project;
  if (!selectedProjectId) return null;
  return projects.find(project => project.id === selectedProjectId) || null;
};

/**
 * Selector to get loading state
 */
export const selectProjectLoading = (state: RootState) => state.project.loading;

/**
 * Selector to get error state
 */
export const selectProjectError = (state: RootState) => state.project.error;