# routers/__init__.py
"""
Router package initialization for Banking Network Security & Discovery Platform

# routers/__init__.py - Updated with comprehensive router system

This package contains all API routers for the integrated system:
- Core application functionality (topology, integration, documentation)
- Authentication and authorization
- Health monitoring and system diagnostics
- Audit logging and compliance
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
from . import audit
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
    "audit",
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
        "requires_auth": False
    },
    "integration": {
        "prefix": "/api/v1/integration",
        "tags": ["integration"],
        "description": "System integrations and external connections", 
        "category": "core",
        "requires_auth": False
    },
    "documentation": {
        "prefix": "/api/v1/documentation",
        "tags": ["documentation"],
        "description": "Automated documentation generation",
        "category": "core",
        "requires_auth": False
    },
    "diagram": {
        "prefix": "/api/v1/diagram",
        "tags": ["diagram"],
        "description": "Network diagram creation and visualization",
        "category": "core", 
        "requires_auth": False
    },
    
    # Authentication and core security
    "auth": {
        "prefix": "/api/v1/auth",
        "tags": ["authentication"],
        "description": "Authentication and authorization services",
        "category": "security",
        "requires_auth": False  # Auth endpoints don't require authentication
    },
    "health": {
        "prefix": "/api/v1/health", 
        "tags": ["health", "monitoring"],
        "description": "Health monitoring and system diagnostics",
        "category": "utility",
        "requires_auth": False
    },
    "audit": {
        "prefix": "/api/v1/audit",
        "tags": ["audit", "logging"],
        "description": "Audit logging and event tracking",
        "category": "security",
        "requires_auth": True
    },
    "compliance": {
        "prefix": "/api/v1/compliance",
        "tags": ["compliance", "governance"],
        "description": "Compliance framework management and assessment",
        "category": "security", 
        "requires_auth": True
    },
    "threat_detection": {
        "prefix": "/api/v1/threats",
        "tags": ["threat-detection", "security"],
        "description": "Threat detection and incident response",
        "category": "security",
        "requires_auth": True
    },
    
    # Network security functionality
    "netseg": {
        "prefix": "/api/v1/netseg",
        "tags": ["network-segmentation"],
        "description": "Network segmentation policies and microsegmentation",
        "category": "security",
        "requires_auth": True
    },
    "log_management": {
        "prefix": "/api/v1/logs",
        "tags": ["log-management"],
        "description": "Log file processing and analysis",
        "category": "security",
        "requires_auth": True
    },
    "analytics": {
        "prefix": "/api/v1/analytics",
        "tags": ["analytics"],
        "description": "Security analytics and traffic insights",
        "category": "security",
        "requires_auth": True
    },
    "reports": {
        "prefix": "/api/v1/reports", 
        "tags": ["reports"],
        "description": "Security and compliance reporting",
        "category": "security",
        "requires_auth": True
    },
    
    # Utility routers
    "test": {
        "prefix": "/api/v1/test",
        "tags": ["testing", "quality-assurance"],
        "description": "Automated testing and validation endpoints",
        "category": "utility",
        "requires_auth": False
    },
    "debug": {
        "prefix": "/api/v1/debug",
        "tags": ["debugging", "diagnostics"],
        "description": "Debugging and system information endpoints",
        "category": "utility", 
        "requires_auth": True
    },
    
    # Optional routers
    "network_discovery": {
        "prefix": "/api/v1/discovery",
        "tags": ["network-discovery"],
        "description": "Advanced network asset discovery",
        "category": "security",
        "requires_auth": True,
        "optional": True
    },
    "migration": {
        "prefix": "/api/v1/migration", 
        "tags": ["migration"],
        "description": "Application migration planning and execution",
        "category": "application",
        "requires_auth": True,
        "optional": True
    },
    "app_rationalization": {
        "prefix": "/api/v1/apps",
        "tags": ["applications", "portfolio"],
        "description": "Application portfolio management and rationalization",
        "category": "application",
        "requires_auth": True,
        "optional": True
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
            available.append({
                "name": router_name,
                "module": router_module,
                "metadata": metadata
            })
    
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
        
        # Security routers (require auth)
        "audit": ["auth"],
        "debug": ["auth"],
        "compliance": ["auth", "audit"],
        "threat_detection": ["auth", "audit"],
        "log_management": ["auth"],
        "netseg": ["auth", "log_management"],
        "analytics": ["auth", "log_management"],
        "reports": ["auth", "analytics", "compliance"],
        
        # Optional routers
        "network_discovery": ["auth"],
        "migration": ["auth"],
        "app_rationalization": ["auth"]
    }

# Version information
__version__ = "2.0.0"
__author__ = "Banking Security Platform Team"
__description__ = "Integrated network discovery and security management platform"

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

# Enhanced initialization order
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
    
    # Basic security features
    "audit",          # Audit logging
    "debug",          # Debug (requires auth)
    
    # Advanced security features
    "log_management", # Log processing
    "compliance",     # Compliance management
    "threat_detection", # Threat detection
    "netseg",         # Network segmentation
    "analytics",      # Security analytics
    "reports",        # Reporting (requires analytics and compliance)
    
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
        "description": "Authentication, authorization, and security management",
        "routers": ["auth", "audit", "compliance", "threat_detection"]
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
    
    return {
        "total_routers": len(available),
        "by_category": by_category,
        "enabled_features": len(get_enabled_features()),
        "initialization_order": get_initialization_order(),
        "compatibility_warnings": check_compatibility(),
        "version": __version__
    }

# Initialize compatibility check on import
_compatibility_warnings = check_compatibility()
if _compatibility_warnings:
    import warnings as python_warnings
    for warning in _compatibility_warnings:
        python_warnings.warn(f"Router compatibility issue: {warning}", UserWarning)

print(f"🔧 Router package initialized (v{__version__})")
print(f"📊 Available routers: {len(get_available_routers())}")
print(f"🔐 Security features: {'✅' if is_feature_enabled('authentication') else '❌'}")
if _compatibility_warnings:
    print(f"⚠️ Compatibility warnings: {len(_compatibility_warnings)}")