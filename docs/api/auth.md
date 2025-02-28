# Authentication API

The Authentication API provides endpoints for user registration, authentication, token management, and account security. It implements JSON Web Token (JWT) based authentication with refresh token rotation and multi-factor authentication support.

## Base URL

All authentication endpoints are relative to: `/api/v1/auth`

## Authentication Methods

The Task Management System supports the following authentication methods:

| Method | Description | Usage |
|--------|-------------|-------|
| JWT Authentication | Standard authentication method using JSON Web Tokens (JWT) with access and refresh tokens | Most API endpoints require a valid JWT token provided in the Authorization header: `Authorization: Bearer {access_token}` |
| OAuth 2.0 | Authentication for third-party applications using the Authorization Code flow with PKCE | Used for integrating third-party applications |
| API Keys | For service-to-service communication using UUID-based API keys | API keys are provided in the X-API-Key header: `X-API-Key: {api_key}` |

## Authentication Flow

The standard authentication flow follows these steps:

1. User registers an account or logs in with credentials
2. System validates credentials and issues JWT access and refresh tokens
3. If MFA is enabled, user must provide a verification code before receiving tokens
4. Client includes access token in Authorization header for protected API requests
5. When access token expires, client uses refresh token to obtain a new access token
6. On logout, both access and refresh tokens are invalidated

## Token Management

The Authentication API uses a token-based authentication system with:

### Access Token
- Short-lived JWT token (15 minutes) used for authenticating API requests
- Format: JWT signed with RS256
- Usage: Include in Authorization header: `Authorization: Bearer {access_token}`

### Refresh Token
- Longer-lived token (7 days) used to obtain new access tokens without re-authentication
- Format: JWT signed with RS256
- Usage: Send to token refresh endpoint to obtain new access token
- Security: Implements token rotation for enhanced security

## Endpoints

### Register

Creates a new user account and initiates email verification.

- **URL**: `/register`
- **Method**: `POST`
- **Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "firstName": "John",
  "lastName": "Doe"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| email | string | User's email address | Yes |
| password | string | User's password (min 8 chars, must include uppercase, lowercase, number, and symbol) | Yes |
| firstName | string | User's first name | Yes |
| lastName | string | User's last name | Yes |

**Responses**:

`201 Created` - User successfully registered

```json
{
  "user": {
    "id": "60d21b4667d0d8992e610c85",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "emailVerified": false,
    "roles": ["user"]
  },
  "message": "Registration successful. Please verify your email."
}
```

