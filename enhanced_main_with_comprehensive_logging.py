# enhanced_main_with_comprehensive_logging.py
"""
Enhanced main.py with comprehensive logging system integration
Includes ALL logging components:
- Uvicorn request/response logging
- Frontend logging collection
- ServiceNow incident management
- Role-based log access control
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
import os
import sys
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import comprehensive logging system
from services.comprehensive_logging_system import initialize_comprehensive_logging, get_comprehensive_logger
from middleware.logging_middleware import RequestResponseLoggingMiddleware

# Global logging system
comprehensive_logger = None

@asynccontextmanager
async def enhanced_lifespan(app: FastAPI):
    """Enhanced lifespan with comprehensive logging initialization"""
    global comprehensive_logger
    
    # STARTUP
    print("\n" + "="*80)
    print("🚀 STARTING ENHANCED APPLICATION WITH COMPREHENSIVE LOGGING")
    print("="*80)
    
    # Load configuration
    config = load_logging_configuration()
    
    # Initialize comprehensive logging system
    print("🔧 Initializing comprehensive logging system...")
    comprehensive_logger = initialize_comprehensive_logging(config)
    app.state.comprehensive_logger = comprehensive_logger
    
    # Start logging system components
    print("✅ Comprehensive logging system initialized")
    print(f"📊 Features enabled:")
    print(f"  - Uvicorn request/response logging: ✅")
    print(f"  - Frontend logging collection: ✅")
    print(f"  - Log classification & categorization: ✅")
    print(f"  - ServiceNow integration: {'✅' if config.get('servicenow', {}).get('enabled') else '❌'}")
    print(f"  - Role-based access control: ✅")
    print(f"  - Incident management: ✅")
    print(f"  - Log lifecycle management: ✅")
    
    # Initialize existing systems
    try:
        import routers
        print(f"🔧 Routers package: ✅ (v{getattr(routers, '__version__', 'unknown')})")
    except ImportError:
        print("🔧 Routers package: ❌ (basic mode)")
    
    print("\n📖 API Documentation: http://localhost:8001/docs")
    print("🔧 Health Check: http://localhost:8001/health") 
    print("📊 Logging Dashboard: http://localhost:8001/api/v1/logs")
    print("🎫 Incident Management: http://localhost:8001/api/v1/incidents")
    print("="*80)
    
    yield
    
    # SHUTDOWN
    print("\n🛑 Enhanced application shutting down...")
    if comprehensive_logger:
        print("✅ Comprehensive logging system shutdown complete")

def load_logging_configuration():
    """Load comprehensive logging configuration"""
    try:
        config = {}
        
        # Load main configuration
        main_config_path = "config/logging/comprehensive_config.yaml"
        if Path(main_config_path).exists():
            with open(main_config_path, 'r', encoding='utf-8') as f:
                config.update(yaml.safe_load(f))
        
        # Load ServiceNow configuration
        snow_config_path = "config/servicenow/servicenow_config.yaml"
        if Path(snow_config_path).exists():
            with open(snow_config_path, 'r', encoding='utf-8') as f:
                config.update(yaml.safe_load(f))
        
        # Load classification rules
        classification_config_path = "config/classification/classification_rules.yaml"
        if Path(classification_config_path).exists():
            with open(classification_config_path, 'r', encoding='utf-8') as f:
                config.update(yaml.safe_load(f))
        
        return config
        
    except Exception as e:
        print(f"⚠️ Error loading configuration: {e}")
        return {}

def create_enhanced_app() -> FastAPI:
    """Create FastAPI app with comprehensive logging"""
    
    app = FastAPI(
        title="Enhanced Application Auto-Discovery Platform",
        description="With comprehensive logging, incident management, and ServiceNow integration",
        version="2.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=enhanced_lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add comprehensive logging middleware (MUST BE FIRST)
    middleware_config = {
        'excluded_paths': ['/health', '/metrics', '/static'],
        'log_request_body': True,
        'log_response_body': False,
        'max_body_size': 10000
    }
    app.add_middleware(RequestResponseLoggingMiddleware, config=middleware_config)
    
    # Mount static files
    static_dir = project_root / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Include routers
    include_all_routers(app)
    
    # Add enhanced endpoints
    setup_enhanced_endpoints(app)
    
    return app

def include_all_routers(app: FastAPI):
    """Include all routers including comprehensive logging router"""
    
    try:
        # Include comprehensive logging router FIRST
        from routers.comprehensive_logging import router as logging_router
        app.include_router(
            logging_router,
            prefix="/api/v1/logs",
            tags=["comprehensive-logging", "incident-management"]
        )
        print("✅ Comprehensive logging router included")
        
        # Include existing routers
        import routers
        available_routers = routers.get_available_routers()
        initialization_order = routers.get_initialization_order()
        
        for router_name in initialization_order:
            try:
                router_info = next((r for r in available_routers if r["name"] == router_name), None)
                if router_info and router_info["module"] and router_name != "comprehensive_logging":
                    metadata = router_info["metadata"]
                    router_module = router_info["module"]
                    
                    if hasattr(router_module, 'router'):
                        app.include_router(
                            router_module.router,
                            prefix=metadata.get("prefix", f"/api/v1/{router_name}"),
                            tags=metadata.get("tags", [router_name])
                        )
                        print(f"  ✅ Included: {router_name}")
                        
            except Exception as e:
                print(f"  ❌ Failed to include {router_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error including routers: {e}")

def setup_enhanced_endpoints(app: FastAPI):
    """Setup enhanced endpoints"""
    
    @app.get("/")
    async def enhanced_root():
        return {
            "message": "Enhanced Application Auto-Discovery Platform",
            "version": "2.2.0",
            "features": [
                "Comprehensive Request/Response Logging",
                "Frontend Activity Tracking", 
                "Advanced Log Classification",
                "ServiceNow Incident Management",
                "Role-based Log Access Control",
                "Automated Incident Detection",
                "Log Lifecycle Management"
            ],
            "logging_endpoints": {
                "query_logs": "/api/v1/logs/query",
                "search_logs": "/api/v1/logs/search", 
                "log_statistics": "/api/v1/logs/statistics",
                "create_incident": "/api/v1/logs/incidents/create",
                "list_incidents": "/api/v1/logs/incidents",
                "system_health": "/api/v1/logs/system/health"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/health")
    async def enhanced_health():
        comprehensive_logger = get_comprehensive_logger()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.2.0",
            "comprehensive_logging": {
                "status": "available" if comprehensive_logger else "unavailable",
                "queue_size": comprehensive_logger.log_queue.qsize() if comprehensive_logger else 0,
                "servicenow_enabled": comprehensive_logger.snow_integration.enabled if comprehensive_logger else False
            }
        }
        
        return health_data

# Create the enhanced app
app = create_enhanced_app()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Application Auto-Discovery Platform")
    print("🔧 With Comprehensive Logging System")
    
    uvicorn.run(
        "enhanced_main_with_comprehensive_logging:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(project_root)],
        log_level="info"
    )
