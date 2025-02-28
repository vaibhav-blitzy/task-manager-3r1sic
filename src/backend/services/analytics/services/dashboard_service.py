"""
Service responsible for managing dashboard operations including creation, retrieval, update, and deletion of dashboards.
Handles widget configuration, data aggregation, and visualization capabilities for the analytics module.
"""

from typing import Dict, List, Optional, Any, Union
import copy
import datetime
import bson
import pymongo
from bson import ObjectId

# Internal imports
from src.backend.common.database.mongo.connection import get_collection, with_retry
from src.backend.common.logging.logger import get_logger
from src.backend.common.database.mongo.models import str_to_object_id
from src.backend.common.exceptions.api_exceptions import NotFoundError, ValidationError, ConflictError

# Models
from src.backend.services.analytics.models.dashboard import (
    Dashboard, DashboardTemplate, DASHBOARD_TYPES, WIDGET_TYPES, 
    VISUALIZATION_TYPES, validate_widget_config
)

# Services
from src.backend.services.analytics.services.metrics_service import MetricsService

# Initialize logger
logger = get_logger(__name__)

# Initialize metrics service
metrics_service = MetricsService()

def create_system_dashboard_templates() -> bool:
    """
    Creates default system dashboard templates if they don't exist.
    
    Returns:
        bool: True if templates were created, False if they already existed
    """
    # Get the templates collection
    template_collection = get_collection('dashboard_templates')
    
    # Check if system templates already exist
    system_templates_count = template_collection.count_documents({'isSystem': True})
    if system_templates_count > 0:
        logger.info(f"System dashboard templates already exist, found {system_templates_count} templates")
        return False
    
    # Create default system templates
    templates = []
    
    # Personal dashboard template
    personal_template = {
        'name': 'Personal Dashboard',
        'description': 'Default dashboard for individual task management',
        'type': 'personal',
        'isSystem': True,
        'category': 'Default',
        'definition': {
            'layout': {'columns': 2},
            'widgets': [
                {
                    'id': 'tasks-due-today',
                    'type': 'due_date',
                    'title': 'Tasks Due Today',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'list',
                        'refreshInterval': 300,
                        'filters': {'preset': 'today'},
                        'drilldownEnabled': True
                    }
                },
                {
                    'id': 'my-task-status',
                    'type': 'task_status',
                    'title': 'My Tasks',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'pie_chart',
                        'refreshInterval': 300,
                        'filters': {'assignee': 'current_user'},
                        'drilldownEnabled': True
                    }
                },
                {
                    'id': 'recent-activity',
                    'type': 'activity',
                    'title': 'Recent Activity',
                    'config': {
                        'dataSource': 'activity',
                        'visualizationType': 'list',
                        'refreshInterval': 300,
                        'filters': {'users': ['current_user']},
                        'drilldownEnabled': False
                    }
                }
            ],
            'defaultScope': {
                'projects': [],
                'users': ['current_user'],
                'dateRange': {'preset': 'month'}
            }
        }
    }
    templates.append(personal_template)
    
    # Project dashboard template
    project_template = {
        'name': 'Project Dashboard',
        'description': 'Default dashboard for project management',
        'type': 'project',
        'isSystem': True,
        'category': 'Default',
        'definition': {
            'layout': {'columns': 3},
            'widgets': [
                {
                    'id': 'project-progress',
                    'type': 'project_progress',
                    'title': 'Project Progress',
                    'config': {
                        'dataSource': 'projects',
                        'visualizationType': 'progress_bar',
                        'refreshInterval': 300,
                        'filters': {},
                        'drilldownEnabled': False
                    }
                },
                {
                    'id': 'task-status',
                    'type': 'task_status',
                    'title': 'Task Status',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'pie_chart',
                        'refreshInterval': 300,
                        'filters': {},
                        'drilldownEnabled': True
                    }
                },
                {
                    'id': 'upcoming-deadlines',
                    'type': 'due_date',
                    'title': 'Upcoming Deadlines',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'list',
                        'refreshInterval': 300,
                        'filters': {'preset': 'week'},
                        'drilldownEnabled': True
                    }
                },
                {
                    'id': 'team-workload',
                    'type': 'workload',
                    'title': 'Team Workload',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'bar_chart',
                        'refreshInterval': 300,
                        'filters': {'users': []},
                        'drilldownEnabled': True
                    }
                }
            ],
            'defaultScope': {
                'projects': ['selected_project'],
                'users': [],
                'dateRange': {'preset': 'month'}
            }
        }
    }
    templates.append(project_template)
    
    # Team performance dashboard template
    team_template = {
        'name': 'Team Performance',
        'description': 'Performance metrics for team productivity',
        'type': 'team',
        'isSystem': True,
        'category': 'Performance',
        'definition': {
            'layout': {'columns': 2},
            'widgets': [
                {
                    'id': 'task-completion-rate',
                    'type': 'task_completion',
                    'title': 'Task Completion Rate',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'line_chart',
                        'refreshInterval': 300,
                        'filters': {'period': 'week'},
                        'drilldownEnabled': False
                    }
                },
                {
                    'id': 'workload-distribution',
                    'type': 'workload',
                    'title': 'Workload Distribution',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'bar_chart',
                        'refreshInterval': 300,
                        'filters': {'users': []},
                        'drilldownEnabled': True
                    }
                },
                {
                    'id': 'overdue-tasks',
                    'type': 'due_date',
                    'title': 'Overdue Tasks',
                    'config': {
                        'dataSource': 'tasks',
                        'visualizationType': 'list',
                        'refreshInterval': 300,
                        'filters': {'overdue': True},
                        'drilldownEnabled': True
                    }
                }
            ],
            'defaultScope': {
                'projects': [],
                'users': [],
                'dateRange': {'preset': 'month'}
            }
        }
    }
    templates.append(team_template)
    
    # Insert all templates
    template_collection.insert_many(templates)
    logger.info(f"Created {len(templates)} system dashboard templates")
    
    return True

