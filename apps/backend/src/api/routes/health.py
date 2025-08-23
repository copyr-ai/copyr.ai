from fastapi import APIRouter, Depends
from typing import Dict, Any
from ...core.monitoring import health_checker, performance_tracker, alert_manager, SystemMetrics
from ...core.logging_config import get_logger
from ...repositories.work_repository import WorkRepository
from ...copyright_analyzer import CopyrightAnalyzer
from datetime import datetime
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["health"])

work_repo = WorkRepository()

@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to copyr.ai API", "version": "1.0.0"}

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "ok", 
        "service": "copyr.ai API", 
        "environment": os.getenv("PYTHON_ENV", "development"),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/status")
async def api_status():
    """Detailed API status"""
    try:
        return {
            "api": "operational",
            "services": {
                "copyright_analyzer": "ready",
                "library_of_congress": "ready",
                # "hathitrust": "ready",  # Removed
                "musicbrainz": "ready"
            },
            "supported_countries": CopyrightAnalyzer.get_all_supported_countries(),
            "supported_work_types": ["literary", "musical"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "api": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with all system components"""
    try:
        health_report = await health_checker.run_full_health_check()
        return health_report
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unhealthy",
            "error": str(e)
        }

@router.get("/metrics")
async def get_metrics():
    """Get system and application metrics"""
    try:
        # System metrics
        system_stats = SystemMetrics.get_system_stats()
        
        # Performance metrics
        performance_stats = performance_tracker.get_performance_summary()
        
        # Database statistics
        db_stats = await work_repo.get_statistics()
        
        # Check for alerts
        performance_alerts = alert_manager.check_performance_alerts(performance_stats)
        system_alerts = alert_manager.check_system_alerts(system_stats)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_stats,
            "performance": performance_stats,
            "database": db_stats,
            "alerts": {
                "performance": performance_alerts,
                "system": system_alerts,
                "total_count": len(performance_alerts) + len(system_alerts)
            }
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check database connectivity
        db_health = await health_checker.check_database_health()
        
        if db_health["status"] == "healthy":
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": "database_unhealthy"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}

@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe"""
    try:
        # Simple check to ensure the service is running
        return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {"status": "dead", "reason": str(e)}