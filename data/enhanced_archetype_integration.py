#!/usr/bin/env python3
"""
Enhanced Archetype Integration with YAML Templates

Integrates the comprehensive archetype templates from archetype_templates.yaml
into the service classification system for more accurate architectural pattern detection.
"""

from typing import Dict, List, Tuple, Set, Optional
import re
import pandas as pd

# Comprehensive archetype definitions based on archetype_templates.yaml
ARCHETYPE_TEMPLATES = {
    'Monolithic': {
        'description': 'Single-tier application where UI, business logic, and data access are tightly integrated',
        'typical_ports': [3306, 8080],
        'indicators': ['direct DB access', 'high port concentration', 'no service boundary', 'single process'],
        'traffic_pattern': 'inbound only',
        'expected_hosts': ['Application server', 'Local DB'],
        'priority': 7,
        'protocols': ['HTTP', 'MYSQL', 'SQL'],
        'service_patterns': ['single_app_with_db', 'consolidated_services']
    },
    
    '3-Tier': {
        'description': 'Standard enterprise structure with separate UI, API, and database components',
        'typical_ports': [80, 443, 3306, 5432],
        'indicators': ['distinct UI/API/DB tiers', 'north-south traffic', 'port layering', 'stateful backend'],
        'traffic_pattern': 'north-south',
        'expected_hosts': ['App Server', 'DB Server', 'Web Server'],
        'priority': 9,
        'protocols': ['HTTP', 'HTTPS', 'MYSQL', 'POSTGRESQL'],
        'service_patterns': ['web_to_app_to_db', 'tiered_architecture']
    },
    
    'Microservices': {
        'description': 'Application composed of independent services communicating via REST/gRPC',
        'typical_ports': list(range(3000, 3100)) + [8080, 9090, 50051],
        'indicators': ['API gateway', 'K8s/docker', 'internal east-west traffic', 'many services'],
        'traffic_pattern': 'east-west',
        'expected_hosts': ['Containers', 'Service nodes', 'Sidecars'],
        'priority': 10,
        'protocols': ['HTTP', 'GRPC', 'HTTP-ALT'],
        'service_patterns': ['container_services', 'service_mesh', 'api_gateway']
    },
    
    'Event-Driven': {
        'description': 'Decoupled services communicating through message queues or pub/sub systems',
        'typical_ports': [5672, 9092, 1883, 15672, 61616],
        'indicators': ['Kafka/RabbitMQ', 'asynchronous traffic', 'low direct coupling', 'non-HTTP ports'],
        'traffic_pattern': 'pub-sub / async',
        'expected_hosts': ['Publisher', 'Queue/Broker', 'Subscriber'],
        'priority': 9,
        'protocols': ['AMQP', 'MQTT'],
        'service_patterns': ['message_broker', 'pub_sub', 'async_processing']
    },
    
    'SOA': {
        'description': 'Enterprise services exposed via ESB, typically with SOAP/XML or legacy protocols',
        'typical_ports': [8080, 8443, 80, 443],
        'indicators': ['ESB', 'SOAP', 'WSDL', 'XML over HTTP', 'service registry'],
        'traffic_pattern': 'service bus mediated',
        'expected_hosts': ['ESB Gateway', 'Legacy App', 'Service Node'],
        'priority': 8,
        'protocols': ['HTTP', 'HTTPS', 'SOAP'],
        'service_patterns': ['service_bus', 'esb_gateway', 'legacy_integration']
    },
    
    'SOA with Message Broker': {
        'description': 'SOA variation where services communicate primarily through a central message broker',
        'typical_ports': [5672, 9092, 61616, 8161],
        'indicators': ['ActiveMQ/WebSphere MQ', 'JMS/AMQP protocols', 'message queues for service requests'],
        'traffic_pattern': 'message broker mediated',
        'expected_hosts': ['Message Broker', 'Service Nodes'],
        'priority': 8,
        'protocols': ['AMQP', 'JMS'],
        'service_patterns': ['central_broker', 'message_mediation']
    },
    
    'Serverless': {
        'description': 'Stateless compute units triggered by events, typically on cloud providers',
        'typical_ports': [443, 80],
        'indicators': ['API Gateway', 'AWS Lambda', 'Azure Functions', 'ephemeral endpoints'],
        'traffic_pattern': 'on-demand stateless',
        'expected_hosts': ['API Gateway', 'Lambda/Function endpoints'],
        'priority': 8,
        'protocols': ['HTTPS', 'HTTP'],
        'service_patterns': ['function_as_service', 'event_triggered', 'stateless_compute']
    },
    
    'Client-Server': {
        'description': 'Traditional fat client connecting directly to backend services or databases',
        'typical_ports': [1433, 3389, 5432, 3306],
        'indicators': ['MS SQL', 'RDP/Citrix', 'desktop installs', 'thick client'],
        'traffic_pattern': 'persistent session',
        'expected_hosts': ['Client PC', 'SQL Server'],
        'priority': 7,
        'protocols': ['TDS', 'SQL', 'RDP', 'MYSQL'],
        'service_patterns': ['thick_client', 'direct_db_access', 'desktop_app']
    },
    
    'Edge+Cloud Hybrid': {
        'description': 'Applications split between local edge devices and cloud-based control/analytics',
        'typical_ports': [443, 1883, 8883, 8080],
        'indicators': ['IoT', 'cloud-REST targets', 'gateway patterns', 'remote sensor endpoints'],
        'traffic_pattern': 'device to cloud',
        'expected_hosts': ['Cloud API', 'Edge Gateway', 'Sensor'],
        'priority': 8,
        'protocols': ['HTTPS', 'MQTT', 'HTTP'],
        'service_patterns': ['iot_gateway', 'edge_computing', 'cloud_sync']
    },
    
    'ETL/Data Pipeline': {
        'description': 'Batch or stream-based data processing flows for BI or analytics systems',
        'typical_ports': [21, 8020, 9000, 5432, 3306],
        'indicators': ['Airflow', 'Spark', 'batch ports', 'cron traffic', 'data lake/DWH targets'],
        'traffic_pattern': 'batch or streaming',
        'expected_hosts': ['Data lake', 'ETL engine', 'Warehouse'],
        'priority': 7,
        'protocols': ['FTP', 'HDFS', 'SQL'],
        'service_patterns': ['batch_processing', 'data_pipeline', 'etl_workflow']
    },
    
    'Web + API Headless': {
        'description': 'Decoupled frontend (SPA) and backend (REST API) layers deployed independently',
        'typical_ports': [80, 443, 8080, 3000],
        'indicators': ['CORS', 'OAuth flows', 'REST API', 'React/Vue', 'frontend-backend split'],
        'traffic_pattern': 'frontend-backend async',
        'expected_hosts': ['API Server', 'Browser', 'OAuth Provider'],
        'priority': 9,
        'protocols': ['HTTP', 'HTTPS'],
        'service_patterns': ['spa_frontend', 'rest_api', 'oauth_auth']
    },
    
    'Cloud-Native': {
        'description': 'Applications built specifically for cloud environments with containerization and managed services',
        'typical_ports': [8080, 9090, 443, 50051],
        'indicators': ['Kubernetes/EKS/GKE', 'container registries', 'service meshes', 'automated scaling'],
        'traffic_pattern': 'dynamic scaling',
        'expected_hosts': ['Containers', 'Managed Services', 'Load Balancers'],
        'priority': 10,
        'protocols': ['HTTP', 'GRPC', 'HTTPS'],
        'service_patterns': ['kubernetes', 'container_orchestration', 'cloud_services']
    },
    
    'N-Tier Architecture': {
        'description': 'Multi-layered architecture with more than three distinct layers',
        'typical_ports': [80, 443, 8080, 3306, 5432, 6379],
        'indicators': ['DMZ', 'application server tier', 'load balancers between tiers', 'distinct network subnets'],
        'traffic_pattern': 'multi-tier',
        'expected_hosts': ['Load Balancers', 'Web Tier', 'App Tier', 'Cache Tier', 'Data Tier'],
        'priority': 8,
        'protocols': ['HTTP', 'HTTPS', 'SQL', 'REDIS'],
        'service_patterns': ['multi_tier', 'load_balanced', 'tiered_services']
    },
    
    'Database-Centric': {
        'description': 'Applications primarily built around database stored procedures and triggers',
        'typical_ports': [3306, 5432, 1521, 1433, 27017],
        'indicators': ['stored procedures/functions', 'database as primary logic layer', 'triggers for business rules'],
        'traffic_pattern': 'database focused',
        'expected_hosts': ['Database Servers', 'Database Clients'],
        'priority': 9,
        'protocols': ['MYSQL', 'POSTGRESQL', 'ORACLE-TNS', 'TDS', 'MONGODB'],
        'service_patterns': ['db_centric', 'stored_procedures', 'database_logic']
    },
    
    'API-Centric (General)': {
        'description': 'Applications primarily designed to expose or consume functionality via structured APIs',
        'typical_ports': [8080, 8443, 443, 9090, 3000],
        'indicators': ['RESTful endpoints', 'GraphQL queries', 'OpenAPI/Swagger', 'gRPC services'],
        'traffic_pattern': 'api focused',
        'expected_hosts': ['API Gateways', 'API Servers', 'API Consumers'],
        'priority': 9,
        'protocols': ['HTTP', 'HTTPS', 'GRPC'],
        'service_patterns': ['rest_api', 'graphql', 'api_gateway']
    },
    
    'Host-Terminal': {
        'description': 'Central host computer serving terminals with all processing on the host',
        'typical_ports': [23, 3270, 5250, 22],
        'indicators': ['character-based interfaces', 'text-based terminals', 'host-based processing only'],
        'traffic_pattern': 'terminal based',
        'expected_hosts': ['Host System', 'Terminals'],
        'priority': 6,
        'protocols': ['TELNET', 'SSH', 'TN3270'],
        'service_patterns': ['terminal_access', 'mainframe', 'character_ui']
    },
    
    'AI/ML Application': {
        'description': 'Systems that apply machine learning models for prediction, classification, or decision-making',
        'typical_ports': [8080, 5000, 8888, 6006],
        'indicators': ['TensorFlow/PyTorch', 'inference endpoints', 'model training pipelines', 'GPU usage'],
        'traffic_pattern': 'model inference',
        'expected_hosts': ['ML Models', 'Training Clusters', 'Inference Servers'],
        'priority': 8,
        'protocols': ['HTTP', 'GRPC'],
        'service_patterns': ['ml_inference', 'model_training', 'ai_pipeline']
    },
    
    'Automation System': {
        'description': 'Systems designed to automate tasks, processes, or workflows without human intervention',
        'typical_ports': [8080, 443, 22, 135],
        'indicators': ['RPA tools', 'event-triggered automation', 'scheduled tasks', 'API orchestration'],
        'traffic_pattern': 'automated workflows',
        'expected_hosts': ['Automation Controllers', 'Target Systems'],
        'priority': 7,
        'protocols': ['HTTP', 'HTTPS', 'SSH', 'MSRPC'],
        'service_patterns': ['rpa', 'workflow_automation', 'task_scheduling']
    }
}