class DashboardService:
    """
    Service class for managing dashboards including CRUD operations and widget data retrieval.
    """
    
    def __init__(self):
        """
        Initialize the dashboard service with database collections.
        """
        logger.info("Initializing Dashboard Service")
        self._dashboard_collection = get_collection('dashboards')
        self._template_collection = get_collection('dashboard_templates')
        
        # Ensure system dashboard templates exist
        create_system_dashboard_templates()
    
    @with_retry(max_retries=3, delay=0.5)
    def get_dashboard_by_id(self, dashboard_id: str, include_data: bool = False) -> Dashboard:
        """
        Retrieves a dashboard by its ID.
        
        Args:
            dashboard_id: ID of the dashboard to retrieve
            include_data: Whether to include widget data in the response
            
        Returns:
            Dashboard instance if found
            
        Raises:
            NotFoundError: If dashboard is not found
        """
        try:
            # Convert string ID to ObjectId
            object_id = str_to_object_id(dashboard_id)
            
            # Query the database
            dashboard_doc = self._dashboard_collection.find_one({'_id': object_id})
            
            if not dashboard_doc:
                logger.error(f"Dashboard not found with ID: {dashboard_id}")
                raise NotFoundError(message=f"Dashboard not found", resource_type="dashboard", resource_id=dashboard_id)
            
            # Create Dashboard instance
            dashboard = Dashboard.from_dict(dashboard_doc)
            
            # Fetch widget data if requested
            if include_data:
                self.get_dashboard_data(dashboard)
            
            # Log this view of the dashboard
            dashboard.log_view()
            
            return dashboard
            
        except bson.errors.InvalidId:
            logger.error(f"Invalid dashboard ID format: {dashboard_id}")
            raise NotFoundError(message=f"Invalid dashboard ID format", resource_type="dashboard", resource_id=dashboard_id)
    
    @with_retry(max_retries=3, delay=0.5)
    def get_dashboards(self, filters: Dict = None, page: int = 1, page_size: int = 20, 
                      sort_by: str = 'updated_at', sort_direction: str = 'desc') -> Dict:
        """
        Retrieves dashboards based on filter criteria.
        
        Args:
            filters: Filter criteria for dashboards
            page: Page number for pagination
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_direction: Sort direction ('asc' or 'desc')
            
        Returns:
            Dictionary with dashboards list and pagination metadata
        """
        if filters is None:
            filters = {}
        
        # Build query
        query = {}
        
        # Add filter criteria to query
        if 'type' in filters and filters['type'] in DASHBOARD_TYPES:
            query['type'] = filters['type']
        
        if 'owner' in filters:
            try:
                if isinstance(filters['owner'], str):
                    query['owner'] = str_to_object_id(filters['owner'])
                else:
                    query['owner'] = filters['owner']
            except Exception as e:
                logger.error(f"Error converting owner ID: {e}")
        
        if 'search' in filters and filters['search']:
            query['$or'] = [
                {'name': {'$regex': filters['search'], '$options': 'i'}},
                {'description': {'$regex': filters['search'], '$options': 'i'}}
            ]
        
        # Add sharing permissions 
        if 'user_id' in filters:
            user_id = filters['user_id']
            if isinstance(user_id, str):
                user_id = str_to_object_id(user_id)
                
            # dashboards owned by the user or shared with the user or public
            query['$or'] = query.get('$or', []) + [
                {'owner': user_id},
                {'sharing.public': True},
                {'sharing.sharedWith': user_id}
            ]
        
        # Calculate pagination values
        skip = (page - 1) * page_size
        limit = page_size
        
        # Determine sort direction
        sort_dir = pymongo.DESCENDING if sort_direction == 'desc' else pymongo.ASCENDING
        
        # Execute query with pagination
        cursor = self._dashboard_collection.find(query).skip(skip).limit(limit)
        
        # Apply sorting
        if sort_by:
            cursor = cursor.sort(sort_by, sort_dir)
        
        # Convert results to Dashboard instances
        dashboards = [Dashboard.from_dict(doc) for doc in cursor]
        
        # Get total count for pagination
        total_count = self._dashboard_collection.count_documents(query)
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            'dashboards': [dashboard.to_dict() for dashboard in dashboards],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
    
    @with_retry(max_retries=3, delay=0.5)
    def create_dashboard(self, dashboard_data: Dict, user: Dict) -> Dashboard:
        """
        Creates a new dashboard.
        
        Args:
            dashboard_data: Dashboard data
            user: User creating the dashboard
            
        Returns:
            Newly created Dashboard instance
        """
        # Validation - add required fields
        if 'name' not in dashboard_data:
            raise ValidationError(message="Dashboard name is required")
        
        if 'type' not in dashboard_data or dashboard_data['type'] not in DASHBOARD_TYPES:
            dashboard_data['type'] = 'personal'  # Default to personal dashboard
        
        # Check if dashboard with same name exists for this user
        existing_dashboard = self._dashboard_collection.find_one({
            'name': dashboard_data['name'],
            'owner': user['_id'] if isinstance(user, dict) and '_id' in user else user
        })
        
        if existing_dashboard:
            logger.error(f"Dashboard with name '{dashboard_data['name']}' already exists for user")
            raise ConflictError(
                message=f"Dashboard with name '{dashboard_data['name']}' already exists", 
                resource_type="dashboard"
            )
        
        # Set owner to current user
        dashboard_data['owner'] = user['_id'] if isinstance(user, dict) and '_id' in user else user
        
        # Create dashboard instance
        dashboard = Dashboard.from_dict(dashboard_data)
        
        # Save to database
        dashboard.save()
        logger.info(f"Created new dashboard: {dashboard.get_id_str()}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def update_dashboard(self, dashboard_id: str, dashboard_data: Dict, user: Dict) -> Dashboard:
        """
        Updates an existing dashboard.
        
        Args:
            dashboard_id: ID of the dashboard to update
            dashboard_data: Updated dashboard data
            user: User performing the update
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Update attributes - only those provided in dashboard_data
        if 'name' in dashboard_data:
            dashboard.set('name', dashboard_data['name'])
        
        if 'description' in dashboard_data:
            dashboard.set('description', dashboard_data['description'])
        
        if 'type' in dashboard_data and dashboard_data['type'] in DASHBOARD_TYPES:
            dashboard.set('type', dashboard_data['type'])
        
        # Don't allow changing owner directly - that's done through sharing
        
        # Save updates
        dashboard.save()
        logger.info(f"Updated dashboard: {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def delete_dashboard(self, dashboard_id: str, user: Dict) -> bool:
        """
        Deletes a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard to delete
            user: User performing the deletion
            
        Returns:
            True if dashboard was deleted
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'delete'):
            logger.error(f"User {user} does not have permission to delete dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to delete this dashboard")
        
        # Convert string ID to ObjectId
        object_id = str_to_object_id(dashboard_id)
        
        # Delete from database
        result = self._dashboard_collection.delete_one({'_id': object_id})
        
        if result.deleted_count == 0:
            logger.error(f"Failed to delete dashboard: {dashboard_id}")
            return False
        
        logger.info(f"Deleted dashboard: {dashboard_id}")
        return True
    
    @with_retry(max_retries=3, delay=0.5)
    def add_widget(self, dashboard_id: str, widget_data: Dict, user: Dict) -> Dashboard:
        """
        Adds a widget to an existing dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            widget_data: Widget configuration data
            user: User performing the action
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Validate widget data
        if 'type' not in widget_data:
            raise ValidationError(message="Widget type is required")
        
        if widget_data['type'] not in WIDGET_TYPES:
            raise ValidationError(message=f"Invalid widget type: {widget_data['type']}")
        
        # Add the widget to the dashboard
        dashboard.add_widget(widget_data)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Added widget to dashboard {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def update_widget(self, dashboard_id: str, widget_id: str, widget_data: Dict, user: Dict) -> Dashboard:
        """
        Updates an existing widget in a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            widget_id: ID of the widget to update
            widget_data: Updated widget data
            user: User performing the update
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Update the widget
        dashboard.update_widget(widget_id, widget_data)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Updated widget {widget_id} in dashboard {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def remove_widget(self, dashboard_id: str, widget_id: str, user: Dict) -> Dashboard:
        """
        Removes a widget from a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            widget_id: ID of the widget to remove
            user: User performing the removal
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Remove the widget
        dashboard.remove_widget(widget_id)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Removed widget {widget_id} from dashboard {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def update_layout(self, dashboard_id: str, layout_data: Dict, user: Dict) -> Dashboard:
        """
        Updates the layout configuration of a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            layout_data: Updated layout configuration
            user: User performing the update
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Update layout
        dashboard.update_layout(layout_data)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Updated layout for dashboard {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def update_dashboard_scope(self, dashboard_id: str, scope_data: Dict, user: Dict) -> Dashboard:
        """
        Updates the data scope of a dashboard (projects, users, date range).
        
        Args:
            dashboard_id: ID of the dashboard
            scope_data: Updated scope configuration
            user: User performing the update
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions
        if not self.has_dashboard_permission(dashboard, user, 'edit'):
            logger.error(f"User {user} does not have permission to edit dashboard {dashboard_id}")
            raise ValidationError(message="You don't have permission to edit this dashboard")
        
        # Update scope
        dashboard.set_scope(scope_data)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Updated scope for dashboard {dashboard_id}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def update_sharing(self, dashboard_id: str, sharing_data: Dict, user: Dict) -> Dashboard:
        """
        Updates the sharing settings of a dashboard.
        
        Args:
            dashboard_id: ID of the dashboard
            sharing_data: Updated sharing configuration
            user: User performing the update
            
        Returns:
            Updated Dashboard instance
        """
        # First get the existing dashboard
        dashboard = self.get_dashboard_by_id(dashboard_id)
        
        # Check permissions - must be owner to change sharing settings
        owner_id = dashboard.get('owner')
        user_id = user['_id'] if isinstance(user, dict) and '_id' in user else user
        
        if str(owner_id) != str(user_id):
            logger.error(f"User {user} is not the owner of dashboard {dashboard_id}")
            raise ValidationError(message="Only the dashboard owner can change sharing settings")
        
        # Update sharing settings
        dashboard.update_sharing(sharing_data)
        
        # Save the dashboard
        dashboard.save()
        logger.info(f"Updated sharing settings for dashboard {dashboard_id}")
        
        return dashboard
    
    def get_dashboard_data(self, dashboard: Dashboard) -> Dict:
        """
        Retrieves data for all widgets in a dashboard.
        
        Args:
            dashboard: Dashboard instance
            
        Returns:
            Dictionary with widget data keyed by widget ID
        """
        result = {}
        
        widgets = dashboard.get('widgets', [])
        dashboard_scope = dashboard.get('scope', {})
        
        for widget in widgets:
            widget_id = widget.get('id')
            if not widget_id:
                continue
                
            try:
                # Get data for this widget
                widget_data = self.get_widget_data(widget, dashboard_scope)
                result[widget_id] = widget_data
            except Exception as e:
                logger.error(f"Error getting data for widget {widget_id}: {str(e)}")
                result[widget_id] = {'error': str(e)}
        
        return result
    
    def get_widget_data(self, widget: Dict, dashboard_scope: Dict = None) -> Dict:
        """
        Retrieves data for a specific dashboard widget.
        
        Args:
            widget: Widget configuration
            dashboard_scope: Dashboard scope configuration (projects, users, date range)
            
        Returns:
            Widget data formatted for visualization
        """
        if dashboard_scope is None:
            dashboard_scope = {}
            
        widget_type = widget.get('type')
        widget_config = widget.get('config', {})
        
        # Merge dashboard scope with widget-specific filters
        filters = copy.deepcopy(dashboard_scope)
        widget_filters = widget_config.get('filters', {})
        
        if 'projects' in widget_filters:
            filters['projects'] = widget_filters['projects']
            
        if 'users' in widget_filters:
            filters['users'] = widget_filters['users']
            
        if 'dateRange' in widget_filters:
            filters['dateRange'] = widget_filters['dateRange']
        
        # Add any additional widget-specific filters
        for key, value in widget_filters.items():
            if key not in ['projects', 'users', 'dateRange']:
                filters[key] = value
        
        # Call metrics service to get the data for this widget type
        return metrics_service.get_widget_data(widget_type, widget_config, filters)
    
    @with_retry(max_retries=3, delay=0.5)
    def get_template_by_id(self, template_id: str) -> DashboardTemplate:
        """
        Retrieves a dashboard template by its ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            DashboardTemplate instance if found
            
        Raises:
            NotFoundError: If template is not found
        """
        try:
            # Convert string ID to ObjectId
            object_id = str_to_object_id(template_id)
            
            # Query the database
            template_doc = self._template_collection.find_one({'_id': object_id})
            
            if not template_doc:
                logger.error(f"Dashboard template not found with ID: {template_id}")
                raise NotFoundError(message=f"Dashboard template not found", resource_type="dashboard_template", resource_id=template_id)
            
            # Create DashboardTemplate instance
            return DashboardTemplate.from_dict(template_doc)
            
        except bson.errors.InvalidId:
            logger.error(f"Invalid template ID format: {template_id}")
            raise NotFoundError(message=f"Invalid template ID format", resource_type="dashboard_template", resource_id=template_id)
    
    @with_retry(max_retries=3, delay=0.5)
    def get_templates(self, filters: Dict = None, page: int = 1, page_size: int = 20) -> Dict:
        """
        Retrieves dashboard templates based on filter criteria.
        
        Args:
            filters: Filter criteria for templates
            page: Page number for pagination
            page_size: Number of results per page
            
        Returns:
            Dictionary with templates list and pagination metadata
        """
        if filters is None:
            filters = {}
        
        # Build query
        query = {}
        
        # Add filter criteria to query
        if 'type' in filters and filters['type'] in DASHBOARD_TYPES:
            query['type'] = filters['type']
        
        if 'isSystem' in filters:
            query['isSystem'] = bool(filters['isSystem'])
        
        if 'category' in filters:
            query['category'] = filters['category']
        
        if 'owner' in filters:
            try:
                if isinstance(filters['owner'], str):
                    query['owner'] = str_to_object_id(filters['owner'])
                else:
                    query['owner'] = filters['owner']
            except Exception as e:
                logger.error(f"Error converting owner ID: {e}")
        
        if 'search' in filters and filters['search']:
            query['$or'] = [
                {'name': {'$regex': filters['search'], '$options': 'i'}},
                {'description': {'$regex': filters['search'], '$options': 'i'}}
            ]
        
        # Calculate pagination values
        skip = (page - 1) * page_size
        limit = page_size
        
        # Execute query with pagination
        cursor = self._template_collection.find(query).skip(skip).limit(limit)
        
        # Convert results to DashboardTemplate instances
        templates = [DashboardTemplate.from_dict(doc) for doc in cursor]
        
        # Get total count for pagination
        total_count = self._template_collection.count_documents(query)
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            'templates': [template.to_dict() for template in templates],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
    
    @with_retry(max_retries=3, delay=0.5)
    def create_dashboard_from_template(self, template_id: str, dashboard_data: Dict, user: Dict) -> Dashboard:
        """
        Creates a new dashboard from a template.
        
        Args:
            template_id: ID of the template to use
            dashboard_data: Dashboard data to override template defaults
            user: User creating the dashboard
            
        Returns:
            Newly created Dashboard instance
        """
        # Get the template
        template = self.get_template_by_id(template_id)
        
        # Validate dashboard data (at minimum, name should be provided)
        if 'name' not in dashboard_data:
            raise ValidationError(message="Dashboard name is required")
        
        # Create dashboard from template
        dashboard = template.create_dashboard(user, dashboard_data)
        
        # Save the new dashboard
        dashboard.save()
        logger.info(f"Created dashboard from template {template_id}: {dashboard.get_id_str()}")
        
        return dashboard
    
    @with_retry(max_retries=3, delay=0.5)
    def create_template(self, template_data: Dict, user: Dict) -> DashboardTemplate:
        """
        Creates a new dashboard template.
        
        Args:
            template_data: Template data
            user: User creating the template
            
        Returns:
            Newly created DashboardTemplate instance
        """
        # Validation - add required fields
        if 'name' not in template_data:
            raise ValidationError(message="Template name is required")
        
        if 'type' not in template_data or template_data['type'] not in DASHBOARD_TYPES:
            template_data['type'] = 'personal'  # Default to personal dashboard
        
        # Check if template with same name exists
        existing_template = self._template_collection.find_one({
            'name': template_data['name'],
            'owner': user['_id'] if isinstance(user, dict) and '_id' in user else user
        })
        
        if existing_template:
            logger.error(f"Template with name '{template_data['name']}' already exists for user")
            raise ConflictError(
                message=f"Template with name '{template_data['name']}' already exists", 
                resource_type="dashboard_template"
            )
        
        # Set owner to current user
        template_data['owner'] = user['_id'] if isinstance(user, dict) and '_id' in user else user
        
        # Ensure it's not marked as a system template
        template_data['isSystem'] = False
        
        # Create template instance
        template = DashboardTemplate.from_dict(template_data)
        
        # Save to database
        template.save()
        logger.info(f"Created new dashboard template: {template.get_id_str()}")
        
        return template
    
    @with_retry(max_retries=3, delay=0.5)
    def update_template(self, template_id: str, template_data: Dict, user: Dict) -> DashboardTemplate:
        """
        Updates an existing dashboard template.
        
        Args:
            template_id: ID of the template to update
            template_data: Updated template data
            user: User performing the update
            
        Returns:
            Updated DashboardTemplate instance
        """
        # Get the existing template
        template = self.get_template_by_id(template_id)
        
        # Check if system template and user is not admin (only admins can update system templates)
        if template.get('isSystem', False) and not user.get('is_admin', False):
            logger.error(f"User {user} attempted to update system template {template_id}")
            raise ValidationError(message="Only administrators can update system templates")
        
        # Check if user is owner or admin (only owner or admin can update)
        owner_id = template.get('owner')
        user_id = user['_id'] if isinstance(user, dict) and '_id' in user else user
        
        if str(owner_id) != str(user_id) and not user.get('is_admin', False):
            logger.error(f"User {user} is not the owner of template {template_id}")
            raise ValidationError(message="You don't have permission to update this template")
        
        # Update attributes - only those provided in template_data
        if 'name' in template_data:
            template.set('name', template_data['name'])
        
        if 'description' in template_data:
            template.set('description', template_data['description'])
        
        if 'type' in template_data and template_data['type'] in DASHBOARD_TYPES:
            template.set('type', template_data['type'])
        
        if 'category' in template_data:
            template.set('category', template_data['category'])
        
        if 'definition' in template_data:
            template.update_definition(template_data['definition'])
        
        # Don't allow changing isSystem or owner directly
        
        # Save updates
        template.save()
        logger.info(f"Updated dashboard template: {template_id}")
        
        return template
    
    @with_retry(max_retries=3, delay=0.5)
    def delete_template(self, template_id: str, user: Dict) -> bool:
        """
        Deletes a dashboard template.
        
        Args:
            template_id: ID of the template to delete
            user: User performing the deletion
            
        Returns:
            True if template was deleted
        """
        # Get the existing template
        template = self.get_template_by_id(template_id)
        
        # Check if system template and user is not admin (only admins can delete system templates)
        if template.get('isSystem', False) and not user.get('is_admin', False):
            logger.error(f"User {user} attempted to delete system template {template_id}")
            raise ValidationError(message="Only administrators can delete system templates")
        
        # Check if user is owner or admin (only owner or admin can delete)
        owner_id = template.get('owner')
        user_id = user['_id'] if isinstance(user, dict) and '_id' in user else user
        
        if str(owner_id) != str(user_id) and not user.get('is_admin', False):
            logger.error(f"User {user} is not the owner of template {template_id}")
            raise ValidationError(message="You don't have permission to delete this template")
        
        # Convert string ID to ObjectId
        object_id = str_to_object_id(template_id)
        
        # Delete from database
        result = self._template_collection.delete_one({'_id': object_id})
        
        if result.deleted_count == 0:
            logger.error(f"Failed to delete template: {template_id}")
            return False
        
        logger.info(f"Deleted dashboard template: {template_id}")
        return True
    
    def has_dashboard_permission(self, dashboard: Dashboard, user: Dict, permission_type: str) -> bool:
        """
        Checks if a user has permission to view/edit a dashboard.
        
        Args:
            dashboard: Dashboard to check permissions for
            user: User to check permissions for
            permission_type: Type of permission ('view', 'edit', 'delete')
            
        Returns:
            True if user has the specified permission
        """
        # System admins can do anything
        if user.get('is_admin', False):
            return True
        
        user_id = user['_id'] if isinstance(user, dict) and '_id' in user else user
        owner_id = dashboard.get('owner')
        
        # Check view permission (owner, public dashboard, or explicitly shared)
        if permission_type == 'view':
            # Owner always has view permission
            if str(owner_id) == str(user_id):
                return True
            
            # Public dashboards are viewable by all
            if dashboard.get('sharing', {}).get('public', False):
                return True
            
            # Check if explicitly shared with this user
            shared_with = dashboard.get('sharing', {}).get('sharedWith', [])
            for shared_user_id in shared_with:
                if str(shared_user_id) == str(user_id):
                    return True
            
            return False
        
        # Check edit/delete permission (only owner can edit/delete)
        elif permission_type in ['edit', 'delete']:
            return str(owner_id) == str(user_id)
        
        # Default to false for unknown permission types
        return False