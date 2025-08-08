"""
Application Auto-Discovery Platform
Main FastAPI application with integrated services
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import services using the package
from services import (
    CostService, 
    MigrationService, 
    AWSService, 
    ArchetypeService, 
    AppService,
    get_all_services,
    AWS_SERVICE_AVAILABLE
)

# Import routers
import routers

# Create FastAPI app
app = FastAPI(
    title="ACTIVnet Topology Discoverer Platform",
    description="Integrated application discovery, rationalization, and migration management platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",                    # Development
        "http://127.0.0.1:8001", 
        "http://localhost:8000",                    # Frontend
        "http://127.0.0.1:8000",
        "http://localhost:8002",                    # Updated frontend port
        "http://127.0.0.1:8002",
        "http://localhost:9000",                    # Combined proxy
        "http://127.0.0.1:9000",
        f"http://{os.getenv('SERVER_HOSTNAME', 'localhost')}:8001",  # Dynamic hostname
        # Add your ngrok domain for remote access
        "https://ethical-lately-racer.ngrok-free.app",
        "*"  # For development - tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services using the package helper
services = get_all_services()
cost_service = services['cost_service']
migration_service = services['migration_service'] 
aws_service = services['aws_service']
archetype_service = services['archetype_service']
app_service = services['app_service']

# Print service status
print("\n" + "="*60)
print("🚀 ACTIVnet APPLICATION AUTO-DISCOVERY PLATFORM")
print("="*60)
print(f"🔧 Services initialized:")
print(f"   - AWS Integration: {'✅ Full' if AWS_SERVICE_AVAILABLE else '⚠️  Simulation Mode'}")
print(f"   - Application Management: ✅ Available")
print(f"   - Cost Analysis: ✅ Available") 
print(f"   - Migration Planning: ✅ Available")
print(f"   - Archetype Analysis: ✅ Available")

# Check router availability
try:
    import routers
    print(f"   - Router System: ✅ (v{getattr(routers, '__version__', 'unknown')})")
    print(f"   - Available Routers: {len(routers.get_available_routers())}")
    if routers.is_feature_enabled('network_segmentation'):
        print(f"   - Network Segmentation: ✅ Enabled")
    if routers.is_feature_enabled('log_based_analysis'):
        print(f"   - Log Analysis: ✅ Enabled")
    if routers.is_feature_enabled('compliance_management'):
        print(f"   - Compliance Management: ✅ Enabled")
except ImportError:
    print(f"   - Router System: ⚠️  Basic Mode")

print(f"\n📖 API Documentation: http://localhost:8001/docs")
print(f"🔧 Health Check: http://localhost:8001/health") 
print(f"📋 API Info: http://localhost:8001/api/info")
print("="*60)

# Pydantic models for API requests
class FilterRequest(BaseModel):
    app_ids: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    archetypes: Optional[List[str]] = None
    complexity_levels: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None

class StrategyUpdateRequest(BaseModel):
    strategy: str

class ExportRequest(BaseModel):
    app_ids: Optional[List[str]] = None
    format: str = "excel"

class MigrationAnalysisRequest(BaseModel):
    app_ids: List[str]
    strategies: List[str]
    approach: str = "phased"

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with platform information"""
    try:
        import routers
        enabled_features = routers.get_enabled_features()
        api_groups = routers.get_api_groups()
        available_routers = [r["name"] for r in routers.get_available_routers()]
    except:
        enabled_features = {"basic_api": True}
        api_groups = {"Basic API": {"description": "Basic endpoints", "routers": []}}
        available_routers = []
    
    return {
        "message": "Application Auto-Discovery Platform API",
        "version": "2.0.0",
        "status": "running",
        "features": enabled_features,
        "api_groups": api_groups,
        "available_routers": available_routers,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "info": "/api/info",
            "applications": "/api/v1/applications",
            "cost_analysis": "/api/v1/analysis/cost",
            "aws_integration": "/api/v1/aws/cost-optimization"
        },
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test service connectivity
        portfolio = await app_service.get_portfolio()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "app_service": "healthy",
                "cost_service": "healthy",
                "migration_service": "healthy",
                "aws_service": "healthy" if aws_service.boto3_available else "simulation_mode",
                "archetype_service": "healthy"
            },
            "application_count": portfolio["total_count"]
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# =================== APPLICATION MANAGEMENT ENDPOINTS ===================

