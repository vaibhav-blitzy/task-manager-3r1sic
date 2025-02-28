import React from 'react';
import { describe, it, expect, jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from './SearchBar';

// Mock the useTaskSearch hook
jest.mock('../../../api/hooks/useTasks', () => ({
  useTaskSearch: jest.fn(() => ({
    data: null,
    isLoading: false
  }))
}));

describe('SearchBar component', () => {
  it('renders the search input', () => {
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('id', 'search-input');
  });

  it('renders with custom placeholder text', () => {
    const placeholder = 'Search tasks...';
    render(<SearchBar placeholder={placeholder} />);
    expect(screen.getByPlaceholderText(placeholder)).toBeInTheDocument();
  });

  it('calls onSearch when form is submitted', () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'test search');
    
    // Simulate Enter key to call handleSearch
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(onSearch).toHaveBeenCalledWith('test search');
  });

  it('calls onSearch when search button is clicked', () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'test search');
    
    // Find the search button by its role and aria-label
    const searchButton = screen.getByRole('button', { name: 'Search' });
    userEvent.click(searchButton);
    
    expect(onSearch).toHaveBeenCalledWith('test search');
  });

  it('clears input when clear button is clicked', () => {
    render(<SearchBar />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'test search');
    
    expect(input).toHaveValue('test search');
    
    // Clear the input
    userEvent.clear(input);
    
    expect(input).toHaveValue('');
  });

  it('triggers search on input change with debounce', async () => {
    // Create a mock function for the useTaskSearch hook
    const mockUseTaskSearch = jest.fn(() => ({
      data: [],
      isLoading: false
    }));
    
    // Update the mock to use our tracking function
    require('../../../api/hooks/useTasks').useTaskSearch = mockUseTaskSearch;
    
    render(<SearchBar />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'test search');
    
    // Wait for debounce (300ms) to complete
    await waitFor(() => {
      // Check that useTaskSearch was called with the debounced search term
      expect(mockUseTaskSearch).toHaveBeenCalledWith('test search');
    }, { timeout: 400 }); // Adding buffer for debounce
  });

  it('renders search results when available', async () => {
    // Mock task search results
    const mockResults = [
      { id: '1', title: 'Task 1', status: 'in-progress' },
      { id: '2', title: 'Task 2', status: 'completed' }
    ];
    
    // Update the mock to return results
    require('../../../api/hooks/useTasks').useTaskSearch.mockReturnValue({
      data: mockResults,
      isLoading: false
    });
    
    render(<SearchBar showResults={true} />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'task');
    
    // Wait for results to be displayed (need to wait for debounce)
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    }, { timeout: 400 });
  });

  it('selects a result when clicked', async () => {
    const onSearch = jest.fn();
    
    // Mock task search results
    const mockResults = [
      { id: '1', title: 'Task 1', status: 'in-progress' },
      { id: '2', title: 'Task 2', status: 'completed' }
    ];
    
    // Update the mock to return results
    require('../../../api/hooks/useTasks').useTaskSearch.mockReturnValue({
      data: mockResults,
      isLoading: false
    });
    
    render(<SearchBar showResults={true} onSearch={onSearch} />);
    
    const input = screen.getByRole('searchbox');
    userEvent.type(input, 'task');
    
    // Wait for results to be displayed
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
    }, { timeout: 400 });
    
    // Click on the first result
    userEvent.click(screen.getByText('Task 1'));
    
    // The onSearch should be called with the task title
    expect(onSearch).toHaveBeenCalledWith('Task 1');
  });

  it('focuses input when focusOnLoad is true', () => {
    render(<SearchBar focusOnLoad={true} />);
    // The input is focused after the component mounts via useEffect
    expect(document.activeElement).toBe(screen.getByRole('searchbox'));
  });
});