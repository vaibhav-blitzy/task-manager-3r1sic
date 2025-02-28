# Use python:3.11-slim as the base image for the builder stage.
FROM python:3.11-slim AS builder

# Set the working directory to /app for the builder stage.
WORKDIR /app

# Copy the requirements.txt file to the working directory.
COPY requirements.txt .

# Install Python dependencies from requirements.txt using pip.
# --no-cache-dir:  Do not use the cache when installing, to reduce image size.
# --user: Install packages in the user's home directory, avoiding the need for root permissions.
RUN pip install --no-cache-dir --user -r requirements.txt

# Use python:3.11-slim as the base image for the runtime stage.
FROM python:3.11-slim

# Set the working directory to /app for the runtime stage.
WORKDIR /app

# Copy the installed packages from the builder stage to the runtime stage.
# This copies the /root/.local directory from the builder stage to the same location in the runtime stage.
COPY --from=builder /root/.local /root/.local

# Set the PATH environment variable to include the user-installed binaries.
# This ensures that the application can find the installed dependencies.
ENV PATH=/root/.local/bin:$PATH

# Set environment variables for Python optimization.
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk, reducing image size.
# PYTHONUNBUFFERED: Disables output buffering, ensuring that logs are immediately flushed to stdout.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Copy the application code from the current directory to the working directory.
COPY . .

# Set environment variables for application configuration.
# MODULE_NAME: The name of the Python module to run (wsgi).
# VARIABLE_NAME: The name of the Flask application instance (application).
# PORT: The port number that the application will listen on (5000).
ENV MODULE_NAME="wsgi" VARIABLE_NAME="application" PORT=5000

# Expose the application port to the outside world.
EXPOSE 5000

# Create a non-root user for security.
# This prevents the application from running as root, reducing the risk of security vulnerabilities.
RUN adduser --disabled-password --gecos "" appuser

# Switch to the non-root user for container execution.
USER appuser

# Define the command to start the application using gunicorn with eventlet worker for WebSocket support.
# gunicorn: A production-ready WSGI HTTP server.
# --worker-class eventlet: Use the eventlet worker class for handling WebSocket connections.
# -w 1: Start one worker process.
# --bind 0.0.0.0:$PORT: Bind to all interfaces on the specified port.
# $MODULE_NAME:$VARIABLE_NAME: The module and variable name of the Flask application.
# --access-logfile -: Redirect access logs to stdout.
# --error-logfile -: Redirect error logs to stdout.
CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT $MODULE_NAME:$VARIABLE_NAME --access-logfile - --error-logfile -