def analyze_service_patterns(df_row_data: List[Dict]) -> Dict[str, int]:
    """Analyze patterns across multiple service connections to identify architectural patterns"""
    
    pattern_scores = {}
    
    # Extract key metrics
    protocols = set()
    ports = set()
    hosts = set()
    total_connections = len(df_row_data)
    
    for row in df_row_data:
        protocols.add(row.get('protocol', '').upper())
        if row.get('port'):
            ports.add(int(row.get('port', 0)) if str(row.get('port', '')).isdigit() else 0)
        hosts.add(row.get('destination_ip') or row.get('destination_hostname', ''))
        hosts.add(row.get('source_ip') or row.get('source_hostname', ''))
    
    # Remove empty/zero values
    ports = {p for p in ports if p > 0}
    hosts = {h for h in hosts if h and h != 'unknown'}
    
    # Pattern detection logic
    for archetype, config in ARCHETYPE_TEMPLATES.items():
        score = 0
        
        # Protocol matches
        archetype_protocols = set(config.get('protocols', []))
        protocol_matches = protocols & archetype_protocols
        if protocol_matches:
            score += len(protocol_matches) * 5
        
        # Port matches
        archetype_ports = set(config.get('typical_ports', []))
        port_matches = ports & archetype_ports
        if port_matches:
            score += len(port_matches) * 3
        
        # Service pattern indicators
        service_patterns = config.get('service_patterns', [])
        
        # Microservices detection
        if 'container_services' in service_patterns or 'service_mesh' in service_patterns:
            # High port diversity in 3000+ range
            high_ports = [p for p in ports if 3000 <= p <= 3100]
            if len(high_ports) >= 3:
                score += 15
            
            # gRPC presence
            if 'GRPC' in protocols or 50051 in ports:
                score += 10
        
        # Database-centric detection
        if 'db_centric' in service_patterns:
            db_protocols = {'MYSQL', 'POSTGRESQL', 'TDS', 'ORACLE-TNS', 'MONGODB'}
            if protocols & db_protocols:
                score += 12
                
                # Multiple DB connections suggest centralized DB logic
                db_ports = {3306, 5432, 1433, 1521, 27017}
                if len(ports & db_ports) >= 2:
                    score += 8
        
        # Event-driven detection
        if 'message_broker' in service_patterns or 'pub_sub' in service_patterns:
            messaging_protocols = {'AMQP', 'MQTT'}
            messaging_ports = {5672, 9092, 1883, 15672, 61616}
            
            if protocols & messaging_protocols:
                score += 15
            if ports & messaging_ports:
                score += 12
        
        # API-centric detection
        if 'rest_api' in service_patterns or 'api_gateway' in service_patterns:
            api_ports = {8080, 8443, 9090}
            if ports & api_ports and ('HTTP' in protocols or 'HTTPS' in protocols):
                score += 10
                
                # Multiple API ports suggest API-centric
                if len(ports & api_ports) >= 2:
                    score += 5
        
        # Web + API Headless detection
        if 'spa_frontend' in service_patterns:
            web_ports = {80, 443}
            api_ports = {8080, 3000}
            if (ports & web_ports) and (ports & api_ports):
                score += 12
        
        # N-Tier detection
        if 'multi_tier' in service_patterns or 'load_balanced' in service_patterns:
            # Presence of multiple tiers (web, app, db, cache)
            tier_indicators = 0
            if ports & {80, 443}:  # Web tier
                tier_indicators += 1
            if ports & {8080, 8443, 3000, 9090}:  # App tier
                tier_indicators += 1
            if ports & {3306, 5432, 1433}:  # DB tier
                tier_indicators += 1
            if ports & {6379, 11211}:  # Cache tier
                tier_indicators += 1
            
            if tier_indicators >= 3:
                score += 15
        
        # Cloud-native detection
        if 'kubernetes' in service_patterns or 'container_orchestration' in service_patterns:
            # Container port ranges and orchestration indicators
            container_ports = [p for p in ports if 8000 <= p <= 9999]
            if len(container_ports) >= 2:
                score += 8
            
            # gRPC and HTTPS together suggest cloud-native
            if 'GRPC' in protocols and 'HTTPS' in protocols:
                score += 10
        
        # Client-Server detection
        if 'thick_client' in service_patterns or 'direct_db_access' in service_patterns:
            client_server_ports = {1433, 3389, 5432}
            if ports & client_server_ports:
                score += 12
                
                # RDP presence strongly suggests client-server
                if 3389 in ports:
                    score += 8
        
        # Host-Terminal detection
        if 'terminal_access' in service_patterns:
            terminal_ports = {23, 22}  # TELNET, SSH
            if ports & terminal_ports:
                score += 10
        
        # Apply priority weighting
        score *= config.get('priority', 5)
        
        pattern_scores[archetype] = score
    
    return pattern_scores

