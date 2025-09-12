"""
Archetype Service
Handles application archetype analysis and classification
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import os
import json
import asyncio

class ArchetypeService:
    """Service for application archetype management and analysis"""
    
    def __init__(self):
        self.archetype_definitions = self._initialize_archetype_definitions()
        self.migration_suitability = self._initialize_migration_suitability()
        self.template_mappings = self._initialize_template_mappings()
        
        # Ensure results directory exists
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
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
                "aws_services": ["ECS", "EKS", "Lambda", "API Gateway", "Service Mesh"],
                "diagram_template": "microservices_template",
                "complexity_score": 8
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
                "aws_services": ["EC2", "RDS", "Application Load Balancer"],
                "diagram_template": "monolithic_template",
                "complexity_score": 4
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
                "aws_services": ["EC2", "RDS", "ElastiCache", "CloudFront"],
                "diagram_template": "three_tier_template",
                "complexity_score": 6
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
                "aws_services": ["API Gateway", "Lambda", "SQS", "SNS"],
                "diagram_template": "soa_template",
                "complexity_score": 7
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
                "aws_services": ["EventBridge", "SQS", "SNS", "Kinesis", "Lambda"],
                "diagram_template": "event_driven_template",
                "complexity_score": 7
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
                "aws_services": ["CloudFront", "S3", "API Gateway", "Lambda"],
                "diagram_template": "headless_api_template",
                "complexity_score": 5
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
                "aws_services": ["WorkSpaces", "AppStream", "RDS"],
                "diagram_template": "client_server_template",
                "complexity_score": 3
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
    
    def _initialize_template_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize architecture diagram template mappings"""
        return {
            "microservices_template": {
                "template_file": "templates/diagrams/microservices.json",
                "visio_template": "templates/visio/microservices.vsdx",
                "components": ["API Gateway", "Service Mesh", "Container Registry", "Load Balancer"],
                "connections": ["HTTP/HTTPS", "gRPC", "Message Queue"],
                "layout": "distributed_grid"
            },
            "three_tier_template": {
                "template_file": "templates/diagrams/three_tier.json",
                "visio_template": "templates/visio/three_tier.vsdx",
                "components": ["Web Server", "Application Server", "Database Server"],
                "connections": ["HTTP", "JDBC/ODBC", "SQL"],
                "layout": "vertical_stack"
            },
            "event_driven_template": {
                "template_file": "templates/diagrams/event_driven.json",
                "visio_template": "templates/visio/event_driven.vsdx",
                "components": ["Event Producer", "Message Broker", "Event Consumer"],
                "connections": ["Event Stream", "Message Queue", "WebSocket"],
                "layout": "flow_diagram"
            },
            "monolithic_template": {
                "template_file": "templates/diagrams/monolithic.json",
                "visio_template": "templates/visio/monolithic.vsdx",
                "components": ["Monolithic Application", "Database", "Load Balancer"],
                "connections": ["HTTP", "Database Connection"],
                "layout": "simple_stack"
            },
            "soa_template": {
                "template_file": "templates/diagrams/soa.json",
                "visio_template": "templates/visio/soa.vsdx",
                "components": ["ESB", "Service Registry", "Services", "Consumers"],
                "connections": ["SOAP", "HTTP", "JMS"],
                "layout": "hub_spoke"
            },
            "headless_api_template": {
                "template_file": "templates/diagrams/headless_api.json",
                "visio_template": "templates/visio/headless_api.vsdx",
                "components": ["Frontend App", "API Gateway", "Backend Services", "CDN"],
                "connections": ["REST API", "GraphQL", "WebSocket"],
                "layout": "frontend_backend"
            },
            "client_server_template": {
                "template_file": "templates/diagrams/client_server.json",
                "visio_template": "templates/visio/client_server.vsdx",
                "components": ["Desktop Client", "Application Server", "Database"],
                "connections": ["TCP/IP", "Database Driver"],
                "layout": "two_tier"
            }
        }
    
    def get_archetypes(self) -> Dict[str, Any]:
        """Get all application archetypes with comprehensive information"""
        
        return {
            "archetypes": self.archetype_definitions,
            "migration_suitability": self.migration_suitability,
            "template_mappings": self.template_mappings,
            "summary": {
                "total_archetypes": len(self.archetype_definitions),
                "cloud_ready_archetypes": len([
                    arch for arch, details in self.archetype_definitions.items() 
                    if details["cloud_readiness"] == "High"
                ]),
                "template_count": len(self.template_mappings),
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
    
    def get_archetype_details(self, archetype_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific archetype"""
        
        if archetype_name not in self.archetype_definitions:
            return None
        
        archetype_info = self.archetype_definitions[archetype_name].copy()
        archetype_info["migration_suitability"] = self.migration_suitability.get(archetype_name, {})
        
        # Add template information
        template_key = archetype_info.get("diagram_template")
        if template_key and template_key in self.template_mappings:
            archetype_info["template_info"] = self.template_mappings[template_key]
        
        return archetype_info
    
    def recommend_strategy(self, archetype: str, business_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
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
            "cloud_readiness": archetype_info["cloud_readiness"],
            "diagram_template": archetype_info.get("diagram_template"),
            "complexity_score": archetype_info.get("complexity_score", 5)
        }
    
    def analyze_portfolio_archetypes(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze archetype distribution across application portfolio"""
        
        archetype_counts = {}
        strategy_recommendations = {}
        complexity_analysis = {"simple": 0, "moderate": 0, "complex": 0}
        
        for app in applications:
            archetype = app.get("archetype", "Unknown")
            
            # Count archetypes
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
            
            # Get strategy recommendations
            if archetype in self.archetype_definitions:
                recommended_strategy = self.archetype_definitions[archetype]["typical_7r_strategy"]
                strategy_recommendations[recommended_strategy] = strategy_recommendations.get(recommended_strategy, 0) + 1
                
                # Analyze complexity
                complexity_score = self.archetype_definitions[archetype].get("complexity_score", 5)
                if complexity_score <= 4:
                    complexity_analysis["simple"] += 1
                elif complexity_score <= 6:
                    complexity_analysis["moderate"] += 1
                else:
                    complexity_analysis["complex"] += 1
        
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
                "strategy_recommendations": strategy_recommendations,
                "complexity_analysis": complexity_analysis
            },
            "modernization_analysis": {
                "effort_distribution": effort_distribution,
                "cloud_readiness_distribution": cloud_readiness_distribution,
                "cloud_ready_percentage": (cloud_readiness_distribution.get("High", 0) / len(applications) * 100) if applications else 0
            },
            "diagram_recommendations": self._generate_diagram_recommendations(archetype_counts),
            "recommendations": self._generate_portfolio_recommendations(archetype_counts, len(applications))
        }
    
    def _generate_diagram_recommendations(self, archetype_counts: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate diagram template recommendations based on portfolio"""
        
        recommendations = []
        
        for archetype, count in archetype_counts.items():
            if archetype in self.archetype_definitions:
                template_key = self.archetype_definitions[archetype].get("diagram_template")
                if template_key and template_key in self.template_mappings:
                    recommendations.append({
                        "archetype": archetype,
                        "application_count": count,
                        "template": template_key,
                        "template_info": self.template_mappings[template_key],
                        "priority": "High" if count > 5 else "Medium" if count > 1 else "Low"
                    })
        
        # Sort by application count (most common archetypes first)
        recommendations.sort(key=lambda x: x["application_count"], reverse=True)
        
        return recommendations
    
    def _generate_portfolio_recommendations(self, archetype_counts: Dict[str, int], total_apps: int) -> List[str]:
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
    
    def export_archetype_analysis(self, applications: List[Dict[str, Any]], format: str = "excel") -> Dict[str, Any]:
        """Export archetype analysis to results folder"""
        
        try:
            if format == "excel":
                export_dir = self.results_dir / "excel"
            else:
                export_dir = self.results_dir / "document"
                
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"archetype_analysis_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == "excel":
                analysis = self.analyze_portfolio_archetypes(applications)
                
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
                                "Key_AWS_Services": ", ".join(arch_info["aws_services"][:3]),
                                "Diagram_Template": arch_info.get("diagram_template", ""),
                                "Complexity_Score": arch_info.get("complexity_score", "")
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
                            "Key_Technologies": ", ".join(details["technologies"][:3]),
                            "Diagram_Template": details.get("diagram_template", ""),
                            "Complexity_Score": details.get("complexity_score", "")
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
                    
                    # Diagram recommendations
                    if analysis.get("diagram_recommendations"):
                        diagram_data = []
                        for rec in analysis["diagram_recommendations"]:
                            diagram_data.append({
                                "Archetype": rec["archetype"],
                                "Application_Count": rec["application_count"],
                                "Template": rec["template"],
                                "Priority": rec["priority"],
                                "Components": ", ".join(rec["template_info"].get("components", [])),
                                "Layout": rec["template_info"].get("layout", "")
                            })
                        
                        pd.DataFrame(diagram_data).to_excel(writer, sheet_name='Diagram Recommendations', index=False)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir)
            }
            
        except Exception as e:
            raise Exception(f"Error exporting archetype analysis: {str(e)}")
    
    def debug_archetype_service(self):
        """Debug method to check available attributes"""
        print("=== ArchetypeService Debug ===")
        print(f"Has archetype_definitions: {hasattr(self, 'archetype_definitions')}")
        print(f"Has template_mappings: {hasattr(self, 'template_mappings')}")
        
        if hasattr(self, 'archetype_definitions'):
            print(f"Archetype definitions keys: {list(getattr(self, 'archetype_definitions', {}).keys())}")
        
        if hasattr(self, 'template_mappings'):
            print(f"Template mappings keys: {list(getattr(self, 'template_mappings', {}).keys())}")
            
    def get_diagram_template(self, archetype: str) -> Optional[Dict[str, Any]]:
        """Get diagram template information for a specific archetype"""
        
        # Use your existing lookup pattern
        if archetype not in self.archetype_definitions:
            return None
        
        template_key = self.archetype_definitions[archetype].get("diagram_template")
        if not template_key or template_key not in self.template_mappings:
            return None
        
        template_info = self.template_mappings[template_key].copy()
        template_info["archetype"] = archetype
        template_info["archetype_details"] = self.archetype_definitions[archetype]
        template_info["template"] = template_info.get("template_file", template_key)
        
        return template_info
    
    def _load_archetype_classification_data(self) -> Dict[str, Any]:
        """Load your existing archetype_templates.yaml"""
        template_path = Path("templates/archetype_templates.yaml")
        
        try:
            with open(template_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading archetype templates: {e}")
            return {}
            
    def _create_diagram_template_from_archetype(self, archetype_key: str, archetype_info: Dict) -> Dict[str, Any]:
        """Create diagram template based on archetype characteristics"""
        
        indicators = archetype_info.get('indicators', {})
        traffic_pattern = indicators.get('traffic', {}).get('pattern', 'standard')
        
        # Map archetype to components and layout
        template_mapping = {
            'monolithic': {
                'layout': 'vertical_stack',
                'components': ['Load Balancer', 'Monolithic Application', 'Database', 'File Storage'],
                'connections': ['HTTP', 'Internal Processing', 'SQL'],
                'data_flows': [
                    {'source': 'Load Balancer', 'target': 'Monolithic Application', 'flow_type': 'request_response', 'annotation': 'web requests'},
                    {'source': 'Monolithic Application', 'target': 'Database', 'flow_type': 'data_access', 'annotation': 'data operations'}
                ]
            },
            'three_tier': {
                'layout': 'vertical_stack',
                'components': ['Web Tier', 'Application Tier', 'Database Tier'],
                'connections': ['HTTP/HTTPS', 'API Calls', 'SQL'],
                'data_flows': [
                    {'source': 'Web Tier', 'target': 'Application Tier', 'flow_type': 'request_response', 'annotation': 'user requests'},
                    {'source': 'Application Tier', 'target': 'Database Tier', 'flow_type': 'data_access', 'annotation': 'data queries'}
                ]
            },
            'microservices': {
                'layout': 'distributed_grid',
                'components': ['API Gateway', 'Service Mesh', 'Business Services', 'Message Broker', 'Database Services', 'Service Registry'],
                'connections': ['REST/gRPC', 'Service Discovery', 'Event Streams'],
                'data_flows': [
                    {'source': 'API Gateway', 'target': 'Business Services', 'flow_type': 'api_routing', 'annotation': 'route requests'},
                    {'source': 'Business Services', 'target': 'Message Broker', 'flow_type': 'publish_subscribe', 'annotation': 'async events'},
                    {'source': 'Business Services', 'target': 'Database Services', 'flow_type': 'data_access', 'annotation': 'data operations'}
                ]
            },
            'event_driven': {
                'layout': 'hub_spoke',
                'components': ['Event Producers', 'Message Broker', 'Event Consumers', 'Event Store', 'Stream Processor'],
                'connections': ['Publish/Subscribe', 'Event Streams', 'Dead Letter Queue'],
                'data_flows': [
                    {'source': 'Event Producers', 'target': 'Message Broker', 'flow_type': 'publish', 'annotation': 'publish events'},
                    {'source': 'Message Broker', 'target': 'Event Consumers', 'flow_type': 'subscribe', 'annotation': 'consume events'},
                    {'source': 'Stream Processor', 'target': 'Event Store', 'flow_type': 'persist', 'annotation': 'store processed events'}
                ]
            },
            'soa': {
                'layout': 'distributed_grid',
                'components': ['ESB', 'Service Registry', 'Business Services', 'Legacy Systems', 'Security Gateway'],
                'connections': ['SOAP/REST', 'ESB Routing', 'Service Contracts'],
                'data_flows': [
                    {'source': 'Business Services', 'target': 'ESB', 'flow_type': 'service_call', 'annotation': 'service requests'},
                    {'source': 'ESB', 'target': 'Legacy Systems', 'flow_type': 'transformation', 'annotation': 'protocol transformation'}
                ]
            },
            'client_server': {
                'layout': 'frontend_backend',
                'components': ['Client Applications', 'Application Server', 'Database Server', 'File Server'],
                'connections': ['Direct Connection', 'SQL', 'File Transfer'],
                'data_flows': [
                    {'source': 'Client Applications', 'target': 'Application Server', 'flow_type': 'thick_client', 'annotation': 'business logic calls'},
                    {'source': 'Application Server', 'target': 'Database Server', 'flow_type': 'data_access', 'annotation': 'direct SQL access'}
                ]
            },
            'serverless': {
                'layout': 'event_driven',
                'components': ['Event Sources', 'Function Runtime', 'Managed Services', 'Storage Services'],
                'connections': ['Event Triggers', 'API Calls', 'Managed Connections'],
                'data_flows': [
                    {'source': 'Event Sources', 'target': 'Function Runtime', 'flow_type': 'trigger', 'annotation': 'invoke functions'},
                    {'source': 'Function Runtime', 'target': 'Managed Services', 'flow_type': 'api_call', 'annotation': 'use cloud services'}
                ]
            },
            # Add more mappings for other archetypes...
        }
        
        template = template_mapping.get(archetype_key, {
            'layout': 'distributed_grid',
            'components': ['Service Layer', 'Data Layer'],
            'connections': ['API Calls'],
            'data_flows': [
                {'source': 'Service Layer', 'target': 'Data Layer', 'flow_type': 'data_access', 'annotation': 'data operations'}
            ]
        })
        
        return {
            'template': f"{archetype_key}_dataflow",
            'archetype_name': archetype_info.get('name', archetype_key.title()),
            'description': archetype_info.get('description', ''),
            'layout': template['layout'],
            'components': template['components'],
            'connections': template['connections'],
            'data_flows': template.get('data_flows', []),
            'port_indicators': indicators.get('ports', {}),
            'traffic_pattern': traffic_pattern
        }
    
    def list_available_templates(self) -> Dict[str, Any]:
        """List all available diagram templates"""
        
        templates_by_archetype = {}
        
        for archetype, details in self.archetype_definitions.items():
            template_key = details.get("diagram_template")
            if template_key and template_key in self.template_mappings:
                templates_by_archetype[archetype] = {
                    "template_key": template_key,
                    "template_info": self.template_mappings[template_key],
                    "complexity_score": details.get("complexity_score", 5),
                    "cloud_readiness": details["cloud_readiness"]
                }
        
        return {
            "total_templates": len(templates_by_archetype),
            "templates_by_archetype": templates_by_archetype,
            "template_categories": {
                "simple": [arch for arch, info in templates_by_archetype.items() 
                          if info["complexity_score"] <= 4],
                "moderate": [arch for arch, info in templates_by_archetype.items() 
                           if 5 <= info["complexity_score"] <= 6],
                "complex": [arch for arch, info in templates_by_archetype.items() 
                          if info["complexity_score"] >= 7]
            }
        }