`400 Bad Request` - Invalid registration data

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Registration data validation failed",
    "details": {
      "email": ["Email address is already in use"],
      "password": ["Password does not meet complexity requirements"]
    }
  }
}
```

### Login

Authenticates a user and returns access and refresh tokens.

- **URL**: `/login`
- **Method**: `POST`
- **Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "rememberMe": true
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| email | string | User's email address | Yes |
| password | string | User's password | Yes |
| rememberMe | boolean | Extends refresh token validity if true | No |

**Responses**:

`200 OK` - Authentication successful

```json
{
  "user": {
    "id": "60d21b4667d0d8992e610c85",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "roles": ["user"]
  },
  "tokens": {
    "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": 1623456789000
  },
  "mfaRequired": false
}
```

`200 OK` - Authentication successful but MFA required

```json
{
  "user": {
    "id": "60d21b4667d0d8992e610c85",
    "email": "user@example.com"
  },
  "mfaRequired": true,
  "mfaToken": "mfa_token_123456789",
  "mfaMethods": ["totp", "email"]
}
```

`401 Unauthorized` - Authentication failed

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

`403 Forbidden` - Account locked due to too many failed attempts

```json
{
  "error": {
    "code": "ACCOUNT_LOCKED",
    "message": "Account temporarily locked due to too many failed attempts",
    "details": {
      "lockedUntil": 1623456789000
    }
  }
}
```

### MFA Verification

Verifies MFA code and completes authentication.

- **URL**: `/mfa/verify`
- **Method**: `POST`
- **Authentication**: None required, but requires MFA token from login response

**Request Body**:
```json
{
  "mfaToken": "mfa_token_123456789",
  "code": "123456",
  "method": "totp"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| mfaToken | string | MFA token from login response | Yes |
| code | string | Verification code | Yes |
| method | string | MFA method (totp, sms, email) | Yes |

**Responses**:

`200 OK` - MFA verification successful

```json
{
  "user": {
    "id": "60d21b4667d0d8992e610c85",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "roles": ["user"]
  },
  "tokens": {
    "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresAt": 1623456789000
  }
}
```

`401 Unauthorized` - MFA verification failed

```json
{
  "error": {
    "code": "INVALID_MFA_CODE",
    "message": "Invalid or expired MFA code"
  }
}
```

### Verify Email

Verifies user's email using the token sent during registration.

- **URL**: `/verify-email`
- **Method**: `GET`
- **Authentication**: None required

**Query Parameters**:

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| token | string | Email verification token | Yes |

**Responses**:

`200 OK` - Email verification successful

```json
{
  "success": true,
  "message": "Email verification successful"
}
```

`400 Bad Request` - Invalid or expired verification token

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired verification token"
  }
}
```

### Refresh Token

Refreshes access token using a valid refresh token.

- **URL**: `/token/refresh`
- **Method**: `POST`
- **Authentication**: None required, but requires valid refresh token

**Request Body**:
```json
{
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| refreshToken | string | Valid refresh token | Yes |

**Responses**:

`200 OK` - Token refresh successful

```json
{
  "accessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresAt": 1623456789000
}
```

`401 Unauthorized` - Invalid or expired refresh token

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired refresh token"
  }
}
```

### Logout

Invalidates the current user's session by blacklisting their tokens.

- **URL**: `/logout`
- **Method**: `POST`
- **Authentication**: Bearer token required

**Request Body**:
```json
{
  "refreshToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| refreshToken | string | Refresh token to invalidate | No |

**Responses**:

`200 OK` - Logout successful

```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Request Password Reset

Initiates the password reset process by sending a reset email.

- **URL**: `/password/reset`
- **Method**: `POST`
- **Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| email | string | User's email address | Yes |

**Responses**:

`200 OK` - Password reset request successful

```json
{
  "success": true,
  "message": "Password reset instructions sent to your email"
}
```

> Note: Always returns 200 OK for security reasons, even if email doesn't exist

### Reset Password

Completes the password reset process using token and new password.

- **URL**: `/password/change`
- **Method**: `POST`
- **Authentication**: None required, but requires valid reset token

**Request Body**:
```json
{
  "token": "reset_token_123456789",
  "newPassword": "NewSecureP@ss123",
  "confirmPassword": "NewSecureP@ss123"
}
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| token | string | Password reset token | Yes |
| newPassword | string | New password (must meet complexity requirements) | Yes |
| confirmPassword | string | Confirmation of new password | Yes |

**Responses**:

`200 OK` - Password reset successful

```json
{
  "success": true,
  "message": "Password has been reset successfully"
}
```

`400 Bad Request` - Invalid token or password mismatch

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password reset validation failed",
    "details": {
      "token": ["Invalid or expired token"],
      "newPassword": ["Password does not meet complexity requirements"],
      "confirmPassword": ["Passwords do not match"]
    }
  }
}
```

### Authentication Status

Checks current authentication status and returns user information.

- **URL**: `/status`
- **Method**: `GET`
- **Authentication**: Bearer token required

**Responses**:

`200 OK` - User is authenticated

```json
{
  "user": {
    "id": "60d21b4667d0d8992e610c85",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "roles": ["user"]
  }
}
```

`401 Unauthorized` - User is not authenticated

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

## Security Considerations

When implementing authentication with the Task Management System API, consider the following security practices:

- Always use HTTPS for all API requests to protect credentials and tokens
- Store refresh tokens securely (HttpOnly cookies in web applications, secure storage in mobile apps)
- Never store access tokens in local storage or session storage due to XSS vulnerabilities
- Implement token refresh logic that handles expiration gracefully
- Logout users from all devices when password changes and on suspicious activity
- Set appropriate Content Security Policy (CSP) headers to mitigate XSS risks
- Follow the principle of least privilege when requesting permissions
- Implement rate limiting to prevent brute force attacks

## Error Handling

Authentication-specific error codes include:

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| INVALID_CREDENTIALS | Email and password combination is incorrect | 401 |
| ACCOUNT_LOCKED | Account temporarily locked due to too many failed attempts | 403 |
| EMAIL_NOT_VERIFIED | Email verification required before login | 403 |
| INVALID_TOKEN | Token is invalid, expired, or has been revoked | 401 |
| TOKEN_EXPIRED | Token has expired and needs to be refreshed | 401 |
| INVALID_MFA_CODE | Multi-factor authentication code is invalid or expired | 401 |
| EMAIL_IN_USE | Email address is already registered | 400 |
| PASSWORD_COMPLEXITY | Password does not meet complexity requirements | 400 |
| PASSWORDS_DONT_MATCH | Password and confirmation do not match | 400 |

## OAuth 2.0 Integration

For third-party application integration, the Task Management System supports OAuth 2.0 with the following endpoints:

| Endpoint | Path | Method | Description |
|----------|------|--------|-------------|
| Authorization Endpoint | `/oauth/authorize` | GET | Initiates the OAuth 2.0 authorization flow |
| Token Endpoint | `/oauth/token` | POST | Exchanges authorization code for access and refresh tokens |
| Token Revocation | `/oauth/revoke` | POST | Revokes an issued token |

> Detailed OAuth 2.0 integration documentation is available in the Developer Portal

## Rate Limiting

Authentication endpoints are rate-limited to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| `/login`, `/register` | 10 requests per minute per IP address |
| `/password/reset` | 5 requests per hour per email address |
| `/mfa/verify` | 10 attempts per token |
| `/token/refresh` | 30 requests per minute per user |

> When rate limits are exceeded, the API returns a 429 Too Many Requests response with Retry-After header

## Examples

### User Registration

```javascript
fetch('https://api.taskmanagementsystem.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecureP@ss123',
    firstName: 'John',
    lastName: 'Doe'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### User Login

```javascript
fetch('https://api.taskmanagementsystem.com/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecureP@ss123'
  })
})
.then(response => response.json())
.then(data => {
  // Store tokens securely
  localStorage.setItem('accessToken', data.tokens.accessToken);
  // Handle MFA if required
  if (data.mfaRequired) {
    // Redirect to MFA verification
  }
})
.catch(error => console.error('Error:', error));
```

### Token Refresh

```javascript
fetch('https://api.taskmanagementsystem.com/api/v1/auth/token/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    refreshToken: 'your-refresh-token'
  })
})
.then(response => response.json())
.then(data => {
  // Update stored tokens
  localStorage.setItem('accessToken', data.accessToken);
})
.catch(error => console.error('Error:', error));
```

### Making Authenticated Requests

```javascript
fetch('https://api.taskmanagementsystem.com/api/v1/tasks', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
  }
})
.then(response => {
  if (response.status === 401) {
    // Token expired, refresh token
  }
  return response.json();
})
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```