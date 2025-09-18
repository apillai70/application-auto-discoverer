#!/usr/bin/env python3
"""
Complete Composite Architecture Analysis Workflow

Integrates all components to analyze real-world composite architectures:
1. Processes raw network data
2. Detects composite architectural patterns (not single archetypes)
3. Includes IBM MQ protocol support
4. Creates traffic-weighted visualizations
5. Shows connectivity patterns between application components
"""

import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import sys
import io

import subprocess
import pandas as pd
from pathlib import Path
import argparse
import time
import shutil

# Fix Windows terminal encoding for Unicode characters
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_composite_analysis_workflow(input_file: str, output_dir: str = "composite_analysis_results"):
    """Run complete composite architecture analysis workflow"""
    
    workflow_start = time.time()
    
    # Extract app name from input file
    app_name = extract_app_name(input_file)  # You'll need this function
    
    results_dir = Path(output_dir)
    results_dir.mkdir(exist_ok=True)
    
    # Create centralized directory for final consolidated files
    central_dir = Path("complete_composite_analysis")
    central_dir.mkdir(exist_ok=True)
    
    print("🏗️  COMPOSITE ARCHITECTURE ANALYSIS WORKFLOW")
    print("=" * 60)
    
    # Step 1: Process raw data through enhanced generate_file.py
    step_start = time.time()
    print(f"\n📊 Step 1: Processing raw network data with enhanced generate_file.py...")
    
    try:
        # Run enhanced generate_file.py to process raw data
        result = subprocess.run([
            sys.executable, "data/generate_file.py",
            "--input", input_file,
            "--staging-dir", "data_staging",
            "--show-archetype-details",
            "--show-service-stats",
            "--dns", "socket",          # Keep DNS but use faster method
            "--threads", "100",         # Increase parallelization
            "--timeout", "0.5"          # Reduce per-lookup timeout
        ], capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        
        step_time = time.time() - step_start
        print(f"Raw data processing completed! ({step_time:.1f}s)")
        
        # Find the generated processed file in data_staging
        staging_dir = Path("data_staging")
        if not staging_dir.exists():
            print("❌ data_staging directory not found")
            return False
        
        # Look for the most recent processed file
        processed_files = list(staging_dir.glob("*_complete_*.csv"))
        if not processed_files:
            # Fallback to any CSV files in staging
            processed_files = list(staging_dir.glob("*.csv"))
        
        if not processed_files:
            print("❌ No processed files found in data_staging")
            return False
        
        # Get the most recent file
        input_file = max(processed_files, key=lambda p: p.stat().st_mtime)
        print(f"📄 Using processed file: {input_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Data processing failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    # Step 2: Analyze composite patterns
    step_start = time.time()
    print(f"Composite pattern analysis started! ({step_time:.1f}s)")
    
    try:

        result = subprocess.run([
            sys.executable, "data/composite_architecture_analyzer.py",
            "--input", str(input_file),
            "--output", str(results_dir / "composite_patterns.png"),
            "--show-summary"
        ], capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        
        step_time = time.time() - step_start
        print(f"Composite pattern analysis completed! ({step_time:.1f}s)")
        
        print("Key findings from composite analysis:")
        
        # Extract and display key findings from output
        output_lines = result.stdout.split('\n')
        in_summary = False
        for line in output_lines:
            if "COMPOSITE ARCHITECTURE ANALYSIS SUMMARY" in line:
                in_summary = True
            if in_summary and (line.startswith("  ") or ":" in line):
                print(f"    {line}")
                
    except subprocess.CalledProcessError as e:
        print(f"❌ Composite analysis failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    # Step 3: Create traffic-weighted visualization
    step_start = time.time()
    print(f"\n📊 Step 3: Creating traffic-weighted network visualization...")
    
    try:
        result = subprocess.run([
            sys.executable, "data/traffic_weighted_visualizer.py",
            "--input", str(input_file),
            "--output", str(results_dir / "traffic_weighted_network.png"),
            "--title", "Traffic-Weighted Composite Architecture"
        ], capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        
        step_time = time.time() - step_start
        print(f"Traffic-weighted visualization completed! ({step_time:.1f}s)")
        
        # Extract network statistics
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if "Network Statistics:" in line or line.startswith("  "):
                print(f"    {line}")
                
    except subprocess.CalledProcessError as e:
        print(f"❌ Traffic visualization failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
    
    # Step 4: Generate comprehensive report
    step_start = time.time()
    print(f"\n📋 Step 4: Generating comprehensive analysis report...")
    
    try:
        report_content = generate_composite_report(input_file, results_dir)
        
        report_file = results_dir / "composite_architecture_report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        step_time = time.time() - step_start
        print(f"Comprehensive report generated! ({step_time:.1f}s)")
        
    except Exception as e:
        print(f"⚠️  Report generation failed: {e}")
    
    # Step 5: Create connectivity matrix
    step_start = time.time()
    print(f"\n🔗 Step 5: Analyzing connectivity patterns...")
    
    try:
        connectivity_analysis = analyze_connectivity_patterns(input_file)
        
        connectivity_file = results_dir / "connectivity_analysis.txt"
        with open(connectivity_file, 'w') as f:
            f.write(connectivity_analysis)
        
        step_time = time.time() - step_start
        print(f"Connectivity analysis completed! ({step_time:.1f}s)")
        print("Key connectivity insights:")
        
        # Show first few lines of connectivity analysis
        lines = connectivity_analysis.split('\n')[:15]
        for line in lines:
            if line.strip():
                print(f"    {line}")
                
    except Exception as e:
        print(f"⚠️  Connectivity analysis failed: {e}")
    
    # Step 6: Generate animated flow diagram
    print(f"\nStep 6: Creating animated flow visualization...")
    step_start = time.time()

    try:
        from animated_flow_mapper import AnimatedFlowMapper
        
        mapper = AnimatedFlowMapper("complete_composite_analysis")
        mapper.create_app_flow_diagram(app_name, pd.read_csv(input_file))
        
        step_time = time.time() - step_start
        print(f"Animated flow diagram completed! ({step_time:.1f}s)")
    except Exception as e:
        print(f"Animated flow generation failed: {e}")
    
    # Summary
    consolidate_output_files(app_name, results_dir, central_dir, input_file)
    print(f"\n🎉 COMPOSITE ARCHITECTURE ANALYSIS COMPLETED!")
    print("=" * 60)
    print(f"📁 All results saved to: {results_dir}")
    print(f"📈 Generated files:")
    print(f"   • Composite patterns visualization: composite_patterns.png")
    print(f"   • Traffic-weighted network: traffic_weighted_network.png")
    print(f"   • Comprehensive report: composite_architecture_report.md")
    print(f"   • Connectivity analysis: connectivity_analysis.txt")
    total_time = time.time() - workflow_start
    print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    
    return True

def extract_app_name(filename):
    """Extract app name from App_Code_XXXXX.csv"""
    stem = Path(filename).stem
    if stem.startswith("App_Code_"):
        return stem.replace("App_Code_", "")
    return stem

def consolidate_output_files(app_name, temp_results_dir, central_dir, original_input):
    """Move and rename all output files to central directory with app prefix"""
    
    # Find the processed CSV file in data_staging
    staging_dir = Path("data_staging")
    processed_files = list(staging_dir.glob(f"*{app_name}*_normalized_*.csv"))
    if processed_files:
        latest_csv = max(processed_files, key=lambda p: p.stat().st_mtime)
        new_csv_name = f"{app_name}_normalized_data.csv"
        shutil.copy2(latest_csv, central_dir / new_csv_name)
    
    # Copy and rename analysis files
    file_mappings = {
        "composite_patterns.png": f"{app_name}_composite_patterns.png",
        "traffic_weighted_network.png": f"{app_name}_traffic_weighted_network.png", 
        "composite_architecture_report.md": f"{app_name}_composite_architecture_report.md",
        "connectivity_analysis.txt": f"{app_name}_connectivity_analysis.txt"
    }
    
    for old_name, new_name in file_mappings.items():
        old_path = temp_results_dir / old_name
        if old_path.exists():
            shutil.copy2(old_path, central_dir / new_name)
    
    print(f"All {app_name} files consolidated in: {central_dir}")
    
def generate_composite_report(input_file: str, results_dir: Path):
    """Generate comprehensive markdown report of composite architecture analysis"""
    
    # Load and analyze the data
    df = pd.read_csv(input_file)
    
    report_lines = [
        "# Composite Architecture Analysis Report",
        "",
        f"**Analysis Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source Data:** {input_file}",
        f"**Total Network Connections:** {len(df):,}",
        "",
        "## Executive Summary",
        "",
        "This report analyzes network traffic data to identify composite architectural patterns",
        "in enterprise applications. Unlike traditional single-archetype classification,",
        "this analysis recognizes that real-world applications typically combine multiple",
        "architectural patterns to meet complex business requirements.",
        "",
        "## Key Findings",
        ""
    ]
    
    # Application analysis
    applications = df['application'].unique()
    report_lines.extend([
        f"### Applications Analyzed: {len(applications)}",
        ""
    ])
    
    for app in applications:
        app_data = df[df['application'] == app]
        unique_protocols = app_data['protocol'].nunique()
        unique_destinations = app_data['destination_ip'].nunique() + app_data['destination_hostname'].nunique()
        total_traffic = (app_data['bytes_in'] + app_data['bytes_out']).sum()
        
        report_lines.extend([
            f"#### {app}",
            f"- **Connections:** {len(app_data):,}",
            f"- **Protocols:** {unique_protocols} different protocols",
            f"- **Components:** {unique_destinations} unique destinations",
            f"- **Total Traffic:** {total_traffic:,} bytes ({total_traffic/(1024*1024):.1f} MB)",
            ""
        ])
        
        # Protocol breakdown for this app
        protocol_counts = app_data['protocol'].value_counts().head(5)
        report_lines.append("**Top Protocols:**")
        for protocol, count in protocol_counts.items():
            percentage = (count / len(app_data)) * 100
            report_lines.append(f"- {protocol}: {count} connections ({percentage:.1f}%)")
        
        report_lines.append("")
    
    # Protocol analysis
    report_lines.extend([
        "## Protocol Distribution",
        "",
        "Analysis of network protocols reveals the communication patterns",
        "and technology stack composition across all applications.",
        ""
    ])
    
    protocol_counts = df['protocol'].value_counts()
    for protocol, count in protocol_counts.items():
        percentage = (count / len(df)) * 100
        report_lines.append(f"- **{protocol}:** {count:,} connections ({percentage:.1f}%)")
    
    # IBM MQ specific analysis
    ibm_mq_connections = df[df['protocol'].str.startswith('IBMMQ', na=False)]
    if not ibm_mq_connections.empty:
        report_lines.extend([
            "",
            "## IBM MQ Integration Analysis",
            "",
            f"**Total IBM MQ Connections:** {len(ibm_mq_connections):,}",
            f"**IBM MQ Traffic Volume:** {(ibm_mq_connections['bytes_in'] + ibm_mq_connections['bytes_out']).sum():,} bytes",
            ""
        ])
        
        ibm_mq_by_app = ibm_mq_connections['application'].value_counts()
        report_lines.append("**IBM MQ Usage by Application:**")
        for app, count in ibm_mq_by_app.items():
            report_lines.append(f"- {app}: {count} connections")
        
        # IBM MQ protocol variants
        mq_protocols = ibm_mq_connections['protocol'].value_counts()
        report_lines.extend(["", "**IBM MQ Protocol Variants:**"])
        for protocol, count in mq_protocols.items():
            report_lines.append(f"- {protocol}: {count} connections")
    
    # Traffic analysis
    report_lines.extend([
        "",
        "## Traffic Flow Analysis",
        "",
        "Analysis of traffic volumes and patterns to identify",
        "high-bandwidth connections and potential bottlenecks.",
        ""
    ])
    
    # Calculate traffic statistics
    total_bytes = (df['bytes_in'] + df['bytes_out']).sum()
    avg_bytes_per_connection = total_bytes / len(df) if len(df) > 0 else 0
    max_connection_bytes = (df['bytes_in'] + df['bytes_out']).max()
    
    report_lines.extend([
        f"- **Total Traffic Volume:** {total_bytes:,} bytes ({total_bytes/(1024*1024*1024):.2f} GB)",
        f"- **Average per Connection:** {avg_bytes_per_connection:,.0f} bytes",
        f"- **Largest Single Connection:** {max_connection_bytes:,} bytes",
        "",
        "## Composite Architecture Patterns",
        "",
        "Based on protocol combinations and traffic patterns, the following",
        "composite architectural patterns have been identified:",
        ""
    ])
    
    # Infer composite patterns for each application
    for app in applications:
        app_data = df[df['application'] == app]
        patterns = infer_composite_patterns(app_data)
        
        if patterns:
            report_lines.extend([
                f"### {app} - Composite Architecture",
                ""
            ])
            
            for pattern, evidence in patterns.items():
                report_lines.extend([
                    f"**{pattern}**",
                    f"- Evidence: {evidence}",
                    ""
                ])
    
    # Recommendations
    report_lines.extend([
        "## Recommendations",
        "",
        "Based on the composite architecture analysis:",
        "",
        "1. **IBM MQ Integration:** Strong messaging middleware presence indicates",
        "   event-driven architecture. Consider message flow optimization.",
        "",
        "2. **Protocol Diversity:** Multiple protocols per application suggest",
        "   complex integration requirements. Standardization opportunities exist.",
        "",
        "3. **Traffic Patterns:** Analyze high-traffic connections for potential",
        "   performance bottlenecks and scaling opportunities.",
        "",
        "4. **Composite Patterns:** Applications show sophisticated architectural",
        "   patterns combining web, messaging, and database technologies.",
        ""
    ])
    
    return "\n".join(report_lines)

def infer_composite_patterns(app_data):
    """Infer composite patterns from application data"""
    
    patterns = {}
    protocols = set(app_data['protocol'])
    
    # Web layer pattern
    if any(p in protocols for p in ['HTTP', 'HTTPS']):
        web_connections = len(app_data[app_data['protocol'].isin(['HTTP', 'HTTPS'])])
        patterns['Web Layer'] = f"{web_connections} HTTP/HTTPS connections"
    
    # Database layer pattern
    db_protocols = ['MYSQL', 'POSTGRESQL', 'ORACLE-TNS', 'TDS', 'MONGODB']
    if any(p in protocols for p in db_protocols):
        db_connections = len(app_data[app_data['protocol'].isin(db_protocols)])
        patterns['Database Layer'] = f"{db_connections} database connections"
    
    # Messaging layer pattern
    msg_protocols = ['IBMMQ', 'IBMMQ-SSL', 'KAFKA', 'AMQP', 'MQTT']
    if any(p in protocols for p in msg_protocols):
        msg_connections = len(app_data[app_data['protocol'].isin(msg_protocols)])
        patterns['Messaging Layer'] = f"{msg_connections} messaging connections"
    
    # Microservices pattern
    if 'GRPC' in protocols:
        grpc_connections = len(app_data[app_data['protocol'] == 'GRPC'])
        patterns['Microservices'] = f"{grpc_connections} gRPC connections"
    
    # Legacy integration pattern
    legacy_protocols = ['TELNET', 'RDP', 'TDS']
    if any(p in protocols for p in legacy_protocols):
        legacy_connections = len(app_data[app_data['protocol'].isin(legacy_protocols)])
        patterns['Legacy Integration'] = f"{legacy_connections} legacy protocol connections"
    
    return patterns

def analyze_connectivity_patterns(input_file: str):
    """Analyze connectivity patterns and generate detailed report"""
    
    df = pd.read_csv(input_file)
    
    analysis_lines = [
        "NETWORK CONNECTIVITY PATTERN ANALYSIS",
        "=" * 50,
        ""
    ]
    
    # Create connectivity matrix
    connectivity_matrix = {}
    
    for _, row in df.iterrows():
        src = row.get('source_ip') or row.get('source_hostname', 'unknown')
        dst = row.get('destination_ip') or row.get('destination_hostname', 'unknown')
        
        if src not in connectivity_matrix:
            connectivity_matrix[src] = {}
        
        if dst not in connectivity_matrix[src]:
            connectivity_matrix[src][dst] = {
                'connections': 0,
                'protocols': set(),
                'total_bytes': 0
            }
        
        connectivity_matrix[src][dst]['connections'] += 1
        connectivity_matrix[src][dst]['protocols'].add(row.get('protocol', ''))
        connectivity_matrix[src][dst]['total_bytes'] += (row.get('bytes_in', 0) + row.get('bytes_out', 0))
    
    # Find highest traffic connections
    high_traffic_connections = []
    
    for src, destinations in connectivity_matrix.items():
        for dst, data in destinations.items():
            high_traffic_connections.append((src, dst, data['total_bytes'], data['connections'], list(data['protocols'])))
    
    high_traffic_connections.sort(key=lambda x: x[2], reverse=True)
    
    analysis_lines.extend([
        f"TOP 15 TRAFFIC FLOWS:",
        "-" * 30
    ])
    
    for i, (src, dst, bytes_total, conn_count, protocols) in enumerate(high_traffic_connections[:15], 1):
        src_short = src[:20] + '..' if len(src) > 20 else src
        dst_short = dst[:20] + '..' if len(dst) > 20 else dst
        
        analysis_lines.extend([
            f"{i:2d}. {src_short} -> {dst_short}",
            f"    Traffic: {bytes_total:,} bytes ({conn_count} connections)",
            f"    Protocols: {', '.join(protocols)}",
            ""
        ])
    
    # Node degree analysis
    analysis_lines.extend([
        "NODE CONNECTIVITY ANALYSIS:",
        "-" * 30
    ])
    
    node_degrees = {}
    for src, destinations in connectivity_matrix.items():
        out_degree = len(destinations)
        node_degrees[src] = {'out_degree': out_degree, 'in_degree': 0}
    
    # Calculate in-degrees
    for src, destinations in connectivity_matrix.items():
        for dst in destinations.keys():
            if dst not in node_degrees:
                node_degrees[dst] = {'out_degree': 0, 'in_degree': 0}
            node_degrees[dst]['in_degree'] += 1
    
    # Find hub nodes (high total degree)
    hub_nodes = []
    for node, degrees in node_degrees.items():
        total_degree = degrees['out_degree'] + degrees['in_degree']
        hub_nodes.append((node, total_degree, degrees['out_degree'], degrees['in_degree']))
    
    hub_nodes.sort(key=lambda x: x[1], reverse=True)
    
    analysis_lines.extend([
        "TOP CONNECTIVITY HUBS:",
        ""
    ])
    
    for i, (node, total_degree, out_deg, in_deg) in enumerate(hub_nodes[:10], 1):
        node_short = node[:25] + '..' if len(node) > 25 else node
        analysis_lines.append(f"{i:2d}. {node_short} (Total: {total_degree}, Out: {out_deg}, In: {in_deg})")
    
    return "\n".join(analysis_lines)

def main():
    parser = argparse.ArgumentParser(description="Complete composite architecture analysis workflow")
    parser.add_argument("--input", "-i", default="network_data.csv", help="Path to network data file")
    parser.add_argument("--output-dir", "-o", default="composite_analysis_results", 
                       help="Output directory for all results")
    parser.add_argument("--generate-example", action="store_true",
                       help="Generate composite example data if input file doesn't exist")
    
    args = parser.parse_args()
    
    print(f"Starting composite architecture analysis...")
    print(f"Input file: {args.input}")
    print(f"Output directory: {args.output_dir}")
    
    if args.generate_example and not Path(args.input).exists():
        print(f"Generating example data since {args.input} doesn't exist...")
        args.input = "composite_architecture_with_ibmmq.csv"
    
    success = run_composite_analysis_workflow(args.input, args.output_dir)
    
    if success:
        print("\n🌟 Composite architecture analysis completed successfully!")
        print(f"\n📖 Key insights:")
        print(f"   • Real applications combine multiple architectural patterns")
        print(f"   • IBM MQ integration enables event-driven messaging")
        print(f"   • Traffic weighting reveals actual usage patterns")
        print(f"   • Connectivity analysis identifies integration hubs")
        return 0
    else:
        print("\n💥 Analysis workflow encountered errors. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())