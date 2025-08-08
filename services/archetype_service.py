"""
Archetype Service
Handles application archetype analysis and classification
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

class ArchetypeService:
    """Service for application archetype management and analysis"""
    
    def __init__(self):
        self.archetype_definitions = self._initialize_archetype_definitions()
        self.migration_suitability = self._initialize_migration_suitability()
    
    def _initialize_archetype_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive archetype definitions"""
        return {
            "Microservices": {
                "description": "Containerized microservices architecture with service mesh",
                "characteristics": [
                    "Distributed services",
                    "Container-based deployment",
                    "API-first design",
                    "Independent scaling"
                ],
                "technologies": ["Docker", "Kubernetes", "Spring Boot", "Node.js"],
                "cloud_readiness": "High",
                "modernization_effort": "Low",
                "typical_7r_strategy": "Replatform",
                "aws_services": ["ECS", "EKS", "Lambda", "API Gateway", "Service Mesh"]
            },
            "Monolithic": {
                "description": "Single-tier monolithic application with tightly coupled components",
                "characteristics": [
                    "Single deployment unit",
                    "Shared database",
                    "Tight coupling",
                    "Traditional architecture"
                ],
                "technologies": ["Java EE", ".NET Framework", "Ruby on Rails", "Django"],
                "cloud_readiness": "Medium",
                "modernization_effort": "High",
                "typical_7r_strategy": "Refactor",
                "aws_services": ["EC2", "RDS", "Application Load Balancer"]
            },
            "3-Tier": {
                "description": "Traditional 3-tier web application (presentation, business, data)",
                "characteristics": [
                    "Presentation layer",
                    "Business logic layer", 
                    "Data access layer",
                    "Clear separation of concerns"
                ],
                "technologies": ["Java EE", "ASP.NET", "PHP", "Oracle", "SQL Server"],
                "cloud_readiness": "Medium",
                "modernization_effort": "Medium",
                "typical_7r_strategy": "Replatform",
                "aws_services": ["EC2", "RDS", "ElastiCache", "CloudFront"]
            },
            "SOA": {
                "description": "Service-oriented architecture with enterprise service bus",
                "characteristics": [
                    "Service interfaces",
                    "Enterprise service bus",
                    "SOAP/XML messaging",
                    "Service registry"
                ],
                "technologies": ["ESB", "SOAP", "WSDL", "Enterprise Services"],
                "cloud_readiness": "Low",
                "modernization_effort": "High", 
                "typical_7r_strategy": "Refactor",
                "aws_services": ["API Gateway", "Lambda", "SQS", "SNS"]
            },
            "Event-Driven": {
                "description": "Event-driven architecture with message queues and event streaming",
                "characteristics": [
                    "Event producers/consumers",
                    "Message queues",
                    "Event streaming",
                    "Asynchronous processing"
                ],
                "technologies": ["Apache Kafka", "RabbitMQ", "Event Streaming", "Message Queues"],
                "cloud_readiness": "High",
                "modernization_effort": "Low",
                "typical_7r_strategy": "Replatform",
                "aws_services": ["EventBridge", "SQS", "SNS", "Kinesis", "Lambda"]
            },
            "Web + API Headless": {
                "description": "Headless web application with RESTful APIs and modern frontend",
                "characteristics": [
                    "RESTful APIs",
                    "Frontend/backend separation",
                    "Modern JavaScript frameworks",
                    "API-first approach"
                ],
                "technologies": ["React", "Angular", "Vue.js", "Node.js", "REST APIs"],
                "cloud_readiness": "High",
                "modernization_effort": "Low",
                "typical_7r_strategy": "Rehost",
                "aws_services": ["CloudFront", "S3", "API Gateway", "Lambda"]
            },
            "Client-Server": {
                "description": "Traditional client-server architecture with desktop applications",
                "characteristics": [
                    "Desktop applications",
                    "Direct database connections",
                    "Two-tier architecture",
                    "Legacy protocols"
                ],
                "technologies": ["Desktop Apps", "Client/Server DB", "Legacy Protocols"],
                "cloud_readiness": "Low",
                "modernization_effort": "Very High",
                "typical_7r_strategy": "Retire",
                "aws_services": ["WorkSpaces", "AppStream", "RDS"]
            }
        }
    
    def _initialize_migration_suitability(self) -> Dict[str, Dict[str, str]]:
        """Initialize migration suitability matrix"""
        return {
            "Microservices": {
                "rehost": "Good",
                "replatform": "Excellent", 
                "refactor": "Good",
                "retire": "Poor",
                "retain": "Poor",
                "repurchase": "Fair",
                "relocate": "Good"
            },
            "Monolithic": {
                "rehost": "Good",
                "replatform": "Fair",
                "refactor": "Excellent",
                "retire": "Fair",
                "retain": "Good",
                "repurchase": "Fair",
                "relocate": "Good"
            },
            "3-Tier": {
                "rehost": "Good",
                "replatform": "Excellent",
                "refactor": "Good",
                "retire": "Fair",
                "retain": "Fair",
                "repurchase": "Good",
                "relocate": "Good"
            },
            "SOA": {
                "rehost": "Poor",
                "replatform": "Fair",
                "refactor": "Excellent",
                "retire": "Good",
                "retain": "Fair",
                "repurchase": "Good",
                "relocate": "Poor"
            },
            "Event-Driven": {
                "rehost": "Good",
                "replatform": "Excellent",
                "refactor": "Good",
                "retire": "Poor",
                "retain": "Poor",
                "repurchase": "Fair",
                "relocate": "Good"
            },
            "Web + API Headless": {
                "rehost": "Excellent",
                "replatform": "Good",
                "refactor": "Fair",
                "retire": "Poor",
                "retain": "Poor",
                "repurchase": "Good",
                "relocate": "Excellent"
            },
            "Client-Server": {
                "rehost": "Poor",
                "replatform": "Poor",
                "refactor": "Poor",
                "retire": "Excellent",
                "retain": "Good",
                "repurchase": "Excellent",
                "relocate": "Poor"
            }
        }
    
    async def get_archetypes(self) -> Dict[str, Any]:
        """Get all application archetypes with comprehensive information"""
        
        return {
            "archetypes": self.archetype_definitions,
            "migration_suitability": self.migration_suitability,
            "summary": {
                "total_archetypes": len(self.archetype_definitions),
                "cloud_ready_archetypes": len([
                    arch for arch, details in self.archetype_definitions.items() 
                    if details["cloud_readiness"] == "High"
                ]),
                "modernization_categories": {
                    "Low Effort": len([
                        arch for arch, details in self.archetype_definitions.items()
                        if details["modernization_effort"] == "Low"
                    ]),
                    "Medium Effort": len([
                        arch for arch, details in self.archetype_definitions.items()
                        if details["modernization_effort"] == "Medium" 
                    ]),
                    "High Effort": len([
                        arch for arch, details in self.archetype_definitions.items()
                        if details["modernization_effort"] in ["High", "Very High"]
                    ])
                }
            }
        }
    
    async def get_archetype_details(self, archetype_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific archetype"""
        
        if archetype_name not in self.archetype_definitions:
            return None
        
        archetype_info = self.archetype_definitions[archetype_name].copy()
        archetype_info["migration_suitability"] = self.migration_suitability.get(archetype_name, {})
        
        return archetype_info
    
    async def recommend_strategy(self, archetype: str, business_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """Recommend 7 Rs strategy based on archetype and business requirements"""
        
        if archetype not in self.archetype_definitions:
            return {"error": f"Unknown archetype: {archetype}"}
        
        archetype_info = self.archetype_definitions[archetype]
        suitability = self.migration_suitability.get(archetype, {})
        
        # Get primary recommendation
        primary_strategy = archetype_info["typical_7r_strategy"]
        
        # Get alternative strategies based on suitability
        excellent_strategies = [strategy for strategy, rating in suitability.items() if rating == "Excellent"]
        good_strategies = [strategy for strategy, rating in suitability.items() if rating == "Good"]
        
        return {
            "archetype": archetype,
            "primary_recommendation": {
                "strategy": primary_strategy,
                "rationale": f"Best fit for {archetype} based on architecture characteristics"
            },
            "alternative_strategies": {
                "excellent": excellent_strategies,
                "good": good_strategies
            },
            "aws_services": archetype_info["aws_services"],
            "modernization_effort": archetype_info["modernization_effort"],
            "cloud_readiness": archetype_info["cloud_readiness"]
        }
    
    async def analyze_portfolio_archetypes(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze archetype distribution across application portfolio"""
        
        archetype_counts = {}
        strategy_recommendations = {}
        
        for app in applications:
            archetype = app.get("archetype", "Unknown")
            
            # Count archetypes
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
            
            # Get strategy recommendations
            if archetype in self.archetype_definitions:
                recommended_strategy = self.archetype_definitions[archetype]["typical_7r_strategy"]
                strategy_recommendations[recommended_strategy] = strategy_recommendations.get(recommended_strategy, 0) + 1
        
        # Calculate modernization effort distribution
        effort_distribution = {"Low": 0, "Medium": 0, "High": 0, "Very High": 0}
        cloud_readiness_distribution = {"High": 0, "Medium": 0, "Low": 0}
        
        for app in applications:
            archetype = app.get("archetype", "Unknown")
            if archetype in self.archetype_definitions:
                effort = self.archetype_definitions[archetype]["modernization_effort"]
                effort_distribution[effort] = effort_distribution.get(effort, 0) + 1
                
                readiness = self.archetype_definitions[archetype]["cloud_readiness"]
                cloud_readiness_distribution[readiness] = cloud_readiness_distribution.get(readiness, 0) + 1
        
        return {
            "portfolio_summary": {
                "total_applications": len(applications),
                "unique_archetypes": len(archetype_counts),
                "archetype_distribution": archetype_counts,
                "strategy_recommendations": strategy_recommendations
            },
            "modernization_analysis": {
                "effort_distribution": effort_distribution,
                "cloud_readiness_distribution": cloud_readiness_distribution,
                "cloud_ready_percentage": (cloud_readiness_distribution.get("High", 0) / len(applications) * 100) if applications else 0
            },
            "recommendations": await self._generate_portfolio_recommendations(archetype_counts, len(applications))
        }
    
    async def _generate_portfolio_recommendations(self, archetype_counts: Dict[str, int], total_apps: int) -> List[str]:
        """Generate recommendations based on portfolio archetype analysis"""
        
        recommendations = []
        
        # Check for modernization opportunities
        legacy_count = archetype_counts.get("Client-Server", 0) + archetype_counts.get("SOA", 0)
        if legacy_count > total_apps * 0.3:
            recommendations.append(
                f"Consider modernization strategy for {legacy_count} legacy applications "
                f"({legacy_count/total_apps*100:.1f}% of portfolio)"
            )
        
        # Check for cloud-ready applications
        cloud_ready = archetype_counts.get("Microservices", 0) + archetype_counts.get("Web + API Headless", 0)
        if cloud_ready > 0:
            recommendations.append(
                f"Fast-track {cloud_ready} cloud-ready applications for immediate migration benefits"
            )
        
        # Check for event-driven applications
        event_driven = archetype_counts.get("Event-Driven", 0)
        if event_driven > 0:
            recommendations.append(
                f"Leverage AWS event services for {event_driven} event-driven applications"
            )
        
        # Check for monolithic applications
        monolithic = archetype_counts.get("Monolithic", 0)
        if monolithic > 0:
            recommendations.append(
                f"Plan refactoring strategy for {monolithic} monolithic applications to maximize cloud benefits"
            )
        
        return recommendations
    
    async def export_archetype_analysis(self, applications: List[Dict[str, Any]], format: str = "excel") -> Dict[str, Any]:
        """Export archetype analysis to results folder"""
        
        try:
            base_results_dir = Path("results")
            
            if format == "excel":
                export_dir = base_results_dir / "excel"
            else:
                export_dir = base_results_dir / "document"
                
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"archetype_analysis_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == "excel":
                analysis = await self.analyze_portfolio_archetypes(applications)
                
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Application archetype mapping
                    app_data = []
                    for app in applications:
                        archetype = app.get("archetype", "Unknown")
                        if archetype in self.archetype_definitions:
                            arch_info = self.archetype_definitions[archetype]
                            app_data.append({
                                "Application": app.get("name", app.get("id")),
                                "Archetype": archetype,
                                "Cloud_Readiness": arch_info["cloud_readiness"],
                                "Modernization_Effort": arch_info["modernization_effort"],
                                "Recommended_Strategy": arch_info["typical_7r_strategy"],
                                "Key_AWS_Services": ", ".join(arch_info["aws_services"][:3])
                            })
                    
                    if app_data:
                        pd.DataFrame(app_data).to_excel(writer, sheet_name='Application Archetypes', index=False)
                    
                    # Archetype definitions
                    arch_data = []
                    for name, details in self.archetype_definitions.items():
                        arch_data.append({
                            "Archetype": name,
                            "Description": details["description"],
                            "Cloud_Readiness": details["cloud_readiness"],
                            "Modernization_Effort": details["modernization_effort"],
                            "Typical_Strategy": details["typical_7r_strategy"],
                            "Key_Technologies": ", ".join(details["technologies"][:3])
                        })
                    
                    pd.DataFrame(arch_data).to_excel(writer, sheet_name='Archetype Definitions', index=False)
                    
                    # Portfolio summary
                    summary_data = []
                    for key, value in analysis["portfolio_summary"].items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                summary_data.append({"Metric": f"{key}_{sub_key}", "Value": sub_value})
                        else:
                            summary_data.append({"Metric": key, "Value": value})
                    
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Portfolio Summary', index=False)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir)
            }
            
        except Exception as e:
            raise Exception(f"Error exporting archetype analysis: {str(e)}")