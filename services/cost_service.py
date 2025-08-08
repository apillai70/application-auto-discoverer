"""
Cost Service
Handles detailed AWS migration cost calculations and optimization analysis
"""

import math
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import datetime
import asyncio

class MigrationStrategy(Enum):
    REHOST = "rehost"
    REPLATFORM = "replatform" 
    REFACTOR = "refactor"
    RETIRE = "retire"
    RETAIN = "retain"
    REPURCHASE = "repurchase"
    RELOCATE = "relocate"

class ApplicationComplexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class AWSCostFactors:
    """AWS-specific cost factors for migration calculations"""
    
    # EC2 instance costs (monthly, USD)
    ec2_small: float = 73.00    # t3.medium
    ec2_medium: float = 146.00  # t3.large
    ec2_large: float = 292.00   # t3.xlarge
    ec2_xlarge: float = 584.00  # t3.2xlarge
    
    # RDS costs (monthly, USD)
    rds_small: float = 144.00   # db.t3.medium
    rds_medium: float = 288.00  # db.t3.large
    rds_large: float = 576.00   # db.t3.xlarge
    
    # Storage costs (monthly per GB, USD)
    ebs_gp3: float = 0.08
    s3_standard: float = 0.023
    s3_ia: float = 0.0125
    
    # Network costs (per GB, USD)
    data_transfer_out: float = 0.09
    data_transfer_in: float = 0.00  # Free
    
    # Load balancer costs (monthly, USD)
    alb_monthly: float = 16.43
    nlb_monthly: float = 16.43
    
    # Lambda costs
    lambda_requests: float = 0.0000002  # Per request
    lambda_gb_second: float = 0.0000166667  # Per GB-second
    
    # Container costs (ECS/EKS)
    ecs_fargate_vcpu_hour: float = 0.04048
    ecs_fargate_gb_hour: float = 0.004445
    eks_cluster_hour: float = 0.10
    
    # Migration tool costs
    dms_instance_hour: float = 0.154  # dms.t3.medium
    datasync_gb: float = 0.0125
    migration_hub_free: bool = True
    
    # Professional services (hourly rates)
    solutions_architect: float = 300.00
    migration_specialist: float = 250.00
    devops_engineer: float = 200.00
    
    # Cost optimization factors
    reserved_instance_discount: float = 0.35  # 35% discount
    savings_plan_discount: float = 0.30  # 30% discount
    spot_instance_discount: float = 0.70  # 70% discount

