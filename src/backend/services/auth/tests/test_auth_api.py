# pytest v7.4.x
import pytest
# json standard library
import json
# datetime standard library
import datetime

# Internal imports for authentication API blueprint and user model
from src.backend.services.auth.api.auth import auth_bp
from src.backend.services.auth.models.user import get_user_by_email, User
# Token validation utility
from src.backend.common.auth.jwt_utils import validate_token

@pytest.fixture
def test_register_success(client, mock_db):
    """Tests successful user registration with valid data"""
    # Prepare valid user data with email, password, firstName, lastName
    user_data = {
        "email": "test@example.com",
        "password": "Password123!",
        "firstName": "Test",
        "lastName": "User"
    }
    # Make POST request to /auth/register with valid data
    response = client.post("/auth/register", json=user_data)
    # Assert response status code is 201 Created
    assert response.status_code == 201
    # Assert response contains success message
    assert response.json["message"] == "User registered successfully. Please check your email to verify your account."
    # Verify user was actually created in the database
    user = get_user_by_email("test@example.com")
    assert user is not None
    # Verify password was properly hashed
    assert user.check_password("Password123!")
    # Verify email verification token was generated
    assert user._data.get("verification_token") is not None

@pytest.fixture
def test_register_duplicate_email(client, test_user):
    """Tests registration failure when email already exists"""
    # Prepare user data with same email as existing test_user
    user_data = {
        "email": test_user["email"],
        "password": "Password123!",
        "firstName": "Test",
        "lastName": "User"
    }
    # Make POST request to /auth/register with duplicate email
    response = client.post("/auth/register", json=user_data)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains error message about duplicate email
    assert response.json["message"] == "User with this email already exists"

@pytest.fixture
def test_register_invalid_data(client):
    """Tests registration validation for invalid data"""
    # Test case 1: Missing required fields
    missing_data = {
        "firstName": "Test",
        "lastName": "User"
    }
    # For each case, make POST request to /auth/register
    response = client.post("/auth/register", json=missing_data)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate validation error message
    assert "Missing required fields" in response.json["message"]

    # Test case 2: Invalid email format
    invalid_email = {
        "email": "invalid-email",
        "password": "Password123!",
        "firstName": "Test",
        "lastName": "User"
    }
    # For each case, make POST request to /auth/register
    response = client.post("/auth/register", json=invalid_email)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate validation error message
    assert "Invalid email format" in response.json["message"]

    # Test case 3: Weak password
    weak_password = {
        "email": "test@example.com",
        "password": "weak",
        "firstName": "Test",
        "lastName": "User"
    }
    # For each case, make POST request to /auth/register
    response = client.post("/auth/register", json=weak_password)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate validation error message
    assert "Password must be at least 8 characters long" in response.json["message"]

