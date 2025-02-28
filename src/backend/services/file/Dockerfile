# Dockerfile for File Management Service
#
# This service handles:
# - Secure file upload and storage
# - File metadata management
# - File retrieval and downloading
# - File scanning for viruses/malware
# - File versioning
# - Integration with storage providers
#
# The container exposes port 8004 for HTTP API access.
# 
# Multi-stage build pattern is used to minimize image size and reduce attack surface.
# Non-root user is employed for enhanced security.

# First stage: build dependencies
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies into the user's home directory for later copying
# Using --no-cache-dir to keep the image size smaller by not storing the package cache
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user gunicorn==21.2.*

# Second stage: runtime image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are available in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default configuration (overridden by environment)
ENV MODULE_NAME="wsgi"
ENV VARIABLE_NAME="app"
ENV PORT=8004

# Expose the port
EXPOSE $PORT

# Create non-root user for security
RUN adduser --disabled-password --gecos "" fileservice

# Switch to non-root user for security
USER fileservice

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT "$MODULE_NAME:$VARIABLE_NAME" --workers 4 --threads 2 --timeout 60 --access-logfile - --error-logfile -