"""
App Rationalization Router
Handles application portfolio management and 7 Rs migration analysis
Integrates with existing banking network security platform
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Import your existing auth system
from routers.auth import get_current_user, require_admin

router = APIRouter()

# Pydantic models for App Rationalization
class Application(BaseModel):
    id: str
    name: str
    archetype: str
    strategy: str
    complexity: str
    risk: str
    estimated_cost: float
    timeline_months: int
    annual_savings: float
    technology_stack: Optional[str] = None
    business_criticality: Optional[str] = None
    dependencies: Optional[List[str]] = []

class ApplicationFilter(BaseModel):
    app_ids: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    archetypes: Optional[List[str]] = None
    complexity_levels: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None

class MigrationRequest(BaseModel):
    applications: List[str]
    strategies: List[str]
    approach: str = "phased"  # "phased" or "bigbang"
    target_cloud: str = "aws"
    budget_limit: Optional[float] = None
    timeline_constraint: Optional[int] = None  # months

class ApplicationPortfolio(BaseModel):
    applications: List[Application]
    total_count: int
    strategy_distribution: dict
    archetype_distribution: dict
    complexity_distribution: dict

# Initialize data paths
DATA_FOLDER = Path("static/ui/data")
APP_LIST_FILE = DATA_FOLDER / "applicationList.csv"
ARCHETYPE_FILE = DATA_FOLDER / "synthetic_flows_apps_archetype_mapped.xlsx"

@router.get("/portfolio", response_model=ApplicationPortfolio)
async def get_application_portfolio(
    current_user: dict = Depends(get_current_user)
):
    """Get complete application portfolio with 7 Rs analysis"""
    try:
        from services.appRationalization import AppRationalizationService
        
        service = AppRationalizationService()
        portfolio = await service.get_portfolio()
        
        return portfolio
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio: {str(e)}")

@router.get("/applications", response_model=List[Application])
async def get_applications(
    app_ids: Optional[str] = None,
    strategy: Optional[str] = None,
    archetype: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get filtered list of applications"""
    try:
        from services.appRationalization import AppRationalizationService
        
        service = AppRationalizationService()
        
        filters = ApplicationFilter(
            app_ids=app_ids.split(',') if app_ids else None,
            strategies=[strategy] if strategy else None,
            archetypes=[archetype] if archetype else None
        )
        
        applications = await service.get_filtered_applications(filters)
        return applications
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error filtering applications: {str(e)}")

