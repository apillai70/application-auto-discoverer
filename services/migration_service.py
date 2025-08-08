"""
Migration Service
Handles migration analysis, wave generation, and strategy recommendations
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime

from services.cost_service import CostService
from services.app_service import AppService

class MigrationApproach(Enum):
    PHASED = "phased"
    BIGBANG = "bigbang"

@dataclass
class MigrationWave:
    name: str
    duration_months: int
    start_month: int
    applications: List[str]
    focus: str
    migration_cost: float
    annual_savings: float
    aws_services: List[str]
    risk_level: str
    dependencies: List[str] = None

class MigrationService:
    """Service for migration analysis and planning"""
    
    def __init__(self):
        self.cost_service = CostService()
        self.app_service = AppService()
        
        # Migration strategy priorities (lower = higher priority)
        self.strategy_priority = {
            "retire": 1,      # Highest priority - quick wins
            "rehost": 2,      # Fast migration
            "relocate": 3,    # Quick cloud move
            "repurchase": 4,  # SaaS replacement
            "replatform": 5,  # Moderate effort
            "refactor": 6     # Lowest priority - high effort
        }
        
        # Risk factors for wave planning
        self.risk_factors = {
            "business_criticality": {"high": 0.8, "medium": 0.5, "low": 0.2},
            "complexity": {"very_high": 0.9, "high": 0.7, "medium": 0.4, "low": 0.1},
            "dependencies": {"many": 0.8, "some": 0.5, "few": 0.2, "none": 0.0}
        }
    
    async def analyze_migration(
        self, 
        app_ids: List[str], 
        strategies: List[str],
        approach: str = "phased",
        target_cloud: str = "aws"
    ) -> Dict[str, Any]:
        """Perform comprehensive migration analysis"""
        
        # Get application data
        applications = await self._get_applications(app_ids)
        
        # Filter by selected strategies
        filtered_apps = [app for app in applications 
                        if app.get("strategy", "").lower() in strategies]
        
        # Calculate strategy distribution
        strategy_distribution = self._calculate_strategy_distribution(filtered_apps)
        
        # Generate migration waves
        waves = await self.generate_migration_waves(
            app_ids=[app["id"] for app in filtered_apps],
            approach=approach
        )
        
        # Calculate costs
        cost_analysis = await self.cost_service.calculate_migration_costs(
            applications=filtered_apps,
            approach=approach,
            target_cloud=target_cloud
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            filtered_apps, approach, cost_analysis
        )
        
        # Risk assessment
        risk_assessment = await self._assess_migration_risks(filtered_apps, approach)
        
        # Timeline analysis
        timeline = self._calculate_timeline(waves, approach)
        
        # Summary metrics
        summary = {
            "total_apps": len(filtered_apps),
            "ready_to_migrate": len([app for app in filtered_apps 
                                   if app.get("strategy") != "retain"]),
            "estimated_savings": sum(app.get("annual_savings", 0) for app in filtered_apps),
            "migration_time": timeline["total_months"],
            "total_cost": cost_analysis["total"],
            "roi_percentage": await self._calculate_simple_roi(
                cost_analysis["total"], 
                sum(app.get("annual_savings", 0) for app in filtered_apps)
            )
        }
        
        return {
            "summary": summary,
            "strategies": strategy_distribution,
            "costs": cost_analysis,
            "waves": waves,
            "recommendations": recommendations,
            "risk_assessment": risk_assessment,
            "timeline": timeline,
            "applications": filtered_apps
        }
    
    async def generate_migration_waves(
        self, 
        app_ids: List[str], 
        approach: str = "phased",
        timeline_constraint: Optional[int] = None
    ) -> List[MigrationWave]:
        """Generate migration waves based on dependencies and risk"""
        
        applications = await self._get_applications(app_ids)
        
        if approach == "bigbang":
            return await self._generate_bigbang_phases(applications)
        else:
            return await self._generate_phased_waves(applications, timeline_constraint)
    
    async def _generate_phased_waves(
        self, 
        applications: List[Dict], 
        timeline_constraint: Optional[int] = None
    ) -> List[MigrationWave]:
        """Generate phased migration waves"""
        
        # Sort applications by risk and priority
        sorted_apps = self._sort_applications_by_priority(applications)
        
        waves = []
        
        # Wave 1: Foundation & Quick Wins (Low risk, Rehost/Retire)
        wave1_apps = [app for app in sorted_apps 
                     if app.get("strategy", "").lower() in ["rehost", "retire"] 
                     and app.get("risk", "").lower() == "low"][:8]
        
        if wave1_apps:
            wave1 = await self._create_wave(
                name="Wave 1: Foundation & Quick Wins",
                apps=wave1_apps,
                start_month=1,
                duration=6,
                focus="Establish AWS landing zone and migrate low-risk applications",
                aws_services=["EC2", "RDS", "S3", "VPC", "IAM", "CloudWatch"]
            )
            waves.append(wave1)
        
        # Wave 2: Core Services (Medium risk, Replatform)
        wave2_apps = [app for app in sorted_apps 
                     if app.get("strategy", "").lower() == "replatform" 
                     and app.get("risk", "").lower() in ["medium", "high"]][:7]
        
        if wave2_apps:
            wave2 = await self._create_wave(
                name="Wave 2: Core Services",
                apps=wave2_apps,
                start_month=7,
                duration=6,
                focus="Migrate core banking applications with replatforming",
                aws_services=["ECS", "EKS", "Lambda", "API Gateway", "DynamoDB", "ElastiCache"]
            )
            waves.append(wave2)
        
        # Wave 3: Advanced Migration (Remaining Rehost/Replatform)
        remaining_apps = [app for app in sorted_apps 
                         if app not in wave1_apps + wave2_apps 
                         and app.get("strategy", "").lower() in ["rehost", "replatform"]]
        
        if remaining_apps:
            wave3 = await self._create_wave(
                name="Wave 3: Advanced Migration",
                apps=remaining_apps,
                start_month=13,
                duration=6,
                focus="Complete remaining rehost and replatform applications",
                aws_services=["EC2", "RDS", "ECS", "Lambda", "CloudFormation"]
            )
            waves.append(wave3)
        
        # Wave 4: Transformation (Refactor applications)
        refactor_apps = [app for app in sorted_apps 
                        if app.get("strategy", "").lower() in ["refactor"]]
        
        if refactor_apps:
            wave4 = await self._create_wave(
                name="Wave 4: Transformation",
                apps=refactor_apps,
                start_month=19,
                duration=6,
                focus="Refactor complex applications and retire legacy systems",
                aws_services=["Lambda", "API Gateway", "DynamoDB", "SQS", "SNS", "Step Functions"]
            )
            waves.append(wave4)
        
        return waves
    
    async def _generate_bigbang_phases(self, applications: List[Dict]) -> List[MigrationWave]:
        """Generate big bang migration phases"""
        
        phases = []
        
        # Phase 1: Infrastructure & Rehost (All rehost apps in parallel)
        rehost_apps = [app for app in applications 
                      if app.get("strategy", "").lower() == "rehost"]
        
        if rehost_apps:
            phase1 = await self._create_wave(
                name="Phase 1: Infrastructure & Rehost",
                apps=rehost_apps,
                start_month=1,
                duration=4,
                focus="Parallel migration of all rehost applications",
                aws_services=["AWS Migration Hub", "CloudEndure", "Server Migration Service"]
            )
            phases.append(phase1)
        
        # Phase 2: Platform Optimization (All replatform apps)
        replatform_apps = [app for app in applications 
                          if app.get("strategy", "").lower() == "replatform"]
        
        if replatform_apps:
            phase2 = await self._create_wave(
                name="Phase 2: Platform Optimization",
                apps=replatform_apps,
                start_month=5,
                duration=4,
                focus="Simultaneous optimization to AWS managed services",
                aws_services=["ECS", "RDS", "Lambda", "API Gateway", "DynamoDB"]
            )
            phases.append(phase2)
        
        # Phase 3: Advanced Transformation (Refactor + Retire)
        transform_apps = [app for app in applications 
                         if app.get("strategy", "").lower() in ["refactor", "retire"]]
        
        if transform_apps:
            phase3 = await self._create_wave(
                name="Phase 3: Advanced Transformation",
                apps=transform_apps,
                start_month=9,
                duration=4,
                focus="Comprehensive modernization and legacy retirement",
                aws_services=["Lambda", "Step Functions", "SQS", "SNS", "ML Services"]
            )
            phases.append(phase3)
        
        return phases
    
    async def _create_wave(
        self, 
        name: str, 
        apps: List[Dict], 
        start_month: int,
        duration: int, 
        focus: str, 
        aws_services: List[str]
    ) -> MigrationWave:
        """Create a migration wave with cost calculations"""
        
        # Calculate wave costs
        migration_cost = sum(await self._estimate_app_migration_cost(app) for app in apps)
        annual_savings = sum(app.get("annual_savings", 0) for app in apps)
        
        # Determine risk level
        risk_scores = [self._calculate_app_risk_score(app) for app in apps]
        avg_risk = np.mean(risk_scores) if risk_scores else 0.5
        
        risk_level = "High" if avg_risk > 0.7 else "Medium" if avg_risk > 0.4 else "Low"
        
        return MigrationWave(
            name=name,
            duration_months=duration,
            start_month=start_month,
            applications=[app["id"] for app in apps],
            focus=focus,
            migration_cost=migration_cost,
            annual_savings=annual_savings,
            aws_services=aws_services,
            risk_level=risk_level
        )
        
    def _sort_applications_by_priority(self, applications: List[Dict]) -> List[Dict]:
        """Sort applications by migration priority"""
        
        def priority_score(app):
            strategy = app.get("strategy", "rehost").lower()
            risk = app.get("risk", "medium").lower()
            complexity = app.get("complexity", "medium").lower()
            
            # Lower score = higher priority
            score = self.strategy_priority.get(strategy, 5)
            
            # Adjust for risk (prefer lower risk first)
            if risk == "low":
                score -= 1
            elif risk == "high":
                score += 1
            
            # Adjust for complexity
            if complexity == "low":
                score -= 0.5
            elif complexity in ["high", "very_high"]:
                score += 0.5
            
            return score
        
        return sorted(applications, key=priority_score)
    
    def _calculate_strategy_distribution(self, applications: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of applications by strategy"""
        
        distribution = {
            "rehost": 0,
            "replatform": 0,
            "refactor": 0,
            "retire": 0,
            "retain": 0,
            "repurchase": 0,
            "relocate": 0
        }
        
        for app in applications:
            strategy = app.get("strategy", "rehost").lower()
            if strategy in distribution:
                distribution[strategy] += 1
        
        return distribution
    
    async def _estimate_app_migration_cost(self, app: Dict) -> float:
        """Estimate migration cost for a single application"""
        
        strategy = app.get("strategy", "rehost").lower()
        complexity = app.get("complexity", "medium").lower()
        
        # Base costs by strategy (USD)
        base_costs = {
            "rehost": {"low": 25000, "medium": 45000, "high": 75000, "very_high": 120000},
            "replatform": {"low": 45000, "medium": 85000, "high": 140000, "very_high": 220000},
            "refactor": {"low": 120000, "medium": 220000, "high": 350000, "very_high": 500000},
            "retire": {"low": 5000, "medium": 8000, "high": 12000, "very_high": 15000},
            "retain": {"low": 1000, "medium": 1500, "high": 2000, "very_high": 2500},
            "repurchase": {"low": 35000, "medium": 65000, "high": 100000, "very_high": 150000},
            "relocate": {"low": 15000, "medium": 25000, "high": 40000, "very_high": 60000}
        }
        
        strategy_costs = base_costs.get(strategy, base_costs["rehost"])
        return strategy_costs.get(complexity, strategy_costs["medium"])
    
    def _calculate_app_risk_score(self, app: Dict) -> float:
        """Calculate risk score for an application (0.0 to 1.0)"""
        
        risk_level = app.get("risk", "medium").lower()
        complexity = app.get("complexity", "medium").lower()
        strategy = app.get("strategy", "rehost").lower()
        
        # Base risk by level
        base_risk = {"low": 0.2, "medium": 0.5, "high": 0.8, "very_high": 0.9}
        risk_score = base_risk.get(risk_level, 0.5)
        
        # Adjust for complexity
        complexity_factor = {"low": 0.8, "medium": 1.0, "high": 1.2, "very_high": 1.4}
        risk_score *= complexity_factor.get(complexity, 1.0)
        
        # Adjust for strategy
        strategy_factor = {
            "retire": 0.3, "rehost": 0.6, "relocate": 0.7, 
            "replatform": 1.0, "repurchase": 1.1, "refactor": 1.5
        }
        risk_score *= strategy_factor.get(strategy, 1.0)
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    async def _generate_recommendations(
        self, 
        applications: List[Dict], 
        approach: str, 
        cost_analysis: Dict
    ) -> List[str]:
        """Generate migration recommendations"""
        
        recommendations = []
        
        # Analyze strategy distribution
        strategies = self._calculate_strategy_distribution(applications)
        total_apps = sum(strategies.values())
        
        if total_apps == 0:
            return ["No applications selected for analysis"]
        
        # Strategy recommendations
        if strategies["retire"] > 0:
            recommendations.append(
                f"Prioritize retirement of {strategies['retire']} legacy applications "
                f"for immediate cost savings and complexity reduction"
            )
        
        if strategies["rehost"] > strategies["replatform"]:
            recommendations.append(
                f"Focus on lift-and-shift migration for {strategies['rehost']} applications "
                f"to achieve quick cloud adoption and establish AWS foundation"
            )
        
        if strategies["refactor"] > 0:
            recommendations.append(
                f"Plan comprehensive modernization for {strategies['refactor']} applications "
                f"in later phases to maximize cloud-native benefits"
            )
        
        # Approach recommendations
        if approach == "phased":
            recommendations.append(
                "Phased approach recommended for risk mitigation and learning optimization. "
                "Start with low-risk applications to build cloud expertise"
            )
        else:
            recommendations.append(
                "Big bang approach requires extensive planning and parallel execution capabilities. "
                "Ensure adequate resources and change management processes"
            )
        
        # Cost recommendations
        total_cost = cost_analysis.get("total", 0)
        if total_cost > 5000000:  # $5M+
            recommendations.append(
                "Consider phased funding approach and Reserved Instance purchases "
                "to optimize large-scale migration costs"
            )
        
        # AWS-specific recommendations
        recommendations.extend([
            "Leverage AWS Migration Hub for centralized tracking and coordination",
            "Implement AWS Well-Architected Framework principles during migration",
            "Utilize AWS Cost Explorer and Trusted Advisor for ongoing optimization",
            "Establish AWS Control Tower for multi-account governance and security"
        ])
        
        return recommendations
    
    async def _assess_migration_risks(
        self, 
        applications: List[Dict], 
        approach: str
    ) -> Dict[str, Any]:
        """Assess migration risks and mitigation strategies"""
        
        # Calculate overall risk scores
        risk_scores = [self._calculate_app_risk_score(app) for app in applications]
        avg_risk = np.mean(risk_scores) if risk_scores else 0.5
        
        # Identify high-risk applications
        high_risk_apps = [app for app in applications 
                         if self._calculate_app_risk_score(app) > 0.7]
        
        # Risk categories
        risks = {
            "technical_complexity": {
                "level": "High" if avg_risk > 0.7 else "Medium" if avg_risk > 0.4 else "Low",
                "description": f"Average technical complexity across {len(applications)} applications",
                "mitigation": "Thorough technical assessment and proof-of-concept implementations"
            },
            "business_continuity": {
                "level": "High" if approach == "bigbang" else "Medium",
                "description": f"{approach.title()} approach impact on business operations",
                "mitigation": "Comprehensive testing, rollback procedures, and change management"
            },
            "resource_availability": {
                "level": "High" if approach == "bigbang" and len(applications) > 20 else "Medium",
                "description": "Availability of skilled migration resources",
                "mitigation": "Training programs, external consultants, and AWS Professional Services"
            },
            "cost_overrun": {
                "level": "Medium",
                "description": "Risk of exceeding migration budget",
                "mitigation": "Detailed cost tracking, contingency planning, and phased funding"
            }
        }
        
        return {
            "overall_risk_score": avg_risk,
            "risk_level": "High" if avg_risk > 0.7 else "Medium" if avg_risk > 0.4 else "Low",
            "high_risk_applications": [app["id"] for app in high_risk_apps],
            "risk_categories": risks,
            "mitigation_plan": self._generate_mitigation_plan(risks, approach)
        }
    
    def _generate_mitigation_plan(self, risks: Dict, approach: str) -> List[str]:
        """Generate risk mitigation plan"""
        
        plan = [
            "Conduct thorough application assessments and dependency mapping",
            "Implement comprehensive testing strategy including disaster recovery",
            "Establish clear rollback procedures for each migration wave",
            "Create dedicated migration war room for real-time issue resolution"
        ]
        
        if approach == "bigbang":
            plan.extend([
                "Deploy additional monitoring and alerting during migration window",
                "Coordinate with business stakeholders for extended support coverage",
                "Prepare emergency response team for critical issue escalation"
            ])
        
        return plan
    
    def _calculate_timeline(self, waves: List[MigrationWave], approach: str) -> Dict[str, Any]:
        """Calculate migration timeline"""
        
        if not waves:
            return {"total_months": 0, "waves": [], "approach": approach}
        
        total_months = max(wave.start_month + wave.duration_months - 1 for wave in waves)
        
        timeline = {
            "total_months": total_months,
            "total_years": round(total_months / 12, 1),
            "approach": approach,
            "waves": [
                {
                    "name": wave.name,
                    "start_month": wave.start_month,
                    "duration_months": wave.duration_months,
                    "end_month": wave.start_month + wave.duration_months - 1,
                    "applications_count": len(wave.applications)
                }
                for wave in waves
            ],
            "critical_path": self._identify_critical_path(waves)
        }
        
        return timeline
    
    def _identify_critical_path(self, waves: List[MigrationWave]) -> List[str]:
        """Identify critical path through migration waves"""
        # Simplified critical path - in reality would consider dependencies
        return [wave.name for wave in sorted(waves, key=lambda w: w.start_month)]
    
    async def _calculate_simple_roi(self, total_cost: float, annual_savings: float) -> float:
        """Calculate simple ROI percentage"""
        if total_cost == 0:
            return 0
        return ((annual_savings * 3 - total_cost) / total_cost) * 100
    
    async def _get_applications(self, app_ids: List[str]) -> List[Dict]:
        """Get application data for analysis"""
        # This would typically fetch from database/service
        # For now, return mock data based on your structure
        
        if "all" in app_ids:
            return await self._get_all_applications()
        else:
            all_apps = await self._get_all_applications()
            return [app for app in all_apps if app["id"] in app_ids]
    
    async def _get_all_applications(self) -> List[Dict]:
        """Get all applications with calculated savings"""
        
        # Base application data with estimated annual savings
        applications = [
            {
                "id": "ACDA", "name": "ATM Check Card Disputes API", 
                "archetype": "Microservices", "strategy": "Replatform", 
                "complexity": "Medium", "risk": "Medium", "annual_savings": 85000
            },
            {
                "id": "ALE", "name": "Advisor Locator Engine", 
                "archetype": "Web + API Headless", "strategy": "Rehost", 
                "complexity": "Low", "risk": "Low", "annual_savings": 45000
            },
            {
                "id": "AODSVY", "name": "AOD Survey", 
                "archetype": "3-Tier", "strategy": "Replatform", 
                "complexity": "Medium", "risk": "Medium", "annual_savings": 75000
            },
            {
                "id": "APSE", "name": "Appointment Setting (Timetrade)", 
                "archetype": "SOA", "strategy": "Refactor", 
                "complexity": "High", "risk": "High", "annual_savings": 120000
            },
            {
                "id": "BKO", "name": "Banko POC", 
                "archetype": "Client-Server", "strategy": "Retire", 
                "complexity": "Low", "risk": "Low", "annual_savings": 25000
            },
            {
                "id": "BLZD", "name": "FICO/Blaze Decisioning", 
                "archetype": "SOA", "strategy": "Refactor", 
                "complexity": "High", "risk": "High", "annual_savings": 140000
            },
            {
                "id": "BLND", "name": "BLEND SSI", 
                "archetype": "Monolithic", "strategy": "Refactor", 
                "complexity": "High", "risk": "High", "annual_savings": 110000
            }
            # Add more applications as needed...
        ]
        
        return applications
    
    async def generate_executive_summary(
        self, 
        app_ids: List[str], 
        strategies: List[str], 
        approach: str
    ) -> Dict[str, Any]:
        """Generate executive summary for migration analysis"""
        
        analysis = await self.analyze_migration(app_ids, strategies, approach)
        
        summary = {
            "overview": f"Analysis of {analysis['summary']['total_apps']} applications "
                       f"using {approach} migration approach",
            "key_findings": [
                f"Portfolio Readiness: {analysis['summary']['ready_to_migrate']} of "
                f"{analysis['summary']['total_apps']} applications ready for cloud migration",
                f"Cost Optimization: ${analysis['summary']['estimated_savings']:,.0f} "
                f"projected annual savings through AWS adoption",
                f"Timeline: {analysis['summary']['migration_time']}-month "
                f"{approach} migration plan",
                f"ROI: {analysis['summary']['roi_percentage']:.0f}% return on investment over 3 years"
            ],
            "recommendations": analysis["recommendations"][:3],  # Top 3 recommendations
            "metrics": {
                "total_investment": analysis["costs"]["total"],
                "annual_savings": analysis["summary"]["estimated_savings"],
                "payback_period_months": (analysis["costs"]["total"] / 
                                        analysis["summary"]["estimated_savings"] * 12) 
                                       if analysis["summary"]["estimated_savings"] > 0 else 999,
                "risk_level": analysis["risk_assessment"]["risk_level"]
            }
        }
        
        return summary
        
    async def export_migration_plan(self, waves: List[MigrationWave], format: str = "excel") -> Dict[str, Any]:
        """Export migration plan to results folder structure"""
        
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
            filename = f"migration_plan_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == "excel":
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Migration waves overview
                    waves_data = []
                    for wave in waves:
                        waves_data.append({
                            "Wave_Name": wave.name,
                            "Duration_Months": wave.duration_months,
                            "Start_Month": wave.start_month,
                            "Applications_Count": len(wave.applications),
                            "Migration_Cost": wave.migration_cost,
                            "Annual_Savings": wave.annual_savings,
                            "Risk_Level": wave.risk_level,
                            "Focus": wave.focus
                        })
                    
                    if waves_data:
                        pd.DataFrame(waves_data).to_excel(writer, sheet_name='Migration Waves', index=False)
                    
                    # Detailed application assignments
                    app_assignments = []
                    for wave in waves:
                        for app_id in wave.applications:
                            app_assignments.append({
                                "Application_ID": app_id,
                                "Wave": wave.name,
                                "Start_Month": wave.start_month,
                                "Duration": wave.duration_months,
                                "AWS_Services": ", ".join(wave.aws_services[:5])  # Limit for readability
                            })
                    
                    if app_assignments:
                        pd.DataFrame(app_assignments).to_excel(writer, sheet_name='Application Assignments', index=False)
                    
                    # Timeline summary
                    total_duration = max(wave.start_month + wave.duration_months - 1 for wave in waves) if waves else 0
                    timeline_summary = [{
                        "Total_Waves": len(waves),
                        "Total_Duration_Months": total_duration,
                        "Total_Applications": sum(len(wave.applications) for wave in waves),
                        "Total_Migration_Cost": sum(wave.migration_cost for wave in waves),
                        "Total_Annual_Savings": sum(wave.annual_savings for wave in waves)
                    }]
                    
                    pd.DataFrame(timeline_summary).to_excel(writer, sheet_name='Timeline Summary', index=False)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir)
            }
            
        except Exception as e:
            raise Exception(f"Error exporting migration plan: {str(e)}")