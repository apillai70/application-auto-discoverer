"""
Migration Router
Handles migration analysis, cost calculation, and strategy recommendations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

from services.migration_service import MigrationService
from services.cost_service import CostService
from services.aws_service import AWSService

router = APIRouter()

class MigrationRequest(BaseModel):
    applications: List[str]
    strategies: List[str]
    approach: str = "phased"  # "phased" or "bigbang"
    target_cloud: str = "aws"
    budget_limit: Optional[float] = None
    timeline_constraint: Optional[int] = None  # months

class MigrationWave(BaseModel):
    name: str
    duration_months: int
    start_month: int
    applications: List[str]
    focus: str
    migration_cost: float
    annual_savings: float
    aws_services: List[str]
    risk_level: str

class MigrationAnalysis(BaseModel):
    summary: Dict[str, Any]
    strategies: Dict[str, int]
    costs: Dict[str, float]
    waves: List[MigrationWave]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    timeline: Dict[str, Any]

class CostBreakdown(BaseModel):
    migration_costs: Dict[str, float]
    operational_costs: Dict[str, float]
    savings: Dict[str, float]
    roi_analysis: Dict[str, Any]
    aws_cost_optimization: Dict[str, Any]

@router.post("/analysis", response_model=MigrationAnalysis)
async def analyze_migration(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(MigrationService),
    cost_service: CostService = Depends(CostService)
):
    """Perform comprehensive migration analysis with cost quantification"""
    try:
        analysis = await migration_service.analyze_migration(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach,
            target_cloud=request.target_cloud
        )
        
        # Calculate detailed costs
        cost_analysis = await cost_service.calculate_migration_costs(
            applications=analysis['applications'],
            approach=request.approach,
            target_cloud=request.target_cloud
        )
        
        # Merge cost data into analysis
        analysis['costs'] = cost_analysis['breakdown']
        analysis['roi_analysis'] = cost_analysis['roi']
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing migration: {str(e)}")

@router.post("/costs", response_model=CostBreakdown)
async def calculate_migration_costs(
    request: MigrationRequest,
    cost_service: CostService = Depends(CostService),
    aws_service: AWSService = Depends(AWSService)
):
    """Calculate detailed migration costs and AWS optimization opportunities"""
    try:
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
        
        return CostBreakdown(
            migration_costs=migration_costs['breakdown'],
            operational_costs=operational_analysis,
            savings=operational_analysis['savings_breakdown'],
            roi_analysis=roi_analysis,
            aws_cost_optimization=aws_optimizations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating costs: {str(e)}")

@router.post("/waves")
async def generate_migration_waves(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(MigrationService)
):
    """Generate migration waves based on dependencies and risk"""
    try:
        waves = await migration_service.generate_migration_waves(
            app_ids=request.applications,
            approach=request.approach,
            timeline_constraint=request.timeline_constraint
        )
        
        return {
            "approach": request.approach,
            "total_waves": len(waves),
            "total_duration_months": sum(wave.duration_months for wave in waves),
            "waves": waves
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating waves: {str(e)}")

@router.post("/recommendations")
async def get_migration_recommendations(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(MigrationService)
):
    """Get AI-powered migration recommendations"""
    try:
        recommendations = await migration_service.generate_recommendations(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach,
            budget_limit=request.budget_limit
        )
        
        return {
            "recommendations": recommendations,
            "confidence_score": recommendations.get("confidence", 0.85),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.post("/optimize")
async def optimize_migration_plan(
    request: MigrationRequest,
    optimization_goals: List[str],  # ["cost", "time", "risk"]
    migration_service: MigrationService = Depends(MigrationService)
):
    """Optimize migration plan based on specified goals"""
    try:
        optimized_plan = await migration_service.optimize_migration_plan(
            app_ids=request.applications,
            approach=request.approach,
            goals=optimization_goals,
            budget_limit=request.budget_limit,
            timeline_constraint=request.timeline_constraint
        )
        
        return {
            "original_approach": request.approach,
            "optimized_plan": optimized_plan,
            "improvements": optimized_plan.get("improvements", {}),
            "trade_offs": optimized_plan.get("trade_offs", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing plan: {str(e)}")

@router.get("/aws/services")
async def get_aws_services_mapping(
    aws_service: AWSService = Depends(AWSService)
):
    """Get AWS services mapping for different migration strategies"""
    try:
        services = await aws_service.get_services_mapping()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving AWS services: {str(e)}")

@router.post("/aws/estimate")
async def estimate_aws_costs(
    application_ids: List[str],
    aws_service: AWSService = Depends(AWSService)
):
    """Estimate AWS costs for specific applications"""
    try:
        cost_estimate = await aws_service.estimate_costs(application_ids)
        return cost_estimate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating AWS costs: {str(e)}")

@router.post("/summary")
async def generate_executive_summary(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(MigrationService)
):
    """Generate executive summary for migration analysis"""
    try:
        summary = await migration_service.generate_executive_summary(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach
        )
        
        return {
            "executive_summary": summary,
            "key_metrics": summary.get("metrics", {}),
            "recommendations": summary.get("recommendations", []),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/strategies/{strategy}/details")
async def get_strategy_details(
    strategy: str,
    migration_service: MigrationService = Depends(MigrationService)
):
    """Get detailed information about a specific migration strategy"""
    try:
        details = await migration_service.get_strategy_details(strategy)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving strategy details: {str(e)}")

@router.post("/validate")
async def validate_migration_plan(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(MigrationService)
):
    """Validate migration plan for feasibility and risks"""
    try:
        validation = await migration_service.validate_migration_plan(
            app_ids=request.applications,
            strategies=request.strategies,
            approach=request.approach,
            timeline_constraint=request.timeline_constraint
        )
        
        return {
            "is_valid": validation.get("valid", False),
            "warnings": validation.get("warnings", []),
            "errors": validation.get("errors", []),
            "suggestions": validation.get("suggestions", []),
            "risk_score": validation.get("risk_score", 0.5)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating plan: {str(e)}")