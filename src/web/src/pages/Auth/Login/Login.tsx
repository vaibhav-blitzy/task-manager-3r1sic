import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // react-router-dom ^6.0.0
import { useForm } from 'react-hook-form'; // react-hook-form 7.46.x
import { yupResolver } from '@hookform/resolvers/yup'; // @hookform/resolvers/yup ^3.0.0
import * as yup from 'yup'; // yup ^1.0.0

import useAuth from '../../../api/hooks/useAuth';
import AuthLayout from '../../../components/templates/AuthLayout/AuthLayout';
import FormField from '../../../components/molecules/FormField/FormField';
import Button from '../../../components/atoms/Button/Button';
import { Checkbox } from '../../../components/atoms/Checkbox/Checkbox';
import { PATHS } from '../../../routes/paths';
import { LoginCredentials } from '../../../types/auth';
import useLocalStorage from '../../../hooks/useLocalStorage';

// Validation schema for the login form
const validationSchema = yup.object({
  email: yup.string().required('Email is required').email('Invalid email format'),
  password: yup.string().required('Password is required').min(8, 'Password must be at least 8 characters'),
  rememberMe: yup.boolean().optional()
});

/**
 * Login page component that handles user authentication through a form,
 * form validation, error handling, and redirection after successful login.
 */
const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading, error, mfaRequired } = useAuth();
  const [rememberMe, setRememberMe] = useLocalStorage<boolean>('rememberMe', false);

  // Set up react-hook-form with validation schema
  const { register, handleSubmit, formState: { errors }, setValue } = useForm<LoginCredentials>({
    resolver: yupResolver(validationSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe
    }
  });

  // Redirect if user is already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(PATHS.DASHBOARD);
    }
  }, [isAuthenticated, navigate]);

  // Handle MFA redirection if required after login
  useEffect(() => {
    if (mfaRequired) {
      navigate('/mfa-verification');
    }
  }, [mfaRequired, navigate]);

  // Form submission handler
  const onSubmit = async (data: LoginCredentials) => {
    try {
      // Save remember me preference
      setRememberMe(data.rememberMe);
      
      // Attempt login
      await login(data);
      // Navigation will be handled by the useEffect hooks above
    } catch (err) {
      // Error handling is managed by useAuth hook
      console.error('Login error:', err);
    }
  };

  // Handle remember me checkbox change
  const handleRememberMeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = e.target.checked;
    setRememberMe(isChecked);
    setValue('rememberMe', isChecked);
  };

  return (
    <AuthLayout title="Login">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Error message display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-md text-sm" role="alert" aria-live="assertive">
            {error}
          </div>
        )}

        {/* Email field */}
        <FormField
          label="Email"
          htmlFor="email"
          error={errors.email?.message}
        >
          <input
            type="email"
            id="email"
            {...register('email')}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            placeholder="your@email.com"
            autoComplete="email"
          />
        </FormField>

        {/* Password field */}
        <FormField
          label="Password"
          htmlFor="password"
          error={errors.password?.message}
        >
          <input
            type="password"
            id="password"
            {...register('password')}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </FormField>

        {/* Remember me and forgot password row */}
        <div className="flex items-center justify-between">
          <Checkbox
            id="rememberMe"
            checked={rememberMe}
            onChange={handleRememberMeChange}
            label="Remember me"
            {...register('rememberMe')}
          />

          <div className="text-sm">
            <Link
              to={PATHS.FORGOT_PASSWORD}
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              Forgot Password?
            </Link>
          </div>
        </div>

        {/* Login button */}
        <Button
          type="submit"
          variant="primary"
          isFullWidth
          isLoading={loading}
        >
          Login
        </Button>

        {/* Sign up link */}
        <div className="mt-4 text-center">
          <span className="text-gray-600">Don't have an account?</span>{' '}
          <Link
            to={PATHS.REGISTER}
            className="font-medium text-primary-600 hover:text-primary-500"
          >
            Sign Up
          </Link>
        </div>
      </form>
    </AuthLayout>
  );
};

export default Login;