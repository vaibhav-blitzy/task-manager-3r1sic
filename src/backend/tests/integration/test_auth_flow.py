"""
Integration tests for authentication flows, testing the complete user authentication lifecycle
including registration, login, token refresh, and logout.
"""

import pytest
import requests
import json
import time
import re
import os


@pytest.fixture
def registered_user(base_url, test_client):
    """
    Creates a pre-registered user for testing duplicate registration.
    
    Returns:
        dict: Dictionary containing registered user details and credentials
    """
    # Generate user data with test email and password
    user_data = {
        "email": "registered@example.com",
        "password": "SecurePassword123!",
        "firstName": "Registered",
        "lastName": "User"
    }
    
    # Register user via API call
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    # Return user data dictionary
    return user_data


@pytest.fixture
def unverified_user(base_url, test_client):
    """
    Creates a test user with unverified email.
    
    Returns:
        dict: Dictionary containing unverified user details and credentials
    """
    # Generate unique user data
    user_data = {
        "email": f"unverified_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "firstName": "Unverified",
        "lastName": "User"
    }
    
    # Register user via API call
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    # Return user data dictionary without verifying email
    return user_data


@pytest.fixture
def verified_user(base_url, test_client, mock_email_service):
    """
    Creates a test user with verified email.
    
    Returns:
        dict: Dictionary containing verified user details and credentials
    """
    # Create unverified user
    user_data = {
        "email": f"verified_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "firstName": "Verified",
        "lastName": "User"
    }
    
    # Register user
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    # Extract verification token from mock_email_service
    verification_token = mock_email_service.get_verification_token(user_data["email"])
    
    # Call verification endpoint to verify email
    verify_response = test_client.get(
        f"{base_url}/auth/verify-email?token={verification_token}"
    )
    
    # Return user data dictionary with verified status
    return user_data


@pytest.fixture
def authenticated_user(base_url, test_client, verified_user):
    """
    Creates a test user and performs login to get authentication tokens.
    
    Returns:
        dict: Dictionary containing user details and authentication tokens
    """
    # Use verified_user fixture to get user credentials
    login_data = {
        "email": verified_user["email"],
        "password": verified_user["password"]
    }
    
    # Perform login API call to get tokens
    response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    # Get response data
    response_data = json.loads(response.data)
    
    # Return user data enriched with access and refresh tokens
    user_data = verified_user.copy()
    user_data["access_token"] = response_data.get("access_token")
    user_data["refresh_token"] = response_data.get("refresh_token")
    
    return user_data


@pytest.fixture
def mock_email_service():
    """
    Mocks the email service for verification and password reset flows.
    
    Returns:
        object: Mock email service object that captures sent emails
    """
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
            self.verification_tokens = {}
            self.reset_tokens = {}
        
        def send_email(self, to, subject, body):
            # Store the email
            self.sent_emails.append({
                "to": to,
                "subject": subject,
                "body": body
            })
            
            # Extract verification token if present
            if "verify" in subject.lower():
                token_match = re.search(r'token=([a-zA-Z0-9\-_]+)', body)
                if token_match:
                    self.verification_tokens[to] = token_match.group(1)
            
            # Extract password reset token if present
            if "reset" in subject.lower() or "password" in subject.lower():
                token_match = re.search(r'token=([a-zA-Z0-9\-_]+)', body)
                if token_match:
                    self.reset_tokens[to] = token_match.group(1)
        
        def get_verification_token(self, email):
            return self.verification_tokens.get(email)
        
        def get_reset_token(self, email):
            return self.reset_tokens.get(email)
    
    return MockEmailService()


