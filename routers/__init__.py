# routers/__init__.py - Updated with Enhanced Audit System Integration
"""
Router package initialization for Banking Network Security & Discovery Platform

This package contains all API routers for the integrated system:
- Core application functionality (topology, integration, documentation)
- Authentication and authorization
- Health monitoring and system diagnostics
- Enhanced audit logging with file-based storage and risk assessment
- Security features (network segmentation, threat detection)
- Testing and debugging utilities
"""

# Import core routers (preserved from original system)
from . import topology
from . import integration
from . import documentation
from . import diagram

# Import authentication and security routers
from . import auth
from . import health
from . import audit  # Enhanced audit router with file-based storage
from . import compliance
from . import threat_detection

# Import network security routers
from . import netseg
from . import log_management
from . import analytics
from . import reports

# Import utility routers
from . import test
from . import debug

# Optional: Import additional routers if implemented
try:
    from . import network_discovery
    from . import migration
    from . import app_rationalization
except ImportError:
    # These are optional modules
    network_discovery = None
    migration = None
    app_rationalization = None

# Check for enhanced audit system components
try:
    import storage.file_audit_storage
    import utils.audit_file_processor
    ENHANCED_AUDIT_AVAILABLE = True
except ImportError:
    ENHANCED_AUDIT_AVAILABLE = False

# Export all available routers
__all__ = [
    # Core functionality routers
    "topology",
    "integration", 
    "documentation",
    "diagram",
    
    # Authentication and security
    "auth",
    "health",
    "audit",  # Enhanced audit system
    "compliance",
    "threat_detection",
    
    # Network security routers
    "netseg",
    "log_management",
    "analytics",
    "reports",
    
    # Utility routers
    "test",
    "debug",
    
    # Optional routers
    "network_discovery",
    "migration",
    "app_rationalization", 
    
    # Utility functions
    "get_available_routers",
    "get_routers_by_category", 
    "get_discovery_routers",
    "get_security_routers",
    "get_utility_routers",
    "get_initialization_order",
    "get_api_groups",
    "get_enabled_features",
    "is_feature_enabled",
    "check_compatibility",
    "get_audit_capabilities",
    
    # Constants
    "ROUTER_METADATA",
    "FEATURES", 
    "API_GROUPS",
    "INITIALIZATION_ORDER"
]