@app.get("/api/v1/applications")
async def get_applications():
    """Get all applications with portfolio analysis"""
    try:
        portfolio = await app_service.get_portfolio()
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/applications/filter")
async def filter_applications(filters: FilterRequest):
    """Get filtered applications based on criteria"""
    try:
        applications = await app_service.get_filtered_applications(filters)
        return {
            "applications": applications,
            "count": len(applications),
            "filters_applied": filters.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/applications/{app_id}")
async def get_application(app_id: str):
    """Get specific application by ID"""
    try:
        application = await app_service.get_application_by_id(app_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/applications/{app_id}/strategy")
async def update_application_strategy(app_id: str, request: StrategyUpdateRequest):
    """Update migration strategy for an application"""
    try:
        updated_app = await app_service.update_strategy(app_id, request.strategy)
        if not updated_app:
            raise HTTPException(status_code=404, detail="Application not found")
        return updated_app
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/applications/refresh")
async def refresh_application_data():
    """Refresh application data from source files"""
    try:
        result = await app_service.refresh_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== COST ANALYSIS ENDPOINTS ===================

@app.post("/api/v1/analysis/cost")
async def analyze_costs(request: MigrationAnalysisRequest):
    """Perform cost analysis for selected applications"""
    try:
        applications = await app_service.get_applications(request.app_ids)
        
        cost_analysis = await cost_service.calculate_migration_costs(
            applications=applications,
            approach=request.approach
        )
        
        operational_analysis = await cost_service.calculate_operational_costs(applications)
        
        # Calculate ROI
        migration_cost = cost_analysis["total"]
        annual_savings = operational_analysis["annual_savings"]
        roi_analysis = await cost_service.calculate_roi(migration_cost, annual_savings)
        
        return {
            "migration_costs": cost_analysis,
            "operational_analysis": operational_analysis,
            "roi_analysis": roi_analysis,
            "applications_analyzed": len(applications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== MIGRATION PLANNING ENDPOINTS ===================
# NOTE: Migration endpoints are now handled by the migration router
# Removed duplicates to avoid FastAPI operation ID conflicts:
# - /api/v1/analysis/migration -> routers/migration.py
# - /api/v1/migration/waves -> routers/migration.py  
# - /api/v1/migration/executive-summary -> routers/migration.py

# =================== AWS INTEGRATION ENDPOINTS ===================

@app.post("/api/v1/aws/cost-optimization")
async def aws_cost_optimization(app_ids: List[str] = Query(...)):
    """Calculate AWS cost optimizations"""
    try:
        applications = await app_service.get_applications(app_ids)
        
        cost_analysis = await aws_service.calculate_cost_optimizations(applications)
        
        return cost_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/aws/assessment")
async def assess_application_for_aws(app_id: str):
    """Assess application for AWS migration"""
    try:
        application = await app_service.get_application_by_id(app_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        assessment = await aws_service.assess_application_for_migration(application)
        
        # Convert dataclass to dict
        assessment_dict = {
            "application_name": assessment.application_name,
            "current_infrastructure": assessment.current_infrastructure,
            "recommended_strategy": assessment.recommended_strategy.value,
            "complexity_score": assessment.complexity_score,
            "estimated_effort_weeks": assessment.estimated_effort_weeks,
            "estimated_cost_monthly": assessment.estimated_cost_monthly,
            "dependencies": assessment.dependencies,
            "compliance_requirements": assessment.compliance_requirements
        }
        
        return assessment_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== ARCHETYPE ANALYSIS ENDPOINTS ===================

@app.get("/api/v1/archetypes")
async def get_archetypes():
    """Get all application archetypes"""
    try:
        archetypes = await archetype_service.get_archetypes()
        return archetypes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/archetypes/{archetype_name}")
async def get_archetype_details(archetype_name: str):
    """Get detailed information about a specific archetype"""
    try:
        details = await archetype_service.get_archetype_details(archetype_name)
        if not details:
            raise HTTPException(status_code=404, detail="Archetype not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/archetypes/{archetype}/recommend")
async def recommend_strategy_for_archetype(archetype: str):
    """Recommend migration strategy for archetype"""
    try:
        recommendation = await archetype_service.recommend_strategy(archetype)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/portfolio/archetype-analysis")
async def analyze_portfolio_archetypes(app_ids: Optional[List[str]] = None):
    """Analyze archetype distribution across portfolio"""
    try:
        if app_ids:
            applications = await app_service.get_applications(app_ids)
        else:
            portfolio = await app_service.get_portfolio()
            applications = portfolio["applications"]
        
        analysis = await archetype_service.analyze_portfolio_archetypes(applications)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== EXPORT ENDPOINTS ===================

@app.post("/api/v1/export/portfolio")
async def export_portfolio_analysis(request: ExportRequest):
    """Export portfolio analysis"""
    try:
        result = await app_service.export_portfolio(format=request.format)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/export/cost-analysis")
async def export_cost_analysis(request: ExportRequest):
    """Export cost analysis"""
    try:
        applications = await app_service.get_applications(request.app_ids or ["all"])
        result = await cost_service.export_cost_analysis(applications, format=request.format)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NOTE: /api/v1/export/migration-plan now handled by migration router

@app.post("/api/v1/export/archetype-analysis")
async def export_archetype_analysis(request: ExportRequest):
    """Export archetype analysis"""
    try:
        applications = await app_service.get_applications(request.app_ids or ["all"])
        result = await archetype_service.export_archetype_analysis(applications, format=request.format)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================== ROUTER INTEGRATION ===================

def include_routers_safely(app: FastAPI):
    """Safely include routers from the routers package (Enhanced from app-root)"""
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
        print("🔧 Running in basic mode...")
        return False
    except Exception as e:
        print(f"❌ Error setting up routers: {e}")
        return False

# Include routers using the enhanced function
print("\n" + "="*50)
print("🔧 INITIALIZING ROUTERS")
print("="*50)

router_success = include_routers_safely(app)

if router_success:
    print("✅ Router integration completed successfully")
else:
    print("⚠️  Running in basic mode without advanced routers")

# API information endpoint
@app.get("/api/info")
async def get_api_info():
    """Get API information and available endpoints"""
    try:
        import routers
        available_routers = [r["name"] for r in routers.get_available_routers()]
        api_groups = routers.get_api_groups()
        features = routers.get_enabled_features()
        
        # Get router capabilities
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
            "Cost Analysis & Optimization", 
            "Migration Planning",
            "Archetype Analysis",
            "AWS Integration"
        ])
        
    except Exception as e:
        print(f"Router info error: {e}")
        available_routers = []
        api_groups = {}
        features = {"basic_api": True}
        capabilities = ["Basic API", "Application Management", "Cost Analysis"]
    
    return {
        "platform": "Application Auto-Discovery Platform with Network Security",
        "version": "2.0.0",
        "available_routers": available_routers,
        "api_groups": api_groups,
        "features": features,
        "capabilities": capabilities,
        "core_endpoints": {
            "applications": "/api/v1/applications",
            "cost_analysis": "/api/v1/analysis/cost", 
            "aws_integration": "/api/v1/aws/cost-optimization",
            "archetypes": "/api/v1/archetypes",
            "export": "/api/v1/export/portfolio",
            "migration": "/api/v1/migration/waves",  # Now handled by router
            "topology": "/api/v1/topology",  # From router
            "compliance": "/api/v1/compliance"  # From router
        },
        "supported_formats": ["JSON", "Excel", "PDF"],
        "last_updated": datetime.now().isoformat()
    }

# Legacy compatibility for the original AppRationalizationService
class AppRationalizationService:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self):
        self.app_service = app_service
        
    async def get_portfolio(self):
        return await self.app_service.get_portfolio()
    
    async def get_all_applications(self):
        return await self.app_service.get_all_applications()
    
    async def get_application_by_id(self, app_id: str):
        return await self.app_service.get_application_by_id(app_id)
    
    async def update_strategy(self, app_id: str, strategy: str):
        return await self.app_service.update_strategy(app_id, strategy)
    
    async def refresh_data(self):
        return await self.app_service.refresh_data()

# Create legacy instance for backward compatibility
app_rationalization_service = AppRationalizationService()

# REMOVED: if __name__ == "__main__": uvicorn.run() 
# This is now handled by start_activnet_full.py using command line uvicorn