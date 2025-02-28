"""
Dashboard data model for the Task Management System Analytics service.

This module defines the data models for customizable dashboards with widgets,
layouts, filtering capabilities, and sharing options.
"""

from typing import Optional, Dict, List, Any, Union
import datetime
import uuid
from bson import ObjectId

from src.backend.common.database.mongo.models import AuditableDocument, TimestampedDocument, str_to_object_id

# Dashboard types
DASHBOARD_TYPES = ['personal', 'project', 'team', 'organization']

# Widget types
WIDGET_TYPES = [
    'task_status',
    'task_completion',
    'workload',
    'due_date',
    'project_progress',
    'activity',
    'custom_metric'
]

# Visualization types
VISUALIZATION_TYPES = [
    'pie_chart',
    'bar_chart',
    'line_chart',
    'progress_bar',
    'calendar',
    'list',
    'heat_map',
    'card'
]

def validate_widget_config(widget_type: str, config: Dict) -> bool:
    """
    Validates that the widget configuration is valid for the specified widget type.
    
    Args:
        widget_type: Type of the widget
        config: Widget configuration to validate
        
    Returns:
        True if configuration is valid, False otherwise
    """
    if widget_type not in WIDGET_TYPES:
        return False
    
    # Check for required fields in all widget configurations
    required_fields = ['dataSource', 'visualizationType']
    for field in required_fields:
        if field not in config:
            return False
    
    # Visualization type must be supported
    if config['visualizationType'] not in VISUALIZATION_TYPES:
        return False
    
    # Widget-specific validations
    if widget_type == 'task_status':
        # Validate task status widget has required filters
        if 'filters' not in config:
            return False
    
    elif widget_type == 'workload':
        # Validate workload widget has user filter
        if 'filters' not in config or 'users' not in config['filters']:
            return False
    
    elif widget_type == 'due_date':
        # Validate due date widget has date range or preset filter
        if 'filters' not in config or ('dateRange' not in config['filters'] and 'preset' not in config['filters']):
            return False
    
    elif widget_type == 'task_completion':
        # Validate task completion has time period
        if 'filters' not in config or 'period' not in config['filters']:
            return False
    
    # Check compatible visualization types for specific widgets
    compatible_viz = {
        'task_status': ['pie_chart', 'bar_chart', 'card'],
        'workload': ['bar_chart', 'heat_map'],
        'due_date': ['calendar', 'list'],
        'task_completion': ['line_chart', 'progress_bar'],
        'project_progress': ['progress_bar', 'bar_chart'],
        'activity': ['list', 'line_chart'],
        'custom_metric': VISUALIZATION_TYPES  # All types are valid for custom metric
    }
    
    if widget_type in compatible_viz and config['visualizationType'] not in compatible_viz[widget_type]:
        return False
    
    return True

def generate_widget_id() -> str:
    """
    Generates a unique identifier for a dashboard widget.
    
    Returns:
        Unique widget identifier
    """
    return str(uuid.uuid4())

