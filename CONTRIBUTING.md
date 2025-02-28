# Contributing to Task Management System

Thank you for your interest in contributing to the Task Management System project! This document provides guidelines and instructions to help you contribute effectively to our project.

## Table of Contents

- [Project Overview](#project-overview)
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Development Environment Setup](#development-environment-setup)
  - [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Commit Messages](#commit-messages)
  - [Development Process](#development-process)
- [Code Standards](#code-standards)
  - [Python Standards](#python-standards)
  - [TypeScript/React Standards](#typescriptreact-standards)
  - [Documentation Requirements](#documentation-requirements)
- [Testing Requirements](#testing-requirements)
  - [Test Coverage](#test-coverage)
  - [Test Types](#test-types)
  - [Test Naming](#test-naming)
- [Pull Request Process](#pull-request-process)
  - [PR Creation](#pr-creation)
  - [Automated Checks](#automated-checks)
  - [Code Review](#code-review)
  - [Merge Requirements](#merge-requirements)
- [Issue Reporting](#issue-reporting)
  - [Bug Reports](#bug-reports)
  - [Feature Requests](#feature-requests)
  - [Issue Labels](#issue-labels)
- [Security Considerations](#security-considerations)
  - [Security Testing](#security-testing)
  - [Vulnerability Reporting](#vulnerability-reporting)
  - [Security Best Practices](#security-best-practices)
- [Community Practices](#community-practices)
  - [Communication Channels](#communication-channels)
  - [Mentorship](#mentorship)
  - [Recognition](#recognition)
- [License Compliance](#license-compliance)

## Project Overview

The Task Management System is a comprehensive web application designed to streamline the organization, tracking, and collaboration on tasks and projects for both individuals and teams. It features task creation and assignment, project organization, real-time collaboration, progress visualization, role-based access control, and file attachment capabilities. This guide helps contributors understand how to effectively participate in the development of this system.

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. We expect all participants in our community to abide by the following guidelines:

- **Be respectful and inclusive**: Treat all individuals with respect. Do not engage in discriminatory, offensive, or harassing behavior or speech.
- **Be professional**: Disagreement and constructive criticism are welcome, but should always be expressed professionally and courteously.
- **Be collaborative**: Support each other, work together, and maintain transparency in your contributions.
- **Respect the work of others**: Honor the intellectual property and contributions of others.
- **Focus on what is best for the community**: Consider what is best for the community and project when making decisions.

Unacceptable behavior includes:
- Harassment of any kind
- Discriminatory jokes and language
- Posting sexually explicit or violent material
- Publishing others' private information without permission
- Any conduct that could reasonably be considered inappropriate in a professional setting

Violations of the code of conduct may result in removal from the project. Report any violations to the project maintainers.

## Getting Started

### Development Environment Setup

To contribute to the Task Management System, you'll need to set up your development environment. Please refer to our detailed [Development Environment Setup Guide](docs/development/setup.md) which covers:

- Required tools and dependencies:
  - Python 3.11
  - Node.js 18.x
  - Docker
  - MongoDB
  - Redis
- Installation instructions for all platforms
- Project configuration
- Database setup
- Running the application locally

### Project Structure

The project follows a microservices architecture with the following main components:

- **Backend**: Python (Flask) services in `src/backend`
- **Frontend**: TypeScript/React application in `src/web`
- **Infrastructure**: Docker configuration and deployment scripts
- **Documentation**: Project documentation in the `docs` directory

## Development Workflow

### Branching Strategy

We follow a trunk-based development approach with the following branch naming conventions:

- **Main branch**: `main` - production-ready code
- **Development branch**: `develop` - integration branch for feature development
- **Feature branches**: `feature/<feature-name>` - new features
- **Bug fix branches**: `bugfix/<bug-name>` - bug fixes
- **Hotfix branches**: `hotfix/<fix-name>` - urgent production fixes

Always create your working branches from the latest `develop` branch (or `main` for hotfixes).

### Commit Messages

We follow the conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types include**:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that don't affect code functionality (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or fixing tests
- `chore`: Changes to build process or auxiliary tools

**Examples**:
```
feat(auth): implement multi-factor authentication
fix(tasks): correct validation error in task creation
docs(api): update authentication endpoint documentation
```

### Development Process

1. **Pick an issue**: Start by selecting an issue to work on from our issue tracker
2. **Create a branch**: Create a new branch following our naming convention
3. **Develop your changes**: Make your changes following our coding standards
4. **Test thoroughly**: Ensure all tests pass and add new tests as needed
5. **Submit a PR**: Create a pull request following our PR template

## Code Standards

We maintain strict coding standards to ensure code quality and consistency. For complete details, please refer to our [Development Standards](docs/development/standards.md) documentation.

### Python Standards

- Follow PEP 8 style guidelines
- Use Google-style docstrings
- Include type annotations for all function parameters and return values
- Keep functions focused and follow single responsibility principle
- Maximum line length: 88 characters
- Use proper error handling with specific exception types

### TypeScript/React Standards

- Follow the AirBnB JavaScript Style Guide
- Use TypeScript strict mode and avoid `any` types
- Use functional components with hooks for React
- Follow component design patterns and atomic design principles
- Implement proper state management following our architecture
- Maximum line length: 100 characters

### Documentation Requirements

- All public functions/methods/classes must have docstrings/JSDoc comments
- Update relevant documentation when making code changes
- Document API endpoints with OpenAPI specification
- Include examples where appropriate
- Keep README files up-to-date

## Testing Requirements

Testing is a critical part of our development process. All contributions must include appropriate tests.

### Test Coverage

We maintain high code coverage requirements:

| Component | Statement Coverage | Branch Coverage | Function Coverage |
|-----------|-------------------|----------------|-------------------|
| Backend Core Services | 90% | 80% | 95% |
| Backend Utilities | 85% | 75% | 90% |
| Frontend Components | 85% | 75% | 90% |
| Frontend Utils | 90% | 80% | 95% |

Pull requests that decrease coverage will be rejected.

### Test Types

Depending on the changes, you should add:

- **Unit Tests**: Test individual functions and components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: For significant features, test complete user flows
- **API Tests**: For API changes, test request/response contracts

### Test Naming

- **Backend Tests**:
  - Test files: `test_[module_name].py`
  - Test functions: `test_[function_name]_[scenario]_[expected_result]`
  - Example: `test_create_task_with_valid_data_returns_created_task`

- **Frontend Tests**:
  - Test files: `[ComponentName].test.tsx`
  - Test descriptions: `should [expected behavior] when [condition]`
  - Example: `it('should display task details when task is provided')`

## Pull Request Process

### PR Creation

1. **Create your PR** targeting the appropriate branch (usually `develop`)
2. **Fill out the PR template** completely, including:
   - Clear description of changes
   - Related issues (use "Fixes #issue_number" to auto-close issues)
   - Type of change (feature, bugfix, etc.)
   - Testing instructions
   - Checklist of completed items
3. **Request reviewers** from the appropriate team
4. **Respond to feedback** promptly and make requested changes

Our PR template can be found [here](.github/pull_request_template.md).

### Automated Checks

All PRs go through automated checks in our CI/CD pipeline, including:

- **Validation**: PR format validation (title, linked issues, etc.)
- **Backend Checks**: Pylint, mypy, pytest with coverage, safety check
- **Frontend Checks**: ESLint, TypeScript compiler, Jest tests, npm audit
- **Security Scan**: CodeQL analysis, secret scanning, OWASP ZAP scan

If any checks fail, the PR cannot be merged until issues are fixed.

### Code Review

Code reviews are an essential part of our development process:

- At least one approval is required from the appropriate team
- Address all comments and suggestions
- Be open to feedback and constructive criticism
- Be responsive and collaborate with reviewers

### Merge Requirements

Before a PR can be merged, it must meet the following criteria:

- All CI checks must pass
- Required code review approvals obtained
- No unresolved conversations
- Up-to-date with the target branch
- All items in the PR checklist completed

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs. **actual behavior**
- **Screenshots** if applicable
- **Environment details** (browser, OS, app version)
- **Possible solution** if you have ideas

### Feature Requests

Feature requests should include:

- **Clear title** describing the feature
- **Problem statement** - what need does this feature address?
- **Proposed solution** - how would it work?
- **Alternatives considered** if applicable
- **User stories** or use cases
- **Acceptance criteria** - how would we know it's done?

### Issue Labels

We use a variety of labels to categorize issues:

- **Type**: `bug`, `enhancement`, `documentation`, etc.
- **Priority**: `priority-high`, `priority-medium`, `priority-low`
- **Status**: `in-progress`, `needs-review`, `blocked`, etc.
- **Component**: `frontend`, `backend`, `api`, `database`, etc.

## Security Considerations

### Security Testing

- Always validate inputs and sanitize outputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization checks
- Test for common vulnerabilities (OWASP Top 10)
- Run security scanning tools before submitting PRs

### Vulnerability Reporting

If you discover a security vulnerability, please DO NOT open a public issue. Instead, follow our [security vulnerability reporting process](SECURITY.md) which includes:

1. Emailing security-team@taskmanagement.example.com
2. Providing a detailed description of the vulnerability
3. Including steps to reproduce the issue
4. Maintaining confidentiality until the issue is resolved

### Security Best Practices

Follow these security practices in all contributions:

- Never hardcode credentials or sensitive data
- Use the system's authentication and permission frameworks
- Apply proper input validation and output encoding
- Follow the principle of least privilege
- Implement proper error handling without leaking sensitive information

For more details, refer to our [Security Policy](SECURITY.md).

## Community Practices

### Communication Channels

- **GitHub Issues**: For bug reports, feature requests, and task tracking
- **Pull Requests**: For code reviews and feedback on changes
- **Slack**: For real-time communication and quick questions
- **Email**: For longer discussions and formal communications
- **Team Meetings**: Regular video calls for planning and coordination

### Mentorship

We welcome contributors of all experience levels! If you're new to the project:

- Look for issues labeled `good-first-issue` or `beginner-friendly`
- Reach out in our Slack channel for help
- Request a mentor by commenting on an issue you're interested in
- Participate in pair programming sessions for knowledge sharing

### Recognition

We value all contributions to the project:

- All contributors are acknowledged in our release notes
- Significant contributions may be highlighted in our documentation
- Consistent contributors may be invited to join the core team
- We celebrate milestones and achievements as a community

## License Compliance

- Ensure all contributions are compatible with our project license
- Include appropriate copyright notices in new files
- Document the use of third-party libraries and their licenses
- Get approval before introducing new dependencies

---

Thank you for taking the time to contribute to the Task Management System! Your efforts help improve the project for everyone.