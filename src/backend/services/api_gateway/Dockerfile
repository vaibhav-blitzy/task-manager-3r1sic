# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install dependencies in user space for better security
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Set Python environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Copy application code
COPY . .

# Set application configuration
ENV MODULE_NAME="wsgi" VARIABLE_NAME="application" PORT=8000

# Expose the application port
EXPOSE 8000

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Start Gunicorn with Uvicorn workers for high performance
CMD gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT $MODULE_NAME:$VARIABLE_NAME --access-logfile - --error-logfile -