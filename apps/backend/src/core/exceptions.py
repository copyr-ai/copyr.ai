from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class CopyRightError(Exception):
    """Base exception for copyr.ai application"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(CopyRightError):
    """Validation related errors"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )

class AuthenticationError(CopyRightError):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(CopyRightError):
    """Authorization related errors"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundError(CopyRightError):
    """Resource not found errors"""
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )

class ExternalServiceError(CopyRightError):
    """External service integration errors"""
    def __init__(self, service: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"{service} service error: {message}",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service": service,
                "original_error": str(original_error) if original_error else None
            }
        )

class DatabaseError(CopyRightError):
    """Database operation errors"""
    def __init__(self, operation: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"Database {operation} failed: {message}",
            status_code=500,
            error_code="DATABASE_ERROR",
            details={
                "operation": operation,
                "original_error": str(original_error) if original_error else None
            }
        )

class RateLimitError(CopyRightError):
    """Rate limiting errors"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )

class SearchError(CopyRightError):
    """Search operation errors"""
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="SEARCH_ERROR",
            details={"query": query}
        )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for the application
    """
    # Generate correlation ID for tracking
    correlation_id = f"err_{int(datetime.now().timestamp() * 1000)}"
    
    if isinstance(exc, CopyRightError):
        # Handle our custom exceptions
        logger.warning(
            f"Application error [{correlation_id}]: {exc.error_code} - {exc.message}",
            extra={
                "correlation_id": correlation_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": str(request.url)
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "code": exc.error_code,
                    "correlation_id": correlation_id,
                    "details": exc.details
                }
            }
        )
    
    elif isinstance(exc, HTTPException):
        # Handle FastAPI HTTP exceptions
        logger.warning(
            f"HTTP error [{correlation_id}]: {exc.status_code} - {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "status_code": exc.status_code,
                "path": str(request.url)
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "code": "HTTP_ERROR",
                    "correlation_id": correlation_id
                }
            }
        )
    
    else:
        # Handle unexpected exceptions
        logger.error(
            f"Unexpected error [{correlation_id}]: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "path": str(request.url)
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "An unexpected error occurred",
                    "code": "INTERNAL_SERVER_ERROR",
                    "correlation_id": correlation_id
                }
            }
        )

def handle_database_errors(func):
    """Decorator to handle database operation errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            operation = func.__name__.replace('_', ' ')
            raise DatabaseError(operation, str(e), e)
    return wrapper

def handle_external_service_errors(service_name: str):
    """Decorator to handle external service errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise ExternalServiceError(service_name, str(e), e)
        return wrapper
    return decorator