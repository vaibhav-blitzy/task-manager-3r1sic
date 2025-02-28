# Use multi-stage builds to reduce image size and improve security
#
# --------------------------------------------------------------------------
# Builder Stage: Install dependencies and prepare the application
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder
# python:3.11-slim - Base image for Python runtime environment

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
# Includes data analysis libraries and reporting tools
# Use pip with --user flag to avoid requiring root permissions
# Optimize installation with --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --user -r requirements.txt

# --------------------------------------------------------------------------
# Runtime Stage: Create the final image
# --------------------------------------------------------------------------
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Update PATH environment variable to include user-installed binaries
ENV PATH=/root/.local/bin:$PATH

# Set Python environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install additional system dependencies for WeasyPrint (PDF generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application code to working directory
COPY . .

# Set environment variables for application configuration
ENV MODULE_NAME=wsgi
ENV VARIABLE_NAME=app
ENV PORT=8000

# Expose the required port (8000)
EXPOSE $PORT

# Create non-root user for security (appuser)
RUN adduser --disabled-password --gecos "" appuser

# Set appropriate permissions for application files
RUN chown -R appuser:appuser /app

# Switch to non-root user for container execution
USER appuser

# Define the command to start the Analytics Service using gunicorn with uvicorn workers
CMD gunicorn --bind 0.0.0.0:$PORT --workers 3 --worker-class uvicorn.workers.UvicornWorker wsgi:app