@pytest.fixture
def test_login_success(client, test_user):
    """Tests successful login with valid credentials"""
    # Prepare login data with test user email and password
    login_data = {
        "email": test_user["email"],
        "password": "Password123!"
    }
    # Make POST request to /auth/login with valid credentials
    response = client.post("/auth/login", json=login_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains access_token and refresh_token
    assert "access_token" in response.json
    assert "refresh_token" in response.json
    # Assert response contains user data (id, email, roles)
    assert "user" in response.json
    assert response.json["user"]["email"] == test_user["email"]
    assert "roles" in response.json["user"]
    # Verify tokens are valid using validate_token function
    validate_token(response.json["access_token"])
    validate_token(response.json["refresh_token"])

@pytest.fixture
def test_login_invalid_credentials(client, test_user):
    """Tests login failure with invalid credentials"""
    # Test case 1: Invalid email
    invalid_email = {
        "email": "invalid@example.com",
        "password": "Password123!"
    }
    # For each case, make POST request to /auth/login
    response = client.post("/auth/login", json=invalid_email)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains appropriate error message
    assert "Invalid credentials" in response.json["message"]

    # Test case 2: Invalid password
    invalid_password = {
        "email": test_user["email"],
        "password": "wrongpassword"
    }
    # For each case, make POST request to /auth/login
    response = client.post("/auth/login", json=invalid_password)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains appropriate error message
    assert "Invalid credentials" in response.json["message"]

@pytest.fixture
def test_login_account_locked(client, test_user, mock_db):
    """Tests login failure when account is locked due to too many failed attempts"""
    # Update test user in database to set failed_attempts to max, account_locked to True
    user = get_user_by_email(test_user["email"])
    user._data["failed_attempts"] = 5
    user._data["account_locked"] = True
    # Set locked_until to future datetime
    user._data["locked_until"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    user.save()
    # Make POST request to /auth/login with valid credentials
    login_data = {
        "email": test_user["email"],
        "password": "Password123!"
    }
    response = client.post("/auth/login", json=login_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains message about account being locked
    assert "Account is temporarily locked" in response.json["message"]

@pytest.fixture
def test_login_unverified_email(client, test_user, mock_db):
    """Tests login behavior with unverified email"""
    # Update test user in database to set email_verified to False
    user = get_user_by_email(test_user["email"])
    user._data["email_verified"] = False
    user.save()
    # Make POST request to /auth/login with valid credentials
    login_data = {
        "email": test_user["email"],
        "password": "Password123!"
    }
    response = client.post("/auth/login", json=login_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains message about unverified email
    assert "Email verification required" in response.json["message"]

@pytest.fixture
def test_login_with_mfa(client, test_user, mock_db, mock_redis):
    """Tests login with MFA enabled"""
    # Update test user in database to set mfa_enabled to True
    user = get_user_by_email(test_user["email"])
    user._data["mfa_enabled"] = True
    # Set mfa_method to 'totp' and appropriate mfa_config
    user._data["mfa_method"] = "totp"
    user._data["mfa_secret"] = "JBSWY3DPEHPKDDAPTJGE"
    user.save()
    # Make POST request to /auth/login with valid credentials
    login_data = {
        "email": test_user["email"],
        "password": "Password123!"
    }
    response = client.post("/auth/login", json=login_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains mfa_required: True
    assert response.json["mfa_required"] == True
    # Assert response contains mfa_token for verification step
    assert "mfa_token" in response.json
    # Verify MFA token was stored in Redis with correct user_id
    mfa_token_key = f"mfa_token:{user.get_id()}"
    assert mock_redis.get(mfa_token_key) is not None

@pytest.fixture
def test_verify_mfa(client, test_user, mock_redis):
    """Tests MFA verification during login process"""
    # Set up Redis with valid MFA challenge token for test user
    user = get_user_by_email(test_user["email"])
    mfa_token = "test_mfa_token"
    mock_redis.set(f"mfa_token:{user.get_id()}", mfa_token)
    # Prepare MFA verification data with code and token
    verification_data = {
        "mfa_code": "123456",
        "mfa_token": mfa_token,
        "user_id": str(user.get_id())
    }
    # Mock User.verify_mfa to return True
    User.verify_mfa = lambda self, code: True
    # Make POST request to /auth/mfa/verify with verification data
    response = client.post("/auth/mfa/verify", json=verification_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains access_token and refresh_token
    assert "access_token" in response.json
    assert "refresh_token" in response.json
    # Assert response contains user data
    assert "user" in response.json
    # Verify MFA token was removed from Redis
    mfa_token_key = f"mfa_token:{user.get_id()}"
    assert mock_redis.get(mfa_token_key) is None

@pytest.fixture
def test_verify_mfa_invalid(client, mock_redis):
    """Tests MFA verification failure with invalid data"""
    # Test case 1: Invalid MFA token
    invalid_token_data = {
        "mfa_code": "123456",
        "mfa_token": "invalid_token",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/mfa/verify
    response = client.post("/auth/mfa/verify", json=invalid_token_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains appropriate error message
    assert "Invalid MFA token" in response.json["message"]

    # Test case 2: Expired MFA token
    expired_token_data = {
        "mfa_code": "123456",
        "mfa_token": "expired_token",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/mfa/verify
    response = client.post("/auth/mfa/verify", json=expired_token_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains appropriate error message
    assert "Invalid MFA token" in response.json["message"]

    # Test case 3: Invalid MFA code
    invalid_code_data = {
        "mfa_code": "000000",
        "mfa_token": "valid_token",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/mfa/verify
    response = client.post("/auth/mfa/verify", json=invalid_code_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains appropriate error message
    assert "Invalid MFA code" in response.json["message"]

@pytest.fixture
def test_verify_email(client, test_user, mock_db):
    """Tests successful email verification"""
    # Set up test user with verification token data
    user = get_user_by_email(test_user["email"])
    verification_token = "test_verification_token"
    user._data["verification_token"] = verification_token
    user._data["verification_token_expiry"] = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    user.save()
    # Mock User.verify_email to return True for the token
    User.verify_email = lambda self, token: True if token == verification_token else False
    # Make GET request to /auth/verify-email with token
    response = client.get(f"/auth/verify-email?token={verification_token}&user_id={str(user.get_id())}")
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains success message
    assert response.json["message"] == "Email verified successfully"
    # Verify user's email_verified flag is set to True in database
    updated_user = get_user_by_email(test_user["email"])
    assert updated_user._data["email_verified"] == True

@pytest.fixture
def test_verify_email_invalid(client):
    """Tests email verification failure with invalid token"""
    # Make GET request to /auth/verify-email with invalid token
    response = client.get("/auth/verify-email?token=invalid_token&user_id=invalid_user_id")
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains error message about invalid token
    assert "Email verification failed" in response.json["message"]

@pytest.fixture
def test_refresh_token(client, test_user_tokens):
    """Tests refreshing access token with valid refresh token"""
    # Prepare request data with refresh token
    refresh_data = {
        "refresh_token": test_user_tokens["refresh_token"]
    }
    # Make POST request to /auth/token/refresh
    response = client.post("/auth/token/refresh", json=refresh_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains new access_token
    assert "access_token" in response.json
    # Verify new token is valid using validate_token function
    validate_token(response.json["access_token"])

@pytest.fixture
def test_refresh_token_invalid(client):
    """Tests token refresh failure with invalid refresh token"""
    # Prepare request data with invalid refresh token
    refresh_data = {
        "refresh_token": "invalid_refresh_token"
    }
    # Make POST request to /auth/token/refresh
    response = client.post("/auth/token/refresh", json=refresh_data)
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains error message about invalid token
    assert "Invalid token" in response.json["message"]

@pytest.fixture
def test_logout(client, authenticated_client, test_user_tokens, mock_redis):
    """Tests successful logout"""
    # Prepare request data with refresh token
    logout_data = {
        "refresh_token": test_user_tokens["refresh_token"]
    }
    # Make POST request to /auth/logout with authenticated client
    response = authenticated_client.post("/auth/logout", json=logout_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains success message
    assert response.json["message"] == "Logged out successfully"
    # Verify tokens are blacklisted in Redis
    access_token = test_user_tokens["access_token"]
    refresh_token = test_user_tokens["refresh_token"]
    # Verify using blacklisted token returns 401 Unauthorized
    headers = {"Authorization": f"Bearer {access_token}"}
    status_response = client.get("/auth/status", headers=headers)
    assert status_response.status_code == 401

@pytest.fixture
def test_request_password_reset(client, test_user):
    """Tests password reset request process"""
    # Prepare request data with user email
    reset_data = {
        "email": test_user["email"]
    }
    # Make POST request to /auth/password/reset
    response = client.post("/auth/password/reset", json=reset_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains success message
    assert response.json["message"] == "Password reset email sent if account exists"
    # For security, verify same response even for non-existent email
    nonexistent_data = {
        "email": "nonexistent@example.com"
    }
    response = client.post("/auth/password/reset", json=nonexistent_data)
    assert response.status_code == 200
    assert response.json["message"] == "Password reset email sent if account exists"

@pytest.fixture
def test_reset_password(client, test_user, mock_db):
    """Tests resetting password with valid token"""
    # Set up test user with reset token data
    user = get_user_by_email(test_user["email"])
    reset_token = "test_reset_token"
    user._data["reset_token"] = reset_token
    user._data["reset_token_expiry"] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    user.save()
    # Prepare request data with token and new password
    reset_data = {
        "token": reset_token,
        "new_password": "NewPassword123!",
        "user_id": str(user.get_id())
    }
    # Make POST request to /auth/password/change
    response = client.post("/auth/password/change", json=reset_data)
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains success message
    assert response.json["message"] == "Password reset successfully"
    # Verify user's password was updated in database
    updated_user = get_user_by_email(test_user["email"])
    assert updated_user.check_password("NewPassword123!")
    # Verify user can login with new password
    login_data = {
        "email": test_user["email"],
        "password": "NewPassword123!"
    }
    login_response = client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200

@pytest.fixture
def test_reset_password_invalid(client):
    """Tests password reset failure with invalid data"""
    # Test case 1: Invalid reset token
    invalid_token_data = {
        "token": "invalid_token",
        "new_password": "NewPassword123!",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/password/change
    response = client.post("/auth/password/change", json=invalid_token_data)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate error message
    assert "Invalid reset token" in response.json["message"]

    # Test case 2: Expired reset token
    expired_token_data = {
        "token": "expired_token",
        "new_password": "NewPassword123!",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/password/change
    response = client.post("/auth/password/change", json=expired_token_data)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate error message
    assert "Invalid reset token" in response.json["message"]

    # Test case 3: Weak new password
    weak_password_data = {
        "token": "valid_token",
        "new_password": "weak",
        "user_id": "test_user_id"
    }
    # For each case, make POST request to /auth/password/change
    response = client.post("/auth/password/change", json=weak_password_data)
    # Assert response status code is 400 Bad Request
    assert response.status_code == 400
    # Assert response contains appropriate error message
    assert "Password must be at least 8 characters long" in response.json["message"]

@pytest.fixture
def test_status_authenticated(client, authenticated_client, test_user):
    """Tests authentication status endpoint with valid token"""
    # Make GET request to /auth/status with authenticated client
    response = authenticated_client.get("/auth/status")
    # Assert response status code is 200 OK
    assert response.status_code == 200
    # Assert response contains user data matching test_user
    assert "user" in response.json
    assert response.json["user"]["email"] == test_user["email"]
    # Verify response includes roles and other non-sensitive user data
    assert "roles" in response.json["user"]
    assert "firstName" in response.json["user"]
    assert "lastName" in response.json["user"]

@pytest.fixture
def test_status_unauthenticated(client):
    """Tests authentication status endpoint without valid token"""
    # Make GET request to /auth/status without authentication
    response = client.get("/auth/status")
    # Assert response status code is 401 Unauthorized
    assert response.status_code == 401
    # Assert response contains error message about missing or invalid token
    assert "Missing token" in response.json["message"]