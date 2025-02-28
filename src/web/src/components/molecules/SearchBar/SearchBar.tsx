import React, { useState, useRef, useCallback, useEffect } from 'react';
import classNames from 'classnames';
import { FiSearch } from 'react-icons/fi';

import Input from '../../atoms/Input/Input';
import Icon from '../../atoms/Icon/Icon';
import useDebounce from '../../../hooks/useDebounce';
import useOutsideClick from '../../../hooks/useOutsideClick';
import { useTaskSearch } from '../../../api/hooks/useTasks';
import { Task } from '../../../types/task';

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (searchTerm: string) => void;
  className?: string;
  showResults?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'simple' | 'expanded';
  focusOnLoad?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  onSearch,
  className,
  showResults = true,
  size = 'md',
  variant = 'simple',
  focusOnLoad = false,
}) => {
  // State for the search term
  const [searchTerm, setSearchTerm] = useState('');
  
  // Ref for the input element
  const inputRef = useRef<HTMLInputElement>(null);
  
  // State for dropdown visibility
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  
  // Ref for dropdown container to detect outside clicks
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Debounce search term changes to avoid too many API calls
  const debouncedSearchTerm = useDebounce(searchTerm, 300);
  
  // Fetch search results based on debounced term
  const { data: searchResults, isLoading } = useTaskSearch(debouncedSearchTerm);
  
  // Close dropdown when clicking outside
  useOutsideClick(dropdownRef, () => {
    setIsDropdownOpen(false);
  });
  
  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // Only open dropdown if there's text in the search field
    setIsDropdownOpen(value.length > 0);
  };
  
  // Handle search submission
  const handleSearch = useCallback(() => {
    if (searchTerm.trim() && onSearch) {
      onSearch(searchTerm);
    }
    setIsDropdownOpen(false);
  }, [searchTerm, onSearch]);
  
  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  // Handle clicking on a search result
  const handleResultClick = (task: Task) => {
    if (onSearch) {
      onSearch(task.title);
      setSearchTerm(task.title);
    }
    setIsDropdownOpen(false);
  };
  
  // Focus input on load if focusOnLoad is true
  useEffect(() => {
    if (focusOnLoad && inputRef.current) {
      const input = document.getElementById('search-input');
      if (input) input.focus();
    }
  }, [focusOnLoad]);
  
  // Determine container classes
  const containerClasses = classNames(
    'relative',
    {
      'w-full': variant === 'expanded',
      'w-64': variant === 'simple',
    },
    className
  );
  
  return (
    <div className={containerClasses} ref={dropdownRef}>
      <div className="relative flex items-center">
        <Input
          id="search-input"
          type="search"
          placeholder={placeholder}
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="pr-10 w-full"
          size={size}
          ariaLabel="Search"
        />
        <div 
          className="absolute right-3 top-1/2 transform -translate-y-1/2 cursor-pointer"
          onClick={handleSearch}
          role="button"
          aria-label="Search"
          tabIndex={0}
        >
          <Icon
            icon={FiSearch}
            className="text-gray-400 hover:text-gray-600"
            size={size === 'sm' ? 16 : size === 'md' ? 18 : 20}
          />
        </div>
      </div>
      
      {/* Search results dropdown */}
      {showResults && isDropdownOpen && (
        <div 
          className="absolute z-10 w-full mt-1 bg-white rounded-md shadow-lg max-h-60 overflow-auto border border-gray-200"
          role="listbox"
          aria-label="Search results"
        >
          {isLoading ? (
            <div className="px-4 py-2 text-sm text-gray-500">Loading...</div>
          ) : searchResults && searchResults.length > 0 ? (
            <ul>
              {searchResults.map((result) => (
                <SearchResultItem 
                  key={result.id} 
                  result={result} 
                  onClick={handleResultClick} 
                />
              ))}
            </ul>
          ) : debouncedSearchTerm.length > 0 ? (
            <div className="px-4 py-2 text-sm text-gray-500">No results found</div>
          ) : null}
        </div>
      )}
    </div>
  );
};

// Helper component for rendering individual search results
const SearchResultItem = ({ 
  result, 
  onClick 
}: { 
  result: Task, 
  onClick: (task: Task) => void 
}) => {
  const handleClick = () => {
    onClick(result);
  };
  
  // Determine status class based on task status
  const getStatusClasses = () => {
    switch (result.status) {
      case 'in-progress':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'on-hold':
        return 'bg-yellow-100 text-yellow-800';
      case 'in-review':
        return 'bg-purple-100 text-purple-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  return (
    <li
      className="px-4 py-2 hover:bg-gray-50 cursor-pointer"
      role="option"
      onClick={handleClick}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <div className="flex justify-between items-center">
        <span className="font-medium truncate mr-2">{result.title}</span>
        <span 
          className={classNames(
            'text-xs px-2 py-1 rounded-full whitespace-nowrap',
            getStatusClasses()
          )}
        >
          {result.status}
        </span>
      </div>
    </li>
  );
};

export default SearchBar;