# Use multi-stage builds to create a lean production image
# https://docs.docker.com/develop/develop-images/multistage-build/

# Builder stage: Install dependencies
FROM python:3.11-slim AS builder
# Install Poetry
# ENV POETRY_VERSION=1.7.0
# RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Set working directory
WORKDIR /app

# Copy requirements file
COPY ./requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Runtime stage: Create the final image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the application code
COPY ./app.py ./
COPY ./wsgi.py ./

# Copy installed packages from builder stage
COPY --from=builder /app /app
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV MODULE_NAME=wsgi
ENV VARIABLE_NAME=app
ENV PORT=8000

# Expose the port the app runs on
EXPOSE $PORT

# Create a non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Switch to the non-root user
USER appuser

# Define the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "3", "--threads", "2", "--timeout", "120", "--worker-class", "uvicorn.workers.UvicornWorker", "$MODULE_NAME:$VARIABLE_NAME"]