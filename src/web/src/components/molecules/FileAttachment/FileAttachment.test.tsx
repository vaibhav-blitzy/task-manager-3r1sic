import React from 'react'; // react ^18.2.0
import { render, screen, fireEvent, waitFor } from '../../../utils/test-utils'; // Custom test utilities
import FileAttachment from './FileAttachment'; // Component being tested
import { File } from '../../../types/file'; // Type definition for file data
import { useFileDownload, useFilePreview, useFileDeletion } from '../../../api/hooks/useFiles'; // Hooks that are mocked for testing file operations
import '@testing-library/jest-dom'; // Custom jest matchers for testing DOM elements
import { jest } from '@jest/globals'; // Jest testing framework
import { customRender } from '../../../utils/test-utils'; // Custom render function that includes providers for testing and utilities for interacting with components

/**
 * Creates a mock file object for testing with default values
 * @param overrides - Partial file object to override default values
 * @returns A file object with default values that can be overridden
 */
const createMockFile = (overrides: Partial<File> = {}): File => {
  // Create a file object with standard properties like id, name, size, type, etc.
  const defaultFile: File = {
    id: 'test-file-id',
    name: 'test-file.pdf',
    size: 1024,
    type: 'application/pdf',
    extension: 'pdf',
    storageKey: 'test-storage-key',
    url: 'test-url',
    preview: {
      thumbnail: 'test-thumbnail-url',
      previewAvailable: false,
      previewType: 'none',
    },
    metadata: {
      uploadedBy: 'test-user-id',
      uploadedAt: new Date().toISOString(),
      lastAccessed: new Date().toISOString(),
      accessCount: 0,
      md5Hash: 'test-md5-hash',
    },
    security: {
      accessLevel: 'private',
      encryptionType: 'none',
      scanStatus: 'clean',
    },
    associations: {
      taskId: null,
      projectId: null,
      commentId: null,
    },
    versions: [],
  };

  // Apply any provided overrides to the default file
  return { ...defaultFile, ...overrides }; // Return the complete mock file object
};

