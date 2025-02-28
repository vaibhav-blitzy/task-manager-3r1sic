/**
 * Custom React hook that provides file management capabilities for the Task Management System.
 * Enables components to upload, download, list, and manage file attachments with
 * React Query integration for data fetching, caching, and synchronization.
 * 
 * @version 1.5.x
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query'; // react-query ^3.39.x
import { toast } from 'react-toastify'; // react-toastify ^9.1.x
import { AxiosProgressEvent } from 'axios'; // axios ^1.5.x

import {
  uploadFile,
  getFileMetadata,
  getDownloadUrl,
  getPreviewUrl,
  deleteFile,
  getAttachments,
  createAttachment,
  removeAttachment,
  getFileVersions,
  uploadNewVersion
} from '../services/fileService';
import {
  File,
  FileUploadRequest,
  FileUploadResponse,
  FileUploadStatus,
  FileVersion,
  AttachmentQuery
} from '../../types/file';
import { handleApiError } from '../client';
import useAuth from './useAuth';

// React Query key constants
const FILE_KEYS = {
  FILES: 'files',
  FILE_DETAIL: 'file-detail',
  ATTACHMENTS: 'attachments',
  FILE_VERSIONS: 'file-versions'
};

/**
 * Hook for handling file uploads with progress tracking
 * 
 * @returns Object containing uploadFile function, isUploading state, uploadProgress, and error state
 */
export function useFileUpload() {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFileMutation = useMutation(
    (file: globalThis.File) => {
      setIsUploading(true);
      setUploadProgress(0);
      setError(null);
      
      return uploadFile(file, (progressEvent: AxiosProgressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });
    },
    {
      onSuccess: (data) => {
        setIsUploading(false);
        toast.success(`File "${data.name}" uploaded successfully`);
        // Invalidate relevant queries
        queryClient.invalidateQueries(FILE_KEYS.FILES);
      },
      onError: (err: any) => {
        setIsUploading(false);
        const errorMessage = err.message || 'Failed to upload file';
        setError(errorMessage);
        toast.error(errorMessage);
      }
    }
  );

  return {
    uploadFile: uploadFileMutation.mutate,
    isUploading,
    uploadProgress,
    error
  };
}

/**
 * Hook for fetching and managing file metadata
 * 
 * @param fileId - ID of the file to fetch metadata for
 * @param options - Optional react-query options
 * @returns Object containing file metadata, loading state, error state, and refetch function
 */
export function useFileMetadata(fileId: string, options?: UseQueryOptions<File, Error>) {
  return useQuery<File, Error>(
    [FILE_KEYS.FILE_DETAIL, fileId],
    () => getFileMetadata(fileId),
    {
      enabled: !!fileId,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      retry: 1,
      ...options
    }
  );
}

/**
 * Hook for generating download URLs for files
 * 
 * @returns Object containing getDownloadUrl function, isGenerating state, and error state
 */
