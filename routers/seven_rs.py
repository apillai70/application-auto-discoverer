# routers/seven_rs.py
"""
7R's Analysis router for banking application modernization strategy
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

from services.seven_rs_service import SevenRsService
from routers.auth import get_current_user, require_admin

router = APIRouter()

# Pydantic models
class ApplicationInfo(BaseModel):
    application_id: str
    application_name: str
    current_archetype: str
    technology_stack: Optional[List[str]] = None
    business_criticality: str  # 'critical', 'important', 'standard', 'low'
    compliance_requirements: Optional[List[str]] = None
    current_hosting: str  # 'on_premises', 'colo', 'hybrid', 'cloud'

class StrategyRecommendation(BaseModel):
    application_id: str
    application_name: str
    current_archetype: str
    recommended_strategy: str  # One of the 7 R's
    rationale: str
    effort_estimate: str  # 'low', 'medium', 'high', 'very_high'
    business_value: str
    priority: str  # 'high', 'medium', 'low'
    estimated_cost: float
    timeline_weeks: int
    dependencies: Optional[List[str]] = None
    risks: Optional[List[str]] = None

class BusinessCase(BaseModel):
    strategy: str
    application_count: int
    total_cost: float
    annual_savings: float
    roi_percentage: float
    payback_period_months: int
    business_benefits: List[str]
    technical_benefits: List[str]
    risk_factors: List[str]

class MigrationPhase(BaseModel):
    phase_number: int
    phase_name: str
    duration_weeks: int
    applications: List[str]
    strategies: List[str]
    prerequisites: List[str]
    deliverables: List[str]
    success_criteria: List[str]

class SevenRsAnalysisRequest(BaseModel):
    application_ids: Optional[List[str]] = None  # If None, analyze all applications
    include_business_case: bool = True
    include_migration_roadmap: bool = True
    analysis_depth: str = "standard"  # 'basic', 'standard', 'comprehensive'
    custom_criteria: Optional[Dict[str, Any]] = None

@router.post("/analyze")
async def analyze_seven_rs(
    request: SevenRsAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
):
    """Generate comprehensive 7R's analysis for banking applications"""
    try:
        service = SevenRsService()
        analysis_job_id = await service.start_analysis(request, background_tasks)
        
        return {
            "message": "7R's analysis started",
            "job_id": analysis_job_id,
            "analysis_scope": len(request.application_ids) if request.application_ids else "all_applications",
            "analysis_depth": request.analysis_depth,
            "estimated_duration": "10-20 minutes",
            "started_at": datetime.utcnow().isoformat(),
            "started_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting 7R's analysis: {str(e)}")

