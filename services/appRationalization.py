"""
App Rationalization Service
Handles application portfolio management and 7 Rs migration analysis
Integrates with existing banking data sources
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from pathlib import Path
import openpyxl
import json

class AppRationalizationService:
    """Service for managing application portfolio data and 7 Rs analysis"""
    
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
            "Client-Server": "Retire",
            "Unknown": "Rehost"
        }
        
        # Complexity mapping
        self.archetype_complexity_mapping = {
            "Microservices": "Medium",
            "Web + API Headless": "Low",
            "3-Tier": "Medium", 
            "SOA": "High",
            "Event-Driven": "Medium",
            "Monolithic": "High",
            "Client-Server": "Low",
            "Unknown": "Medium"
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
        
        # Cost and savings estimates (USD)
        self.strategy_cost_mapping = {
            "Rehost": {"base_cost": 45000, "annual_savings": 35000},
            "Replatform": {"base_cost": 85000, "annual_savings": 75000},
            "Refactor": {"base_cost": 220000, "annual_savings": 150000},
            "Retire": {"base_cost": 8000, "annual_savings": 45000},
            "Retain": {"base_cost": 1500, "annual_savings": 0},
            "Repurchase": {"base_cost": 65000, "annual_savings": 55000},
            "Relocate": {"base_cost": 25000, "annual_savings": 30000}
        }
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get complete application portfolio with analysis"""
        
        applications = await self.get_all_applications()
        
        # Calculate distributions
        strategy_distribution = self._calculate_distribution(applications, "strategy")
        archetype_distribution = self._calculate_distribution(applications, "archetype")
        complexity_distribution = self._calculate_distribution(applications, "complexity")
        
        return {
            "applications": applications,
            "total_count": len(applications),
            "strategy_distribution": strategy_distribution,
            "archetype_distribution": archetype_distribution,
            "complexity_distribution": complexity_distribution
        }
    
    async def get_all_applications(self) -> List[Dict]:
        """Get all applications with 7 Rs analysis"""
        
        if self.applications_cache is None or self._needs_refresh():
            await self.refresh_data()
        
        return self.applications_cache or []
    
    async def get_filtered_applications(self, filters) -> List[Dict]:
        """Get filtered applications based on criteria"""
        
        applications = await self.get_all_applications()
        
        # Apply filters
        if filters.app_ids:
            applications = [app for app in applications if app["id"] in filters.app_ids]
        
        if filters.strategies:
            applications = [app for app in applications 
                          if app["strategy"].lower() in [s.lower() for s in filters.strategies]]
        
        if filters.archetypes:
            applications = [app for app in applications 
                          if app["archetype"] in filters.archetypes]
        
        if filters.complexity_levels:
            applications = [app for app in applications 
                          if app["complexity"] in filters.complexity_levels]
        
        if filters.risk_levels:
            applications = [app for app in applications 
                          if app["risk"] in filters.risk_levels]
        
        return applications
    
    async def get_application_by_id(self, app_id: str) -> Optional[Dict]:
        """Get specific application by ID"""
        
        applications = await self.get_all_applications()
        return next((app for app in applications if app["id"] == app_id), None)
    
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
    
    async def refresh_data(self) -> Dict[str, Any]:
        """Refresh application data from source files"""
        
        try:
            # Load application list from CSV
            csv_path = self.data_folder / "applicationList.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Application list not found: {csv_path}")
            
            app_df = pd.read_csv(csv_path)
            
            # Load archetype mapping from Excel
            excel_path = self.data_folder / "synthetic_flows_apps_archetype_mapped.xlsx"
            archetype_mapping = {}
            
            if excel_path.exists():
                # Read Excel file and extract archetype mapping
                archetype_mapping = await self._load_archetype_mapping(excel_path)
            
            # Process applications
            applications = []
            for _, row in app_df.iterrows():
                app_id = str(row["app_id"]).strip()
                app_name = str(row["app_name"]).strip()
                
                # Skip empty rows
                if not app_id or app_id == 'nan':
                    continue
                
                # Get archetype from mapping or assign default
                archetype = archetype_mapping.get(app_name, "Unknown")
                
                # Assign strategy based on archetype
                strategy = self._assign_strategy(archetype)
                
                # Calculate other attributes
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
                    "technology_stack": self._infer_technology_stack(archetype),
                    "business_criticality": self._assess_business_criticality(app_name),
                    "dependencies": []  # Would be populated from dependency analysis
                }
                
                # Calculate derived fields
                app_data["estimated_cost"] = self._calculate_estimated_cost(app_data)
                app_data["timeline_months"] = self._calculate_timeline(app_data)
                app_data["annual_savings"] = self._calculate_annual_savings(app_data)
                
                applications.append(app_data)
            
            self.applications_cache = applications
            self.last_refresh = datetime.now()
            
            return {
                "count": len(applications),
                "timestamp": self.last_refresh.isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            raise Exception(f"Error refreshing application data: {str(e)}")
    
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
        
        # Get base cost for strategy
        strategy_data = self.strategy_cost_mapping.get(strategy, self.strategy_cost_mapping["Rehost"])
        base_cost = strategy_data["base_cost"]
        
        # Apply complexity multiplier
        complexity_multipliers = {"Low": 0.7, "Medium": 1.0, "High": 1.5}
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # Add random variation (±20%)
        variation = np.random.uniform(0.8, 1.2)
        
        return int(base_cost * multiplier * variation)
    
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
        
        # Add random variation (±1 month)
        variation = np.random.randint(-1, 2)
        return max(1, base_timeline + variation)
    
    def _calculate_annual_savings(self, app: Dict) -> float:
        """Calculate estimated annual savings"""
        
        strategy = app["strategy"]
        complexity = app["complexity"]
        
        # Get base savings for strategy
        strategy_data = self.strategy_cost_mapping.get(strategy, self.strategy_cost_mapping["Rehost"])
        base_savings = strategy_data["annual_savings"]
        
        # Apply complexity multiplier
        complexity_multipliers = {"Low": 0.8, "Medium": 1.0, "High": 1.3}
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # Add random variation (±15%)
        variation = np.random.uniform(0.85, 1.15)
        
        return int(base_savings * multiplier * variation)
    
    def _infer_technology_stack(self, archetype: str) -> str:
        """Infer technology stack from archetype"""
        
        tech_mapping = {
            "Microservices": "Docker, Kubernetes, Spring Boot",
            "Web + API Headless": "React, Node.js, REST APIs",
            "3-Tier": "Java EE, Oracle DB, Apache",
            "SOA": "ESB, SOAP, Enterprise Services",
            "Event-Driven": "Kafka, Message Queues, Event Streaming",
            "Monolithic": "Legacy Java/.NET, Monolithic DB",
            "Client-Server": "Desktop Apps, Client/Server DB",
            "Unknown": "Mixed Technology Stack"
        }
        
        return tech_mapping.get(archetype, "Mixed Technology Stack")
    
    def _assess_business_criticality(self, app_name: str) -> str:
        """Assess business criticality based on application name"""
        
        critical_keywords = ["core", "primary", "main", "critical", "auth", "security", "card", "dispute", "fraud"]
        high_keywords = ["bank", "customer", "account", "transaction", "payment"]
        
        app_lower = app_name.lower()
        
        if any(keyword in app_lower for keyword in critical_keywords):
            return "Critical"
        elif any(keyword in app_lower for keyword in high_keywords):
            return "High"
        else:
            return "Medium"
    
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
    
    async def export_analysis(self, app_ids: List[str], format: str) -> Dict[str, Any]:
        """Export app rationalization analysis to results folder structure"""
        
        try:
            applications = await self.get_all_applications()
            
            # Filter applications if specific IDs provided
            if app_ids:
                applications = [app for app in applications if app["id"] in app_ids]
            
            # Use results folder structure
            base_results_dir = Path("results")
            
            # Determine export directory based on format
            if format == "excel":
                export_dir = base_results_dir / "excel"
            elif format == "pdf":
                export_dir = base_results_dir / "pdf"
            elif format == "json":
                export_dir = base_results_dir / "document"  # JSON goes to document folder
            else:
                export_dir = base_results_dir / "document"  # Default to document folder
            
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format == "json":
                filename = f"app_rationalization_{timestamp}.json"
                filepath = export_dir / filename
                
                export_data = {
                    "report_metadata": {
                        "title": "Application Rationalization Analysis",
                        "generated_at": datetime.now().isoformat(),
                        "total_applications": len(applications),
                        "export_format": "json"
                    },
                    "applications": applications,
                    "summary": {
                        "strategy_distribution": self._calculate_distribution(applications, "strategy"),
                        "archetype_distribution": self._calculate_distribution(applications, "archetype"),
                        "complexity_distribution": self._calculate_distribution(applications, "complexity"),
                        "total_estimated_cost": sum(app['estimated_cost'] for app in applications),
                        "total_annual_savings": sum(app['annual_savings'] for app in applications),
                        "average_timeline_months": np.mean([app['timeline_months'] for app in applications]) if applications else 0
                    }
                }
                
                with open(filepath, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
            elif format == "excel":
                filename = f"app_rationalization_{timestamp}.xlsx"
                filepath = export_dir / filename
                
                # Create DataFrame
                df = pd.DataFrame(applications)
                
                # Write to Excel with multiple sheets
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Applications sheet
                    df.to_excel(writer, sheet_name='Applications', index=False)
                    
                    # Summary sheet
                    summary_data = {
                        "Metric": [
                            "Total Applications", 
                            "Total Estimated Cost", 
                            "Total Annual Savings", 
                            "Average Timeline (months)",
                            "ROI (3-year)",
                            "Payback Period (months)"
                        ],
                        "Value": [
                            len(applications),
                            f"${sum(app['estimated_cost'] for app in applications):,.0f}",
                            f"${sum(app['annual_savings'] for app in applications):,.0f}",
                            f"{np.mean([app['timeline_months'] for app in applications]):.1f}",
                            f"{self._calculate_roi(applications):.1f}%",
                            f"{self._calculate_payback_period(applications):.1f}"
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Strategy Distribution sheet
                    strategy_dist = self._calculate_distribution(applications, "strategy")
                    strategy_df = pd.DataFrame(list(strategy_dist.items()), columns=['Strategy', 'Count'])
                    strategy_df.to_excel(writer, sheet_name='Strategy Distribution', index=False)
                    
                    # Cost Analysis sheet
                    cost_analysis = []
                    for strategy in strategy_dist.keys():
                        strategy_apps = [app for app in applications if app['strategy'] == strategy]
                        if strategy_apps:
                            cost_analysis.append({
                                'Strategy': strategy,
                                'Applications': len(strategy_apps),
                                'Total Cost': sum(app['estimated_cost'] for app in strategy_apps),
                                'Total Savings': sum(app['annual_savings'] for app in strategy_apps),
                                'Avg Timeline': np.mean([app['timeline_months'] for app in strategy_apps])
                            })
                    
                    if cost_analysis:
                        pd.DataFrame(cost_analysis).to_excel(writer, sheet_name='Cost Analysis', index=False)
            
            elif format == "pdf":
                filename = f"app_rationalization_{timestamp}.pdf"
                filepath = export_dir / filename
                
                # Generate comprehensive PDF report using reportlab
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                
                doc = SimpleDocTemplate(str(filepath), pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    alignment=1  # Center alignment
                )
                story.append(Paragraph("Application Rationalization Analysis", title_style))
                story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                # Executive Summary
                story.append(Paragraph("Executive Summary", styles['Heading2']))
                summary_text = f"""
                This analysis covers {len(applications)} applications with a total estimated migration cost of 
                ${sum(app['estimated_cost'] for app in applications):,.0f} and projected annual savings of 
                ${sum(app['annual_savings'] for app in applications):,.0f}.
                """
                story.append(Paragraph(summary_text, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                # Strategy Distribution Table
                story.append(Paragraph("Strategy Distribution", styles['Heading2']))
                strategy_data = [['Strategy', 'Count', 'Percentage']]
                strategy_dist = self._calculate_distribution(applications, "strategy")
                total_apps = len(applications)
                
                for strategy, count in strategy_dist.items():
                    percentage = (count / total_apps * 100) if total_apps > 0 else 0
                    strategy_data.append([strategy, str(count), f"{percentage:.1f}%"])
                
                strategy_table = Table(strategy_data)
                strategy_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(strategy_table)
                story.append(Spacer(1, 0.3*inch))
                
                # Applications Detail
                story.append(Paragraph("Application Details", styles['Heading2']))
                app_data = [['Application', 'Strategy', 'Cost', 'Annual Savings', 'Timeline']]
                
                for app in applications[:20]:  # Limit to first 20 for PDF readability
                    app_data.append([
                        app['name'][:30] + "..." if len(app['name']) > 30 else app['name'],
                        app['strategy'],
                        f"${app['estimated_cost']:,.0f}",
                        f"${app['annual_savings']:,.0f}",
                        f"{app['timeline_months']}m"
                    ])
                
                app_table = Table(app_data)
                app_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(app_table)
                
                if len(applications) > 20:
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"Note: Showing first 20 of {len(applications)} applications", styles['Italic']))
                
                doc.build(story)
            
            return {
                "file_path": str(filepath),
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "export_directory": str(export_dir),
                "applications_exported": len(applications)
            }
            
        except Exception as e:
            raise Exception(f"Error exporting analysis: {str(e)}")
    
    def _calculate_roi(self, applications: List[Dict]) -> float:
        """Calculate 3-year ROI percentage"""
        total_cost = sum(app['estimated_cost'] for app in applications)
        total_annual_savings = sum(app['annual_savings'] for app in applications)
        
        if total_cost == 0:
            return 0
        
        three_year_savings = total_annual_savings * 3
        roi = ((three_year_savings - total_cost) / total_cost) * 100
        return roi
    
    def _calculate_payback_period(self, applications: List[Dict]) -> float:
        """Calculate payback period in months"""
        total_cost = sum(app['estimated_cost'] for app in applications)
        total_annual_savings = sum(app['annual_savings'] for app in applications)
        
        if total_annual_savings == 0:
            return 999  # Return high number if no savings
        
        payback_years = total_cost / total_annual_savings
        return payback_years * 12  # Convert to months