import React, { useState, useEffect, useCallback } from 'react'; // react ^18.2.0
import { useNavigate } from 'react-router-dom'; // react-router-dom ^6.15.0
import { FiBell, FiFilter, FiCheck, FiTrash2, FiChevronLeft, FiChevronRight } from 'react-icons/fi'; // react-icons/fi ^4.10.0

import DashboardLayout from '../../components/templates/DashboardLayout/DashboardLayout';
import NotificationComponent from '../../components/molecules/Notification/Notification';
import Button from '../../components/atoms/Button/Button';
import SearchBar from '../../components/molecules/SearchBar/SearchBar';
import useNotifications from '../../api/hooks/useNotifications';
import { Notification, NotificationType } from '../../types/notification';
import { getRelativeDateLabel } from '../../utils/date';

type FilterOptions = {
  type: NotificationType | 'all';
  readStatus: 'all' | 'read' | 'unread';
  sortBy: 'date' | 'priority';
};

/**
 * Main component for the notification center page
 */
const NotificationCenter: React.FC = () => {
  // Initialize state for filter options (type, readStatus, sortBy)
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    type: 'all',
    readStatus: 'all',
    sortBy: 'date',
  });

  // Initialize state for pagination (currentPage, itemsPerPage)
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Initialize state for search query
  const [searchQuery, setSearchQuery] = useState('');

  // Use useNotifications hook to get notification data and functions
  const {
    notifications,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  // Use useNavigate hook for navigation to notification sources
  const navigate = useNavigate();

  // Create useEffect hook to fetch notifications on initial load and when filters change
  useEffect(() => {
    fetchNotifications({
      page: currentPage,
      limit: itemsPerPage,
      filter: {
        type: filterOptions.type === 'all' ? undefined : filterOptions.type,
        read: filterOptions.readStatus === 'all' ? undefined : filterOptions.readStatus === 'read',
      },
    });
  }, [currentPage, itemsPerPage, filterOptions, fetchNotifications]);

  // Implement handleFilterChange function to update filter options
  const handleFilterChange = (newFilterOptions: Partial<FilterOptions>) => {
    setFilterOptions((prev) => ({ ...prev, ...newFilterOptions }));
    setCurrentPage(1); // Reset to first page on filter change
  };

  // Implement handleSearch function to update search query
  const handleSearch = (newSearchQuery: string) => {
    setSearchQuery(newSearchQuery);
    setCurrentPage(1); // Reset to first page on search
  };

  // Implement handleMarkAsRead function to mark individual notifications as read
  const handleMarkAsRead = (notificationId: string) => {
    markAsRead(notificationId);
  };

  // Implement handleMarkAllAsRead function to mark all notifications as read
  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  // Implement handleDismiss function to dismiss notifications
  const handleDismiss = (notificationId: string) => {
    // Dismiss logic here (e.g., API call to delete notification)
    console.log(`Dismissing notification with ID: ${notificationId}`);
  };

  // Implement handleNotificationClick function to navigate to notification source
  const handleNotificationClick = (notification: Notification) => {
    if (notification.actionUrl) {
      navigate(notification.actionUrl);
    }
  };

  // Implement pagination handlers (handlePageChange, handleItemsPerPageChange)
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to first page on items per page change
  };

  // Implement sortAndFilterNotifications function to process notifications based on filters
  const sortAndFilterNotifications = useCallback(
    (notifications: Notification[], filterOptions: FilterOptions, searchQuery: string): Notification[] => {
      // Create a copy of notifications array to avoid mutations
      let filteredNotifications = [...notifications];

      // Filter by notification type if not set to 'all'
      if (filterOptions.type !== 'all') {
        filteredNotifications = filteredNotifications.filter((notification) => notification.type === filterOptions.type);
      }

      // Filter by read status if not set to 'all'
      if (filterOptions.readStatus !== 'all') {
        filteredNotifications = filteredNotifications.filter((notification) =>
          filterOptions.readStatus === 'read' ? notification.read : !notification.read
        );
      }

      // Filter by search query if provided (match against title and content)
      if (searchQuery) {
        const searchTerm = searchQuery.toLowerCase();
        filteredNotifications = filteredNotifications.filter((notification) => {
          return (
            notification.title.toLowerCase().includes(searchTerm) ||
            notification.content.toLowerCase().includes(searchTerm)
          );
        });
      }

      // Sort notifications based on sortBy option (date or priority)
      if (filterOptions.sortBy === 'date') {
        filteredNotifications.sort((a, b) => new Date(b.metadata.created).getTime() - new Date(a.metadata.created).getTime());
      } else if (filterOptions.sortBy === 'priority') {
        filteredNotifications.sort((a, b) => b.priority.localeCompare(a.priority));
      }

      return filteredNotifications;
    },
    []
  );

  // Calculate total pages based on filtered notifications count
  const filteredNotifications = sortAndFilterNotifications(notifications, filterOptions, searchQuery);
  const totalPages = Math.ceil(filteredNotifications.length / itemsPerPage);

  // Render page with DashboardLayout as container
  return (
    <DashboardLayout title="Notification Center">
      {/* Render page header with title and action buttons */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">Notifications</h2>
        <div>
          <Button variant="primary" size="sm" onClick={handleMarkAllAsRead}>
            <FiCheck className="mr-2" />
            Mark All as Read
          </Button>
        </div>
      </div>

      {/* Render filter section with dropdown selectors for type, read status, and sort order */}
      <div className="flex items-center mb-4 space-x-4">
        <div>
          <label htmlFor="typeFilter" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Type:
          </label>
          <select
            id="typeFilter"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600"
            value={filterOptions.type}
            onChange={(e) => handleFilterChange({ type: e.target.value as NotificationType | 'all' })}
          >
            <option value="all">All</option>
            <option value="task_assigned">Task Assigned</option>
            <option value="task_due_soon">Task Due Soon</option>
            <option value="task_overdue">Task Overdue</option>
            <option value="comment_added">Comment Added</option>
            <option value="mention">Mention</option>
            <option value="project_invitation">Project Invitation</option>
            <option value="status_change">Status Change</option>
          </select>
        </div>

        <div>
          <label htmlFor="readStatusFilter" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Status:
          </label>
          <select
            id="readStatusFilter"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600"
            value={filterOptions.readStatus}
            onChange={(e) => handleFilterChange({ readStatus: e.target.value as 'all' | 'read' | 'unread' })}
          >
            <option value="all">All</option>
            <option value="read">Read</option>
            <option value="unread">Unread</option>
          </select>
        </div>

        <div>
          <label htmlFor="sortByFilter" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Sort By:
          </label>
          <select
            id="sortByFilter"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600"
            value={filterOptions.sortBy}
            onChange={(e) => handleFilterChange({ sortBy: e.target.value as 'date' | 'priority' })}
          >
            <option value="date">Date</option>
            <option value="priority">Priority</option>
          </select>
        </div>
      </div>

      {/* Render search bar for keyword filtering */}
      <SearchBar placeholder="Search notifications..." onSearch={handleSearch} className="mb-4" />

      {/* Implement conditional rendering for loading state */}
      {loading && <p>Loading notifications...</p>}

      {/* Implement conditional rendering for error state */}
      {error && <p className="text-red-500">Error: {error}</p>}

      {/* Implement conditional rendering for empty state (no notifications) */}
      {!loading && !error && notifications.length === 0 && <p>No notifications found.</p>}

      {/* Render notification list with filtered and paginated items */}
      {!loading && !error && notifications.length > 0 && (
        <div>
          {filteredNotifications
            .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
            .map((notification) => (
              <NotificationComponent
                key={notification.id}
                notification={notification}
                onRead={handleMarkAsRead}
                onDismiss={handleDismiss}
                onClick={() => handleNotificationClick(notification)}
              />
            ))}
        </div>
      )}

      {/* Render pagination controls with page numbers and navigation buttons */}
      {renderPagination(currentPage, totalPages, handlePageChange)}

      {/* Items per page selector */}
      <div className="flex justify-end items-center mt-4">
        <label htmlFor="itemsPerPage" className="mr-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          Items per page:
        </label>
        <select
          id="itemsPerPage"
          className="mt-1 block w-24 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600"
          value={itemsPerPage}
          onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
        >
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>
    </DashboardLayout>
  );
};

