# services/__init__.py
"""
Services package initialization for Application Auto-Discovery Platform

This package contains all service classes for the integrated system.
"""

# Import all service classes
from .app_service import AppService
from .cost_service import CostService
from .migration_service import MigrationService
from .archetype_service import ArchetypeService

# Conditional AWS service import
try:
    from .aws_service import AWSService
    AWS_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AWS Service not available: {e}")
    
    # Fallback AWS service
    class AWSService:
        def __init__(self, *args, **kwargs):
            self.boto3_available = False
            
        async def calculate_cost_optimizations(self, applications):
            return {
                "total_current_monthly_cost": 0,
                "total_optimized_monthly_cost": 0,
                "total_monthly_savings": 0,
                "savings_percentage": 0,
                "optimizations_by_strategy": {},
                "recommendations": ["AWS service not available - running in simulation mode"],
                "roi_months": 12,
                "simulation_mode": True
            }
            
        async def assess_application_for_migration(self, application):
            from dataclasses import dataclass
            from enum import Enum
            
            class MigrationStrategy(Enum):
                REHOST = "rehost"
                REPLATFORM = "replatform"
                REFACTOR = "refactor"
                RETIRE = "retire"
                RETAIN = "retain"
                REPURCHASE = "repurchase"
                RELOCATE = "relocate"
            
            @dataclass
            class MigrationAssessment:
                application_name: str
                current_infrastructure: dict
                recommended_strategy: MigrationStrategy
                complexity_score: int
                estimated_effort_weeks: int
                estimated_cost_monthly: float
                dependencies: list
                compliance_requirements: list
            
            # Default assessment
            return MigrationAssessment(
                application_name=application.get('name', 'Unknown'),
                current_infrastructure={},
                recommended_strategy=MigrationStrategy.REHOST,
                complexity_score=5,
                estimated_effort_weeks=4,
                estimated_cost_monthly=1000.0,
                dependencies=[],
                compliance_requirements=[]
            )
    
    AWS_SERVICE_AVAILABLE = False

# Export the classes (either full or fallback)
__all__ = [
     # Service classes
    'AppService', 'CostService', 'MigrationService', 'ArchetypeService', 'AWSService',
    
    # Data classes
    'MigrationStrategy', 'MigrationAssessment',
    
    # Utility functions
    'get_all_services', 'get_available_services', 'initialize_services',
    'get_service_initialization_order', 'get_enabled_features', 'is_feature_enabled',
    
    # Constants
    'AWS_SERVICE_AVAILABLE', 'SERVICE_METADATA', 'FEATURES'
]

# Service metadata for dependency management
SERVICE_METADATA = {
    "AppService": {
        "description": "Application portfolio management and data services",
        "dependencies": [],
        "required": True
    },
    "CostService": {
        "description": "Migration cost calculation and optimization analysis",
        "dependencies": [],
        "required": True
    },
    "MigrationService": {
        "description": "Migration planning and wave generation services",
        "dependencies": ["AppService"],
        "required": True
    },
    "ArchetypeService": {
        "description": "Application archetype analysis and classification",
        "dependencies": [],
        "required": True
    },
    "AWSService": {
        "description": "AWS integration and cloud migration services",
        "dependencies": [],
        "required": False,
        "fallback_available": True
    }
}

def get_available_services():
    """Get list of available services with their status"""
    services = []
    
    for service_name in __all__:
        if service_name == 'AWS_SERVICE_AVAILABLE':
            continue
            
        service_class = globals().get(service_name)
        metadata = SERVICE_METADATA.get(service_name, {})
        
        status = "available"
        if service_name == "AWSService" and not AWS_SERVICE_AVAILABLE:
            status = "fallback"
        
        services.append({
            "name": service_name,
            "class": service_class,
            "metadata": metadata,
            "status": status
        })
    
    return services

def get_service_initialization_order():
    """Get recommended order for service initialization based on dependencies"""
    # Simple dependency resolution
    order = []
    remaining = list(__all__)
    remaining.remove('AWS_SERVICE_AVAILABLE')  # Not a service class
    
    while remaining:
        # Find services with no unresolved dependencies
        for service_name in remaining[:]:
            metadata = SERVICE_METADATA.get(service_name, {})
            dependencies = metadata.get("dependencies", [])
            
            # Check if all dependencies are already in order
            if all(dep in order for dep in dependencies):
                order.append(service_name)
                remaining.remove(service_name)
    
    return order

def initialize_services():
    """Initialize all services in proper dependency order"""
    services = {}
    
    for service_name in get_service_initialization_order():
        try:
            service_class = globals().get(service_name)
            if service_class:
                if service_name == "AWSService":
                    # AWS service may need special initialization
                    services[service_name] = service_class()
                else:
                    services[service_name] = service_class()
                
                print(f"✅ Initialized {service_name}")
        except Exception as e:
            print(f"❌ Failed to initialize {service_name}: {e}")
            # For critical services, this might raise an exception
            # For optional services, continue with fallback
            if SERVICE_METADATA.get(service_name, {}).get("required", True):
                raise
    
    return services

# Feature flags based on service availability
FEATURES = {
    "application_management": True,
    "cost_analysis": True,
    "migration_planning": True,
    "archetype_analysis": True,
    "aws_integration": AWS_SERVICE_AVAILABLE,
    "aws_simulation": not AWS_SERVICE_AVAILABLE
}

def get_enabled_features():
    """Get dictionary of enabled features"""
    return {k: v for k, v in FEATURES.items() if v}

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled"""
    return FEATURES.get(feature_name, False)

# Version information
__version__ = "2.0.0"
__author__ = "Application Auto-Discovery Platform Team"
__description__ = "Integrated application portfolio management and migration services"

# Convenience function for main.py
def get_all_services():
    """Get instances of all services for easy use in main.py"""
    return {
        'app_service': AppService(),
        'cost_service': CostService(),
        'migration_service': MigrationService(),
        'archetype_service': ArchetypeService(),
        'aws_service': AWSService()
    }

# Add convenience imports at package level
try:
    # Try to import from aws_service directly
    from .aws_service import MigrationStrategy, MigrationAssessment
except ImportError:
    # Create fallback classes
    from enum import Enum
    from dataclasses import dataclass
    
    class MigrationStrategy(Enum):
        REHOST = "rehost"
        REPLATFORM = "replatform"
        REFACTOR = "refactor"
        RETIRE = "retire"
        RETAIN = "retain"
        REPURCHASE = "repurchase"
        RELOCATE = "relocate"
    
    @dataclass
    class MigrationAssessment:
        application_name: str
        current_infrastructure: dict
        recommended_strategy: MigrationStrategy
        complexity_score: int
        estimated_effort_weeks: int
        estimated_cost_monthly: float
        dependencies: list
        compliance_requirements: list

# Export additional classes and functions
__all__.extend([
    'MigrationStrategy', 
    'MigrationAssessment', 
    'get_all_services', 
    'get_available_services', 
    'initialize_services',
    'get_service_initialization_order',
    'get_enabled_features',
    'is_feature_enabled',
    'SERVICE_METADATA',
    'FEATURES'
])