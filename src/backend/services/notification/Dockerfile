# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user uvicorn==0.23.2

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default configuration (overridden by environment)
ENV MODULE_NAME="app.main"
ENV VARIABLE_NAME="app"
ENV PORT=8000

# Expose the service port
EXPOSE $PORT

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Start notification service
CMD uvicorn $MODULE_NAME:$VARIABLE_NAME --host 0.0.0.0 --port $PORT