# Enhanced router metadata for API documentation and management
ROUTER_METADATA = {
    # Core functionality
    "topology": {
        "prefix": "/api/v1/topology",
        "tags": ["topology"],
        "description": "Network topology discovery and mapping",
        "category": "core",
        "requires_auth": False,
        "version": "1.0.0"
    },
    "integration": {
        "prefix": "/api/v1/integration",
        "tags": ["integration"],
        "description": "System integrations and external connections", 
        "category": "core",
        "requires_auth": False,
        "version": "1.0.0"
    },
    "documentation": {
        "prefix": "/api/v1/documentation",
        "tags": ["documentation"],
        "description": "Automated documentation generation",
        "category": "core",
        "requires_auth": False,
        "version": "1.0.0"
    },
    "diagram": {
        "prefix": "/api/v1/diagram",
        "tags": ["diagram"],
        "description": "Network diagram creation and visualization",
        "category": "core", 
        "requires_auth": False,
        "version": "1.0.0"
    },
    
    # Authentication and core security
    "auth": {
        "prefix": "/api/v1/auth",
        "tags": ["authentication"],
        "description": "Authentication and authorization services",
        "category": "security",
        "requires_auth": False,  # Auth endpoints don't require authentication
        "version": "1.0.0"
    },
    "health": {
        "prefix": "/api/v1/health", 
        "tags": ["health", "monitoring"],
        "description": "Health monitoring and system diagnostics",
        "category": "utility",
        "requires_auth": False,
        "version": "1.0.0"
    },
    
    # ENHANCED AUDIT SYSTEM
    "audit": {
        "prefix": "/api/v1/audit",
        "tags": ["audit", "security", "compliance", "risk-assessment"],
        "description": "Enhanced audit system with file-based storage, risk assessment, and threat detection",
        "category": "security",
        "requires_auth": True,
        "version": "2.1.0",  # Enhanced version
        "enhanced_features": {
            "file_based_storage": ENHANCED_AUDIT_AVAILABLE,
            "risk_assessment": True,
            "suspicious_activity_detection": True,
            "identity_provider_integrations": True,
            "bulk_event_processing": True,
            "advanced_analytics": ENHANCED_AUDIT_AVAILABLE,
            "real_time_monitoring": True,
            "compliance_frameworks": ["SOX", "PCI-DSS", "GDPR", "SOC2"],
            "storage_location": "essentials/audit/",
            "supported_formats": ["JSONL", "JSON", "CSV"],
            "data_retention": "365 days",
            "compression": True,
            "encryption": True
        },
        "integrations": {
            "azure_ad": "/integrations/azure-ad",
            "okta": "/integrations/okta", 
            "adfs": "/integrations/adfs"
        },
        "endpoints": {
            "overview": "/",
            "create_event": "/events",
            "bulk_events": "/events/bulk",
            "query_events": "/events/query",
            "summary": "/summary",
            "risk_profiles": "/risk-profiles/{user_id}",
            "suspicious_activity": "/suspicious-activity",
            "storage_info": "/storage-info",
            "export": "/export",
            "health_check": "/health"
        }
    },
    
    "compliance": {
        "prefix": "/api/v1/compliance",
        "tags": ["compliance", "governance"],
        "description": "Compliance framework management and assessment",
        "category": "security", 
        "requires_auth": True,
        "version": "1.0.0",
        "depends_on": ["audit"]  # Enhanced compliance depends on audit
    },
    "threat_detection": {
        "prefix": "/api/v1/threats",
        "tags": ["threat-detection", "security"],
        "description": "Threat detection and incident response",
        "category": "security",
        "requires_auth": True,
        "version": "1.0.0",
        "depends_on": ["audit"]  # Threat detection integrates with audit
    },
    
    # Network security functionality
    "netseg": {
        "prefix": "/api/v1/netseg",
        "tags": ["network-segmentation"],
        "description": "Network segmentation policies and microsegmentation",
        "category": "security",
        "requires_auth": True,
        "version": "1.0.0"
    },
    "log_management": {
        "prefix": "/api/v1/logs",
        "tags": ["log-management"],
        "description": "Log file processing and analysis",
        "category": "security",
        "requires_auth": True,
        "version": "1.0.0",
        "integrates_with": ["audit"]  # Log management feeds into audit
    },
    "analytics": {
        "prefix": "/api/v1/analytics",
        "tags": ["analytics"],
        "description": "Security analytics and traffic insights",
        "category": "security",
        "requires_auth": True,
        "version": "1.0.0",
        "data_sources": ["audit", "log_management"]
    },
    "reports": {
        "prefix": "/api/v1/reports", 
        "tags": ["reports"],
        "description": "Security and compliance reporting",
        "category": "security",
        "requires_auth": True,
        "version": "1.0.0",
        "data_sources": ["audit", "analytics", "compliance"]
    },
    
    # Utility routers
    "test": {
        "prefix": "/api/v1/test",
        "tags": ["testing", "quality-assurance"],
        "description": "Automated testing and validation endpoints",
        "category": "utility",
        "requires_auth": False,
        "version": "1.0.0"
    },
    "debug": {
        "prefix": "/api/v1/debug",
        "tags": ["debugging", "diagnostics"],
        "description": "Debugging and system information endpoints",
        "category": "utility", 
        "requires_auth": True,
        "version": "1.0.0"
    },
    
    # Optional routers
    "network_discovery": {
        "prefix": "/api/v1/discovery",
        "tags": ["network-discovery"],
        "description": "Advanced network asset discovery",
        "category": "security",
        "requires_auth": True,
        "optional": True,
        "version": "1.0.0"
    },
    "migration": {
        "prefix": "/api/v1/migration", 
        "tags": ["migration"],
        "description": "Application migration planning and execution",
        "category": "application",
        "requires_auth": True,
        "optional": True,
        "version": "1.0.0"
    },
    "app_rationalization": {
        "prefix": "/api/v1/apps",
        "tags": ["applications", "portfolio"],
        "description": "Application portfolio management and rationalization",
        "category": "application",
        "requires_auth": True,
        "optional": True,
        "version": "1.0.0"
    }
}