@router.get("/analysis/{job_id}")
async def get_analysis_status(
    job_id: str,
    current_user: dict = Depends(require_admin)
):
    """Get status of 7R's analysis job"""
    try:
        service = SevenRsService()
        status = await service.get_analysis_status(job_id)
        
        return {
            "job_status": status,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analysis status: {str(e)}")

@router.get("/strategies/distribution")
async def get_strategy_distribution(
    filter_by_archetype: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """Get distribution of 7R strategies across applications"""
    try:
        service = SevenRsService()
        distribution = await service.get_strategy_distribution(filter_by_archetype)
        
        return {
            "strategy_distribution": distribution["distribution"],
            "total_applications": distribution["total_count"],
            "archetype_filter": filter_by_archetype,
            "summary_stats": distribution["stats"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting strategy distribution: {str(e)}")

@router.post("/recommendations/generate")
async def generate_recommendations(
    applications: List[ApplicationInfo],
    criteria_weights: Optional[Dict[str, float]] = None,
    current_user: dict = Depends(require_admin)
):
    """Generate 7R strategy recommendations for specific applications"""
    try:
        service = SevenRsService()
        recommendations = await service.generate_recommendations(applications, criteria_weights)
        
        return {
            "recommendations": recommendations,
            "application_count": len(applications),
            "criteria_weights": criteria_weights,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/recommendations/{application_id}")
async def get_application_recommendation(
    application_id: str,
    include_alternatives: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Get detailed recommendation for a specific application"""
    try:
        service = SevenRsService()
        recommendation = await service.get_application_recommendation(application_id, include_alternatives)
        
        return {
            "recommendation": recommendation,
            "include_alternatives": include_alternatives,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting application recommendation: {str(e)}")

@router.post("/business-case/generate")
async def generate_business_case(
    strategies: List[str],
    time_horizon_years: int = 3,
    include_risk_analysis: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Generate detailed business case for selected 7R strategies"""
    try:
        service = SevenRsService()
        business_case = await service.generate_business_case(strategies, time_horizon_years, include_risk_analysis)
        
        return {
            "business_case": business_case,
            "strategies_analyzed": strategies,
            "time_horizon_years": time_horizon_years,
            "include_risk_analysis": include_risk_analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating business case: {str(e)}")

@router.get("/business-case/compare")
async def compare_strategy_business_cases(
    strategy1: str,
    strategy2: str,
    application_count: Optional[int] = None,
    current_user: dict = Depends(require_admin)
):
    """Compare business cases between two 7R strategies"""
    try:
        service = SevenRsService()
        comparison = await service.compare_strategies(strategy1, strategy2, application_count)
        
        return {
            "comparison": comparison,
            "strategy1": strategy1,
            "strategy2": strategy2,
            "application_count": application_count,
            "compared_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing strategies: {str(e)}")

@router.get("/roadmap")
async def get_migration_roadmap(
    prioritization_method: str = "business_value",  # 'business_value', 'risk_based', 'dependencies'
    phase_duration_weeks: int = 12,
    current_user: dict = Depends(require_admin)
):
    """Get phased migration roadmap based on 7R strategies"""
    try:
        service = SevenRsService()
        roadmap = await service.generate_migration_roadmap(prioritization_method, phase_duration_weeks)
        
        return {
            "migration_roadmap": roadmap,
            "total_phases": len(roadmap["phases"]),
            "total_duration_weeks": roadmap["total_duration"],
            "prioritization_method": prioritization_method,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating migration roadmap: {str(e)}")

@router.post("/roadmap/customize")
async def customize_migration_roadmap(
    phase_configurations: List[Dict[str, Any]],
    constraints: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(require_admin)
):
    """Customize migration roadmap with specific phase configurations"""
    try:
        service = SevenRsService()
        custom_roadmap = await service.customize_roadmap(phase_configurations, constraints)
        
        return {
            "custom_roadmap": custom_roadmap,
            "phase_count": len(phase_configurations),
            "constraints_applied": constraints,
            "customized_at": datetime.utcnow().isoformat(),
            "customized_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error customizing roadmap: {str(e)}")

@router.get("/cost-analysis")
async def get_cost_analysis(
    strategy_filter: Optional[List[str]] = None,
    include_hidden_costs: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Get detailed cost analysis for 7R strategies"""
    try:
        service = SevenRsService()
        cost_analysis = await service.get_cost_analysis(strategy_filter, include_hidden_costs)
        
        return {
            "cost_analysis": cost_analysis,
            "strategy_filter": strategy_filter,
            "include_hidden_costs": include_hidden_costs,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost analysis: {str(e)}")

@router.post("/validate")
async def validate_strategy_assignments(
    application_strategies: Dict[str, str],  # application_id -> strategy
    current_user: dict = Depends(require_admin)
):
    """Validate proposed 7R strategy assignments"""
    try:
        service = SevenRsService()
        validation_result = await service.validate_assignments(application_strategies)
        
        return {
            "validation_result": validation_result,
            "applications_validated": len(application_strategies),
            "validation_passed": validation_result["overall_valid"],
            "warnings": validation_result["warnings"],
            "errors": validation_result["errors"],
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating strategy assignments: {str(e)}")

@router.get("/reports/executive-summary")
async def generate_executive_summary(
    include_charts: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Generate executive summary report for 7R's analysis"""
    try:
        service = SevenRsService()
        summary = await service.generate_executive_summary(include_charts)
        
        return {
            "executive_summary": summary,
            "include_charts": include_charts,
            "generated_at": datetime.utcnow().isoformat(),
            "generated_for": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating executive summary: {str(e)}")

@router.post("/export")
async def export_seven_rs_analysis(
    job_id: str,
    export_format: str = "excel",  # 'excel', 'pdf', 'json', 'powerpoint'
    include_charts: bool = True,
    current_user: dict = Depends(require_admin)
):
    """Export complete 7R's analysis in specified format"""
    try:
        if export_format not in ['excel', 'pdf', 'json', 'powerpoint']:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        service = SevenRsService()
        export_result = await service.export_analysis(job_id, export_format, include_charts)
        
        return {
            "message": "7R's analysis exported successfully",
            "export_path": export_result["file_path"],
            "export_format": export_format,
            "file_size": export_result["file_size"],
            "include_charts": include_charts,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting 7R's analysis: {str(e)}")

@router.get("/health")
async def seven_rs_health_check():
    """Health check for 7R's analysis service"""
    try:
        service = SevenRsService()
        health_status = await service.health_check()
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "service": "seven_rs_analysis",
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "seven_rs_analysis",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }