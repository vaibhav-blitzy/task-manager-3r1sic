/**
 * File management utility functions for the Task Management System.
 * Provides functionality for file validation, type detection, formatting,
 * and access control throughout the application.
 */

import {
  FiFile, FiImage, FiFileText, FiVideo, FiMusic,
  FiArchive, FiCode, FiDatabase, FiPaperclip
} from 'react-icons/fi'; // v4.10.0
import { formatFileSize } from '../../../utils/formatting';
import { File, FileUploadStatus, FileAccessLevel } from '../../../types/file';

/**
 * Map of allowed file types by category
 */
export const ALLOWED_FILE_TYPES = {
  'image': [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml'
  ],
  'document': [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv'
  ],
  'video': [
    'video/mp4',
    'video/webm',
    'video/ogg'
  ],
  'audio': [
    'audio/mpeg',
    'audio/ogg',
    'audio/wav'
  ],
  'archive': [
    'application/zip',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
    'application/x-tar',
    'application/gzip'
  ],
  'code': [
    'text/html',
    'text/css',
    'text/javascript',
    'application/json',
    'application/xml'
  ]
};

/**
 * Default maximum file size in MB
 */
export const MAX_FILE_SIZE_MB = 25;

/**
 * Map of file extensions to MIME types
 */
export const FILE_TYPE_EXTENSIONS = {
  'jpeg': 'image/jpeg',
  'jpg': 'image/jpeg',
  'png': 'image/png',
  'gif': 'image/gif',
  'webp': 'image/webp',
  'svg': 'image/svg+xml',
  'pdf': 'application/pdf',
  'doc': 'application/msword',
  'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'xls': 'application/vnd.ms-excel',
  'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'ppt': 'application/vnd.ms-powerpoint',
  'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'txt': 'text/plain',
  'csv': 'text/csv',
  'mp4': 'video/mp4',
  'webm': 'video/webm',
  'ogg': 'video/ogg',
  'mp3': 'audio/mpeg',
  'wav': 'audio/wav',
  'zip': 'application/zip',
  'rar': 'application/x-rar-compressed',
  '7z': 'application/x-7z-compressed',
  'tar': 'application/x-tar',
  'gz': 'application/gzip',
  'html': 'text/html',
  'css': 'text/css',
  'js': 'text/javascript',
  'json': 'application/json',
  'xml': 'application/xml'
};

/**
 * Validates a file against size and type constraints
 * 
 * @param file - The file to validate
 * @param maxSizeInMB - Maximum file size in MB (defaults to MAX_FILE_SIZE_MB)
 * @param allowedTypes - Array of allowed MIME types (if undefined, all types in ALLOWED_FILE_TYPES are allowed)
 * @returns True if the file is valid, false otherwise
 */
export function isValidFile(
  file: File,
  maxSizeInMB?: number,
  allowedTypes?: string[]
): boolean {
  if (!file) {
    return false;
  }

  // Validate file size
  const maxSizeInBytes = (maxSizeInMB || MAX_FILE_SIZE_MB) * 1024 * 1024;
  if (file.size > maxSizeInBytes) {
    return false;
  }

  // Validate file type
  if (allowedTypes && allowedTypes.length > 0) {
    return allowedTypes.includes(file.type);
  }

  // If no specific types provided, check against all allowed types
  const allAllowedTypes = Object.values(ALLOWED_FILE_TYPES).flat();
  return allAllowedTypes.includes(file.type);
}

/**
 * Determines the general category of a file based on its MIME type
 * 
 * @param mimeType - The MIME type of the file
 * @returns The category of the file (image, document, video, etc.) or 'other' if not categorized
 */
export function getFileCategory(mimeType: string): string {
  if (!mimeType) {
    return 'other';
  }

  for (const [category, types] of Object.entries(ALLOWED_FILE_TYPES)) {
    if (types.includes(mimeType)) {
      return category;
    }
  }

  return 'other';
}

/**
 * Returns the appropriate icon component based on file type
 * 
 * @param mimeType - The MIME type of the file
 * @returns The icon component for the file type
 */
export function getIconForFileType(mimeType: string): JSX.Element {
  const category = getFileCategory(mimeType);

  switch (category) {
    case 'image':
      return <FiImage />;
    case 'document':
      return <FiFileText />;
    case 'video':
      return <FiVideo />;
    case 'audio':
      return <FiMusic />;
    case 'archive':
      return <FiArchive />;
    case 'code':
      return <FiCode />;
    case 'data':
      return <FiDatabase />;
    default:
      return <FiFile />;
  }
}

/**
 * Determines MIME type based on file extension
 * 
 * @param filename - The filename including extension
 * @returns The MIME type or null if the extension is unknown
 */
