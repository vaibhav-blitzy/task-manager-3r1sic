import { createSlice, PayloadAction } from '@reduxjs/toolkit'; // v1.9.x
import { ThemeType } from '../../config/themes';

// Define the interface for UI state
interface UIState {
  theme: ThemeType;
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  modal: {
    isOpen: boolean;
    type: string | null;
    data: any;
  };
}

// Interface for modal payload
interface ModalPayload {
  type: string;
  data?: any;
}

// For TypeScript type safety - in a real app this would be imported from the store
type RootState = {
  ui: UIState;
  // other slices would be defined here
};

// Define the initial state
const initialState: UIState = {
  theme: 'light',
  sidebarOpen: true,
  mobileMenuOpen: false,
  modal: {
    isOpen: false,
    type: null,
    data: null
  }
};

// Create the UI slice
export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Toggle between light and dark themes
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    
    // Set theme to specific value
    setTheme: (state, action: PayloadAction<ThemeType>) => {
      state.theme = action.payload;
    },
    
    // Toggle sidebar open/closed
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    
    // Set sidebar to specific state
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    
    // Toggle mobile menu open/closed
    toggleMobileMenu: (state) => {
      state.mobileMenuOpen = !state.mobileMenuOpen;
    },
    
    // Set mobile menu to specific state
    setMobileMenuOpen: (state, action: PayloadAction<boolean>) => {
      state.mobileMenuOpen = action.payload;
    },
    
    // Open modal with type and data
    openModal: (state, action: PayloadAction<ModalPayload>) => {
      state.modal.isOpen = true;
      state.modal.type = action.payload.type;
      state.modal.data = action.payload.data || null;
    },
    
    // Close current modal
    closeModal: (state) => {
      state.modal.isOpen = false;
      state.modal.type = null;
      state.modal.data = null;
    }
  }
});

// Export actions
export const uiActions = uiSlice.actions;

// Define selectors using RootState type
export const selectTheme = (state: RootState) => state.ui.theme;
export const selectSidebarOpen = (state: RootState) => state.ui.sidebarOpen;
export const selectMobileMenuOpen = (state: RootState) => state.ui.mobileMenuOpen;
export const selectModal = (state: RootState) => state.ui.modal;

// Export reducer as default
export default uiSlice.reducer;