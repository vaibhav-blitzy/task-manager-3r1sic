# flask v3.0.0
from flask import Blueprint, request, jsonify
# datetime standard library
import datetime
# uuid standard library
import uuid

# Internal imports for authentication logic
from ..services import auth_service, user_service
from src.backend.common.auth.jwt_utils import create_access_token, create_refresh_token, decode_token
from src.backend.common.auth.decorators import token_required
from src.backend.common.database.redis.connection import get_redis_connection
from src.backend.common.events.event_bus import publish_event
from src.backend.common.exceptions.api_exceptions import UnauthorizedException, BadRequestException, NotFoundException
from src.backend.common.utils.validators import validate_email, validate_password

# Blueprint for authentication API routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user with email, password, and name. Sends a verification email.
    """
    try:
        # Extract registration data (email, password, name) from request JSON
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        firstName = data.get('firstName')
        lastName = data.get('lastName')

        # Validate email format and password strength
        validate_email(email)
        validate_password(password)

        # Call auth_service.register_user with validated data
        user_data = auth_service.register_user({'email': email, 'password': password, 'firstName': firstName, 'lastName': lastName})

        # Publish user.registered event to event bus
        publish_event('user.registered', {'user_id': str(user_data['user_id']), 'email': email})

        # Return success response with status 201
        return jsonify({'message': 'User registered successfully. Please check your email to verify your account.'}), 201
    except BadRequestException as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user with email and password, returning JWT tokens for successful login.
    """
    try:
        # Extract login credentials (email, password) from request JSON
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Call auth_service.login_user to authenticate
        auth_result = auth_service.login(email, password)

        if 'mfa_required' in auth_result and auth_result['mfa_required']:
            # If MFA is required, return MFA challenge response
            return jsonify({'mfa_required': True, 'mfa_token': auth_result['mfa_token'], 'user_id': auth_result['user_id']}), 200
        else:
            # If authentication successful, generate access and refresh tokens
            access_token = auth_result['access_token']
            refresh_token = auth_result['refresh_token']
            user = auth_result['user']

            # Publish user.login event to event bus
            publish_event('user.login', {'user_id': str(user['id']), 'email': user['email']})

            # Return tokens with user information
            return jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'user': user}), 200
    except UnauthorizedException as e:
        return jsonify({'message': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'Login failed'}), 500

@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """
    Verify user's email address using the token sent during registration.
    """
    try:
        # Extract verification token from query parameter
        token = request.args.get('token')
        user_id = request.args.get('user_id')

        # Call auth_service.verify_email with token
        if auth_service.verify_email(user_id, token):
            # Publish user.verified event to event bus
            publish_event('user.verified', {'user_id': user_id})

            # Return success response
            return jsonify({'message': 'Email verified successfully'}), 200
        else:
            return jsonify({'message': 'Email verification failed'}), 400
    except Exception as e:
        return jsonify({'message': 'Email verification failed'}), 500

@auth_bp.route('/mfa/verify', methods=['POST'])
def verify_mfa():
    """
    Verify multi-factor authentication code during login process.
    """
    try:
        # Extract MFA code and challenge ID from request JSON
        data = request.get_json()
        mfa_code = data.get('mfa_code')
        mfa_token = data.get('mfa_token')
        user_id = data.get('user_id')

        # Call auth_service.verify_mfa with code and challenge ID
        auth_result = auth_service.verify_mfa(user_id, mfa_code, mfa_token)

        # If verification successful, generate access and refresh tokens
        access_token = auth_result['access_token']
        refresh_token = auth_result['refresh_token']
        user = auth_result['user']

        # Publish user.login.mfa event to event bus
        publish_event('user.login.mfa', {'user_id': str(user['id']), 'email': user['email']})

        # Return tokens with user information
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'user': user}), 200
    except UnauthorizedException as e:
        return jsonify({'message': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'MFA verification failed'}), 500

@auth_bp.route('/token/refresh', methods=['POST'])
def refresh_token():
    """
    Generate new access token using a valid refresh token.
    """
    try:
        # Extract refresh token from request JSON
        data = request.get_json()
        refresh_token = data.get('refresh_token')

        # Call auth_service.refresh_auth_token with refresh token
        new_tokens = auth_service.refresh_token(refresh_token)

        # Return new access token
        return jsonify({'access_token': new_tokens['access_token'], 'refresh_token': new_tokens['refresh_token']}), 200
    except UnauthorizedException as e:
        return jsonify({'message': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    Invalidate user's tokens and log them out of the system.
    """
    try:
        # Extract token from authorization header
        auth_header = request.headers.get('Authorization')
        access_token = extract_token_from_header(auth_header)
        refresh_token = request.get_json().get('refresh_token')

        # Call auth_service.logout_user with token
        auth_service.logout(access_token, refresh_token)

        # Publish user.logout event to event bus
        publish_event('user.logout', {'user_id': g.user['user_id']})

        # Return success response
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Logout failed'}), 500

@auth_bp.route('/password/reset', methods=['POST'])
def request_password_reset():
    """
    Initiate password reset process by sending reset email to user.
    """
    try:
        # Extract email from request JSON
        data = request.get_json()
        email = data.get('email')

        # Call auth_service.request_password_reset with email
        auth_service.forgot_password(email)

        # Return success response (even if email not found for security)
        return jsonify({'message': 'Password reset email sent if account exists'}), 200
    except Exception as e:
        return jsonify({'message': 'Password reset request failed'}), 500

@auth_bp.route('/password/change', methods=['POST'])
def reset_password():
    """
    Complete password reset using token and new password.
    """
    try:
        # Extract reset token and new password from request JSON
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('new_password')
        user_id = data.get('user_id')

        # Call auth_service.reset_password with token and new password
        auth_service.reset_password(user_id, token, new_password)

        # Publish user.password.changed event to event bus
        publish_event('user.password.changed', {'user_id': user_id, 'email': 'user@example.com'})

        # Return success response
        return jsonify({'message': 'Password reset successfully'}), 200
    except BadRequestException as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': 'Password reset failed'}), 500

@auth_bp.route('/status', methods=['GET'])
@token_required
def status():
    """
    Check if current authentication token is valid and return user information.
    """
    try:
        # Extract user ID from request context (set by token_required decorator)
        user_id = g.user['user_id']

        # Call user_service.get_user_by_id to get user details
        user = user_service.get_user_by_id(user_id)

        # Return user information
        return jsonify({'user': user.to_dict()}), 200
    except NotFoundException as e:
        return jsonify({'message': str(e)}), 404
    except Exception as e:
        return jsonify({'message': 'Authentication status check failed'}), 500