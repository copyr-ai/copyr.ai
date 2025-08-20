from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import jwt
from datetime import datetime, timedelta
import logging
from ...auth.middleware import require_auth

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    expires_in: int
    message: str

@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(credentials: AdminLoginRequest):
    """
    Admin login with fixed credentials from environment variables
    
    Use this to get a JWT token for testing the user APIs:
    1. Call this endpoint with admin credentials
    2. Copy the access_token from response
    3. Click "Authorize" in Swagger UI 
    4. Paste token in "Value" field
    5. Test protected endpoints!
    """
    
    # Get admin credentials from environment
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_user_id = os.getenv("ADMIN_USER_ID", "admin-123e4567-e89b-12d3-a456-426614174000")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@copyr.ai")
    
    # Validate credentials
    if credentials.username != admin_username or credentials.password != admin_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials"
        )
    
    # Generate JWT token
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
    # Token payload
    import time
    current_time = int(time.time())
    
    payload = {
        "user_id": admin_user_id,
        "email": admin_email,
        "sub": admin_user_id,
        "aud": "authenticated", 
        "role": "admin",
        "iat": current_time,
        "exp": current_time + (24 * 60 * 60),  # 24 hours
        "iss": "copyr.ai"
    }
    
    # Create token
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    return AdminTokenResponse(
        access_token=token,
        token_type="Bearer",
        user_id=admin_user_id,
        email=admin_email,
        expires_in=86400,
        message="Token generated successfully! Copy access_token and use in Swagger UI Authorization."
    )

@router.get("/verify")
async def verify_admin_token(current_user: dict = Depends(require_auth)):
    """
    Test endpoint to verify your admin token works
    Requires authentication
    """
    return {
        "message": "🎉 Admin authentication successful!",
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "user"),
        "status": "authenticated"
    }