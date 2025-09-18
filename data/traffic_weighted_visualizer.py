#!/usr/bin/env python3
"""
Traffic-Weighted Network Visualizer with IBM MQ Support

Creates network topology visualizations where:
1. Link thickness represents traffic volume
2. Node size represents centrality/importance
3. Colors represent composite architectural patterns
4. IBM MQ and messaging patterns are highlighted
5. Multiple components per application are shown
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from collections import defaultdict, Counter
import math
import argparse

class TrafficWeightedVisualizer:
    def __init__(self, df):
        self.df = df
        self.G = nx.MultiDiGraph()
        self.traffic_flows = defaultdict(lambda: defaultdict(float))
        self.protocol_flows = defaultdict(lambda: defaultdict(list))
        self.composite_patterns = {}
        
    def build_traffic_graph(self):
        """Build graph with traffic-weighted edges and composite pattern detection"""
        
        print("Building traffic-weighted network graph...")
        
        # Group connections by source-destination pairs
        connection_groups = defaultdict(lambda: {
            'total_bytes': 0,
            'connections': [],
            'protocols': Counter(),
            'applications': set(),
            'dominant_protocol': '',
            'avg_bytes_per_conn': 0
        })
        
        for _, row in self.df.iterrows():
            src = row.get('source_ip') or row.get('source_hostname', 'unknown_src')
            dst = row.get('destination_ip') or row.get('destination_hostname', 'unknown_dst')
            
            if src == 'unknown_src' or dst == 'unknown_dst':
                continue
            
            conn_key = (src, dst)
            
            # Aggregate traffic data
            bytes_in = int(row.get('bytes_in', 0))
            bytes_out = int(row.get('bytes_out', 0))
            total_bytes = bytes_in + bytes_out
            
            connection_groups[conn_key]['total_bytes'] += total_bytes
            connection_groups[conn_key]['connections'].append({
                'protocol': row.get('protocol', ''),
                'port': row.get('port', ''),
                'bytes_in': bytes_in,
                'bytes_out': bytes_out,
                'service_type': row.get('service_type', ''),
                'application': row.get('application', '')
            })
            connection_groups[conn_key]['protocols'][row.get('protocol', 'Unknown')] += 1
            connection_groups[conn_key]['applications'].add(row.get('application', ''))
        
        # Build graph with aggregated data
        for (src, dst), data in connection_groups.items():
            data['avg_bytes_per_conn'] = data['total_bytes'] / len(data['connections'])
            data['dominant_protocol'] = data['protocols'].most_common(1)[0][0] if data['protocols'] else 'Unknown'
            
            # Determine edge type based on protocol
            edge_type = self._classify_edge_type(data['dominant_protocol'], data['connections'])
            
            self.G.add_edge(src, dst,
                          weight=data['total_bytes'],
                          connection_count=len(data['connections']),
                          protocols=list(data['protocols'].keys()),
                          dominant_protocol=data['dominant_protocol'],
                          applications=list(data['applications']),
                          edge_type=edge_type,
                          avg_bytes=data['avg_bytes_per_conn'])
            
            # Store detailed flow information
            self.traffic_flows[src][dst] = data['total_bytes']
            self.protocol_flows[src][dst] = data['connections']
        
        print(f"Created graph with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
        
        # Detect composite patterns for each node
        self._detect_composite_node_patterns()
    
    def _classify_edge_type(self, protocol, connections):
        """Classify edge type based on protocol and traffic patterns"""
        
        protocol_types = {
            'IBMMQ': 'ibm_mq',
            'IBMMQ-SSL': 'ibm_mq_secure',
            'AMQP': 'message_broker',
            'KAFKA': 'event_streaming',
            'JMS': 'java_messaging',
            'MQTT': 'iot_messaging',
            'HTTP': 'web_api',
            'HTTPS': 'secure_web_api',
            'GRPC': 'microservice_api',
            'MYSQL': 'database',
            'POSTGRESQL': 'database',
            'ORACLE-TNS': 'enterprise_db',
            'TDS': 'mssql_db',
            'REDIS': 'cache',
            'RDP': 'remote_desktop',
            'SSH': 'secure_shell',
            'TELNET': 'terminal'
        }
        
        return protocol_types.get(protocol, 'generic')
    
    def _detect_composite_node_patterns(self):
        """Detect composite architectural patterns for each node"""
        
        print("Detecting composite patterns for nodes...")
        
        for node in self.G.nodes():
            patterns = set()
            
            # Analyze incoming connections (node as destination)
            incoming_protocols = []
            incoming_traffic = 0
            for pred in self.G.predecessors(node):
                edge_data = self.G[pred][node][0]  # Get first edge (MultiDiGraph)
                incoming_protocols.extend(edge_data.get('protocols', []))
                incoming_traffic += edge_data.get('weight', 0)
            
            # Analyze outgoing connections (node as source)
            outgoing_protocols = []
            outgoing_traffic = 0
            for succ in self.G.successors(node):
                edge_data = self.G[node][succ][0]
                outgoing_protocols.extend(edge_data.get('protocols', []))
                outgoing_traffic += edge_data.get('weight', 0)
            
            # Determine patterns based on protocol combinations
            all_protocols = set(incoming_protocols + outgoing_protocols)
            
            # Web tier pattern
            if any(p in all_protocols for p in ['HTTP', 'HTTPS']):
                patterns.add('web_layer')
            
            # Database pattern
            if any(p in all_protocols for p in ['MYSQL', 'POSTGRESQL', 'ORACLE-TNS', 'TDS', 'MONGODB']):
                patterns.add('data_layer')
            
            # Messaging pattern (including IBM MQ)
            if any(p in all_protocols for p in ['IBMMQ', 'IBMMQ-SSL', 'AMQP', 'KAFKA', 'JMS', 'MQTT']):
                patterns.add('messaging_layer')
                
                # Specific IBM MQ pattern
                if any(p.startswith('IBMMQ') for p in all_protocols):
                    patterns.add('ibm_mq_integration')
            
            # API Gateway pattern (high fanout)
            if len(list(self.G.successors(node))) > 3 and 'HTTP' in all_protocols:
                patterns.add('api_gateway')
            
            # Microservices pattern
            if 'GRPC' in all_protocols or len([p for p in all_protocols if p == 'HTTP']) > 2:
                patterns.add('microservices')
            
            # Legacy system pattern
            if any(p in all_protocols for p in ['RDP', 'TELNET', 'TDS']):
                patterns.add('legacy_system')
            
            # Cache pattern
            if 'REDIS' in all_protocols:
                patterns.add('cache_layer')
            
            # Hub pattern (high connectivity)
            total_connections = len(list(self.G.predecessors(node))) + len(list(self.G.successors(node)))
            if total_connections > 5:
                patterns.add('integration_hub')
            
            self.composite_patterns[node] = patterns if patterns else {'simple_service'}
    
    def create_traffic_weighted_visualization(self, output_path=None, title="Traffic-Weighted Network Architecture"):
        """Create comprehensive traffic-weighted visualization"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(24, 20))
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # Main network graph with traffic weighting
        self._plot_main_network(ax1)
        
        # Protocol distribution and traffic analysis
        self._plot_protocol_analysis(ax2)
        
        # Composite pattern distribution
        self._plot_composite_patterns(ax3)
        
        # Traffic flow matrix
        self._plot_traffic_matrix(ax4)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Traffic-weighted visualization saved to: {output_path}")
        else:
            plt.show()
    
    def _plot_main_network(self, ax):
        """Plot main network graph with traffic-weighted edges"""
        
        ax.set_title("Traffic-Weighted Network Topology", fontsize=14, fontweight='bold')
        
        # Calculate layout
        pos = self._calculate_optimized_layout()
        
        # Calculate edge weights for visualization
        edge_weights = []
        edge_colors = []
        edge_styles = []
        
        for src, dst, data in self.G.edges(data=True):
            weight = data.get('weight', 0)
            edge_type = data.get('edge_type', 'generic')
            
            edge_weights.append(weight)
            
            # Color based on edge type
            color_map = {
                'ibm_mq': '#FF6B6B',
                'ibm_mq_secure': '#FF4444',
                'message_broker': '#96CEB4',
                'event_streaming': '#74B9FF',
                'web_api': '#4ECDC4',
                'secure_web_api': '#26D0CE',
                'database': '#E55039',
                'microservice_api': '#A29BFE',
                'cache': '#FDCB6E',
                'generic': '#DDA0DD'
            }
            edge_colors.append(color_map.get(edge_type, '#999999'))
            
            # Style based on protocol
            if edge_type in ['ibm_mq', 'ibm_mq_secure']:
                edge_styles.append('solid')
            elif edge_type in ['message_broker', 'event_streaming']:
                edge_styles.append('dashed')
            else:
                edge_styles.append('solid')
        
        # Normalize edge weights for thickness
        if edge_weights:
            max_weight = max(edge_weights)
            min_weight = min(edge_weights)
            weight_range = max_weight - min_weight if max_weight > min_weight else 1
            
            normalized_widths = []
            for weight in edge_weights:
                normalized = (weight - min_weight) / weight_range
                width = 0.5 + (normalized * 6.0)  # 0.5 to 6.5 thickness
                normalized_widths.append(width)
        else:
            normalized_widths = [1.0] * len(edge_weights)
        
        # Draw edges
        for i, (src, dst, data) in enumerate(self.G.edges(data=True)):
            if src in pos and dst in pos:
                ax.annotate('', xy=pos[dst], xytext=pos[src],
                           arrowprops=dict(
                               arrowstyle='->',
                               color=edge_colors[i],
                               lw=normalized_widths[i],
                               alpha=0.7,
                               linestyle=edge_styles[i]
                           ))
        
        # Calculate node properties
        node_sizes = []
        node_colors = []
        
        for node in self.G.nodes():
            # Size based on centrality
            degree = self.G.degree(node)
            node_sizes.append(300 + degree * 50)
            
            # Color based on dominant composite pattern
            patterns = self.composite_patterns.get(node, {'simple_service'})
            dominant_pattern = next(iter(patterns))  # Get first pattern
            
            pattern_colors = {
                'web_layer': '#4ECDC4',
                'data_layer': '#FF6B6B',
                'messaging_layer': '#96CEB4',
                'ibm_mq_integration': '#E74C3C',
                'api_gateway': '#F39C12',
                'microservices': '#9B59B6',
                'legacy_system': '#95A5A6',
                'cache_layer': '#F1C40F',
                'integration_hub': '#E67E22',
                'simple_service': '#BDC3C7'
            }
            
            node_colors.append(pattern_colors.get(dominant_pattern, '#BDC3C7'))
        
        # Draw nodes
        if pos:
            for i, node in enumerate(self.G.nodes()):
                if node in pos:
                    ax.scatter(pos[node][0], pos[node][1], 
                             s=node_sizes[i], c=node_colors[i], 
                             alpha=0.8, edgecolors='black', linewidth=1)
                    
                    # Add node labels
                    label = node[:8] + '..' if len(node) > 10 else node
                    ax.annotate(label, pos[node], xytext=(0, 5), 
                              textcoords='offset points', ha='center', 
                              fontsize=8, fontweight='bold')
        
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Add legend for edge types
        legend_elements = []
        for edge_type, color in [
            ('IBM MQ', '#FF6B6B'),
            ('Message Broker', '#96CEB4'),
            ('Web/API', '#4ECDC4'),
            ('Database', '#E55039'),
            ('Microservice', '#A29BFE')
        ]:
            legend_elements.append(plt.Line2D([0], [0], color=color, lw=3, label=edge_type))
        
        ax.legend(handles=legend_elements, loc='upper right', title='Connection Types')
    
    def _calculate_optimized_layout(self):
        """Calculate layout optimized for showing traffic flows"""
        
        if self.G.number_of_nodes() == 0:
            return {}
        
        # Use force-directed layout with edge weights
        try:
            pos = nx.spring_layout(self.G, 
                                 weight='weight',
                                 k=2,
                                 iterations=50,
                                 seed=42)
        except:
            # Fallback to circular layout if spring layout fails
            pos = nx.circular_layout(self.G)
        
        return pos
    
    def _plot_protocol_analysis(self, ax):
        """Plot protocol usage and traffic analysis"""
        
        ax.set_title("Protocol Usage & Traffic Analysis", fontsize=14, fontweight='bold')
        
        # Count protocol usage
        protocol_traffic = defaultdict(float)
        protocol_counts = defaultdict(int)
        
        for _, _, data in self.G.edges(data=True):
            protocols = data.get('protocols', [])
            weight = data.get('weight', 0)
            
            for protocol in protocols:
                protocol_traffic[protocol] += weight
                protocol_counts[protocol] += 1
        
        if not protocol_traffic:
            ax.text(0.5, 0.5, 'No protocol data available', ha='center', va='center')
            return
        
        # Sort by traffic volume
        sorted_protocols = sorted(protocol_traffic.items(), key=lambda x: x[1], reverse=True)
        protocols = [p[0] for p in sorted_protocols[:10]]  # Top 10
        traffic_values = [p[1] for p in sorted_protocols[:10]]
        
        # Create bubble chart: x=usage count, y=avg traffic, size=total traffic
        x_values = [protocol_counts[p] for p in protocols]
        y_values = [protocol_traffic[p] / protocol_counts[p] for p in protocols]
        sizes = [(protocol_traffic[p] / max(protocol_traffic.values())) * 1000 for p in protocols]
        
        # Color based on protocol type
        colors = []
        for protocol in protocols:
            if protocol.startswith('IBMMQ'):
                colors.append('#FF6B6B')
            elif protocol in ['AMQP', 'KAFKA', 'JMS', 'MQTT']:
                colors.append('#96CEB4')
            elif protocol in ['HTTP', 'HTTPS']:
                colors.append('#4ECDC4')
            elif protocol in ['MYSQL', 'POSTGRESQL', 'ORACLE-TNS']:
                colors.append('#E55039')
            else:
                colors.append('#95A5A6')
        
        scatter = ax.scatter(x_values, y_values, s=sizes, c=colors, alpha=0.6, edgecolors='black')
        
        # Add protocol labels
        for i, protocol in enumerate(protocols):
            ax.annotate(protocol, (x_values[i], y_values[i]), 
                       xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax.set_xlabel('Connection Count')
        ax.set_ylabel('Average Bytes per Connection')
        ax.grid(alpha=0.3)
        
        # Add IBM MQ highlight
        ibm_mq_protocols = [p for p in protocols if p.startswith('IBMMQ')]
        if ibm_mq_protocols:
            ax.text(0.02, 0.98, f'IBM MQ Protocols: {len(ibm_mq_protocols)}', 
                   transform=ax.transAxes, va='top', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#FF6B6B', alpha=0.3))
    
    def _plot_composite_patterns(self, ax):
        """Plot distribution of composite patterns"""
        
        ax.set_title("Composite Architecture Patterns", fontsize=14, fontweight='bold')
        
        # Count pattern occurrences
        pattern_counts = Counter()
        multi_pattern_nodes = 0
        
        for node, patterns in self.composite_patterns.items():
            if len(patterns) > 1:
                multi_pattern_nodes += 1
            
            for pattern in patterns:
                pattern_counts[pattern] += 1
        
        if not pattern_counts:
            ax.text(0.5, 0.5, 'No patterns detected', ha='center', va='center')
            return
        
        # Create pie chart for pattern distribution
        patterns = list(pattern_counts.keys())
        counts = list(pattern_counts.values())
        
        # Color scheme
        colors = ['#FF6B6B', '#4ECDC4', '#96CEB4', '#45B7D1', '#F39C12', 
                 '#9B59B6', '#95A5A6', '#F1C40F', '#E67E22', '#BDC3C7']
        
        wedges, texts, autotexts = ax.pie(counts, labels=[p.replace('_', ' ').title() for p in patterns],
                                         colors=colors[:len(patterns)], autopct='%1.1f%%',
                                         startangle=90)
        
        # Add composite architecture statistics
        total_nodes = len(self.composite_patterns)
        composite_percentage = (multi_pattern_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        ax.text(-1.3, -1.3, f'Composite Architecture Nodes: {multi_pattern_nodes}/{total_nodes} ({composite_percentage:.1f}%)',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))
    
    def _plot_traffic_matrix(self, ax):
        """Plot traffic flow matrix showing heaviest connections"""
        
        ax.set_title("Top Traffic Flows", fontsize=14, fontweight='bold')
        
        # Get top traffic flows
        all_flows = []
        for src, destinations in self.traffic_flows.items():
            for dst, traffic in destinations.items():
                all_flows.append((src, dst, traffic))
        
        # Sort by traffic volume
        all_flows.sort(key=lambda x: x[2], reverse=True)
        top_flows = all_flows[:15]  # Top 15 flows
        
        if not top_flows:
            ax.text(0.5, 0.5, 'No traffic flows detected', ha='center', va='center')
            return
        
        # Create horizontal bar chart
        flow_labels = []
        traffic_values = []
        colors = []
        
        for src, dst, traffic in top_flows:
            # Truncate long names
            src_short = src[:12] + '..' if len(src) > 12 else src
            dst_short = dst[:12] + '..' if len(dst) > 12 else dst
            flow_labels.append(f'{src_short} → {dst_short}')
            traffic_values.append(traffic)
            
            # Color based on traffic volume
            max_traffic = max(traffic_values) if traffic_values else 1
            intensity = traffic / max_traffic
            colors.append(plt.cm.Reds(0.3 + intensity * 0.7))
        
        y_pos = range(len(flow_labels))
        bars = ax.barh(y_pos, traffic_values, color=colors)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(flow_labels, fontsize=8)
        ax.set_xlabel('Traffic Volume (bytes)')
        ax.grid(axis='x', alpha=0.3)
        
        # Add traffic volume labels
        for i, (bar, traffic) in enumerate(zip(bars, traffic_values)):
            if traffic > 1000000:
                label = f'{traffic/1000000:.1f}M'
            elif traffic > 1000:
                label = f'{traffic/1000:.1f}K'
            else:
                label = str(int(traffic))
            
            ax.text(bar.get_width() + max(traffic_values) * 0.01, bar.get_y() + bar.get_height()/2,
                   label, va='center', fontsize=8)

def main():
    parser = argparse.ArgumentParser(description="Create traffic-weighted network visualization")
    parser.add_argument("--input", "-i", required=True, help="Path to processed network data CSV")
    parser.add_argument("--output", "-o", help="Output path for visualization")
    parser.add_argument("--title", default="Traffic-Weighted Network Architecture", help="Visualization title")
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading network data from: {args.input}")
    df = pd.read_csv(args.input)
    
    if df.empty:
        print("No data found in input file")
        return
    
    print(f"Loaded {len(df)} network connections")
    
    # Create visualizer and build graph
    visualizer = TrafficWeightedVisualizer(df)
    visualizer.build_traffic_graph()
    
    # Generate visualization
    output_path = args.output or "traffic_weighted_network.png"
    visualizer.create_traffic_weighted_visualization(output_path, args.title)
    
    # Print summary statistics
    print(f"\nNetwork Statistics:")
    print(f"  Nodes: {visualizer.G.number_of_nodes()}")
    print(f"  Connections: {visualizer.G.number_of_edges()}")
    
    # Protocol summary
    protocol_counts = Counter()
    for _, _, data in visualizer.G.edges(data=True):
        for protocol in data.get('protocols', []):
            protocol_counts[protocol] += 1
    
    print(f"  Protocols: {len(protocol_counts)}")
    for protocol, count in protocol_counts.most_common(5):
        print(f"    {protocol}: {count} connections")
    
    # IBM MQ specific
    ibm_mq_connections = sum(1 for _, _, data in visualizer.G.edges(data=True) 
                           if any(p.startswith('IBMMQ') for p in data.get('protocols', [])))
    if ibm_mq_connections > 0:
        print(f"  IBM MQ Connections: {ibm_mq_connections}")
    
    # Composite patterns
    multi_pattern_count = sum(1 for patterns in visualizer.composite_patterns.values() if len(patterns) > 1)
    total_nodes = len(visualizer.composite_patterns)
    print(f"  Composite Architecture Nodes: {multi_pattern_count}/{total_nodes} ({multi_pattern_count/total_nodes*100:.1f}%)")

if __name__ == "__main__":
    main()