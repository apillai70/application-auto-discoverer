"""
Template-Based Archetype Stencil Library for LucidChart Integration
Place this file at: services/archetype_lucid_stencils.py

This loads stencils and layouts from YAML templates instead of hardcoding them.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import xml.etree.ElementTree as ET
from xml.dom import minidom
import yaml
import json
import math
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ArchetypeType(Enum):
    MONOLITHIC = "monolithic"
    THREE_TIER = "three_tier"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    SOA = "soa"
    SERVERLESS = "serverless"
    CLIENT_SERVER = "client_server"
    CLOUD_NATIVE = "cloud_native"
    DATA_PIPELINE = "data_pipeline"

@dataclass
class LucidStencil:
    """Defines a LucidChart stencil component loaded from template"""
    id: str
    name: str
    shape_type: str
    width: float
    height: float
    fill_color: str
    border_color: str
    border_width: int
    corner_radius: int
    icon: str
    text_size: int
    font: str
    category: str

class TemplateLoader:
    """Loads and caches YAML templates"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self._stencil_cache = None
        self._layout_cache = None
    
    def load_stencil_library(self) -> Dict[str, Any]:
        """Load stencil library from YAML template"""
        if self._stencil_cache is not None:
            return self._stencil_cache
        
        stencil_path = self.templates_dir / "stencil_library.yaml"
        
        if not stencil_path.exists():
            logger.warning(f"Stencil library template not found: {stencil_path}")
            return self._get_fallback_stencils()
        
        try:
            with open(stencil_path, 'r', encoding='utf-8') as f:
                self._stencil_cache = yaml.safe_load(f)
                logger.info(f"Loaded stencil library from {stencil_path}")
                return self._stencil_cache
        except Exception as e:
            logger.error(f"Error loading stencil library: {e}")
            return self._get_fallback_stencils()
    
    def load_layout_templates(self) -> Dict[str, Any]:
        """Load layout templates from YAML"""
        if self._layout_cache is not None:
            return self._layout_cache
        
        layout_path = self.templates_dir / "layout_templates.yaml"
        
        if not layout_path.exists():
            logger.warning(f"Layout templates not found: {layout_path}")
            return self._get_fallback_layouts()
        
        try:
            with open(layout_path, 'r', encoding='utf-8') as f:
                self._layout_cache = yaml.safe_load(f)
                logger.info(f"Loaded layout templates from {layout_path}")
                return self._layout_cache
        except Exception as e:
            logger.error(f"Error loading layout templates: {e}")
            return self._get_fallback_layouts()
    
    def _get_fallback_stencils(self) -> Dict[str, Any]:
        """Fallback stencil definitions if template file not found"""
        return {
            "stencils": {
                "web_server": {
                    "name": "Web Server",
                    "shape_type": "rectangle",
                    "dimensions": {"width": 120, "height": 80},
                    "styling": {"fill_color": "#4ECDC4", "border_color": "#45B7D1", "border_width": 2, "corner_radius": 8},
                    "display": {"icon": "WEB", "text_size": 10, "font": "Arial"},
                    "category": "web_frontend"
                },
                "database": {
                    "name": "Database", 
                    "shape_type": "cylinder",
                    "dimensions": {"width": 100, "height": 120},
                    "styling": {"fill_color": "#6C5CE7", "border_color": "#5F3DC4", "border_width": 2, "corner_radius": 8},
                    "display": {"icon": "DB", "text_size": 10, "font": "Arial"},
                    "category": "data_storage"
                }
            },
            "archetype_stencils": {
                "monolithic": ["web_server", "database"],
                "three_tier": ["web_server", "database"],
                "microservices": ["web_server", "database"]
            }
        }
    
    def _get_fallback_layouts(self) -> Dict[str, Any]:
        """Fallback layout definitions if template file not found"""
        return {
            "layouts": {
                "monolithic": {
                    "name": "Monolithic Architecture",
                    "canvas": {"width": 800, "height": 600},
                    "pattern": "vertical_stack"
                }
            }
        }

