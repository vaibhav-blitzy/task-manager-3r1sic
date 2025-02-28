import os  # standard library
import logging  # standard library

# Internal imports
from .app import create_app  # src/backend/services/realtime/app.py
from .config import get_config  # src/backend/services/realtime/config.py

# Initialize logger
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()

# Create Flask application
app, socketio = create_app()

# Export Flask application and SocketIO instance
__all__ = ['app', 'socketio']

if __name__ == '__main__':
    # Get the port from the environment, default to 5003
    port = int(os.environ.get('PORT', config.PORT))

    # Run the SocketIO application
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=config.DEBUG)
    except Exception as e:
        logger.error(f"An error occurred while running the application: {e}")