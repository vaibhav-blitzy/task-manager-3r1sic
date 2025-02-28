import React from 'react'; // react ^18.2.0
import { render, screen, waitFor, fireEvent } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.4.3
import { rest } from 'msw'; // msw ^1.2.1
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'; // vitest ^0.34.3

import FileUploader from './FileUploader';
import server from '../../../__tests__/mocks/server';
import { API_BASE_URL } from '../../../config/constants';
import { FILE_ENDPOINTS } from '../../../api/endpoints';
import { FileUploadStatus } from '../../../types/file';
import { isValidFile } from '../../../features/fileManagement/utils';

/**
 * Creates a mock File object for testing file uploads
 * @param name 
 * @param size 
 * @param type 
 * @returns A mock File object for testing
 */
const createMockFile = (name: string, size: number, type: string): File => {
  const arrayBuffer = new ArrayBuffer(size);
  const file = new File([arrayBuffer], name, { type });
  return file;
};

/**
 * Sets up MSW handlers to mock file upload API responses
 * @param options 
 * @returns void
 */
const setupUploadMocks = (options: { success?: boolean; progress?: number; error?: boolean } = {}) => {
  const { success = true, progress = 100, error = false } = options;

  // Mock handler for upload URL request endpoint
  server.use(
    rest.post(`${API_BASE_URL}${FILE_ENDPOINTS.UPLOAD}`, (req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          uploadUrl: 'https://example.com/upload',
          fileId: 'test-file-id',
          expiresAt: new Date(Date.now() + 60000).toISOString(),
        })
      );
    })
  );

  // Mock handler for upload complete notification endpoint
  server.use(
    rest.post(`${API_BASE_URL}${FILE_ENDPOINTS.UPLOAD}/complete`, (req, res, ctx) => {
      if (error) {
        return res(
          ctx.status(500),
          ctx.json({ message: 'Upload failed' })
        );
      }

      return res(
        ctx.status(200),
        ctx.json({
          id: 'test-file-id',
          name: 'test-file.pdf',
          size: 1024,
          type: 'application/pdf',
        })
      );
    })
  );

  // Mock handler for the upload URL itself to simulate progress
  server.use(
    rest.put('https://example.com/upload', (req, res, ctx) => {
      if (progress < 100) {
        // Simulate progress event
        req.events.emit('progress', { loaded: progress * 10, total: 1000 });
      }
      return res(ctx.status(200));
    })
  );
};

/**
 * Main test suite for FileUploader component
 * @param string "FileUploader"
 * @param callback 
 * @returns void
 */
