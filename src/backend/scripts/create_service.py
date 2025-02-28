#!/usr/bin/env python3
"""
Service Creator Script

This script creates a new microservice for the Task Management System with the proper 
directory structure and all necessary boilerplate files. It scaffolds the complete 
service framework based on the architectural patterns used throughout the system.
"""

import os
import sys
import argparse
import re
import shutil
from os import path, makedirs, listdir

# Define the root and services directories
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(ROOT_DIR, 'services')

# Templates for all the files
TEMPLATES = {
    'app.py': '''"""
{service_name} Service

This module initializes and configures the Flask application for the {service_name} service.
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from {service_name}.api import api_blueprint
from {service_name}.config import CONFIG

def create_app(env='development'):
    """Create and configure the Flask application.
    
    Args:
        env (str): The environment to use for configuration ('development', 'testing', 'production')
        
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(CONFIG[env])
    
    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api/v1/{service_name}')
    
    return app

def init_app():
    """Initialize the application with default configuration.
    
    Returns:
        Flask: The initialized Flask application
    """
    return create_app()

app = init_app()
''',

    'config.py': '''"""
Configuration settings for the {service_name} service.

This module defines configuration classes for different environments (development, testing, production).
"""

import os

class BaseConfig:
    """Base configuration class for all environments."""
    
    DEBUG = False
    TESTING = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/{service_name}')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

class DevelopmentConfig(BaseConfig):
    """Configuration for development environment."""
    
    DEBUG = True
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/{service_name}_dev')

class TestingConfig(BaseConfig):
    """Configuration for testing environment."""
    
    TESTING = True
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/{service_name}_test')

class ProductionConfig(BaseConfig):
    """Configuration for production environment."""
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # Must be set in production
    MONGO_URI = os.getenv('MONGO_URI')  # Must be set in production

# Configuration dictionary
CONFIG = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
''',

    'wsgi.py': '''"""
WSGI entry point for the {service_name} service.

This module exposes the Flask application as a WSGI application.
"""

from {service_name}.app import app
import os

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
''',

    'Dockerfile': '''# Use Python 3.11 slim as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV MODULE_NAME="{service_name}.wsgi"
ENV VARIABLE_NAME="app"
ENV PORT=5000

# Expose the port
EXPOSE $PORT

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
''',

    'requirements.txt': '''# Flask and Extensions
Flask==2.3.3
Flask-RESTful==0.3.10
Flask-JWT-Extended==4.5.2
Flask-Cors==4.0.0

# Database
pymongo==4.5.0
Flask-PyMongo==2.3.0

# Utilities
pydantic==2.1.1
marshmallow==3.20.1
python-dotenv==1.0.0
gunicorn==21.2.0

# Testing
pytest==7.4.0
pytest-flask==1.2.0
pytest-cov==4.1.0
''',

    '__init__.py': '''"""
{service_name} service package.
"""
''',

    'model.py': '''"""
Model definitions for the {service_name} service.

This module defines the data models for the {service_name} domain.
"""

from datetime import datetime
from bson import ObjectId

class {model_name}:
    """
    {model_name} model representing a {service_name} entity.
    """
    
    def __init__(self, name, description=None, status="active", created_by=None, **kwargs):
        """
        Initialize a new {model_name} instance.
        
        Args:
            name (str): The name of the {model_name}
            description (str, optional): A description of the {model_name}
            status (str, optional): The status of the {model_name}
            created_by (str, optional): The ID of the user who created this {model_name}
            **kwargs: Additional fields to set on the {model_name}
        """
        self.id = kwargs.get('id') or kwargs.get('_id')
        self.name = name
        self.description = description
        self.status = status
        self.created_by = created_by
        self.created_at = kwargs.get('created_at') or datetime.utcnow()
        self.updated_at = kwargs.get('updated_at') or datetime.utcnow()
        
        # Add any additional fields from kwargs
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """
        Convert the {model_name} instance to a dictionary.
        
        Returns:
            dict: A dictionary representation of the {model_name}
        """
        result = {
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if self.id:
            result['id'] = str(self.id) if isinstance(self.id, ObjectId) else self.id
            
        return result
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a {model_name} instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing {model_name} data
            
        Returns:
            {model_name}: A new {model_name} instance
        """
        return cls(**data)
    
    def __repr__(self):
        """String representation of the {model_name}."""
        return f"<{model_name} {self.name}>"
''',

    'service.py': '''"""
Service layer for the {service_name} service.

This module contains the business logic for the {service_name} domain.
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

from {service_name}.models.{model_name_lower} import {model_name}

class {model_name}Service:
    """
    Service class for {model_name} operations.
    """
    
    def __init__(self, mongo_uri=None):
        """
        Initialize the {model_name}Service.
        
        Args:
            mongo_uri (str, optional): MongoDB connection URI
        """
        self.mongo_uri = mongo_uri or "mongodb://localhost:27017/{service_name}"
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client.get_database()
        self.collection = self.db["{model_name_lower}s"]
    
    def get_all(self, filter_params=None, page=1, per_page=20):
        """
        Get all {model_name_lower}s with optional filtering and pagination.
        
        Args:
            filter_params (dict, optional): Dictionary of filter parameters
            page (int, optional): Page number, starting from 1
            per_page (int, optional): Number of items per page
            
        Returns:
            list: List of {model_name} objects
        """
        filter_params = filter_params or {}
        skip = (page - 1) * per_page
        
        cursor = self.collection.find(filter_params).skip(skip).limit(per_page)
        return [self._document_to_model(doc) for doc in cursor]
    
    def get_by_id(self, {model_name_lower}_id):
        """
        Get a {model_name_lower} by ID.
        
        Args:
            {model_name_lower}_id (str): The ID of the {model_name_lower}
            
        Returns:
            {model_name}: The {model_name} object if found, None otherwise
        """
        if not {model_name_lower}_id:
            return None
            
        object_id = ObjectId({model_name_lower}_id) if not isinstance({model_name_lower}_id, ObjectId) else {model_name_lower}_id
        document = self.collection.find_one({"_id": object_id})
        return self._document_to_model(document) if document else None
    
    def create(self, {model_name_lower}_data):
        """
        Create a new {model_name_lower}.
        
        Args:
            {model_name_lower}_data (dict): Dictionary containing {model_name_lower} data
            
        Returns:
            {model_name}: The created {model_name} object
        """
        {model_name_lower} = {model_name}.from_dict({model_name_lower}_data)
        {model_name_lower}_dict = {model_name_lower}.to_dict()
        
        # Remove id if it's None
        if 'id' in {model_name_lower}_dict and not {model_name_lower}_dict['id']:
            del {model_name_lower}_dict['id']
        
        # Set timestamps
        now = datetime.utcnow()
        {model_name_lower}_dict['created_at'] = now
        {model_name_lower}_dict['updated_at'] = now
        
        result = self.collection.insert_one({model_name_lower}_dict)
        {model_name_lower}.id = result.inserted_id
        
        return {model_name_lower}
    
    def update(self, {model_name_lower}_id, {model_name_lower}_data):
        """
        Update an existing {model_name_lower}.
        
        Args:
            {model_name_lower}_id (str): The ID of the {model_name_lower} to update
            {model_name_lower}_data (dict): Dictionary containing updated {model_name_lower} data
            
        Returns:
            {model_name}: The updated {model_name} object
        """
        object_id = ObjectId({model_name_lower}_id) if not isinstance({model_name_lower}_id, ObjectId) else {model_name_lower}_id
        
        # Set update timestamp
        {model_name_lower}_data['updated_at'] = datetime.utcnow()
        
        # Remove fields that should not be updated
        if 'id' in {model_name_lower}_data:
            del {model_name_lower}_data['id']
        if 'created_at' in {model_name_lower}_data:
            del {model_name_lower}_data['created_at']
        
        result = self.collection.update_one(
            {"_id": object_id},
            {"$set": {model_name_lower}_data}
        )
        
        if result.modified_count > 0:
            return self.get_by_id({model_name_lower}_id)
        return None
    
    def delete(self, {model_name_lower}_id):
        """
        Delete a {model_name_lower}.
        
        Args:
            {model_name_lower}_id (str): The ID of the {model_name_lower} to delete
            
        Returns:
            bool: True if the {model_name_lower} was deleted, False otherwise
        """
        object_id = ObjectId({model_name_lower}_id) if not isinstance({model_name_lower}_id, ObjectId) else {model_name_lower}_id
        result = self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    
    def _document_to_model(self, document):
        """
        Convert a MongoDB document to a {model_name} model.
        
        Args:
            document (dict): MongoDB document
            
        Returns:
            {model_name}: {model_name} instance
        """
        if not document:
            return None
            
        document_copy = document.copy()
        document_copy['id'] = document_copy.pop('_id')
        return {model_name}.from_dict(document_copy)
''',

    'api.py': '''"""
API routes for the {service_name} service.

This module defines the API endpoints for the {service_name} domain.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.errors import InvalidId

from {service_name}.services.{model_name_lower}_service import {model_name}Service

api_blueprint = Blueprint('{service_name}', __name__)
{model_name_lower}_service = {model_name}Service()

@api_blueprint.route('/{model_name_lower}s', methods=['GET'])
@jwt_required()
def get_{model_name_lower}s():
    """
    Get all {model_name_lower}s with optional filtering and pagination.
    
    Returns:
        JSON response with list of {model_name_lower}s
    """
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build filter parameters
        filter_params = {}
        for key in ['status', 'created_by']:
            if key in request.args:
                filter_params[key] = request.args[key]
        
        {model_name_lower}s = {model_name_lower}_service.get_all(filter_params, page, per_page)
        
        return jsonify({
            'data': [{model_name_lower}.to_dict() for {model_name_lower} in {model_name_lower}s],
            'page': page,
            'per_page': per_page,
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@api_blueprint.route('/{model_name_lower}s/<{model_name_lower}_id>', methods=['GET'])
@jwt_required()
def get_{model_name_lower}({model_name_lower}_id):
    """
    Get a {model_name_lower} by ID.
    
    Args:
        {model_name_lower}_id (str): The ID of the {model_name_lower}
        
    Returns:
        JSON response with {model_name_lower} data
    """
    try:
        {model_name_lower} = {model_name_lower}_service.get_by_id({model_name_lower}_id)
        
        if not {model_name_lower}:
            return jsonify({
                'error': '{model_name} not found',
                'success': False
            }), 404
            
        return jsonify({
            'data': {model_name_lower}.to_dict(),
            'success': True
        }), 200
        
    except InvalidId:
        return jsonify({
            'error': 'Invalid ID format',
            'success': False
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@api_blueprint.route('/{model_name_lower}s', methods=['POST'])
@jwt_required()
def create_{model_name_lower}():
    """
    Create a new {model_name_lower}.
    
    Returns:
        JSON response with created {model_name_lower} data
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({
                'error': 'Name is required',
                'success': False
            }), 400
            
        # Set created_by to current user
        current_user = get_jwt_identity()
        data['created_by'] = current_user
        
        {model_name_lower} = {model_name_lower}_service.create(data)
        
        return jsonify({
            'data': {model_name_lower}.to_dict(),
            'success': True,
            'message': '{model_name} created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@api_blueprint.route('/{model_name_lower}s/<{model_name_lower}_id>', methods=['PUT'])
@jwt_required()
def update_{model_name_lower}({model_name_lower}_id):
    """
    Update an existing {model_name_lower}.
    
    Args:
        {model_name_lower}_id (str): The ID of the {model_name_lower} to update
        
    Returns:
        JSON response with updated {model_name_lower} data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'success': False
            }), 400
            
        {model_name_lower} = {model_name_lower}_service.update({model_name_lower}_id, data)
        
        if not {model_name_lower}:
            return jsonify({
                'error': '{model_name} not found',
                'success': False
            }), 404
            
        return jsonify({
            'data': {model_name_lower}.to_dict(),
            'success': True,
            'message': '{model_name} updated successfully'
        }), 200
        
    except InvalidId:
        return jsonify({
            'error': 'Invalid ID format',
            'success': False
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@api_blueprint.route('/{model_name_lower}s/<{model_name_lower}_id>', methods=['DELETE'])
@jwt_required()
def delete_{model_name_lower}({model_name_lower}_id):
    """
    Delete a {model_name_lower}.
    
    Args:
        {model_name_lower}_id (str): The ID of the {model_name_lower} to delete
        
    Returns:
        JSON response with deletion status
    """
    try:
        result = {model_name_lower}_service.delete({model_name_lower}_id)
        
        if not result:
            return jsonify({
                'error': '{model_name} not found',
                'success': False
            }), 404
            
        return jsonify({
            'success': True,
            'message': '{model_name} deleted successfully'
        }), 200
        
    except InvalidId:
        return jsonify({
            'error': 'Invalid ID format',
            'success': False
        }), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
''',

    'test_api.py': '''"""
API tests for the {service_name} service.

This module contains tests for the {service_name} API endpoints.
"""

import json
import pytest
from flask_jwt_extended import create_access_token

from {service_name}.app import create_app
from {service_name}.models.{model_name_lower} import {model_name}

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app('testing')
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    """Create authentication headers with JWT token."""
    with app.app_context():
        token = create_access_token(identity='test_user')
        headers = {
            'Authorization': f'Bearer {{token}}',
            'Content-Type': 'application/json'
        }
        return headers

def test_get_{model_name_lower}s(client, auth_headers):
    """Test getting all {model_name_lower}s."""
    response = client.get('/api/v1/{service_name}/{model_name_lower}s', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data
    assert isinstance(data['data'], list)

def test_get_{model_name_lower}_by_id_not_found(client, auth_headers):
    """Test getting a non-existent {model_name_lower}."""
    response = client.get('/api/v1/{service_name}/{model_name_lower}s/60f1a5c85f1c8d1234567890', headers=auth_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data

def test_create_{model_name_lower}(client, auth_headers):
    """Test creating a new {model_name_lower}."""
    {model_name_lower}_data = {{
        'name': 'Test {model_name}',
        'description': 'Test description',
        'status': 'active'
    }}
    
    response = client.post(
        '/api/v1/{service_name}/{model_name_lower}s',
        data=json.dumps({model_name_lower}_data),
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data
    assert data['data']['name'] == {model_name_lower}_data['name']
    assert 'id' in data['data']

def test_create_{model_name_lower}_invalid(client, auth_headers):
    """Test creating a {model_name_lower} with invalid data."""
    {model_name_lower}_data = {{
        'description': 'Missing name field'
    }}
    
    response = client.post(
        '/api/v1/{service_name}/{model_name_lower}s',
        data=json.dumps({model_name_lower}_data),
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data

def test_update_{model_name_lower}(client, auth_headers, mocker):
    """Test updating a {model_name_lower}."""
    # Mock the service to return a {model_name_lower} for testing update
    {model_name_lower} = {model_name}(
        name='Original Name', 
        description='Original description'
    )
    {model_name_lower}.id = '60f1a5c85f1c8d1234567890'
    
    mocker.patch(
        '{service_name}.services.{model_name_lower}_service.{model_name}Service.get_by_id',
        return_value={model_name_lower}
    )
    
    mocker.patch(
        '{service_name}.services.{model_name_lower}_service.{model_name}Service.update',
        return_value={model_name_lower}
    )
    
    update_data = {{
        'name': 'Updated Name',
        'description': 'Updated description'
    }}
    
    response = client.put(
        '/api/v1/{service_name}/{model_name_lower}s/60f1a5c85f1c8d1234567890',
        data=json.dumps(update_data),
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'data' in data

def test_delete_{model_name_lower}(client, auth_headers, mocker):
    """Test deleting a {model_name_lower}."""
    mocker.patch(
        '{service_name}.services.{model_name_lower}_service.{model_name}Service.delete',
        return_value=True
    )
    
    response = client.delete(
        '/api/v1/{service_name}/{model_name_lower}s/60f1a5c85f1c8d1234567890',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'message' in data
''',

    'conftest.py': '''"""
Pytest configuration file for {service_name} service tests.

This module contains shared fixtures for tests.
"""

import pytest
from pymongo import MongoClient
from flask_jwt_extended import create_access_token

from {service_name}.app import create_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app('testing')
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def mongodb():
    """Set up a MongoDB test database and clean it up after tests."""
    mongo_client = MongoClient('mongodb://localhost:27017/{service_name}_test')
    db = mongo_client.get_database()
    
    # Clear test database before tests
    for collection in db.list_collection_names():
        db[collection].delete_many({})
        
    yield db
    
    # Clean up after tests
    for collection in db.list_collection_names():
        db[collection].delete_many({})
    
    mongo_client.close()

@pytest.fixture
def auth_headers(app):
    """Create authentication headers with JWT token."""
    with app.app_context():
        token = create_access_token(identity='test_user')
        headers = {
            'Authorization': f'Bearer {{token}}',
            'Content-Type': 'application/json'
        }
        return headers
'''
}

