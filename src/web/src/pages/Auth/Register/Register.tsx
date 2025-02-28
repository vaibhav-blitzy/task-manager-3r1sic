import React, { useState, useEffect } from 'react'; // react ^18.2.0
import { useNavigate, Link } from 'react-router-dom'; // react-router-dom ^6.0.0

// Import layout and form components
import AuthLayout from '../../../components/templates/AuthLayout/AuthLayout';
import { FormField } from '../../../components/molecules/FormField/FormField';
import { Input } from '../../../components/atoms/Input/Input';
import { Button } from '../../../components/atoms/Button/Button';

// Import hooks and utilities
import useAuth from '../../../api/hooks/useAuth';
import * as validate from '../../../utils/validation';
import { ROUTES } from '../../../routes/paths';
import { RegisterRequest } from '../../../types/auth';

/**
 * Registration page component that allows users to create a new account with
 * form validation and submission handling
 */
const Register: React.FC = () => {
  // Initialize form state
  const [form, setForm] = useState<RegisterRequest>({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: ''
  });

  // Initialize errors state to hold validation error messages
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Get auth-related functions and state from custom hook
  const { register, loading, error: authError } = useAuth();

  // Get navigation function for redirecting after successful registration
  const navigate = useNavigate();

  // Handle input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prevForm) => ({
      ...prevForm,
      [name]: value
    }));

    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prevErrors) => ({
        ...prevErrors,
        [name]: ''
      }));
    }
  };

  // Validate form fields
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validate first name
    if (!validate.isRequired(form.firstName)) {
      newErrors.firstName = 'First name is required';
    }

    // Validate last name
    if (!validate.isRequired(form.lastName)) {
      newErrors.lastName = 'Last name is required';
    }

    // Validate email
    if (!validate.isRequired(form.email)) {
      newErrors.email = 'Email is required';
    } else if (!validate.isEmailValid(form.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Validate password
    if (!validate.isRequired(form.password)) {
      newErrors.password = 'Password is required';
    } else if (!validate.isPasswordValid(form.password)) {
      newErrors.password = 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character';
    }

    // Validate confirm password
    if (!validate.isRequired(form.confirmPassword)) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (form.password !== form.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Update the errors state
    setErrors(newErrors);

    // Return true if no errors, false otherwise
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form before submitting
    if (!validateForm()) {
      return;
    }

    try {
      // Attempt registration with the provided form data
      await register(form);
      // On successful registration, navigation is handled by the useAuth hook
    } catch (error) {
      // Error handling is managed by the useAuth hook
      console.error('Registration error:', error);
    }
  };

  return (
    <AuthLayout title="Create an Account">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* First Name Field */}
          <FormField
            htmlFor="firstName"
            label="First Name"
            required
            error={errors.firstName}
          >
            <Input
              id="firstName"
              name="firstName"
              type="text"
              value={form.firstName}
              onChange={handleChange}
              placeholder="John"
              error={errors.firstName}
              disabled={loading}
            />
          </FormField>

          {/* Last Name Field */}
          <FormField
            htmlFor="lastName"
            label="Last Name"
            required
            error={errors.lastName}
          >
            <Input
              id="lastName"
              name="lastName"
              type="text"
              value={form.lastName}
              onChange={handleChange}
              placeholder="Doe"
              error={errors.lastName}
              disabled={loading}
            />
          </FormField>
        </div>

        {/* Email Field */}
        <FormField
          htmlFor="email"
          label="Email Address"
          required
          error={errors.email}
        >
          <Input
            id="email"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            placeholder="your.email@example.com"
            error={errors.email}
            disabled={loading}
          />
        </FormField>

        {/* Password Field */}
        <FormField
          htmlFor="password"
          label="Password"
          required
          error={errors.password}
          helperText="Must be at least 8 characters with uppercase, lowercase, number and special character"
        >
          <Input
            id="password"
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="••••••••••••"
            error={errors.password}
            disabled={loading}
          />
        </FormField>

        {/* Confirm Password Field */}
        <FormField
          htmlFor="confirmPassword"
          label="Confirm Password"
          required
          error={errors.confirmPassword}
        >
          <Input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={form.confirmPassword}
            onChange={handleChange}
            placeholder="••••••••••••"
            error={errors.confirmPassword}
            disabled={loading}
          />
        </FormField>

        {/* Display authentication error if any */}
        {authError && (
          <div className="mt-2 text-sm text-red-600" role="alert">
            {authError}
          </div>
        )}

        {/* Submit Button */}
        <div className="mt-6">
          <Button
            type="submit"
            isFullWidth
            isLoading={loading}
            disabled={loading}
          >
            Create Account
          </Button>
        </div>

        {/* Link to Login */}
        <div className="mt-4 text-center text-sm">
          Already have an account?{' '}
          <Link 
            to={ROUTES.LOGIN} 
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Sign in
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
};

export default Register;