/**
 * Renders pagination controls for the notification list
 */
const renderPagination = (
  currentPage: number,
  totalPages: number,
  onPageChange: (page: number) => void
): JSX.Element => {
  // Calculate range of page numbers to display
  let pageNumbers: (number | string)[] = [];
  if (totalPages <= 7) {
    // Less than or equal to 7 pages, display all
    pageNumbers = Array.from({ length: totalPages }, (_, i) => i + 1);
  } else {
    // More than 7 pages, display a condensed range with ellipsis
    if (currentPage <= 3) {
      pageNumbers = [1, 2, 3, 4, '...', totalPages - 1, totalPages];
    } else if (currentPage >= totalPages - 2) {
      pageNumbers = [1, 2, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    } else {
      pageNumbers = [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
    }
  }

  // Render previous page button (disabled if on first page)
  return (
    <div className="flex justify-center items-center mt-4">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        aria-label="Previous Page"
      >
        <FiChevronLeft className="mr-2" />
        Previous
      </Button>

      {/* Render page number buttons with active state for current page */}
      {pageNumbers.map((pageNumber, index) => (
        <React.Fragment key={index}>
          {typeof pageNumber === 'number' ? (
            <Button
              variant={currentPage === pageNumber ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onPageChange(pageNumber)}
              aria-label={`Go to page ${pageNumber}`}
            >
              {pageNumber}
            </Button>
          ) : (
            <span className="mx-2 text-gray-500">...</span>
          )}
        </React.Fragment>
      ))}

      {/* Render next page button (disabled if on last page) */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        aria-label="Next Page"
      >
        Next
        <FiChevronRight className="ml-2" />
      </Button>
    </div>
  );
};

export default NotificationCenter;