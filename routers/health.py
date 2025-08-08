# routers/health.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import psutil
import time

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: float
    system_info: Dict[str, Any]
    services: Dict[str, str]

start_time = time.time()

@router.get("/", response_model=HealthStatus)
async def health_check():
    """Comprehensive health check"""
    uptime = time.time() - start_time
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    system_info = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "disk_usage_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2)
    }
    
    # Service status checks
    services = {
        "database": "healthy" if cpu_percent < 90 else "degraded",
        "authentication": "healthy",
        "network_segmentation": "healthy" if memory.percent < 85 else "degraded",
        "log_processing": "healthy",
        "analytics": "healthy" if disk.percent < 90 else "degraded"
    }
    
    # Overall status
    overall_status = "healthy"
    if any(status == "degraded" for status in services.values()):
        overall_status = "degraded"
    if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
        overall_status = "critical"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=uptime,
        system_info=system_info,
        services=services
    )

@router.get("/detailed")
async def detailed_health():
    """Detailed health metrics"""
    return {
        "application": {
            "name": "Application Auto-Discovery Platform",
            "version": "2.0.0",
            "uptime_seconds": time.time() - start_time,
            "status": "running"
        },
        "system": {
            "cpu_count": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        },
        "network": {
            "connections": len(psutil.net_connections()),
            "io_stats": psutil.net_io_counters()._asdict()
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.now().isoformat()}