@pytest.fixture
def mock_mfa_service():
    """
    Mocks the MFA service for testing MFA authentication flow.
    
    Returns:
        object: Mock MFA service object that generates predictable codes
    """
    class MockMFAService:
        def __init__(self):
            self.user_secrets = {}
            self.current_codes = {}
        
        def setup_mfa(self, user_id):
            # Create mock MFA secret
            self.user_secrets[user_id] = "TESTSECRET123456"
            return {
                "secret": self.user_secrets[user_id],
                "qr_code_url": "https://example.com/qrcode"
            }
        
        def generate_code(self, user_id):
            # Generate a predictable code for testing
            code = "123456"  # Fixed test code
            self.current_codes[user_id] = code
            return code
        
        def verify_code(self, user_id, code):
            return code == self.current_codes.get(user_id)
        
        def get_current_code(self, user_id):
            return self.current_codes.get(user_id, "123456")
    
    return MockMFAService()


def test_user_registration_success(base_url, test_client):
    """
    Tests successful user registration flow.
    """
    # Define test user data with valid email, password, and name
    user_data = {
        "email": f"test_user_{int(time.time())}@example.com",
        "password": "SecurePassword123!",
        "firstName": "Test",
        "lastName": "User"
    }
    
    # Send POST request to /auth/register endpoint
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    # Verify 201 status code in response
    assert response.status_code == 201
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify response contains user data and token
    assert "id" in response_data
    assert "email" in response_data
    assert response_data["email"] == user_data["email"]
    assert "firstName" in response_data
    assert response_data["firstName"] == user_data["firstName"]
    assert "lastName" in response_data
    assert response_data["lastName"] == user_data["lastName"]
    
    # Verify user email is marked as unverified
    assert "emailVerified" in response_data
    assert response_data["emailVerified"] is False
    
    # Verify response doesn't contain password
    assert "password" not in response_data


def test_user_registration_duplicate_email(base_url, test_client, registered_user):
    """
    Tests user registration with an email that already exists.
    """
    # Try to register with the same email as registered_user
    user_data = {
        "email": registered_user["email"],  # Using existing email
        "password": "DifferentPassword123!",
        "firstName": "Duplicate",
        "lastName": "User"
    }
    
    # Send request to register endpoint
    response = test_client.post(
        f"{base_url}/auth/register",
        json=user_data
    )
    
    # Verify 400 status code in response
    assert response.status_code == 400
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify error message indicates duplicate email
    assert "errors" in response_data
    assert "email" in response_data["errors"]
    assert any("already exists" in err.lower() for err in response_data["errors"]["email"])


def test_user_registration_invalid_data(base_url, test_client):
    """
    Tests user registration with invalid data.
    """
    # Test registration with invalid email format
    invalid_email_data = {
        "email": "not_an_email",
        "password": "SecurePassword123!",
        "firstName": "Test",
        "lastName": "User"
    }
    
    response = test_client.post(
        f"{base_url}/auth/register",
        json=invalid_email_data
    )
    
    # Verify 400 status code and appropriate error message
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "errors" in response_data
    assert "email" in response_data["errors"]
    
    # Test registration with short password
    weak_password_data = {
        "email": "test@example.com",
        "password": "weak",
        "firstName": "Test",
        "lastName": "User"
    }
    
    response = test_client.post(
        f"{base_url}/auth/register",
        json=weak_password_data
    )
    
    # Verify 400 status code and password requirements error
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "errors" in response_data
    assert "password" in response_data["errors"]
    
    # Test registration with missing required fields
    missing_fields_data = {
        "email": "test@example.com"
        # Missing password and firstName fields
    }
    
    response = test_client.post(
        f"{base_url}/auth/register",
        json=missing_fields_data
    )
    
    # Verify 400 status code and missing field errors
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "errors" in response_data
    assert "password" in response_data["errors"]


def test_email_verification_flow(base_url, test_client, unverified_user, mock_email_service):
    """
    Tests the email verification flow.
    """
    # Extract verification token from mock_email_service
    verification_token = mock_email_service.get_verification_token(unverified_user["email"])
    
    # Send GET request to /auth/verify-email with token
    response = test_client.get(
        f"{base_url}/auth/verify-email?token={verification_token}"
    )
    
    # Verify 200 status code in response
    assert response.status_code == 200
    
    # Login to get access token
    login_data = {
        "email": unverified_user["email"],
        "password": unverified_user["password"]
    }
    
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    login_data = json.loads(login_response.data)
    access_token = login_data.get("access_token")
    
    # Send GET request to get user profile
    profile_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    profile_data = json.loads(profile_response.data)
    
    # Verify user email is now marked as verified
    assert "emailVerified" in profile_data
    assert profile_data["emailVerified"] is True


