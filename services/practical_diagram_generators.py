"""
Enhanced Practical Diagram Generators with Template-Driven Architecture
Integrates YAML templates for professional diagrams like the banking example
"""

import csv
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import base64
import re
import logging
import asyncio

logger = logging.getLogger(__name__)

# Import the new template processor
try:
    from .template_driven_generator import create_template_driven_generator, generate_from_template
    TEMPLATE_PROCESSOR_AVAILABLE = True
    logger.info("Template processor available")
except ImportError as e:
    logger.warning(f"Template processor not available: {e}")
    TEMPLATE_PROCESSOR_AVAILABLE = False

# Import the Playwright-based PDF converter
try:
    from .drawio_converter import pdf_converter, convert_drawio_to_pdf_background
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright PDF converter available")
except ImportError as e:
    logger.warning(f"Playwright PDF converter not available: {e}")
    PLAYWRIGHT_AVAILABLE = False
    pdf_converter = None

class EnhancedDrawIOGenerator:
    """Enhanced Draw.io generator with template support"""
    
    def __init__(self):
        self.template_processor = None
        if TEMPLATE_PROCESSOR_AVAILABLE:
            try:
                self.template_processor = create_template_driven_generator()
                logger.info("Template processor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize template processor: {e}")
                self.template_processor = None
        
        # Fallback shape styles
        self.shape_styles = {
            "web_server": "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;",
            "database": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e1d5e7;strokeColor=#9673a6;",
            "api_gateway": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;",
            "microservice": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;",
            "load_balancer": "ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;",
            "message_queue": "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#ffe6cc;strokeColor=#d79b00;",
            "data_warehouse": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#00b894;strokeColor=#00a085;",
        }
    
    def generate_drawio_file(self, archetype: str, applications: List[Dict[str, Any]], 
                           app_name: str, job_id: str) -> Path:
        """Generate Draw.io XML file with template support"""
        
        # Try template-driven generation first
        if self.template_processor and self._should_use_template(archetype, app_name):
            return self._generate_template_driven_drawio(archetype, applications, app_name, job_id)
        else:
            return self._generate_fallback_drawio(archetype, applications, app_name, job_id)
    
    def _should_use_template(self, archetype: str, app_name: str) -> bool:
        """Determine if we should use template-driven generation"""
        # Use templates for sophisticated architectures or banking-style applications
        template_archetypes = ["microservices", "microservices_banking", "event_driven", "serverless", "cloud_native"]
        banking_keywords = ["bank", "financial", "fintech", "payment", "trading", "nudge"]
        
        return (archetype in template_archetypes or 
                any(keyword in app_name.lower() for keyword in banking_keywords))
    
    def _generate_template_driven_drawio(self, archetype: str, applications: List[Dict[str, Any]], 
                                       app_name: str, job_id: str) -> Path:
        """Generate Draw.io file using template system"""
        try:
            logger.info(f"Generating template-driven Draw.io for {archetype}")
            
            # Check for banking-style architecture
            if "bank" in app_name.lower() or archetype == "microservices_banking":
                result = self.template_processor.generate_banking_style_diagram(applications, app_name, job_id)
                archetype = "microservices_banking"
            else:
                result = self.template_processor.generate_diagram_from_template(archetype, applications, app_name, job_id)
            
            # Save the professional Draw.io XML
            results_dir = Path("results/lucid")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name or "App")
            filename = f"{clean_app_name}_{archetype}_{job_id}.drawio"
            file_path = results_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result["drawio_xml"])
            
            logger.info(f"Generated professional Draw.io file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Template-driven generation failed: {e}")
            return self._generate_fallback_drawio(archetype, applications, app_name, job_id)
    
    def _generate_fallback_drawio(self, archetype: str, applications: List[Dict[str, Any]], 
                                app_name: str, job_id: str) -> Path:
        """Generate Draw.io file using fallback method"""
        logger.info(f"Using fallback Draw.io generation for {archetype}")
        
        # Create layout
        layout = self._generate_layout_for_archetype(archetype, applications)
        
        # Create Draw.io XML
        xml_content = self._create_drawio_xml(layout, archetype)
        
        # Save to lucid directory
        results_dir = Path("results/lucid")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name or "App")
        filename = f"{clean_app_name}_{archetype}_{job_id}.drawio"
        file_path = results_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"Generated fallback Draw.io file: {file_path}")
        return file_path
    
    def _create_drawio_xml(self, layout: Dict[str, Any], archetype: str) -> str:
        """Create Draw.io XML structure (fallback method)"""
        
        # Create root mxfile element
        mxfile = ET.Element("mxfile")
        mxfile.set("host", "app.diagrams.net")
        mxfile.set("modified", datetime.now().isoformat())
        mxfile.set("agent", "Enhanced Archetype Generator")
        mxfile.set("version", "1.5")
        
        # Create diagram
        diagram = ET.SubElement(mxfile, "diagram")
        diagram.set("name", f"{archetype.replace('_', ' ').title()} Architecture")
        diagram.set("id", str(uuid.uuid4()))
        
        # Create mxGraphModel
        graph_model = ET.SubElement(diagram, "mxGraphModel")
        graph_model.set("dx", "1422")
        graph_model.set("dy", "794") 
        graph_model.set("grid", "1")
        graph_model.set("gridSize", "10")
        
        # Root cell
        root = ET.SubElement(graph_model, "root")
        
        # Layer 0 and 1 (required by Draw.io)
        layer0 = ET.SubElement(root, "mxCell")
        layer0.set("id", "0")
        
        layer1 = ET.SubElement(root, "mxCell") 
        layer1.set("id", "1")
        layer1.set("parent", "0")
        
        # Add components
        cell_id = 2
        for component in layout["components"]:
            cell = ET.SubElement(root, "mxCell")
            cell.set("id", str(cell_id))
            cell.set("value", component["name"])
            cell.set("style", self.shape_styles.get(component["type"], self.shape_styles["web_server"]))
            cell.set("vertex", "1")
            cell.set("parent", "1")
            
            # Geometry
            geometry = ET.SubElement(cell, "mxGeometry")
            geometry.set("x", str(component["x"]))
            geometry.set("y", str(component["y"]))
            geometry.set("width", str(component.get("width", 120)))
            geometry.set("height", str(component.get("height", 80)))
            geometry.set("as", "geometry")
            
            component["cell_id"] = cell_id
            cell_id += 1
        
        # Add connections
        for connection in layout["connections"]:
            source_comp = next((c for c in layout["components"] if c["id"] == connection["from"]), None)
            target_comp = next((c for c in layout["components"] if c["id"] == connection["to"]), None)
            
            if source_comp and target_comp:
                cell = ET.SubElement(root, "mxCell")
                cell.set("id", str(cell_id))
                cell.set("value", connection.get("label", ""))
                cell.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;")
                cell.set("edge", "1")
                cell.set("parent", "1")
                cell.set("source", str(source_comp["cell_id"]))
                cell.set("target", str(target_comp["cell_id"]))
                
                # Geometry for edge
                geometry = ET.SubElement(cell, "mxGeometry")
                geometry.set("relative", "1")
                geometry.set("as", "geometry")
                
                cell_id += 1
        
        # Convert to string with proper formatting
        rough_string = ET.tostring(mxfile, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _generate_layout_for_archetype(self, archetype: str, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate layout based on archetype (fallback method)"""
        
        if archetype == "three_tier":
            return self._generate_three_tier_layout(applications)
        elif archetype == "microservices":
            return self._generate_microservices_layout(applications)
        elif archetype == "monolithic":
            return self._generate_monolithic_layout(applications)
        else:
            return self._generate_generic_layout(applications)
    
    def _generate_three_tier_layout(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Three-tier layout (fallback)"""
        components = []
        connections = []
        
        components.append({
            "id": "lb1", "name": "Load Balancer", "type": "load_balancer",
            "x": 50, "y": 200, "width": 120, "height": 60
        })
        
        components.append({
            "id": "web1", "name": "Web Server", "type": "web_server", 
            "x": 250, "y": 200, "width": 120, "height": 80
        })
        
        app_name = applications[0]["name"] if applications else "App Server"
        components.append({
            "id": "app1", "name": app_name[:15], "type": "web_server",
            "x": 450, "y": 200, "width": 120, "height": 80
        })
        
        components.append({
            "id": "db1", "name": "Database", "type": "database",
            "x": 650, "y": 180, "width": 100, "height": 120
        })
        
        connections.extend([
            {"from": "lb1", "to": "web1", "label": "HTTP"},
            {"from": "web1", "to": "app1", "label": "API"},
            {"from": "app1", "to": "db1", "label": "SQL"}
        ])
        
        return {"components": components, "connections": connections}
    
    def _generate_microservices_layout(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced microservices layout"""
        components = []
        connections = []
        
        # API Gateway
        components.append({
            "id": "gateway", "name": "API Gateway", "type": "api_gateway",
            "x": 50, "y": 250, "width": 120, "height": 80
        })
        
        # Services in grid
        start_x, start_y = 250, 150
        spacing_x, spacing_y = 150, 120
        
        for i, app in enumerate(applications[:6]):
            row = i // 3
            col = i % 3
            
            components.append({
                "id": f"svc{i+1}",
                "name": app.get("name", f"Service {i+1}")[:12],
                "type": "microservice",
                "x": start_x + (col * spacing_x),
                "y": start_y + (row * spacing_y),
                "width": 100,
                "height": 60
            })
            
            connections.append({
                "from": "gateway",
                "to": f"svc{i+1}",
                "label": "HTTP"
            })
        
        # Shared database
        components.append({
            "id": "db1", "name": "Shared DB", "type": "database",
            "x": 650, "y": 200, "width": 100, "height": 120
        })
        
        # Message queue for event-driven communication
        components.append({
            "id": "mq1", "name": "Message Queue", "type": "message_queue",
            "x": 450, "y": 400, "width": 120, "height": 60
        })
        
        return {"components": components, "connections": connections}
    
    def _generate_monolithic_layout(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Monolithic layout (fallback)"""
        components = []
        connections = []
        
        app_name = applications[0]["name"] if applications else "Monolithic App"
        
        components.extend([
            {"id": "lb1", "name": "Load Balancer", "type": "load_balancer", "x": 100, "y": 100, "width": 120, "height": 60},
            {"id": "app1", "name": app_name[:15], "type": "web_server", "x": 100, "y": 200, "width": 120, "height": 100},
            {"id": "db1", "name": "Database", "type": "database", "x": 100, "y": 350, "width": 100, "height": 120}
        ])
        
        connections.extend([
            {"from": "lb1", "to": "app1", "label": "HTTP"},
            {"from": "app1", "to": "db1", "label": "SQL"}
        ])
        
        return {"components": components, "connections": connections}
    
    def _generate_generic_layout(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generic grid layout (fallback)"""
        components = []
        connections = []
        
        start_x, start_y = 50, 50
        spacing_x, spacing_y = 150, 120
        
        for i, app in enumerate(applications[:9]):
            row = i // 3
            col = i % 3
            
            components.append({
                "id": f"app{i+1}",
                "name": app.get("name", f"App {i+1}")[:15],
                "type": "web_server",
                "x": start_x + (col * spacing_x),
                "y": start_y + (row * spacing_y),
                "width": 120,
                "height": 80
            })
        
        return {"components": components, "connections": connections}


class LucidChartCSVGenerator:
    """Generate CSV files for LucidChart import (unchanged)"""
    
    def generate_csv_files(self, layout: Dict[str, Any], app_name: str, job_id: str, results_dir: Path) -> List[Path]:
        """Generate CSV files for LucidChart"""
        files = []
        
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name)
        
        # Shapes CSV
        shapes_file = results_dir / f"{clean_app_name}_shapes_{job_id}.csv"
        with open(shapes_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Shape Library", "Shape", "Text Area 1", "Position X", "Position Y", "Width", "Height"])
            
            for comp in layout["components"]:
                writer.writerow([
                    comp["name"],
                    "Standard",
                    "Rectangle" if comp["type"] != "database" else "Cylinder",
                    comp["name"],
                    comp["x"],
                    comp["y"], 
                    comp.get("width", 120),
                    comp.get("height", 80)
                ])
        
        files.append(shapes_file)
        
        # Connections CSV - Start with app name
        if layout.get("connections"):
            conn_file = results_dir / f"{clean_app_name}_connections_{job_id}.csv"
            with open(conn_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Source", "Target", "Label"])
                
                for conn in layout["connections"]:
                    source_name = next((c["name"] for c in layout["components"] if c["id"] == conn["from"]), "")
                    target_name = next((c["name"] for c in layout["components"] if c["id"] == conn["to"]), "")
                    writer.writerow([source_name, target_name, conn.get("label", "")])
            
            files.append(conn_file)
        
        return files


class PDFGenerator:
    """Enhanced PDF generation with template support"""
    
    def generate_pdf_fallback(self, layout: Dict[str, Any], archetype: str, app_name: str, job_id: str, results_dir: Path) -> Path:
        """Generate basic PDF diagram using reportlab (fallback only)"""
        
        logger.info(f"Generating fallback PDF for {app_name}_{archetype}_{job_id}")
        
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.colors import blue, red, green, orange, purple
            
            return self._create_reportlab_pdf(layout, archetype, app_name, job_id, results_dir)
            
        except ImportError as e:
            logger.warning(f"reportlab not available ({e}), using HTML fallback")
            return self._create_html_fallback(layout, archetype, app_name, job_id, results_dir)
    
    def _create_reportlab_pdf(self, layout: Dict[str, Any], archetype: str, app_name: str, job_id: str, results_dir: Path) -> Path:
        """Create PDF using reportlab with improved styling"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import blue, red, green, orange, purple
        
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name)
        filename = f"{clean_app_name}_{archetype}_{job_id}_fallback.pdf"
        file_path = results_dir / filename
        
        c = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4
        
        # Enhanced title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, f"{archetype.replace('_', ' ').title()} Architecture")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Application: {app_name}")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 90, f"Note: Install Playwright for professional-quality diagrams like the banking example")
        
        # Draw components with better styling
        colors = [blue, green, orange, purple, red]
        
        for i, comp in enumerate(layout["components"]):
            x = comp["x"] / 2 + 50
            y = height - comp["y"] / 2 - 150
            w = comp.get("width", 120) / 2
            h = comp.get("height", 80) / 2
            
            color = colors[i % len(colors)]
            c.setStrokeColor(color)
            c.setFillColor(color)
            c.setFillAlpha(0.3)
            
            if comp["type"] == "database" or comp["type"] == "data_warehouse":
                # Enhanced cylinder representation
                c.ellipse(x, y + h - 5, x + w, y + h, fill=1)
                c.rect(x, y, w, h - 5, fill=1)
                c.ellipse(x, y, x + w, y + 5, fill=1)
            else:
                c.rect(x, y, w, h, fill=1)
            
            # Enhanced text rendering
            c.setFillAlpha(1)
            c.setFillColor("black")
            c.setFont("Helvetica-Bold", 9)
            text_x = x + w/2
            text_y = y + h/2
            
            # Multi-line text support
            lines = comp["name"].split('\n')
            for line_i, line in enumerate(lines):
                text_width = c.stringWidth(line, c._fontname, c._fontsize)
                line_y = text_y + (len(lines) - 1) * 5 - line_i * 10
                c.drawString(text_x - text_width/2, line_y, line)
        
        # Enhanced connections
        c.setStrokeColor("black")
        for conn in layout["connections"]:
            source = next((c for c in layout["components"] if c["id"] == conn["from"]), None)
            target = next((c for c in layout["components"] if c["id"] == conn["to"]), None)
            
            if source and target:
                x1 = source["x"] / 2 + source.get("width", 120) / 4 + 50
                y1 = height - source["y"] / 2 - source.get("height", 80) / 4 - 150
                x2 = target["x"] / 2 + target.get("width", 120) / 4 + 50
                y2 = height - target["y"] / 2 - target.get("height", 80) / 4 - 150
                
                c.line(x1, y1, x2, y2)
                
                # Enhanced connection labels
                if conn.get("label"):
                    c.setFont("Helvetica", 8)
                    label_x = (x1 + x2) / 2
                    label_y = (y1 + y2) / 2 + 5
                    label_width = c.stringWidth(conn["label"], c._fontname, c._fontsize)
                    c.drawString(label_x - label_width/2, label_y, conn["label"])
        
        c.save()
        logger.info(f"Created enhanced fallback PDF: {file_path}")
        return file_path
    
    def _create_html_fallback(self, layout: Dict[str, Any], archetype: str, app_name: str, job_id: str, results_dir: Path) -> Path:
        """Create enhanced HTML file as fallback"""
        
        clean_app_name = re.sub(r'[<>:"/\\|?*]', '-', app_name)
        filename = f"{clean_app_name}_{archetype}_{job_id}_fallback.html"
        file_path = results_dir / filename
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{archetype.replace('_', ' ').title()} Architecture - {app_name}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            background: #f5f7fa;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        .notice {{
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        .component {{ 
            border: 2px solid #3498db; 
            border-radius: 8px; 
            padding: 15px; 
            margin: 15px; 
            background: white;
            display: inline-block;
            min-width: 140px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .component:hover {{ transform: translateY(-2px); }}
        .database {{ border-color: #9C27B0; background: linear-gradient(145deg, #f3e5f5, white); }}
        .data_warehouse {{ border-color: #00b894; background: linear-gradient(145deg, #e8f8f5, white); }}
        .api_gateway {{ border-color: #FF9800; background: linear-gradient(145deg, #fff3e0, white); }}
        .microservice {{ border-color: #4CAF50; background: linear-gradient(145deg, #e8f5e9, white); }}
        .message_queue {{ border-color: #f39c12; background: linear-gradient(145deg, #fef9e7, white); }}
        .layout {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            align-items: center;
            justify-content: center;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .connections {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .connection {{ 
            margin: 8px 0; 
            color: #34495e;
            font-weight: 500;
        }}
        @media print {{
            body {{ margin: 20px; background: white; }}
            .component {{ break-inside: avoid; box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{archetype.replace('_', ' ').title()} Architecture</h1>
        <p><strong>Application:</strong> {app_name}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="notice">
        <strong>📝 Note:</strong> This is a basic HTML representation. For professional diagrams like the banking PDF example, 
        install <code>pip install playwright</code> and run <code>playwright install chromium</code> to enable high-quality PDF generation.
    </div>
    
    <h2>Architecture Components</h2>
    <div class="layout">
"""
        
        # Add enhanced components
        for comp in layout["components"]:
            comp_class = comp["type"] if comp["type"] in ["database", "data_warehouse", "api_gateway", "microservice", "message_queue"] else "component"
            component_name = comp["name"].replace('\n', '<br>')
            html_content += f"""
        <div class="component {comp_class}">
            <strong>{component_name}</strong><br>
            <small style="color: #7f8c8d;">{comp["type"].replace('_', ' ').title()}</small>
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="connections">
        <h2>Data Flows & Connections</h2>
        <ul>
"""
        
        # Add enhanced connections
        for conn in layout["connections"]:
            source_name = next((c["name"] for c in layout["components"] if c["id"] == conn["from"]), conn["from"])
            target_name = next((c["name"] for c in layout["components"] if c["id"] == conn["to"]), conn["to"])
            label = conn.get("label", "connection")
            
            html_content += f"""
        <li class="connection">{source_name} <span style="color: #3498db;">→</span> {target_name} <em>({label})</em></li>
"""
        
        html_content += """
        </ul>
    </div>
    
    <div style="margin-top: 40px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px;">
        <h3 style="color: white; border: none;">🚀 Upgrade to Professional Quality</h3>
        <p>To generate diagrams like the banking PDF example:</p>
        <ol>
            <li><code>pip install playwright</code></li>
            <li><code>playwright install chromium</code></li>
            <li>Place your YAML templates in the <code>templates/</code> folder</li>
            <li>Re-run the diagram generation</li>
        </ol>
    </div>
</body>
</html>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Created enhanced HTML fallback: {file_path}")
        return file_path


async def generate_high_quality_pdf(drawio_file_path: Path, output_dir: Path, job_id: str = None) -> Optional[Path]:
    """Generate high-quality PDF from Draw.io file using Playwright"""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available for high-quality PDF generation")
        return None
    
    try:
        output_pdf_path = output_dir / f"{drawio_file_path.stem}.pdf"
        result_path = await pdf_converter.convert_to_pdf_direct(str(drawio_file_path), str(output_pdf_path))
        
        if result_path and Path(result_path).exists():
            logger.info(f"High-quality PDF created: {result_path}")
            return Path(result_path)
        else:
            logger.error("Playwright PDF conversion failed")
            return None
            
    except Exception as e:
        logger.error(f"Error in high-quality PDF generation: {e}")
        return None


def generate_all_formats(archetype: str, applications: List[Dict[str, Any]], 
                        app_name: str, job_id: str = None) -> Dict[str, Any]:
    """Enhanced generate_all_formats with template support and professional PDF"""
    
    try:
        if not job_id:
            job_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Generating enhanced formats for {app_name} ({archetype}) - Job: {job_id}")
        
        # Clean app name
        clean_app_name = re.sub(r'[<>:"/\\|?*\s]', '_', app_name or "Application")
        
        # Create directories
        base_results_dir = Path("results")
        lucid_dir = base_results_dir / "lucid"
        pdf_dir = base_results_dir / "pdf"
        
        lucid_dir.mkdir(parents=True, exist_ok=True)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        drawio_file = None
        
        # Generate Draw.io file using enhanced generator
        try:
            drawio_gen = EnhancedDrawIOGenerator()
            drawio_file = drawio_gen.generate_drawio_file(archetype, applications, clean_app_name, job_id)
            generated_files.append({
                "format": "drawio",
                "path": str(drawio_file),
                "filename": drawio_file.name,
                "file_size": drawio_file.stat().st_size,
                "directory": "results/lucid/",
                "description": "Professional Draw.io file (import directly)",
                "quality": "professional" if TEMPLATE_PROCESSOR_AVAILABLE else "standard"
            })
        except Exception as e:
            logger.error(f"Draw.io generation failed: {e}")
        
        # Generate LucidChart CSV files
        try:
            # Use basic layout for CSV generation
            layout = drawio_gen._generate_layout_for_archetype(archetype, applications)
            csv_gen = LucidChartCSVGenerator()
            csv_files = csv_gen.generate_csv_files(layout, clean_app_name, job_id, lucid_dir)
            
            for csv_file in csv_files:
                generated_files.append({
                    "format": "csv",
                    "path": str(csv_file),
                    "filename": csv_file.name,
                    "file_size": csv_file.stat().st_size,
                    "directory": "results/lucid/",
                    "description": "Import into LucidChart via CSV"
                })
        except Exception as e:
            logger.error(f"CSV generation failed: {e}")
        
        # Generate High-Quality PDF using Playwright (if available)
        high_quality_pdf = None
        if drawio_file and PLAYWRIGHT_AVAILABLE:
            try:
                # Run the async PDF generation
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    logger.info("Scheduling high-quality PDF generation...")
                else:
                    high_quality_pdf = loop.run_until_complete(
                        generate_high_quality_pdf(drawio_file, pdf_dir, job_id)
                    )
                    
                if high_quality_pdf:
                    generated_files.append({
                        "format": "pdf",
                        "path": str(high_quality_pdf),
                        "filename": high_quality_pdf.name,
                        "file_size": high_quality_pdf.stat().st_size,
                        "directory": "results/pdf/",
                        "description": "Professional PDF (like banking example)",
                        "quality": "professional"
                    })
                    logger.info(f"Professional PDF generated: {high_quality_pdf}")
                
            except Exception as e:
                logger.error(f"High-quality PDF generation failed: {e}")
        
        # Generate Enhanced Fallback PDF (if high-quality failed)
        if not high_quality_pdf:
            try:
                pdf_gen = PDFGenerator()
                layout = drawio_gen._generate_layout_for_archetype(archetype, applications)
                fallback_pdf = pdf_gen.generate_pdf_fallback(layout, archetype, clean_app_name, job_id, pdf_dir)
                
                generated_files.append({
                    "format": "pdf",
                    "path": str(fallback_pdf),
                    "filename": fallback_pdf.name,
                    "file_size": fallback_pdf.stat().st_size,
                    "directory": "results/pdf/",
                    "description": "Enhanced fallback PDF (install Playwright for professional quality)",
                    "quality": "enhanced_fallback"
                })
            except Exception as e:
                logger.error(f"Fallback PDF generation failed: {e}")
        
        result = {
            "success": True,
            "job_id": job_id,
            "app_name": clean_app_name,
            "archetype": archetype,
            "files": generated_files,
            "total_files": len(generated_files),
            "formats_generated": [f["format"] for f in generated_files],
            "directories": {
                "draw_io_csv": str(lucid_dir),
                "pdf": str(pdf_dir)
            },
            "generated_at": datetime.now().isoformat(),
            "drawio_file_path": str(drawio_file) if drawio_file else None,
            "enhancements": {
                "template_processor": TEMPLATE_PROCESSOR_AVAILABLE,
                "playwright_pdf": PLAYWRIGHT_AVAILABLE,
                "professional_quality": TEMPLATE_PROCESSOR_AVAILABLE and PLAYWRIGHT_AVAILABLE
            }
        }
        
        logger.info(f"Successfully generated {len(generated_files)} enhanced files")
        return result
        
    except Exception as e:
        logger.error(f"Enhanced generate_all_formats failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "job_id": job_id or "unknown",
            "app_name": app_name,
            "archetype": archetype,
            "generated_at": datetime.now().isoformat()
        }


# Test function for the enhanced system
def test_banking_style_generation():
    """Test the enhanced banking-style diagram generation"""
    test_apps = [
        {"id": "api", "name": "Banking API", "type": "api_gateway"},
        {"id": "nudges", "name": "Nudges Service", "type": "microservice"},
        {"id": "content", "name": "Content Service", "type": "microservice"},
        {"id": "compute", "name": "Nudge Compute", "type": "microservice"},
        {"id": "expiry", "name": "Nudge Expiry", "type": "microservice"}
    ]
    
    # Test with banking-style name to trigger template processing
    result = generate_all_formats("microservices", test_apps, "MBank_Nudges", "test_banking")
    
    print("=== Enhanced Banking-Style Test Results ===")
    print(f"Success: {result['success']}")
    print(f"Files generated: {result['total_files']}")
    print(f"Professional quality: {result['enhancements']['professional_quality']}")
    
    for file_info in result["files"]:
        print(f"  - {file_info['format']}: {file_info['filename']} ({file_info['quality']})")
    
    return result


if __name__ == "__main__":
    # Test the enhanced system
    test_result = test_banking_style_generation()
    print("Enhanced banking diagram test completed")