class CostService:
    """Service for calculating AWS migration costs with detailed quantification"""
    
    def __init__(self):
        self.aws_costs = AWSCostFactors()
        self.migration_complexity_multipliers = {
            ApplicationComplexity.LOW: 1.0,
            ApplicationComplexity.MEDIUM: 1.5,
            ApplicationComplexity.HIGH: 2.0,
            ApplicationComplexity.VERY_HIGH: 3.0
        }
        
    async def calculate_migration_costs(
        self, 
        applications: List[Dict], 
        approach: str = "phased",
        target_cloud: str = "aws"
    ) -> Dict[str, Any]:
        """Calculate comprehensive migration costs"""
        
        total_costs = {
            "rehost": 0,
            "replatform": 0, 
            "refactor": 0,
            "retire": 0,
            "retain": 0,
            "repurchase": 0,
            "relocate": 0
        }
        
        detailed_breakdown = {
            "infrastructure_setup": 0,
            "migration_tools": 0,
            "professional_services": 0,
            "application_migration": 0,
            "testing_validation": 0,
            "training": 0,
            "contingency": 0
        }
        
        # Calculate per-application costs
        for app in applications:
            strategy = app.get("strategy", "rehost").lower()
            complexity = app.get("complexity", "medium").lower()
            
            app_cost = await self._calculate_application_migration_cost(
                app, strategy, complexity, approach
            )
            
            total_costs[strategy] += app_cost["total"]
            
            # Add to detailed breakdown
            for category, cost in app_cost["breakdown"].items():
                if category in detailed_breakdown:
                    detailed_breakdown[category] += cost
        
        # Apply approach-specific multipliers
        if approach == "bigbang":
            # Big bang requires more parallel resources and coordination
            detailed_breakdown["professional_services"] *= 1.4
            detailed_breakdown["testing_validation"] *= 1.3
            detailed_breakdown["infrastructure_setup"] *= 1.2
        
        # Add contingency (15% for phased, 20% for big bang)
        contingency_rate = 0.20 if approach == "bigbang" else 0.15
        subtotal = sum(detailed_breakdown.values())
        detailed_breakdown["contingency"] = subtotal * contingency_rate
        
        total_migration_cost = sum(detailed_breakdown.values())
        
        return {
            "total": total_migration_cost,
            "breakdown": detailed_breakdown,
            "by_strategy": total_costs,
            "approach": approach,
            "contingency_rate": contingency_rate,
            "currency": "USD"
        }
    
    async def _calculate_application_migration_cost(
        self, 
        app: Dict, 
        strategy: str, 
        complexity: str,
        approach: str
    ) -> Dict[str, Any]:
        """Calculate migration cost for a single application"""
        
        complexity_enum = ApplicationComplexity(complexity.lower())
        multiplier = self.migration_complexity_multipliers[complexity_enum]
        
        # Base costs by strategy (in USD)
        base_costs = {
            "rehost": {
                "infrastructure_setup": 5000 * multiplier,
                "migration_tools": 2000 * multiplier,
                "professional_services": 15000 * multiplier,
                "application_migration": 8000 * multiplier,
                "testing_validation": 5000 * multiplier,
                "training": 2000 * multiplier
            },
            "replatform": {
                "infrastructure_setup": 8000 * multiplier,
                "migration_tools": 4000 * multiplier,
                "professional_services": 25000 * multiplier,
                "application_migration": 15000 * multiplier,
                "testing_validation": 10000 * multiplier,
                "training": 5000 * multiplier
            },
            "refactor": {
                "infrastructure_setup": 15000 * multiplier,
                "migration_tools": 8000 * multiplier,
                "professional_services": 50000 * multiplier,
                "application_migration": 35000 * multiplier,
                "testing_validation": 20000 * multiplier,
                "training": 10000 * multiplier
            },
            "retire": {
                "infrastructure_setup": 0,
                "migration_tools": 1000,
                "professional_services": 3000 * multiplier,
                "application_migration": 2000 * multiplier,
                "testing_validation": 1000,
                "training": 500
            },
            "retain": {
                "infrastructure_setup": 0,
                "migration_tools": 0,
                "professional_services": 1000,
                "application_migration": 0,
                "testing_validation": 500,
                "training": 0
            },
            "repurchase": {
                "infrastructure_setup": 3000 * multiplier,
                "migration_tools": 2000,
                "professional_services": 20000 * multiplier,
                "application_migration": 10000 * multiplier,
                "testing_validation": 8000 * multiplier,
                "training": 8000 * multiplier
            },
            "relocate": {
                "infrastructure_setup": 3000 * multiplier,
                "migration_tools": 1500,
                "professional_services": 8000 * multiplier,
                "application_migration": 5000 * multiplier,
                "testing_validation": 3000 * multiplier,
                "training": 2000 * multiplier
            }
        }
        
        costs = base_costs.get(strategy, base_costs["rehost"])
        total = sum(costs.values())
        
        # Apply archetype-specific adjustments
        archetype = app.get("archetype", "").lower()
        if "microservices" in archetype:
            costs["infrastructure_setup"] *= 1.2  # More complex infrastructure
            costs["testing_validation"] *= 1.3   # More integration testing
        elif "monolithic" in archetype:
            costs["application_migration"] *= 1.4  # Harder to migrate
            costs["testing_validation"] *= 1.2
        elif "soa" in archetype:
            costs["professional_services"] *= 1.3  # Requires SOA expertise
        
        return {
            "total": sum(costs.values()),
            "breakdown": costs,
            "complexity": complexity,
            "strategy": strategy,
            "archetype": archetype
        }
    
    async def calculate_operational_costs(
        self, 
        applications: List[Dict], 
        target_cloud: str = "aws"
    ) -> Dict[str, Any]:
        """Calculate ongoing operational costs and savings"""
        
        current_costs = {
            "infrastructure": 0,
            "maintenance": 0,
            "licenses": 0,
            "support": 0,
            "utilities": 0
        }
        
        aws_costs = {
            "compute": 0,
            "storage": 0,
            "network": 0,
            "managed_services": 0,
            "support": 0
        }
        
        savings_breakdown = {
            "infrastructure_savings": 0,
            "license_savings": 0,
            "maintenance_savings": 0,
            "operational_efficiency": 0,
            "power_cooling_savings": 0
        }
        
        for app in applications:
            # Estimate current on-premises costs
            app_current = await self._estimate_current_costs(app)
            app_aws = await self._estimate_aws_costs(app)
            
            # Add to totals
            for category, cost in app_current.items():
                current_costs[category] += cost
            
            for category, cost in app_aws.items():
                aws_costs[category] += cost
        
        # Calculate savings
        total_current = sum(current_costs.values())
        total_aws = sum(aws_costs.values())
        
        # Apply AWS cost optimizations
        optimized_aws_costs = await self._apply_aws_optimizations(aws_costs)
        total_optimized_aws = sum(optimized_aws_costs.values())
        
        annual_savings = total_current - total_optimized_aws
        
        # Breakdown savings categories
        savings_breakdown["infrastructure_savings"] = current_costs["infrastructure"] * 0.4
        savings_breakdown["license_savings"] = current_costs["licenses"] * 0.3
        savings_breakdown["maintenance_savings"] = current_costs["maintenance"] * 0.5
        savings_breakdown["operational_efficiency"] = total_current * 0.15
        savings_breakdown["power_cooling_savings"] = current_costs["utilities"] * 0.8
        
        return {
            "current_annual_costs": current_costs,
            "aws_annual_costs": optimized_aws_costs,
            "annual_savings": annual_savings,
            "savings_breakdown": savings_breakdown,
            "savings_percentage": (annual_savings / total_current) * 100 if total_current > 0 else 0,
            "currency": "USD"
        }
    
    async def _estimate_current_costs(self, app: Dict) -> Dict[str, float]:
        """Estimate current on-premises costs for an application"""
        
        complexity = app.get("complexity", "medium").lower()
        archetype = app.get("archetype", "").lower()
        
        # Base monthly costs (USD)
        base_infrastructure = {
            "low": 5000,
            "medium": 12000,
            "high": 25000,
            "very_high": 45000
        }
        
        monthly_costs = {
            "infrastructure": base_infrastructure.get(complexity, 12000),
            "maintenance": base_infrastructure.get(complexity, 12000) * 0.3,
            "licenses": base_infrastructure.get(complexity, 12000) * 0.4,
            "support": base_infrastructure.get(complexity, 12000) * 0.2,
            "utilities": base_infrastructure.get(complexity, 12000) * 0.15
        }
        
        # Apply archetype adjustments
        if "microservices" in archetype:
            monthly_costs["infrastructure"] *= 1.3  # More instances
        elif "monolithic" in archetype:
            monthly_costs["licenses"] *= 1.4  # Expensive enterprise licenses
        
        # Convert to annual
        annual_costs = {k: v * 12 for k, v in monthly_costs.items()}
        return annual_costs
        
    async def export_cost_analysis(self, applications: List[Dict], format: str = "excel") -> Dict[str, Any]:
        """Export cost analysis to results folder structure"""
        
        try:
            # Use results folder structure
            base_results_dir = Path("results")
            
            if format == "excel":
                export_dir = base_results_dir / "excel"
            elif format == "pdf":
                export_dir = base_results_dir / "pdf"
            else:
                export_dir = base_results_dir / "document"
            
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cost_analysis_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == "excel":
                # Create comprehensive cost analysis Excel report
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Migration costs
                    migration_costs = await self.calculate_migration_costs(applications)
                    cost_df = pd.DataFrame([migration_costs["breakdown"]])
                    cost_df.to_excel(writer, sheet_name='Migration Costs', index=False)
                    
                    # Operational analysis
                    operational = await self.calculate_operational_costs(applications)
                    ops_df = pd.DataFrame([operational])
                    ops_df.to_excel(writer, sheet_name='Operational Costs', index=False)
                    
                    # ROI analysis
                    roi = await self.calculate_roi(
                        migration_costs["total"],
                        operational["annual_savings"]
                    )
                    roi_df = pd.DataFrame([roi])
                    roi_df.to_excel(writer, sheet_name='ROI Analysis', index=False)
                    
                    # Application-level breakdown
                    app_costs = []
                    for app in applications:
                        app_cost = await self._calculate_application_migration_cost(
                            app, app.get("strategy", "rehost"), app.get("complexity", "medium"), "phased"
                        )
                        app_costs.append({
                            "Application": app.get("name", app.get("id")),
                            "Strategy": app.get("strategy"),
                            "Complexity": app.get("complexity"),
                            "Migration_Cost": app_cost["total"],
                            "Annual_Savings": app.get("annual_savings", 0)
                        })
                    
                    if app_costs:
                        pd.DataFrame(app_costs).to_excel(writer, sheet_name='Application Breakdown', index=False)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir)
            }
            
        except Exception as e:
            raise Exception(f"Error exporting cost analysis: {str(e)}")
    
    async def _estimate_aws_costs(self, app: Dict) -> Dict[str, float]:
        """Estimate AWS costs for an application"""
        
        complexity = app.get("complexity", "medium").lower()
        strategy = app.get("strategy", "rehost").lower()
        archetype = app.get("archetype", "").lower()
        
        # Base monthly AWS costs by complexity
        if strategy == "rehost":
            # Lift and shift - similar resource requirements
            compute_monthly = {
                "low": self.aws_costs.ec2_small + self.aws_costs.rds_small,
                "medium": self.aws_costs.ec2_medium + self.aws_costs.rds_medium,
                "high": (self.aws_costs.ec2_large * 2) + self.aws_costs.rds_large,
                "very_high": (self.aws_costs.ec2_xlarge * 3) + (self.aws_costs.rds_large * 2)
            }
        elif strategy == "replatform":
            # Some optimization possible
            compute_monthly = {
                "low": self.aws_costs.ec2_small * 0.8 + self.aws_costs.rds_small,
                "medium": self.aws_costs.ec2_medium * 0.9 + self.aws_costs.rds_medium,
                "high": (self.aws_costs.ec2_large * 1.5) + self.aws_costs.rds_large,
                "very_high": (self.aws_costs.ec2_xlarge * 2) + (self.aws_costs.rds_large * 1.5)
            }
        elif strategy == "refactor":
            # Cloud-native, more efficient
            compute_monthly = {
                "low": self.aws_costs.ec2_small * 0.6,
                "medium": self.aws_costs.ec2_medium * 0.7,
                "high": self.aws_costs.ec2_large * 0.8,
                "very_high": (self.aws_costs.ec2_xlarge * 1.2)
            }
        else:
            compute_monthly = {"low": 0, "medium": 0, "high": 0, "very_high": 0}
        
        monthly_costs = {
            "compute": compute_monthly.get(complexity, compute_monthly["medium"]),
            "storage": 500 if complexity != "low" else 200,  # EBS + S3
            "network": 300 if complexity == "high" else 150,  # Data transfer
            "managed_services": 400 if strategy in ["replatform", "refactor"] else 100,
            "support": 200  # AWS support
        }
        
        # Apply archetype adjustments
        if "microservices" in archetype:
            monthly_costs["compute"] *= 1.2
            monthly_costs["managed_services"] *= 1.5  # More managed services
        elif "event-driven" in archetype:
            monthly_costs["managed_services"] *= 1.3  # SQS, SNS, Lambda
        
        # Convert to annual
        annual_costs = {k: v * 12 for k, v in monthly_costs.items()}
        
        return annual_costs
    
    async def _apply_aws_optimizations(self, aws_costs: Dict[str, float]) -> Dict[str, float]:
        """Apply AWS cost optimization strategies"""
        
        optimized_costs = aws_costs.copy()
        
        # Apply Reserved Instance savings on compute (assuming 60% RI coverage)
        ri_coverage = 0.6
        optimized_costs["compute"] = (
            aws_costs["compute"] * ri_coverage * (1 - self.aws_costs.reserved_instance_discount) +
            aws_costs["compute"] * (1 - ri_coverage)
        )
        
        # Apply storage optimization (intelligent tiering)
        optimized_costs["storage"] *= 0.85  # 15% savings from tiering
        
        # Apply network optimization
        optimized_costs["network"] *= 0.9  # 10% savings from optimization
        
        return optimized_costs
    
    async def calculate_roi(
        self, 
        migration_costs: float, 
        annual_savings: float, 
        timeline_years: int = 3
    ) -> Dict[str, Any]:
        """Calculate return on investment analysis"""
        
        # Calculate payback period
        payback_months = (migration_costs / annual_savings) * 12 if annual_savings > 0 else float('inf')
        
        # Calculate NPV (assuming 10% discount rate)
        discount_rate = 0.10
        npv = -migration_costs
        for year in range(1, timeline_years + 1):
            npv += annual_savings / ((1 + discount_rate) ** year)
        
        # Calculate IRR (simplified approximation)
        irr = (annual_savings / migration_costs) if migration_costs > 0 else 0
        
        # Total benefits over timeline
        total_savings = annual_savings * timeline_years
        net_benefit = total_savings - migration_costs
        roi_percentage = (net_benefit / migration_costs) * 100 if migration_costs > 0 else 0
        
        return {
            "migration_investment": migration_costs,
            "annual_savings": annual_savings,
            "timeline_years": timeline_years,
            "payback_period_months": min(payback_months, 999),  # Cap at reasonable number
            "total_savings": total_savings,
            "net_benefit": net_benefit,
            "roi_percentage": roi_percentage,
            "npv": npv,
            "irr_estimate": irr,
            "break_even_achieved": payback_months <= (timeline_years * 12),
            "currency": "USD"
        }
    
    async def get_applications_for_cost_analysis(self, app_ids: List[str]) -> List[Dict]:
        """Get application data needed for cost analysis"""
        # This would typically fetch from database
        # For now, return mock data based on your application list
        
        applications = []
        for app_id in app_ids:
            if app_id == "all":
                # Return all applications
                applications.extend(await self._get_all_applications())
            else:
                app_data = await self._get_application_data(app_id)
                if app_data:
                    applications.append(app_data)
        
        return applications
    
    async def _get_all_applications(self) -> List[Dict]:
        """Get all applications with their characteristics"""
        # Mock data - in production, this would come from your data sources
        return [
            {"id": "ACDA", "name": "ATM Check Card Disputes API", "archetype": "Microservices", 
             "strategy": "Replatform", "complexity": "Medium", "risk": "Medium"},
            {"id": "ALE", "name": "Advisor Locator Engine", "archetype": "Web + API Headless", 
             "strategy": "Rehost", "complexity": "Low", "risk": "Low"},
            # Add more applications...
        ]
    
    async def _get_application_data(self, app_id: str) -> Optional[Dict]:
        """Get specific application data"""
        apps = await self._get_all_applications()
        return next((app for app in apps if app["id"] == app_id), None)