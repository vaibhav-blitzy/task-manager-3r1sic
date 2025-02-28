import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

import DashboardLayout from '../../../components/templates/DashboardLayout/DashboardLayout';
import FormField from '../../../components/molecules/FormField/FormField';
import Input from '../../../components/atoms/Input/Input';
import Button from '../../../components/atoms/Button/Button';
import Checkbox from '../../../components/atoms/Checkbox/Checkbox';
import useAuth from '../../../api/hooks/useAuth';
import { updateProfile, changePassword } from '../../../api/services/authService';
import { useTheme } from '../../../contexts/ThemeContext';
import { UserProfileUpdateData, UserPasswordChangeData, UserSettings as UserSettingsType, UserNotificationSettings } from '../../../types/user';
import { validatePassword } from '../../../utils/validation';

// Initial form state for profile information
const initialProfileFormState = {
  firstName: '',
  lastName: '',
  settings: {
    language: 'en',
    theme: 'light',
    notifications: {
      email: true,
      push: true,
      inApp: true,
      digest: {
        enabled: false,
        frequency: 'daily'
      }
    },
    defaultView: 'dashboard'
  }
};

// Initial form state for password change
const initialPasswordFormState = {
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
};

/**
 * User settings page component that allows users to view and update their profile information, 
 * preferences, and security settings.
 */
