import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any
import json

class CorrelationIDFilter(logging.Filter):
    """
    Logging filter to add correlation ID to all log records
    """
    def filter(self, record):
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, '_correlation_id', 'none')
        return True

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'correlation_id': getattr(record, 'correlation_id', 'none')
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'correlation_id']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

def setup_logging(
    log_level: str = None,
    log_format: str = "json",
    log_file: str = None
) -> None:
    """
    Setup application logging configuration
    """
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Ensure log_level is a string
    if not isinstance(log_level, str):
        log_level = "INFO"
    
    # Validate log level - map to numeric values
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL
    }
    
    numeric_level = level_mapping.get(log_level.upper(), logging.INFO)
    
    # Choose formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIDFilter())
    
    # File handler (optional)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationIDFilter())
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True
    )
    
    # Configure specific loggers
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    logging.getLogger("postgrest").setLevel(logging.WARNING)
    
    # Configure application loggers
    logging.getLogger("copyr").setLevel(numeric_level)
    logging.getLogger("src").setLevel(numeric_level)

class LoggingMiddleware:
    """
    Middleware for request/response logging
    """
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate correlation ID for this request
            import uuid
            correlation_id = str(uuid.uuid4())[:8]
            
            # Add correlation ID to the scope for other middleware/handlers
            scope["correlation_id"] = correlation_id
            
            # Set correlation ID in logging context
            import contextvars
            correlation_var = contextvars.ContextVar('correlation_id')
            correlation_var.set(correlation_id)
            
            # Log request
            logger = logging.getLogger("copyr.http")
            logger.info(
                "HTTP request started",
                extra={
                    "correlation_id": correlation_id,
                    "method": scope["method"],
                    "path": scope["path"],
                    "query_string": scope["query_string"].decode() if scope["query_string"] else "",
                    "client_ip": scope.get("client", ["unknown", None])[0]
                }
            )
            
            # Wrap send to log response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    logger.info(
                        "HTTP response started",
                        extra={
                            "correlation_id": correlation_id,
                            "status_code": message["status"]
                        }
                    )
                elif message["type"] == "http.response.body" and not message.get("more_body", False):
                    logger.info(
                        "HTTP request completed",
                        extra={
                            "correlation_id": correlation_id
                        }
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with proper configuration
    """
    return logging.getLogger(name)

class PerformanceLogger:
    """
    Context manager for performance logging
    """
    def __init__(self, operation_name: str, logger: logging.Logger = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger("copyr.performance")
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(
            f"Operation started: {self.operation_name}",
            extra={"operation": self.operation_name}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_seconds": round(duration, 4),
                    "status": "success"
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                extra={
                    "operation": self.operation_name,
                    "duration_seconds": round(duration, 4),
                    "status": "error",
                    "exception": str(exc_val)
                }
            )

def log_performance(operation_name: str):
    """
    Decorator for performance logging
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with PerformanceLogger(operation_name):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceLogger(operation_name):
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Health check logging
class HealthCheckLogger:
    """
    Logger for health check and monitoring
    """
    def __init__(self):
        self.logger = logging.getLogger("copyr.health")
    
    def log_health_check(self, service: str, status: str, details: Dict[str, Any] = None):
        """Log health check result"""
        self.logger.info(
            f"Health check: {service}",
            extra={
                "service": service,
                "health_status": status,
                "details": details or {}
            }
        )
    
    def log_service_availability(self, service: str, available: bool, response_time: float = None):
        """Log service availability"""
        self.logger.info(
            f"Service availability: {service}",
            extra={
                "service": service,
                "available": available,
                "response_time_ms": response_time
            }
        )

# Import asyncio at the end to avoid circular imports
import asyncio