"""
Application Service
Handles application data management and portfolio operations
Enhanced for integration with AWS migration services
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from pathlib import Path
import openpyxl
import asyncio

class AppService:
    """Service for managing application portfolio data"""
    
    def __init__(self):
        self.data_folder = Path("static/ui/data")
        self.applications_cache = None
        self.last_refresh = None
        
        # Strategy assignment rules based on archetype
        self.archetype_strategy_mapping = {
            "Microservices": "Replatform",
            "Web + API Headless": "Rehost", 
            "3-Tier": "Replatform",
            "SOA": "Refactor",
            "Event-Driven": "Replatform",
            "Monolithic": "Refactor",
            "Client-Server": "Retire"
        }
        
        # Complexity mapping
        self.archetype_complexity_mapping = {
            "Microservices": "Medium",
            "Web + API Headless": "Low",
            "3-Tier": "Medium", 
            "SOA": "High",
            "Event-Driven": "Medium",
            "Monolithic": "High",
            "Client-Server": "Low"
        }
        
        # Risk assessment mapping
        self.strategy_risk_mapping = {
            "Rehost": "Low",
            "Relocate": "Low",
            "Retire": "Low",
            "Replatform": "Medium",
            "Repurchase": "Medium", 
            "Refactor": "High",
            "Retain": "Low"
        }

        # Business criticality keywords for better assessment
        self.criticality_keywords = {
            "Critical": ["core", "primary", "main", "critical", "auth", "security", "card", "dispute", "fraud", "payment", "transaction"],
            "High": ["bank", "customer", "account", "loan", "credit", "financial", "regulatory", "compliance"],
            "Medium": ["support", "admin", "report", "analytics", "monitor"],
            "Low": ["test", "poc", "demo", "prototype", "legacy"]
        }
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get complete application portfolio with analysis"""
        
        applications = await self.get_all_applications()
        
        # Calculate distributions
        strategy_distribution = self._calculate_distribution(applications, "strategy")
        archetype_distribution = self._calculate_distribution(applications, "archetype")
        complexity_distribution = self._calculate_distribution(applications, "complexity")
        risk_distribution = self._calculate_distribution(applications, "risk")
        criticality_distribution = self._calculate_distribution(applications, "business_criticality")
        
        # Calculate summary metrics
        total_cost = sum(app.get("estimated_cost", 0) for app in applications)
        total_savings = sum(app.get("annual_savings", 0) for app in applications)
        avg_timeline = np.mean([app.get("timeline_months", 0) for app in applications]) if applications else 0
        
        return {
            "applications": applications,
            "total_count": len(applications),
            "strategy_distribution": strategy_distribution,
            "archetype_distribution": archetype_distribution,
            "complexity_distribution": complexity_distribution,
            "risk_distribution": risk_distribution,
            "criticality_distribution": criticality_distribution,
            "summary_metrics": {
                "total_migration_cost": total_cost,
                "total_annual_savings": total_savings,
                "average_timeline_months": round(avg_timeline, 1),
                "roi_3_year": ((total_savings * 3 - total_cost) / total_cost * 100) if total_cost > 0 else 0
            }
        }
    
    async def get_all_applications(self) -> List[Dict]:
        """Get all applications with 7 Rs analysis"""
        
        if self.applications_cache is None or self._needs_refresh():
            await self.refresh_data()
        
        return self.applications_cache or []
    
    async def get_applications(self, app_ids: List[str]) -> List[Dict]:
        """Get applications by IDs - for service integration"""
        
        applications = await self.get_all_applications()
        
        if "all" in app_ids:
            return applications
        
        return [app for app in applications if app["id"] in app_ids]
    
    async def get_filtered_applications(self, filters) -> List[Dict]:
        """Get filtered applications based on criteria"""
        
        applications = await self.get_all_applications()
        
        # Apply filters
        if hasattr(filters, 'app_ids') and filters.app_ids:
            applications = [app for app in applications if app["id"] in filters.app_ids]
        
        if hasattr(filters, 'strategies') and filters.strategies:
            applications = [app for app in applications 
                          if app["strategy"].lower() in [s.lower() for s in filters.strategies]]
        
        if hasattr(filters, 'archetypes') and filters.archetypes:
            applications = [app for app in applications 
                          if app["archetype"] in filters.archetypes]
        
        if hasattr(filters, 'complexity_levels') and filters.complexity_levels:
            applications = [app for app in applications 
                          if app["complexity"] in filters.complexity_levels]
        
        if hasattr(filters, 'risk_levels') and filters.risk_levels:
            applications = [app for app in applications 
                          if app["risk"] in filters.risk_levels]
        
        return applications
    
    async def get_application_by_id(self, app_id: str) -> Optional[Dict]:
        """Get specific application by ID"""
        
        applications = await self.get_all_applications()
        return next((app for app in applications if app["id"] == app_id), None)
    
    async def get_application(self, app_id: str) -> Optional[Dict]:
        """Alias for get_application_by_id - for service integration"""
        return await self.get_application_by_id(app_id)
    
    async def update_strategy(self, app_id: str, strategy: str) -> Optional[Dict]:
        """Update migration strategy for an application"""
        
        applications = await self.get_all_applications()
        
        for app in applications:
            if app["id"] == app_id:
                app["strategy"] = strategy.title()
                # Update risk based on new strategy
                app["risk"] = self.strategy_risk_mapping.get(strategy.title(), "Medium")
                # Recalculate costs and timeline
                app["estimated_cost"] = self._calculate_estimated_cost(app)
                app["timeline_months"] = self._calculate_timeline(app)
                app["annual_savings"] = self._calculate_annual_savings(app)
                
                # Update cache
                self.applications_cache = applications
                
                return app
        
        return None
    
    async def update_application(self, app_id: str, updates: Dict[str, Any]) -> Optional[Dict]:
        """Update application with multiple fields"""
        
        applications = await self.get_all_applications()
        
        for app in applications:
            if app["id"] == app_id:
                # Update provided fields
                for key, value in updates.items():
                    if key in app:
                        app[key] = value
                
                # Recalculate derived fields if strategy or complexity changed
                if "strategy" in updates or "complexity" in updates:
                    app["estimated_cost"] = self._calculate_estimated_cost(app)
                    app["timeline_months"] = self._calculate_timeline(app)
                    app["annual_savings"] = self._calculate_annual_savings(app)
                    app["risk"] = self.strategy_risk_mapping.get(app["strategy"], "Medium")
                
                # Update cache
                self.applications_cache = applications
                
                return app
        
        return None
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh application data from source files"""
        
        try:
            # Load application list from CSV
            csv_path = self.data_folder / "applicationList.csv"
            if not csv_path.exists():
                # Fallback to mock data if CSV doesn't exist
                applications = self._generate_mock_applications()
            else:
                app_df = pd.read_csv(csv_path)
                
                # Load archetype mapping from Excel
                excel_path = self.data_folder / "synthetic_flows_apps_archetype_mapped.xlsx"
                archetype_mapping = {}
                
                if excel_path.exists():
                    archetype_mapping = await self._load_archetype_mapping(excel_path)
                
                # Process applications
                applications = []
                for _, row in app_df.iterrows():
                    app_id = row.get("app_id", f"APP_{len(applications):03d}")
                    app_name = row.get("app_name", f"Application {len(applications) + 1}")
                    
                    # Get archetype from mapping or assign based on name
                    archetype = archetype_mapping.get(app_name, self._infer_archetype_from_name(app_name))
                    
                    # Create application data
                    app_data = self._create_application_data(app_id, app_name, archetype)
                    applications.append(app_data)
            
            self.applications_cache = applications
            self.last_refresh = datetime.now()
            
            return {
                "count": len(applications),
                "timestamp": self.last_refresh.isoformat(),
                "status": "success",
                "source": "csv" if csv_path.exists() else "mock"
            }
            
        except Exception as e:
            # Generate mock data on error
            applications = self._generate_mock_applications()
            self.applications_cache = applications
            self.last_refresh = datetime.now()
            
            return {
                "count": len(applications),
                "timestamp": self.last_refresh.isoformat(),
                "status": "fallback_mock",
                "error": str(e)
            }
    
    def _generate_mock_applications(self) -> List[Dict]:
        """Generate mock applications for testing"""
        
        mock_apps = [
            ("ACDA", "ATM Check Card Disputes API", "Microservices"),
            ("ALE", "Advisor Locator Engine", "Web + API Headless"),
            ("AODSVY", "AOD Survey", "3-Tier"),
            ("APSE", "Appointment Setting (Timetrade)", "SOA"),
            ("BKO", "Banko POC", "Client-Server"),
            ("BLZD", "FICO/Blaze Decisioning", "SOA"),
            ("BLND", "BLEND SSI", "Monolithic"),
            ("CAL", "Calculator", "3-Tier"),
            ("CCMS", "Call Center Management System", "Monolithic"),
            ("CDESK", "Contact Desktop", "Client-Server"),
            ("CFLOW", "Core Banking Flow", "Monolithic"),
            ("DOCMGR", "Document Manager", "3-Tier"),
            ("EBANK", "E-Banking Portal", "Web + API Headless"),
            ("FRAUD", "Fraud Detection System", "Event-Driven"),
            ("LOANAPP", "Loan Application System", "SOA"),
            ("MOBILE", "Mobile Banking App", "Microservices"),
            ("NOTIFY", "Notification Service", "Event-Driven"),
            ("REPORTS", "Reporting Dashboard", "3-Tier"),
            ("SECURITY", "Security Gateway", "Microservices"),
            ("WORKFLOW", "Workflow Engine", "SOA")
        ]
        
        applications = []
        for app_id, app_name, archetype in mock_apps:
            app_data = self._create_application_data(app_id, app_name, archetype)
            applications.append(app_data)
        
        return applications
    
    def _create_application_data(self, app_id: str, app_name: str, archetype: str) -> Dict[str, Any]:
        """Create complete application data structure"""
        
        # Assign strategy based on archetype
        strategy = self._assign_strategy(archetype)
        
        # Create application data
        app_data = {
            "id": app_id,
            "name": app_name,
            "archetype": archetype,
            "strategy": strategy,
            "complexity": self._assign_complexity(archetype),
            "risk": self._assign_risk(strategy),
            "estimated_cost": 0,  # Will be calculated
            "timeline_months": 0,  # Will be calculated
            "annual_savings": 0,  # Will be calculated
            "current_monthly_cost": 0,  # Will be calculated
            "technology_stack": self._infer_technology_stack(archetype),
            "business_criticality": self._assess_business_criticality(app_name),
            "dependencies": self._generate_dependencies(app_name),
            "compliance": self._assess_compliance_requirements(app_name),
            "cloud_ready": self._assess_cloud_readiness(archetype),
            "performance_requirements": self._generate_performance_requirements(archetype),
            "data_requirements": self._generate_data_requirements(archetype),
            "infrastructure": self._generate_infrastructure_info(archetype)
        }
        
        # Calculate derived fields
        app_data["estimated_cost"] = self._calculate_estimated_cost(app_data)
        app_data["timeline_months"] = self._calculate_timeline(app_data)
        app_data["annual_savings"] = self._calculate_annual_savings(app_data)
        app_data["current_monthly_cost"] = self._calculate_current_monthly_cost(app_data)
        
        return app_data
    
    async def _load_archetype_mapping(self, excel_path: Path) -> Dict[str, str]:
        """Load archetype mapping from Excel file"""
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_path, sheet_name=0)
            
            # Extract unique application-archetype mappings
            if "application" in df.columns and "archetype" in df.columns:
                mapping = df.groupby("application")["archetype"].first().to_dict()
                return mapping
            else:
                print(f"Warning: Expected columns not found in {excel_path}")
                return {}
                
        except Exception as e:
            print(f"Warning: Could not load archetype mapping: {str(e)}")
            return {}
    
    def _infer_archetype_from_name(self, app_name: str) -> str:
        """Infer archetype from application name"""
        
        app_lower = app_name.lower()
        
        # Keywords to archetype mapping
        archetype_keywords = {
            "Microservices": ["api", "service", "micro", "container"],
            "Web + API Headless": ["web", "portal", "frontend", "ui"],
            "Event-Driven": ["event", "notify", "queue", "stream"],
            "3-Tier": ["dashboard", "report", "calculator", "manager"],
            "SOA": ["workflow", "engine", "process", "enterprise"],
            "Monolithic": ["core", "main", "banking", "system"],
            "Client-Server": ["desktop", "client", "poc", "legacy"]
        }
        
        for archetype, keywords in archetype_keywords.items():
            if any(keyword in app_lower for keyword in keywords):
                return archetype
        
        return "3-Tier"  # Default archetype
    
    def _assign_strategy(self, archetype: str) -> str:
        """Assign 7 Rs strategy based on archetype"""
        return self.archetype_strategy_mapping.get(archetype, "Rehost")
    
    def _assign_complexity(self, archetype: str) -> str:
        """Assign complexity level based on archetype"""
        return self.archetype_complexity_mapping.get(archetype, "Medium")
    
    def _assign_risk(self, strategy: str) -> str:
        """Assign risk level based on strategy"""
        return self.strategy_risk_mapping.get(strategy, "Medium")
    
    def _calculate_estimated_cost(self, app: Dict) -> float:
        """Calculate estimated migration cost"""
        
        strategy = app["strategy"]
        complexity = app["complexity"]
        
        # Base costs by strategy and complexity (USD)
        base_costs = {
            "Rehost": {"Low": 25000, "Medium": 45000, "High": 75000},
            "Replatform": {"Low": 45000, "Medium": 85000, "High": 140000},
            "Refactor": {"Low": 120000, "Medium": 220000, "High": 350000},
            "Retire": {"Low": 5000, "Medium": 8000, "High": 12000},
            "Retain": {"Low": 1000, "Medium": 1500, "High": 2000},
            "Repurchase": {"Low": 35000, "Medium": 65000, "High": 100000},
            "Relocate": {"Low": 15000, "Medium": 25000, "High": 40000}
        }
        
        strategy_costs = base_costs.get(strategy, base_costs["Rehost"])
        base_cost = strategy_costs.get(complexity, strategy_costs["Medium"])
        
        # Add variation based on business criticality
        criticality = app.get("business_criticality", "Medium")
        criticality_multiplier = {"Critical": 1.5, "High": 1.2, "Medium": 1.0, "Low": 0.8}
        
        # Add random variation (±15%)
        variation = np.random.uniform(0.85, 1.15)
        
        return int(base_cost * criticality_multiplier.get(criticality, 1.0) * variation)
    
    def _calculate_timeline(self, app: Dict) -> int:
        """Calculate estimated timeline in months"""
        
        strategy = app["strategy"]
        complexity = app["complexity"]
        
        # Base timelines by strategy and complexity (months)
        base_timelines = {
            "Rehost": {"Low": 2, "Medium": 3, "High": 4},
            "Replatform": {"Low": 4, "Medium": 6, "High": 8},
            "Refactor": {"Low": 8, "Medium": 12, "High": 18},
            "Retire": {"Low": 1, "Medium": 2, "High": 3},
            "Retain": {"Low": 0, "Medium": 0, "High": 1},
            "Repurchase": {"Low": 3, "Medium": 5, "High": 7},
            "Relocate": {"Low": 2, "Medium": 3, "High": 5}
        }
        
        strategy_timelines = base_timelines.get(strategy, base_timelines["Rehost"])
        base_timeline = strategy_timelines.get(complexity, strategy_timelines["Medium"])
        
        # Add complexity for dependencies
        dependencies = len(app.get("dependencies", []))
        dependency_months = min(dependencies // 3, 3)  # Max 3 additional months
        
        return max(1, base_timeline + dependency_months)
    
    def _calculate_annual_savings(self, app: Dict) -> float:
        """Calculate estimated annual savings"""
        
        strategy = app["strategy"]
        complexity = app["complexity"]
        
        # Annual savings by strategy (USD)
        savings_multipliers = {
            "Rehost": {"Low": 35000, "Medium": 55000, "High": 85000},
            "Replatform": {"Low": 55000, "Medium": 85000, "High": 130000},
            "Refactor": {"Low": 85000, "Medium": 130000, "High": 200000},
            "Retire": {"Low": 20000, "Medium": 35000, "High": 50000},
            "Retain": {"Low": 0, "Medium": 0, "High": 0},
            "Repurchase": {"Low": 25000, "Medium": 45000, "High": 70000},
            "Relocate": {"Low": 30000, "Medium": 50000, "High": 75000}
        }
        
        strategy_savings = savings_multipliers.get(strategy, savings_multipliers["Rehost"])
        base_savings = strategy_savings.get(complexity, strategy_savings["Medium"])
        
        # Add random variation (±10%)
        variation = np.random.uniform(0.9, 1.1)
        return int(base_savings * variation)
    
    def _calculate_current_monthly_cost(self, app: Dict) -> float:
        """Calculate current monthly operational cost"""
        
        complexity = app["complexity"]
        criticality = app.get("business_criticality", "Medium")
        
        # Base monthly costs
        base_costs = {"Low": 3000, "Medium": 6000, "High": 12000}
        criticality_multiplier = {"Critical": 2.0, "High": 1.5, "Medium": 1.0, "Low": 0.7}
        
        base_cost = base_costs.get(complexity, base_costs["Medium"])
        multiplier = criticality_multiplier.get(criticality, 1.0)
        
        return int(base_cost * multiplier)
    
    def _infer_technology_stack(self, archetype: str) -> List[str]:
        """Infer technology stack from archetype"""
        
        tech_mapping = {
            "Microservices": ["Docker", "Kubernetes", "Spring Boot", "Node.js"],
            "Web + API Headless": ["React", "Node.js", "REST APIs", "JavaScript"],
            "3-Tier": ["Java EE", "Oracle DB", "Apache", "SQL"],
            "SOA": ["ESB", "SOAP", "XML", "Enterprise Services"],
            "Event-Driven": ["Kafka", "RabbitMQ", "Event Streaming", "Message Queues"],
            "Monolithic": ["Java/.NET", "Monolithic DB", "Legacy Framework"],
            "Client-Server": ["Desktop Apps", "Client/Server DB", "Legacy Protocols"]
        }
        
        return tech_mapping.get(archetype, ["Mixed Technology Stack"])
    
    def _assess_business_criticality(self, app_name: str) -> str:
        """Assess business criticality based on application name"""
        
        app_lower = app_name.lower()
        
        for criticality, keywords in self.criticality_keywords.items():
            if any(keyword in app_lower for keyword in keywords):
                return criticality
        
        return "Medium"  # Default
    
    def _generate_dependencies(self, app_name: str) -> List[str]:
        """Generate realistic dependencies based on application type"""
        
        app_lower = app_name.lower()
        dependencies = []
        
        # Common dependencies based on application type
        if any(keyword in app_lower for keyword in ["api", "service"]):
            dependencies.extend(["authentication_service", "database_service"])
        
        if any(keyword in app_lower for keyword in ["web", "portal", "ui"]):
            dependencies.extend(["api_gateway", "content_service"])
        
        if any(keyword in app_lower for keyword in ["core", "banking", "main"]):
            dependencies.extend(["database", "security_service", "audit_service"])
        
        if any(keyword in app_lower for keyword in ["report", "analytics"]):
            dependencies.extend(["data_warehouse", "etl_service"])
        
        # Add random additional dependencies
        additional_deps = ["logging_service", "monitoring_service", "cache_service", "message_queue"]
        dependencies.extend(np.random.choice(additional_deps, size=np.random.randint(0, 3), replace=False))
        
        return list(set(dependencies))  # Remove duplicates
    
    def _assess_compliance_requirements(self, app_name: str) -> List[str]:
        """Assess compliance requirements based on application type"""
        
        app_lower = app_name.lower()
        compliance = []
        
        # Financial applications typically need these
        if any(keyword in app_lower for keyword in ["bank", "card", "payment", "loan", "credit"]):
            compliance.extend(["PCI", "SOX", "FFIEC"])
        
        if any(keyword in app_lower for keyword in ["customer", "personal", "data"]):
            compliance.extend(["GDPR", "CCPA"])
        
        if any(keyword in app_lower for keyword in ["security", "auth", "fraud"]):
            compliance.extend(["SOC2", "ISO27001"])
        
        return list(set(compliance))
    
    def _assess_cloud_readiness(self, archetype: str) -> bool:
        """Assess if application is cloud-ready"""
        
        cloud_ready_archetypes = ["Microservices", "Web + API Headless", "Event-Driven"]
        return archetype in cloud_ready_archetypes
    
    def _generate_performance_requirements(self, archetype: str) -> Dict[str, Any]:
        """Generate performance requirements based on archetype"""
        
        perf_profiles = {
            "Microservices": {"response_time_ms": 100, "throughput_rps": 1000},
            "Web + API Headless": {"response_time_ms": 200, "throughput_rps": 500},
            "3-Tier": {"response_time_ms": 500, "throughput_rps": 200},
            "SOA": {"response_time_ms": 1000, "throughput_rps": 100},
            "Event-Driven": {"response_time_ms": 50, "throughput_rps": 2000},
            "Monolithic": {"response_time_ms": 1000, "throughput_rps": 100},
            "Client-Server": {"response_time_ms": 2000, "throughput_rps": 50}
        }
        
        return perf_profiles.get(archetype, {"response_time_ms": 500, "throughput_rps": 200})
    
    def _generate_data_requirements(self, archetype: str) -> Dict[str, Any]:
        """Generate data requirements based on archetype"""
        
        data_profiles = {
            "Microservices": {"storage_gb": 100, "backup_frequency": "daily"},
            "Web + API Headless": {"storage_gb": 50, "backup_frequency": "daily"},
            "3-Tier": {"storage_gb": 500, "backup_frequency": "daily"},
            "SOA": {"storage_gb": 1000, "backup_frequency": "daily"},
            "Event-Driven": {"storage_gb": 200, "backup_frequency": "hourly"},
            "Monolithic": {"storage_gb": 2000, "backup_frequency": "daily"},
            "Client-Server": {"storage_gb": 100, "backup_frequency": "weekly"}
        }
        
        return data_profiles.get(archetype, {"storage_gb": 200, "backup_frequency": "daily"})
    
    def _generate_infrastructure_info(self, archetype: str) -> Dict[str, Any]:
        """Generate infrastructure information based on archetype"""
        
        infra_profiles = {
            "Microservices": {"instances": 3, "cpu_cores": 2, "memory_gb": 4},
            "Web + API Headless": {"instances": 2, "cpu_cores": 2, "memory_gb": 4},
            "3-Tier": {"instances": 3, "cpu_cores": 4, "memory_gb": 8},
            "SOA": {"instances": 4, "cpu_cores": 4, "memory_gb": 16},
            "Event-Driven": {"instances": 2, "cpu_cores": 2, "memory_gb": 4},
            "Monolithic": {"instances": 2, "cpu_cores": 8, "memory_gb": 16},
            "Client-Server": {"instances": 1, "cpu_cores": 2, "memory_gb": 4}
        }
        
        return infra_profiles.get(archetype, {"instances": 2, "cpu_cores": 4, "memory_gb": 8})
    
    def _calculate_distribution(self, applications: List[Dict], field: str) -> Dict[str, int]:
        """Calculate distribution of applications by field"""
        
        distribution = {}
        for app in applications:
            value = app.get(field, "Unknown")
            distribution[value] = distribution.get(value, 0) + 1
        
        return distribution
    
    def _needs_refresh(self) -> bool:
        """Check if data needs refresh (refresh every hour)"""
        
        if self.last_refresh is None:
            return True
        
        time_diff = datetime.now() - self.last_refresh
        return time_diff.total_seconds() > 3600  # 1 hour
    
    async def export_portfolio(self, format: str = "excel") -> Dict[str, Any]:
        """Export portfolio data to results folder"""
        
        try:
            # Use results folder structure
            base_results_dir = Path("results")
            
            if format == "excel":
                export_dir = base_results_dir / "excel"
            else:
                export_dir = base_results_dir / "document"
            
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_analysis_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == "excel":
                applications = await self.get_all_applications()
                
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Main application data
                    app_df = pd.DataFrame(applications)
                    app_df.to_excel(writer, sheet_name='Applications', index=False)
                    
                    # Portfolio summary
                    portfolio = await self.get_portfolio()
                    summary_data = []
                    for key, value in portfolio["summary_metrics"].items():
                        summary_data.append({"Metric": key, "Value": value})
                    
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Portfolio Summary', index=False)
                    
                    # Distribution analysis
                    distributions = {
                        "Strategy": portfolio["strategy_distribution"],
                        "Archetype": portfolio["archetype_distribution"],
                        "Complexity": portfolio["complexity_distribution"],
                        "Risk": portfolio["risk_distribution"]
                    }
                    
                    dist_data = []
                    for dist_type, dist_values in distributions.items():
                        for category, count in dist_values.items():
                            dist_data.append({
                                "Distribution_Type": dist_type,
                                "Category": category,
                                "Count": count,
                                "Percentage": round(count / len(applications) * 100, 1) if applications else 0
                            })
                    
                    pd.DataFrame(dist_data).to_excel(writer, sheet_name='Distributions', index=False)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir),
                "applications_exported": len(await self.get_all_applications())
            }
            
        except Exception as e:
            raise Exception(f"Error exporting portfolio: {str(e)}")

    # Additional methods for service integration
    async def get_applications_for_cost_analysis(self, app_ids: List[str]) -> List[Dict]:
        """Get applications formatted for cost analysis"""
        return await self.get_applications(app_ids)
    
    async def get_applications_for_migration_analysis(self, app_ids: List[str]) -> List[Dict]:
        """Get applications formatted for migration analysis"""
        return await self.get_applications(app_ids)