/**
 * Hook collection for file management functionality
 * 
 * Provides custom React hooks for handling file attachments, validation, and actions
 * in different contexts (tasks, projects, comments) within the Task Management System.
 * 
 * @version 1.0.0
 */

import { useState, useCallback, useMemo } from 'react';
import { toast } from 'react-toastify'; // react-toastify ^9.1.x

// Import API hooks for file management operations
import {
  useFileUpload,
  useFileMetadata,
  useFileDownload,
  useFilePreview,
  useFileDeletion,
  useAttachments,
  useFileVersions
} from '../../../api/hooks/useFiles';

// Import utility functions and constants for file handling
import {
  isValidFile,
  getFileCategory,
  canUserAccessFile,
  MAX_FILE_SIZE_MB,
  ALLOWED_FILE_TYPES
} from '../utils';

// Import file-related type definitions
import { File, AttachmentQuery, FileUploadStatus } from '../../../types/file';

/**
 * Hook for managing file attachments within a task context
 * 
 * @param taskId - The ID of the task to manage attachments for
 * @returns Object containing attachments data and management functions
 */
export function useTaskAttachments(taskId: string) {
  // Create a query object for task attachments
  const query: AttachmentQuery = useMemo(() => ({
    taskId,
    projectId: null,
    commentId: null
  }), [taskId]);

  // Use the base attachments hook with the task-specific query
  const {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment
  } = useAttachments(query);

  return {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment,
    // Add task-specific context information
    context: {
      type: 'task',
      id: taskId
    }
  };
}

/**
 * Hook for managing file attachments within a project context
 * 
 * @param projectId - The ID of the project to manage attachments for
 * @returns Object containing attachments data and management functions
 */
export function useProjectAttachments(projectId: string) {
  // Create a query object for project attachments
  const query: AttachmentQuery = useMemo(() => ({
    taskId: null,
    projectId,
    commentId: null
  }), [projectId]);

  // Use the base attachments hook with the project-specific query
  const {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment
  } = useAttachments(query);

  return {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment,
    // Add project-specific context information
    context: {
      type: 'project',
      id: projectId
    }
  };
}

/**
 * Hook for managing file attachments within a comment context
 * 
 * @param commentId - The ID of the comment to manage attachments for
 * @returns Object containing attachments data and management functions
 */
export function useCommentAttachments(commentId: string) {
  // Create a query object for comment attachments
  const query: AttachmentQuery = useMemo(() => ({
    taskId: null,
    projectId: null,
    commentId
  }), [commentId]);

  // Use the base attachments hook with the comment-specific query
  const {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment
  } = useAttachments(query);

  return {
    attachments,
    isLoading,
    error,
    refetch,
    addAttachment,
    isAddingAttachment,
    removeAttachment,
    isRemovingAttachment,
    // Add comment-specific context information
    context: {
      type: 'comment',
      id: commentId
    }
  };
}

/**
 * Hook for validating files against size and type constraints with customizable settings
 * 
 * @param options - Configuration options for validation
 * @param options.maxSizeInMB - Maximum file size in megabytes (defaults to MAX_FILE_SIZE_MB)
 * @param options.allowedTypes - Array of allowed MIME types (defaults to all ALLOWED_FILE_TYPES)
 * @returns Object containing validation function and settings
 */