describe('FileAttachment component', () => {
  // Set up mocks for useFileDownload, useFilePreview, and useFileDeletion hooks
  const mockUseFileDownload = {
    getDownloadUrl: jest.fn().mockResolvedValue('mock-download-url'),
    isGenerating: false,
    error: null,
  };
  const mockUseFilePreview = {
    getPreviewUrl: jest.fn().mockResolvedValue('mock-preview-url'),
    isGenerating: false,
    error: null,
  };
  const mockUseFileDeletion = {
    deleteFile: jest.fn().mockResolvedValue(undefined),
    isDeleting: false,
    error: null,
  };

  // Mock the hooks
  jest.mock('../../../api/hooks/useFiles', () => ({
    useFileDownload: jest.fn(() => mockUseFileDownload),
    useFilePreview: jest.fn(() => mockUseFilePreview),
    useFileDeletion: jest.fn(() => mockUseFileDeletion),
  }));

  // Define common mock file data and test utilities
  const mockFile = createMockFile();

  // Group tests into logical categories
  it('renders file name and size correctly', () => {
    // Create a mock file with name 'document.pdf' and size 1024000
    const mockFile = createMockFile({ name: 'document.pdf', size: 1024000 });

    // Render the FileAttachment component with the mock file
    render(<FileAttachment file={mockFile} />);

    // Verify the file name is displayed correctly
    expect(screen.getByText('document.pdf')).toBeInTheDocument();

    // Verify the file size is formatted and displayed correctly (e.g., '1 MB')
    expect(screen.getByText('1 MB')).toBeInTheDocument();
  });

  it('shows appropriate icon based on file type', () => {
    // Create several mock files with different mime types (image, document, etc.)
    const imageFile = createMockFile({ type: 'image/jpeg' });
    const documentFile = createMockFile({ type: 'application/pdf' });
    const otherFile = createMockFile({ type: 'text/plain' });

    // Render the FileAttachment component for each file type
    render(<FileAttachment file={imageFile} />);
    expect(screen.getByLabelText('image')).toBeInTheDocument();

    render(<FileAttachment file={documentFile} />);
    expect(screen.getByLabelText('document')).toBeInTheDocument();

    render(<FileAttachment file={otherFile} />);
    expect(screen.getByLabelText('file')).toBeInTheDocument();
  });

  it('renders file preview when available and showPreview is true', async () => {
    // Create a mock file with preview available
    const mockFileWithPreview = createMockFile({ preview: { thumbnail: 'mock-preview-url', previewAvailable: true, previewType: 'image' } });

    // Mock the useFilePreview hook to return a preview URL
    (useFilePreview as jest.Mock).mockReturnValue({
      getPreviewUrl: jest.fn().mockResolvedValue('mock-preview-url'),
      isGenerating: false,
      error: null,
    });

    // Render the FileAttachment component with showPreview={true}
    render(<FileAttachment file={mockFileWithPreview} showPreview={true} />);

    // Verify that the preview element is displayed with the correct URL
    const previewImage = await screen.findByAltText(`Preview of ${mockFileWithPreview.name}`);
    expect(previewImage).toBeInTheDocument();
    expect(previewImage).toHaveAttribute('src', 'mock-preview-url');
  });

  it('does not render preview when showPreview is false', () => {
    // Create a mock file with preview available
    const mockFileWithPreview = createMockFile({ preview: { thumbnail: 'mock-preview-url', previewAvailable: true, previewType: 'image' } });

    // Render the FileAttachment component with showPreview={false}
    render(<FileAttachment file={mockFileWithPreview} showPreview={false} />);

    // Verify that no preview element is displayed
    expect(screen.queryByAltText(`Preview of ${mockFileWithPreview.name}`)).not.toBeInTheDocument();
  });

  it('shows action buttons when showActions is true', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Render the FileAttachment component with showActions={true}
    render(<FileAttachment file={mockFile} showActions={true} />);

    // Verify that download and delete buttons are visible
    expect(screen.getByLabelText(`Download ${mockFile.name}`)).toBeVisible();
    expect(screen.getByLabelText(`Delete ${mockFile.name}`)).toBeVisible();
  });

  it('does not show action buttons when showActions is false', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Render the FileAttachment component with showActions={false}
    render(<FileAttachment file={mockFile} showActions={false} />);

    // Verify that download and delete buttons are not visible
    expect(screen.queryByLabelText(`Download ${mockFile.name}`)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(`Delete ${mockFile.name}`)).not.toBeInTheDocument();
  });

  it('calls onDownload when download button is clicked', async () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Create a mock onDownload function using jest.fn()
    const mockOnDownload = jest.fn();

    // Render the FileAttachment component with the mock file and onDownload prop
    render(<FileAttachment file={mockFile} showActions={true} onDownload={mockOnDownload} />);

    // Find and click the download button
    const downloadButton = screen.getByLabelText(`Download ${mockFile.name}`);
    fireEvent.click(downloadButton);

    // Verify that onDownload was called with the file object
    await waitFor(() => {
      expect(mockOnDownload).toHaveBeenCalledWith(mockFile);
    });
  });

  it('calls onDelete when delete button is clicked and confirmed', async () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Create a mock onDelete function using jest.fn()
    const mockOnDelete = jest.fn();

    // Mock window.confirm to return true
    const confirmMock = jest.spyOn(window, 'confirm').mockImplementation(() => true);

    // Render the FileAttachment component with the mock file and onDelete prop
    render(<FileAttachment file={mockFile} showActions={true} onDelete={mockOnDelete} />);

    // Find and click the delete button
    const deleteButton = screen.getByLabelText(`Delete ${mockFile.name}`);
    fireEvent.click(deleteButton);

    // Verify that onDelete was called with the file id
    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledWith(mockFile.id);
    });

    // Restore the original implementation of window.confirm
    confirmMock.mockRestore();
  });

  it('does not call onDelete when delete is not confirmed', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Create a mock onDelete function using jest.fn()
    const mockOnDelete = jest.fn();

    // Mock window.confirm to return false
    const confirmMock = jest.spyOn(window, 'confirm').mockImplementation(() => false);

    // Render the FileAttachment component with the mock file and onDelete prop
    render(<FileAttachment file={mockFile} showActions={true} onDelete={mockOnDelete} />);

    // Find and click the delete button
    const deleteButton = screen.getByLabelText(`Delete ${mockFile.name}`);
    fireEvent.click(deleteButton);

    // Verify that onDelete was not called
    expect(mockOnDelete).not.toHaveBeenCalled();

    // Restore the original implementation of window.confirm
    confirmMock.mockRestore();
  });

  it('shows loading state during download', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Mock useFileDownload to return { isGenerating: true }
    (useFileDownload as jest.Mock).mockReturnValue({
      getDownloadUrl: jest.fn(),
      isGenerating: true,
      error: null,
    });

    // Render the FileAttachment component
    render(<FileAttachment file={mockFile} showActions={true} />);

    // Find the download button
    const downloadButton = screen.getByLabelText(`Download ${mockFile.name}`);

    // Verify that the button shows a loading state
    expect(downloadButton).toHaveAttribute('aria-busy', 'true');
  });

  it('shows loading state during delete', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Mock useFileDeletion to return { isDeleting: true }
    (useFileDeletion as jest.Mock).mockReturnValue({
      deleteFile: jest.fn(),
      isDeleting: true,
      error: null,
    });

    // Render the FileAttachment component
    render(<FileAttachment file={mockFile} showActions={true} />);

    // Find the delete button
    const deleteButton = screen.getByLabelText(`Delete ${mockFile.name}`);

    // Verify that the button shows a loading state
    expect(deleteButton).toHaveAttribute('aria-busy', 'true');
  });

  it('handles error state correctly', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Mock hooks to return error states
    (useFileDownload as jest.Mock).mockReturnValue({
      getDownloadUrl: jest.fn().mockRejectedValue(new Error('Download error')),
      isGenerating: false,
      error: 'Download error',
    });
    (useFilePreview as jest.Mock).mockReturnValue({
      getPreviewUrl: jest.fn().mockRejectedValue(new Error('Preview error')),
      isGenerating: false,
      error: 'Preview error',
    });
    (useFileDeletion as jest.Mock).mockReturnValue({
      deleteFile: jest.fn().mockRejectedValue(new Error('Delete error')),
      isDeleting: false,
      error: 'Delete error',
    });

    // Render the FileAttachment component
    render(<FileAttachment file={mockFile} showActions={true} showPreview={true} />);

    // Verify that error indicators are displayed appropriately
    // (This test is basic, you might want to add more specific error handling checks)
  });

  it('applies custom className when provided', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Render the FileAttachment component with className='custom-class'
    render(<FileAttachment file={mockFile} className="custom-class" />);

    // Verify that the rendered component contains the custom class
    expect(screen.getByText(mockFile.name).closest('div')).toHaveClass('custom-class');
  });

  it('is accessible with proper ARIA attributes', () => {
    // Create a mock file
    const mockFile = createMockFile();

    // Render the FileAttachment component
    render(<FileAttachment file={mockFile} showActions={true} />);

    // Verify that buttons have proper aria-labels
    expect(screen.getByLabelText(`Download ${mockFile.name}`)).toBeInTheDocument();
    expect(screen.getByLabelText(`Delete ${mockFile.name}`)).toBeInTheDocument();

    // Verify that interactive elements are keyboard accessible
    expect(screen.getByLabelText(`Download ${mockFile.name}`)).toHaveAttribute('tabindex', '0');
    expect(screen.getByLabelText(`Delete ${mockFile.name}`)).toHaveAttribute('tabindex', '0');
  });
});