import { User, Role, Permission } from '../types/auth';
import { UserPermission } from '../types/user';

/**
 * Maps roles to their associated permissions
 * This defines the RBAC matrix for the application
 */
export const ROLE_PERMISSIONS: Record<Role | string, Permission[]> = {
  [Role.ADMIN]: [
    { type: 'all' }, // Admin has all permissions
  ],
  [Role.MANAGER]: [
    // Project management permissions
    { type: 'project:create' },
    { type: 'project:read' },
    { type: 'project:update' },
    { type: 'project:delete' },
    // Task management permissions 
    { type: 'task:create' },
    { type: 'task:read' },
    { type: 'task:update' },
    { type: 'task:delete' },
    { type: 'task:assign' },
    // Team management permissions
    { type: 'team:read' },
    { type: 'team:update' },
    // Report permissions
    { type: 'report:read' },
    { type: 'report:create' },
  ],
  [Role.USER]: [
    // Basic user permissions
    { type: 'project:read' },
    { type: 'task:create' },
    { type: 'task:read' },
    { type: 'task:update' }, // Can update own tasks
    { type: 'comment:create' },
    { type: 'comment:read' },
    { type: 'attachment:create' },
    { type: 'attachment:read' },
    { type: 'report:read' },
  ],
};

/**
 * Checks if a user has a specific role
 * 
 * @param user - The user to check roles for
 * @param roleName - The role to check
 * @returns True if the user has the specified role, false otherwise
 */
export const hasRole = (user: User, roleName: Role | string): boolean => {
  if (!user?.roles) {
    return false;
  }
  
  return user.roles.includes(roleName);
};

/**
 * Checks if a user has any of the specified roles
 * 
 * @param user - The user to check roles for
 * @param roles - Array of roles to check
 * @returns True if the user has any of the specified roles, false otherwise
 */
export const hasAnyRole = (user: User, roles: (Role | string)[]): boolean => {
  if (!user) {
    return false;
  }
  
  if (!roles || roles.length === 0) {
    return true; // No role restrictions
  }
  
  return roles.some(role => hasRole(user, role));
};

/**
 * Checks if a user has a specific permission
 * 
 * @param user - The user to check permissions for
 * @param resource - The resource to check access for
 * @param action - The action to check
 * @returns True if the user has the specified permission, false otherwise
 */
export const hasPermission = (user: User, resource: string, action: string): boolean => {
  if (!user) {
    return false;
  }
  
  // Admins have all permissions
  if (hasRole(user, Role.ADMIN)) {
    return true;
  }
  
  // Check if user has the specific permission
  if ('permissions' in user) {
    // Type assertion for UserWithPermissions
    const permissions = (user as any).permissions as UserPermission[];
    if (permissions) {
      return permissions.some(
        permission => 
          permission.resource === resource && 
          permission.action === action
      );
    }
  }
  
  // Check permissions based on user roles
  return user.roles.some(role => {
    const permissions = ROLE_PERMISSIONS[role] || [];
    return permissions.some(permission => 
      // Check for type-specific permission
      permission.type === `${resource}:${action}` ||
      // Check for all permissions on a resource
      permission.type === `${resource}:all` ||
      // Check for global all permissions
      permission.type === 'all'
    );
  });
};

/**
 * Determines if a user can access a specific resource based on permissions
 * 
 * @param user - The user to check
 * @param resource - The resource to check access for
 * @param action - The action to check
 * @returns True if the user can access the resource, false otherwise
 */
export const canAccessResource = (user: User, resource: string, action: string): boolean => {
  // Admins can access everything
  if (hasRole(user, Role.ADMIN)) {
    return true;
  }
  
  // Check specific permission
  return hasPermission(user, resource, action);
};

/**
 * Determines if a user can access a specific route based on required roles or permissions
 * 
 * @param user - The user to check
 * @param requiredRoles - Roles that can access the route (optional)
 * @param requiredPermissions - Permissions needed to access the route (optional)
 * @returns True if the user can access the route, false otherwise
 */
export const canAccessRoute = (
  user: User,
  requiredRoles: Role[] | null = null,
  requiredPermissions: Permission[] | null = null
): boolean => {
  // If no restrictions, allow access
  if ((!requiredRoles || requiredRoles.length === 0) && 
      (!requiredPermissions || requiredPermissions.length === 0)) {
    return true;
  }
  
  if (!user) {
    return false;
  }
  
  // Check role-based access
  if (requiredRoles && requiredRoles.length > 0) {
    if (hasAnyRole(user, requiredRoles)) {
      return true;
    }
  }
  
  // Check permission-based access
  if (requiredPermissions && requiredPermissions.length > 0) {
    return requiredPermissions.every(permission => {
      // Extract resource and action from permission type
      const [resource, action] = permission.type.split(':');
      if (!resource || !action) {
        return false;
      }
      return hasPermission(user, resource, action);
    });
  }
  
  // If we have required permissions/roles but none matched
  return false;
};

/**
 * Checks if a user can perform a specific action on a resource object
 * 
 * @param user - The user to check
 * @param action - The action to perform
 * @param resource - The resource object
 * @returns True if the user can perform the action, false otherwise
 */
export const canPerformAction = (user: User, action: string, resource: any): boolean => {
  if (!user) {
    return false;
  }
  
  // Admins can perform any action
  if (hasRole(user, Role.ADMIN)) {
    return true;
  }
  
  // Check if user is the owner of the resource
  if (isResourceOwner(user, resource)) {
    return true;
  }
  
  // Check specific permission for the resource type
  const resourceType = resource?.type || resource?.resourceType || '';
  if (resourceType) {
    return hasPermission(user, resourceType, action);
  }
  
  return false;
};

/**
 * Determines if a user is the owner of a resource
 * 
 * @param user - The user to check
 * @param resource - The resource to check ownership
 * @returns True if the user is the owner, false otherwise
 */
export const isResourceOwner = (user: User, resource: any): boolean => {
  if (!user || !resource) {
    return false;
  }
  
  // Check common ownership fields
  const ownerId = resource.createdBy || resource.ownerId || resource.userId;
  
  return ownerId === user.id;
};

/**
 * Returns the permissions associated with a specific role
 * 
 * @param role - The role to get permissions for
 * @returns Array of permissions for the role
 */
export const getRolePermissions = (role: Role | string): Permission[] => {
  return ROLE_PERMISSIONS[role] || [];
};