class Dashboard(TimestampedDocument):
    """
    Model representing a customizable dashboard with widgets and filters for data visualization.
    """
    collection_name = 'dashboards'
    schema = {
        '_id': {'type': 'ObjectId', 'required': True},
        'name': {'type': 'str', 'required': True},
        'description': {'type': 'str'},
        'type': {'type': 'str', 'required': True},
        'owner': {'type': 'ObjectId', 'required': True},
        'layout': {
            'columns': {'type': 'int'},
            'widgets': {'type': 'list'}
        },
        'scope': {
            'projects': {'type': 'list'},
            'users': {'type': 'list'},
            'dateRange': {
                'start': {'type': 'datetime', 'nullable': True},
                'end': {'type': 'datetime', 'nullable': True},
                'preset': {'type': 'str'}
            }
        },
        'widgets': {'type': 'list'},
        'sharing': {
            'public': {'type': 'bool'},
            'sharedWith': {'type': 'list'}
        },
        'lastViewed': {'type': 'datetime', 'nullable': True},
        'created_at': {'type': 'datetime'},
        'updated_at': {'type': 'datetime'}
    }
    use_schema_validation = True
    
    def __init__(self, data: Dict = None):
        """
        Initialize a new Dashboard instance with provided data.
        
        Args:
            data: Initial dashboard data
        """
        # Initialize with default values if data is None
        if data is None:
            data = {}
        
        # Set default values if not provided
        if 'type' not in data and 'type' in self.schema:
            data['type'] = 'personal'
        
        if 'layout' not in data:
            data['layout'] = {'columns': 3, 'widgets': []}
        
        if 'scope' not in data:
            data['scope'] = {'projects': [], 'users': [], 'dateRange': None}
        
        if 'widgets' not in data:
            data['widgets'] = []
        
        if 'sharing' not in data:
            data['sharing'] = {'public': False, 'sharedWith': []}
        
        super().__init__(data)
    
    def add_widget(self, widget_data: Dict) -> 'Dashboard':
        """
        Adds a new widget to the dashboard.
        
        Args:
            widget_data: Widget configuration data
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If widget data is invalid
        """
        # Validate required fields
        if 'type' not in widget_data:
            raise ValueError("Widget type is required")
        
        # Validate widget type
        if widget_data['type'] not in WIDGET_TYPES:
            raise ValueError(f"Invalid widget type: {widget_data['type']}")
        
        # Validate widget configuration if provided
        if 'config' in widget_data:
            if not validate_widget_config(widget_data['type'], widget_data['config']):
                raise ValueError("Invalid widget configuration")
        else:
            # Set default configuration if not provided
            widget_data['config'] = {
                'dataSource': 'default',
                'refreshInterval': 300,  # 5 minutes
                'visualizationType': 'bar_chart',
                'filters': {},
                'drilldownEnabled': False
            }
        
        # Generate widget ID if not provided
        if 'id' not in widget_data:
            widget_data['id'] = generate_widget_id()
        
        # Add title if not provided
        if 'title' not in widget_data:
            widget_data['title'] = f"New {widget_data['type'].replace('_', ' ').title()} Widget"
        
        # Add widget to list
        widgets = self._data.get('widgets', [])
        widgets.append(widget_data)
        self._data['widgets'] = widgets
        
        return self
    
    def update_widget(self, widget_id: str, widget_data: Dict) -> 'Dashboard':
        """
        Updates an existing widget in the dashboard.
        
        Args:
            widget_id: ID of the widget to update
            widget_data: Updated widget data
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If widget is not found or data is invalid
        """
        widgets = self._data.get('widgets', [])
        
        # Find the widget by ID
        for i, widget in enumerate(widgets):
            if widget.get('id') == widget_id:
                # Validate updated configuration if provided
                if 'config' in widget_data and 'type' in widget:
                    widget_type = widget_data.get('type', widget['type'])
                    if not validate_widget_config(widget_type, widget_data['config']):
                        raise ValueError("Invalid widget configuration")
                
                # Merge the updated data with existing widget
                for key, value in widget_data.items():
                    # Don't update the ID
                    if key != 'id':
                        widget[key] = value
                
                self._data['widgets'] = widgets
                return self
        
        # If we get here, the widget was not found
        raise ValueError(f"Widget with ID {widget_id} not found")
    
    def remove_widget(self, widget_id: str) -> 'Dashboard':
        """
        Removes a widget from the dashboard.
        
        Args:
            widget_id: ID of the widget to remove
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If widget is not found
        """
        widgets = self._data.get('widgets', [])
        
        # Look for the widget by ID
        for i, widget in enumerate(widgets):
            if widget.get('id') == widget_id:
                # Remove the widget
                widgets.pop(i)
                self._data['widgets'] = widgets
                return self
        
        # If we get here, the widget was not found
        raise ValueError(f"Widget with ID {widget_id} not found")
    
    def update_layout(self, layout_data: Dict) -> 'Dashboard':
        """
        Updates the layout configuration of the dashboard.
        
        Args:
            layout_data: Updated layout configuration
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If layout data is invalid
        """
        # Validate layout data structure
        if 'columns' not in layout_data and 'widgets' not in layout_data:
            raise ValueError("Layout must include columns and/or widget positions")
        
        current_layout = self._data.get('layout', {})
        
        # Update with provided values
        if 'columns' in layout_data:
            current_layout['columns'] = layout_data['columns']
        
        if 'widgets' in layout_data:
            # Validate that all widgets in layout exist in dashboard
            widget_ids = [w.get('id') for w in self._data.get('widgets', [])]
            for layout_widget in layout_data['widgets']:
                if 'id' not in layout_widget:
                    raise ValueError("Widget position must include widget ID")
                if layout_widget['id'] not in widget_ids:
                    raise ValueError(f"Widget with ID {layout_widget['id']} not found in dashboard")
            
            current_layout['widgets'] = layout_data['widgets']
        
        self._data['layout'] = current_layout
        return self
    
    def set_scope(self, scope_data: Dict) -> 'Dashboard':
        """
        Sets the data scope of the dashboard (projects, users, date range).
        
        Args:
            scope_data: Scope configuration
            
        Returns:
            Self for method chaining
        """
        current_scope = self._data.get('scope', {})
        
        # Update with provided values and convert IDs to ObjectId where needed
        if 'projects' in scope_data:
            current_scope['projects'] = [
                str_to_object_id(project_id) if isinstance(project_id, str) else project_id
                for project_id in scope_data['projects']
            ]
            
        if 'users' in scope_data:
            current_scope['users'] = [
                str_to_object_id(user_id) if isinstance(user_id, str) else user_id
                for user_id in scope_data['users']
            ]
            
        if 'dateRange' in scope_data:
            current_scope['dateRange'] = scope_data['dateRange']
        
        self._data['scope'] = current_scope
        return self
    
    def update_sharing(self, sharing_data: Dict) -> 'Dashboard':
        """
        Updates the sharing settings of the dashboard.
        
        Args:
            sharing_data: Updated sharing configuration
            
        Returns:
            Self for method chaining
        """
        current_sharing = self._data.get('sharing', {})
        
        # Update public flag if provided
        if 'public' in sharing_data:
            current_sharing['public'] = bool(sharing_data['public'])
        
        # Update shared users if provided
        if 'sharedWith' in sharing_data:
            current_sharing['sharedWith'] = [
                str_to_object_id(user_id) if isinstance(user_id, str) else user_id
                for user_id in sharing_data['sharedWith']
            ]
        
        self._data['sharing'] = current_sharing
        return self
    
    def log_view(self, user: Dict = None) -> 'Dashboard':
        """
        Records a view of the dashboard by updating the last viewed timestamp.
        
        Args:
            user: User viewing the dashboard (for future auditing purposes)
            
        Returns:
            Self for method chaining
        """
        self._data['lastViewed'] = datetime.datetime.utcnow()
        self.save()
        return self
    
    def get_widget_by_id(self, widget_id: str) -> Optional[Dict]:
        """
        Retrieves a widget by its ID.
        
        Args:
            widget_id: ID of the widget to retrieve
            
        Returns:
            The widget data or None if not found
        """
        widgets = self._data.get('widgets', [])
        
        for widget in widgets:
            if widget.get('id') == widget_id:
                return widget
                
        return None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Dashboard':
        """
        Creates a Dashboard instance from dictionary data.
        
        Args:
            data: Dictionary containing dashboard data
            
        Returns:
            New Dashboard instance
        """
        # Make a copy to avoid modifying the original
        dashboard_data = data.copy()
        
        # Convert string IDs to ObjectId where needed
        if 'owner' in dashboard_data and isinstance(dashboard_data['owner'], str):
            dashboard_data['owner'] = str_to_object_id(dashboard_data['owner'])
            
        if 'scope' in dashboard_data:
            scope = dashboard_data['scope']
            
            if 'projects' in scope:
                scope['projects'] = [
                    str_to_object_id(project_id) if isinstance(project_id, str) else project_id
                    for project_id in scope['projects']
                ]
                
            if 'users' in scope:
                scope['users'] = [
                    str_to_object_id(user_id) if isinstance(user_id, str) else user_id
                    for user_id in scope['users']
                ]
        
        if 'sharing' in dashboard_data and 'sharedWith' in dashboard_data['sharing']:
            dashboard_data['sharing']['sharedWith'] = [
                str_to_object_id(user_id) if isinstance(user_id, str) else user_id
                for user_id in dashboard_data['sharing']['sharedWith']
            ]
        
        return cls(dashboard_data)
    
    def to_dict(self) -> Dict:
        """
        Converts Dashboard to a dictionary representation.
        
        Returns:
            Dashboard data as dictionary
        """
        # Start with the base to_dict method
        data = super().to_dict()
        
        # Any specific conversions can be added here
        
        return data

