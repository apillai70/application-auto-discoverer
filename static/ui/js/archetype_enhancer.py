"""
Banking Archetype Enhancement Service
Extends existing archetype classifications with banking-specific metadata
"""

from typing import List, Dict, Any, Set
import re

class BankingArchetypeEnhancer:
    """Enhances archetype data with banking service types and security zones"""
    
    def __init__(self):
        self.banking_service_mapping = {
            'Web + API Headless': 'api_gateway',
            'API-Centric': 'api_gateway', 
            'Microservices': 'business_service',
            'SOA': 'business_service',
            'Database-Centric': 'data_store',
            'Client-Server': 'data_store',
            'Event-Driven': 'message_broker',
            'ETL/Data Pipeline': 'data_pipeline',
            '3-Tier': 'application_server',
            'Monolithic': 'application_server'
        }
        
        self.zone_colors = {
            'dmz': '#FF6B35',
            'internal': '#4ECDC4',
            'core_banking': '#45B7D1'
        }
        
        self.service_type_shapes = {
            'api_gateway': 'diamond',
            'business_service': 'rectangle',
            'data_store': 'cylinder',
            'message_broker': 'hexagon',
            'data_pipeline': 'parallelogram',
            'application_server': 'rectangle'
        }
    
    def enhance_applications(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance application list with banking metadata"""
        
        enhanced_apps = []
        connections = []
        
        for app in applications:
            enhanced_app = self._enhance_single_application(app)
            enhanced_apps.append(enhanced_app)
        
        # Generate banking-specific connections
        connections = self._generate_banking_connections(enhanced_apps)
        
        # Group by security zones for analysis
        zone_stats = self._calculate_zone_statistics(enhanced_apps)
        
        return {
            'applications': enhanced_apps,
            'connections': connections,
            'banking_metadata': {
                'security_zones': zone_stats,
                'service_types': self._count_service_types(enhanced_apps),
                'compliance_coverage': self._analyze_compliance(enhanced_apps)
            }
        }
    
    def _enhance_single_application(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Add banking context to a single application"""
        
        archetype = app.get('archetype', 'Unknown')
        app_name = app.get('name', '')
        ports = self._extract_ports_from_app(app)
        
        # Determine banking service type
        banking_service_type = self._classify_banking_service_type(archetype, app_name, ports)
        
        # Determine security zone
        security_zone = self._determine_security_zone(banking_service_type, app_name, ports)
        
        # Get compliance requirements
        compliance = self._get_compliance_requirements(security_zone, banking_service_type)
        
        # Extract data flow context from network evidence
        data_flows = self._extract_data_flows(app.get('network_evidence', []), app_name)
        
        return {
            **app,
            'banking_service_type': banking_service_type,
            'security_zone': security_zone,
            'zone_color': self.zone_colors.get(security_zone, '#64748b'),
            'service_shape': self.service_type_shapes.get(banking_service_type, 'rectangle'),
            'compliance_requirements': compliance,
            'data_flows': data_flows,
            'business_criticality': self._determine_criticality(security_zone, archetype),
            'banking_context': self._get_banking_context(app_name, banking_service_type)
        }
    
    def _classify_banking_service_type(self, archetype: str, app_name: str, ports: List[int]) -> str:
        """Classify application as banking service type"""
        
        name_lower = app_name.lower()
        port_set = set(ports)
        
        # Direct name-based classification first
        if any(term in name_lower for term in ['api', 'gateway', 'proxy']):
            return 'api_gateway'
        elif any(term in name_lower for term in ['queue', 'kafka', 'topic', 'event']):
            return 'message_broker'
        elif any(term in name_lower for term in ['database', 'db', 'sql', 'dynamo', 'snowflake']):
            return 'data_store'
        elif any(term in name_lower for term in ['etl', 'pipeline', 'batch']):
            return 'data_pipeline'
        
        # Port-based classification
        if any(p in port_set for p in [80, 443, 8080, 8443]):
            return 'api_gateway'
        elif any(p in port_set for p in [3306, 5432, 1433, 1521]):
            return 'data_store'
        elif any(p in port_set for p in [5672, 9092, 61616]):
            return 'message_broker'
        
        # Archetype-based fallback
        return self.banking_service_mapping.get(archetype, 'business_service')
    
    def _determine_security_zone(self, service_type: str, app_name: str, ports: List[int]) -> str:
        """Determine banking security zone"""
        
        name_lower = app_name.lower()
        
        # DMZ: External-facing services
        if (service_type == 'api_gateway' or 
            any(term in name_lower for term in ['api', 'web', 'portal', 'external'])):
            return 'dmz'
        
        # Core Banking: Critical data systems
        elif (service_type == 'data_store' or
              any(term in name_lower for term in ['core', 'ledger', 'transaction', 'account'])):
            return 'core_banking'
        
        # Internal: Business logic and integration
        else:
            return 'internal'
    
    def _get_compliance_requirements(self, zone: str, service_type: str) -> List[str]:
        """Get compliance requirements based on zone and service type"""
        
        base_compliance = {
            'dmz': ['PCI-DSS', 'SOX'],
            'internal': ['SOX', 'GDPR'], 
            'core_banking': ['PCI-DSS', 'SOX', 'GDPR', 'FFIEC']
        }
        
        compliance = set(base_compliance.get(zone, ['SOX']))
        
        # Add service-specific requirements
        if service_type == 'data_store':
            compliance.add('GDPR')
        elif service_type == 'api_gateway':
            compliance.add('PCI-DSS')
        
        return sorted(list(compliance))
    
    def _extract_ports_from_app(self, app: Dict[str, Any]) -> List[int]:
        """Extract port numbers from application data"""
        
        ports = []
        
        # From primary_ports field
        if 'primary_ports' in app and isinstance(app['primary_ports'], list):
            for port_info in app['primary_ports']:
                if isinstance(port_info, dict) and 'port' in port_info:
                    ports.append(int(port_info['port']))
                elif isinstance(port_info, (int, str)):
                    try:
                        ports.append(int(port_info))
                    except (ValueError, TypeError):
                        pass
        
        # From ports field (alternative format)
        if 'ports' in app and isinstance(app['ports'], list):
            for port in app['ports']:
                try:
                    ports.append(int(port))
                except (ValueError, TypeError):
                    pass
        
        return ports
    
    def _extract_data_flows(self, network_evidence: List[str], app_name: str) -> List[str]:
        """Extract data flow patterns from network evidence and app name"""
        
        flows = []
        name_lower = app_name.lower()
        evidence_text = ' '.join(network_evidence).lower()
        
        # Infer flows based on app name and evidence
        if 'nudge' in name_lower:
            if 'api' in name_lower:
                flows.append('customer requests')
            elif 'service' in name_lower:
                flows.append('creates nudge instances')
            elif 'compute' in name_lower:
                flows.append('processes nudge logic')
        
        if 'activity' in name_lower or 'event' in evidence_text:
            flows.append('activity events')
            
        if 'transaction' in name_lower or 'payment' in name_lower:
            flows.append('transaction data')
            
        if 'customer' in name_lower:
            flows.append('customer data')
        
        if not flows:
            flows.append('data processing')
        
        return flows
    
    def _determine_criticality(self, zone: str, archetype: str) -> str:
        """Determine business criticality"""
        
        if zone == 'core_banking':
            return 'critical'
        elif zone == 'dmz' or archetype in ['Database-Centric', 'Event-Driven']:
            return 'high'
        else:
            return 'medium'
    
    def _get_banking_context(self, app_name: str, service_type: str) -> Dict[str, Any]:
        """Get banking-specific context"""
        
        context = {
            'domain': 'banking',
            'regulatory_environment': 'financial_services',
            'data_sensitivity': 'high' if service_type == 'data_store' else 'medium'
        }
        
        # Add specific banking functions
        name_lower = app_name.lower()
        if any(term in name_lower for term in ['payment', 'transaction']):
            context['banking_function'] = 'payments'
        elif any(term in name_lower for term in ['customer', 'account']):
            context['banking_function'] = 'customer_management'
        elif any(term in name_lower for term in ['risk', 'compliance']):
            context['banking_function'] = 'risk_management'
        else:
            context['banking_function'] = 'core_operations'
        
        return context
    
    def _generate_banking_connections(self, applications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate banking-specific connections between applications"""
        
        connections = []
        connection_id = 1
        
        # Group applications by service type
        service_groups = {}
        for app in applications:
            service_type = app['banking_service_type']
            if service_type not in service_groups:
                service_groups[service_type] = []
            service_groups[service_type].append(app)
        
        # API Gateway -> Business Services
        for api in service_groups.get('api_gateway', []):
            for service in service_groups.get('business_service', []):
                if self._apps_share_context(api, service):
                    connections.append({
                        'id': f'conn_{connection_id}',
                        'source': api['id'],
                        'target': service['id'],
                        'connection_type': 'api_call',
                        'flow_annotation': 'customer requests',
                        'protocol': 'HTTPS',
                        'security_level': 'encrypted'
                    })
                    connection_id += 1
        
        # Business Services -> Data Stores
        for service in service_groups.get('business_service', []):
            for store in service_groups.get('data_store', []):
                if self._apps_share_data_context(service, store):
                    annotation = self._infer_connection_annotation(service, store)
                    connections.append({
                        'id': f'conn_{connection_id}',
                        'source': service['id'],
                        'target': store['id'],
                        'connection_type': 'data_access',
                        'flow_annotation': annotation,
                        'protocol': 'SQL' if 'sql' in store['name'].lower() else 'NoSQL',
                        'security_level': 'encrypted'
                    })
                    connection_id += 1
        
        # Services -> Message Brokers
        for service in service_groups.get('business_service', []):
            for broker in service_groups.get('message_broker', []):
                if self._apps_share_event_context(service, broker):
                    connections.append({
                        'id': f'conn_{connection_id}',
                        'source': service['id'],
                        'target': broker['id'],
                        'connection_type': 'event_publish',
                        'flow_annotation': 'activity events',
                        'protocol': 'Kafka',
                        'security_level': 'authenticated'
                    })
                    connection_id += 1
        
        return connections
    
    def _apps_share_context(self, app1: Dict, app2: Dict) -> bool:
        """Check if two apps share business context"""
        
        name1 = app1['name'].lower()
        name2 = app2['name'].lower()
        
        # Check for common business terms
        business_terms = ['nudge', 'customer', 'account', 'transaction', 'payment']
        
        for term in business_terms:
            if term in name1 and term in name2:
                return True
        
        return False
    
    def _apps_share_data_context(self, service: Dict, store: Dict) -> bool:
        """Check if service likely accesses data store"""
        
        service_name = service['name'].lower()
        store_name = store['name'].lower()
        
        # Direct name matching
        if any(term in service_name for term in ['nudge', 'customer', 'activity']):
            if any(term in store_name for term in ['nudge', 'customer', 'activity']):
                return True
        
        # Zone-based logic - services typically access data in same or lower security zones
        service_zone = service.get('security_zone', 'internal')
        store_zone = store.get('security_zone', 'internal')
        
        zone_hierarchy = {'dmz': 1, 'internal': 2, 'core_banking': 3}
        return zone_hierarchy.get(service_zone, 2) <= zone_hierarchy.get(store_zone, 2)
    
    def _apps_share_event_context(self, service: Dict, broker: Dict) -> bool:
        """Check if service publishes to message broker"""
        
        service_name = service['name'].lower()
        broker_name = broker['name'].lower()
        
        # Event-related naming patterns
        return (any(term in service_name for term in ['activity', 'event', 'notification']) or
                any(term in broker_name for term in ['activity', 'user', 'event']))
    
    def _infer_connection_annotation(self, service: Dict, store: Dict) -> str:
        """Infer the connection annotation based on service and store names"""
        
        service_name = service['name'].lower()
        store_name = store['name'].lower()
        
        if 'nudge' in service_name and 'nudge' in store_name:
            return 'creates nudge instances'
        elif 'activity' in service_name or 'activity' in store_name:
            return 'consumes activity for expiry'
        elif 'transaction' in service_name or 'transaction' in store_name:
            return 'consume transactions'
        else:
            return 'data access'
    
    def _calculate_zone_statistics(self, applications: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics by security zone"""
        
        zones = {}
        for app in applications:
            zone = app.get('security_zone', 'internal')
            if zone not in zones:
                zones[zone] = {
                    'name': zone.replace('_', ' ').title(),
                    'color': self.zone_colors.get(zone, '#64748b'),
                    'count': 0,
                    'applications': []
                }
            zones[zone]['count'] += 1
            zones[zone]['applications'].append(app['id'])
        
        return zones
    
    def _count_service_types(self, applications: List[Dict]) -> Dict[str, int]:
        """Count applications by banking service type"""
        
        counts = {}
        for app in applications:
            service_type = app.get('banking_service_type', 'unknown')
            counts[service_type] = counts.get(service_type, 0) + 1
        
        return counts
    
    def _analyze_compliance(self, applications: List[Dict]) -> Dict[str, Any]:
        """Analyze compliance coverage across applications"""
        
        all_requirements = set()
        by_requirement = {}
        
        for app in applications:
            requirements = app.get('compliance_requirements', [])
            all_requirements.update(requirements)
            
            for req in requirements:
                if req not in by_requirement:
                    by_requirement[req] = []
                by_requirement[req].append(app['id'])
        
        return {
            'total_requirements': len(all_requirements),
            'requirements': sorted(list(all_requirements)),
            'coverage_by_requirement': by_requirement
        }