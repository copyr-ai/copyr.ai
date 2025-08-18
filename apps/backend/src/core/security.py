from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import Callable
import re
import logging
from .exceptions import ValidationError

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # More permissive CSP for FastAPI docs to work
        csp_policy = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

class InputSanitizer:
    """
    Input sanitization and validation utilities
    """
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize string input
        """
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input too long. Maximum {max_length} characters allowed")
        
        # Remove HTML if not allowed
        if not allow_html:
            value = re.sub(r'<[^>]*>', '', value)
        
        return value
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """
        Validate and sanitize search queries
        """
        if not query:
            raise ValidationError("Search query cannot be empty")
        
        # Sanitize the query
        query = InputSanitizer.sanitize_string(query, max_length=500)
        
        # Check for minimum length
        if len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters long")
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    @staticmethod
    def validate_user_id(user_id: str) -> str:
        """
        Validate user ID format (UUID)
        """
        if not user_id:
            raise ValidationError("User ID cannot be empty")
        
        # Check UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, user_id.lower()):
            raise ValidationError("Invalid user ID format")
        
        return user_id.lower()
    
    @staticmethod
    def validate_work_type(work_type: str) -> str:
        """
        Validate work type input
        """
        allowed_types = ["literary", "musical", "auto"]
        
        if work_type not in allowed_types:
            raise ValidationError(f"Invalid work type. Allowed values: {', '.join(allowed_types)}")
        
        return work_type
    
    @staticmethod
    def validate_country_code(country_code: str) -> str:
        """
        Validate country code input
        """
        if not country_code:
            raise ValidationError("Country code cannot be empty")
        
        # Basic validation for country codes (2-3 uppercase letters)
        if not re.match(r'^[A-Z]{2,3}$', country_code.upper()):
            raise ValidationError("Invalid country code format")
        
        return country_code.upper()
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 50) -> int:
        """
        Validate pagination limit
        """
        if not isinstance(limit, int):
            raise ValidationError("Limit must be an integer")
        
        if limit < 1:
            raise ValidationError("Limit must be at least 1")
        
        if limit > max_limit:
            raise ValidationError(f"Limit cannot exceed {max_limit}")
        
        return limit

class RequestValidator:
    """
    Request validation utilities
    """
    
    @staticmethod
    def validate_content_type(request: Request, allowed_types: list = None):
        """
        Validate request content type
        """
        if allowed_types is None:
            allowed_types = ["application/json"]
        
        content_type = request.headers.get("content-type", "").lower()
        
        # Extract base content type (ignore charset, etc.)
        base_content_type = content_type.split(';')[0].strip()
        
        if base_content_type not in allowed_types:
            raise ValidationError(f"Unsupported content type: {content_type}")
    
    @staticmethod
    def validate_request_size(request: Request, max_size: int = 1024 * 1024):  # 1MB default
        """
        Validate request body size
        """
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > max_size:
            raise ValidationError(f"Request body too large. Maximum {max_size} bytes allowed")

def sanitize_search_request(search_data: dict) -> dict:
    """
    Sanitize search request data
    """
    sanitized = {}
    
    if "author" in search_data and search_data["author"]:
        sanitized["author"] = InputSanitizer.sanitize_string(search_data["author"], max_length=200)
    
    if "title" in search_data and search_data["title"]:
        sanitized["title"] = InputSanitizer.sanitize_string(search_data["title"], max_length=500)
    
    if "work_type" in search_data and search_data["work_type"]:
        sanitized["work_type"] = InputSanitizer.validate_work_type(search_data["work_type"])
    
    if "country" in search_data and search_data["country"]:
        sanitized["country"] = InputSanitizer.validate_country_code(search_data["country"])
    
    if "limit" in search_data:
        sanitized["limit"] = InputSanitizer.validate_limit(search_data["limit"])
    
    if "user_id" in search_data and search_data["user_id"]:
        sanitized["user_id"] = InputSanitizer.validate_user_id(search_data["user_id"])
    
    return sanitized

class SQLInjectionProtector:
    """
    SQL injection protection utilities
    """
    
    @staticmethod
    def is_safe_for_sql(value: str) -> bool:
        """
        Check if a string is safe for SQL operations
        """
        # List of dangerous SQL keywords and patterns
        dangerous_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bor\b.*=.*\bor\b)",
            r"(\band\b.*=.*\band\b)",
            r"(\'.*\bor\b.*\')",
            r"(\".*\bor\b.*\")",
            r"(\;.*\b(drop|delete|update|insert)\b)"
        ]
        
        value_lower = value.lower()
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def sanitize_for_sql(value: str) -> str:
        """
        Sanitize string for SQL operations
        """
        if not SQLInjectionProtector.is_safe_for_sql(value):
            raise ValidationError("Input contains potentially dangerous content")
        
        # Escape single quotes
        value = value.replace("'", "''")
        
        return value