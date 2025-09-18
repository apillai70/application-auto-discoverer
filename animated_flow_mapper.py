#!/usr/bin/env python3
"""
Per-Application Animated Flow Mapper
Creates animated traffic flow diagrams for individual applications
Outputs: SVG, HTML, JSON formats for each application
"""

import pandas as pd
import json
from pathlib import Path
import networkx as nx
from collections import defaultdict
import math

class AnimatedFlowMapper:
    def __init__(self, analysis_dir="complete_composite_analysis"):
        self.analysis_dir = Path(analysis_dir)
        self.output_dir = Path("animated_flow_diagrams")
        self.output_dir.mkdir(exist_ok=True)
        
    def process_all_applications(self):
        """Process each application individually"""
        
        for csv_file in self.analysis_dir.glob("*_normalized_data.csv"):
            app_name = csv_file.stem.replace("_normalized_data", "")
            print(f"Processing animated flows for: {app_name}")
            
            df = pd.read_csv(csv_file)
            self.create_app_flow_diagram(app_name, df)
    
    def create_app_flow_diagram(self, app_name, df):
        """Create animated flow diagram for a single application"""
        
        # Process data
        nodes, edges, flow_sequences = self._process_app_data(app_name, df)
        
        # Generate multiple output formats
        self._generate_animated_html(app_name, nodes, edges, flow_sequences)
        self._generate_static_svg(app_name, nodes, edges)
        self._generate_json_export(app_name, nodes, edges, flow_sequences)
        
        print(f"Generated animated diagrams for {app_name}")
    
    def _process_app_data(self, app_name, df):
        """Process application data into nodes, edges, and flow sequences"""
        
        nodes = {}
        edges = []
        flow_sequences = []
        
        # Create unique nodes
        for idx, row in df.iterrows():
            # Source node
            src_id = self._get_node_id(row, 'source')
            if src_id not in nodes:
                nodes[src_id] = self._create_node(row, 'source', app_name)
            
            # Destination node
            dst_id = self._get_node_id(row, 'destination')
            if dst_id not in nodes:
                nodes[dst_id] = self._create_node(row, 'destination', app_name)
            
            # Create edge with flow data
            edge = {
                'id': f"edge_{idx}",
                'source': src_id,
                'target': dst_id,
                'protocol': row.get('protocol', ''),
                'port': row.get('port', ''),
                'bytes_in': row.get('bytes_in', 0),
                'bytes_out': row.get('bytes_out', 0),
                'service_type': row.get('service_type', ''),
                'flow_weight': row.get('bytes_in', 0) + row.get('bytes_out', 0),
                'animation_delay': (idx * 100) % 5000  # Stagger animations
            }
            edges.append(edge)
            
            # Create flow sequence for animation
            flow_sequences.append({
                'timestamp': idx * 50,  # Animation timing
                'source': src_id,
                'target': dst_id,
                'protocol': row.get('protocol', ''),
                'bytes': edge['flow_weight'],
                'color': self._get_protocol_color(row.get('protocol', ''))
            })
        
        return list(nodes.values()), edges, flow_sequences
    
    def _get_node_id(self, row, direction):
        """Get unique node identifier"""
        if direction == 'source':
            return row.get('source_hostname') or row.get('source_ip') or f"unknown_src_{hash(str(row))}"
        else:
            return row.get('destination_hostname') or row.get('destination_ip') or f"unknown_dst_{hash(str(row))}"
    
    def _create_node(self, row, direction, app_name):
        """Create node with metadata"""
        node_id = self._get_node_id(row, direction)
        
        if direction == 'source':
            ip = row.get('source_ip', '')
            hostname = row.get('source_hostname', '')
        else:
            ip = row.get('destination_ip', '')
            hostname = row.get('destination_hostname', '')
        
        # Handle NaN values - convert to empty strings
        if pd.isna(ip) or str(ip) == 'nan':
            ip = ''
        else:
            ip = str(ip)
            
        if pd.isna(hostname) or str(hostname) == 'nan':
            hostname = ''
        else:
            hostname = str(hostname)
            
        # Determine node type and styling
        service_category = row.get('service_category', 'UNKNOWN')
        service_type = row.get('service_type', 'unknown')
        
        return {
            'id': node_id,
            'label': self._get_node_label(hostname, ip),
            'ip': ip,
            'hostname': hostname,
            'application': app_name,
            'service_category': service_category,
            'service_type': service_type,
            'node_type': service_category.lower(),
            'infrastructure_type': self._infer_infrastructure_type(hostname or ip, service_type),
            'zone': self._determine_zone(service_category),
            'x': 0,  # Will be positioned by layout algorithm
            'y': 0
        }
    
    def _get_node_label(self, hostname, ip):
        """Get display label for node"""
        # Handle NaN values properly
        if pd.notna(hostname) and str(hostname) != 'nan' and str(hostname).strip():
            hostname_str = str(hostname)
            return hostname_str[:15] + '...' if len(hostname_str) > 15 else hostname_str
        elif pd.notna(ip) and str(ip) != 'nan' and str(ip).strip():
            return str(ip)
        else:
            return 'Unknown'
    
    def _infer_infrastructure_type(self, identifier, service_type):
        """Infer infrastructure abstraction level"""
        if not identifier:
            return 'unknown'
            
        id_lower = identifier.lower()
        
        # Container patterns
        if any(pattern in id_lower for pattern in ['pod-', 'container-', 'docker-', 'k8s-', 'ocp-']):
            return 'container'
        # VM patterns
        elif any(pattern in id_lower for pattern in ['vm-', 'virtual', 'virt-']):
            return 'vm'
        # Database patterns
        elif 'db' in service_type or 'database' in id_lower:
            return 'database'
        # Web server patterns
        elif service_type == 'web_server':
            return 'web_server'
        # Load balancer patterns
        elif service_type == 'load_balancer':
            return 'load_balancer'
        else:
            return 'server'
    
    def _determine_zone(self, service_category):
        """Determine network zone for positioning"""
        zone_map = {
            'APPLICATION': 'app_tier',
            'DATA': 'data_tier',
            'MESSAGING': 'msg_tier',
            'SECURITY': 'dmz',
            'INFRASTRUCTURE': 'infra_tier',
            'NETWORK': 'net_tier'
        }
        return zone_map.get(service_category, 'unknown_tier')
    
    def _get_protocol_color(self, protocol):
        """Get color for protocol-based animation"""
        color_map = {
            'HTTP': '#4CAF50',
            'HTTPS': '#2E7D32', 
            'IBMMQ': '#FF5722',
            'IBMMQ-SSL': '#D32F2F',
            'GRPC': '#2196F3',
            'MYSQL': '#FF9800',
            'POSTGRESQL': '#9C27B0',
            'REDIS': '#E91E63',
            'SSH': '#607D8B'
        }
        return color_map.get(protocol, '#757575')
    
    def _generate_animated_html(self, app_name, nodes, edges, flow_sequences):
        """Generate animated HTML diagram"""
        
        output_file = self.output_dir / f"{app_name}_animated_flow.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} - Animated Flow Diagram</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
        }}
        
        .container {{
            background: #2d2d2d;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        
        h1 {{
            color: #4CAF50;
            text-align: center;
            margin-bottom: 10px;
        }}
        
        .app-info {{
            text-align: center;
            color: #ccc;
            margin-bottom: 30px;
        }}
        
        #diagram {{
            background: #1e1e1e;
            border-radius: 4px;
            border: 1px solid #444;
        }}
        
        .node {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .node:hover {{
            stroke-width: 3px;
            filter: brightness(1.3);
        }}
        
        /* Node types */
        .application {{ fill: #4CAF50; stroke: #2E7D32; }}
        .data {{ fill: #FF5722; stroke: #D32F2F; }}
        .messaging {{ fill: #2196F3; stroke: #1976D2; }}
        .security {{ fill: #FF9800; stroke: #F57C00; }}
        .infrastructure {{ fill: #9C27B0; stroke: #7B1FA2; }}
        .network {{ fill: #607D8B; stroke: #455A64; }}
        .unknown {{ fill: #757575; stroke: #424242; }}
        
        .link {{
            stroke: #666;
            stroke-opacity: 0.6;
            fill: none;
        }}
        
        .flow-particle {{
            r: 4;
            opacity: 0;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.95);
            color: white;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #4CAF50;
            font-size: 12px;
            pointer-events: none;
            max-width: 300px;
            z-index: 1000;
        }}
        
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .control-btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .control-btn:hover {{
            background: #45a049;
        }}
        
        .control-btn:disabled {{
            background: #666;
            cursor: not-allowed;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            font-size: 14px;
        }}
        
        .stat-item {{
            text-align: center;
            color: #ccc;
        }}
        
        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app_name} Application Flow</h1>
        <div class="app-info">Real-time Traffic Flow Visualization</div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="node-count">{len(nodes)}</div>
                <div>Components</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="connection-count">{len(edges)}</div>
                <div>Connections</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="flow-count">{len(flow_sequences)}</div>
                <div>Flow Events</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="control-btn" onclick="startAnimation()">Start Animation</button>
            <button class="control-btn" onclick="stopAnimation()">Stop</button>
            <button class="control-btn" onclick="resetView()">Reset View</button>
            <button class="control-btn" onclick="exportSVG()">Export SVG</button>
            <button class="control-btn" onclick="saveImage()">Save PNG</button>
        </div>
        
        <svg id="diagram" width="100%" height="600"></svg>
    </div>

    <script>
        // Data
        const nodes = {json.dumps(nodes, indent=2)};
        const links = {json.dumps(edges, indent=2)};
        const flowSequences = {json.dumps(flow_sequences, indent=2)};
        
        // Animation state
        let animationRunning = false;
        let animationInterval;
        let currentFlowIndex = 0;
        
        // SVG setup
        const svg = d3.select("#diagram");
        const width = parseInt(svg.style("width"));
        const height = 600;
        
        svg.attr("viewBox", [0, 0, width, height]);
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", zoomed);
        
        svg.call(zoom);
        
        const g = svg.append("g");
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        // Create links
        const link = g.append("g")
            .selectAll("path")
            .data(links)
            .enter().append("path")
            .attr("class", "link")
            .attr("stroke-width", d => Math.max(1, Math.log(d.flow_weight / 1000 + 1)))
            .on("mouseover", showLinkTooltip)
            .on("mouseout", hideTooltip);
        
        // Create nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", d => `node ${{d.node_type}}`)
            .attr("r", d => Math.max(8, Math.log(nodes.filter(n => 
                links.some(l => l.source.id === d.id || l.target.id === d.id)
            ).length + 1) * 3))
            .on("mouseover", showNodeTooltip)
            .on("mouseout", hideTooltip)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Labels
        const labels = g.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.label)
            .attr("font-size", 10)
            .attr("fill", "white")
            .attr("text-anchor", "middle")
            .attr("dy", -15);
        
        // Flow particles container
        const flowParticles = g.append("g").attr("class", "flow-particles");
        
        // Update simulation
        simulation.on("tick", () => {{
            link.attr("d", d => {{
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dr = Math.sqrt(dx * dx + dy * dy) * 0.3;
                return `M${{d.source.x}},${{d.source.y}}A${{dr}},${{dr}} 0 0,1 ${{d.target.x}},${{d.target.y}}`;
            }});
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        // Animation functions
        function startAnimation() {{
            if (animationRunning) return;
            
            animationRunning = true;
            currentFlowIndex = 0;
            
            animationInterval = setInterval(() => {{
                if (currentFlowIndex >= flowSequences.length) {{
                    currentFlowIndex = 0;
                }}
                
                animateFlow(flowSequences[currentFlowIndex]);
                currentFlowIndex++;
            }}, 200);
            
            document.querySelector('button[onclick="startAnimation()"]').disabled = true;
            document.querySelector('button[onclick="stopAnimation()"]').disabled = false;
        }}
        
        function stopAnimation() {{
            animationRunning = false;
            clearInterval(animationInterval);
            
            // Clear all particles
            flowParticles.selectAll(".flow-particle").remove();
            
            document.querySelector('button[onclick="startAnimation()"]').disabled = false;
            document.querySelector('button[onclick="stopAnimation()"]').disabled = true;
        }}
        
        function animateFlow(flowData) {{
            const sourceNode = nodes.find(n => n.id === flowData.source);
            const targetNode = nodes.find(n => n.id === flowData.target);
            
            if (!sourceNode || !targetNode) return;
            
            // Create particle
            const particle = flowParticles.append("circle")
                .attr("class", "flow-particle")
                .attr("fill", flowData.color)
                .attr("r", Math.max(2, Math.log(flowData.bytes / 1000 + 1)))
                .attr("cx", sourceNode.x)
                .attr("cy", sourceNode.y)
                .style("opacity", 0);
            
            // Animate particle movement
            particle
                .transition()
                .duration(50)
                .style("opacity", 0.8)
                .transition()
                .duration(1500)
                .ease(d3.easeCubicInOut)
                .attr("cx", targetNode.x)
                .attr("cy", targetNode.y)
                .transition()
                .duration(200)
                .style("opacity", 0)
                .remove();
        }}
        
        // Tooltip functions
        function showNodeTooltip(event, d) {{
            const content = `
                <h4>${{d.label}}</h4>
                <div><strong>IP:</strong> ${{d.ip || 'N/A'}}</div>
                <div><strong>Hostname:</strong> ${{d.hostname || 'N/A'}}</div>
                <div><strong>Service Type:</strong> ${{d.service_type.replace('_', ' ')}}</div>
                <div><strong>Infrastructure:</strong> ${{d.infrastructure_type}}</div>
                <div><strong>Zone:</strong> ${{d.zone}}</div>
            `;
            
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }}
        
        function showLinkTooltip(event, d) {{
            const content = `
                <h4>Connection</h4>
                <div><strong>Protocol:</strong> ${{d.protocol}}</div>
                <div><strong>Port:</strong> ${{d.port}}</div>
                <div><strong>Service:</strong> ${{d.service_type}}</div>
                <div><strong>Traffic:</strong> ${{d.flow_weight.toLocaleString()}} bytes</div>
            `;
            
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }}
        
        function hideTooltip() {{
            tooltip.transition().duration(500).style("opacity", 0);
        }}
        
        // Control functions
        function zoomed(event) {{
            g.attr("transform", event.transform);
        }}
        
        function resetView() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}
        
        function exportSVG() {{
            const svgData = new XMLSerializer().serializeToString(svg.node());
            const blob = new Blob([svgData], {{type: "image/svg+xml"}});
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "{app_name}_flow_diagram.svg";
            link.click();
        }}
        
        function saveImage() {{
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            const img = new Image();
            
            canvas.width = width;
            canvas.height = height;
            
            const svgData = new XMLSerializer().serializeToString(svg.node());
            const blob = new Blob([svgData], {{type: "image/svg+xml;charset=utf-8"}});
            const url = URL.createObjectURL(blob);
            
            img.onload = function() {{
                ctx.drawImage(img, 0, 0);
                const imgURL = canvas.toDataURL("image/png");
                const dlLink = document.createElement("a");
                dlLink.href = imgURL;
                dlLink.download = "{app_name}_flow_diagram.png";
                dlLink.click();
            }};
            
            img.src = url;
        }}
        
        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_static_svg(self, app_name, nodes, edges):
        """Generate static SVG diagram"""
        
        output_file = self.output_dir / f"{app_name}_static_diagram.svg"
        
        # Create NetworkX graph for layout
        G = nx.Graph()
        for node in nodes:
            G.add_node(node['id'], **node)
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], **edge)
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Scale positions
        width, height = 800, 600
        for node_id in pos:
            pos[node_id] = (
                pos[node_id][0] * width/2 + width/2,
                pos[node_id][1] * height/2 + height/2
            )
        
        # Generate SVG
        svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <title>{app_name} Network Architecture</title>
    <defs>
        <style>
            .node-app {{ fill: #4CAF50; stroke: #2E7D32; }}
            .node-data {{ fill: #FF5722; stroke: #D32F2F; }}
            .node-messaging {{ fill: #2196F3; stroke: #1976D2; }}
            .node-security {{ fill: #FF9800; stroke: #F57C00; }}
            .node-infrastructure {{ fill: #9C27B0; stroke: #7B1FA2; }}
            .link {{ stroke: #666; stroke-width: 2; }}
            .label {{ font-family: Arial; font-size: 10px; fill: #333; }}
        </style>
    </defs>
    
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#f8f9fa"/>
    
    <!-- Title -->
    <text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#333">
        {app_name} - Network Architecture
    </text>
    
    <!-- Edges -->
"""
        
        for edge in edges:
            if edge['source'] in pos and edge['target'] in pos:
                x1, y1 = pos[edge['source']]
                x2, y2 = pos[edge['target']]
                svg_content += f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="link"/>\n'
        
        # Nodes
        svg_content += "    <!-- Nodes -->\n"
        for node in nodes:
            if node['id'] in pos:
                x, y = pos[node['id']]
                node_class = f"node-{node['node_type']}"
                svg_content += f'    <circle cx="{x}" cy="{y}" r="12" class="{node_class}"/>\n'
                svg_content += f'    <text x="{x}" y="{y-15}" text-anchor="middle" class="label">{node["label"]}</text>\n'
        
        svg_content += "</svg>"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    def _generate_json_export(self, app_name, nodes, edges, flow_sequences):
        """Generate JSON export for further processing"""
        
        output_file = self.output_dir / f"{app_name}_flow_data.json"
        
        export_data = {
            'application': app_name,
            'generated_at': pd.Timestamp.now().isoformat(),
            'nodes': nodes,
            'edges': edges,
            'flow_sequences': flow_sequences,
            'metadata': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'flow_count': len(flow_sequences),
                'protocols': list(set(edge['protocol'] for edge in edges)),
                'service_types': list(set(node['service_type'] for node in nodes))
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate animated flow diagrams per application")
    parser.add_argument("--input-dir", default="complete_composite_analysis", 
                       help="Directory containing normalized data files")
    parser.add_argument("--output-dir", default="animated_flow_diagrams",
                       help="Output directory for diagrams")
    
    args = parser.parse_args()
    
    mapper = AnimatedFlowMapper(args.input_dir)
    mapper.output_dir = Path(args.output_dir)
    mapper.output_dir.mkdir(exist_ok=True)
    
    mapper.process_all_applications()
    
    print(f"\nAnimated flow diagrams generated in: {mapper.output_dir}")
    print("\nGenerated files for each application:")
    print("- *_animated_flow.html (Interactive animated diagram)")
    print("- *_static_diagram.svg (Static SVG for editing)")
    print("- *_flow_data.json (Data export)")

if __name__ == "__main__":
    main()