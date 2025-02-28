# Development Environment Setup Guide

## Table of Contents
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Core Development Tools](#core-development-tools)
- [Backend Development Environment](#backend-development-environment)
- [Frontend Development Environment](#frontend-development-environment)
- [Database Setup](#database-setup)
- [Docker Environment](#docker-environment)
- [Project Setup](#project-setup)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

## Introduction

This guide provides comprehensive instructions for setting up the development environment for the Task Management System. Following these steps will ensure a consistent development environment across the team and minimize "works on my machine" issues.

## Prerequisites

### System Requirements

- **Operating System**: 
  - Windows 10/11 Pro or Enterprise (required for Docker)
  - macOS 10.15 (Catalina) or newer
  - Ubuntu 20.04 LTS or newer

- **Hardware Requirements**:
  - 8GB RAM minimum (16GB recommended)
  - 4 CPU cores (or virtual cores)
  - 30GB free disk space

### Required Accounts

1. **GitHub**: Create or use an existing account at [github.com](https://github.com)
2. **AWS Account** (optional for S3 testing): [aws.amazon.com](https://aws.amazon.com)
3. **MongoDB Atlas** (optional, for cloud database): [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)

## Core Development Tools

### Visual Studio Code

Visual Studio Code is our recommended IDE for consistent development experience.

#### Installation

1. Download from [code.visualstudio.com](https://code.visualstudio.com/download)
2. Follow the installation instructions for your operating system

#### Required Extensions

Install the following extensions from the VS Code marketplace:

- **Essential Extensions**:
  - Python (ms-python.python)
  - ESLint (dbaeumer.vscode-eslint)
  - Prettier (esbenp.prettier-vscode)
  - Docker (ms-azuretools.vscode-docker)
  - EditorConfig (editorconfig.editorconfig)
  - GitLens (eamodio.gitlens)

- **Recommended Extensions**:
  - MongoDB for VS Code (mongodb.mongodb-vscode)
  - REST Client (humao.rest-client)
  - Thunder Client (rangav.vscode-thunder-client)
  - Todo Tree (gruntfuggly.todo-tree)
  - Error Lens (usernamehw.errorlens)

#### VS Code Configuration

Create the following files in your project root directory:

**.vscode/settings.json**:
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackPath": "${workspaceFolder}/.venv/bin/black",
  "eslint.validate": ["javascript", "typescript", "typescriptreact"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

### Git and GitHub

Git is required for version control and collaborating with the team.

#### Installation

**Windows**:
- Download Git from [git-scm.com](https://git-scm.com/download/win) and install

**macOS**:
- Using Homebrew: `brew install git`
- Or download from [git-scm.com](https://git-scm.com/download/mac)

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install git
```

#### Git Configuration

Set up your Git identity:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Configure line endings:
```bash
# On Windows
git config --global core.autocrlf true

# On Mac/Linux
git config --global core.autocrlf input
```

#### GitHub SSH Setup

For secure GitHub access, setting up SSH is recommended:

1. Generate SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```

2. Add the SSH key to your SSH agent:
   ```bash
   # Start the SSH agent
   eval "$(ssh-agent -s)"
   
   # Add your key
   ssh-add ~/.ssh/id_ed25519
   ```

3. Add the public key to your GitHub account:
   - Copy the contents of your public key:
     ```bash
     cat ~/.ssh/id_ed25519.pub
     ```
   - Go to GitHub Settings → SSH and GPG keys → New SSH key
   - Paste your key and save

4. Test the connection:
   ```bash
   ssh -T git@github.com
   ```

### Postman

Postman is essential for API testing and development.

#### Installation

1. Download from [postman.com/downloads](https://www.postman.com/downloads/)
2. Follow the installation instructions for your OS

#### Project Collection Setup

The team shares Postman collections for API testing. To import:

1. In Postman, click "Import" button
2. Select the collection JSON file from the project repository (`/docs/api/postman_collection.json`)
3. The collection will be imported with all predefined requests

## Backend Development Environment

### Python 3.11

Python 3.11 is required for the backend services.

#### Installation

**Windows**:
1. Download Python 3.11 from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer, check "Add Python to PATH"
3. Verify installation: `python --version`

**macOS**:
```bash
# Using Homebrew
brew install python@3.11

# Add to your PATH if needed
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
python3.11 --version
```

**Linux (Ubuntu)**:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
python3.11 --version
```

### Poetry

Poetry is used for dependency management and packaging for Python projects.

#### Installation

**All Platforms**:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify installation:
```bash
poetry --version
```

Add to PATH if needed (follow instructions from installer output).

#### Poetry Configuration

Configure Poetry to create virtual environments inside the project:
```bash
poetry config virtualenvs.in-project true
```

### Python Linting & Formatting

#### Installation

We use pylint for linting and black for formatting:
```bash
pip install pylint black
```

#### Configuration

Create a `.pylintrc` file in your project root with project-specific settings. A basic configuration:

```ini
[MASTER]
ignore=CVS
ignore-patterns=
persistent=yes
load-plugins=

[MESSAGES CONTROL]
disable=C0111,R0903,C0103

[REPORTS]
output-format=text
reports=yes
evaluation=10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)

[BASIC]
good-names=i,j,k,ex,Run,_
```

Create a `pyproject.toml` file with Black configuration:

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

## Frontend Development Environment

### Node.js and npm

Node.js and npm are required for the frontend development environment.

#### Installation

**All Platforms**:
1. Install Node.js 18.x LTS from [nodejs.org](https://nodejs.org/)
2. Verify installation:
   ```bash
   node --version
   npm --version
   ```

Alternatively, use nvm (Node Version Manager) for easier version management:

**macOS/Linux**:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
source ~/.bashrc  # or ~/.zshrc
nvm install 18
nvm use 18
```

**Windows**:
- Use [nvm-windows](https://github.com/coreybutler/nvm-windows)

### TypeScript

TypeScript 5.2 is used for the frontend development.

#### Installation

```bash
npm install -g typescript@5.2
```

Verify installation:
```bash
tsc --version
```

### ESLint and Prettier

ESLint is used for JavaScript/TypeScript linting, and Prettier for formatting.

#### Installation

```bash
npm install -g eslint prettier
```

#### Configuration

Create the following config files in your project frontend directory:

**.eslintrc.json**:
```json
{
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaFeatures": {
      "jsx": true
    },
    "ecmaVersion": 2021,
    "sourceType": "module"
  },
  "plugins": ["react", "@typescript-eslint", "react-hooks", "prettier"],
  "rules": {
    "prettier/prettier": "error",
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off"
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

**.prettierrc**:
```json
{
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true
}
```

## Database Setup

The Task Management System uses MongoDB as the main database, Redis for caching, and AWS S3 for file storage.

### MongoDB

#### Local Installation

**Docker (Recommended)**:
```bash
docker run --name mongodb -d -p 27017:27017 -v mongodb_data:/data/db mongo:5.0
```

**Manual Installation**:

**Windows**:
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Follow the installation wizard
3. Start MongoDB service

**macOS**:
```bash
brew tap mongodb/brew
brew install mongodb-community@5.0
brew services start mongodb-community@5.0
```

**Linux (Ubuntu)**:
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### MongoDB Compass (GUI Client)

1. Download MongoDB Compass from [mongodb.com/products/compass](https://www.mongodb.com/products/compass)
2. Install and connect to your local MongoDB instance with the connection string: `mongodb://localhost:27017`

### Redis

#### Local Installation

**Docker (Recommended)**:
```bash
docker run --name redis -d -p 6379:6379 redis:6.2
```

**Manual Installation**:

**Windows**:
- Redis is not officially supported on Windows. Use Docker or WSL2.

**macOS**:
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu)**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### Redis Insight (GUI Client)

1. Download RedisInsight from [redis.com/redis-enterprise/redis-insight](https://redis.com/redis-enterprise/redis-insight/)
2. Install and connect to your local Redis instance with the host `localhost` and port `6379`

### AWS S3 (LocalStack for Development)

For local development, we use LocalStack to emulate AWS S3.

#### Installation with Docker

```bash
docker run --name localstack -d -p 4566:4566 -p 4571:4571 localstack/localstack
```

#### Creating Local S3 Bucket

Using AWS CLI with LocalStack:

1. Install AWS CLI:
   ```bash
   pip install awscli
   ```

2. Create a bucket in LocalStack:
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 mb s3://task-management-files
   ```

3. Test the bucket:
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 ls
   ```

## Docker Environment

Docker is used for containerization and creating consistent development environments.

### Docker Desktop Installation

**Windows/macOS**:
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Follow the installation instructions
3. Start Docker Desktop

**Linux (Ubuntu)**:
```bash
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ${USER}
```
Log out and back in for group changes to take effect.

### Docker Compose

Docker Compose is used to orchestrate the development environment with all required services.

Create a `docker-compose.yml` file in the project root with the following content:

```yaml
version: '3.8'

services:
  # MongoDB
  mongodb:
    image: mongo:5.0
    container_name: tms-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=example
    networks:
      - tms-network

  # Redis
  redis:
    image: redis:6.2
    container_name: tms-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - tms-network

  # LocalStack (AWS S3)
  localstack:
    image: localstack/localstack
    container_name: tms-localstack
    ports:
      - "4566:4566"
      - "4571:4571"
    environment:
      - SERVICES=s3
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - ./localstack:/tmp/localstack
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - tms-network

networks:
  tms-network:
    driver: bridge

volumes:
  mongodb_data:
  redis_data:
```

Run the Docker Compose environment:
```bash
docker-compose up -d
```

## Project Setup

### Clone the Repository

```bash
git clone git@github.com:your-org/task-management-system.git
cd task-management-system
```

### Configure Backend Services

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Create environment variables file:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your local configuration (MongoDB, Redis, S3 settings).

### Configure Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment variables file:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your local API endpoint configuration.

### Initial Database Setup

1. Run the database initialization script:
   ```bash
   cd backend
   python scripts/init_db.py
   ```

This will create necessary collections and indexes in MongoDB.

### Create S3 Bucket

If using LocalStack (recommended for development):

```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://task-management-files
```

## Development Workflow

### Starting the Development Environment

1. Start the Docker containers (if not already running):
   ```bash
   docker-compose up -d
   ```

2. Start the backend services:
   ```bash
   cd backend
   poetry shell
   python run.py
   ```

3. Start the frontend development server:
   ```bash
   cd frontend
   npm start
   ```

### Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- MongoDB: localhost:27017
- Redis: localhost:6379
- LocalStack S3: http://localhost:4566

### Development Best Practices

1. **Branch Strategy**:
   - Main branch: `main` (production-ready code)
   - Development branch: `develop` (integration branch)
   - Feature branches: `feature/feature-name`
   - Fix branches: `fix/issue-name`

2. **Commit Guidelines**:
   - Follow conventional commits format:
     - `feat: add new user dashboard`
     - `fix: correct login validation error`
     - `docs: update API documentation`
     - `chore: update dependencies`

3. **Code Reviews**:
   - All code changes require at least one review
   - Use GitHub pull requests
   - Run linting and tests before submitting for review

4. **Testing**:
   - Write unit tests for backend logic
   - Write component tests for frontend
   - Run the test suite before committing:
     ```bash
     # Backend
     cd backend
     pytest
     
     # Frontend
     cd frontend
     npm test
     ```

## Troubleshooting

### Common Issues and Solutions

#### Docker Issues

**Problem**: Cannot start Docker containers
**Solution**:
- Ensure Docker Desktop is running
- Check available system resources
- Try resetting Docker to factory defaults

**Problem**: Port conflicts
**Solution**:
- Check if another application is using the required ports
- Modify the port mappings in docker-compose.yml

#### MongoDB Issues

**Problem**: Cannot connect to MongoDB
**Solution**:
- Verify the MongoDB container is running: `docker ps | grep mongodb`
- Check MongoDB logs: `docker logs tms-mongodb`
- Ensure connection string is correct in your .env file

#### Python/Poetry Issues

**Problem**: Poetry cannot install dependencies
**Solution**:
- Update Poetry: `poetry self update`
- Clear Poetry cache: `poetry cache clear pypi --all`
- Check Python version compatibility: `python --version`

#### Node.js/npm Issues

**Problem**: npm install fails
**Solution**:
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Update npm: `npm install -g npm`

### Getting Help

If you encounter issues not covered here:

1. Check the project GitHub Issues for similar problems
2. Ask in the development team Slack channel #dev-help
3. Contact the project maintainers via email

### Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Redis Documentation](https://redis.io/documentation)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Poetry Documentation](https://python-poetry.org/docs/)