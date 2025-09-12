"""
Archetype Enhancement Service
Place this file at: services/archetype_enhancement.py

This enhances your existing archetype service with LucidChart generation
without breaking existing functionality.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import asyncio
import re

# Import your existing services
try:
    from .archetype_service import ArchetypeService
    from .enhanced_diagram_generator import EnhancedDiagramService
    from .archetype_lucid_stencils import (
        ArchetypeType, ArchetypeLayoutEngine, LucidChartGenerator
    )
    SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some services not available: {e}")
    SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

class ArchetypeEnhancementService:
    """
    Enhancement service that adds LucidChart generation to your existing archetype service.
    This works alongside your existing functionality without breaking changes.
    """
    
    def __init__(self):
        # Initialize existing services
        self.archetype_service = ArchetypeService() if SERVICES_AVAILABLE else None
        self.enhanced_diagram_service = EnhancedDiagramService() if SERVICES_AVAILABLE else None
        
        # Initialize new LucidChart components
        if SERVICES_AVAILABLE:
            self.layout_engine = ArchetypeLayoutEngine()
            self.lucid_generator = LucidChartGenerator()
        
        self.archetype_mapping = {
            "monolithic": ArchetypeType.MONOLITHIC,
            "three_tier": ArchetypeType.THREE_TIER,
            "microservices": ArchetypeType.MICROSERVICES,
            "event_driven": ArchetypeType.EVENT_DRIVEN,
            "soa": ArchetypeType.SOA,
            "serverless": ArchetypeType.SERVERLESS,
            "client_server": ArchetypeType.CLIENT_SERVER,
            "cloud_native": ArchetypeType.CLOUD_NATIVE,
            "data_pipeline": ArchetypeType.DATA_PIPELINE
        }
        
        logger.info("ArchetypeEnhancementService initialized")
    
    async def enhance_diagram_generation(self, diagram_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance your existing diagram generation with archetype-specific LucidChart features.
        
        This method can be called from your existing archetype router without breaking changes.
        It adds LucidChart optimization while maintaining all existing functionality.
        """
        
        if not SERVICES_AVAILABLE:
            return {
                "success": False,
                "error": "Enhancement services not available",
                "fallback": "Using standard diagram generation"
            }
        
        try:
            # Extract data from your existing request format
            applications = diagram_request.get("applications", [])
            archetype_hint = diagram_request.get("archetype", None)
            app_name = diagram_request.get("app_name", None)  # NEW
            job_id = diagram_request.get("job_id", None)      # NEW
            
            # Infer app_name from applications if not provided
            if not app_name and applications:
                app_name = applications[0].get("name", "Application")
            
            # Step 1: Use your existing archetype classification if no hint provided
            if not archetype_hint and self.archetype_service:
                classification_result = self.archetype_service.classify_application_portfolio({
                    "applications": applications
                })
                archetype_hint = classification_result.get("primary_archetype", "three_tier")
            
            # Convert to our archetype type
            archetype_type = self._convert_archetype_string(archetype_hint or "three_tier")
            
            # Step 2: Generate archetype-optimized layout
            layout = self.layout_engine.generate_layout_for_archetype(archetype_type, applications)
            
            # Step 3: Generate LucidChart XML
            lucid_xml = self.lucid_generator.generate_lucidchart_xml(archetype_type, applications)
            
            # Step 4: Save LucidChart file
            lucid_file_path = await self._save_lucidchart_file(
                        lucid_xml, archetype_hint, app_name, job_id  # Pass the new parameters
                    )
                    
            # Step 5: Call your existing enhanced diagram service for other formats
            enhanced_result = None
            if self.enhanced_diagram_service:
                try:
                    enhanced_result = await self.enhanced_diagram_service.generate_professional_diagram(
                        diagram_type=f"archetype_{archetype_hint}",
                        data={
                            "applications": applications,
                            "archetype_info": {
                                "detected_archetype": archetype_hint,
                                "layout": layout
                            }
                        },
                        quality_level=diagram_request.get("quality_level", "professional")
                    )
                except Exception as e:
                    logger.warning(f"Enhanced diagram service failed: {e}")
            
            # Combine results
            result = {
                "success": True,
                "archetype_detected": archetype_hint,
                "archetype_optimized": True,
                "lucidchart_file": str(lucid_file_path) if lucid_file_path else None,
                "filename": lucid_file_path.name if lucid_file_path else None,  # NEW
                "app_name": app_name,  # NEW
                "job_id": job_id,      # NEW
                "layout_info": {
                    "components": len(layout["components"]),
                    "connections": len(layout["connections"]),
                    "archetype_specific": True
                },
                "files": []
            }
            
            # Add LucidChart file to results
            if lucid_file_path:
                result["files"].append({
                    "format": "lucidchart",
                    "filename": lucid_file_path.name,
                    "file_path": str(lucid_file_path),
                    "app_name": app_name,
                    "job_id": job_id,
                    "archetype_optimized": True,
                    "features": [
                        f"Optimized for {archetype_hint} architecture",
                        "Professional stencils and layouts", 
                        "Import directly into LucidChart"
                    ]
                })
            
            # Add enhanced diagram files if available
            if enhanced_result and enhanced_result.get("success"):
                enhanced_files = enhanced_result.get("files", [])
                result["files"].extend(enhanced_files)
                result["enhanced_diagram_job_id"] = enhanced_result.get("job_id")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_available": True
            }
    
    async def get_archetype_stencils(self, archetype: str) -> Dict[str, Any]:
        """Get available stencils for a specific archetype"""
        
        if not SERVICES_AVAILABLE:
            return {"stencils": [], "error": "Services not available"}
        
        try:
            archetype_type = self._convert_archetype_string(archetype)
            stencil_ids = self.layout_engine.stencil_library.get_stencils_for_archetype(archetype_type)
            
            stencils = []
            for stencil_id in stencil_ids:
                stencil = self.layout_engine.stencil_library.get_stencil(stencil_id)
                if stencil:
                    stencils.append({
                        "id": stencil.id,
                        "name": stencil.name,
                        "shape_type": stencil.shape_type,
                        "colors": {
                            "fill": stencil.fill_color,
                            "border": stencil.border_color
                        },
                        "icon": stencil.icon
                    })
            
            return {
                "archetype": archetype,
                "stencils": stencils,
                "count": len(stencils)
            }
            
        except Exception as e:
            return {"error": str(e), "stencils": []}
    
    async def preview_archetype_layout(self, archetype: str, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview layout for archetype without generating full diagram"""
        
        if not SERVICES_AVAILABLE:
            return {"error": "Services not available"}
        
        try:
            archetype_type = self._convert_archetype_string(archetype)
            layout = self.layout_engine.generate_layout_for_archetype(archetype_type, applications)
            
            return {
                "success": True,
                "archetype": archetype,
                "preview": {
                    "canvas_size": layout["canvas"],
                    "component_count": len(layout["components"]),
                    "connection_count": len(layout["connections"]),
                    "components": [
                        {
                            "name": comp["name"],
                            "type": comp["type"],
                            "position": comp["position"]
                        }
                        for comp in layout["components"]
                    ]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_supported_archetypes(self) -> Dict[str, Any]:
        """Get list of supported archetypes with descriptions"""
        
        archetypes = {}
        for archetype_str, archetype_type in self.archetype_mapping.items():
            if SERVICES_AVAILABLE:
                stencil_count = len(self.layout_engine.stencil_library.get_stencils_for_archetype(archetype_type))
            else:
                stencil_count = 0
            
            archetypes[archetype_str] = {
                "name": archetype_str.replace("_", " ").title(),
                "description": self._get_archetype_description(archetype_str),
                "stencil_count": stencil_count,
                "lucidchart_optimized": SERVICES_AVAILABLE
            }
        
        return {
            "supported_archetypes": archetypes,
            "total_count": len(archetypes),
            "enhancement_available": SERVICES_AVAILABLE
        }
    
    def _convert_archetype_string(self, archetype_str: str) -> ArchetypeType:
        """Convert archetype string to enum type"""
        return self.archetype_mapping.get(archetype_str, ArchetypeType.THREE_TIER)
    
    def _get_archetype_description(self, archetype: str) -> str:
        """Get description for archetype"""
        descriptions = {
            "monolithic": "Single-tier application with integrated components",
            "three_tier": "Standard enterprise structure with presentation, application, and data tiers",
            "microservices": "Application composed of independent services",
            "event_driven": "Services communicating through message queues and events",
            "soa": "Service-oriented architecture with enterprise service bus",
            "serverless": "Stateless compute functions triggered by events",
            "client_server": "Traditional client applications connecting to backend services",
            "cloud_native": "Applications built specifically for cloud environments",
            "data_pipeline": "Batch or stream processing for analytics and BI"
        }
        return descriptions.get(archetype, "Architecture pattern")
    
    async def _save_lucidchart_file(self, xml_content: str, archetype: str, 
                                   app_name: str = None, job_id: str = None) -> Optional[Path]:
        """Save LucidChart XML to file with appname and jobid tagging"""
        try:
            # Create results directory structure
            results_dir = Path("results")
            lucid_dir = results_dir / "lucid"
            lucid_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean app name for filename (remove invalid characters)
            if app_name:
                clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name)
                clean_app_name = re.sub(r'\s+', '_', clean_app_name)
            else:
                clean_app_name = "Application"
            
            # Use provided job_id or generate short one
            if not job_id:
                job_id = str(uuid.uuid4())[:8]
            
            # Generate filename with appname and jobid
            filename = f"{clean_app_name}_{archetype}_{job_id}.lucid"
            file_path = lucid_dir / filename
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"LucidChart file saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save LucidChart file: {e}")
            return None


# Convenience function for your existing router
async def enhance_archetype_diagram(diagram_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function that can be imported and used in your existing archetype router.
    
    Usage in your routers/archetype_router.py:
    
    from services.archetype_enhancement import enhance_archetype_diagram
    
    @router.post("/generate-diagram")  # Your existing endpoint
    async def generate_diagram(request: DiagramRequest):
        # Your existing logic...
        
        # Add LucidChart enhancement
        enhanced_result = await enhance_archetype_diagram(request.dict())
        
        # Merge with your existing results
        # ... your response logic
    """
    service = ArchetypeEnhancementService()
    return await service.enhance_diagram_generation(diagram_request)