const UserSettings: React.FC = () => {
  const { user, loading, error } = useAuth();
  const { theme, setTheme } = useTheme();
  
  // Form states
  const [profileForm, setProfileForm] = useState<UserProfileUpdateData>(initialProfileFormState);
  const [passwordForm, setPasswordForm] = useState<UserPasswordChangeData>(initialPasswordFormState);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Populate form with user data when available
  useEffect(() => {
    if (user) {
      setProfileForm({
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        settings: user.settings || initialProfileFormState.settings
      });
    }
  }, [user]);

  // Handle profile form changes
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileForm(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear any error for this field
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Handle password form changes
  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear any error for this field
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Handle theme changes
  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme as 'light' | 'dark');
    setProfileForm(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        theme: newTheme
      }
    }));
  };

  // Handle notification preference changes
  const handleNotificationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    
    setProfileForm(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        notifications: {
          ...prev.settings.notifications,
          [name]: checked
        }
      }
    }));
  };

  // Handle digest settings change
  const handleDigestChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { checked } = e.target;
    
    setProfileForm(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        notifications: {
          ...prev.settings.notifications,
          digest: {
            ...prev.settings.notifications.digest,
            enabled: checked
          }
        }
      }
    }));
  };

  // Handle digest frequency change
  const handleDigestFrequencyChange = (frequency: string) => {
    setProfileForm(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        notifications: {
          ...prev.settings.notifications,
          digest: {
            ...prev.settings.notifications.digest,
            frequency
          }
        }
      }
    }));
  };

  // Validate profile form
  const validateProfileForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!profileForm.firstName.trim()) {
      errors.firstName = 'First name is required';
    }
    
    if (!profileForm.lastName.trim()) {
      errors.lastName = 'Last name is required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Validate password form
  const validatePasswordForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!passwordForm.currentPassword) {
      errors.currentPassword = 'Current password is required';
    }
    
    if (!passwordForm.newPassword) {
      errors.newPassword = 'New password is required';
    } else if (!validatePassword(passwordForm.newPassword)) {
      errors.newPassword = 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character';
    }
    
    if (!passwordForm.confirmPassword) {
      errors.confirmPassword = 'Please confirm your new password';
    } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle profile form submission
  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateProfileForm()) {
      return;
    }
    
    setIsSubmittingProfile(true);
    setSuccessMessage(null);
    
    try {
      const response = await updateProfile(profileForm);
      toast.success('Profile updated successfully');
      setSuccessMessage('Profile updated successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
      toast.error(errorMessage);
      setFormErrors(prev => ({
        ...prev,
        general: errorMessage
      }));
    } finally {
      setIsSubmittingProfile(false);
    }
  };

  // Handle password form submission
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePasswordForm()) {
      return;
    }
    
    setIsSubmittingPassword(true);
    setSuccessMessage(null);
    
    try {
      const response = await changePassword(passwordForm);
      toast.success('Password changed successfully');
      setSuccessMessage('Password changed successfully');
      // Reset form after successful submission
      setPasswordForm(initialPasswordFormState);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to change password';
      toast.error(errorMessage);
      setFormErrors(prev => ({
        ...prev,
        general: errorMessage
      }));
    } finally {
      setIsSubmittingPassword(false);
    }
  };

  return (
    <DashboardLayout title="User Settings">
      <div className="max-w-3xl mx-auto">
        {loading ? (
          <div className="flex justify-center p-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
          </div>
        ) : (
          <>
            {/* Profile Information */}
            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg mb-6 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Profile Information</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Update your personal information</p>
              </div>
              
              <form className="p-6" onSubmit={handleProfileSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField 
                    label="First Name"
                    htmlFor="firstName"
                    required
                    error={formErrors.firstName}
                  >
                    <Input
                      id="firstName"
                      name="firstName"
                      value={profileForm.firstName}
                      onChange={handleProfileChange}
                      placeholder="Your first name"
                    />
                  </FormField>
                  
                  <FormField 
                    label="Last Name"
                    htmlFor="lastName"
                    required
                    error={formErrors.lastName}
                  >
                    <Input
                      id="lastName"
                      name="lastName"
                      value={profileForm.lastName}
                      onChange={handleProfileChange}
                      placeholder="Your last name"
                    />
                  </FormField>
                </div>
                
                <div className="mt-4">
                  <FormField 
                    label="Email Address"
                    htmlFor="email"
                    helperText="Email address cannot be changed. Contact support for assistance."
                  >
                    <Input
                      id="email"
                      name="email"
                      value={user?.email || ''}
                      readOnly
                      disabled
                    />
                  </FormField>
                </div>
                
                <div className="mt-6">
                  <Button
                    type="submit"
                    variant="primary"
                    isLoading={isSubmittingProfile}
                    disabled={isSubmittingProfile}
                  >
                    Save Profile
                  </Button>
                </div>
              </form>
            </div>
            
            {/* Theme Preferences */}
            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg mb-6 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Theme Preferences</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Customize the appearance of the application</p>
              </div>
              
              <div className="p-6">
                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => handleThemeChange('light')}
                    className={`flex flex-col items-center justify-center p-4 border rounded-lg ${
                      theme === 'light' 
                        ? 'border-primary-500 bg-primary-50 text-primary-700' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    aria-pressed={theme === 'light'}
                  >
                    <div className="h-12 w-12 bg-white border border-gray-200 rounded-full mb-2 flex items-center justify-center">
                      <span role="img" aria-label="Light mode">☀️</span>
                    </div>
                    <span className="font-medium">Light Mode</span>
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => handleThemeChange('dark')}
                    className={`flex flex-col items-center justify-center p-4 border rounded-lg ${
                      theme === 'dark' 
                        ? 'border-primary-500 bg-primary-50 text-primary-700' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    aria-pressed={theme === 'dark'}
                  >
                    <div className="h-12 w-12 bg-gray-800 border border-gray-700 rounded-full mb-2 flex items-center justify-center">
                      <span role="img" aria-label="Dark mode">🌙</span>
                    </div>
                    <span className="font-medium">Dark Mode</span>
                  </button>
                </div>
              </div>
            </div>
            
            {/* Notification Preferences */}
            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg mb-6 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Notification Preferences</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Control how you receive notifications</p>
              </div>
              
              <div className="p-6">
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Notification Channels</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <Checkbox
                        id="email"
                        name="email"
                        checked={profileForm.settings.notifications.email}
                        onChange={handleNotificationChange}
                        label="Email Notifications"
                      />
                    </div>
                    
                    <div className="flex items-center">
                      <Checkbox
                        id="push"
                        name="push"
                        checked={profileForm.settings.notifications.push}
                        onChange={handleNotificationChange}
                        label="Push Notifications"
                      />
                    </div>
                    
                    <div className="flex items-center">
                      <Checkbox
                        id="inApp"
                        name="inApp"
                        checked={profileForm.settings.notifications.inApp}
                        onChange={handleNotificationChange}
                        label="In-App Notifications"
                      />
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Digest Settings</h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <Checkbox
                        id="digestEnabled"
                        name="digestEnabled"
                        checked={profileForm.settings.notifications.digest.enabled}
                        onChange={handleDigestChange}
                        label="Receive Digest Emails"
                      />
                    </div>
                    
                    {profileForm.settings.notifications.digest.enabled && (
                      <div className="ml-7 mt-2">
                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Digest Frequency</div>
                        <div className="flex space-x-4">
                          <button
                            type="button"
                            onClick={() => handleDigestFrequencyChange('daily')}
                            className={`px-3 py-1 text-sm rounded ${
                              profileForm.settings.notifications.digest.frequency === 'daily'
                                ? 'bg-primary-100 text-primary-700 border-primary-300'
                                : 'bg-white border-gray-300 hover:bg-gray-50'
                            } border`}
                          >
                            Daily
                          </button>
                          
                          <button
                            type="button"
                            onClick={() => handleDigestFrequencyChange('weekly')}
                            className={`px-3 py-1 text-sm rounded ${
                              profileForm.settings.notifications.digest.frequency === 'weekly'
                                ? 'bg-primary-100 text-primary-700 border-primary-300'
                                : 'bg-white border-gray-300 hover:bg-gray-50'
                            } border`}
                          >
                            Weekly
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="mt-6">
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleProfileSubmit}
                    isLoading={isSubmittingProfile}
                    disabled={isSubmittingProfile}
                  >
                    Save Notification Preferences
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Security Settings */}
            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg mb-6 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Security Settings</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Manage your account security preferences</p>
              </div>
              
              <div className="p-6">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">Change Password</h3>
                
                <form onSubmit={handlePasswordSubmit}>
                  <FormField 
                    label="Current Password"
                    htmlFor="currentPassword"
                    required
                    error={formErrors.currentPassword}
                  >
                    <Input
                      id="currentPassword"
                      name="currentPassword"
                      type="password"
                      value={passwordForm.currentPassword}
                      onChange={handlePasswordChange}
                      placeholder="Enter your current password"
                    />
                  </FormField>
                  
                  <div className="mt-4">
                    <FormField 
                      label="New Password"
                      htmlFor="newPassword"
                      required
                      error={formErrors.newPassword}
                      helperText="Password must be at least 8 characters and include uppercase, lowercase, number, and special character"
                    >
                      <Input
                        id="newPassword"
                        name="newPassword"
                        type="password"
                        value={passwordForm.newPassword}
                        onChange={handlePasswordChange}
                        placeholder="Enter your new password"
                      />
                    </FormField>
                  </div>
                  
                  <div className="mt-4">
                    <FormField 
                      label="Confirm New Password"
                      htmlFor="confirmPassword"
                      required
                      error={formErrors.confirmPassword}
                    >
                      <Input
                        id="confirmPassword"
                        name="confirmPassword"
                        type="password"
                        value={passwordForm.confirmPassword}
                        onChange={handlePasswordChange}
                        placeholder="Confirm your new password"
                      />
                    </FormField>
                  </div>
                  
                  <div className="mt-6">
                    <Button
                      type="submit"
                      variant="primary"
                      isLoading={isSubmittingPassword}
                      disabled={isSubmittingPassword}
                    >
                      Change Password
                    </Button>
                  </div>
                </form>
                
                <div className="mt-8">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">Two-Factor Authentication</h3>
                  
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                    <div className="flex items-start">
                      <div className={`mt-0.5 h-4 w-4 rounded-full flex-shrink-0 ${user?.security?.mfaEnabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {user?.security?.mfaEnabled ? 'Enabled' : 'Not Enabled'}
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {user?.security?.mfaEnabled 
                            ? `Two-factor authentication is currently enabled using ${user.security.mfaMethod}.` 
                            : 'Two-factor authentication is not enabled for your account.'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      <Button
                        type="button"
                        variant={user?.security?.mfaEnabled ? 'outline' : 'primary'}
                        size="sm"
                      >
                        {user?.security?.mfaEnabled ? 'Manage 2FA' : 'Enable 2FA'}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Success message */}
            {successMessage && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative mb-6" role="alert">
                <span className="block sm:inline">{successMessage}</span>
              </div>
            )}
            
            {/* General error message */}
            {formErrors.general && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
                <span className="block sm:inline">{formErrors.general}</span>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default UserSettings;