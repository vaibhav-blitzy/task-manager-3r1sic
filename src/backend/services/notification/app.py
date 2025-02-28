# Standard library imports
import os
import logging
import atexit

# Third-party imports
from flask import Flask, jsonify, request  # flask==2.3.x
from flask_jwt_extended import JWTManager  # flask_jwt_extended==4.5.x
from apscheduler.schedulers.background import BackgroundScheduler  # apscheduler==3.10.x

# Internal imports
from .config import get_config  # src/backend/services/notification/config.py
from .api.notifications import notification_blueprint  # src/backend/services/notification/api/notifications.py
from .api.preferences import preferences_blueprint  # src/backend/services/notification/api/preferences.py
from .services.notification_service import NotificationService  # src/backend/services/notification/services/notification_service.py
from common.exceptions.error_handlers import register_error_handlers  # src/backend/common/exceptions/error_handlers.py
from common.middlewares.cors import setup_cors  # src/backend/common/middlewares/cors.py
from common.middlewares.request_id import setup_request_id  # src/backend/common/middlewares/request_id.py
from common.middlewares.rate_limiter import setup_rate_limiter  # src/backend/common/middlewares/rate_limiter.py
from common.logging.logger import setup_logger  # src/backend/common/logging/logger.py
from common.database.mongo.connection import init_mongo  # src/backend/common/database/mongo/connection.py
from common.database.redis.connection import init_redis  # src/backend/common/database/redis/connection.py
from common.events.event_bus import get_event_bus_instance  # src/backend/common/events/event_bus.py
from common.auth.decorators import jwt_required  # src/backend/common/auth/jwt_utils.py

# Initialize logger
logger = logging.getLogger(__name__)

# Global variables
notification_service = None
scheduler = None


def create_app(config_name: str) -> Flask:
    """
    Factory function that creates and configures the Flask application instance for the Notification microservice.
    
    Args:
        config_name: The configuration name (e.g., 'development', 'production')
    
    Returns:
        Configured Flask application instance
    """
    # Create Flask application instance
    app = Flask(__name__)

    # Load configuration based on config_name parameter
    init_app_config(app, config_name)

    # Set up logging
    setup_logger(app)

    # Initialize database connections (MongoDB, Redis)
    init_mongo()
    init_redis()

    # Initialize global notification_service instance
    global notification_service
    notification_service = initialize_notification_service(app)

    # Initialize scheduler for periodic notification tasks
    global scheduler
    scheduler = initialize_scheduler(app, notification_service)

    # Set up middleware (CORS, request ID, rate limiter)
    configure_middlewares(app)

    # Register API blueprints (notifications, preferences)
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Set up application shutdown handler via atexit
    atexit.register(shutdown_services)

    # Register health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint for the notification service"""
        # Check MongoDB connection
        mongo_status = init_mongo()

        # Check Redis connection
        redis_status = init_redis()

        # Check notification service status
        notification_status = "Running" if notification_service else "Not Initialized"

        # Return service health information as JSON
        return jsonify({
            "status": "OK",
            "mongo": mongo_status,
            "redis": redis_status,
            "notification_service": notification_status
        })

    # Return configured application
    return app


def init_app_config(app: Flask, config_name: str) -> None:
    """
    Initializes application configuration based on environment.
    
    Args:
        app: Flask application instance
        config_name: Configuration name (e.g., 'development', 'production')
    """
    # Determine configuration class from get_config() using config_name
    config = get_config()

    # Apply configuration to Flask app
    app.config.from_object(config)

    # Log which configuration is being used
    logger.info(f"Using configuration: {config_name}")


def register_blueprints(app: Flask) -> None:
    """
    Registers all API blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register notification_blueprint with URL prefix '/api/v1/notifications'
    app.register_blueprint(notification_blueprint, url_prefix='/api/v1/notifications')

    # Register preferences_blueprint with URL prefix '/api/v1/notifications/preferences'
    app.register_blueprint(preferences_blueprint, url_prefix='/api/v1/notifications/preferences')

    # Log successful registration of blueprints
    logger.info("Registered API blueprints")


def configure_middlewares(app: Flask) -> None:
    """
    Sets up middleware for the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Set up CORS middleware using setup_cors
    setup_cors(app)

    # Set up request ID middleware using setup_request_id
    setup_request_id(app)

    # Set up rate limiting middleware using setup_rate_limiter
    setup_rate_limiter(app)

    # Initialize JWT extension for the application
    JWTManager(app)

    # Log successful middleware configuration
    logger.info("Configured middleware")


def initialize_notification_service(app: Flask) -> NotificationService:
    """
    Initializes the global notification service instance.
    
    Args:
        app: Flask application instance
    
    Returns:
        Initialized notification service
    """
    # Create new NotificationService instance
    notification_service = NotificationService()

    # Start the notification service
    notification_service.start()

    # Log successful service initialization
    logger.info("Initialized NotificationService")

    # Return the initialized service
    return notification_service


def initialize_scheduler(app: Flask, notification_service: NotificationService) -> BackgroundScheduler:
    """
    Sets up the job scheduler for periodic notification tasks.
    
    Args:
        app: Flask application instance
        notification_service: Initialized notification service
    
    Returns:
        Configured scheduler instance
    """
    # Create APScheduler instance with background execution mode
    scheduler = BackgroundScheduler()

    # Add job to check for due date notifications (runs every hour)
    scheduler.add_job(
        func=notification_service.check_due_date_notifications,
        trigger="interval",
        hours=1,
        name="Check Due Date Notifications"
    )

    # Add job to process daily notification digests (runs daily at midnight)
    # TODO: Implement daily digest processing
    # scheduler.add_job(
    #     func=notification_service.process_daily_digests,
    #     trigger="cron",
    #     hour=0,
    #     minute=0,
    #     name="Process Daily Notification Digests"
    # )

    # Add job to process weekly notification digests (runs weekly on Sunday)
    # TODO: Implement weekly digest processing
    # scheduler.add_job(
    #     func=notification_service.process_weekly_digests,
    #     trigger="cron",
    #     day_of_week="sun",
    #     hour=0,
    #     minute=0,
    #     name="Process Weekly Notification Digests"
    # )

    # Start the scheduler
    scheduler.start()

    # Log successful scheduler initialization
    logger.info("Initialized scheduler")

    # Return the scheduler instance
    return scheduler


def shutdown_services() -> None:
    """
    Gracefully stops services on application shutdown.
    """
    # Log shutdown initiation
    logger.info("Shutting down services...")

    # Stop the scheduler if running
    if scheduler and scheduler.running:
        logger.info("Stopping scheduler...")
        scheduler.shutdown(wait=False)  # Non-blocking shutdown

    # Stop the notification service if running
    if notification_service and notification_service._running:
        logger.info("Stopping notification service...")
        notification_service.stop()

    # Log successful shutdown
    logger.info("Services shutdown complete")

def check_api_key() -> bool:
    """
    Validates API key for internal service communication.
    
    Returns:
        True if valid, False otherwise
    """
    # Get API key from request header
    api_key = request.headers.get('X-API-Key')

    # Validate against configured service API key
    if api_key == os.environ.get('SERVICE_API_KEY'):
        return True
    else:
        return False