"""
Template-Driven Architecture Diagram Generator
Uses YAML templates to create professional architecture diagrams like the banking example
"""

import yaml
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import uuid
from datetime import datetime
import re
import logging
import math

logger = logging.getLogger(__name__)

class TemplateProcessor:
    """Process YAML templates and generate architecture diagrams"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.layout_templates = {}
        self.stencil_library = {}
        self.archetype_templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load all YAML template files"""
        try:
            # Load layout templates
            layout_file = self.templates_dir / "layout_templates.yaml"
            if layout_file.exists():
                with open(layout_file, 'r', encoding='utf-8') as f:
                    self.layout_templates = yaml.safe_load(f)
                logger.info("Loaded layout templates")
            
            # Load stencil library
            stencil_file = self.templates_dir / "stencil_library.yaml"
            if stencil_file.exists():
                with open(stencil_file, 'r', encoding='utf-8') as f:
                    self.stencil_library = yaml.safe_load(f)
                logger.info("Loaded stencil library")
            
            # Load archetype templates
            archetype_file = self.templates_dir / "archetype_templates.yaml"
            if archetype_file.exists():
                with open(archetype_file, 'r', encoding='utf-8') as f:
                    self.archetype_templates = yaml.safe_load(f)
                logger.info("Loaded archetype templates")
                
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            # Create fallback templates
            self._create_fallback_templates()
    
    def _create_fallback_templates(self):
        """Create basic fallback templates if YAML files don't exist"""
        self.layout_templates = {
            "layouts": {
                "three_tier": {
                    "name": "Three-Tier Architecture",
                    "canvas": {"width": 900, "height": 600},
                    "pattern": "horizontal_tiers",
                    "components": [
                        {
                            "id": "load_balancer",
                            "stencil": "load_balancer", 
                            "position": {"x": 150, "y": 150}
                        },
                        {
                            "id": "web_servers",
                            "stencil": "web_server",
                            "position": {"x": 150, "y": 250}
                        },
                        {
                            "id": "app_servers", 
                            "stencil": "app_server",
                            "position": {"x": 400, "y": 250}
                        },
                        {
                            "id": "databases",
                            "stencil": "database",
                            "position": {"x": 650, "y": 250}
                        }
                    ]
                }
            }
        }
        
        self.stencil_library = {
            "stencils": {
                "web_server": {
                    "name": "Web Server",
                    "shape_type": "rectangle",
                    "dimensions": {"width": 120, "height": 80},
                    "styling": {
                        "fill_color": "#4ECDC4",
                        "border_color": "#45B7D1",
                        "border_width": 2,
                        "corner_radius": 8
                    }
                },
                "database": {
                    "name": "Database",
                    "shape_type": "cylinder",
                    "dimensions": {"width": 100, "height": 120},
                    "styling": {
                        "fill_color": "#6C5CE7",
                        "border_color": "#5F3DC4",
                        "border_width": 2,
                        "corner_radius": 8
                    }
                }
            }
        }

    def generate_diagram_from_template(self, archetype: str, applications: List[Dict[str, Any]], 
                                     app_name: str, job_id: str) -> Dict[str, Any]:
        """Generate diagram using template-driven approach"""
        
        logger.info(f"Generating template-driven diagram for {archetype}")
        
        # Get the layout template
        layout = self._get_layout_template(archetype)
        if not layout:
            logger.warning(f"No template found for {archetype}, using fallback")
            layout = self._create_fallback_layout(archetype, applications)
        
        # Apply application-specific data
        processed_layout = self._apply_application_data(layout, applications, app_name)
        
        # Generate components with professional styling
        components = self._generate_styled_components(processed_layout, archetype)
        
        # Create Draw.io XML
        drawio_xml = self._create_professional_drawio_xml(components, processed_layout, archetype, app_name)
        
        return {
            "layout": processed_layout,
            "components": components,
            "drawio_xml": drawio_xml,
            "archetype": archetype,
            "app_name": app_name
        }

    def _get_layout_template(self, archetype: str) -> Optional[Dict]:
        """Get layout template for the specified archetype"""
        layouts = self.layout_templates.get("layouts", {})
        return layouts.get(archetype)

    def _apply_application_data(self, layout: Dict, applications: List[Dict], app_name: str) -> Dict:
        """Apply real application data to the template"""
        processed = layout.copy()
        
        # Map applications to components
        app_mapping = self._map_applications_to_components(applications, layout)
        
        # Update component names and properties
        for component in processed.get("components", []):
            comp_id = component["id"]
            if comp_id in app_mapping:
                mapped_app = app_mapping[comp_id]
                component["name"] = mapped_app.get("name", component["id"].replace("_", " ").title())
                component["app_data"] = mapped_app
            else:
                component["name"] = component["id"].replace("_", " ").title()
        
        return processed

    def _map_applications_to_components(self, applications: List[Dict], layout: Dict) -> Dict:
        """Map application data to layout components intelligently"""
        mapping = {}
        
        if not applications:
            return mapping
        
        components = layout.get("components", [])
        
        # Simple mapping logic - can be enhanced
        for i, app in enumerate(applications[:len(components)]):
            if i < len(components):
                comp_id = components[i]["id"]
                mapping[comp_id] = app
        
        return mapping

    def _generate_styled_components(self, layout: Dict, archetype: str) -> List[Dict]:
        """Generate components with professional styling from stencil library"""
        styled_components = []
        
        for component in layout.get("components", []):
            styled_comp = self._apply_stencil_styling(component, archetype)
            styled_components.append(styled_comp)
        
        return styled_components

    def _apply_stencil_styling(self, component: Dict, archetype: str) -> Dict:
        """Apply stencil library styling to a component"""
        stencil_name = component.get("stencil", "web_server")
        stencils = self.stencil_library.get("stencils", {})
        stencil = stencils.get(stencil_name, stencils.get("web_server", {}))
        
        styled_component = {
            "id": component["id"],
            "name": component.get("name", component["id"].replace("_", " ").title()),
            "type": stencil_name,
            "position": component.get("position", {"x": 100, "y": 100}),
            "dimensions": stencil.get("dimensions", {"width": 120, "height": 80}),
            "styling": stencil.get("styling", {
                "fill_color": "#4ECDC4",
                "border_color": "#45B7D1",
                "border_width": 2,
                "corner_radius": 8
            }),
            "shape_type": stencil.get("shape_type", "rectangle"),
            "category": stencil.get("category", "application_services")
        }
        
        return styled_component

    def _create_professional_drawio_xml(self, components: List[Dict], layout: Dict, 
                                      archetype: str, app_name: str) -> str:
        """Create professional Draw.io XML with advanced styling"""
        
        # Create root mxfile element
        mxfile = ET.Element("mxfile")
        mxfile.set("host", "app.diagrams.net")
        mxfile.set("modified", datetime.now().isoformat())
        mxfile.set("agent", "Professional Archetype Generator")
        mxfile.set("version", "2.0")
        
        # Create diagram
        diagram = ET.SubElement(mxfile, "diagram")
        diagram.set("name", f"{app_name} - {archetype.replace('_', ' ').title()}")
        diagram.set("id", str(uuid.uuid4()))
        
        # Create mxGraphModel with professional settings
        graph_model = ET.SubElement(diagram, "mxGraphModel")
        graph_model.set("dx", str(layout.get("canvas", {}).get("width", 1200)))
        graph_model.set("dy", str(layout.get("canvas", {}).get("height", 800)))
        graph_model.set("grid", "1")
        graph_model.set("gridSize", "10")
        graph_model.set("guides", "1")
        graph_model.set("tooltips", "1")
        graph_model.set("connect", "1")
        
        # Root cell
        root = ET.SubElement(graph_model, "root")
        
        # Layer 0 and 1 (required by Draw.io)
        layer0 = ET.SubElement(root, "mxCell")
        layer0.set("id", "0")
        
        layer1 = ET.SubElement(root, "mxCell")
        layer1.set("id", "1")
        layer1.set("parent", "0")
        
        # Add zones/backgrounds if specified
        cell_id = 2
        if "zones" in layout:
            cell_id = self._add_zones(root, layout["zones"], cell_id)
        
        # Add professional components
        component_map = {}
        for component in components:
            cell_id = self._add_professional_component(root, component, cell_id)
            component_map[component["id"]] = cell_id - 1
        
        # Add connections
        connections = self._generate_connections(components, layout)
        for connection in connections:
            cell_id = self._add_professional_connection(root, connection, component_map, cell_id)
        
        # Convert to formatted XML string
        rough_string = ET.tostring(mxfile, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _add_zones(self, root: ET.Element, zones: List[Dict], cell_id: int) -> int:
        """Add background zones/tiers to the diagram"""
        for zone in zones:
            cell = ET.SubElement(root, "mxCell")
            cell.set("id", str(cell_id))
            cell.set("value", zone.get("name", "Zone"))
            
            # Professional zone styling
            style = (
                f"rounded=1;whiteSpace=wrap;html=1;"
                f"fillColor={zone.get('color', '#F5F5F5')};"
                f"strokeColor=#C0C0C0;strokeWidth=1;"
                f"fontSize=14;fontStyle=1;fontColor=#666666;"
                f"align=left;verticalAlign=top;spacingLeft=10;spacingTop=5;"
            )
            
            cell.set("style", style)
            cell.set("vertex", "1")
            cell.set("parent", "1")
            
            # Geometry for zone
            geometry = ET.SubElement(cell, "mxGeometry")
            geometry.set("x", str(zone.get("x", 50)))
            geometry.set("y", str(zone.get("y", 50)))
            geometry.set("width", str(zone.get("width", 200)))
            geometry.set("height", str(zone.get("height", 400)))
            geometry.set("as", "geometry")
            
            cell_id += 1
        
        return cell_id

    def _add_professional_component(self, root: ET.Element, component: Dict, cell_id: int) -> int:
        """Add a professionally styled component to the diagram"""
        cell = ET.SubElement(root, "mxCell")
        cell.set("id", str(cell_id))
        cell.set("value", component["name"])
        
        # Build professional style string
        style = self._build_component_style(component)
        cell.set("style", style)
        cell.set("vertex", "1")
        cell.set("parent", "1")
        
        # Geometry
        geometry = ET.SubElement(cell, "mxGeometry")
        pos = component["position"]
        dims = component["dimensions"]
        
        geometry.set("x", str(pos["x"]))
        geometry.set("y", str(pos["y"]))
        geometry.set("width", str(dims["width"]))
        geometry.set("height", str(dims["height"]))
        geometry.set("as", "geometry")
        
        return cell_id + 1

    def _build_component_style(self, component: Dict) -> str:
        """Build professional Draw.io style string for component"""
        styling = component.get("styling", {})
        shape_type = component.get("shape_type", "rectangle")
        
        # Base style components
        style_parts = []
        
        # Shape-specific styling
        if shape_type == "cylinder":
            style_parts.append("shape=cylinder3")
            style_parts.append("whiteSpace=wrap")
            style_parts.append("html=1")
            style_parts.append("boundedLbl=1")
            style_parts.append("backgroundOutline=1")
            style_parts.append("size=15")
        elif shape_type == "hexagon":
            style_parts.append("shape=hexagon")
            style_parts.append("perimeter=hexagonPerimeter2")
            style_parts.append("whiteSpace=wrap")
            style_parts.append("html=1")
            style_parts.append("fixedSize=1")
        elif shape_type == "diamond":
            style_parts.append("rhombus")
            style_parts.append("whiteSpace=wrap")
            style_parts.append("html=1")
        elif shape_type == "cloud":
            style_parts.append("ellipse")
            style_parts.append("shape=cloud")
            style_parts.append("whiteSpace=wrap")
            style_parts.append("html=1")
        else:  # rectangle or rounded_rectangle
            if component.get("category") in ["microservice", "lambda_function"]:
                style_parts.append("rounded=1")
            style_parts.append("whiteSpace=wrap")
            style_parts.append("html=1")
        
        # Colors and styling
        fill_color = styling.get("fill_color", "#4ECDC4")
        border_color = styling.get("border_color", "#45B7D1")
        border_width = styling.get("border_width", 2)
        corner_radius = styling.get("corner_radius", 8)
        
        style_parts.append(f"fillColor={fill_color}")
        style_parts.append(f"strokeColor={border_color}")
        style_parts.append(f"strokeWidth={border_width}")
        
        if shape_type in ["rectangle", "rounded_rectangle"]:
            style_parts.append(f"rounded=1")
            style_parts.append(f"arcSize={corner_radius}")
        
        # Professional typography
        style_parts.extend([
            "fontSize=11",
            "fontFamily=Helvetica",
            "fontColor=#2c3e50",
            "align=center",
            "verticalAlign=middle",
            "spacing=2"
        ])
        
        # Add shadow for depth
        style_parts.append("shadow=1")
        style_parts.append("glass=0")
        
        return ";".join(style_parts) + ";"

    def _generate_connections(self, components: List[Dict], layout: Dict) -> List[Dict]:
        """Generate connections between components based on layout and patterns"""
        connections = []
        
        # Use explicit connections from layout if available
        if "connections" in layout:
            return layout["connections"]
        
        # Auto-generate connections based on archetype patterns
        if len(components) >= 2:
            # Simple linear flow for basic architectures
            for i in range(len(components) - 1):
                connections.append({
                    "from": components[i]["id"],
                    "to": components[i + 1]["id"],
                    "label": self._get_connection_label(components[i], components[i + 1]),
                    "style": "http"
                })
        
        return connections

    def _get_connection_label(self, from_comp: Dict, to_comp: Dict) -> str:
        """Determine appropriate connection label based on component types"""
        from_type = from_comp.get("type", "")
        to_type = to_comp.get("type", "")
        
        if to_type == "database":
            return "SQL"
        elif from_type == "load_balancer":
            return "HTTP"
        elif "api" in from_type.lower() or "api" in to_type.lower():
            return "REST API"
        elif "message" in from_type.lower() or "message" in to_type.lower():
            return "Message"
        else:
            return "HTTP"

    def _add_professional_connection(self, root: ET.Element, connection: Dict, 
                                   component_map: Dict, cell_id: int) -> int:
        """Add professional connection/edge to diagram"""
        cell = ET.SubElement(root, "mxCell")
        cell.set("id", str(cell_id))
        cell.set("value", connection.get("label", ""))
        
        # Professional connection styling
        conn_style = connection.get("style", "http")
        style = self._get_connection_style(conn_style)
        
        cell.set("style", style)
        cell.set("edge", "1")
        cell.set("parent", "1")
        
        # Set source and target
        from_id = component_map.get(connection["from"])
        to_id = component_map.get(connection["to"])
        
        if from_id and to_id:
            cell.set("source", str(from_id))
            cell.set("target", str(to_id))
        
        # Geometry for edge
        geometry = ET.SubElement(cell, "mxGeometry")
        geometry.set("relative", "1")
        geometry.set("as", "geometry")
        
        return cell_id + 1

    def _get_connection_style(self, style_name: str) -> str:
        """Get professional connection styling"""
        styles = {
            "http": (
                "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#4ECDC4;strokeWidth=2;endArrow=classic;"
                "fontSize=10;fontColor=#2c3e50;"
            ),
            "sql": (
                "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#6C5CE7;strokeWidth=2;endArrow=classic;"
                "fontSize=10;fontColor=#2c3e50;"
            ),
            "message": (
                "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;"
                "html=1;strokeColor=#E17055;strokeWidth=2;endArrow=classic;dashed=1;"
                "fontSize=10;fontColor=#2c3e50;"
            )
        }
        
        return styles.get(style_name, styles["http"])

    def _create_fallback_layout(self, archetype: str, applications: List[Dict]) -> Dict:
        """Create basic fallback layout when template doesn't exist"""
        return {
            "name": f"{archetype.replace('_', ' ').title()} Architecture",
            "canvas": {"width": 800, "height": 600},
            "components": [
                {
                    "id": f"comp_{i}",
                    "stencil": "web_server",
                    "position": {"x": 100 + i * 150, "y": 200},
                    "name": app.get("name", f"Component {i+1}")
                }
                for i, app in enumerate(applications[:5])
            ]
        }

    def generate_banking_style_diagram(self, applications: List[Dict], app_name: str, 
                                     job_id: str) -> Dict[str, Any]:
        """Generate a banking-style microservices diagram like the PDF example"""
        
        # Create a sophisticated banking microservices layout
        banking_layout = {
            "name": "Banking Microservices Architecture", 
            "canvas": {"width": 1000, "height": 700},
            "pattern": "microservices_banking",
            "zones": [
                {
                    "name": "API Layer",
                    "x": 50, "y": 50, "width": 200, "height": 600,
                    "color": "#E8F4FD"
                },
                {
                    "name": "Services Layer", 
                    "x": 300, "y": 50, "width": 400, "height": 600,
                    "color": "#FFF8E1"
                },
                {
                    "name": "Data Layer",
                    "x": 750, "y": 50, "width": 200, "height": 600, 
                    "color": "#F3E5F5"
                }
            ],
            "components": [
                {
                    "id": "api_gateway",
                    "stencil": "api_gateway",
                    "position": {"x": 150, "y": 350},
                    "name": f"{app_name} API"
                },
                {
                    "id": "nudges_service", 
                    "stencil": "microservice",
                    "position": {"x": 350, "y": 200},
                    "name": "Nudges Service"
                },
                {
                    "id": "content_service",
                    "stencil": "microservice", 
                    "position": {"x": 500, "y": 200},
                    "name": "Content Service"
                },
                {
                    "id": "compute_service",
                    "stencil": "microservice",
                    "position": {"x": 350, "y": 350},
                    "name": "Nudge Compute"
                },
                {
                    "id": "expiry_service",
                    "stencil": "microservice",
                    "position": {"x": 500, "y": 500},
                    "name": "Nudge Expiry"
                },
                {
                    "id": "dynamodb",
                    "stencil": "database",
                    "position": {"x": 800, "y": 150},
                    "name": "Nudges\n(DynamoDB)"
                },
                {
                    "id": "snowflake_activity",
                    "stencil": "data_warehouse",
                    "position": {"x": 800, "y": 300},
                    "name": "Customer Activity\n(Snowflake)"
                },
                {
                    "id": "snowflake_nudges",
                    "stencil": "data_warehouse", 
                    "position": {"x": 800, "y": 450},
                    "name": "Nudges\n(Snowflake)"
                },
                {
                    "id": "kafka",
                    "stencil": "message_queue",
                    "position": {"x": 350, "y": 500},
                    "name": "Kafka Topic"
                }
            ],
            "connections": [
                {"from": "api_gateway", "to": "nudges_service", "label": "REST API", "style": "http"},
                {"from": "nudges_service", "to": "dynamodb", "label": "customer nudges", "style": "sql"},
                {"from": "nudges_service", "to": "content_service", "label": "templates", "style": "http"},
                {"from": "compute_service", "to": "snowflake_activity", "label": "activity events", "style": "sql"},
                {"from": "compute_service", "to": "snowflake_nudges", "label": "creates nudge instances", "style": "sql"},
                {"from": "expiry_service", "to": "snowflake_activity", "label": "consumes activity", "style": "sql"},
                {"from": "kafka", "to": "expiry_service", "label": "user activity", "style": "message"}
            ]
        }
        
        # Generate using the template processor
        result = self.generate_diagram_from_template("microservices_banking", applications, app_name, job_id)
        result["layout"] = banking_layout
        
        # Override with banking-specific layout
        components = self._generate_styled_components(banking_layout, "microservices_banking")
        result["components"] = components
        result["drawio_xml"] = self._create_professional_drawio_xml(components, banking_layout, "microservices_banking", app_name)
        
        return result


def create_template_driven_generator() -> TemplateProcessor:
    """Factory function to create template processor"""
    return TemplateProcessor()


# Integration with existing practical_diagram_generators.py
def generate_from_template(archetype: str, applications: List[Dict[str, Any]], 
                          app_name: str, job_id: str) -> Dict[str, Any]:
    """Generate diagram using template-driven approach"""
    
    processor = create_template_driven_generator()
    
    # Special handling for banking-style diagrams
    if archetype == "microservices_banking" or "bank" in app_name.lower():
        result = processor.generate_banking_style_diagram(applications, app_name, job_id)
    else:
        result = processor.generate_diagram_from_template(archetype, applications, app_name, job_id)
    
    return result


# Test function
def test_banking_diagram():
    """Test banking-style diagram generation"""
    test_apps = [
        {"id": "api", "name": "Banking API", "type": "api_gateway"},
        {"id": "nudges", "name": "Nudges Service", "type": "microservice"},
        {"id": "content", "name": "Content Service", "type": "microservice"},
        {"id": "compute", "name": "Nudge Compute", "type": "microservice"}
    ]
    
    processor = create_template_driven_generator()
    result = processor.generate_banking_style_diagram(test_apps, "MBank", "test_123")
    
    # Save the Draw.io XML
    output_file = Path("results/lucid/MBank_banking_test.drawio")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result["drawio_xml"])
    
    print(f"Banking diagram generated: {output_file}")
    return result


if __name__ == "__main__":
    # Test the banking diagram generation
    test_result = test_banking_diagram()
    print("Banking diagram test completed")