export function getMimeTypeFromExtension(filename: string): string | null {
  if (!filename) {
    return null;
  }

  const extension = filename.split('.').pop()?.toLowerCase();
  if (!extension) {
    return null;
  }

  return FILE_TYPE_EXTENSIONS[extension as keyof typeof FILE_TYPE_EXTENSIONS] || null;
}

/**
 * Gets the file extension from a MIME type
 * 
 * @param mimeType - The MIME type
 * @returns The file extension or null if the MIME type is unknown
 */
export function getExtensionFromMimeType(mimeType: string): string | null {
  if (!mimeType) {
    return null;
  }

  // Reverse lookup in FILE_TYPE_EXTENSIONS
  for (const [ext, mime] of Object.entries(FILE_TYPE_EXTENSIONS)) {
    if (mime === mimeType) {
      return ext;
    }
  }

  return null;
}

/**
 * Creates a temporary object URL for a file
 * 
 * @param file - The file to create a URL for
 * @returns The object URL
 */
export function createObjectURL(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * Revokes a previously created object URL to free up resources
 * 
 * @param url - The URL to revoke
 */
export function revokeObjectURL(url: string): void {
  URL.revokeObjectURL(url);
}

/**
 * Formats file access level enum value to user-friendly string
 * 
 * @param accessLevel - The access level enum value
 * @returns Formatted access level string
 */
export function formatFileAccessLevel(accessLevel: FileAccessLevel): string {
  switch (accessLevel) {
    case FileAccessLevel.PUBLIC:
      return 'Public';
    case FileAccessLevel.PRIVATE:
      return 'Private';
    case FileAccessLevel.SHARED:
      return 'Shared with team';
    default:
      return 'Unknown';
  }
}

/**
 * Formats file upload status enum value to user-friendly string
 * 
 * @param status - The upload status enum value
 * @returns Formatted status string
 */
export function formatFileUploadStatus(status: FileUploadStatus): string {
  switch (status) {
    case FileUploadStatus.PENDING:
      return 'Pending';
    case FileUploadStatus.UPLOADING:
      return 'Uploading...';
    case FileUploadStatus.SCANNING:
      return 'Scanning...';
    case FileUploadStatus.COMPLETED:
      return 'Completed';
    case FileUploadStatus.FAILED:
      return 'Failed';
    default:
      return 'Unknown';
  }
}

/**
 * Extracts the original filename from a file URL
 * 
 * @param url - The file URL
 * @returns The extracted filename
 */
export function extractFilenameFromURL(url: string): string {
  if (!url) {
    return '';
  }

  try {
    // Get the pathname from the URL
    const pathname = new URL(url).pathname;
    
    // Extract the filename from the pathname
    const filename = pathname.split('/').pop() || '';
    
    // Decode any URL-encoded characters
    return decodeURIComponent(filename);
  } catch (error) {
    // If URL parsing fails, try a simpler approach
    const parts = url.split('/');
    return decodeURIComponent(parts[parts.length - 1]);
  }
}

/**
 * Calculates upload progress percentage from loaded and total bytes
 * 
 * @param loaded - The number of bytes loaded
 * @param total - The total number of bytes
 * @returns Progress percentage between 0 and 100
 */
export function calculateUploadProgress(loaded: number, total: number): number {
  if (!total || total <= 0) {
    return 0;
  }

  const percentage = Math.round((loaded / total) * 100);
  return Math.min(100, Math.max(0, percentage));
}

/**
 * Determines if the current user can access a file based on its access level and associations
 * 
 * @param file - The file to check access for
 * @param userPermissions - Object containing user permissions information
 * @returns True if the user can access the file, false otherwise
 */
export function canUserAccessFile(file: File, userPermissions: any): boolean {
  if (!file || !userPermissions) {
    return false;
  }

  // Public files are accessible to everyone
  if (file.security.accessLevel === FileAccessLevel.PUBLIC) {
    return true;
  }

  // Private files are only accessible to the uploader
  if (file.security.accessLevel === FileAccessLevel.PRIVATE) {
    return file.metadata.uploadedBy === userPermissions.userId;
  }

  // Shared files are accessible based on task/project associations
  if (file.security.accessLevel === FileAccessLevel.SHARED) {
    // Check task access
    if (file.associations.taskId && userPermissions.tasks) {
      if (userPermissions.tasks.includes(file.associations.taskId)) {
        return true;
      }
    }

    // Check project access
    if (file.associations.projectId && userPermissions.projects) {
      if (userPermissions.projects.includes(file.associations.projectId)) {
        return true;
      }
    }
    
    // If user is a member of a team that has access
    if (userPermissions.teamMember && file.associations.projectId) {
      return userPermissions.teamProjects?.includes(file.associations.projectId) || false;
    }
  }

  return false;
}

// Re-export formatFileSize from formatting utils for convenience
export { formatFileSize };