def validate_service_name(service_name):
    """
    Validates that the service name follows project conventions and doesn't already exist.
    
    Args:
        service_name (str): The name of the service to create
        
    Returns:
        bool: True if service name is valid, False otherwise
    """
    # Check if service name is a valid Python identifier
    if not re.match(r'^[a-z][a-z0-9_]*$', service_name):
        print(f"Error: Service name '{service_name}' is invalid. It must start with a lowercase letter and contain only lowercase letters, numbers, and underscores.")
        return False
    
    # Check if service already exists
    service_path = os.path.join(SERVICES_DIR, service_name)
    if os.path.exists(service_path):
        print(f"Error: Service '{service_name}' already exists at {service_path}")
        return False
    
    return True

def create_directory_structure(service_name, service_path):
    """
    Creates the directory structure for a new service following project patterns.
    
    Args:
        service_name (str): The name of the service
        service_path (str): Path to the service directory
    """
    # Create main service directory
    os.makedirs(service_path, exist_ok=True)
    
    # Create subdirectories
    subdirs = ['models', 'services', 'api', 'tests']
    for subdir in subdirs:
        os.makedirs(os.path.join(service_path, subdir), exist_ok=True)
    
    # Create __init__.py files in each directory
    for root, dirs, _ in os.walk(service_path):
        write_file(
            os.path.join(root, '__init__.py'), 
            TEMPLATES['__init__.py'].format(service_name=service_name)
        )
    
    # Create conftest.py for pytest
    write_file(
        os.path.join(service_path, 'tests', 'conftest.py'),
        TEMPLATES['conftest.py'].format(service_name=service_name)
    )

