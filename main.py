# main.py with App Factory Pattern

# =================== IMPORTS ===================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# =================== LIFESPAN EVENT HANDLER ===================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events"""
    
    # STARTUP
    print("\n" + "="*60)
    print("🚀 APPLICATION AUTO-DISCOVERY PLATFORM STARTING")
    print("="*60)
    
    # Check project structure
    print(f"📁 Project root: {project_root}")
    static_dir = project_root / "static"
    print(f"📁 Static files: {'✅' if static_dir.exists() else '❌'}")
    
    # Check routers
    try:
        import routers
        print(f"🔧 Routers package: ✅ (v{getattr(routers, '__version__', 'unknown')})")
        print(f"📊 Available routers: {len(routers.get_available_routers())}")
        print(f"🔐 Security features: {'✅' if routers.is_feature_enabled('network_segmentation') else '❌'}")
    except ImportError:
        print("🔧 Routers package: ❌ (running in basic mode)")
    
    print("\n📖 API Documentation: http://localhost:8001/docs")
    print("🔧 Health Check: http://localhost:8001/health")
    print("📋 API Info: http://localhost:8001/api/info")
    print("="*60)
    
    # Yield control to the application
    yield
    
    # SHUTDOWN
    print("\n🛑 Application Auto-Discovery Platform shutting down...")

# =================== APP FACTORY FUNCTION ===================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Application Auto-Discovery Platform with Network Security",
        description="Comprehensive application portfolio management with network segmentation",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files (with error handling)
    static_dir = project_root / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print(f"✅ Static files mounted from {static_dir}")
    else:
        print(f"⚠️ Static directory not found: {static_dir}")

    # Include routers
    include_routers_safely(app)
    
    # Add basic endpoints
    setup_basic_endpoints(app)
    
    # Add error handlers
    setup_error_handlers(app)
    
    return app

# =================== ROUTER INTEGRATION ===================

def include_routers_safely(app: FastAPI):
    """Safely include routers from the routers package"""
    try:
        # Import the routers package
        import routers
        
        print(f"🔧 Router package version: {getattr(routers, '__version__', 'unknown')}")
        print(f"📊 Available features: {list(routers.get_enabled_features().keys())}")
        
        # Get available routers in initialization order
        available_routers = routers.get_available_routers()
        initialization_order = routers.get_initialization_order()
        
        print(f"🚀 Found {len(available_routers)} available routers")
        
        # Include routers in proper order
        for router_name in initialization_order:
            try:
                router_info = next((r for r in available_routers if r["name"] == router_name), None)
                if router_info and router_info["module"]:
                    metadata = router_info["metadata"]
                    
                    # Get the router object from the module
                    router_module = router_info["module"]
                    if hasattr(router_module, 'router'):
                        app.include_router(
                            router_module.router,
                            prefix=metadata.get("prefix", f"/api/v1/{router_name}"),
                            tags=metadata.get("tags", [router_name])
                        )
                        print(f"  ✅ Included router: {router_name}")
                    else:
                        print(f"  ⚠️ Router module {router_name} has no 'router' attribute")
                        
            except Exception as e:
                print(f"  ❌ Failed to include router {router_name}: {e}")
        
        # Check for compatibility warnings
        warnings = routers.check_compatibility()
        if warnings:
            print("⚠️ Router compatibility warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import routers package: {e}")
        print("🔧 Creating basic routers...")
        return False
    except Exception as e:
        print(f"❌ Error setting up routers: {e}")
        return False

def setup_basic_endpoints(app: FastAPI):
    """Setup basic endpoints"""
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        try:
            import routers
            enabled_features = routers.get_enabled_features()
            api_groups = routers.get_api_groups()
        except:
            enabled_features = {"basic_api": True}
            api_groups = {"Basic API": {"description": "Basic endpoints", "routers": []}}
        
        return {
            "message": "Application Auto-Discovery Platform API",
            "version": "2.0.0",
            "status": "running",
            "features": enabled_features,
            "api_groups": api_groups,
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "info": "/api/info"
            },
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            import routers
            router_status = {
                "routers_available": len(routers.get_available_routers()),
                "features_enabled": len(routers.get_enabled_features()),
                "security_enabled": routers.is_feature_enabled("network_segmentation")
            }
        except:
            router_status = {"routers_available": 0, "basic_mode": True}
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": router_status,
            "version": "2.0.0"
        }

    @app.get("/api/info")
    async def api_info():
        """API information endpoint"""
        try:
            import routers
            capabilities = []
            
            if routers.is_feature_enabled("network_segmentation"):
                capabilities.append("Network Segmentation")
            if routers.is_feature_enabled("log_based_analysis"):
                capabilities.append("Log Analysis")
            if routers.is_feature_enabled("compliance_management"):
                capabilities.append("Compliance Management")
            if routers.is_feature_enabled("threat_detection"):
                capabilities.append("Threat Detection")
            
            # Always available capabilities
            capabilities.extend([
                "Application Portfolio Management",
                "Network Topology Discovery",
                "Documentation Generation"
            ])
            
        except:
            capabilities = ["Basic API", "Health Monitoring"]
        
        return {
            "platform": "Application Auto-Discovery with Network Security",
            "version": "2.0.0",
            "capabilities": capabilities,
            "supported_formats": ["JSON", "Excel", "PDF"],
            "last_updated": datetime.now().isoformat()
        }

    @app.get("/api/v1/dashboard/summary")
    async def get_basic_dashboard():
        """Basic dashboard when full services aren't available"""
        return {
            "overview": {
                "total_applications": 0,
                "status": "Service starting up",
                "last_updated": datetime.now().isoformat()
            },
            "message": "Dashboard data will be available once services are fully initialized",
            "available_endpoints": ["/docs", "/health", "/api/info"]
        }

    @app.post("/api/v1/export/cost-analysis")
    async def basic_export_endpoint():
        """Basic export endpoint"""
        return {
            "status": "service_initializing",
            "message": "Export functionality will be available once all services are loaded",
            "timestamp": datetime.now().isoformat()
        }

def setup_error_handlers(app: FastAPI):
    """Setup error handlers"""
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Endpoint not found",
                "message": "The requested endpoint is not available",
                "available_endpoints": ["/docs", "/health", "/api/info"],
                "timestamp": datetime.now().isoformat()
            }
        )

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat()
            }
        )

# =================== CREATE APP INSTANCE ===================

# Create the app instance
app = create_app()

# =================== MAIN EXECUTION ===================

if __name__ == "__main__":
    print("\n🚀 Starting ACTIVnet Auto-Discovery Platform")
    print("📊 Platform Features:")
    print("   - Application portfolio management")
    print("   - Network topology discovery")
    print("   - Documentation generation")
    
    try:
        import routers
        if routers.is_feature_enabled("network_segmentation"):
            print("   - Network segmentation analysis ✅")
        if routers.is_feature_enabled("log_based_analysis"):
            print("   - Log-based analysis ✅")
        if routers.is_feature_enabled("compliance_management"):
            print("   - Compliance management ✅")
        if routers.is_feature_enabled("threat_detection"):
            print("   - Threat detection ✅")
    except ImportError:
        print("   - Basic mode (router package not available)")
    
    print(f"\n📖 API Documentation: http://localhost:8001/docs")
    print(f"🔧 Health Check: http://localhost:8001/health")
    print(f"📋 API Info: http://localhost:8001/api/info")
    
    # Start the server
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        reload_dirs=[str(project_root)],
        log_level="info"
    )