def get_available_routers():
    """Get list of available routers with their metadata"""
    available = []
    
    for router_name in __all__:
        if router_name.startswith('get_') or router_name.isupper():
            continue  # Skip utility functions and constants
            
        router_module = globals().get(router_name)
        if router_module is not None:
            metadata = ROUTER_METADATA.get(router_name, {})
            
            # Add runtime status information
            status = {
                "name": router_name,
                "module": router_module,
                "metadata": metadata,
                "status": "available"
            }
            
            # Special handling for enhanced audit system
            if router_name == "audit":
                status["enhanced_features_available"] = ENHANCED_AUDIT_AVAILABLE
                status["storage_components"] = {
                    "file_storage": ENHANCED_AUDIT_AVAILABLE,
                    "analytics_processor": ENHANCED_AUDIT_AVAILABLE
                }
            
            available.append(status)
    
    return available

def get_routers_by_category(category: str):
    """Get routers filtered by category"""
    return [
        router for router in get_available_routers()
        if router["metadata"].get("category") == category
    ]

def get_security_routers():
    """Get all security-related routers"""
    return get_routers_by_category("security")

def get_discovery_routers():
    """Get all discovery-related routers (legacy compatibility)"""
    return get_routers_by_category("core")

def get_utility_routers():
    """Get all utility routers (testing, debugging, health)"""
    return get_routers_by_category("utility")

def get_application_routers():
    """Get all application management routers"""
    return get_routers_by_category("application")

def get_audit_capabilities():
    """Get detailed audit system capabilities"""
    audit_metadata = ROUTER_METADATA.get("audit", {})
    
    capabilities = {
        "basic_audit": True,
        "enhanced_features_available": ENHANCED_AUDIT_AVAILABLE,
        "version": audit_metadata.get("version", "1.0.0"),
        "storage_type": "file_based" if ENHANCED_AUDIT_AVAILABLE else "memory",
        "features": audit_metadata.get("enhanced_features", {}),
        "integrations": audit_metadata.get("integrations", {}),
        "endpoints": audit_metadata.get("endpoints", {}),
        "compliance_frameworks": audit_metadata.get("enhanced_features", {}).get("compliance_frameworks", [])
    }
    
    if ENHANCED_AUDIT_AVAILABLE:
        capabilities["storage_info"] = {
            "location": "essentials/audit/",
            "formats": ["JSONL", "JSON", "CSV"],
            "compression": True,
            "retention_days": 365,
            "backup_enabled": True
        }
        
        capabilities["risk_assessment"] = {
            "real_time": True,
            "factors": ["geographic", "temporal", "device", "behavioral"],
            "risk_levels": ["low", "medium", "high", "critical"],
            "thresholds_configurable": True
        }
    
    return capabilities

