# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install dependencies with optimized flags
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default configuration (overridden by environment)
ENV MODULE_NAME="wsgi"
ENV VARIABLE_NAME="app"
ENV PORT=8000

EXPOSE $PORT

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD uvicorn $MODULE_NAME:$VARIABLE_NAME --host 0.0.0.0 --port $PORT