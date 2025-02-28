import os
from src.backend.common.config.base import BaseConfig

class AnalyticsConfig(BaseConfig):
    """
    Configuration class for the Analytics Service with settings for databases, caching,
    and service-specific parameters.
    """
    
    SERVICE_NAME = "analytics-service"
    API_PREFIX = "/api/v1/analytics"
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    
    MONGODB_SETTINGS = {
        'db': 'analytics',
        'collection_prefix': 'analytics_',
        'indexes': {
            'dashboards': [
                {'field': 'owner', 'unique': False},
                {'field': 'name', 'unique': False},
                {'field': 'created_at', 'unique': False}
            ],
            'reports': [
                {'field': 'owner', 'unique': False},
                {'field': 'name', 'unique': False},
                {'field': 'scheduled', 'unique': False}
            ],
            'metrics': [
                {'field': 'type', 'unique': False},
                {'field': 'timestamp', 'unique': False},
                {'field': 'project_id', 'unique': False}
            ]
        }
    }
    
    REDIS_SETTINGS = {
        'prefix': 'analytics:',
        'channels': {
            'dashboard_updates': 'analytics:dashboard:updates',
            'report_generation': 'analytics:report:generation'
        }
    }
    
    DASHBOARD_SETTINGS = {
        'refresh_intervals': [
            30,      # 30 seconds
            60,      # 1 minute
            300,     # 5 minutes
            600,     # 10 minutes
            1800,    # 30 minutes
            3600,    # 1 hour
            21600,   # 6 hours
            86400    # 24 hours
        ],
        'default_refresh_interval': 300,  # 5 minutes
        'widget_types': {
            'task_status': {
                'description': 'Task distribution by status',
                'chart_types': ['pie', 'bar', 'card'],
                'data_source': 'tasks',
                'aggregation': 'status_count'
            },
            'burndown': {
                'description': 'Remaining work over time',
                'chart_types': ['line'],
                'data_source': 'tasks',
                'aggregation': 'time_series'
            },
            'task_completion': {
                'description': 'Completed vs. remaining tasks',
                'chart_types': ['progress', 'area'],
                'data_source': 'tasks',
                'aggregation': 'completion_ratio'
            },
            'due_date': {
                'description': 'Upcoming/overdue tasks',
                'chart_types': ['calendar', 'list'],
                'data_source': 'tasks',
                'aggregation': 'due_date_grouping'
            },
            'workload': {
                'description': 'Task count per assignee',
                'chart_types': ['bar', 'heatmap'],
                'data_source': 'tasks',
                'aggregation': 'assignee_count'
            },
            'activity': {
                'description': 'Recent system activity',
                'chart_types': ['timeline', 'list'],
                'data_source': 'activity',
                'aggregation': 'activity_timeline'
            },
            'custom_metric': {
                'description': 'User-defined calculations',
                'chart_types': ['line', 'bar', 'pie', 'number'],
                'data_source': 'custom',
                'aggregation': 'custom_query'
            }
        },
        'max_widgets_per_dashboard': 20,
        'default_layout': {
            'columns': 2,
            'widgets': [
                {'type': 'task_status', 'position': {'x': 0, 'y': 0, 'width': 1, 'height': 1}},
                {'type': 'workload', 'position': {'x': 1, 'y': 0, 'width': 1, 'height': 1}},
                {'type': 'task_completion', 'position': {'x': 0, 'y': 1, 'width': 2, 'height': 1}}
            ]
        }
    }
    
    REPORT_SETTINGS = {
        'formats': ['pdf', 'csv', 'excel', 'json'],
        'templates': {
            'project_summary': {
                'description': 'Overview of project status and metrics',
                'sections': ['summary', 'task_status', 'timeline', 'member_activity']
            },
            'task_analysis': {
                'description': 'Detailed analysis of task completion and performance',
                'sections': ['summary', 'completion_rates', 'overdue_analysis', 'time_tracking']
            },
            'workload': {
                'description': 'Team workload distribution and capacity',
                'sections': ['summary', 'member_allocation', 'capacity_planning']
            },
            'time_tracking': {
                'description': 'Analysis of time spent on tasks and projects',
                'sections': ['summary', 'time_distribution', 'estimates_vs_actual']
            }
        },
        'scheduling': {
            'frequencies': ['daily', 'weekly', 'monthly', 'quarterly'],
            'max_scheduled_reports_per_user': 10,
            'timezone': 'UTC'
        },
        'retention': {
            'generated_reports': 90,  # days
            'report_data': 365  # days
        },
        'generation_timeout': 300,  # seconds
        'max_rows_per_export': {
            'csv': 100000,
            'excel': 50000,
            'json': 100000,
            'pdf': 1000
        }
    }
    
    METRICS_SETTINGS = {
        'calculation_methods': {
            'task_completion_rate': {
                'description': 'Percentage of completed tasks relative to total tasks',
                'formula': '(completed_tasks / total_tasks) * 100',
                'thresholds': {
                    'good': 80,
                    'warning': 60,
                    'critical': 40
                }
            },
            'on_time_completion_rate': {
                'description': 'Percentage of tasks completed before their due date',
                'formula': '(on_time_tasks / completed_tasks) * 100',
                'thresholds': {
                    'good': 90,
                    'warning': 75,
                    'critical': 60
                }
            },
            'average_task_age': {
                'description': 'Average time from task creation to current date or completion',
                'formula': 'sum(current_date - task_creation_date) / total_tasks',
                'thresholds': {
                    'good': 7,  # days
                    'warning': 14,  # days
                    'critical': 30  # days
                }
            },
            'cycle_time': {
                'description': 'Average time from task creation to completion',
                'formula': 'sum(completion_date - task_creation_date) / completed_tasks',
                'thresholds': {
                    'good': 5,  # days
                    'warning': 10,  # days
                    'critical': 20  # days
                }
            },
            'lead_time': {
                'description': 'Average time from task request to delivery',
                'formula': 'sum(completion_date - task_request_date) / completed_tasks',
                'thresholds': {
                    'good': 7,  # days
                    'warning': 14,  # days
                    'critical': 28  # days
                }
            },
            'workload_distribution': {
                'description': 'Standard deviation of active tasks per assignee',
                'formula': 'stddev(tasks_per_assignee)',
                'thresholds': {
                    'good': 2,  # tasks
                    'warning': 5,  # tasks
                    'critical': 10  # tasks
                }
            },
            'burndown_rate': {
                'description': 'Rate of task completion over time',
                'formula': 'tasks_completed / time_period',
                'thresholds': {
                    'project_dependent': True
                }
            }
        },
        'aggregation_periods': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
        'default_aggregation_period': 'weekly',
        'real_time_metrics': [
            'active_users',
            'tasks_created_today',
            'tasks_completed_today',
            'overdue_tasks'
        ],
        'calculation_schedule': {
            'high_frequency': '*/15 * * * *',  # every 15 minutes
            'medium_frequency': '0 */2 * * *',  # every 2 hours
            'low_frequency': '0 0 * * *'  # daily at midnight
        },
        'calculation_timeout': 60  # seconds
    }
    
    EXPORT_SETTINGS = {
        'pdf': {
            'page_size': 'A4',
            'orientation': 'portrait',
            'template_path': 'templates/pdf',
            'fonts_path': 'assets/fonts',
            'max_pages': 50
        },
        'csv': {
            'delimiter': ',',
            'quotechar': '"',
            'encoding': 'utf-8',
            'include_headers': True
        },
        'excel': {
            'sheet_name': 'Data',
            'include_charts': True,
            'max_sheets': 10
        },
        'json': {
            'pretty_print': False,
            'include_metadata': True
        }
    }
    
    CACHE_SETTINGS = {
        'dashboard_data': {
            'ttl': 300,  # 5 minutes in seconds
            'per_user': True
        },
        'report_data': {
            'ttl': 1800,  # 30 minutes in seconds
            'per_user': True
        },
        'metrics': {
            'ttl': 600,  # 10 minutes in seconds
            'per_user': False  # Shared across users
        },
        'chart_data': {
            'ttl': 300,  # 5 minutes in seconds
            'per_user': True
        },
        'export_files': {
            'ttl': 86400,  # 24 hours in seconds
            'per_user': True
        }
    }
    
    def __init__(self):
        """
        Initializes the configuration with default values.
        """
        super().__init__()
        
        # Set MongoDB URI from environment or use default for development
        self.MONGO_URI = os.environ.get('ANALYTICS_MONGO_URI', 'mongodb://localhost:27017/analytics')
        
        # Set Redis connection from environment or use default for development
        self.REDIS_HOST = os.environ.get('ANALYTICS_REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.environ.get('ANALYTICS_REDIS_PORT', 6379))
        self.REDIS_DB = int(os.environ.get('ANALYTICS_REDIS_DB', 1))  # Use DB 1 for analytics
        self.REDIS_PASSWORD = os.environ.get('ANALYTICS_REDIS_PASSWORD', '')
        
        # Set performance limits from environment
        self.PERFORMANCE_LIMITS = {
            'query_timeout': int(os.environ.get('ANALYTICS_QUERY_TIMEOUT', 30)),  # seconds
            'max_concurrent_reports': int(os.environ.get('ANALYTICS_MAX_CONCURRENT_REPORTS', 5)),
            'max_data_points': int(os.environ.get('ANALYTICS_MAX_DATA_POINTS', 10000)),
            'max_aggregation_period': int(os.environ.get('ANALYTICS_MAX_AGGREGATION_PERIOD', 365)),  # days
        }
    
    def init_app(self, app):
        """
        Configure the Flask application with the settings from this configuration.
        
        Args:
            app: Flask application instance
        """
        # Configure app settings
        app.config.from_object(self)
        
        # Set up MongoDB connection
        app.config['MONGODB_SETTINGS'] = self.get_mongodb_settings()
        
        # Set up Redis connection
        app.config['REDIS_URI'] = self.get_redis_uri()
        
        # Configure performance monitoring
        app.config['PERFORMANCE_MONITORING'] = {
            'slow_query_threshold': self.PERFORMANCE_LIMITS['query_timeout'] / 2,
            'track_metrics': True
        }
        
        # Configure export paths
        analytics_storage_path = os.path.join(self.get_file_storage_path(), 'analytics')
        os.makedirs(analytics_storage_path, exist_ok=True)
        app.config['ANALYTICS_STORAGE_PATH'] = analytics_storage_path
        
        # Configure logging for analytics service
        app.config['LOGGING']['loggers']['analytics'] = {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }


class DevelopmentConfig(AnalyticsConfig):
    """
    Development environment configuration with debug settings and local database connections.
    """
    
    DEBUG = True
    TESTING = False
    
    MONGODB_SETTINGS = {
        'db': 'analytics_dev',
        'collection_prefix': 'analytics_'
    }
    
    REDIS_SETTINGS = {
        'prefix': 'analytics_dev:',
        'channels': {
            'dashboard_updates': 'analytics_dev:dashboard:updates',
            'report_generation': 'analytics_dev:report:generation'
        }
    }
    
    def __init__(self):
        """
        Initializes the development configuration.
        """
        super().__init__()
        self.MONGO_URI = os.environ.get('DEV_ANALYTICS_MONGO_URI', 'mongodb://localhost:27017/analytics_dev')
        self.REDIS_HOST = os.environ.get('DEV_ANALYTICS_REDIS_HOST', 'localhost')
        
        # Override performance limits for development
        self.PERFORMANCE_LIMITS = {
            'query_timeout': 60,  # Extended timeout for debugging
            'max_concurrent_reports': 2,
            'max_data_points': 5000,
            'max_aggregation_period': 90  # days
        }
        
        # Enable more detailed logging in development
        self.LOGGING['root']['level'] = 'DEBUG'
        self.LOGGING['loggers']['analytics']['level'] = 'DEBUG'


class TestingConfig(AnalyticsConfig):
    """
    Testing environment configuration for running automated tests.
    """
    
    TESTING = True
    DEBUG = True
    
    MONGODB_SETTINGS = {
        'db': 'analytics_test',
        'collection_prefix': 'analytics_'
    }
    
    REDIS_SETTINGS = {
        'prefix': 'analytics_test:',
        'channels': {
            'dashboard_updates': 'analytics_test:dashboard:updates',
            'report_generation': 'analytics_test:report:generation'
        }
    }
    
    def __init__(self):
        """
        Initializes the testing configuration.
        """
        super().__init__()
        self.MONGO_URI = os.environ.get('TEST_ANALYTICS_MONGO_URI', 'mongodb://localhost:27017/analytics_test')
        self.REDIS_HOST = os.environ.get('TEST_ANALYTICS_REDIS_HOST', 'localhost')
        
        # Configure for testing environment
        self.REPORT_SETTINGS['generation_timeout'] = 10  # Faster timeout for tests
        self.CACHE_SETTINGS = {
            'dashboard_data': {'ttl': 30, 'per_user': True},
            'report_data': {'ttl': 30, 'per_user': True},
            'metrics': {'ttl': 30, 'per_user': False},
            'chart_data': {'ttl': 30, 'per_user': True},
            'export_files': {'ttl': 60, 'per_user': True}
        }
        
        # Smaller limits for faster tests
        self.PERFORMANCE_LIMITS = {
            'query_timeout': 5,
            'max_concurrent_reports': 1,
            'max_data_points': 1000,
            'max_aggregation_period': 30  # days
        }


class ProductionConfig(AnalyticsConfig):
    """
    Production environment configuration with optimized settings for performance and security.
    """
    
    DEBUG = False
    TESTING = False
    
    MONGODB_SETTINGS = {
        'db': 'analytics',
        'collection_prefix': 'analytics_',
        'read_preference': 'secondaryPreferred'  # Read from secondary replicas when possible
    }
    
    REDIS_SETTINGS = {
        'prefix': 'analytics:',
        'channels': {
            'dashboard_updates': 'analytics:dashboard:updates',
            'report_generation': 'analytics:report:generation'
        }
    }
    
    CACHE_SETTINGS = {
        'dashboard_data': {
            'ttl': 300,  # 5 minutes
            'per_user': True
        },
        'report_data': {
            'ttl': 3600,  # 1 hour
            'per_user': True
        },
        'metrics': {
            'ttl': 900,  # 15 minutes
            'per_user': False
        },
        'chart_data': {
            'ttl': 600,  # 10 minutes
            'per_user': True
        },
        'export_files': {
            'ttl': 86400,  # 24 hours
            'per_user': True
        }
    }
    
    def __init__(self):
        """
        Initializes the production configuration.
        """
        super().__init__()
        
        # Use environment variables for production settings
        self.MONGO_URI = os.environ.get('ANALYTICS_MONGO_URI')
        if not self.MONGO_URI:
            raise ValueError("ANALYTICS_MONGO_URI environment variable must be set in production")
        
        self.REDIS_HOST = os.environ.get('ANALYTICS_REDIS_HOST')
        if not self.REDIS_HOST:
            raise ValueError("ANALYTICS_REDIS_HOST environment variable must be set in production")
        
        self.REDIS_PORT = int(os.environ.get('ANALYTICS_REDIS_PORT', 6379))
        self.REDIS_DB = int(os.environ.get('ANALYTICS_REDIS_DB', 1))
        self.REDIS_PASSWORD = os.environ.get('ANALYTICS_REDIS_PASSWORD', '')
        
        # Production-optimized performance limits
        self.PERFORMANCE_LIMITS = {
            'query_timeout': int(os.environ.get('ANALYTICS_QUERY_TIMEOUT', 30)),
            'max_concurrent_reports': int(os.environ.get('ANALYTICS_MAX_CONCURRENT_REPORTS', 10)),
            'max_data_points': int(os.environ.get('ANALYTICS_MAX_DATA_POINTS', 50000)),
            'max_aggregation_period': int(os.environ.get('ANALYTICS_MAX_AGGREGATION_PERIOD', 365))  # days
        }
        
        # Set logging to more restrictive levels in production
        self.LOGGING['root']['level'] = 'WARNING'
        self.LOGGING['loggers']['analytics']['level'] = 'INFO'


# Configuration dictionary mapping environment names to config classes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}