def test_login_success(base_url, test_client, verified_user):
    """
    Tests successful login with valid credentials.
    """
    # Send POST request to /auth/login with valid email and password
    login_data = {
        "email": verified_user["email"],
        "password": verified_user["password"]
    }
    
    response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    # Verify 200 status code in response
    assert response.status_code == 200
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify response contains access token and refresh token
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    
    # Verify response contains user details
    assert "user" in response_data
    assert response_data["user"]["email"] == verified_user["email"]


def test_login_invalid_credentials(base_url, test_client, verified_user):
    """
    Tests login with invalid credentials.
    """
    # Send POST request to /auth/login with valid email but wrong password
    wrong_password_data = {
        "email": verified_user["email"],
        "password": "WrongPassword123!"
    }
    
    response = test_client.post(
        f"{base_url}/auth/login",
        json=wrong_password_data
    )
    
    # Verify 401 status code in response
    assert response.status_code == 401
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify error message indicates invalid credentials
    assert "invalid credentials" in response_data.get("message", "").lower()
    
    # Send POST request to /auth/login with non-existent email
    nonexistent_email_data = {
        "email": "nonexistent@example.com",
        "password": "SecurePassword123!"
    }
    
    response = test_client.post(
        f"{base_url}/auth/login",
        json=nonexistent_email_data
    )
    
    # Verify 401 status code in response
    assert response.status_code == 401
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify error message indicates invalid credentials
    assert "invalid credentials" in response_data.get("message", "").lower()


def test_login_unverified_user(base_url, test_client, unverified_user):
    """
    Tests login with unverified user account.
    """
    # Send POST request to /auth/login with unverified user credentials
    login_data = {
        "email": unverified_user["email"],
        "password": unverified_user["password"]
    }
    
    response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify response indicates email verification required
    assert any([
        "verification_required" in response_data,
        ("emailVerified" in response_data and not response_data["emailVerified"]),
        ("message" in response_data and "verify" in response_data["message"].lower()),
        ("message" in response_data and "verification" in response_data["message"].lower())
    ])
    
    # Verify no access token is provided
    assert "access_token" not in response_data


def test_password_reset_flow(base_url, test_client, verified_user, mock_email_service):
    """
    Tests the password reset flow from request to reset completion.
    """
    # Send POST request to /auth/password/reset with user email
    reset_request_data = {
        "email": verified_user["email"]
    }
    
    reset_response = test_client.post(
        f"{base_url}/auth/password/reset",
        json=reset_request_data
    )
    
    # Verify 200 status code in response
    assert reset_response.status_code == 200
    
    # Extract reset token from mock_email_service
    reset_token = mock_email_service.get_reset_token(verified_user["email"])
    
    # Send POST request to /auth/password/change with token and new password
    new_password = "NewSecurePassword123!"
    reset_password_data = {
        "token": reset_token,
        "password": new_password
    }
    
    reset_password_response = test_client.post(
        f"{base_url}/auth/password/change",
        json=reset_password_data
    )
    
    # Verify 200 status code in response
    assert reset_password_response.status_code == 200
    
    # Login with new password to verify password was changed
    login_data = {
        "email": verified_user["email"],
        "password": new_password
    }
    
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    # Verify 200 status code in login response
    assert login_response.status_code == 200


def test_token_refresh(base_url, test_client, authenticated_user):
    """
    Tests refreshing access token using refresh token.
    """
    # Extract refresh token from authenticated_user fixture
    refresh_token = authenticated_user["refresh_token"]
    
    # Send POST request to /auth/token/refresh with refresh token
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    response = test_client.post(
        f"{base_url}/auth/token/refresh",
        json=refresh_data
    )
    
    # Verify 200 status code in response
    assert response.status_code == 200
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify response contains new access token
    assert "access_token" in response_data
    
    # Use new access token to access a protected endpoint
    new_access_token = response_data["access_token"]
    
    profile_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    # Verify protected endpoint access is successful
    assert profile_response.status_code == 200