export function useFileValidation({ 
  maxSizeInMB = MAX_FILE_SIZE_MB, 
  allowedTypes 
}: { 
  maxSizeInMB?: number, 
  allowedTypes?: string[] 
} = {}) {
  // Store validation settings
  const settings = useMemo(() => ({
    maxSizeInMB,
    // If allowedTypes is undefined, we'll use isValidFile's default behavior
    allowedTypes: allowedTypes || Object.values(ALLOWED_FILE_TYPES).flat()
  }), [maxSizeInMB, allowedTypes]);

  // Create validation function
  const validateFile = useCallback((file: File | globalThis.File): {
    valid: boolean;
    error?: string;
  } => {
    // For browser File objects
    if (file instanceof globalThis.File) {
      // Convert to our file interface for validation
      const fileObj: File = {
        id: 'temp-id',
        name: file.name,
        size: file.size,
        type: file.type,
        extension: file.name.split('.').pop() || '',
        storageKey: '',
        url: '',
        preview: {
          thumbnail: '',
          previewAvailable: false,
          previewType: ''
        },
        metadata: {
          uploadedBy: '',
          uploadedAt: new Date().toISOString(),
          lastAccessed: new Date().toISOString(),
          accessCount: 0,
          md5Hash: ''
        },
        security: {
          accessLevel: 'PRIVATE',
          encryptionType: 'none',
          scanStatus: 'PENDING'
        },
        associations: {
          taskId: null,
          projectId: null,
          commentId: null
        },
        versions: []
      };

      if (!isValidFile(fileObj, settings.maxSizeInMB, settings.allowedTypes)) {
        return { 
          valid: false, 
          error: `File validation failed. Please check that your file is under ${settings.maxSizeInMB}MB and is an allowed type.` 
        };
      }

      return { valid: true };
    }

    // For application File objects
    if (!isValidFile(file, settings.maxSizeInMB, settings.allowedTypes)) {
      return { 
        valid: false, 
        error: `File validation failed. Please check that your file is under ${settings.maxSizeInMB}MB and is an allowed type.` 
      };
    }

    return { valid: true };
  }, [settings.maxSizeInMB, settings.allowedTypes]);

  return {
    validateFile,
    settings
  };
}

/**
 * Comprehensive hook that combines download, preview, and deletion capabilities for a file
 * 
 * @param file - The file to perform actions on
 * @returns Object containing download, preview, and delete functions with loading states
 */
export function useFileActions(file: File) {
  // Use the individual file operation hooks
  const { getDownloadUrl, isGenerating: isGeneratingDownloadUrl, error: downloadError } = useFileDownload();
  const { getPreviewUrl, isGenerating: isGeneratingPreviewUrl, error: previewError } = useFilePreview();
  const { deleteFile, isDeleting, error: deleteError } = useFileDeletion();

  // Combined download function with error handling
  const downloadFile = useCallback(async () => {
    try {
      const url = await getDownloadUrl(file.id);
      
      // Create an anchor element to trigger the download
      const link = document.createElement('a');
      link.href = url;
      link.download = file.name; // Set suggested filename
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success(`Downloading: ${file.name}`);
    } catch (error) {
      toast.error(`Failed to download ${file.name}: ${downloadError || 'Unknown error'}`);
    }
  }, [file, getDownloadUrl, downloadError]);

  // Combined preview function with error handling
  const previewFile = useCallback(async (width?: number, height?: number) => {
    try {
      const sizeParams = width || height ? { width, height } : undefined;
      const url = await getPreviewUrl(file.id, sizeParams);
      
      // Open preview in new tab or return URL depending on file type
      const category = getFileCategory(file.type);
      
      if (category === 'image' || category === 'document') {
        window.open(url, '_blank');
      }
      
      return url;
    } catch (error) {
      toast.error(`Failed to preview ${file.name}: ${previewError || 'Unknown error'}`);
      return null;
    }
  }, [file, getPreviewUrl, previewError]);

  // Combined delete function with confirmation and error handling
  const handleDeleteFile = useCallback(async () => {
    try {
      // Delete the file
      await deleteFile(file.id);
      toast.success(`${file.name} deleted successfully`);
    } catch (error) {
      toast.error(`Failed to delete ${file.name}: ${deleteError || 'Unknown error'}`);
    }
  }, [file, deleteFile, deleteError]);

  return {
    download: downloadFile,
    preview: previewFile,
    delete: handleDeleteFile,
    isDownloading: isGeneratingDownloadUrl,
    isPreviewing: isGeneratingPreviewUrl,
    isDeleting,
    error: downloadError || previewError || deleteError
  };
}

// Re-export the API hooks for convenience
export {
  useFileUpload,
  useFileMetadata,
  useFileVersions
};