# routers/__init__.py
"""
Routers package for comprehensive logging system
"""

__version__ = "2.2.0"

def get_available_routers():
    """Get list of available routers"""
    return [
        {
            "name": "comprehensive_logging",
            "module": None,
            "metadata": {
                "prefix": "/api/v1/logs",
                "tags": ["comprehensive-logging"],
                "enabled": True
            }
        },
        {
            "name": "frontend_logging", 
            "module": None,
            "metadata": {
                "prefix": "/api/v1/logs",
                "tags": ["frontend-logging"],
                "enabled": True
            }
        },
        {
            "name": "enhanced_audit",
            "module": None,
            "metadata": {
                "prefix": "/api/v1/audit",
                "tags": ["audit", "logging", "security"],
                "enabled": True
            }
        },
        {
            "name": "archetype_classification",
            "module": None,  # or import the actual module
            "metadata": {
                "prefix": "/api/v1/archetype",
                "tags": ["archetype-classification", "diagram-generation"],
                "enabled": True
            }
        },
        {
            "name": "excel_processing",
            "module": None,
            "metadata": {
                "prefix": "/api/v1/excel", 
                "tags": ["excel-processing"],
                "enabled": True
            }
        }
    ]

def get_initialization_order():
    """Get router initialization order"""
    return ["comprehensive_logging", "frontend_logging", "enhanced_audit"]

def get_router_statistics():
    """Get router statistics"""
    return {
        "total_routers": 3,
        "enabled_routers": 3,
        "failed_routers": 0
    }

# =================== FEATURE MANAGEMENT ===================

