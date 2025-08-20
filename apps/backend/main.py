from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging

from src.core.logging_config import setup_logging
from src.core.exceptions import global_exception_handler
from src.core.security import SecurityHeadersMiddleware
from src.api.routes import search, health, users, works, admin_auth

# Load environment variables
load_dotenv()

setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_format=os.getenv("LOG_FORMAT", "json")
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="copyr.ai API",
    description="Premium copyright intelligence infrastructure platform - Multi-country copyright analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health checks and system monitoring"
        },
        {
            "name": "search",
            "description": "Copyright work search and analysis"
        },
        {
            "name": "works",
            "description": "Work management and popular content"
        },
        {
            "name": "users",
            "description": "User profiles and search history"
        },
        {
            "name": "admin",
            "description": "Admin authentication for testing API endpoints"
        }
    ]
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://copyrai.vercel.app",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)
app.include_router(health.router)
app.include_router(search.router)
app.include_router(works.router)
app.include_router(users.router)
app.include_router(admin_auth.router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting copyr.ai API v2.0")
    
    try:
        # Initialize database components
        from src.database.cache_manager import CacheManager
        cache_manager = CacheManager()
        logger.info("Database components initialized successfully")
        
        # Initialize external API service
        from src.services.external_api_service import external_api_service
        await external_api_service.start_session()
        logger.info("External API service initialized successfully")
        
        logger.info("copyr.ai API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("API starting in degraded mode")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down copyr.ai API v2.0")
    
    try:
        from src.services.external_api_service import external_api_service
        await external_api_service.close_session()
        logger.info("External API service connections closed")
        logger.info("copyr.ai API shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to copyr.ai API v2.0",
        "version": "2.0.0",
        "features": [
            "JWT authentication with admin access",
            "Comprehensive error handling",
            "Structured logging",
            "Repository pattern for database operations",
            "Service layer for external API integrations",
            "Input validation and security headers"
        ],
        "documentation": "/docs"
    }

@app.get("/version")
async def get_version():
    """Get API version and build information"""
    return {
        "version": "2.0.0",
        "environment": os.getenv("PYTHON_ENV", "development"),
        "features": {
            "authentication": True,
            "structured_logging": True,
            "input_validation": True,
            "security_headers": True
        }
    }

if __name__ == "__main__":
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "reload": os.getenv("PYTHON_ENV", "development") == "development",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "workers": 1 if os.getenv("PYTHON_ENV", "development") == "development" else int(os.getenv("WORKERS", 4))
    }
    
    logger.info(f"Starting copyr.ai API v2.0")
    uvicorn.run(**uvicorn_config)