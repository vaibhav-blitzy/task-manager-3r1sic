/**
 * Type definitions for file-related entities in the Task Management System.
 * These interfaces support the File Attachments feature which allows users to attach
 * and share files with tasks and projects.
 */

/**
 * Enum representing possible file upload statuses
 */
export enum FileUploadStatus {
  PENDING = 'PENDING',
  UPLOADING = 'UPLOADING',
  SCANNING = 'SCANNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

/**
 * Enum representing possible file access levels
 */
export enum FileAccessLevel {
  PUBLIC = 'PUBLIC',
  PRIVATE = 'PRIVATE',
  SHARED = 'SHARED'
}

/**
 * Enum representing possible file scan statuses
 */
export enum FileScanStatus {
  PENDING = 'PENDING',
  CLEAN = 'CLEAN',
  INFECTED = 'INFECTED',
  UNKNOWN = 'UNKNOWN'
}

/**
 * Defines metadata properties for files in the system
 */
export interface FileMetadata {
  /**
   * ID of the user who uploaded the file
   */
  uploadedBy: string;
  
  /**
   * ISO date string of when the file was uploaded
   */
  uploadedAt: string;
  
  /**
   * ISO date string of when the file was last accessed
   */
  lastAccessed: string;
  
  /**
   * Number of times the file has been accessed
   */
  accessCount: number;
  
  /**
   * MD5 hash of the file for integrity verification
   */
  md5Hash: string;
}

/**
 * Defines security-related properties for files
 */
export interface FileSecurity {
  /**
   * Access level controlling who can view the file
   */
  accessLevel: FileAccessLevel;
  
  /**
   * Type of encryption used for the file, or 'none'
   */
  encryptionType: string;
  
  /**
   * Status of virus/malware scan
   */
  scanStatus: FileScanStatus;
}

/**
 * Defines preview-related properties for files
 */
export interface FilePreview {
  /**
   * URL to file thumbnail, if available
   */
  thumbnail: string;
  
  /**
   * Whether a preview is available for this file
   */
  previewAvailable: boolean;
  
  /**
   * Type of preview (image/pdf/document/none)
   */
  previewType: string;
}

/**
 * Defines association properties linking files to other entities
 */
export interface FileAssociation {
  /**
   * ID of associated task, or null
   */
  taskId: string | null;
  
  /**
   * ID of associated project, or null
   */
  projectId: string | null;
  
  /**
   * ID of associated comment, or null
   */
  commentId: string | null;
}

/**
 * Defines properties for file versioning
 */
export interface FileVersion {
  /**
   * Unique identifier for the version
   */
  id: string;
  
  /**
   * Internal storage key for the version
   */
  storageKey: string;
  
  /**
   * Size of the version in bytes
   */
  size: number;
  
  /**
   * ID of user who uploaded this version
   */
  uploadedBy: string;
  
  /**
   * ISO date string of when this version was uploaded
   */
  uploadedAt: string;
  
  /**
   * Notes describing changes in this version
   */
  changeNotes: string;
}

/**
 * Main file interface that represents a file in the Task Management System
 */
export interface File {
  /**
   * Unique identifier for the file
   */
  id: string;
  
  /**
   * Original filename
   */
  name: string;
  
  /**
   * Size in bytes
   */
  size: number;
  
  /**
   * MIME type of the file
   */
  type: string;
  
  /**
   * File extension
   */
  extension: string;
  
  /**
   * Internal storage identifier
   */
  storageKey: string;
  
  /**
   * Temporary access URL for the file
   */
  url: string;
  
  /**
   * Preview information
   */
  preview: FilePreview;
  
  /**
   * File metadata
   */
  metadata: FileMetadata;
  
  /**
   * Security information
   */
  security: FileSecurity;
  
  /**
   * Entity associations
   */
  associations: FileAssociation;
  
  /**
   * Version history
   */
  versions: FileVersion[];
}

/**
 * Request type for initiating a file upload
 */
export interface FileUploadRequest {
  /**
   * Name of the file to upload
   */
  name: string;
  
  /**
   * Size of the file in bytes
   */
  size: number;
  
  /**
   * MIME type of the file
   */
  type: string;
  
  /**
   * Optional task to associate the file with
   */
  taskId: string | null;
  
  /**
   * Optional project to associate the file with
   */
  projectId: string | null;
  
  /**
   * Optional comment to associate the file with
   */
  commentId: string | null;
}

/**
 * Response type containing information needed for uploading a file
 */
export interface FileUploadResponse {
  /**
   * Pre-signed URL for uploading the file
   */
  uploadUrl: string;
  
  /**
   * ID assigned to the file
   */
  fileId: string;
  
  /**
   * ISO date string when the upload URL expires
   */
  expiresAt: string;
}