def test_token_refresh_invalid_token(base_url, test_client):
    """
    Tests refreshing access token with invalid refresh token.
    """
    # Send POST request to /auth/token/refresh with invalid refresh token
    refresh_data = {
        "refresh_token": "invalid_token"
    }
    
    response = test_client.post(
        f"{base_url}/auth/token/refresh",
        json=refresh_data
    )
    
    # Verify 401 status code in response
    assert response.status_code == 401
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify error message indicates invalid token
    assert "invalid" in response_data.get("message", "").lower()


def test_logout(base_url, test_client, authenticated_user):
    """
    Tests user logout functionality.
    """
    # Send POST request to /auth/logout with valid access token
    access_token = authenticated_user["access_token"]
    
    response = test_client.post(
        f"{base_url}/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify 200 status code in response
    assert response.status_code == 200
    
    # Try to use the same access token to access a protected endpoint
    profile_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify 401 status code indicating token is no longer valid
    assert profile_response.status_code == 401


def test_access_protected_endpoint(base_url, test_client, authenticated_user):
    """
    Tests accessing a protected endpoint with valid and invalid tokens.
    """
    # Access a protected endpoint (e.g., /users/profile) with valid token
    access_token = authenticated_user["access_token"]
    
    profile_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify 200 status code in response
    assert profile_response.status_code == 200
    
    # Access the same endpoint without a token
    no_token_response = test_client.get(f"{base_url}/users/profile")
    
    # Verify 401 status code in response
    assert no_token_response.status_code == 401
    
    # Access the same endpoint with expired or invalid token
    invalid_token_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    # Verify 401 status code in response
    assert invalid_token_response.status_code == 401


@pytest.mark.skipif(not os.getenv('ENABLE_MFA'), reason='MFA not enabled')
def test_mfa_flow(base_url, test_client, verified_user, mock_mfa_service):
    """
    Tests multi-factor authentication flow if enabled.
    """
    # Enable MFA for the verified user
    login_data = {
        "email": verified_user["email"],
        "password": verified_user["password"]
    }
    
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    login_data = json.loads(login_response.data)
    access_token = login_data["access_token"]
    
    # Setup MFA for the user
    mfa_setup_response = test_client.post(
        f"{base_url}/auth/mfa/setup",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert mfa_setup_response.status_code == 200
    
    # Get MFA code from mock_mfa_service
    mfa_code = mock_mfa_service.get_current_code(verified_user["email"])
    
    # Send MFA code to /auth/mfa/verify
    mfa_verify_data = {
        "code": mfa_code,
        "user_id": verified_user["email"]
    }
    
    mfa_verify_response = test_client.post(
        f"{base_url}/auth/mfa/verify",
        json=mfa_verify_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert mfa_verify_response.status_code == 200
    
    # Login again, should require MFA verification
    login_response = test_client.post(
        f"{base_url}/auth/login",
        json=login_data
    )
    
    login_result = json.loads(login_response.data)
    
    # Verify response indicates MFA verification required
    assert "mfa_required" in login_result
    assert login_result["mfa_required"] is True
    
    # Complete MFA verification
    mfa_verification_data = {
        "code": mock_mfa_service.get_current_code(verified_user["email"]),
        "mfa_token": login_result.get("mfa_token")
    }
    
    mfa_completion_response = test_client.post(
        f"{base_url}/auth/mfa/verify",
        json=mfa_verification_data
    )
    
    assert mfa_completion_response.status_code == 200
    
    mfa_result = json.loads(mfa_completion_response.data)
    
    # Verify can access protected endpoints with the token
    assert "access_token" in mfa_result
    
    profile_response = test_client.get(
        f"{base_url}/users/profile",
        headers={"Authorization": f"Bearer {mfa_result['access_token']}"}
    )
    
    assert profile_response.status_code == 200