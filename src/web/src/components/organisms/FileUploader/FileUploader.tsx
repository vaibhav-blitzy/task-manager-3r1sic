import React, { useState, useRef, useCallback, useMemo } from 'react';
import classNames from 'classnames';
import { toast } from 'react-toastify';
import { FiUpload, FiFile, FiX, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

import { Button } from '../../atoms/Button/Button';
import { Icon } from '../../atoms/Icon/Icon';
import { useFileUpload, useAttachments } from '../../../api/hooks/useFiles';
import { File, FileUploadStatus } from '../../../types/file';
import {
  isValidFile,
  formatFileSize,
  getIconForFileType
} from '../../../features/fileManagement/utils';

/**
 * Props for the FileUploader component
 */
interface FileUploaderProps {
  /**
   * Whether to allow multiple file uploads
   * @default false
   */
  multiple?: boolean;
  
  /**
   * Maximum number of files that can be uploaded at once
   * @default 5
   */
  maxFiles?: number;
  
  /**
   * Maximum file size in megabytes
   * @default 25
   */
  maxSizeInMB?: number;
  
  /**
   * Array of allowed MIME types. If not provided, all types defined in ALLOWED_FILE_TYPES will be accepted
   */
  allowedTypes?: string[];
  
  /**
   * ID of the task to associate the upload with
   */
  taskId?: string;
  
  /**
   * ID of the project to associate the upload with
   */
  projectId?: string;
  
  /**
   * ID of the comment to associate the upload with
   */
  commentId?: string;
  
  /**
   * Callback fired when uploads complete successfully
   */
  onUploadComplete?: (files: File[]) => void;
  
  /**
   * Callback fired when an error occurs during upload
   */
  onUploadError?: (error: Error) => void;
  
  /**
   * Additional CSS class names
   */
  className?: string;
  
  /**
   * Custom label for the file input
   */
  label?: string;
}

/**
 * A component for uploading files to the Task Management System.
 * Supports drag-and-drop, file selection, progress tracking, and file validation.
 */
const FileUploader: React.FC<FileUploaderProps> = ({
  multiple = false,
  maxFiles = 5,
  maxSizeInMB = 25,
  allowedTypes,
  taskId,
  projectId,
  commentId,
  onUploadComplete,
  onUploadError,
  className,
  label = 'Upload Files'
}) => {
  // References
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // File upload hook
  const { uploadFile, isUploading, uploadProgress, error } = useFileUpload();
  
  // Attachments hook for attaching files to tasks/projects/comments
  const { addAttachment, isAddingAttachment } = useAttachments({
    taskId,
    projectId,
    commentId
  });
  
  // State
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFiles, setSelectedFiles] = useState<globalThis.File[]>([]);
  const [fileStatus, setFileStatus] = useState<Record<string, FileUploadStatus>>({});
  const [fileProgress, setFileProgress] = useState<Record<string, number>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Check if a file is being processed
  const isProcessing = isUploading || isAddingAttachment;
  
  /**
   * Handles file input change event
   */
  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;
    
    const files = Array.from(event.target.files);
    
    // Check if number of files exceeds maximum allowed
    if (multiple === false && files.length > 1) {
      toast.error(`Only one file can be uploaded at a time`);
      return;
    }
    
    if (files.length > maxFiles) {
      toast.error(`Maximum ${maxFiles} files can be uploaded at once`);
      return;
    }
    
    // Validate each file
    const validFiles: globalThis.File[] = [];
    const newErrors: Record<string, string> = {};
    
    files.forEach(file => {
      if (!isValidFile(file as any, maxSizeInMB, allowedTypes)) {
        const error = file.size > maxSizeInMB * 1024 * 1024
          ? `File exceeds maximum size of ${maxSizeInMB}MB`
          : 'File type not supported';
        
        newErrors[file.name] = error;
      } else {
        validFiles.push(file);
      }
    });
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(prev => ({ ...prev, ...newErrors }));
    }
    
    if (validFiles.length > 0) {
      // Initialize file status and progress
      const newFileStatus: Record<string, FileUploadStatus> = {};
      const newFileProgress: Record<string, number> = {};
      
      validFiles.forEach(file => {
        newFileStatus[file.name] = FileUploadStatus.PENDING;
        newFileProgress[file.name] = 0;
      });
      
      setSelectedFiles(prev => [...prev, ...validFiles]);
      setFileStatus(prev => ({ ...prev, ...newFileStatus }));
      setFileProgress(prev => ({ ...prev, ...newFileProgress }));
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [multiple, maxFiles, maxSizeInMB, allowedTypes]);
  
  /**
   * Drag event handlers
   */
  const handleDragEnter = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);
  
  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!dragActive) setDragActive(true);
  }, [dragActive]);
  
  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const fileList = e.dataTransfer.files;
      
      // Create a synthetic event object to reuse handleFileChange logic
      const syntheticEvent = {
        target: {
          files: fileList
        }
      } as React.ChangeEvent<HTMLInputElement>;
      
      handleFileChange(syntheticEvent);
    }
  }, [handleFileChange]);
  
  /**
   * Opens file dialog when the dropzone is clicked
   */
  const handleDropzoneClick = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);
  
  /**
   * Removes a file from the selected files list
   */
  const handleRemoveFile = useCallback((fileName: string) => {
    setSelectedFiles(prev => prev.filter(file => file.name !== fileName));
    setFileStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[fileName];
      return newStatus;
    });
    setFileProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileName];
      return newProgress;
    });
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[fileName];
      return newErrors;
    });
  }, []);
  
  /**
   * Uploads selected files
   */
  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0 || isProcessing) return;
    
    const uploadedFiles: File[] = [];
    const newErrors: Record<string, string> = {};
    
    for (const file of selectedFiles) {
      try {
        // Update status to uploading
        setFileStatus(prev => ({
          ...prev,
          [file.name]: FileUploadStatus.UPLOADING
        }));
        
        // Upload file
        const uploadedFile = await uploadFile(file);
        
        // Update progress
        setFileProgress(prev => ({
          ...prev,
          [file.name]: 100
        }));
        
        // Update status to completed
        setFileStatus(prev => ({
          ...prev,
          [file.name]: FileUploadStatus.COMPLETED
        }));
        
        // If we have a taskId, projectId, or commentId, attach the file
        if (taskId || projectId || commentId) {
          await addAttachment(uploadedFile.id);
        }
        
        uploadedFiles.push(uploadedFile);
      } catch (err) {
        console.error(`Error uploading file: ${file.name}`, err);
        
        // Update status to failed
        setFileStatus(prev => ({
          ...prev,
          [file.name]: FileUploadStatus.FAILED
        }));
        
        // Add error message
        const errorMessage = err instanceof Error ? err.message : 'Upload failed';
        newErrors[file.name] = errorMessage;
        
        // Call error callback if provided
        if (onUploadError) {
          onUploadError(err instanceof Error ? err : new Error('Upload failed'));
        }
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(prev => ({ ...prev, ...newErrors }));
    }
    
    // Call complete callback if provided and we have uploaded files
    if (uploadedFiles.length > 0 && onUploadComplete) {
      onUploadComplete(uploadedFiles);
    }
    
  }, [selectedFiles, isProcessing, uploadFile, addAttachment, taskId, projectId, commentId, onUploadComplete, onUploadError]);
  
  /**
   * Updates file progress during upload
   */
  React.useEffect(() => {
    if (isUploading && selectedFiles.length > 0) {
      // Update progress for the current file being uploaded
      const currentFile = selectedFiles.find(
        file => fileStatus[file.name] === FileUploadStatus.UPLOADING
      );
      
      if (currentFile) {
        setFileProgress(prev => ({
          ...prev,
          [currentFile.name]: uploadProgress
        }));
      }
    }
  }, [isUploading, uploadProgress, selectedFiles, fileStatus]);
  
  /**
   * Updates error state when upload hook reports an error
   */
  React.useEffect(() => {
    if (error) {
      const currentFile = selectedFiles.find(
        file => fileStatus[file.name] === FileUploadStatus.UPLOADING
      );
      
      if (currentFile) {
        setErrors(prev => ({
          ...prev,
          [currentFile.name]: error
        }));
        
        setFileStatus(prev => ({
          ...prev,
          [currentFile.name]: FileUploadStatus.FAILED
        }));
      }
    }
  }, [error, selectedFiles, fileStatus]);
  
  // Calculate if upload button should be enabled
  const canUpload = useMemo(() => {
    return selectedFiles.length > 0 && 
           !isProcessing && 
           selectedFiles.every(file => fileStatus[file.name] !== FileUploadStatus.UPLOADING);
  }, [selectedFiles, isProcessing, fileStatus]);
  
  return (
    <div className={classNames('file-uploader', className)}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={allowedTypes?.join(',')}
        onChange={handleFileChange}
        style={{ display: 'none' }}
        aria-label="File upload"
      />
      
      {/* Dropzone area */}
      <div
        className={classNames(
          'file-uploader__dropzone',
          'p-6 border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors',
          {
            'border-primary-500 bg-primary-50': dragActive,
            'border-gray-300 bg-gray-50 hover:border-primary-300 hover:bg-gray-100': !dragActive
          }
        )}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleDropzoneClick}
        role="button"
        tabIndex={0}
        aria-label={label}
      >
        <div className="file-uploader__icon mb-4 text-gray-400">
          <Icon icon={FiUpload} size={32} />
        </div>
        
        <div className="file-uploader__text text-center">
          <p className="text-sm font-medium text-gray-700 mb-1">
            Drag and drop files here, or click to select files
          </p>
          <p className="text-xs text-gray-500">
            {multiple
              ? `Upload up to ${maxFiles} files (max ${maxSizeInMB}MB each)`
              : `Upload a file (max ${maxSizeInMB}MB)`}
          </p>
          {allowedTypes && allowedTypes.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Allowed types: {allowedTypes.map(type => type.split('/')[1]).join(', ')}
            </p>
          )}
        </div>
        
        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={(e) => {
            e.stopPropagation();
            handleDropzoneClick();
          }}
        >
          Select Files
        </Button>
      </div>
      
      {/* Selected files list */}
      {selectedFiles.length > 0 && (
        <div className="file-uploader__files mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Selected Files ({selectedFiles.length})
          </h4>
          <ul className="file-uploader__file-list space-y-2">
            {selectedFiles.map(file => (
              <FileItem
                key={file.name}
                file={file}
                status={fileStatus[file.name] || FileUploadStatus.PENDING}
                progress={fileProgress[file.name] || 0}
                error={errors[file.name]}
                onRemove={() => handleRemoveFile(file.name)}
              />
            ))}
          </ul>
          
          <div className="file-uploader__actions mt-4">
            <Button
              variant="primary"
              disabled={!canUpload}
              isLoading={isProcessing}
              onClick={handleUpload}
            >
              Upload Files
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Individual file item component with status and controls
 */
interface FileItemProps {
  file: globalThis.File;
  status: FileUploadStatus;
  progress: number;
  error?: string;
  onRemove: () => void;
}

const FileItem: React.FC<FileItemProps> = ({
  file,
  status,
  progress,
  error,
  onRemove
}) => {
  // Get file icon based on type
  const fileIcon = useMemo(() => getIconForFileType(file.type), [file.type]);
  
  // Status icon based on status
  const statusIcon = useMemo(() => {
    switch (status) {
      case FileUploadStatus.COMPLETED:
        return <Icon icon={FiCheckCircle} className="text-green-500" />;
      case FileUploadStatus.FAILED:
        return <Icon icon={FiAlertCircle} className="text-red-500" />;
      default:
        return null;
    }
  }, [status]);
  
  return (
    <li
      className={classNames(
        'file-uploader__file-item',
        'flex items-center justify-between p-3 border rounded-md',
        {
          'border-green-300 bg-green-50': status === FileUploadStatus.COMPLETED,
          'border-red-300 bg-red-50': status === FileUploadStatus.FAILED,
          'border-gray-300 bg-white': status !== FileUploadStatus.COMPLETED && status !== FileUploadStatus.FAILED
        }
      )}
    >
      <div className="file-uploader__file-info flex items-center">
        <div className="file-uploader__file-icon mr-3 text-gray-400">
          {fileIcon}
        </div>
        
        <div className="file-uploader__file-details">
          <div className="file-uploader__file-name text-sm font-medium text-gray-700">
            {file.name}
          </div>
          
          <div className="file-uploader__file-meta flex items-center text-xs text-gray-500">
            <span className="file-uploader__file-size">
              {formatFileSize(file.size)}
            </span>
            
            {error && (
              <span className="file-uploader__file-error ml-2 text-red-500">
                {error}
              </span>
            )}
          </div>
          
          {status === FileUploadStatus.UPLOADING && (
            <div className="file-uploader__progress mt-1 w-full max-w-xs">
              <ProgressBar progress={progress} />
            </div>
          )}
        </div>
      </div>
      
      <div className="file-uploader__file-actions flex items-center">
        {statusIcon && (
          <span className="file-uploader__status-icon mr-2">
            {statusIcon}
          </span>
        )}
        
        {status !== FileUploadStatus.UPLOADING && (
          <button
            type="button"
            className="file-uploader__remove-button text-gray-400 hover:text-gray-600 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            aria-label={`Remove file: ${file.name}`}
          >
            <Icon icon={FiX} size={16} />
          </button>
        )}
      </div>
    </li>
  );
};

/**
 * Progress bar component for visualizing upload progress
 */
interface ProgressBarProps {
  progress: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress }) => {
  const progressPercentage = Math.min(100, Math.max(0, progress));
  
  return (
    <div className="progress-bar w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
      <div
        className="progress-bar__fill h-full bg-primary-500 transition-all duration-300 ease-in-out"
        style={{ width: `${progressPercentage}%` }}
        role="progressbar"
        aria-valuenow={progressPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
};

export default FileUploader;