import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify'; // react-toastify ^9.1.3

import AuthLayout from '../../../components/templates/AuthLayout/AuthLayout';
import { Button } from '../../../components/atoms/Button/Button';
import FormField from '../../../components/molecules/FormField/FormField';
import { validateEmail } from '../../../utils/validation';
import { paths } from '../../../routes/paths';
import { forgotPassword } from '../../../api/services/authService';

/**
 * ForgotPassword component that allows users to request a password reset link
 * via email if they've forgotten their password.
 */
const ForgotPassword: React.FC = () => {
  // State for the email input
  const [email, setEmail] = useState('');
  
  // State for form submission status
  const [formState, setFormState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  
  // State for validation errors
  const [errors, setErrors] = useState<{
    email?: string;
  }>({});
  
  // Navigation hook for redirecting after success
  const navigate = useNavigate();
  
  /**
   * Handles form submission, validates the input and calls the API
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Validate email format
    if (!validateEmail(email)) {
      setErrors({ email: 'Please enter a valid email address' });
      return;
    }
    
    setFormState('submitting');
    
    try {
      // Call the API to request password reset
      await forgotPassword({ email });
      
      // Show success message
      toast.success('Password reset link has been sent to your email');
      setFormState('success');
      
      // After a delay, redirect to login page
      setTimeout(() => {
        navigate(paths.login);
      }, 3000);
    } catch (error) {
      console.error('Password reset request failed', error);
      toast.error('Failed to send password reset link. Please try again.');
      setFormState('error');
    } finally {
      setFormState('idle');
    }
  };
  
  /**
   * Updates email state and clears validation errors
   */
  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target;
    setEmail(value);
    
    // Clear any existing email validation errors
    if (errors.email) {
      setErrors({ ...errors, email: undefined });
    }
  };
  
  return (
    <AuthLayout title="Forgot Password">
      {formState === 'success' ? (
        <div className="text-center">
          <div className="mb-6">
            <svg 
              className="mx-auto h-12 w-12 text-green-500" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Recovery email sent</h3>
          <p className="mb-4 text-gray-600">We've sent a password reset link to <strong>{email}</strong>.</p>
          <p className="mb-4 text-gray-600">Please check your email and follow the instructions to reset your password.</p>
          <p className="text-sm text-gray-500">Redirecting you to login page...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <p className="text-sm text-gray-600 mb-4">
            Enter your email address below and we'll send you a link to reset your password.
          </p>
          
          <FormField
            label="Email Address"
            htmlFor="email"
            required
            error={errors.email}
          >
            <input
              id="email"
              type="email"
              value={email}
              onChange={handleEmailChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              placeholder="your.email@example.com"
              required
              disabled={formState === 'submitting'}
            />
          </FormField>
          
          <div className="mt-6">
            <Button
              type="submit"
              variant="primary"
              isFullWidth
              isLoading={formState === 'submitting'}
              disabled={formState === 'submitting'}
            >
              Send Reset Link
            </Button>
          </div>
          
          <div className="mt-4 text-center">
            <Link to={paths.login} className="text-sm text-primary-600 hover:text-primary-500">
              Return to Login
            </Link>
          </div>
        </form>
      )}
    </AuthLayout>
  );
};

export default ForgotPassword;