class DashboardTemplate(TimestampedDocument):
    """
    Model representing a reusable dashboard template that can be instantiated into dashboards.
    """
    collection_name = 'dashboard_templates'
    schema = {
        '_id': {'type': 'ObjectId', 'required': True},
        'name': {'type': 'str', 'required': True},
        'description': {'type': 'str'},
        'type': {'type': 'str', 'required': True},
        'definition': {
            'layout': {'type': 'dict'},
            'widgets': {'type': 'list'},
            'defaultScope': {'type': 'dict'}
        },
        'isSystem': {'type': 'bool'},
        'category': {'type': 'str'},
        'owner': {'type': 'ObjectId'},
        'created_at': {'type': 'datetime'},
        'updated_at': {'type': 'datetime'}
    }
    use_schema_validation = True
    
    def __init__(self, data: Dict = None):
        """
        Initialize a new DashboardTemplate instance with provided data.
        
        Args:
            data: Initial template data
        """
        # Initialize with default values if data is None
        if data is None:
            data = {}
        
        # Set default values if not provided
        if 'type' not in data and 'type' in self.schema:
            data['type'] = 'personal'
        
        if 'definition' not in data:
            data['definition'] = {
                'layout': {'columns': 3},
                'widgets': [],
                'defaultScope': {}
            }
        
        if 'isSystem' not in data:
            data['isSystem'] = False
            
        super().__init__(data)
    
    def create_dashboard(self, user: Dict, override_data: Dict = None) -> Dashboard:
        """
        Creates a Dashboard instance from this template.
        
        Args:
            user: User creating the dashboard
            override_data: Data to override default template values
            
        Returns:
            New Dashboard instance based on template
        """
        if override_data is None:
            override_data = {}
            
        # Create base dashboard data from template
        dashboard_data = {
            'name': override_data.get('name', self._data.get('name')),
            'description': override_data.get('description', self._data.get('description')),
            'type': override_data.get('type', self._data.get('type')),
            'owner': user.get('_id') if isinstance(user, dict) else user,
            'widgets': self._data.get('definition', {}).get('widgets', []),
            'layout': override_data.get('layout', self._data.get('definition', {}).get('layout', {'columns': 3}))
        }
        
        # Apply default scope from template if available
        default_scope = self._data.get('definition', {}).get('defaultScope')
        if default_scope:
            dashboard_data['scope'] = override_data.get('scope', default_scope)
        
        # Generate new IDs for all widgets
        for widget in dashboard_data['widgets']:
            widget['id'] = generate_widget_id()
        
        # Create and return the dashboard
        return Dashboard.from_dict(dashboard_data)
    
    def update_definition(self, definition_data: Dict) -> 'DashboardTemplate':
        """
        Updates the template definition.
        
        Args:
            definition_data: Updated definition data
            
        Returns:
            Self for method chaining
        """
        current_definition = self._data.get('definition', {})
        
        # Update with provided values
        for key, value in definition_data.items():
            current_definition[key] = value
            
        self._data['definition'] = current_definition
        return self
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'DashboardTemplate':
        """
        Creates a DashboardTemplate instance from dictionary data.
        
        Args:
            data: Dictionary containing template data
            
        Returns:
            New DashboardTemplate instance
        """
        # Make a copy to avoid modifying the original
        template_data = data.copy()
        
        # Convert string IDs to ObjectId where needed
        if 'owner' in template_data and isinstance(template_data['owner'], str):
            template_data['owner'] = str_to_object_id(template_data['owner'])
        
        return cls(template_data)
    
    def to_dict(self) -> Dict:
        """
        Converts DashboardTemplate to a dictionary representation.
        
        Returns:
            DashboardTemplate data as dictionary
        """
        # Start with the base to_dict method
        data = super().to_dict()
        
        # Any specific conversions can be added here
        
        return data