#!/usr/bin/env python3
"""
Interactive Enterprise Architecture Mapper
Generates web-based, interactive SVG diagrams with hover capabilities
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict, Counter
import networkx as nx

class InteractiveArchitectureMapper:
    def __init__(self, analysis_dir="complete_composite_analysis"):
        self.analysis_dir = Path(analysis_dir)
        self.applications = {}
        self.nodes = []
        self.edges = []
        self.infrastructure_layers = {}
        
    def load_all_applications(self):
        """Load all application data and create unified model"""
        
        for csv_file in self.analysis_dir.glob("*_normalized_data.csv"):
            app_name = csv_file.stem.replace("_normalized_data", "")
            df = pd.read_csv(csv_file)
            self.applications[app_name] = df
            self._process_application_data(app_name, df)
    
    def _process_application_data(self, app_name, df):
        """Extract nodes and edges with rich metadata"""
        
        # Process each connection
        for idx, row in df.iterrows():
            # Source node
            source_node = self._create_node_info(
                ip=row.get('source_ip', ''),
                hostname=row.get('source_hostname', ''),
                app_name=app_name,
                role='source'
            )
            
            # Destination node  
            dest_node = self._create_node_info(
                ip=row.get('destination_ip', ''),
                hostname=row.get('destination_hostname', ''),
                app_name=app_name,
                role='destination',
                service_type=row.get('service_type', ''),
                service_category=row.get('service_category', '')
            )
            
            # Connection edge
            edge_info = {
                'source': source_node['id'],
                'target': dest_node['id'],
                'protocol': row.get('protocol', ''),
                'port': row.get('port', ''),
                'bytes_in': row.get('bytes_in', 0),
                'bytes_out': row.get('bytes_out', 0),
                'service_type': row.get('service_type', ''),
                'application': app_name,
                'archetype': row.get('archetype', ''),
                'connection_weight': (row.get('bytes_in', 0) + row.get('bytes_out', 0))
            }
            
            self.nodes.append(source_node)
            self.nodes.append(dest_node)
            self.edges.append(edge_info)
    
    def _create_node_info(self, ip, hostname, app_name, role, service_type='', service_category=''):
        """Create rich node metadata for hover information"""
        
        # Determine primary identifier
        primary_id = hostname if hostname and hostname != 'nan' else ip
        if not primary_id or primary_id == 'nan':
            primary_id = f"unknown_{role}_{len(self.nodes)}"
        
        # Classify infrastructure type
        infra_type = self._classify_infrastructure_type(primary_id, service_type)
        zone = self._determine_network_zone(primary_id, service_category)
        
        return {
            'id': primary_id,
            'label': primary_id[:20] + '...' if len(primary_id) > 20 else primary_id,
            'ip_address': ip,
            'hostname': hostname,
            'application': app_name,
            'service_type': service_type,
            'service_category': service_category,
            'infrastructure_type': infra_type,
            'network_zone': zone,
            'role': role,
            'node_type': self._get_node_type(service_category, service_type),
            'hover_info': self._generate_hover_info(ip, hostname, app_name, service_type, service_category, infra_type)
        }
    
    def _classify_infrastructure_type(self, identifier, service_type):
        """Classify infrastructure abstraction level"""
        
        id_lower = identifier.lower()
        
        # Container/OpenShift patterns
        if any(pattern in id_lower for pattern in ['pod-', 'container-', 'docker-', 'k8s-', 'ocp-']):
            return 'container'
        elif any(pattern in id_lower for pattern in ['vm-', 'virtual', 'virt-']):
            return 'virtual_machine'
        elif any(pattern in id_lower for pattern in ['db-', 'database', 'sql']):
            return 'database_server'
        elif service_type == 'web_server':
            return 'web_server'
        elif service_type == 'app_server':
            return 'application_server'
        elif service_type == 'load_balancer':
            return 'load_balancer'
        else:
            return 'physical_server'
    
    def _determine_network_zone(self, identifier, service_category):
        """Determine network zone/tier"""
        
        if service_category == 'APPLICATION':
            if 'web' in identifier.lower():
                return 'dmz'
            else:
                return 'application_tier'
        elif service_category == 'DATA':
            return 'database_tier'
        elif service_category == 'MESSAGING':
            return 'messaging_tier'
        elif service_category == 'SECURITY':
            return 'security_tier'
        else:
            return 'infrastructure_tier'
    
    def _get_node_type(self, service_category, service_type):
        """Get node type for visualization styling"""
        
        type_mapping = {
            'APPLICATION': 'app-node',
            'DATA': 'db-node', 
            'MESSAGING': 'msg-node',
            'SECURITY': 'sec-node',
            'INFRASTRUCTURE': 'infra-node',
            'NETWORK': 'net-node'
        }
        return type_mapping.get(service_category, 'default-node')
    
    def _generate_hover_info(self, ip, hostname, app_name, service_type, service_category, infra_type):
        """Generate rich hover tooltip content"""
        
        return {
            'IP Address': ip if ip else 'N/A',
            'Hostname': hostname if hostname else 'N/A', 
            'Application': app_name,
            'Service Type': service_type.replace('_', ' ').title() if service_type else 'Unknown',
            'Service Category': service_category,
            'Infrastructure': infra_type.replace('_', ' ').title(),
            'Network Zone': self._determine_network_zone(hostname or ip, service_category)
        }
    
    def generate_interactive_html(self, output_file="enterprise_architecture.html"):
        """Generate interactive HTML with D3.js visualization"""
        
        # Remove duplicates
        unique_nodes = {}
        for node in self.nodes:
            unique_nodes[node['id']] = node
        
        nodes_list = list(unique_nodes.values())
        
        # Create the interactive HTML
        html_template = self._get_html_template()
        
        # Inject data
        html_content = html_template.replace(
            '{{NODES_DATA}}', json.dumps(nodes_list, indent=2)
        ).replace(
            '{{EDGES_DATA}}', json.dumps(self.edges, indent=2)
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Interactive architecture diagram generated: {output_file}")
        return output_file
    
    def _get_html_template(self):
        """HTML template with D3.js interactive visualization"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Architecture Diagram</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 20px;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        
        #diagram {
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .node {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .node:hover {
            stroke-width: 3px;
            filter: brightness(1.2);
        }
        
        .app-node { fill: #4CAF50; stroke: #2E7D32; }
        .db-node { fill: #FF5722; stroke: #BF360C; }
        .msg-node { fill: #2196F3; stroke: #0D47A1; }
        .sec-node { fill: #FF9800; stroke: #E65100; }
        .infra-node { fill: #9C27B0; stroke: #4A148C; }
        .net-node { fill: #607D8B; stroke: #263238; }
        .default-node { fill: #757575; stroke: #212121; }
        
        .link {
            stroke: #666;
            stroke-opacity: 0.6;
            transition: all 0.3s ease;
        }
        
        .link:hover {
            stroke-opacity: 1;
            stroke-width: 3px;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            max-width: 300px;
            z-index: 1000;
        }
        
        .tooltip h4 {
            margin: 0 0 8px 0;
            color: #4CAF50;
        }
        
        .tooltip-row {
            margin: 4px 0;
        }
        
        .tooltip-label {
            font-weight: bold;
            color: #ccc;
        }
        
        .controls {
            margin: 20px 0;
            text-align: center;
        }
        
        .control-btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 4px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .control-btn:hover {
            background: #1976D2;
        }
        
        .legend {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin: 20px 0;
            gap: 15px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 12px;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            margin-right: 6px;
            border-radius: 50%;
            border: 2px solid #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enterprise Architecture Diagram</h1>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50; border-color: #2E7D32;"></div>
                Application Services
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF5722; border-color: #BF360C;"></div>
                Database Services
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2196F3; border-color: #0D47A1;"></div>
                Messaging Services
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF9800; border-color: #E65100;"></div>
                Security Services
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9C27B0; border-color: #4A148C;"></div>
                Infrastructure
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #607D8B; border-color: #263238;"></div>
                Network Services
            </div>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="resetZoom()">Reset View</button>
            <button class="control-btn" onclick="toggleLabels()">Toggle Labels</button>
            <button class="control-btn" onclick="exportSVG()">Export SVG</button>
        </div>
        
        <svg id="diagram" width="100%" height="800"></svg>
    </div>

    <script>
        // Data
        const nodes = {{NODES_DATA}};
        const links = {{EDGES_DATA}};
        
        // SVG setup
        const svg = d3.select("#diagram");
        const width = parseInt(svg.style("width"));
        const height = 800;
        
        svg.attr("viewBox", [0, 0, width, height]);
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", zoomed);
        
        svg.call(zoom);
        
        const g = svg.append("g");
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(25));
        
        // Links
        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.max(1, Math.log(d.connection_weight + 1)))
            .on("mouseover", showLinkTooltip)
            .on("mouseout", hideTooltip);
        
        // Nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", d => `node ${d.node_type}`)
            .attr("r", 12)
            .on("mouseover", showNodeTooltip)
            .on("mouseout", hideTooltip)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Labels
        let labelsVisible = true;
        const labels = g.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.label)
            .attr("font-size", 10)
            .attr("dx", 15)
            .attr("dy", 4);
        
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });
        
        // Event handlers
        function showNodeTooltip(event, d) {
            let content = `<h4>${d.label}</h4>`;
            for (const [key, value] of Object.entries(d.hover_info)) {
                content += `<div class="tooltip-row"><span class="tooltip-label">${key}:</span> ${value}</div>`;
            }
            
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }
        
        function showLinkTooltip(event, d) {
            const content = `
                <h4>Connection</h4>
                <div class="tooltip-row"><span class="tooltip-label">Protocol:</span> ${d.protocol}</div>
                <div class="tooltip-row"><span class="tooltip-label">Port:</span> ${d.port}</div>
                <div class="tooltip-row"><span class="tooltip-label">Application:</span> ${d.application}</div>
                <div class="tooltip-row"><span class="tooltip-label">Service:</span> ${d.service_type}</div>
                <div class="tooltip-row"><span class="tooltip-label">Traffic:</span> ${(d.connection_weight).toLocaleString()} bytes</div>
            `;
            
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }
        
        function hideTooltip() {
            tooltip.transition().duration(500).style("opacity", 0);
        }
        
        function zoomed(event) {
            g.attr("transform", event.transform);
        }
        
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        // Control functions
        function resetZoom() {
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }
        
        function toggleLabels() {
            labelsVisible = !labelsVisible;
            labels.style("display", labelsVisible ? "block" : "none");
        }
        
        function exportSVG() {
            const svgData = new XMLSerializer().serializeToString(svg.node());
            const blob = new Blob([svgData], {type: "image/svg+xml"});
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "enterprise_architecture.svg";
            link.click();
        }
    </script>
</body>
</html>
        """

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate interactive enterprise architecture diagrams")
    parser.add_argument("--input-dir", default="complete_composite_analysis", 
                       help="Directory containing normalized data files")
    parser.add_argument("--output", default="enterprise_architecture.html",
                       help="Output HTML file")
    
    args = parser.parse_args()
    
    # Generate interactive diagram
    mapper = InteractiveArchitectureMapper(args.input_dir)
    mapper.load_all_applications()
    output_file = mapper.generate_interactive_html(args.output)
    
    print(f"\nInteractive architecture diagram created: {output_file}")
    print("Open this file in a web browser to explore the interactive diagram.")
    print("\nFeatures:")
    print("- Hover over nodes and connections for detailed information")
    print("- Drag nodes to reorganize the layout")  
    print("- Zoom and pan to explore different areas")
    print("- Export as SVG for further editing")

if __name__ == "__main__":
    main()