def enhanced_archetype_classification(df, service_classifications: Dict) -> Dict[str, str]:
    """Enhanced archetype classification using YAML template patterns"""
    
    archetype_assignments = {}
    
    # Group connections by application
    app_groups = df.groupby('application')
    
    for app_name, app_data in app_groups:
        # Convert to list of dicts for analysis
        app_rows = app_data.to_dict('records')
        
        # Analyze patterns for this application
        pattern_scores = analyze_service_patterns(app_rows)
        
        # Get the highest scoring archetype
        if pattern_scores:
            best_archetype = max(pattern_scores.keys(), key=lambda k: pattern_scores[k])
            best_score = pattern_scores[best_archetype]
            
            # Only assign if score is above threshold
            if best_score > 10:
                archetype_assignments[app_name] = best_archetype
            else:
                # Fallback to service-based classification
                archetype_assignments[app_name] = classify_by_service_category(app_rows, service_classifications)
        else:
            archetype_assignments[app_name] = '3-Tier'  # Default fallback
    
    return archetype_assignments

def classify_by_service_category(app_rows: List[Dict], service_classifications: Dict) -> str:
    """Fallback classification based on service categories"""
    
    # Count service categories in this application
    categories = {}
    for row in app_rows:
        dest_ip = row.get('destination_ip', '')
        dest_host = row.get('destination_hostname', '')
        dest_key = dest_ip or dest_host
        
        if dest_key in service_classifications:
            category, service_type = service_classifications[dest_key]
            categories[category] = categories.get(category, 0) + 1
    
    # Map dominant service category to archetype
    if not categories:
        return '3-Tier'
    
    dominant_category = max(categories.keys(), key=lambda k: categories[k])
    
    category_to_archetype = {
        'APPLICATION': 'Web + API Headless',
        'DATA': 'Database-Centric',
        'MESSAGING': 'Event-Driven',
        'SECURITY': 'SOA',
        'INFRASTRUCTURE': 'N-Tier Architecture',
        'MONITORING': 'Monolithic',
        'NETWORK': 'Client-Server'
    }
    
    return category_to_archetype.get(dominant_category, '3-Tier')