export function useFileDownload() {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const downloadFile = useCallback(async (fileId: string): Promise<string> => {
    setIsGenerating(true);
    setError(null);

    try {
      const url = await getDownloadUrl(fileId);
      setIsGenerating(false);
      return url;
    } catch (err) {
      setIsGenerating(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate download URL';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  return {
    getDownloadUrl: downloadFile,
    isGenerating,
    error
  };
}

/**
 * Hook for generating preview URLs for files
 * 
 * @returns Object containing getPreviewUrl function, isGenerating state, and error state
 */
export function useFilePreview() {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const previewFile = useCallback(async (
    fileId: string,
    sizeParams?: { width?: number; height?: number }
  ): Promise<string> => {
    setIsGenerating(true);
    setError(null);

    try {
      const url = await getPreviewUrl(fileId, sizeParams);
      setIsGenerating(false);
      return url;
    } catch (err) {
      setIsGenerating(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate preview URL';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  return {
    getPreviewUrl: previewFile,
    isGenerating,
    error
  };
}

/**
 * Hook for deleting files
 * 
 * @returns Object containing deleteFile function, isDeleting state, and error state
 */
export function useFileDeletion() {
  const queryClient = useQueryClient();

  const deleteFileMutation = useMutation(
    (fileId: string) => deleteFile(fileId),
    {
      onSuccess: (_, fileId) => {
        // Invalidate relevant queries
        queryClient.invalidateQueries(FILE_KEYS.FILES);
        queryClient.invalidateQueries([FILE_KEYS.FILE_DETAIL, fileId]);
        queryClient.invalidateQueries(FILE_KEYS.ATTACHMENTS);
        toast.success('File deleted successfully');
      },
      onError: (err: any) => {
        const errorMessage = err.message || 'Failed to delete file';
        toast.error(errorMessage);
      }
    }
  );

  return {
    deleteFile: deleteFileMutation.mutate,
    isDeleting: deleteFileMutation.isLoading,
    error: deleteFileMutation.error
      ? (deleteFileMutation.error as Error).message
      : null
  };
}

/**
 * Hook for fetching and managing file attachments
 * 
 * @param query - Query parameters for fetching attachments (taskId, projectId, commentId)
 * @param options - Optional react-query options
 * @returns Object containing attachments, loading state, error state, refetch, addAttachment, and removeAttachment functions
 */
export function useAttachments(query: AttachmentQuery, options?: UseQueryOptions<File[], Error>) {
  const queryClient = useQueryClient();
  
  // Generate query key based on the attachment query
  const queryKey = useMemo(() => {
    const { taskId, projectId, commentId } = query;
    return [
      FILE_KEYS.ATTACHMENTS,
      taskId ? `task-${taskId}` : undefined,
      projectId ? `project-${projectId}` : undefined,
      commentId ? `comment-${commentId}` : undefined
    ].filter(Boolean);
  }, [query]);

  // Fetch attachments
  const attachmentsQuery = useQuery<File[], Error>(
    queryKey,
    () => getAttachments(query),
    {
      enabled: !!(query.taskId || query.projectId || query.commentId),
      ...options
    }
  );

  // Add attachment mutation
  const addAttachmentMutation = useMutation(
    (fileId: string) => createAttachment(fileId, query),
    {
      onMutate: async (fileId) => {
        // Cancel any outgoing refetches to avoid overwriting our optimistic update
        await queryClient.cancelQueries(queryKey);

        // Snapshot the previous value
        const previousAttachments = queryClient.getQueryData<File[]>(queryKey) || [];

        // Optimistically update to the new value
        const optimisticAttachment: Partial<File> = {
          id: fileId,
          name: 'Loading...', // Placeholder until we get real data
          size: 0,
          type: '',
          extension: '',
          metadata: {
            uploadedAt: new Date().toISOString(),
            uploadedBy: 'currentUser', // Placeholder
            lastAccessed: new Date().toISOString(),
            accessCount: 0,
            md5Hash: ''
          }
        };

        queryClient.setQueryData<File[]>(
          queryKey,
          [...previousAttachments, optimisticAttachment as File]
        );

        return { previousAttachments };
      },
      onSuccess: (newAttachment) => {
        toast.success('File attached successfully');
      },
      onError: (err, fileId, context: any) => {
        // Revert to previous state on error
        if (context?.previousAttachments) {
          queryClient.setQueryData(queryKey, context.previousAttachments);
        }
        const errorMessage = err instanceof Error ? err.message : 'Failed to attach file';
        toast.error(errorMessage);
      },
      onSettled: () => {
        // Always refetch to ensure we have the correct data
        queryClient.invalidateQueries(queryKey);
      }
    }
  );

  // Remove attachment mutation
  const removeAttachmentMutation = useMutation(
    (fileId: string) => removeAttachment(fileId, query),
    {
      onMutate: async (fileId) => {
        // Cancel any outgoing refetches to avoid overwriting our optimistic update
        await queryClient.cancelQueries(queryKey);

        // Snapshot the previous value
        const previousAttachments = queryClient.getQueryData<File[]>(queryKey) || [];

        // Optimistically update to the new value by removing the file
        queryClient.setQueryData<File[]>(
          queryKey,
          previousAttachments.filter(file => file.id !== fileId)
        );

        return { previousAttachments };
      },
      onSuccess: () => {
        toast.success('File detached successfully');
      },
      onError: (err, fileId, context: any) => {
        // Revert to previous state on error
        if (context?.previousAttachments) {
          queryClient.setQueryData(queryKey, context.previousAttachments);
        }
        const errorMessage = err instanceof Error ? err.message : 'Failed to detach file';
        toast.error(errorMessage);
      },
      onSettled: () => {
        // Always refetch to ensure we have the correct data
        queryClient.invalidateQueries(queryKey);
      }
    }
  );

  return {
    attachments: attachmentsQuery.data || [],
    isLoading: attachmentsQuery.isLoading,
    error: attachmentsQuery.error ? (attachmentsQuery.error as Error).message : null,
    refetch: attachmentsQuery.refetch,
    addAttachment: addAttachmentMutation.mutate,
    isAddingAttachment: addAttachmentMutation.isLoading,
    removeAttachment: removeAttachmentMutation.mutate,
    isRemovingAttachment: removeAttachmentMutation.isLoading
  };
}

/**
 * Hook for managing file versions
 * 
 * @param fileId - ID of the file to manage versions for
 * @param options - Optional react-query options
 * @returns Object containing versions, loading state, error state, refetch, and uploadNewVersion functions
 */
export function useFileVersions(fileId: string, options?: UseQueryOptions<FileVersion[], Error>) {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  // Create query key for file versions
  const versionsQueryKey = useMemo(() => [FILE_KEYS.FILE_VERSIONS, fileId], [fileId]);

  // Fetch file versions
  const versionsQuery = useQuery<FileVersion[], Error>(
    versionsQueryKey,
    () => getFileVersions(fileId),
    {
      enabled: !!fileId,
      ...options
    }
  );

  // Upload new version mutation
  const uploadVersionMutation = useMutation(
    ({ file, changeNotes }: { file: globalThis.File; changeNotes: string }) => {
      setUploadProgress(0);
      return uploadNewVersion(
        fileId,
        file,
        changeNotes,
        (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        }
      );
    },
    {
      onSuccess: () => {
        // Invalidate relevant queries
        queryClient.invalidateQueries(versionsQueryKey);
        queryClient.invalidateQueries([FILE_KEYS.FILE_DETAIL, fileId]);
        toast.success('New version uploaded successfully');
      },
      onError: (err) => {
        const errorMessage = err instanceof Error ? err.message : 'Failed to upload new version';
        toast.error(errorMessage);
      }
    }
  );

  return {
    versions: versionsQuery.data || [],
    isLoading: versionsQuery.isLoading,
    error: versionsQuery.error ? (versionsQuery.error as Error).message : null,
    refetch: versionsQuery.refetch,
    uploadNewVersion: uploadVersionMutation.mutate,
    isUploading: uploadVersionMutation.isLoading,
    uploadProgress
  };
}

/**
 * Main hook that provides file management capabilities
 * 
 * @returns An object containing all file management functions and state variables
 */
function useFiles() {
  const { isAuthenticated, user } = useAuth();
  const queryClient = useQueryClient();
  
  const fileUpload = useFileUpload();
  const fileDownload = useFileDownload();
  const filePreview = useFilePreview();
  const fileDeletion = useFileDeletion();

  return {
    // Upload operations
    uploadFile: fileUpload.uploadFile,
    isUploading: fileUpload.isUploading,
    uploadProgress: fileUpload.uploadProgress,
    uploadError: fileUpload.error,
    
    // Download operations
    getDownloadUrl: fileDownload.getDownloadUrl,
    isGeneratingDownloadUrl: fileDownload.isGenerating,
    downloadError: fileDownload.error,
    
    // Preview operations
    getPreviewUrl: filePreview.getPreviewUrl,
    isGeneratingPreviewUrl: filePreview.isGenerating,
    previewError: filePreview.error,
    
    // Deletion operations
    deleteFile: fileDeletion.deleteFile,
    isDeleting: fileDeletion.isDeleting,
    deleteError: fileDeletion.error,
    
    // Utility functions
    clearFileCache: () => {
      queryClient.invalidateQueries(FILE_KEYS.FILES);
      queryClient.invalidateQueries(FILE_KEYS.FILE_DETAIL);
      queryClient.invalidateQueries(FILE_KEYS.ATTACHMENTS);
      queryClient.invalidateQueries(FILE_KEYS.FILE_VERSIONS);
    },
    
    // Authentication context
    isAuthenticated,
    user
  };
}

export default useFiles;
export {
  useFileUpload,
  useFileMetadata,
  useFileDownload,
  useFilePreview,
  useFileDeletion,
  useAttachments,
  useFileVersions
};