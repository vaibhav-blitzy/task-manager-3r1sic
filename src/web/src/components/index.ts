/**
 * src/web/src/components/index.ts
 *
 * Main entry point for exporting all React components in the component library,
 * organized by atomic design principles (atoms, molecules, organisms, templates)
 * and mobile-specific components.
 *
 * This file serves as a central module for importing and re-exporting components,
 * simplifying component imports throughout the application.
 */

// ==================== Atoms ====================
// Export atom components
export { default as Avatar } from './atoms/Avatar/Avatar'; // Atom component for displaying user avatars
export { default as Badge } from './atoms/Badge/Badge'; // Atom component for displaying status badges
export { Button } from './atoms/Button/Button'; // Atom component for interactive buttons
export { Checkbox } from './atoms/Checkbox/Checkbox'; // Atom component for checkbox inputs
export { default as DatePicker } from './atoms/DatePicker/DatePicker'; // Atom component for date selection
export { default as Icon } from './atoms/Icon/Icon'; // Atom component for displaying icons
export { default as Input } from './atoms/Input/Input'; // Atom component for text input fields
export { default as Label } from './atoms/Label/Label'; // Atom component for form labels

// ==================== Molecules ====================
// Export molecule components
export { default as CommentItem } from './molecules/CommentItem/CommentItem'; // Molecule component for displaying individual comments
export { default as FileAttachment } from './molecules/FileAttachment/FileAttachment'; // Molecule component for displaying file attachments
export { default as FormField } from './molecules/FormField/FormField'; // Molecule component for form field groups
export { default as Notification } from './molecules/Notification/Notification'; // Molecule component for displaying notification messages
export { default as SearchBar } from './molecules/SearchBar/SearchBar'; // Molecule component for search functionality
export { default as StatusBadge } from './molecules/StatusBadge/StatusBadge'; // Molecule component for displaying task status
export { default as TaskCard } from './molecules/TaskCard/TaskCard'; // Molecule component for displaying task cards

// ==================== Organisms ====================
// Export organism components
export { default as BarChart } from './organisms/Charts/BarChart/BarChart'; // Organism component for bar chart visualization
export { default as LineChart } from './organisms/Charts/LineChart/LineChart'; // Organism component for line chart visualization
export { default as PieChart } from './organisms/Charts/PieChart/PieChart'; // Organism component for pie chart visualization
export { default as CommentSection } from './organisms/CommentSection/CommentSection'; // Organism component for comment sections in tasks
export { default as FileUploader } from './organisms/FileUploader/FileUploader'; // Organism component for file uploads
export { default as NavigationMenu } from './organisms/NavigationMenu/NavigationMenu'; // Organism component for main navigation
export { default as ProjectCard } from './organisms/ProjectCard/ProjectCard'; // Organism component for displaying project cards
export { default as TaskBoard } from './organisms/TaskBoard/TaskBoard'; // Organism component for kanban-style task boards
export { default as TaskList } from './organisms/TaskList/TaskList'; // Organism component for displaying task lists
export { default as UserDropdown } from './organisms/UserDropdown/UserDropdown'; // Organism component for user dropdown menus

// ==================== Templates ====================
// Export template components
export { default as AuthLayout } from './templates/AuthLayout/AuthLayout'; // Template component for authentication page layouts
export { default as DashboardLayout } from './templates/DashboardLayout/DashboardLayout'; // Template component for dashboard page layouts
export { default as ProjectLayout } from './templates/ProjectLayout/ProjectLayout'; // Template component for project page layouts

// ==================== Mobile-Specific Components ====================
// Export mobile-specific components
export { default as BottomNavigation } from './mobile/BottomNavigation/BottomNavigation'; // Mobile component for bottom navigation bars
export { default as MobileTaskCard } from './mobile/MobileTaskCard/MobileTaskCard'; // Mobile component for displaying task cards on small screens