def get_archetype_details(archetype_name: str) -> Dict:
    """Get detailed information about a specific archetype"""
    return ARCHETYPE_TEMPLATES.get(archetype_name, {
        'description': 'Unknown archetype pattern',
        'typical_ports': [],
        'indicators': [],
        'traffic_pattern': 'unknown',
        'expected_hosts': [],
        'priority': 1
    })

def generate_archetype_summary(df, archetype_assignments: Dict[str, str]) -> str:
    """Generate a detailed summary of archetype classifications"""
    
    summary_lines = [
        "ENHANCED ARCHETYPE ANALYSIS SUMMARY",
        "=" * 40,
        ""
    ]
    
    # Count archetype occurrences
    archetype_counts = {}
    for archetype in archetype_assignments.values():
        archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
    
    # Sort by frequency
    sorted_archetypes = sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True)
    
    summary_lines.append("DETECTED ARCHITECTURAL PATTERNS:")
    summary_lines.append("-" * 35)
    
    for archetype, count in sorted_archetypes:
        percentage = (count / len(archetype_assignments)) * 100 if archetype_assignments else 0
        summary_lines.append(f"{archetype}: {count} applications ({percentage:.1f}%)")
        
        # Add archetype details
        details = get_archetype_details(archetype)
        summary_lines.append(f"  Description: {details['description']}")
        summary_lines.append(f"  Traffic Pattern: {details['traffic_pattern']}")
        summary_lines.append(f"  Key Indicators: {', '.join(details['indicators'][:3])}")
        summary_lines.append("")
    
    # Application-specific assignments
    summary_lines.append("APPLICATION-SPECIFIC ASSIGNMENTS:")
    summary_lines.append("-" * 32)
    
    for app_name, archetype in sorted(archetype_assignments.items()):
        summary_lines.append(f"{app_name}: {archetype}")
    
    return "\n".join(summary_lines)

# Integration function to be used in the main processing pipeline
def apply_enhanced_archetype_mapping(df: pd.DataFrame, service_classifications: Dict) -> pd.DataFrame:
    """Apply enhanced archetype mapping using YAML templates"""
    
    print("Applying enhanced archetype mapping with comprehensive templates...")
    
    # Get archetype assignments for each application
    archetype_assignments = enhanced_archetype_classification(df, service_classifications)
    
    # Apply archetype assignments to dataframe
    df['archetype'] = df['application'].map(archetype_assignments).fillna('3-Tier')
    
    # Generate and print summary
    summary = generate_archetype_summary(df, archetype_assignments)
    print("\n" + summary)
    
    # Show distribution
    print("\nFinal Archetype Distribution:")
    archetype_counts = df['archetype'].value_counts()
    for archetype, count in archetype_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {archetype}: {count} records ({percentage:.1f}%)")
    
    return df

# Export the key components for integration
__all__ = [
    'ARCHETYPE_TEMPLATES',
    'enhanced_archetype_classification', 
    'apply_enhanced_archetype_mapping',
    'get_archetype_details',
    'generate_archetype_summary'
]