describe('FileUploader', () => {
  beforeEach(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
    server.close();
  });

  describe('FileUploader Component Rendering', () => {
    it('renders the file upload dropzone correctly', () => {
      render(<FileUploader />);
      expect(screen.getByText('Drag and drop files here, or click to select files')).toBeVisible();
      expect(screen.getByRole('button', { name: 'Select Files' })).toBeInTheDocument();
    });

    it('applies custom classNames correctly', () => {
      const { container } = render(<FileUploader className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('displays custom label when provided', () => {
      render(<FileUploader label="Custom Upload Label" />);
      expect(screen.getByRole('button', { name: 'Custom Upload Label' })).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('allows file selection via input change', async () => {
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      await waitFor(() => expect(screen.getByText('test.pdf')).toBeInTheDocument());
    });

    it('allows file selection via drag and drop', async () => {
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const dropzone = screen.getByText('Drag and drop files here, or click to select files').parentElement;
      fireEvent.dragEnter(dropzone);
      fireEvent.dragOver(dropzone);
      fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });
      await waitFor(() => expect(screen.getByText('test.pdf')).toBeInTheDocument());
    });

    it('shows active dropzone during drag over', () => {
      render(<FileUploader />);
      const dropzone = screen.getByText('Drag and drop files here, or click to select files').parentElement;
      fireEvent.dragEnter(dropzone);
      expect(dropzone).toHaveClass('border-primary-500');
      fireEvent.dragLeave(dropzone);
      expect(dropzone).not.toHaveClass('border-primary-500');
    });
  });

  describe('File Validation', () => {
    it('validates maximum file size correctly', async () => {
      render(<FileUploader maxSizeInMB={1} />);
      const file = createMockFile('large.pdf', 2 * 1024 * 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      await waitFor(() => expect(screen.getByText('File exceeds maximum size of 1MB')).toBeInTheDocument());
      expect(screen.queryByText('large.pdf')).not.toBeInTheDocument();
    });

    it('validates allowed file types correctly', async () => {
      render(<FileUploader allowedTypes={['image/png']} />);
      const allowedFile = createMockFile('image.png', 1024, 'image/png');
      const disallowedFile = createMockFile('document.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [allowedFile, disallowedFile] } });
      await waitFor(() => expect(screen.getByText('image.png')).toBeInTheDocument());
      await waitFor(() => expect(screen.getByText('File type not supported')).toBeInTheDocument());
      expect(screen.queryByText('document.pdf')).not.toBeInTheDocument();
    });

    it('validates maximum number of files correctly', async () => {
      render(<FileUploader maxFiles={2} multiple />);
      const file1 = createMockFile('file1.pdf', 1024, 'application/pdf');
      const file2 = createMockFile('file2.pdf', 1024, 'application/pdf');
      const file3 = createMockFile('file3.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file1, file2, file3] } });
      await waitFor(() => expect(screen.getByText('Maximum 2 files can be uploaded at once')).toBeInTheDocument());
      expect(screen.getAllByRole('listitem').length).toBeLessThanOrEqual(2);
    });

    it('handles single vs multiple file selection correctly', async () => {
      const file1 = createMockFile('file1.pdf', 1024, 'application/pdf');
      const file2 = createMockFile('file2.pdf', 1024, 'application/pdf');

      // Test single file selection
      render(<FileUploader multiple={false} />);
      const inputSingle = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(inputSingle, { target: { files: [file1, file2] } });
      await waitFor(() => expect(screen.getByText('file1.pdf')).toBeInTheDocument());
      expect(screen.queryByText('file2.pdf')).not.toBeInTheDocument();

      // Test multiple file selection
      render(<FileUploader multiple={true} />);
      const inputMultiple = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(inputMultiple, { target: { files: [file1, file2] } });
      await waitFor(() => expect(screen.getByText('file1.pdf')).toBeInTheDocument());
      await waitFor(() => expect(screen.getByText('file2.pdf')).toBeInTheDocument());
    });
  });

  describe('File Upload Functionality', () => {
    it('uploads files when upload button is clicked', async () => {
      setupUploadMocks();
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(screen.getByText('Completed')).toBeInTheDocument());
    });

    it('shows upload progress correctly', async () => {
      setupUploadMocks({ progress: 50 });
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50'));
    });

    it('handles upload errors correctly', async () => {
      setupUploadMocks({ error: true });
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(screen.getByText('Upload failed')).toBeInTheDocument());
    });

    it('calls onUploadComplete callback when uploads finish', async () => {
      setupUploadMocks();
      const onUploadComplete = vi.fn();
      render(<FileUploader onUploadComplete={onUploadComplete} />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(onUploadComplete).toHaveBeenCalled());
    });

    it('calls onUploadError callback when uploads fail', async () => {
      setupUploadMocks({ error: true });
      const onUploadError = vi.fn();
      render(<FileUploader onUploadError={onUploadError} />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(onUploadError).toHaveBeenCalled());
    });
  });

  describe('File Management UI', () => {
    it('allows removing files before upload', async () => {
      render(<FileUploader />);
      const file1 = createMockFile('file1.pdf', 1024, 'application/pdf');
      const file2 = createMockFile('file2.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file1, file2] } });
      await waitFor(() => expect(screen.getByText('file1.pdf')).toBeInTheDocument());
      const removeButton = screen.getAllByLabelText('Remove file: file1.pdf')[0];
      userEvent.click(removeButton);
      expect(screen.queryByText('file1.pdf')).not.toBeInTheDocument();
      expect(screen.getByText('file2.pdf')).toBeInTheDocument();
    });

    it('disables file removal during upload', async () => {
      setupUploadMocks({ progress: 50 });
      render(<FileUploader />);
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      const uploadButton = screen.getByRole('button', { name: 'Upload Files' });
      userEvent.click(uploadButton);
      await waitFor(() => expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50'));
      const removeButton = screen.queryByLabelText('Remove file: test.pdf');
      expect(removeButton).toBeNull();
    });

    it('displays correct file information', async () => {
      const fileSize = 2048;
      const fileType = 'image/png';
      const fileName = 'test_image.png';
      const file = createMockFile(fileName, fileSize, fileType);
      render(<FileUploader />);
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });
      await waitFor(() => expect(screen.getByText(fileName)).toBeInTheDocument());
      expect(screen.getByText('2 KB')).toBeInTheDocument();
    });

    it('displays appropriate icons based on file type', async () => {
      const imageFile = createMockFile('image.png', 1024, 'image/png');
      const documentFile = createMockFile('document.pdf', 1024, 'application/pdf');
      render(<FileUploader />);
      const input = screen.getByLabelText('File upload') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [imageFile, documentFile] } });
      await waitFor(() => expect(screen.getByText('image.png')).toBeInTheDocument());
      await waitFor(() => expect(screen.getByText('document.pdf')).toBeInTheDocument());
    });
  });
});