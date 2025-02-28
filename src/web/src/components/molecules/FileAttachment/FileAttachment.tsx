import React, { useState, useCallback } from 'react';
import classNames from 'classnames';
import { FiDownload, FiTrash2, FiFile, FiImage, FiFileText, FiPaperclip } from 'react-icons/fi';
import { IconType } from 'react-icons';

import { useFileDownload, useFilePreview, useFileDeletion } from '../../../api/hooks/useFiles';
import { Button } from '../../atoms/Button/Button';
import Icon from '../../atoms/Icon/Icon';
import { File } from '../../../types/file';
import { formatFileSize } from '../../../utils/formatting';

interface FileAttachmentProps {
  file: File;
  showPreview?: boolean;
  showActions?: boolean;
  onDelete?: (fileId: string) => void;
  onDownload?: (file: File) => void;
  className?: string;
}

/**
 * A component that displays a file attachment with preview, metadata, and action buttons
 */
const FileAttachment: React.FC<FileAttachmentProps> = ({
  file,
  showPreview = true,
  showActions = true,
  onDelete,
  onDownload,
  className,
}) => {
  const { getDownloadUrl, isGenerating: isGeneratingDownloadUrl, error: downloadError } = useFileDownload();
  const { getPreviewUrl, isGenerating: isGeneratingPreviewUrl, error: previewError } = useFilePreview();
  const { deleteFile, isDeleting, error: deleteError } = useFileDeletion();
  
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isImageLoading, setIsImageLoading] = useState<boolean>(false);
  
  // Determine which icon to show based on file type
  const FileIcon = getFileIcon(file.type);
  
  // Format file size for display
  const formattedSize = formatFileSize(file.size);
  
  // Load preview if showPreview is true and file type supports previews
  React.useEffect(() => {
    if (showPreview && file.preview?.previewAvailable) {
      setIsImageLoading(true);
      getPreviewUrl(file.id, { width: 100, height: 100 })
        .then(url => {
          setPreviewUrl(url);
        })
        .catch(error => {
          console.error('Error loading preview:', error);
        })
        .finally(() => {
          setIsImageLoading(false);
        });
    }
  }, [file.id, file.preview?.previewAvailable, getPreviewUrl, showPreview]);
  
  // Handle download button click
  const handleDownload = useCallback(async () => {
    try {
      const url = await getDownloadUrl(file.id);
      
      // Create a hidden anchor and trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      // Call onDownload callback if provided
      if (onDownload) {
        onDownload(file);
      }
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  }, [file, getDownloadUrl, onDownload]);
  
  // Handle delete button click
  const handleDelete = useCallback(async () => {
    if (window.confirm(`Are you sure you want to delete ${file.name}?`)) {
      try {
        await deleteFile(file.id);
        
        // Call onDelete callback if provided
        if (onDelete) {
          onDelete(file.id);
        }
      } catch (error) {
        console.error('Error deleting file:', error);
      }
    }
  }, [file, deleteFile, onDelete]);
  
  return (
    <div 
      className={classNames(
        'flex items-center p-3 border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700',
        {
          'opacity-75': isDeleting || isGeneratingDownloadUrl,
        },
        className
      )}
      aria-busy={isDeleting || isGeneratingDownloadUrl}
    >
      {/* File preview or icon */}
      <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center">
        {showPreview && previewUrl ? (
          <img 
            src={previewUrl} 
            alt={`Preview of ${file.name}`} 
            className="w-10 h-10 object-cover rounded-sm" 
            onLoad={() => setIsImageLoading(false)}
          />
        ) : (
          <Icon 
            icon={FileIcon} 
            size={24} 
            className="text-gray-500 dark:text-gray-400" 
            aria-hidden="true" 
          />
        )}
      </div>
      
      {/* File information */}
      <div className="ml-3 flex-grow min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate" title={file.name}>
          {file.name}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {formattedSize} • {file.metadata?.uploadedAt && new Date(file.metadata.uploadedAt).toLocaleDateString()}
        </p>
      </div>
      
      {/* Action buttons */}
      {showActions && (
        <div className="flex-shrink-0 ml-2 space-x-2">
          <Button 
            variant="outline"
            size="sm"
            aria-label={`Download ${file.name}`}
            title="Download file"
            disabled={isGeneratingDownloadUrl || isDeleting}
            icon={<FiDownload size={16} />}
            onClick={handleDownload}
          />
          {onDelete && (
            <Button 
              variant="outline"
              size="sm"
              aria-label={`Delete ${file.name}`}
              title="Delete file"
              disabled={isDeleting}
              icon={<FiTrash2 size={16} />}
              onClick={handleDelete}
              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            />
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Determines the appropriate icon based on file type
 */
function getFileIcon(fileType: string): IconType {
  // Check for image types
  if (fileType.startsWith('image/')) {
    return FiImage;
  }
  
  // Check for document types
  if (
    fileType === 'application/pdf' ||
    fileType === 'application/msword' ||
    fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    fileType === 'text/plain'
  ) {
    return FiFileText;
  }
  
  // Check for spreadsheet types
  if (
    fileType === 'application/vnd.ms-excel' ||
    fileType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ) {
    return FiFileText;
  }
  
  // Check for presentation types
  if (
    fileType === 'application/vnd.ms-powerpoint' ||
    fileType === 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  ) {
    return FiFileText;
  }
  
  // Default file icon
  return FiFile;
}

export default FileAttachment;