import time
import psutil
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
# Database import moved to avoid circular dependency issues
# from ..database.config import supabase
from .logging_config import HealthCheckLogger

logger = logging.getLogger(__name__)
health_logger = HealthCheckLogger()

class SystemMetrics:
    """
    System performance metrics collection
    """
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_stats = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            }
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_stats = {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 2)
            }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": cpu_count
                },
                "memory": memory_stats,
                "disk": disk_stats
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {"error": str(e)}

class PerformanceTracker:
    """
    Application performance tracking
    """
    
    def __init__(self):
        self.request_times = []
        self.error_counts = {}
        self.endpoint_stats = {}
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record request performance metrics"""
        key = f"{method} {endpoint}"
        
        if key not in self.endpoint_stats:
            self.endpoint_stats[key] = {
                "count": 0,
                "total_duration": 0,
                "error_count": 0,
                "avg_duration": 0
            }
        
        stats = self.endpoint_stats[key]
        stats["count"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        
        if status_code >= 400:
            stats["error_count"] += 1
        
        # Keep recent request times for percentile calculations
        self.request_times.append({
            "endpoint": key,
            "duration": duration,
            "timestamp": time.time(),
            "status_code": status_code
        })
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.request_times:
            return {"message": "No performance data available"}
        
        recent_requests = [
            r for r in self.request_times 
            if time.time() - r["timestamp"] < 3600  # Last hour
        ]
        
        if not recent_requests:
            return {"message": "No recent performance data"}
        
        durations = [r["duration"] for r in recent_requests]
        durations.sort()
        
        count = len(durations)
        error_count = sum(1 for r in recent_requests if r["status_code"] >= 400)
        
        return {
            "requests_last_hour": count,
            "error_rate_percent": round((error_count / count) * 100, 2) if count > 0 else 0,
            "avg_response_time_ms": round(sum(durations) / count * 1000, 2) if count > 0 else 0,
            "p50_response_time_ms": round(durations[count // 2] * 1000, 2) if count > 0 else 0,
            "p95_response_time_ms": round(durations[int(count * 0.95)] * 1000, 2) if count > 0 else 0,
            "p99_response_time_ms": round(durations[int(count * 0.99)] * 1000, 2) if count > 0 else 0,
            "endpoint_stats": dict(list(self.endpoint_stats.items())[:10])  # Top 10 endpoints
        }

class HealthChecker:
    """
    Health check for all system components
    """
    
    def __init__(self):
        self.last_check = None
        self.check_interval = timedelta(minutes=5)
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Import here to avoid circular dependency
            from ..database.config import supabase
            
            start_time = time.time()
            
            # Simple query to test connectivity
            response = supabase.table("work_cache").select("id").limit(1).execute()
            
            duration = time.time() - start_time
            
            health_status = {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
                "connection": "ok"
            }
            
            health_logger.log_service_availability("database", True, duration * 1000)
            return health_status
            
        except Exception as e:
            health_status = {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }
            
            health_logger.log_service_availability("database", False)
            logger.error(f"Database health check failed: {e}")
            return health_status
    
    async def check_external_services_health(self) -> Dict[str, Any]:
        """Check health of external API services"""
        services_health = {}
        
        # Library of Congress API check
        try:
            from ..countries.us.api_clients.library_of_congress import LibraryOfCongressClient
            
            start_time = time.time()
            loc_client = LibraryOfCongressClient()
            # Simple test query
            results = loc_client.search_by_title("test", limit=1)
            duration = time.time() - start_time
            
            services_health["library_of_congress"] = {
                "status": "healthy" if results else "degraded",
                "response_time_ms": round(duration * 1000, 2)
            }
            
            health_logger.log_service_availability("library_of_congress", True, duration * 1000)
            
        except Exception as e:
            services_health["library_of_congress"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_logger.log_service_availability("library_of_congress", False)
        
        # MusicBrainz API check
        try:
            from ..countries.us.api_clients.musicbrainz import MusicBrainzClient
            
            start_time = time.time()
            mb_client = MusicBrainzClient()
            # Simple test query
            response = mb_client.search_works("test", "")
            duration = time.time() - start_time
            
            services_health["musicbrainz"] = {
                "status": "healthy" if response and response.success else "degraded",
                "response_time_ms": round(duration * 1000, 2)
            }
            
            health_logger.log_service_availability("musicbrainz", True, duration * 1000)
            
        except Exception as e:
            services_health["musicbrainz"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_logger.log_service_availability("musicbrainz", False)
        
        return services_health
    
    async def run_full_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        if (self.last_check and 
            datetime.utcnow() - self.last_check < self.check_interval):
            return {"message": "Health check skipped (too recent)"}
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy"
        }
        
        # System metrics
        health_report["system"] = SystemMetrics.get_system_stats()
        
        # Database health
        health_report["database"] = await self.check_database_health()
        
        # External services health
        health_report["external_services"] = await self.check_external_services_health()
        
        # Determine overall status
        unhealthy_services = []
        
        if health_report["database"]["status"] != "healthy":
            unhealthy_services.append("database")
        
        for service, status in health_report["external_services"].items():
            if status["status"] == "unhealthy":
                unhealthy_services.append(service)
        
        if unhealthy_services:
            health_report["overall_status"] = "degraded" if len(unhealthy_services) < 2 else "unhealthy"
            health_report["unhealthy_services"] = unhealthy_services
        
        self.last_check = datetime.utcnow()
        
        # Log overall health status
        health_logger.log_health_check(
            "system", 
            health_report["overall_status"],
            {"unhealthy_services": unhealthy_services}
        )
        
        return health_report

class AlertManager:
    """
    Alert management for critical issues
    """
    
    def __init__(self):
        self.alert_thresholds = {
            "error_rate_percent": 10.0,
            "avg_response_time_ms": 5000.0,
            "cpu_usage_percent": 80.0,
            "memory_usage_percent": 85.0,
            "disk_usage_percent": 90.0
        }
        self.active_alerts = set()
    
    def check_performance_alerts(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for performance-based alerts"""
        alerts = []
        
        # Error rate alert
        error_rate = performance_data.get("error_rate_percent", 0)
        if error_rate > self.alert_thresholds["error_rate_percent"]:
            alert = {
                "type": "high_error_rate",
                "message": f"Error rate is {error_rate}%, threshold is {self.alert_thresholds['error_rate_percent']}%",
                "severity": "critical" if error_rate > 20 else "warning",
                "value": error_rate,
                "threshold": self.alert_thresholds["error_rate_percent"]
            }
            alerts.append(alert)
        
        # Response time alert
        avg_response = performance_data.get("avg_response_time_ms", 0)
        if avg_response > self.alert_thresholds["avg_response_time_ms"]:
            alert = {
                "type": "slow_response_time",
                "message": f"Average response time is {avg_response}ms, threshold is {self.alert_thresholds['avg_response_time_ms']}ms",
                "severity": "warning",
                "value": avg_response,
                "threshold": self.alert_thresholds["avg_response_time_ms"]
            }
            alerts.append(alert)
        
        return alerts
    
    def check_system_alerts(self, system_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for system-based alerts"""
        alerts = []
        
        if "error" in system_data:
            return [{"type": "system_metrics_error", "message": system_data["error"], "severity": "critical"}]
        
        # CPU usage alert
        cpu_usage = system_data.get("cpu", {}).get("usage_percent", 0)
        if cpu_usage > self.alert_thresholds["cpu_usage_percent"]:
            alert = {
                "type": "high_cpu_usage",
                "message": f"CPU usage is {cpu_usage}%, threshold is {self.alert_thresholds['cpu_usage_percent']}%",
                "severity": "critical" if cpu_usage > 95 else "warning",
                "value": cpu_usage,
                "threshold": self.alert_thresholds["cpu_usage_percent"]
            }
            alerts.append(alert)
        
        # Memory usage alert
        memory_usage = system_data.get("memory", {}).get("used_percent", 0)
        if memory_usage > self.alert_thresholds["memory_usage_percent"]:
            alert = {
                "type": "high_memory_usage",
                "message": f"Memory usage is {memory_usage}%, threshold is {self.alert_thresholds['memory_usage_percent']}%",
                "severity": "critical" if memory_usage > 95 else "warning",
                "value": memory_usage,
                "threshold": self.alert_thresholds["memory_usage_percent"]
            }
            alerts.append(alert)
        
        # Disk usage alert
        disk_usage = system_data.get("disk", {}).get("used_percent", 0)
        if disk_usage > self.alert_thresholds["disk_usage_percent"]:
            alert = {
                "type": "high_disk_usage",
                "message": f"Disk usage is {disk_usage}%, threshold is {self.alert_thresholds['disk_usage_percent']}%",
                "severity": "critical" if disk_usage > 98 else "warning",
                "value": disk_usage,
                "threshold": self.alert_thresholds["disk_usage_percent"]
            }
            alerts.append(alert)
        
        return alerts

# Global instances
performance_tracker = PerformanceTracker()
health_checker = HealthChecker()
alert_manager = AlertManager()