def get_router_dependencies():
    """Get router dependency information for proper initialization order"""
    return {
        # Core routers (no dependencies)
        "health": [],
        "test": [],
        "topology": [],
        "integration": [],
        "documentation": [],
        "diagram": [],
        
        # Authentication must be first for security routers
        "auth": [],
        
        # Enhanced audit system (minimal dependencies)
        "audit": ["auth"] if ROUTER_METADATA["audit"]["requires_auth"] else [],
        
        # Security routers (require auth and often depend on audit)
        "debug": ["auth"],
        "compliance": ["auth", "audit"],  # Compliance benefits from audit data
        "threat_detection": ["auth", "audit"],  # Threat detection uses audit events
        "log_management": ["auth"],
        "netseg": ["auth", "log_management"],
        "analytics": ["auth", "log_management", "audit"],  # Analytics uses audit data
        "reports": ["auth", "analytics", "compliance", "audit"],  # Reports aggregate data
        
        # Optional routers
        "network_discovery": ["auth"],
        "migration": ["auth"],
        "app_rationalization": ["auth"]
    }

# Version information
__version__ = "2.1.0"  # Updated to reflect enhanced audit system
__author__ = "Banking Security Platform Team"
__description__ = "Integrated network discovery and security management platform with enhanced audit capabilities"

# Enhanced feature flags
FEATURES = {
    # Core features
    "network_topology": True,
    "documentation_generation": True,
    "system_integration": True,
    "diagram_creation": True,
    
    # Security features
    "authentication": True,
    "audit_logging": True,
    "enhanced_audit_system": ENHANCED_AUDIT_AVAILABLE,  # New feature flag
    "file_based_audit_storage": ENHANCED_AUDIT_AVAILABLE,  # New feature flag
    "audit_risk_assessment": True,  # New feature flag
    "suspicious_activity_detection": True,  # New feature flag
    "identity_provider_integrations": True,  # New feature flag
    "compliance_management": True,
    "threat_detection": True,
    "network_segmentation": True,
    "log_based_analysis": True,
    "security_analytics": True,
    "security_reporting": True,
    
    # Utility features
    "health_monitoring": True,
    "automated_testing": True,
    "debug_diagnostics": True,
    
    # Optional features (based on available modules)
    "advanced_discovery": network_discovery is not None,
    "migration_planning": migration is not None,
    "application_portfolio": app_rationalization is not None
}

