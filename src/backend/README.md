# Task Management System - Backend

## Overview
Backend implementation of the Task Management System built with a microservices architecture. The system provides comprehensive task and project management capabilities with real-time collaboration features.

## Services Architecture
The backend consists of the following microservices:
- Authentication Service: User management, authentication, and authorization
- Task Service: Task CRUD operations, status tracking, and assignment
- Project Service: Project organization and team management
- Notification Service: Real-time and email notifications
- File Service: File uploads, storage, and retrieval
- Analytics Service: Reporting and dashboard data
- Real-time Service: WebSocket connections for live updates

## Technologies
- Python 3.11
- Flask 2.3.x and Flask extensions
- MongoDB for persistent storage
- Redis for caching and real-time features
- AWS S3 for file storage
- Docker and Docker Compose for containerization
- JWT for authentication
- Celery for asynchronous task processing
- PyTest for testing

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- MongoDB (or Docker image)
- Redis (or Docker image)
- AWS account for S3 (optional for development)

## Setup Instructions
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see .env.example)
4. Run database services: `docker-compose up -d mongodb redis`
5. Start all services: `docker-compose up` or `python scripts/run_services.py`

## Environment Variables
Configure the following environment variables:
- `FLASK_APP`: Entry point for Flask applications
- `FLASK_ENV`: Environment (development, testing, production)
- `MONGODB_URI`: MongoDB connection string
- `REDIS_URI`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT generation
- `AWS_ACCESS_KEY_ID`: AWS access key for S3
- `AWS_SECRET_ACCESS_KEY`: AWS secret for S3
- `S3_BUCKET`: S3 bucket name for file storage

## Running the Services
### Using Docker Compose
```
docker-compose up
```

### Running Individual Services
```
cd services/auth
FLASK_APP=app.py flask run --port=5001
```

## API Documentation
API documentation is available at the following endpoints when running the services:

- Swagger UI: http://localhost:5000/api/docs
- ReDoc: http://localhost:5000/api/redoc

## Testing
Run tests using PyTest:

```
pytest
```

For specific service tests:

```
pytest services/auth/tests/
```

## Code Structure
- `common/`: Shared utilities, configurations, and base classes
- `services/`: Individual microservices
  - `api_gateway/`: API Gateway service
  - `auth/`: Authentication service
  - `task/`: Task management service
  - `project/`: Project management service
  - `notification/`: Notification service
  - `file/`: File management service
  - `analytics/`: Analytics and reporting service
  - `realtime/`: Real-time WebSocket service
- `tests/`: Integration and performance tests
- `scripts/`: Utility scripts for development and deployment

## Development Guidelines
- Follow PEP 8 style guide for Python code
- Write unit tests for all new features
- Document API endpoints using OpenAPI/Swagger
- Use feature branches and pull requests for code changes
- Run linters and tests before submitting pull requests

## Deployment
The system is deployed on AWS using ECS with the following environments:

- Development: Feature testing
- Staging: Pre-production testing with production-like data
- Production: Live system

Deployment is managed through GitHub Actions workflows defined in `.github/workflows/`.

## Troubleshooting
### Common Issues

- **Database Connection Errors**: Verify MongoDB and Redis are running and connection strings are correct
- **Authentication Issues**: Check JWT configuration and secret keys
- **Service Discovery Problems**: Ensure service names in the API Gateway configuration match running services
- **File Upload Failures**: Verify S3 credentials and bucket permissions