class ArchetypeStencilLibrary:
    """Template-based stencil library for LucidChart components"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.template_loader = TemplateLoader(templates_dir)
        self.stencils = self._load_stencils()
        self.archetype_mappings = self._load_archetype_mappings()
    
    def _load_stencils(self) -> Dict[str, LucidStencil]:
        """Load stencils from template files"""
        stencil_data = self.template_loader.load_stencil_library()
        stencils = {}
        
        for stencil_id, config in stencil_data.get("stencils", {}).items():
            try:
                stencils[stencil_id] = LucidStencil(
                    id=stencil_id,
                    name=config["name"],
                    shape_type=config["shape_type"],
                    width=config["dimensions"]["width"],
                    height=config["dimensions"]["height"],
                    fill_color=config["styling"]["fill_color"],
                    border_color=config["styling"]["border_color"],
                    border_width=config["styling"]["border_width"],
                    corner_radius=config["styling"]["corner_radius"],
                    icon=config["display"]["icon"],
                    text_size=config["display"]["text_size"],
                    font=config["display"]["font"],
                    category=config["category"]
                )
            except KeyError as e:
                logger.warning(f"Incomplete stencil definition for {stencil_id}: missing {e}")
        
        logger.info(f"Loaded {len(stencils)} stencils from templates")
        return stencils
    
    def _load_archetype_mappings(self) -> Dict[ArchetypeType, List[str]]:
        """Load archetype to stencil mappings"""
        stencil_data = self.template_loader.load_stencil_library()
        mappings = {}
        
        archetype_stencils = stencil_data.get("archetype_stencils", {})
        for archetype_str, stencil_list in archetype_stencils.items():
            try:
                archetype_type = ArchetypeType(archetype_str)
                mappings[archetype_type] = stencil_list
            except ValueError:
                logger.warning(f"Unknown archetype in template: {archetype_str}")
        
        return mappings
    
    def get_stencil(self, component_type: str) -> Optional[LucidStencil]:
        """Get stencil by component type"""
        return self.stencils.get(component_type)
    
    def get_stencils_for_archetype(self, archetype: ArchetypeType) -> List[str]:
        """Get relevant stencil types for an archetype"""
        return self.archetype_mappings.get(archetype, ["web_server", "database"])
    
    def get_stencils_by_category(self, category: str) -> List[LucidStencil]:
        """Get all stencils in a category"""
        return [stencil for stencil in self.stencils.values() if stencil.category == category]
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return list(set(stencil.category for stencil in self.stencils.values()))

class ArchetypeLayoutEngine:
    """Template-based layout engine for archetype-specific diagrams"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.stencil_library = ArchetypeStencilLibrary(templates_dir)
        self.template_loader = TemplateLoader(templates_dir)
        self.layout_templates = self.template_loader.load_layout_templates()
    
    def generate_layout_for_archetype(self, archetype: ArchetypeType, 
                                    applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate layout for specific archetype using templates"""
        
        # Get layout template for archetype
        layout_template = self.layout_templates.get("layouts", {}).get(archetype.value)
        
        if not layout_template:
            logger.warning(f"No layout template found for {archetype.value}, using fallback")
            return self._generate_fallback_layout(applications, archetype)
        
        # Apply template to actual application data
        return self._apply_template_to_applications(layout_template, applications, archetype)
    
    def _apply_template_to_applications(self, template: Dict[str, Any], 
                                      applications: List[Dict[str, Any]], 
                                      archetype: ArchetypeType) -> Dict[str, Any]:
        """Apply layout template to actual application data"""
        
        components = []
        connections = []
        
        # Get template components
        template_components = template.get("components", [])
        
        # Map applications to template components
        app_index = 0
        
        for template_comp in template_components:
            comp_id = template_comp["id"]
            stencil_type = template_comp["stencil"]
            
            # Handle position patterns (grid, circle, etc.)
            if "position_pattern" in template_comp:
                pattern = template_comp["position_pattern"]
                positions = self._generate_positions_from_pattern(pattern, applications)
                
                # Create multiple components for this pattern
                for i, pos in enumerate(positions):
                    if app_index < len(applications):
                        app = applications[app_index]
                        components.append({
                            "id": app.get("id", f"{comp_id}_{i}"),
                            "type": stencil_type,
                            "name": app.get("name", f"{comp_id} {i+1}"),
                            "position": pos,
                            "stencil": self.stencil_library.get_stencil(stencil_type)
                        })
                        app_index += 1
            else:
                # Single component with fixed position
                position = template_comp["position"]
                
                if app_index < len(applications):
                    app = applications[app_index]
                    name = app.get("name", template_comp.get("name", comp_id.replace("_", " ").title()))
                    app_index += 1
                else:
                    name = template_comp.get("name", comp_id.replace("_", " ").title())
                
                components.append({
                    "id": comp_id,
                    "type": stencil_type,
                    "name": name,
                    "position": position,
                    "stencil": self.stencil_library.get_stencil(stencil_type)
                })
        
        # Generate connections based on template
        connections = self._generate_connections_from_template(template, components)
        
        return {
            "archetype": archetype.value,
            "canvas": template.get("canvas", {"width": 800, "height": 600}),
            "components": components,
            "connections": connections,
            "zones": template.get("zones", [])
        }
    
    def _generate_positions_from_pattern(self, pattern: Dict[str, Any], 
                                       applications: List[Dict[str, Any]]) -> List[Dict[str, int]]:
        """Generate positions based on pattern type"""
        pattern_type = pattern["type"]
        positions = []
        
        if pattern_type == "grid":
            start_x = pattern["start_x"]
            start_y = pattern["start_y"]
            spacing_x = pattern["spacing_x"]
            spacing_y = pattern["spacing_y"]
            rows = pattern.get("rows", 2)
            cols = pattern.get("cols", 3)
            
            count = min(len(applications), rows * cols)
            for i in range(count):
                row = i // cols
                col = i % cols
                positions.append({
                    "x": start_x + (col * spacing_x),
                    "y": start_y + (row * spacing_y)
                })
        
        elif pattern_type == "circle":
            center_x = pattern["center_x"]
            center_y = pattern["center_y"]
            radius = pattern["radius"]
            count = min(len(applications), pattern.get("count", 6))
            
            for i in range(count):
                angle = i * 2 * math.pi / count
                positions.append({
                    "x": center_x + radius * math.cos(angle),
                    "y": center_y + radius * math.sin(angle)
                })
        
        return positions
    
    def _generate_connections_from_template(self, template: Dict[str, Any], 
                                          components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate connections based on template definitions"""
        connections = []
        
        # Create a lookup for components by ID
        comp_lookup = {comp["id"]: comp for comp in components}
        
        # Process template components for connection info
        for template_comp in template.get("components", []):
            comp_id = template_comp["id"]
            
            # Handle connections_to
            if "connections_to" in template_comp:
                for target_id in template_comp["connections_to"]:
                    # If target is a pattern, connect to all matching components
                    if target_id == "service_grid":
                        service_components = [c for c in components if c["type"] in ["microservice"]]
                        for service_comp in service_components:
                            connections.append({
                                "from": comp_id,
                                "to": service_comp["id"],
                                "type": "http"
                            })
                    elif target_id in comp_lookup:
                        connections.append({
                            "from": comp_id,
                            "to": target_id,
                            "type": "http"
                        })
        
        return connections
    
    def _generate_fallback_layout(self, applications: List[Dict[str, Any]], 
                                archetype: ArchetypeType) -> Dict[str, Any]:
        """Generate simple fallback layout when template not available"""
        
        if archetype == ArchetypeType.MONOLITHIC:
            return self._generate_simple_monolithic_layout(applications)
        elif archetype == ArchetypeType.THREE_TIER:
            return self._generate_simple_three_tier_layout(applications)
        else:
            return self._generate_simple_grid_layout(applications, archetype)
    
    def _generate_simple_monolithic_layout(self, applications: List[Dict]) -> Dict[str, Any]:
        """Simple monolithic fallback"""
        components = []
        main_app = applications[0] if applications else {"name": "Monolithic App"}
        
        components.extend([
            {
                "id": "lb_1", "type": "load_balancer", "name": "Load Balancer",
                "position": {"x": 400, "y": 100}, 
                "stencil": self.stencil_library.get_stencil("load_balancer")
            },
            {
                "id": main_app.get("id", "main_app"), "type": "web_server", 
                "name": main_app.get("name", "Monolithic Application"),
                "position": {"x": 400, "y": 250}, 
                "stencil": self.stencil_library.get_stencil("web_server")
            },
            {
                "id": "db_1", "type": "database", "name": "Application Database",
                "position": {"x": 400, "y": 400}, 
                "stencil": self.stencil_library.get_stencil("database")
            }
        ])
        
        connections = [
            {"from": "lb_1", "to": main_app.get("id", "main_app"), "type": "http"},
            {"from": main_app.get("id", "main_app"), "to": "db_1", "type": "sql"}
        ]
        
        return {
            "archetype": "monolithic",
            "canvas": {"width": 800, "height": 600},
            "components": components,
            "connections": connections
        }
    
    def _generate_simple_three_tier_layout(self, applications: List[Dict]) -> Dict[str, Any]:
        """Simple three-tier fallback"""
        components = []
        
        # Simple positioning
        components.extend([
            {
                "id": "web_1", "type": "web_server", "name": "Web Server",
                "position": {"x": 150, "y": 250}, 
                "stencil": self.stencil_library.get_stencil("web_server")
            },
            {
                "id": "app_1", "type": "app_server", "name": "App Server",
                "position": {"x": 400, "y": 250}, 
                "stencil": self.stencil_library.get_stencil("app_server")
            },
            {
                "id": "db_1", "type": "database", "name": "Database",
                "position": {"x": 650, "y": 250}, 
                "stencil": self.stencil_library.get_stencil("database")
            }
        ])
        
        connections = [
            {"from": "web_1", "to": "app_1", "type": "http"},
            {"from": "app_1", "to": "db_1", "type": "sql"}
        ]
        
        return {
            "archetype": "three_tier",
            "canvas": {"width": 900, "height": 600},
            "components": components,
            "connections": connections
        }
    
    def _generate_simple_grid_layout(self, applications: List[Dict], archetype: ArchetypeType) -> Dict[str, Any]:
        """Simple grid fallback for other archetypes"""
        components = []
        
        # Arrange applications in a grid
        cols = 3
        spacing_x, spacing_y = 150, 120
        start_x, start_y = 150, 150
        
        for i, app in enumerate(applications[:9]):  # Limit to 9 apps
            row = i // cols
            col = i % cols
            
            # Choose appropriate stencil
            stencil_type = "microservice" if archetype in [ArchetypeType.MICROSERVICES, ArchetypeType.EVENT_DRIVEN] else "app_server"
            
            components.append({
                "id": app.get("id", f"app_{i}"),
                "type": stencil_type,
                "name": app.get("name", f"Application {i+1}"),
                "position": {
                    "x": start_x + (col * spacing_x),
                    "y": start_y + (row * spacing_y)
                },
                "stencil": self.stencil_library.get_stencil(stencil_type)
            })
        
        return {
            "archetype": archetype.value,
            "canvas": {"width": 800, "height": 600},
            "components": components,
            "connections": []
        }

class LucidChartGenerator:
    """Generate LucidChart XML from archetype layouts using templates"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.layout_engine = ArchetypeLayoutEngine(templates_dir)
        self.template_loader = TemplateLoader(templates_dir)
    
    def generate_lucidchart_xml(self, archetype: ArchetypeType, 
                               applications: List[Dict[str, Any]]) -> str:
        """Generate LucidChart XML for archetype using templates"""
        
        # Generate layout using template
        layout = self.layout_engine.generate_layout_for_archetype(archetype, applications)
        
        # Create XML structure
        lucid_doc = ET.Element("lucidchart")
        lucid_doc.set("version", "2.0")
        lucid_doc.set("archetype", archetype.value)
        lucid_doc.set("template_based", "true")
        
        # Metadata
        metadata = ET.SubElement(lucid_doc, "metadata")
        ET.SubElement(metadata, "title").text = f"{archetype.value.replace('_', ' ').title()} Architecture"
        ET.SubElement(metadata, "archetype").text = archetype.value
        ET.SubElement(metadata, "generated_from_template").text = "true"
        ET.SubElement(metadata, "application_count").text = str(len(applications))
        
        # Canvas
        canvas = ET.SubElement(lucid_doc, "canvas")
        canvas_info = layout["canvas"]
        ET.SubElement(canvas, "width").text = str(canvas_info["width"])
        ET.SubElement(canvas, "height").text = str(canvas_info["height"])
        
        # Zones if present
        if layout.get("zones"):
            zones_elem = ET.SubElement(lucid_doc, "zones")
            for zone in layout["zones"]:
                zone_elem = ET.SubElement(zones_elem, "zone")
                zone_elem.set("name", zone["name"])
                ET.SubElement(zone_elem, "x").text = str(zone["x"])
                ET.SubElement(zone_elem, "y").text = str(zone["y"])
                ET.SubElement(zone_elem, "width").text = str(zone["width"])
                ET.SubElement(zone_elem, "height").text = str(zone["height"])
                ET.SubElement(zone_elem, "color").text = zone["color"]
        
        # Components
        components_elem = ET.SubElement(lucid_doc, "components")
        for component in layout["components"]:
            comp_elem = ET.SubElement(components_elem, "component")
            comp_elem.set("id", component["id"])
            comp_elem.set("type", component["type"])
            comp_elem.set("template_based", "true")
            
            ET.SubElement(comp_elem, "name").text = component["name"]
            
            # Position
            pos_elem = ET.SubElement(comp_elem, "position")
            ET.SubElement(pos_elem, "x").text = str(component["position"]["x"])
            ET.SubElement(pos_elem, "y").text = str(component["position"]["y"])
            
            # Styling from template stencil
            if component.get("stencil"):
                stencil = component["stencil"]
                style_elem = ET.SubElement(comp_elem, "styling")
                ET.SubElement(style_elem, "width").text = str(stencil.width)
                ET.SubElement(style_elem, "height").text = str(stencil.height)
                ET.SubElement(style_elem, "fill_color").text = stencil.fill_color
                ET.SubElement(style_elem, "border_color").text = stencil.border_color
                ET.SubElement(style_elem, "border_width").text = str(stencil.border_width)
                ET.SubElement(style_elem, "corner_radius").text = str(stencil.corner_radius)
                ET.SubElement(style_elem, "shape_type").text = stencil.shape_type
                ET.SubElement(style_elem, "icon").text = stencil.icon
                ET.SubElement(style_elem, "font").text = stencil.font
                ET.SubElement(style_elem, "text_size").text = str(stencil.text_size)
        
        # Connections
        if layout.get("connections"):
            conn_elem = ET.SubElement(lucid_doc, "connections")
            for connection in layout["connections"]:
                conn = ET.SubElement(conn_elem, "connection")
                conn.set("from", connection["from"])
                conn.set("to", connection["to"])
                conn.set("type", connection["type"])
                
                # Connection styling from template
                style_elem = ET.SubElement(conn, "styling")
                ET.SubElement(style_elem, "color").text = "#4ECDC4"
                ET.SubElement(style_elem, "width").text = "2"
                ET.SubElement(style_elem, "style").text = "solid"
                ET.SubElement(style_elem, "arrow").text = "true"
        
        # Format XML
        rough_string = ET.tostring(lucid_doc, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")