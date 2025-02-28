# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements file for dependency installation
COPY requirements.txt .

# Install dependencies to user directory for later copying
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user gunicorn

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default configuration (overridden by environment)
ENV MODULE_NAME="wsgi"
ENV FLASK_APP="app:create_app()"
ENV PORT=5000

# Expose the port the app will run on
EXPOSE ${PORT}

# Create and use non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} ${MODULE_NAME}:app