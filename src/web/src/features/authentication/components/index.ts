/**
 * Authentication Components Barrel File
 * 
 * Centralizes the export of authentication-related React components for easy importing
 * throughout the application. This pattern improves code organization and maintainability
 * by providing a single import point for all authentication UI components.
 * 
 * @version 1.0.0
 */

// Import authentication-related components
import Login from '../../../pages/Auth/Login/Login';
import Register from '../../../pages/Auth/Register/Register';
import ForgotPassword from '../../../pages/Auth/ForgotPassword/ForgotPassword';

// Export individual components as named exports for selective importing
export { Login, Register, ForgotPassword };

// Export consolidated object containing all authentication components
const AuthComponents = {
  Login,
  Register,
  ForgotPassword
};

export default AuthComponents;