@router.get("/applications/{app_id}", response_model=Application)
async def get_application(
    app_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific application details"""
    try:
        from services.appRationalization import AppRationalizationService
        
        service = AppRationalizationService()
        application = await service.get_application_by_id(app_id)
        
        if not application:
            raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving application: {str(e)}")

@router.post("/applications/{app_id}/strategy")
async def update_application_strategy(
    app_id: str,
    strategy: str,
    current_user: dict = Depends(require_admin)
):
    """Update migration strategy for an application (Admin only)"""
    try:
        from services.appRationalization import AppRationalizationService
        
        valid_strategies = ['rehost', 'replatform', 'refactor', 'retire', 'retain', 'repurchase', 'relocate']
        if strategy.lower() not in valid_strategies:
            raise HTTPException(status_code=400, detail=f"Invalid strategy. Must be one of: {valid_strategies}")
        
        service = AppRationalizationService()
        updated_app = await service.update_strategy(app_id, strategy)
        
        return {
            "message": f"Strategy updated for {app_id}",
            "application": updated_app,
            "updated_by": current_user["display_name"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating strategy: {str(e)}")

@router.post("/migration/analysis")
async def analyze_migration(
    request: MigrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Perform comprehensive migration analysis with cost quantification"""
    try:
        # Use the full implementations from snake_case files
        from services.migration_service import MigrationService
        from services.cost_service import CostService
        
        migration_service = MigrationService()
        cost_service = CostService()
        
        # Perform migration analysis
        analysis = await migration_service.analyze_migration(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach,
            target_cloud=request.target_cloud
        )
        
        # Calculate detailed costs
        cost_analysis = await cost_service.calculate_migration_costs(
            applications=analysis.get('applications', []),
            approach=request.approach,
            target_cloud=request.target_cloud
        )
        
        # Merge cost data into analysis
        analysis['costs'] = cost_analysis['breakdown']
        analysis['roi_analysis'] = cost_analysis.get('roi', {})
        analysis['analyzed_by'] = current_user["display_name"]
        analysis['analyzed_at'] = datetime.utcnow().isoformat()
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing migration: {str(e)}")

@router.post("/migration/costs")
async def calculate_migration_costs(
    request: MigrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate detailed migration costs and AWS optimization opportunities"""
    try:
        from services.cost_service import CostService
        from services.aws_service import AWSService
        
        cost_service = CostService()
        aws_service = AWSService()
        
        # Get applications for cost calculation
        applications = await cost_service.get_applications_for_cost_analysis(request.applications)
        
        # Calculate migration costs
        migration_costs = await cost_service.calculate_migration_costs(
            applications=applications,
            approach=request.approach,
            target_cloud=request.target_cloud
        )
        
        # Calculate operational costs and savings
        operational_analysis = await cost_service.calculate_operational_costs(
            applications=applications,
            target_cloud=request.target_cloud
        )
        
        # Get AWS-specific cost optimizations
        aws_optimizations = await aws_service.calculate_cost_optimizations(applications)
        
        # Calculate ROI
        roi_analysis = await cost_service.calculate_roi(
            migration_costs=migration_costs['total'],
            annual_savings=operational_analysis['annual_savings'],
            timeline_years=3
        )
        
        return {
            "migration_costs": migration_costs['breakdown'],
            "operational_costs": operational_analysis,
            "savings": operational_analysis['savings_breakdown'],
            "roi_analysis": roi_analysis,
            "aws_cost_optimization": aws_optimizations,
            "calculated_by": current_user["display_name"],
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating costs: {str(e)}")

@router.post("/migration/waves")
async def generate_migration_waves(
    request: MigrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate migration waves based on dependencies and risk"""
    try:
        from services.migrationService import MigrationService
        
        service = MigrationService()
        waves = await service.generate_migration_waves(
            app_ids=request.applications,
            approach=request.approach,
            timeline_constraint=request.timeline_constraint
        )
        
        return {
            "approach": request.approach,
            "total_waves": len(waves),
            "total_duration_months": sum(getattr(wave, 'duration_months', 6) for wave in waves),
            "waves": waves,
            "generated_by": current_user["display_name"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating waves: {str(e)}")

@router.post("/recommendations")
async def get_migration_recommendations(
    request: MigrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get AI-powered migration recommendations"""
    try:
        from services.migrationService import MigrationService
        
        service = MigrationService()
        recommendations = await service.generate_recommendations(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach,
            budget_limit=request.budget_limit
        )
        
        return {
            "recommendations": recommendations,
            "confidence_score": recommendations.get("confidence", 0.85),
            "generated_by": current_user["display_name"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/strategies")
async def get_migration_strategies(
    current_user: dict = Depends(get_current_user)
):
    """Get all 7 Rs migration strategies with descriptions"""
    strategies = {
        "rehost": {
            "name": "Rehost (Lift & Shift)",
            "description": "Move applications to cloud with minimal changes",
            "effort": "Low",
            "risk": "Low",
            "time_to_value": "Fast",
            "cost_savings": "Moderate",
            "typical_use_cases": ["Legacy applications", "Quick cloud adoption", "Cost reduction focus"]
        },
        "replatform": {
            "name": "Replatform",
            "description": "Move to cloud with some optimization",
            "effort": "Medium",
            "risk": "Medium", 
            "time_to_value": "Medium",
            "cost_savings": "High",
            "typical_use_cases": ["Database migrations", "Container adoption", "Managed services"]
        },
        "refactor": {
            "name": "Refactor/Re-architect",
            "description": "Redesign application for cloud-native architecture",
            "effort": "High",
            "risk": "High",
            "time_to_value": "Slow",
            "cost_savings": "Very High",
            "typical_use_cases": ["Microservices", "Serverless", "Modern architectures"]
        },
        "retire": {
            "name": "Retire",
            "description": "Decommission applications no longer needed",
            "effort": "Low",
            "risk": "Low",
            "time_to_value": "Immediate",
            "cost_savings": "Very High",
            "typical_use_cases": ["Redundant systems", "End-of-life applications", "Consolidation"]
        },
        "retain": {
            "name": "Retain",
            "description": "Keep applications on-premises for now",
            "effort": "None",
            "risk": "None",
            "time_to_value": "None",
            "cost_savings": "None",
            "typical_use_cases": ["Compliance requirements", "Recent investments", "Dependencies"]
        },
        "repurchase": {
            "name": "Repurchase",
            "description": "Replace with SaaS or cloud-native solution",
            "effort": "Medium",
            "risk": "Medium",
            "time_to_value": "Fast",
            "cost_savings": "High",
            "typical_use_cases": ["COTS replacement", "SaaS adoption", "Vendor solutions"]
        },
        "relocate": {
            "name": "Relocate",
            "description": "Move to cloud with hypervisor-level changes",
            "effort": "Low",
            "risk": "Low",
            "time_to_value": "Fast",
            "cost_savings": "Moderate",
            "typical_use_cases": ["VMware workloads", "Hybrid scenarios", "Infrastructure focus"]
        }
    }
    return strategies

@router.get("/archetypes")
async def get_archetypes(
    current_user: dict = Depends(get_current_user)
):
    """Get all application archetypes with their characteristics"""
    try:
        from services.archetype_service import ArchetypeService
        
        service = ArchetypeService()
        archetypes = await service.get_archetypes()
        return archetypes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving archetypes: {str(e)}")

@router.post("/refresh")
async def refresh_application_data(
    current_user: dict = Depends(require_admin)
):
    """Refresh application data from source files (Admin only)"""
    try:
        from services.appRationalization import AppRationalizationService
        
        service = AppRationalizationService()
        result = await service.refresh_data()
        
        return {
            "message": "Application data refreshed successfully",
            "applications_loaded": result.get("count", 0),
            "timestamp": result.get("timestamp"),
            "refreshed_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}")

@router.post("/export")
async def export_analysis(
    format: str = "excel",  # "excel", "pdf", "json"
    app_ids: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export app rationalization analysis"""
    try:
        if format not in ["excel", "pdf", "json"]:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        from services.appRationalization import AppRationalizationService
        
        service = AppRationalizationService()
        export_result = await service.export_analysis(app_ids or [], format)
        
        return {
            "message": "Analysis exported successfully",
            "export_path": export_result["file_path"],
            "export_format": format,
            "file_size": export_result.get("file_size"),
            "exported_by": current_user["display_name"],
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting analysis: {str(e)}")

@router.get("/health")
async def app_rationalization_health_check():
    """Health check for app rationalization service"""
    try:
        data_status = {
            "application_list_file": APP_LIST_FILE.exists(),
            "archetype_file": ARCHETYPE_FILE.exists(),
            "data_folder": DATA_FOLDER.exists()
        }
        
        return {
            "status": "healthy" if all(data_status.values()) else "degraded",
            "service": "app_rationalization",
            "data_sources": {
                "application_list": str(APP_LIST_FILE),
                "archetype_mapping": str(ARCHETYPE_FILE)
            },
            "data_status": data_status,
            "features": {
                "portfolio_management": "active",
                "migration_analysis": "active",
                "cost_calculation": "active",
                "strategy_recommendations": "active"
            },
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "app_rationalization",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }