"""
Rate limiting middleware for Flask applications.

This module implements a Redis-backed token bucket algorithm for rate limiting HTTP requests
in Flask applications. It provides configurable rate limits based on user types with support
for burst allowances to handle traffic spikes.
"""

import time
from typing import Dict, Any, Tuple, Callable, Optional
import functools
from flask import request, current_app

from ...database.redis.connection import get_redis_client
from ...exceptions.api_exceptions import RateLimitError
from ...logging.logger import get_logger
from ...config import get_config

# Set up module logger
logger = get_logger(__name__)

# Default rate limits (requests per minute)
DEFAULT_RATE_LIMITS = {
    'anonymous': 30,      # Anonymous users
    'authenticated': 120, # Authenticated users
    'service': 600        # Service accounts
}

# Default burst limits (additional request allowance)
DEFAULT_BURST_LIMITS = {
    'anonymous': 10,      # Anonymous users
    'authenticated': 30,  # Authenticated users
    'service': 100        # Service accounts
}


class RateLimiter:
    """
    Rate limiting implementation using token bucket algorithm with Redis for distributed
    state storage. Supports different rate limits based on user types and provides
    burst allowances.
    """
    
    def __init__(
        self, 
        rate_limits: Optional[Dict[str, int]] = None,
        burst_limits: Optional[Dict[str, int]] = None,
        redis_client = None
    ):
        """
        Initialize the rate limiter with configuration.
        
        Args:
            rate_limits: Dictionary of rate limits per user type (requests per minute)
            burst_limits: Dictionary of burst limits per user type
            redis_client: Redis client instance (if None, a new one will be created)
        """
        # Get configuration or use defaults
        config = get_config()
        
        # Store rate limits (default or provided)
        self._rate_limits = rate_limits or getattr(
            config, 'RATE_LIMIT_SETTINGS', DEFAULT_RATE_LIMITS
        )
        
        # Store burst limits (default or provided)
        self._burst_limits = burst_limits or getattr(
            config, 'BURST_LIMIT_SETTINGS', DEFAULT_BURST_LIMITS
        )
        
        # Initialize Redis client
        self._redis_client = redis_client or get_redis_client()
        
        # Set up logger
        self._logger = logger
        self._logger.info("Rate limiter initialized with the following limits: "
                         f"Rate limits: {self._rate_limits}, "
                         f"Burst limits: {self._burst_limits}")

    def get_user_identifier(self, request) -> str:
        """
        Extract a unique identifier for the user from request.
        
        Args:
            request: Flask request object
            
        Returns:
            User identifier (user ID or IP address)
        """
        # Check for Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            try:
                # Extract token
                token = auth_header[7:]
                
                # In a real implementation, we would decode and validate the JWT
                # and extract the user ID. For now, we'll use the token itself
                # as an identifier for authenticated users.
                return f"user:{token}"
            except Exception as e:
                self._logger.warning(f"Error extracting user ID from token: {str(e)}")
        
        # Fallback to IP address for anonymous users
        return f"ip:{request.remote_addr}"

    def get_user_type(self, request) -> str:
        """
        Determine the user type from the request.
        
        Args:
            request: Flask request object
            
        Returns:
            User type (anonymous, authenticated, service)
        """
        # Check if request has a valid Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            return 'anonymous'
        
        if auth_header.startswith('Bearer '):
            try:
                # Extract token
                token = auth_header[7:]
                
                # In a real implementation, we would decode the JWT and check 
                # if it's a service account token. For now, we'll check for
                # an API key header as a simple way to identify service accounts.
                if request.headers.get('X-API-Key'):
                    return 'service'
                
                # Otherwise it's a regular authenticated user
                return 'authenticated'
            except Exception as e:
                self._logger.warning(f"Error determining user type: {str(e)}")
                
        # Default to anonymous if we can't determine the user type
        return 'anonymous'

    def check_rate_limit(self, identifier: str, user_type: str) -> Tuple[bool, int, int]:
        """
        Check if the request exceeds rate limits using token bucket algorithm.
        
        Args:
            identifier: User identifier
            user_type: User type (anonymous, authenticated, service)
            
        Returns:
            Tuple of (is_limited: bool, remaining: int, reset_time: int)
        """
        # Get rate limit and burst limit for user type
        rate_limit = self._rate_limits.get(user_type, DEFAULT_RATE_LIMITS['anonymous'])
        burst_limit = self._burst_limits.get(user_type, DEFAULT_BURST_LIMITS['anonymous'])
        
        # Redis key for this user's token bucket
        redis_key = f"rate_limit:{user_type}:{identifier}"
        
        # Get current token count and last refill time
        bucket_data = self._redis_client.hgetall(redis_key)
        
        current_time = time.time()
        tokens = float(bucket_data.get('tokens', rate_limit + burst_limit))
        last_refill = float(bucket_data.get('last_refill', current_time))
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - last_refill
        tokens_to_add = time_elapsed * (rate_limit / 60.0)  # Convert from requests/minute to tokens/second
        
        # Refill bucket (up to max capacity)
        tokens = min(rate_limit + burst_limit, tokens + tokens_to_add)
        
        # Cost of this request
        cost = 1
        
        # Check if there are enough tokens
        if tokens >= cost:
            # Consume tokens
            tokens -= cost
            is_limited = False
        else:
            # Rate limit exceeded
            is_limited = True
        
        # Calculate time until next token is available
        if is_limited and tokens < cost:
            time_per_token = 60.0 / rate_limit  # seconds per token
            time_until_available = (cost - tokens) * time_per_token
            reset_time = int(current_time + time_until_available)
        else:
            reset_time = int(current_time)
        
        # Update Redis with new token count and refill time
        pipeline = self._redis_client.pipeline()
        pipeline.hset(redis_key, 'tokens', tokens)
        pipeline.hset(redis_key, 'last_refill', current_time)
        
        # Set key expiration to 2x the rate limit period to avoid stale data
        pipeline.expire(redis_key, 120)
        pipeline.execute()
        
        # Calculate remaining tokens
        remaining = int(tokens)
        
        return (is_limited, remaining, reset_time)

    def apply(self, app):
        """
        Apply rate limiting to a Flask app as middleware.
        
        Args:
            app: Flask application
            
        Returns:
            None
        """
        self._logger.info("Applying rate limiting middleware to Flask application")
        
        @app.before_request
        def check_rate_limit():
            # Skip rate limiting for exempt routes
            if getattr(request.endpoint, '_rate_limit_exempt', False):
                return None
                
            # Get user identifier and type
            identifier = self.get_user_identifier(request)
            user_type = self.get_user_type(request)
            
            # Check rate limit
            is_limited, remaining, reset_time = self.check_rate_limit(identifier, user_type)
            
            if is_limited:
                # Calculate retry after seconds
                retry_after = max(1, reset_time - int(time.time()))
                
                # Log rate limit exceeded
                self._logger.warning(
                    f"Rate limit exceeded for {user_type} user {identifier} "
                    f"(path: {request.path}, method: {request.method})"
                )
                
                # Raise rate limit error
                raise RateLimitError(
                    message="Rate limit exceeded",
                    retry_after=retry_after,
                    limit=self._rate_limits.get(user_type),
                    current=0
                )
        
        @app.after_request
        def add_rate_limit_headers(response):
            # Skip if route is exempt
            if getattr(request.endpoint, '_rate_limit_exempt', False):
                return response
                
            try:
                # Get user identifier and type
                identifier = self.get_user_identifier(request)
                user_type = self.get_user_type(request)
                
                # Check current rate limit status (without consuming a token)
                redis_key = f"rate_limit:{user_type}:{identifier}"
                bucket_data = self._redis_client.hgetall(redis_key)
                
                if bucket_data:
                    tokens = float(bucket_data.get('tokens', 0))
                    rate_limit = self._rate_limits.get(user_type, DEFAULT_RATE_LIMITS['anonymous'])
                    
                    # Add rate limit headers
                    response.headers['X-RateLimit-Limit'] = str(rate_limit)
                    response.headers['X-RateLimit-Remaining'] = str(int(tokens))
                    response.headers['X-RateLimit-Reset'] = bucket_data.get('last_refill', str(int(time.time())))
            except Exception as e:
                self._logger.error(f"Error adding rate limit headers: {str(e)}")
                
            return response

    def limit_request(self) -> Tuple[bool, Dict[str, str]]:
        """
        Check if current request is rate limited.
        
        Returns:
            Tuple of (is_limited: bool, headers: dict)
        """
        # Get user identifier and type
        identifier = self.get_user_identifier(request)
        user_type = self.get_user_type(request)
        
        # Check rate limit
        is_limited, remaining, reset_time = self.check_rate_limit(identifier, user_type)
        
        # Prepare rate limit headers
        headers = {
            'X-RateLimit-Limit': str(self._rate_limits.get(user_type, DEFAULT_RATE_LIMITS['anonymous'])),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time)
        }
        
        # Add Retry-After header if limited
        if is_limited:
            retry_after = max(1, reset_time - int(time.time()))
            headers['Retry-After'] = str(retry_after)
            
        return (is_limited, headers)

    @staticmethod
    def exempt(f: Callable) -> Callable:
        """
        Decorator to mark routes as exempt from rate limiting.
        
        Args:
            f: Function to decorate
            
        Returns:
            Decorated function
        """
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
            
        # Mark the function as exempt from rate limiting
        decorated_function._rate_limit_exempt = True
        return decorated_function

    def limiter(self, limit: int, burst: Optional[int] = None) -> Callable:
        """
        Decorator to apply rate limiting to a specific route.
        
        Args:
            limit: Rate limit in requests per minute
            burst: Burst limit (optional)
            
        Returns:
            Decorator function
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                # Use the provided limit and burst instead of the default
                identifier = self.get_user_identifier(request)
                user_type = self.get_user_type(request)
                
                # Override rate limits for this route
                original_rate_limit = self._rate_limits.get(user_type)
                original_burst_limit = self._burst_limits.get(user_type)
                
                try:
                    # Set custom limits for this request
                    self._rate_limits[user_type] = limit
                    if burst is not None:
                        self._burst_limits[user_type] = burst
                    
                    # Check rate limit
                    is_limited, remaining, reset_time = self.check_rate_limit(identifier, user_type)
                    
                    if is_limited:
                        # Calculate retry after seconds
                        retry_after = max(1, reset_time - int(time.time()))
                        
                        # Log rate limit exceeded
                        self._logger.warning(
                            f"Route-specific rate limit exceeded for {user_type} user {identifier} "
                            f"(path: {request.path}, method: {request.method}, limit: {limit})"
                        )
                        
                        # Raise rate limit error
                        raise RateLimitError(
                            message="Rate limit exceeded",
                            retry_after=retry_after,
                            limit=limit,
                            current=0
                        )
                    
                    # Execute the original function
                    response = f(*args, **kwargs)
                    
                    # Add rate limit headers if it's a Response object
                    if hasattr(response, 'headers'):
                        response.headers['X-RateLimit-Limit'] = str(limit)
                        response.headers['X-RateLimit-Remaining'] = str(remaining)
                        response.headers['X-RateLimit-Reset'] = str(reset_time)
                    
                    return response
                    
                finally:
                    # Restore original rate limits
                    self._rate_limits[user_type] = original_rate_limit
                    self._burst_limits[user_type] = original_burst_limit
                    
            return decorated_function
            
        return decorator