def write_file(file_path, content):
    """
    Helper function to write content to a file, creating parent directories if needed.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to write to the file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write content to file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Created: {file_path}")

def generate_app_file(service_name):
    """
    Generates content for app.py with Flask application setup.
    
    Args:
        service_name (str): Name of the service
        
    Returns:
        str: Content for app.py file
    """
    return TEMPLATES['app.py'].format(service_name=service_name)

def generate_config_file(service_name):
    """
    Generates content for config.py with environment-specific configurations.
    
    Args:
        service_name (str): Name of the service
        
    Returns:
        str: Content for config.py file
    """
    return TEMPLATES['config.py'].format(service_name=service_name)

def generate_wsgi_file(service_name):
    """
    Generates content for wsgi.py as the WSGI entry point.
    
    Args:
        service_name (str): Name of the service
        
    Returns:
        str: Content for wsgi.py file
    """
    return TEMPLATES['wsgi.py'].format(service_name=service_name)

def generate_dockerfile(service_name):
    """
    Generates content for Dockerfile to containerize the service.
    
    Args:
        service_name (str): Name of the service
        
    Returns:
        str: Content for Dockerfile
    """
    return TEMPLATES['Dockerfile'].format(service_name=service_name)

def generate_requirements_file():
    """
    Generates content for requirements.txt with service dependencies.
    
    Returns:
        str: Content for requirements.txt file
    """
    return TEMPLATES['requirements.txt']

def generate_model_file(service_name, model_name):
    """
    Generates a basic model file for the service domain.
    
    Args:
        service_name (str): Name of the service
        model_name (str): Name of the model class
        
    Returns:
        str: Content for model file
    """
    return TEMPLATES['model.py'].format(service_name=service_name, model_name=model_name)

def generate_service_file(service_name, model_name):
    """
    Generates a service file with business logic for the domain.
    
    Args:
        service_name (str): Name of the service
        model_name (str): Name of the model class
        
    Returns:
        str: Content for service file
    """
    model_name_lower = model_name.lower()
    return TEMPLATES['service.py'].format(
        service_name=service_name, 
        model_name=model_name, 
        model_name_lower=model_name_lower
    )

def generate_api_file(service_name, model_name):
    """
    Generates an API file with routes for the service domain.
    
    Args:
        service_name (str): Name of the service
        model_name (str): Name of the model class
        
    Returns:
        str: Content for API file
    """
    model_name_lower = model_name.lower()
    return TEMPLATES['api.py'].format(
        service_name=service_name, 
        model_name=model_name, 
        model_name_lower=model_name_lower
    )

def generate_test_file(service_name, model_name):
    """
    Generates a test file for the API endpoints.
    
    Args:
        service_name (str): Name of the service
        model_name (str): Name of the model class
        
    Returns:
        str: Content for test file
    """
    model_name_lower = model_name.lower()
    return TEMPLATES['test_api.py'].format(
        service_name=service_name, 
        model_name=model_name, 
        model_name_lower=model_name_lower
    )

def create_service_files(service_name, service_path):
    """
    Creates all necessary files for a new service.
    
    Args:
        service_name (str): Name of the service
        service_path (str): Path to the service directory
    """
    # Determine model name (capitalized service name without underscores)
    model_name = ''.join(word.capitalize() for word in service_name.split('_'))
    model_name_lower = model_name.lower()
    
    # Create root service files
    write_file(os.path.join(service_path, 'app.py'), generate_app_file(service_name))
    write_file(os.path.join(service_path, 'config.py'), generate_config_file(service_name))
    write_file(os.path.join(service_path, 'wsgi.py'), generate_wsgi_file(service_name))
    write_file(os.path.join(service_path, 'Dockerfile'), generate_dockerfile(service_name))
    write_file(os.path.join(service_path, 'requirements.txt'), generate_requirements_file())
    
    # Create model files
    write_file(
        os.path.join(service_path, 'models', f'{model_name_lower}.py'),
        generate_model_file(service_name, model_name)
    )
    
    # Create service files
    write_file(
        os.path.join(service_path, 'services', f'{model_name_lower}_service.py'),
        generate_service_file(service_name, model_name)
    )
    
    # Create API files
    write_file(
        os.path.join(service_path, 'api', 'api.py'),
        generate_api_file(service_name, model_name)
    )
    
    # Create test files
    write_file(
        os.path.join(service_path, 'tests', f'test_{model_name_lower}_api.py'),
        generate_test_file(service_name, model_name)
    )

def main():
    """
    Main function that handles the creation of a new service.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description='Create a new microservice for the Task Management System')
    parser.add_argument('service_name', help='Name of the service to create (lowercase with underscores)')
    
    args = parser.parse_args()
    service_name = args.service_name
    
    # Validate service name
    if not validate_service_name(service_name):
        return 1
    
    # Create service path
    service_path = os.path.join(SERVICES_DIR, service_name)
    
    # Create directory structure
    print(f"Creating directory structure for service: {service_name}")
    create_directory_structure(service_name, service_path)
    
    # Create service files
    print(f"Creating service files for: {service_name}")
    create_service_files(service_name, service_path)
    
    print(f"\nService '{service_name}' created successfully!")
    print(f"Location: {service_path}")
    print("\nNext steps:")
    print(f"1. Review the generated files in {service_path}")
    print(f"2. Install dependencies: cd {service_path} && pip install -r requirements.txt")
    print(f"3. Run the service: python -m {service_name}.app")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())