def get_enabled_features():
    """Get dictionary of enabled features"""
    return {k: v for k, v in FEATURES.items() if v}

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled"""
    return FEATURES.get(feature_name, False)

# Enhanced initialization order (updated for audit dependencies)
INITIALIZATION_ORDER = [
    # Core system routers (no dependencies)
    "health",         # Health monitoring should be available first
    "test",           # Testing endpoints
    "topology",       # Core functionality
    "integration",    # Core functionality
    "documentation",  # Core functionality
    "diagram",        # Core functionality
    
    # Authentication (required for security features)
    "auth",           # Must be before security routers
    
    # Enhanced audit system (early in security chain)
    "audit",          # Enhanced audit logging with file storage
    
    # Other security features
    "debug",          # Debug (requires auth)
    "log_management", # Log processing
    "compliance",     # Compliance management (benefits from audit)
    "threat_detection", # Threat detection (integrates with audit)
    "netseg",         # Network segmentation
    "analytics",      # Security analytics (uses audit data)
    "reports",        # Reporting (aggregates all security data)
    
    # Optional application management
    "app_rationalization", # Application portfolio
    "migration",      # Migration planning
    "network_discovery" # Advanced discovery
]

def get_initialization_order():
    """Get the recommended order for router initialization"""
    available_routers = [r["name"] for r in get_available_routers()]
    return [router for router in INITIALIZATION_ORDER if router in available_routers]

# Enhanced API documentation grouping
API_GROUPS = {
    "Core Platform": {
        "description": "Core network discovery and documentation features",
        "routers": ["topology", "integration", "documentation", "diagram"]
    },
    "System Management": {
        "description": "System health, testing, and debugging utilities",
        "routers": ["health", "test", "debug"]
    },
    "Security & Authentication": {
        "description": "Authentication, authorization, and enhanced audit management",
        "routers": ["auth", "audit", "compliance", "threat_detection"],
        "enhanced_features": {
            "audit": ["file_based_storage", "risk_assessment", "identity_integrations"]
        }
    },
    "Network Security": {
        "description": "Network segmentation, monitoring, and analytics",
        "routers": ["netseg", "log_management", "analytics", "reports"]
    },
    "Application Management": {
        "description": "Application portfolio and migration management",
        "routers": ["app_rationalization", "migration"]
    },
    "Advanced Features": {
        "description": "Optional advanced security and discovery features",
        "routers": ["network_discovery"]
    }
}

def get_api_groups():
    """Get API documentation groups with available routers only"""
    available_router_names = [r["name"] for r in get_available_routers()]
    
    groups = {}
    for group_name, group_config in API_GROUPS.items():
        available_routers_in_group = [
            router for router in group_config["routers"] 
            if router in available_router_names
        ]
        
        if available_routers_in_group:  # Only include groups with available routers
            groups[group_name] = {
                "description": group_config["description"],
                "routers": available_routers_in_group
            }
            
            # Add enhanced feature information
            if "enhanced_features" in group_config:
                groups[group_name]["enhanced_features"] = group_config["enhanced_features"]
    
    return groups

def check_compatibility():
    """Check for compatibility issues between routers"""
    warnings = []
    
    # Check if auth router is available when security routers are present
    security_routers = get_security_routers()
    auth_available = any(r["name"] == "auth" for r in get_available_routers())
    
    if security_routers and not auth_available:
        warnings.append("Security routers detected but auth router not available")
    
    # Check for missing dependencies
    dependencies = get_router_dependencies()
    available_names = [r["name"] for r in get_available_routers()]
    
    for router_name, deps in dependencies.items():
        if router_name in available_names:
            for dep in deps:
                if dep not in available_names:
                    warnings.append(f"Router '{router_name}' requires '{dep}' but it's not available")
    
    # Check audit system specific compatibility
    if "audit" in available_names:
        if not ENHANCED_AUDIT_AVAILABLE:
            warnings.append("Basic audit router available but enhanced features (file storage, analytics) not installed")
        
        # Check if storage directory exists
        from pathlib import Path
        if not Path("essentials/audit").exists():
            warnings.append("Audit router available but storage directory not initialized")
    
    return warnings

def get_router_summary():
    """Get a comprehensive summary of router status"""
    available = get_available_routers()
    by_category = {}
    
    for router in available:
        category = router["metadata"].get("category", "unknown")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(router["name"])
    
    # Enhanced summary with audit system details
    summary = {
        "total_routers": len(available),
        "by_category": by_category,
        "enabled_features": len(get_enabled_features()),
        "initialization_order": get_initialization_order(),
        "compatibility_warnings": check_compatibility(),
        "version": __version__,
        "enhanced_audit": {
            "available": ENHANCED_AUDIT_AVAILABLE,
            "version": ROUTER_METADATA["audit"]["version"],
            "capabilities": get_audit_capabilities() if "audit" in [r["name"] for r in available] else None
        }
    }
    
    return summary

# Initialize compatibility check on import
_compatibility_warnings = check_compatibility()
if _compatibility_warnings:
    import warnings as python_warnings
    for warning in _compatibility_warnings:
        python_warnings.warn(f"Router compatibility issue: {warning}", UserWarning)

# Enhanced startup message
print(f"🔧 Router package initialized (v{__version__})")
print(f"📊 Available routers: {len(get_available_routers())}")
print(f"🔐 Security features: {'✅' if is_feature_enabled('authentication') else '❌'}")
print(f"🛡️ Enhanced audit system: {'✅' if ENHANCED_AUDIT_AVAILABLE else '⚠️ Basic only'}")
if is_feature_enabled('enhanced_audit_system'):
    print(f"📁 Audit storage: File-based (essentials/audit/)")
    print(f"🔍 Risk assessment: {'✅' if is_feature_enabled('audit_risk_assessment') else '❌'}")
if _compatibility_warnings:
    print(f"⚠️ Compatibility warnings: {len(_compatibility_warnings)}")