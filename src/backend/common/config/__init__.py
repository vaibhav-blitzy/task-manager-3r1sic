import os
import logging
from typing import Dict, Type

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

# Set up module logger
logger = logging.getLogger(__name__)

# Map environment names to configuration classes
CONFIG_CLASSES = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

# Determine the active environment from environment variables
# Default to 'development' if not specified
ENV = os.environ.get("FLASK_ENV", "development")

# Get the configuration class for the current environment
config_class = CONFIG_CLASSES.get(ENV, DevelopmentConfig)

# Log a warning if an unknown environment was specified
if ENV not in CONFIG_CLASSES:
    logger.warning(f"Unknown environment: {ENV}, falling back to development configuration")

# Create an instance of the configuration class
CONFIG = config_class()

def get_config() -> BaseConfig:
    """
    Returns the configuration instance for the current environment
    
    Returns:
        BaseConfig: Configuration instance for the current environment
    """
    return CONFIG

def get_config_by_env(env: str) -> BaseConfig:
    """
    Returns a configuration instance for the specified environment
    
    Args:
        env (str): The environment to get the configuration for
        
    Returns:
        BaseConfig: Configuration instance for the specified environment
    """
    config_class = CONFIG_CLASSES.get(env)
    if config_class is None:
        logger.warning(f"Unknown environment: {env}, falling back to development configuration")
        config_class = DevelopmentConfig
    
    return config_class()