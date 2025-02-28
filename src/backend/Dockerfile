# Stage 1: Builder stage for dependency installation
# python:3.11-slim version 3.11.6
FROM python:3.11-slim AS builder

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies using pip with user flag to avoid root installations
# This creates a .local directory with installed packages
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage with minimal layers
FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the installed packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default configuration (overridden by environment variables at runtime)
ENV MODULE_NAME="app.main" \
    VARIABLE_NAME="app" \
    PORT=8000

# Expose the application port
EXPOSE $PORT

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to start the application
CMD uvicorn $MODULE_NAME:$VARIABLE_NAME --host 0.0.0.0 --port $PORT