"""
Production environment configuration for the Task Management System.
Defines secure, optimized settings suitable for a scalable production deployment on AWS infrastructure.
"""

import boto3
import json
import os
import logging
from datetime import timedelta
from botocore.exceptions import ClientError
from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """
    Configuration class for the production environment with secure settings
    and optimized performance parameters. Designed for AWS deployment with
    tight security controls, robust monitoring, and high availability.
    """

    def __init__(self):
        """
        Initialize the production configuration with secure environment-specific settings.
        """
        # Initialize base configuration
        super().__init__()
        
        # Basic environment settings
        self.ENV = 'production'
        self.DEBUG = False
        self.TESTING = False
        
        # Load secrets from AWS Secrets Manager or environment variables
        secrets = self._load_secrets()
        
        # Set secret key from secrets
        self.SECRET_KEY = secrets.get('SECRET_KEY')
        
        # Configure MongoDB with high-availability settings
        self.MONGO_URI, self.MONGO_OPTIONS = self._configure_mongodb(secrets)
        
        # Configure Redis for caching and real-time features
        self.REDIS_URL, self.REDIS_OPTIONS = self._configure_redis(secrets)
        
        # Configure CORS settings for production
        self.CORS_SETTINGS = {
            'origins': [
                'https://taskmanagement.example.com',
                'https://api.taskmanagement.example.com',
                # Add additional production domains here
            ],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key'],
            'expose_headers': ['Content-Type', 'X-Pagination', 'X-Rate-Limit'],
            'supports_credentials': True,
            'max_age': 3600  # 1 hour cache for preflight requests
        }
        
        # JWT configuration
        self.JWT_SETTINGS = {
            'SECRET_KEY': self.SECRET_KEY,
            'ACCESS_TOKEN_EXPIRES': timedelta(minutes=15),  # Short-lived access tokens
            'REFRESH_TOKEN_EXPIRES': timedelta(days=7),     # 7-day refresh tokens
            'ALGORITHM': 'HS256',
            'BLACKLIST_ENABLED': True,
            'BLACKLIST_STORAGE': 'redis',
            'TOKEN_LOCATION': ['headers'],
            'HEADER_NAME': 'Authorization',
            'HEADER_TYPE': 'Bearer'
        }
        
        # Rate limiting settings
        self.RATE_LIMIT_SETTINGS = {
            'default': '120/minute',
            'authenticated': {
                'limit': 120,
                'period': 60,  # 60 seconds = 1 minute
                'key_func': 'user_id'
            },
            'service_account': {
                'limit': 600,
                'period': 60,
                'key_func': 'api_key'
            },
            'anonymous': {
                'limit': 30,
                'period': 60,
                'key_func': 'ip_address'
            },
            'login': {
                'limit': 5, 
                'period': 60,
                'key_func': 'ip_address'
            }
        }
        
        # Configure logging
        self.LOGGING_CONFIG = self._configure_logging()
        
        # S3 configuration for file storage
        self.S3_CONFIG = {
            'bucket_name': 'task-management-files-prod',
            'region': os.environ.get('AWS_REGION', 'us-east-1'),
            'signature_version': 's3v4',
            'acl': 'private',
            'presigned_url_expiration': 3600,  # 1 hour in seconds
            'max_file_size': 104857600,  # 100MB
            'allowed_extensions': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 
                                  'jpg', 'jpeg', 'png', 'gif', 'zip', 'tar', 'gz'],
            'encryption': {
                'enabled': True,
                'kms_key_id': secrets.get('S3_KMS_KEY_ID', None)
            }
        }
        
        # Email configuration (using SendGrid)
        self.EMAIL_CONFIG = {
            'provider': 'sendgrid',
            'api_key': secrets.get('SENDGRID_API_KEY'),
            'sender_email': 'noreply@taskmanagement.example.com',
            'sender_name': 'Task Management System',
            'templates': {
                'welcome': 'd-123456789abcdef',
                'password_reset': 'd-abcdef123456789',
                'task_assignment': 'd-123abc456def789',
                'task_reminder': 'd-789def456abc123',
                'task_completed': 'd-def789abc123456'
            },
            'tracking_enabled': True,
            'batch_size': 100
        }
        
        # Auth configuration (using Auth0)
        self.AUTH_CONFIG = {
            'provider': 'auth0',
            'domain': secrets.get('AUTH0_DOMAIN'),
            'client_id': secrets.get('AUTH0_CLIENT_ID'),
            'client_secret': secrets.get('AUTH0_CLIENT_SECRET'),
            'audience': 'https://api.taskmanagement.example.com',
            'algorithms': ['RS256'],
            'mfa_enabled': True,
            'passwordless_enabled': True,
            'social_logins': ['google', 'microsoft', 'github'],
            'token_introspection_enabled': True
        }
        
        # Cache configuration
        self.CACHE_CONFIG = {
            'default_timeout': 300,  # 5 minutes
            'key_prefix': 'tms:',
            'ttl': {
                'user_profile': 3600,  # 1 hour
                'project_details': 900,  # 15 minutes
                'task_list': 300,  # 5 minutes
                'dashboard': 300,  # 5 minutes
                'reports': 1800,  # 30 minutes
                'api_response': 300  # 5 minutes
            },
            'ignored_query_params': ['_', 'timestamp', 'random'],
            'distributed': True,
            'serializer': 'json'
        }
        
        # Performance configuration
        self.PERFORMANCE_CONFIG = {
            'database': {
                'connection_pool_size': 100,
                'min_pool_size': 20,
                'max_pool_size': 100,
                'max_idle_time_ms': 600000,  # 10 minutes
                'connection_timeout_ms': 3000  # 3 seconds
            },
            'http': {
                'keep_alive': True,
                'connection_timeout': 5,  # seconds
                'read_timeout': 30,  # seconds
                'max_retries': 3,
                'backoff_factor': 0.3
            },
            'worker': {
                'concurrency': 8,
                'prefetch_multiplier': 4
            }
        }
        
        # Feature flags for controlled rollout
        self.FEATURE_FLAGS = {
            'real_time_collaboration': True,
            'advanced_analytics': True,
            'calendar_integration': True,
            'custom_fields': True,
            'workflow_automation': True,
            'api_v2': True,
            'enhanced_search': True,
            'team_dashboard': True
        }
        
        # API Gateway configuration
        self.API_GATEWAY_CONFIG = {
            'enabled': True,
            'base_url': 'https://api.taskmanagement.example.com',
            'stage': 'prod',
            'api_key_required': True,
            'api_key_source': 'HEADER',
            'throttling': {
                'rate': 1000,
                'burst': 500
            }
        }
        
        # Enhanced security configuration
        self.SECURITY_CONFIG = {
            'content_security_policy': "default-src 'self'; script-src 'self'; object-src 'none'; "
                                      "img-src 'self' data:; media-src 'self'; "
                                      "frame-src 'none'; font-src 'self'; "
                                      "connect-src 'self' https://api.taskmanagement.example.com;",
            'x_content_type_options': 'nosniff',
            'x_frame_options': 'DENY',
            'x_xss_protection': '1; mode=block',
            'strict_transport_security': 'max-age=31536000; includeSubDomains; preload',
            'referrer_policy': 'strict-origin-when-cross-origin',
            'secure_cookies': True,
            'httponly_cookies': True,
            'samesite_cookies': 'Lax',
            'session_expiry': 3600,  # 1 hour
            'encryption': {
                'algorithm': 'AES-256-GCM',
                'key_rotation_days': 90
            },
            'pii_fields': ['name', 'email', 'phone', 'address', 'ip_address']
        }

    def _load_secrets(self):
        """
        Load secrets from AWS Secrets Manager with fallback to environment variables.
        
        Returns:
            dict: Dictionary of secret configuration values
        """
        secrets = {}
        
        try:
            # Create a Secrets Manager client
            secrets_client = boto3.client(
                service_name='secretsmanager',
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
            
            # Get the secret name from environment or use default
            secret_name = os.environ.get('SECRET_NAME', 'task-management-system/production')
            
            # Get the secret value
            response = secrets_client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret JSON string
            if 'SecretString' in response:
                secrets = json.loads(response['SecretString'])
                logging.info(f"Loaded secrets from AWS Secrets Manager: {secret_name}")
            
        except ClientError as e:
            # If AWS Secrets Manager fails, fall back to environment variables
            logging.warning(f"Failed to load from AWS Secrets Manager: {str(e)}")
            logging.info("Falling back to environment variables for secrets")
            
            # Load essential secrets from environment variables
            secrets = {
                'SECRET_KEY': os.environ.get('SECRET_KEY'),
                'MONGO_USERNAME': os.environ.get('MONGO_USERNAME'),
                'MONGO_PASSWORD': os.environ.get('MONGO_PASSWORD'),
                'MONGO_HOSTS': os.environ.get('MONGO_HOSTS'),
                'MONGO_REPLICA_SET': os.environ.get('MONGO_REPLICA_SET'),
                'REDIS_HOST': os.environ.get('REDIS_HOST'),
                'REDIS_PORT': os.environ.get('REDIS_PORT'),
                'REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD'),
                'SENDGRID_API_KEY': os.environ.get('SENDGRID_API_KEY'),
                'AUTH0_DOMAIN': os.environ.get('AUTH0_DOMAIN'),
                'AUTH0_CLIENT_ID': os.environ.get('AUTH0_CLIENT_ID'),
                'AUTH0_CLIENT_SECRET': os.environ.get('AUTH0_CLIENT_SECRET'),
                'S3_KMS_KEY_ID': os.environ.get('S3_KMS_KEY_ID')
            }
            
        # Ensure critical secrets are present
        for key in ['SECRET_KEY', 'MONGO_USERNAME', 'MONGO_PASSWORD']:
            if not secrets.get(key):
                logging.error(f"Critical secret missing: {key}")
                # In production, we might want to raise an exception here
                # For now, we'll log an error but continue
        
        return secrets

    def _configure_mongodb(self):
        """
        Configure MongoDB connection with replica set, TLS, and authentication for production.
        
        Returns:
            tuple: MongoDB URI and connection options dictionary
        """
        # Extract MongoDB configuration from secrets
        secrets = self._load_secrets()
        mongo_username = secrets.get('MONGO_USERNAME')
        mongo_password = secrets.get('MONGO_PASSWORD')
        mongo_hosts = secrets.get('MONGO_HOSTS', 'mongodb-0.example.com:27017,mongodb-1.example.com:27017,mongodb-2.example.com:27017')
        mongo_db_name = secrets.get('MONGO_DB_NAME', 'task_management_prod')
        mongo_replica_set = secrets.get('MONGO_REPLICA_SET', 'rs0')
        
        # Format the MongoDB URI
        mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_hosts}/{mongo_db_name}?replicaSet={mongo_replica_set}&ssl=true"
        
        # Set production-specific MongoDB options
        mongo_options = {
            'maxPoolSize': 100,  # Maximum number of connections in the pool
            'minPoolSize': 20,   # Minimum number of connections to maintain
            'maxIdleTimeMS': 600000,  # 10 minutes - close idle connections after this time
            'connectTimeoutMS': 3000,  # 3 seconds - fail fast on connection issues
            'socketTimeoutMS': 45000,  # 45 seconds - for longer operations
            'serverSelectionTimeoutMS': 5000,  # 5 seconds - fail fast on server selection
            'retryWrites': True,  # Retry write operations upon failure
            'readPreference': 'secondaryPreferred',  # Read from secondaries when possible
            'w': 'majority',  # Write to majority of nodes for durability
            'ssl': True,  # Use SSL/TLS for all connections
            'authSource': 'admin',  # Authentication database
            'journal': True  # Ensure writes are journaled
        }
        
        return mongo_uri, mongo_options

    def _configure_redis(self):
        """
        Configure Redis connection with appropriate settings for production caching
        and real-time features.
        
        Returns:
            tuple: Redis URL and connection options dictionary
        """
        # Extract Redis configuration from secrets
        secrets = self._load_secrets()
        redis_host = secrets.get('REDIS_HOST', 'redis.example.com')
        redis_port = secrets.get('REDIS_PORT', '6379')
        redis_password = secrets.get('REDIS_PASSWORD', '')
        redis_db = secrets.get('REDIS_DB', '0')
        
        # Format the Redis URL
        auth_part = f":{redis_password}@" if redis_password else ""
        redis_url = f"redis://{auth_part}{redis_host}:{redis_port}/{redis_db}"
        
        # Set production-specific Redis options
        redis_options = {
            'socket_timeout': 5,  # 5 seconds socket timeout
            'socket_connect_timeout': 3,  # 3 seconds connection timeout
            'socket_keepalive': True,  # Keep connections alive
            'retry_on_timeout': True,  # Retry operations on timeout
            'health_check_interval': 30,  # Check health every 30 seconds
            'max_connections': 100,  # Maximum number of connections
            'ssl': True,  # Use SSL/TLS for Redis connection
            'ssl_cert_reqs': 'required'  # Verify Redis server certificate
        }
        
        return redis_url, redis_options

    def _configure_logging(self):
        """
        Configure production logging with structured JSON format and appropriate log levels.
        
        Returns:
            dict: Logging configuration dictionary compatible with Flask and Python logging
        """
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "service": "task-management", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "trace_id": "%(trace_id)s", "user_id": "%(user_id)s", "correlation_id": "%(correlation_id)s"}'
                }
            },
            'filters': {
                'contextual': {
                    '()': 'app.logging.ContextualFilter'  # Custom filter to add trace_id, user_id, etc.
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'filters': ['contextual'],
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'filters': ['contextual'],
                    'filename': '/var/log/app/application.log',
                    'maxBytes': 10485760,  # 10 MB
                    'backupCount': 10
                },
                'cloudwatch': {
                    'class': 'watchtower.CloudWatchLogHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'filters': ['contextual'],
                    'log_group': 'task-management-system',
                    'stream_name': 'production-{strftime:%Y-%m-%d}',
                    'create_log_group': True
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console', 'file', 'cloudwatch']
            },
            'loggers': {
                'flask': {
                    'level': 'WARNING',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                },
                'werkzeug': {
                    'level': 'WARNING',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                },
                'botocore': {
                    'level': 'WARNING',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                },
                'tasks': {
                    'level': 'INFO',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                },
                'auth': {
                    'level': 'INFO',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                },
                'projects': {
                    'level': 'INFO',
                    'handlers': ['console', 'file', 'cloudwatch'],
                    'propagate': False
                }
            }
        }
        
        return logging_config