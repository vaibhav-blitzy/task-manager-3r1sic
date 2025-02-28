#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for the Task Management System backend.

This script configures the Python package with metadata, dependencies,
and installation requirements. It enables the backend services to be
installed as a package and used across the application.
"""

import os
import io
import re
from setuptools import setup, find_packages

# Path to the directory containing this file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Read the README file for long description
try:
    with io.open(os.path.join(BASE_DIR, 'README.md'), encoding='utf-8') as f:
        README = f.read()
except FileNotFoundError:
    README = "Task Management System Backend - A comprehensive task management solution"

# Package name
PACKAGE_NAME = 'task-management-backend'

def get_version():
    """
    Extract version string from the common package __init__.py file.
    
    Returns:
        str: Version string (e.g., '1.0.0')
    """
    init_path = os.path.join(BASE_DIR, 'common', '__init__.py')
    try:
        with io.open(init_path, encoding='utf-8') as f:
            init_content = f.read()
            version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", 
                                      init_content, re.M)
            if version_match:
                return version_match.group(1)
    except (FileNotFoundError, IOError):
        pass
    return '0.1.0'

VERSION = get_version()

def get_requirements():
    """
    Read requirements from requirements.txt file
    
    Returns:
        list: List of requirement strings
    """
    requirements_path = os.path.join(BASE_DIR, 'requirements.txt')
    try:
        with io.open(requirements_path, encoding='utf-8') as f:
            return [line.strip() for line in f
                    if line.strip() and not line.startswith('#')]
    except (FileNotFoundError, IOError):
        # Default requirements if file not found
        return [
            'Flask==2.3.2',                    # API development framework
            'Flask-RESTful==0.3.10',           # REST API framework
            'Flask-SQLAlchemy==3.0.5',         # ORM
            'Flask-Migrate==4.0.4',            # Database migrations
            'Flask-JWT-Extended==4.5.2',       # Authentication
            'Flask-SocketIO==5.3.4',           # Real-time communications
            'Celery==5.3.1',                   # Task queue
            'pytest==7.4.0',                   # Testing framework
            'pymongo==4.5.0',                  # MongoDB driver
            'redis==4.6.0',                    # Redis client
            'boto3==1.28.38',                  # AWS SDK
            'gunicorn==21.2.0',                # WSGI HTTP Server
            'Werkzeug==2.3.6',                 # WSGI utilities
            'marshmallow==3.20.1',             # Object serialization/deserialization
            'python-dotenv==1.0.0',            # Environment variable management
            'requests==2.31.0',                # HTTP library
            'PyJWT==2.8.0',                    # JSON Web Token implementation
            'cryptography==41.0.3',            # Cryptographic recipes
            'Pygments==2.16.1',                # Syntax highlighting
            'Click==8.1.7',                    # Command line interface creation
        ]

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description='Task Management System Backend Services',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Task Management System Team',
    author_email='team@taskmanagementsystem.com',
    url='https://github.com/taskmanagementsystem/backend',
    packages=find_packages(exclude=['tests*', 'scripts*']),
    include_package_data=True,
    python_requires='>=3.11',
    install_requires=get_requirements(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'tms-run-services=backend.scripts.run_services:main',
            'tms-create-service=backend.scripts.create_service:main',
        ],
    },
    zip_safe=False,
)