def get_enabled_features():
    """Get dictionary of enabled features"""
    return {
        "basic_api": True,
        "comprehensive_logging": True,
        "frontend_logging": True,
        "enhanced_audit": True,
        "file_storage": True,
        "network_segmentation": True,
        "log_based_analysis": True,
        "compliance_management": True,
        "threat_detection": True,
        "risk_assessment": True,
        "user_activity_tracking": True,
        "security_violation_detection": True,
        "export_reporting": True,
        "archetype_identification": True,
        "excel_processing": True
    }

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled"""
    enabled_features = get_enabled_features()
    return enabled_features.get(feature_name, False)

def get_api_groups():
    """Get API groups for organization"""
    return {
        "Logging & Audit": {
            "description": "Comprehensive logging and audit trail management",
            "routers": ["comprehensive_logging", "frontend_logging", "enhanced_audit"],
            "endpoints": [
                "/api/v1/logs/",
                "/api/v1/audit/",
                "/api/v1/audit/frontend/"
            ]
        },
        "Security": {
            "description": "Security monitoring and threat detection",
            "routers": ["enhanced_audit"],
            "endpoints": [
                "/api/v1/audit/events",
                "/api/v1/audit/security-violations",
                "/api/v1/audit/risk-profiles/"
            ]
        },
        "Health & Monitoring": {
            "description": "System health and monitoring endpoints",
            "routers": ["comprehensive_logging"],
            "endpoints": [
                "/health",
                "/api/v1/health/simple",
                "/api/v1/health/detailed"
            ]
        },
        "Application Discovery": {
            "description": "Application portfolio management and discovery",
            "routers": [],
            "endpoints": [
                "/api/v1/dashboard/summary",
                "/api/v1/export/cost-analysis"
            ]
        }
    }

# =================== COMPATIBILITY & VALIDATION ===================

def check_compatibility():
    """Check for compatibility warnings"""
    warnings = []
    
    # Check Python version
    import sys
    if sys.version_info < (3, 8):
        warnings.append("Python 3.8+ recommended for optimal performance")
    
    # Check required modules
    try:
        import fastapi
        if hasattr(fastapi, '__version__'):
            version_parts = fastapi.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major == 0 and minor < 68:
                warnings.append("FastAPI 0.68+ recommended for full feature support")
    except ImportError:
        warnings.append("FastAPI not found - some features may be unavailable")
    
    # Check for storage directories
    import os
    from pathlib import Path
    
    base_paths = ["essentials", "logs", "static"]
    for path in base_paths:
        if not Path(path).exists():
            warnings.append(f"Directory '{path}' not found - will be created automatically")
    
    return warnings

# =================== ROUTER METADATA ===================

def get_router_metadata(router_name: str):
    """Get metadata for a specific router"""
    routers = get_available_routers()
    for router in routers:
        if router["name"] == router_name:
            return router["metadata"]
    return None

def get_router_status():
    """Get status of all routers"""
    routers = get_available_routers()
    status = {}
    
    for router in routers:
        router_name = router["name"]
        try:
            # Try to import the router module
            if router_name == "enhanced_audit":
                from routers import enhanced_audit
                status[router_name] = {
                    "status": "available",
                    "module": "enhanced_audit",
                    "endpoints": "operational"
                }
            else:
                status[router_name] = {
                    "status": "configured",
                    "module": router_name,
                    "endpoints": "pending"
                }
        except ImportError as e:
            status[router_name] = {
                "status": "unavailable",
                "error": str(e),
                "endpoints": "failed"
            }
    
    return status

# =================== FEATURE CATEGORIES ===================

def get_feature_categories():
    """Get features organized by category"""
    return {
        "Core Features": [
            "basic_api",
            "comprehensive_logging",
            "frontend_logging"
        ],
        "Security Features": [
            "enhanced_audit",
            "network_segmentation",
            "threat_detection",
            "risk_assessment",
            "security_violation_detection"
        ],
        "Analysis Features": [
            "log_based_analysis",
            "user_activity_tracking",
            "compliance_management"
        ],
        "Storage Features": [
            "file_storage",
            "export_reporting"
        ]
    }

def get_security_features():
    """Get list of security-related features"""
    categories = get_feature_categories()
    return categories.get("Security Features", [])

def get_core_features():
    """Get list of core features"""
    categories = get_feature_categories()
    return categories.get("Core Features", [])

# =================== UTILITY FUNCTIONS ===================

def validate_router_config():
    """Validate router configuration"""
    issues = []
    
    # Check router count
    available = get_available_routers()
    if len(available) == 0:
        issues.append("No routers configured")
    
    # Check for duplicate names
    names = [r["name"] for r in available]
    if len(names) != len(set(names)):
        issues.append("Duplicate router names detected")
    
    # Check initialization order
    init_order = get_initialization_order()
    for router_name in init_order:
        if not any(r["name"] == router_name for r in available):
            issues.append(f"Router '{router_name}' in initialization order but not in available routers")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "router_count": len(available),
        "enabled_count": len([r for r in available if r["metadata"]["enabled"]])
    }

def get_system_info():
    """Get system information for debugging"""
    import sys
    import platform
    from datetime import datetime
    
    return {
        "routers_version": __version__,
        "python_version": sys.version,
        "platform": platform.platform(),
        "timestamp": datetime.now().isoformat(),
        "available_routers": len(get_available_routers()),
        "enabled_features": len(get_enabled_features()),
        "security_features": len(get_security_features())
    }

# =================== HEALTH CHECK ===================

def health_check():
    """Perform health check on router system"""
    try:
        config_validation = validate_router_config()
        router_status = get_router_status()
        compatibility_warnings = check_compatibility()
        
        # Determine overall health
        healthy_routers = sum(1 for status in router_status.values() 
                            if status["status"] in ["available", "configured"])
        total_routers = len(router_status)
        
        health_status = "healthy"
        if healthy_routers < total_routers:
            health_status = "degraded"
        if not config_validation["valid"]:
            health_status = "error"
        
        return {
            "status": health_status,
            "router_health": f"{healthy_routers}/{total_routers} routers operational",
            "config_valid": config_validation["valid"],
            "warnings": compatibility_warnings,
            "details": {
                "config_validation": config_validation,
                "router_status": router_status
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "router_health": "unknown",
            "config_valid": False
        }

# =================== EXPORTS ===================

# Make commonly used functions easily accessible
__all__ = [
    "get_available_routers",
    "get_initialization_order", 
    "get_router_statistics",
    "get_enabled_features",
    "is_feature_enabled",
    "get_api_groups",
    "check_compatibility",
    "get_router_status",
    "health_check",
    "validate_router_config",
    "get_system_info"
]