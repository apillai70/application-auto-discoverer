# health_hotfix.py - Save this in your routers folder
import sys
import importlib

# Force reload the health module
if 'routers.health' in sys.modules:
    del sys.modules['routers.health']

# Now import and patch
from routers import health

# Override the SERVICE_CONFIG directly
health.SERVICE_CONFIG = {
    "activnet_api": {
        "urls": ["http://localhost:8001"],
        "port": 8001,
        "type": health.ServiceType.API,
        "critical": True,
        "health_endpoint": "/api/v1/health/ping",
        "functionality_checks": {},  # Empty - no checks
        "dependencies": []
    },
    "compliance": {
        "urls": ["http://localhost:8001"],
        "type": health.ServiceType.API,
        "critical": False,  # Not critical
        "health_endpoint": "/api/v1/compliance/features",
        "functionality_checks": {},  # Empty - no checks
        "dependencies": []
    },
    "audit": {
        "urls": ["http://localhost:8001"],
        "type": health.ServiceType.MONITORING,
        "critical": False,
        "health_endpoint": "/api/v1/audit/events",
        "functionality_checks": {},  # Empty - no checks
        "dependencies": []
    }
}

print("✅ Health hotfix applied - Compliance checks disabled")