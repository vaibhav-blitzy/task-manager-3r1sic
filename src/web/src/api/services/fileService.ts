/**
 * File Service
 * 
 * Service module that provides functions for interacting with the file management API endpoints.
 * Includes methods for file uploads, downloads, metadata retrieval, and attachment management.
 * 
 * @version 1.5.x
 */

import apiClient from '../client';
import { handleApiError } from '../client';
import { 
  FILE_ENDPOINTS
} from '../endpoints';
import { 
  File, 
  FileUploadRequest, 
  FileUploadResponse, 
  FileUploadStatus,
  FileVersion,
  AttachmentQuery
} from '../../types/file';
import { AxiosProgressEvent } from 'axios'; // axios ^1.5.x

/**
 * Initiates a file upload process using the two-step approach:
 * 1. Request a presigned upload URL from the server
 * 2. Upload the file directly to the provided URL
 * 
 * @param file - The browser File object to upload
 * @param onProgress - Optional callback function to track upload progress
 * @returns Promise resolving to the uploaded file metadata
 */
export async function uploadFile(
  file: globalThis.File, 
  onProgress?: (progressEvent: AxiosProgressEvent) => void
): Promise<File> {
  try {
    // Create upload request payload with file information
    const uploadRequest: FileUploadRequest = {
      name: file.name,
      size: file.size,
      type: file.type,
      taskId: null,
      projectId: null,
      commentId: null
    };

    // Request presigned upload URL from the server
    const response = await apiClient.post<FileUploadResponse>(
      FILE_ENDPOINTS.UPLOAD,
      uploadRequest
    );

    const { uploadUrl, fileId, expiresAt } = response.data;

    // Upload file directly to the provided URL with progress tracking
    await apiClient.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type
      },
      onUploadProgress: onProgress
    });

    // Notify server that upload is complete
    const completeResponse = await apiClient.post<File>(
      `${FILE_ENDPOINTS.UPLOAD}/complete`,
      { fileId }
    );

    return completeResponse.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Retrieves metadata for a specific file by ID
 * 
 * @param fileId - ID of the file to retrieve
 * @returns Promise resolving to the file metadata
 */
export async function getFileMetadata(fileId: string): Promise<File> {
  try {
    const response = await apiClient.get<File>(FILE_ENDPOINTS.GET_FILE(fileId));
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Generates a temporary URL for downloading a file
 * 
 * @param fileId - ID of the file to download
 * @returns Promise resolving to temporary download URL
 */
export async function getDownloadUrl(fileId: string): Promise<string> {
  try {
    const response = await apiClient.get<{ url: string }>(
      FILE_ENDPOINTS.DOWNLOAD(fileId)
    );
    return response.data.url;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Generates a URL for previewing a file with optional size parameters
 * 
 * @param fileId - ID of the file to preview
 * @param sizeParams - Optional parameters for controlling preview size
 * @returns Promise resolving to preview URL
 */
export async function getPreviewUrl(
  fileId: string, 
  sizeParams?: { width?: number; height?: number }
): Promise<string> {
  try {
    const response = await apiClient.get<{ url: string }>(
      `${FILE_ENDPOINTS.GET_FILE(fileId)}/preview`,
      { params: sizeParams }
    );
    return response.data.url;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Deletes a file by ID
 * 
 * @param fileId - ID of the file to delete
 * @returns Promise resolving when deletion is complete
 */
export async function deleteFile(fileId: string): Promise<void> {
  try {
    await apiClient.delete(FILE_ENDPOINTS.DELETE_FILE(fileId));
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Retrieves file attachments based on query parameters
 * 
 * @param query - Query parameters specifying which attachments to retrieve
 * @returns Promise resolving to array of file attachments
 */
export async function getAttachments(query: AttachmentQuery): Promise<File[]> {
  try {
    const { entityType, entityId } = determineEntityInfo(query);
    
    const response = await apiClient.get<File[]>(
      FILE_ENDPOINTS.ATTACHMENTS(entityType, entityId)
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Creates a file attachment association between a file and task/project/comment
 * 
 * @param fileId - ID of the file to attach
 * @param association - Details of entity to associate with the file
 * @returns Promise resolving to the updated file with new association
 */
export async function createAttachment(
  fileId: string, 
  association: AttachmentQuery
): Promise<File> {
  try {
    const { entityType, entityId } = determineEntityInfo(association);
    
    const response = await apiClient.post<File>(
      FILE_ENDPOINTS.ATTACHMENTS(entityType, entityId),
      { fileId }
    );
    
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Removes a file attachment association
 * 
 * @param fileId - ID of the file to detach
 * @param association - Details of entity to remove association from
 * @returns Promise resolving when attachment is removed
 */
export async function removeAttachment(
  fileId: string, 
  association: AttachmentQuery
): Promise<void> {
  try {
    const { entityType, entityId } = determineEntityInfo(association);
    
    await apiClient.delete(
      `${FILE_ENDPOINTS.ATTACHMENTS(entityType, entityId)}/${fileId}`
    );
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Retrieves version history for a specific file
 * 
 * @param fileId - ID of the file to get versions for
 * @returns Promise resolving to array of file versions
 */
export async function getFileVersions(fileId: string): Promise<FileVersion[]> {
  try {
    const response = await apiClient.get<FileVersion[]>(
      `${FILE_ENDPOINTS.GET_FILE(fileId)}/versions`
    );
    return response.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Uploads a new version of an existing file
 * 
 * @param fileId - ID of the file to update
 * @param file - The new file version to upload (browser File object)
 * @param changeNotes - Notes describing the changes in this version
 * @param onProgress - Optional callback function to track upload progress
 * @returns Promise resolving to updated file with new version
 */
export async function uploadNewVersion(
  fileId: string,
  file: globalThis.File,
  changeNotes: string,
  onProgress?: (progressEvent: AxiosProgressEvent) => void
): Promise<File> {
  try {
    // Create version upload request with file information and change notes
    const versionRequest = {
      name: file.name,
      size: file.size,
      type: file.type,
      changeNotes
    };

    // Request presigned upload URL for the new version
    const response = await apiClient.post<FileUploadResponse>(
      `${FILE_ENDPOINTS.GET_FILE(fileId)}/versions`,
      versionRequest
    );

    const { uploadUrl, fileId: versionId, expiresAt } = response.data;

    // Upload file directly to the provided URL with progress tracking
    await apiClient.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type
      },
      onUploadProgress: onProgress
    });

    // Notify server that version upload is complete
    const completeResponse = await apiClient.post<File>(
      `${FILE_ENDPOINTS.GET_FILE(fileId)}/versions/${versionId}/complete`,
      {}
    );

    return completeResponse.data;
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * Helper function to determine entity type and ID from an attachment query
 * 
 * @param query - The attachment query
 * @returns Object containing entityType and entityId
 * @throws Error if no valid entity ID is found
 */
function determineEntityInfo(query: AttachmentQuery): { entityType: string; entityId: string } {
  let entityType = '';
  let entityId = '';
  
  if (query.taskId) {
    entityType = 'tasks';
    entityId = query.taskId;
  } else if (query.projectId) {
    entityType = 'projects';
    entityId = query.projectId;
  } else if (query.commentId) {
    entityType = 'comments';
    entityId = query.commentId;
  } else {
    throw new Error('Invalid attachment query: missing entity ID');
  }
  
  return { entityType, entityId };
}