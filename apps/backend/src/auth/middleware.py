from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable, Any
import jwt
import os
from functools import wraps
# from ..database.config import supabase_admin  # Import moved to avoid version issues
import logging

logger = logging.getLogger(__name__)

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)

class AuthError(Exception):
    """Custom authentication error"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """
    Verify JWT token from Authorization header
    Returns user data if valid, None if no token provided
    Supports both Supabase tokens and local admin JWT tokens
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # First try to verify as local admin JWT token
    try:
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_aud": False})
        
        if payload.get("role") == "admin":
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": "admin",
                "iss": payload.get("iss"),
                "user_metadata": {}
            }
    except jwt.InvalidTokenError:
        pass
    except Exception:
        pass
    
    # If not a local JWT, try Supabase token verification
    try:
        from ..database.config import supabase_admin
        response = supabase_admin.auth.get_user(token)
        if response.user:
            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata
            }
        return None
    except Exception as e:
        logger.warning(f"Supabase token verification failed: {e}")
        return None

async def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """
    Require valid authentication - raises 401 if not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = await verify_token(credentials)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

async def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """
    Optional authentication - returns user data if authenticated, None if not
    Does not raise errors for missing/invalid tokens
    """
    return await verify_token(credentials)

def require_user_permission(user_id_param: str = "user_id"):
    """
    Decorator to ensure authenticated user can only access their own resources
    """
    async def permission_check(
        current_user: dict = Depends(require_auth),
        **path_params
    ) -> dict:
        requested_user_id = path_params.get(user_id_param)
        if requested_user_id and requested_user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: insufficient permissions"
            )
        return current_user
    
    return permission_check

class RateLimitExceeded(Exception):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

# Simple in-memory rate limiter (for production, use Redis)
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """
        Simple rate limiting - for production, implement with Redis
        """
        import time
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if current_time - req_time < window_seconds
        ]
        
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        self.requests[identifier].append(current_time)
        return True

rate_limiter = SimpleRateLimiter()

async def rate_limit_check(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 3600,
    current_user: Optional[dict] = Depends(optional_auth)
):
    """
    Rate limiting middleware
    """
    # Use user ID if authenticated, otherwise use IP
    identifier = current_user["user_id"] if current_user else str(request.client.host)
    
    if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True