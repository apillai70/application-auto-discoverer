#!/usr/bin/env python3
"""
Composite Architecture Analyzer

Detects and visualizes composite architectural patterns instead of forcing applications
into single archetype bins. Real applications often combine multiple patterns:
- 3-Tier + Event-Driven (web app with message queues)
- Microservices + Database-Centric (microservices with shared databases)  
- SOA + Client-Server (service bus with legacy thick clients)
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from collections import defaultdict, Counter
import math
from pathlib import Path
import argparse

# Enhanced protocol definitions including IBM MQ
ENHANCED_PROTOCOLS = {
    'HTTP': 80, 'HTTPS': 443, 'HTTP-ALT': 8080,
    'MYSQL': 3306, 'POSTGRESQL': 5432, 'ORACLE-TNS': 1521, 'TDS': 1433,
    'MONGODB': 27017, 'REDIS': 6379,
    'IBMMQ': 1414, 'IBMMQ-SSL': 1415, 'AMQP': 5672, 'KAFKA': 9092, 'JMS': 61616,
    'MQTT': 1883, 'MQTT-SSL': 8883, 'NATS': 4222,
    'GRPC': 50051, 'RDP': 3389, 'SSH': 22, 'TELNET': 23,
    'LDAP': 389, 'KERBEROS': 88, 'DNS': 53, 'SNMP': 161
}

# Architectural pattern indicators
PATTERN_INDICATORS = {
    'web_tier': {
        'protocols': ['HTTP', 'HTTPS'],
        'ports': [80, 443, 8080],
        'characteristics': ['public_facing', 'stateless'],
        'weight': 1.0
    },
    'api_gateway': {
        'protocols': ['HTTP', 'HTTPS'],
        'ports': [8080, 8443, 9090],
        'characteristics': ['aggregation_point', 'high_fanout'],
        'weight': 1.2
    },
    'app_services': {
        'protocols': ['HTTP', 'GRPC'],
        'ports': list(range(3000, 3100)) + [8080, 9090],
        'characteristics': ['business_logic', 'east_west_traffic'],
        'weight': 1.0
    },
    'database_layer': {
        'protocols': ['MYSQL', 'POSTGRESQL', 'ORACLE-TNS', 'TDS', 'MONGODB'],
        'ports': [3306, 5432, 1521, 1433, 27017],
        'characteristics': ['data_persistence', 'high_read_write'],
        'weight': 1.5
    },
    'messaging_layer': {
        'protocols': ['IBMMQ', 'IBMMQ-SSL', 'AMQP', 'KAFKA', 'JMS', 'MQTT'],
        'ports': [1414, 1415, 5672, 9092, 61616, 1883],
        'characteristics': ['async_communication', 'pub_sub'],
        'weight': 1.3
    },
    'cache_layer': {
        'protocols': ['REDIS'],
        'ports': [6379, 11211],
        'characteristics': ['performance_optimization', 'temporary_storage'],
        'weight': 0.8
    },
    'legacy_systems': {
        'protocols': ['TDS', 'RDP', 'TELNET'],
        'ports': [1433, 3389, 23],
        'characteristics': ['thick_client', 'persistent_connection'],
        'weight': 1.1
    },
    'auth_services': {
        'protocols': ['LDAP', 'KERBEROS'],
        'ports': [389, 636, 88],
        'characteristics': ['security', 'centralized_auth'],
        'weight': 0.9
    },
    'microservices_mesh': {
        'protocols': ['GRPC', 'HTTP'],
        'ports': [50051] + list(range(3000, 3050)),
        'characteristics': ['service_mesh', 'container_orchestration'],
        'weight': 1.4
    }
}

class CompositeArchitectureAnalyzer:
    def __init__(self, df):
        self.df = df
        self.application_patterns = defaultdict(lambda: defaultdict(float))
        self.application_components = defaultdict(list)
        self.traffic_flows = defaultdict(list)
        
    def analyze_application_patterns(self):
        """Analyze each application to detect composite architectural patterns"""
        
        print("Analyzing composite architectural patterns...")
        
        for app_name in self.df['application'].unique():
            app_data = self.df[self.df['application'] == app_name]
            
            print(f"\nAnalyzing {app_name} ({len(app_data)} connections):")
            
            # Detect patterns within this application
            pattern_scores = self._detect_patterns_in_app(app_data)
            
            # Store significant patterns (above threshold)
            significant_patterns = {pattern: score for pattern, score in pattern_scores.items() if score > 0.3}
            
            if significant_patterns:
                self.application_patterns[app_name] = significant_patterns
                print(f"  Detected composite patterns:")
                for pattern, score in sorted(significant_patterns.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {pattern.replace('_', ' ').title()}: {score:.2f}")
            else:
                print(f"  No clear patterns detected (may be simple/monolithic)")
                self.application_patterns[app_name] = {'simple_app': 1.0}
            
            # Analyze components
            components = self._extract_application_components(app_data)
            self.application_components[app_name] = components
            
            if len(components) > 1:
                print(f"  Components identified: {len(components)}")
                for comp in components[:3]:  # Show first 3
                    print(f"    - {comp['node']} ({comp['type']}) - {comp['protocols']}")
                if len(components) > 3:
                    print(f"    ... and {len(components) - 3} more")
    
    def _detect_patterns_in_app(self, app_data):
        """Detect architectural patterns within a single application"""
        
        pattern_scores = defaultdict(float)
        
        # Analyze traffic patterns and protocols
        protocol_counts = Counter(app_data['protocol'])
        port_counts = Counter(app_data['port'])
        
        # Calculate traffic characteristics
        total_connections = len(app_data)
        unique_sources = app_data['source_ip'].nunique() + app_data['source_hostname'].nunique()
        unique_destinations = app_data['destination_ip'].nunique() + app_data['destination_hostname'].nunique()
        
        avg_bytes_in = app_data['bytes_in'].mean()
        avg_bytes_out = app_data['bytes_out'].mean()
        
        # Score each pattern
        for pattern_name, pattern_config in PATTERN_INDICATORS.items():
            score = 0.0
            
            # Protocol matching
            protocol_matches = sum(protocol_counts.get(proto, 0) for proto in pattern_config['protocols'])
            if protocol_matches > 0:
                score += (protocol_matches / total_connections) * pattern_config['weight']
            
            # Port matching
            port_matches = sum(port_counts.get(port, 0) for port in pattern_config['ports'])
            if port_matches > 0:
                score += (port_matches / total_connections) * pattern_config['weight'] * 0.5
            
            # Characteristic-based scoring
            characteristics = pattern_config.get('characteristics', [])
            
            if 'high_fanout' in characteristics and unique_destinations > 5:
                score += 0.3
            
            if 'aggregation_point' in characteristics and unique_sources > unique_destinations * 2:
                score += 0.2
                
            if 'east_west_traffic' in characteristics:
                # Check for internal communication (same subnet)
                internal_traffic = self._count_internal_traffic(app_data)
                if internal_traffic > total_connections * 0.3:
                    score += 0.4
            
            if 'async_communication' in characteristics:
                # Messaging patterns often have lower bytes_in than bytes_out
                if avg_bytes_out > avg_bytes_in * 0.5 and protocol_matches > 0:
                    score += 0.3
            
            if 'high_read_write' in characteristics:
                # Database patterns have high byte ratios
                if (avg_bytes_in + avg_bytes_out) > 5000 and protocol_matches > 0:
                    score += 0.4
            
            if 'pub_sub' in characteristics:
                # Look for many-to-many communication patterns
                if unique_sources > 2 and unique_destinations > 2 and protocol_matches > 0:
                    score += 0.3
            
            pattern_scores[pattern_name] = min(score, 2.0)  # Cap at 2.0
        
        return pattern_scores
    
    def _count_internal_traffic(self, app_data):
        """Count connections that appear to be internal (same subnet)"""
        internal_count = 0
        
        for _, row in app_data.iterrows():
            src_ip = row.get('source_ip', '')
            dest_ip = row.get('destination_ip', '')
            
            if src_ip and dest_ip and '.' in src_ip and '.' in dest_ip:
                try:
                    src_parts = src_ip.split('.')[:3]
                    dest_parts = dest_ip.split('.')[:3]
                    if src_parts == dest_parts:
                        internal_count += 1
                except:
                    pass
        
        return internal_count
    
    def _extract_application_components(self, app_data):
        """Extract distinct components within an application"""
        
        components = []
        
        # Group by destination to identify components
        dest_groups = app_data.groupby(['destination_ip', 'destination_hostname'])
        
        for (dest_ip, dest_hostname), group in dest_groups:
            node_id = dest_ip or dest_hostname or 'unknown'
            
            if node_id == 'unknown':
                continue
            
            # Analyze this component
            protocols = list(group['protocol'].unique())
            ports = list(group['port'].unique())
            service_types = list(group.get('service_type', ['unknown']).unique())
            
            # Infer component type based on protocols/ports
            component_type = self._infer_component_type(protocols, ports)
            
            # Calculate traffic stats
            total_bytes = (group['bytes_in'] + group['bytes_out']).sum()
            connection_count = len(group)
            
            components.append({
                'node': node_id,
                'type': component_type,
                'protocols': protocols,
                'ports': ports,
                'service_types': service_types,
                'total_traffic': total_bytes,
                'connections': connection_count
            })
        
        return sorted(components, key=lambda x: x['total_traffic'], reverse=True)
    
    def _infer_component_type(self, protocols, ports):
        """Infer component type from protocols and ports"""
        
        protocol_set = set(protocols)
        port_set = set(ports)
        
        # Check against pattern indicators
        for pattern_name, config in PATTERN_INDICATORS.items():
            protocol_overlap = protocol_set.intersection(set(config['protocols']))
            port_overlap = port_set.intersection(set(config['ports']))
            
            if protocol_overlap or port_overlap:
                return pattern_name.replace('_', ' ').title()
        
        return 'Unknown Component'
    
    def create_composite_visualization(self, output_path=None):
        """Create visualization showing composite architecture patterns"""
        
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle('Composite Architecture Analysis', fontsize=16, fontweight='bold')
        
        # Top-left: Pattern distribution across applications
        self._plot_pattern_distribution(axes[0, 0])
        
        # Top-right: Application complexity analysis  
        self._plot_complexity_analysis(axes[0, 1])
        
        # Bottom-left: Component interconnections
        self._plot_component_network(axes[1, 0])
        
        # Bottom-right: Pattern combinations
        self._plot_pattern_combinations(axes[1, 1])
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Composite architecture visualization saved to: {output_path}")
        else:
            plt.show()
    
    def _plot_pattern_distribution(self, ax):
        """Plot distribution of patterns across applications"""
        
        # Collect all patterns and their frequencies
        pattern_frequencies = defaultdict(int)
        
        for app_patterns in self.application_patterns.values():
            for pattern in app_patterns.keys():
                pattern_frequencies[pattern] += 1
        
        if not pattern_frequencies:
            ax.text(0.5, 0.5, 'No patterns detected', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Pattern Distribution')
            return
        
        patterns = list(pattern_frequencies.keys())
        frequencies = list(pattern_frequencies.values())
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(patterns)), frequencies)
        ax.set_yticks(range(len(patterns)))
        ax.set_yticklabels([p.replace('_', ' ').title() for p in patterns])
        ax.set_xlabel('Number of Applications')
        ax.set_title('Architectural Patterns Frequency')
        
        # Color bars based on frequency
        max_freq = max(frequencies) if frequencies else 1
        for i, bar in enumerate(bars):
            intensity = frequencies[i] / max_freq
            bar.set_color(plt.cm.viridis(intensity))
        
        ax.grid(axis='x', alpha=0.3)
    
    def _plot_complexity_analysis(self, ax):
        """Plot application complexity based on number of patterns"""
        
        app_names = []
        pattern_counts = []
        max_pattern_scores = []
        
        for app_name, patterns in self.application_patterns.items():
            app_names.append(app_name[:15] + '...' if len(app_name) > 15 else app_name)
            pattern_counts.append(len(patterns))
            max_pattern_scores.append(max(patterns.values()) if patterns else 0)
        
        if not pattern_counts:
            ax.text(0.5, 0.5, 'No applications analyzed', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Application Complexity')
            return
        
        # Scatter plot: x=number of patterns, y=max pattern score, size=proportional to complexity
        sizes = [count * score * 100 for count, score in zip(pattern_counts, max_pattern_scores)]
        
        scatter = ax.scatter(pattern_counts, max_pattern_scores, s=sizes, alpha=0.6, c=pattern_counts, cmap='plasma')
        
        ax.set_xlabel('Number of Architectural Patterns')
        ax.set_ylabel('Strongest Pattern Score')
        ax.set_title('Application Architecture Complexity')
        
        # Add application labels
        for i, name in enumerate(app_names):
            ax.annotate(name, (pattern_counts[i], max_pattern_scores[i]), 
                       xytext=(5, 5), textcoords='offset points', fontsize=8, alpha=0.8)
        
        plt.colorbar(scatter, ax=ax, label='Pattern Count')
        ax.grid(alpha=0.3)
    
    def _plot_component_network(self, ax):
        """Plot network of components and their relationships"""
        
        # Create a simplified network graph
        G = nx.Graph()
        
        # Add nodes for each application with their dominant pattern
        app_positions = {}
        
        for i, (app_name, patterns) in enumerate(self.application_patterns.items()):
            if not patterns:
                continue
                
            # Get dominant pattern
            dominant_pattern = max(patterns.keys(), key=lambda k: patterns[k])
            
            # Add node
            G.add_node(app_name, pattern=dominant_pattern, 
                      pattern_score=patterns[dominant_pattern],
                      component_count=len(self.application_components.get(app_name, [])))
        
        # Position nodes in a circle
        if len(G.nodes()) > 0:
            pos = nx.circular_layout(G)
        else:
            pos = {}
        
        # Draw nodes with colors based on dominant pattern
        pattern_colors = {
            'web_tier': '#4ECDC4',
            'database_layer': '#FF6B6B', 
            'messaging_layer': '#96CEB4',
            'app_services': '#45B7D1',
            'microservices_mesh': '#74B9FF',
            'legacy_systems': '#FFEAA7',
            'simple_app': '#DDA0DD'
        }
        
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            pattern = G.nodes[node].get('pattern', 'simple_app')
            node_colors.append(pattern_colors.get(pattern, '#CCCCCC'))
            
            # Size based on component count
            component_count = G.nodes[node].get('component_count', 1)
            node_sizes.append(300 + component_count * 100)
        
        if pos:
            nx.draw_networkx_nodes(G, pos, ax=ax, 
                                 node_color=node_colors, 
                                 node_size=node_sizes,
                                 alpha=0.8)
            
            nx.draw_networkx_labels(G, pos, ax=ax,
                                  labels={node: node[:8] + '..' if len(node) > 8 else node for node in G.nodes()},
                                  font_size=8)
        
        ax.set_title('Application Component Network')
        ax.axis('off')
        
        # Add legend
        legend_elements = []
        for pattern, color in pattern_colors.items():
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=10,
                                            label=pattern.replace('_', ' ').title()))
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.3, 1))
    
    def _plot_pattern_combinations(self, ax):
        """Plot common pattern combinations"""
        
        # Find applications with multiple patterns
        multi_pattern_apps = {app: patterns for app, patterns in self.application_patterns.items() 
                            if len(patterns) > 1}
        
        if not multi_pattern_apps:
            ax.text(0.5, 0.5, 'No composite patterns found\n(Applications have single patterns)', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Pattern Combinations')
            return
        
        # Count pattern combinations
        combination_counts = Counter()
        
        for app, patterns in multi_pattern_apps.items():
            # Sort patterns by score to get consistent combinations
            sorted_patterns = sorted(patterns.keys(), key=lambda x: patterns[x], reverse=True)
            if len(sorted_patterns) >= 2:
                combo = tuple(sorted_patterns[:2])  # Top 2 patterns
                combination_counts[combo] += 1
        
        if not combination_counts:
            ax.text(0.5, 0.5, 'No frequent pattern combinations', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Pattern Combinations')
            return
        
        # Create visualization of combinations
        combos = list(combination_counts.keys())
        counts = list(combination_counts.values())
        
        # Create labels
        combo_labels = []
        for combo in combos:
            label = ' + '.join([p.replace('_', ' ').title() for p in combo])
            combo_labels.append(label)
        
        # Horizontal bar chart
        y_pos = range(len(combo_labels))
        bars = ax.barh(y_pos, counts)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(combo_labels)
        ax.set_xlabel('Number of Applications')
        ax.set_title('Common Composite Patterns')
        
        # Color bars
        for i, bar in enumerate(bars):
            bar.set_color(plt.cm.Set3(i % 12))
        
        ax.grid(axis='x', alpha=0.3)
    
    def generate_composite_summary(self):
        """Generate detailed summary of composite architecture analysis"""
        
        summary_lines = [
            "COMPOSITE ARCHITECTURE ANALYSIS SUMMARY",
            "=" * 50,
            ""
        ]
        
        # Application breakdown
        summary_lines.append(f"ANALYZED APPLICATIONS: {len(self.application_patterns)}")
        summary_lines.append("-" * 30)
        
        simple_apps = 0
        composite_apps = 0
        
        for app_name, patterns in self.application_patterns.items():
            if len(patterns) == 1 and 'simple_app' in patterns:
                simple_apps += 1
            elif len(patterns) > 1:
                composite_apps += 1
                summary_lines.append(f"\n{app_name}:")
                for pattern, score in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
                    summary_lines.append(f"  - {pattern.replace('_', ' ').title()}: {score:.2f}")
                    
                # Add component info
                components = self.application_components.get(app_name, [])
                if len(components) > 1:
                    summary_lines.append(f"  Components: {len(components)}")
        
        summary_lines.append(f"\nSIMPLE APPLICATIONS: {simple_apps}")
        summary_lines.append(f"COMPOSITE APPLICATIONS: {composite_apps}")
        
        if composite_apps > 0:
            summary_lines.append(f"\nCOMPOSITE ARCHITECTURE PERCENTAGE: {(composite_apps / len(self.application_patterns)) * 100:.1f}%")
        
        # Pattern frequency
        pattern_freq = Counter()
        for patterns in self.application_patterns.values():
            for pattern in patterns.keys():
                pattern_freq[pattern] += 1
        
        summary_lines.append(f"\nMOST COMMON PATTERNS:")
        summary_lines.append("-" * 20)
        for pattern, count in pattern_freq.most_common():
            summary_lines.append(f"{pattern.replace('_', ' ').title()}: {count} applications")
        
        return "\n".join(summary_lines)

def main():
    parser = argparse.ArgumentParser(description="Analyze composite architectural patterns")
    parser.add_argument("--input", "-i", required=True, help="Path to processed network data CSV")
    parser.add_argument("--output", "-o", help="Output path for visualization")
    parser.add_argument("--show-summary", action="store_true", help="Show detailed analysis summary")
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading network data from: {args.input}")
    df = pd.read_csv(args.input)
    
    if df.empty:
        print("No data found in input file")
        return
    
    print(f"Loaded {len(df)} network connections")
    print(f"Applications found: {', '.join(df['application'].unique())}")
    
    # Analyze composite patterns
    analyzer = CompositeArchitectureAnalyzer(df)
    analyzer.analyze_application_patterns()
    
    # Generate visualization
    output_path = args.output or "composite_architecture_analysis.png"
    analyzer.create_composite_visualization(output_path)
    
    # Show summary if requested
    if args.show_summary:
        summary = analyzer.generate_composite_summary()
        print("\n" + summary)

if __name__ == "__main__":
    main()