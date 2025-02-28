#!/usr/bin/env python3
"""
Script for running multiple backend microservices concurrently in a development environment.
This allows developers to start selected or all services with appropriate configurations.
"""

import argparse
import subprocess
import os
import sys
import signal
import time
import logging
from pathlib import Path

# Dictionary of available services with their configurations
SERVICES = {
    'api_gateway': {
        'name': 'API Gateway',
        'module': 'services.api_gateway.app:app',
        'host': 'localhost',
        'port': 5000
    },
    'auth': {
        'name': 'Authentication Service',
        'module': 'services.auth.app:app',
        'host': 'localhost',
        'port': 5001
    },
    'task': {
        'name': 'Task Service',
        'module': 'services.task.app:app',
        'host': 'localhost',
        'port': 5002
    },
    'project': {
        'name': 'Project Service',
        'module': 'services.project.app:app',
        'host': 'localhost',
        'port': 5003
    },
    'notification': {
        'name': 'Notification Service',
        'module': 'services.notification.app:app',
        'host': 'localhost',
        'port': 5004
    },
    'file': {
        'name': 'File Service',
        'module': 'services.file.app:app',
        'host': 'localhost',
        'port': 5005
    },
    'analytics': {
        'name': 'Analytics Service',
        'module': 'services.analytics.app:app',
        'host': 'localhost',
        'port': 5006
    },
    'realtime': {
        'name': 'Real-time Service',
        'module': 'services.realtime.app:app',
        'host': 'localhost',
        'port': 5007
    }
}

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Dictionary to store running processes
processes = {}

# Global logger instance
logger = None

# Flag to control the main loop
running = True


def setup_logging(debug=False):
    """
    Configure logging for the script
    
    Args:
        debug (bool): Whether to enable debug logging
        
    Returns:
        logging.Logger: Configured logger instance
    """
    log_format = '%(asctime)s - %(levelname)s - %(message)s' if not debug else \
                 '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    log_level = logging.DEBUG if debug else logging.INFO
    
    logger = logging.getLogger('service_runner')
    logger.setLevel(log_level)
    
    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger and clear any existing handlers
    logger.handlers = []
    logger.addHandler(console_handler)
    
    return logger


def parse_args():
    """
    Parse command-line arguments
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description='Run backend microservices for development')
    
    # Add arguments
    parser.add_argument('--all', action='store_true', help='Run all services')
    parser.add_argument('--services', type=str, help='Comma-separated list of services to run')
    parser.add_argument('--env', type=str, default='development', 
                        help='Environment to run services in (default: development)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    return parser.parse_args()


def run_service(service_key, service_config, env, debug):
    """
    Start a service with Flask
    
    Args:
        service_key (str): Key of the service in SERVICES dict
        service_config (dict): Configuration for the service
        env (str): Environment to run in (development, testing, etc.)
        debug (bool): Whether to enable debug mode
    
    Returns:
        subprocess.Popen: Process object for the started service
    """
    module = service_config['module']
    host = service_config['host']
    port = service_config['port']
    
    # Set up environment variables
    env_vars = os.environ.copy()
    env_vars['FLASK_APP'] = module
    env_vars['FLASK_ENV'] = env
    env_vars['FLASK_DEBUG'] = '1' if debug else '0'
    
    # Build the command
    cmd = [
        sys.executable, '-m', 'flask', 'run',
        '--host', host,
        '--port', str(port),
        '--no-debugger', '--no-reload'  # We handle reloading ourselves
    ]
    
    if debug:
        cmd.append('--debug')
    
    # Start the service
    process = subprocess.Popen(
        cmd,
        env=env_vars,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    logger.info(f"Started {service_config['name']} on http://{host}:{port}")
    
    return process


def stop_service(service_key, process):
    """
    Stop a specific service
    
    Args:
        service_key (str): Key of the service in SERVICES dict
        process (subprocess.Popen): Process object to stop
    
    Returns:
        bool: True if successfully stopped, False otherwise
    """
    logger.info(f"Stopping {SERVICES[service_key]['name']}...")
    
    try:
        # Send SIGTERM
        process.terminate()
        
        # Wait for process to terminate with timeout
        try:
            process.wait(timeout=5)
            logger.info(f"Stopped {SERVICES[service_key]['name']}")
            return True
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            logger.warning(f"{SERVICES[service_key]['name']} did not terminate gracefully, forcing...")
            process.kill()
            process.wait()
            logger.info(f"Force stopped {SERVICES[service_key]['name']}")
            return True
    except Exception as e:
        logger.error(f"Error stopping {SERVICES[service_key]['name']}: {e}")
        return False


def stop_all_services():
    """
    Stop all running services gracefully
    """
    logger.info("Stopping all services...")
    
    for service_key, process in list(processes.items()):
        stop_service(service_key, process)
    
    processes.clear()
    logger.info("All services stopped")


def check_services(env, debug):
    """
    Check the status of running services and restart if needed
    
    Args:
        env (str): Environment to run in
        debug (bool): Whether to enable debug mode
    """
    for service_key, process in list(processes.items()):
        # Check if process is still running
        if process.poll() is not None:
            exit_code = process.poll()
            logger.warning(f"{SERVICES[service_key]['name']} terminated unexpectedly (exit code: {exit_code})")
            
            # Try to restart the service
            logger.info(f"Restarting {SERVICES[service_key]['name']}...")
            try:
                new_process = run_service(service_key, SERVICES[service_key], env, debug)
                processes[service_key] = new_process
            except Exception as e:
                logger.error(f"Failed to restart {SERVICES[service_key]['name']}: {e}")


def signal_handler(signum, frame):
    """
    Handle termination signals for graceful shutdown
    
    Args:
        signum (int): Signal number
        frame: Current stack frame
    """
    global running
    running = False
    
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name}, shutting down...")
    
    stop_all_services()
    sys.exit(0)


def monitor_services(env, debug):
    """
    Monitor running services and keep the script running
    
    Args:
        env (str): Environment to run in
        debug (bool): Whether to enable debug mode
    """
    try:
        while running:
            check_services(env, debug)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        stop_all_services()


def main():
    """
    Main function to run services
    
    Returns:
        int: Exit code
    """
    global logger
    
    try:
        # Parse arguments
        args = parse_args()
        
        # Set up logging
        logger = setup_logging(args.debug)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Determine which services to run
        service_keys = []
        if args.all:
            service_keys = list(SERVICES.keys())
        elif args.services:
            service_keys = [s.strip() for s in args.services.split(',')]
            # Validate service keys
            invalid_keys = [k for k in service_keys if k not in SERVICES]
            if invalid_keys:
                logger.error(f"Invalid service(s): {', '.join(invalid_keys)}")
                logger.info(f"Available services: {', '.join(SERVICES.keys())}")
                return 1
        else:
            logger.error("No services specified. Use --all or --services")
            logger.info(f"Available services: {', '.join(SERVICES.keys())}")
            return 1
        
        # Start services
        for service_key in service_keys:
            try:
                process = run_service(service_key, SERVICES[service_key], args.env, args.debug)
                processes[service_key] = process
            except Exception as e:
                logger.error(f"Failed to start {SERVICES[service_key]['name']}: {e}")
                stop_all_services()
                return 1
        
        logger.info(f"Started {len(processes)} service(s)")
        
        # Monitor services
        monitor_services(args.env, args.debug)
        
        return 0
    except Exception as e:
        if logger:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
        else:
            print(f"Unhandled exception: {e}")
        
        # Ensure services are stopped
        stop_all_services()
        return 1


if __name__ == "__main__":
    sys.exit(main())