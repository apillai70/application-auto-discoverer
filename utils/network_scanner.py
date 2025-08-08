"""
Network scanner service for log-based network discovery
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from models.topology_models import TopologyNode, TopologyEdge, NodeType, ConnectionType
from utils.network_utils import NetworkUtils

logger = logging.getLogger(__name__)

class NetworkScanner:
    """
    Log-based network scanner that analyzes network traffic logs
    to discover topology and connections
    """
    
    def __init__(self):
        self.network_utils = NetworkUtils()
        self.discovered_nodes: Dict[str, TopologyNode] = {}
        self.discovered_connections: List[TopologyEdge] = []
        
    async def scan_from_logs(self, log_data: List[Dict[str, Any]], source_type: str = "unknown") -> Dict[str, Any]:
        """
        Main scanning method that analyzes log data to discover network topology
        """
        logger.info(f"Starting network scan from {len(log_data)} log entries from {source_type}")
        
        scan_results = {
            "nodes": [],
            "connections": [],
            "statistics": {},
            "source_type": source_type,
            "scan_timestamp": datetime.now()
        }
        
        try:
            # Extract nodes and connections from logs
            nodes = await self._extract_nodes_from_logs(log_data, source_type)
            connections = await self._extract_connections_from_logs(log_data, nodes)
            
            # Enhance node information
            enhanced_nodes = await self._enhance_node_information(nodes, log_data)
            
            # Generate statistics
            statistics = self._generate_scan_statistics(enhanced_nodes, connections, log_data)
            
            scan_results.update({
                "nodes": enhanced_nodes,
                "connections": connections,
                "statistics": statistics
            })
            
            logger.info(f"Scan completed: {len(enhanced_nodes)} nodes, {len(connections)} connections")
            
        except Exception as e:
            logger.error(f"Error during network scan: {str(e)}")
            scan_results["error"] = str(e)
        
        return scan_results
    
    async def _extract_nodes_from_logs(self, log_data: List[Dict[str, Any]], source_type: str) -> List[TopologyNode]:
        """Extract unique network nodes from log data"""
        unique_ips = set()
        node_info = {}
        
        # Extract all unique IP addresses
        for entry in log_data:
            source_ip = entry.get("source_ip") or entry.get("src_ip") or entry.get("client_ip")
            dest_ip = entry.get("dest_ip") or entry.get("dst_ip") or entry.get("server_ip")
            
            for ip in [source_ip, dest_ip]:
                if ip and self.network_utils.validate_ip_address(ip):
                    unique_ips.add(ip)
                    
                    # Initialize node info if not exists
                    if ip not in node_info:
                        node_info[ip] = {
                            "ip_address": ip,
                            "hostnames": set(),
                            "services": set(),
                            "ports": set(),
                            "protocols": set(),
                            "first_seen": None,
                            "last_seen": None,
                            "traffic_volume": 0,
                            "connection_count": 0
                        }
                    
                    # Update node information from log entry
                    self._update_node_from_log_entry(node_info[ip], entry)
        
        # Convert to TopologyNode objects
        nodes = []
        for ip, info in node_info.items():
            node = TopologyNode(
                id=f"node_{ip.replace('.', '_')}",
                ip_address=ip,
                hostname=list(info["hostnames"])[0] if info["hostnames"] else None,
                node_type=self._determine_node_type_from_logs(info),
                services=list(info["services"]),
                ports=list(info["ports"]),
                discovered_at=info["first_seen"] or datetime.now(),
                last_seen=info["last_seen"] or datetime.now(),
                metadata={
                    "source_type": source_type,
                    "traffic_volume": info["traffic_volume"],
                    "connection_count": info["connection_count"],
                    "protocols": list(info["protocols"])
                }
            )
            nodes.append(node)
        
        return nodes
    
    def _update_node_from_log_entry(self, node_info: Dict, entry: Dict[str, Any]):
        """Update node information from a single log entry"""
        # Update timestamps
        timestamp = entry.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = pd.to_datetime(timestamp)
                except:
                    timestamp = datetime.now()
            
            if node_info["first_seen"] is None or timestamp < node_info["first_seen"]:
                node_info["first_seen"] = timestamp
            if node_info["last_seen"] is None or timestamp > node_info["last_seen"]:
                node_info["last_seen"] = timestamp
        
        # Update hostnames
        hostname = entry.get("hostname") or entry.get("host") or entry.get("server_name")
        if hostname:
            node_info["hostnames"].add(hostname)
        
        # Update services and applications
        service = entry.get("service") or entry.get("application") or entry.get("app")
        if service:
            node_info["services"].add(service)
        
        # Update ports
        port = entry.get("port") or entry.get("dest_port") or entry.get("server_port")
        if port:
            try:
                node_info["ports"].add(int(port))
            except (ValueError, TypeError):
                pass
        
        # Update protocols
        protocol = entry.get("protocol") or entry.get("proto")
        if protocol:
            node_info["protocols"].add(protocol.upper())
        
        # Update traffic volume
        bytes_sent = entry.get("bytes_sent") or entry.get("bytes") or 0
        bytes_received = entry.get("bytes_received") or 0
        try:
            node_info["traffic_volume"] += int(bytes_sent) + int(bytes_received)
        except (ValueError, TypeError):
            pass
        
        # Update connection count
        node_info["connection_count"] += 1
    
    def _determine_node_type_from_logs(self, node_info: Dict) -> NodeType:
        """Determine node type based on log analysis"""
        services = node_info.get("services", set())
        ports = node_info.get("ports", set())
        protocols = node_info.get("protocols", set())
        traffic_volume = node_info.get("traffic_volume", 0)
        connection_count = node_info.get("connection_count", 0)
        
        # Convert to lists for easier analysis
        services_list = [s.lower() for s in services]
        ports_list = list(ports)
        
        # Router indicators
        if any(service in services_list for service in ['snmp', 'bgp', 'ospf']):
            return NodeType.ROUTER
        if any(port in ports_list for port in [161, 179, 520]):  # SNMP, BGP, RIP
            return NodeType.ROUTER
        
        # Switch indicators
        if 'spanning-tree' in services_list or 'stp' in services_list:
            return NodeType.SWITCH
        
        # Firewall indicators
        if any(service in services_list for service in ['ipsec', 'vpn', 'firewall']):
            return NodeType.FIREWALL
        
        # Load balancer indicators
        if any(service in services_list for service in ['haproxy', 'nginx', 'f5', 'load-balancer']):
            return NodeType.LOAD_BALANCER
        if connection_count > 1000:  # High connection count might indicate load balancer
            return NodeType.LOAD_BALANCER
        
        # Server indicators
        server_services = ['http', 'https', 'ssh', 'ftp', 'smtp', 'dns', 'database', 'mysql', 'postgresql']
        server_ports = [22, 80, 443, 21, 25, 53, 3306, 5432, 1433, 3389]
        
        if any(service in services_list for service in server_services):
            return NodeType.SERVER
        if any(port in ports_list for port in server_ports):
            return NodeType.SERVER
        if traffic_volume > 10000000:  # High traffic volume might indicate server
            return NodeType.SERVER
        
        # Workstation indicators
        workstation_services = ['rdp', 'vnc', 'smb', 'cifs']
        workstation_ports = [3389, 5900, 445, 139]
        
        if any(service in services_list for service in workstation_services):
            return NodeType.WORKSTATION
        if any(port in ports_list for port in workstation_ports):
            return NodeType.WORKSTATION
        
        return NodeType.UNKNOWN
    
    async def _extract_connections_from_logs(self, log_data: List[Dict[str, Any]], nodes: List[TopologyNode]) -> List[TopologyEdge]:
        """Extract network connections from log data"""
        connections = {}
        node_map = {node.ip_address: node.id for node in nodes}
        
        for entry in log_data:
            source_ip = entry.get("source_ip") or entry.get("src_ip") or entry.get("client_ip")
            dest_ip = entry.get("dest_ip") or entry.get("dst_ip") or entry.get("server_ip")
            
            if source_ip and dest_ip and source_ip in node_map and dest_ip in node_map:
                connection_key = (source_ip, dest_ip)
                
                if connection_key not in connections:
                    connections[connection_key] = {
                        "source_ip": source_ip,
                        "dest_ip": dest_ip,
                        "protocols": set(),
                        "ports": set(),
                        "services": set(),
                        "total_bytes": 0,
                        "packet_count": 0,
                        "first_seen": None,
                        "last_seen": None
                    }
                
                conn = connections[connection_key]
                
                # Update connection information
                protocol = entry.get("protocol", "TCP")
                if protocol:
                    conn["protocols"].add(protocol.upper())
                
                port = entry.get("dest_port") or entry.get("port")
                if port:
                    try:
                        conn["ports"].add(int(port))
                    except (ValueError, TypeError):
                        pass
                
                service = entry.get("service") or entry.get("application")
                if service:
                    conn["services"].add(service)
                
                # Update traffic statistics
                bytes_transferred = (entry.get("bytes_sent", 0) or 0) + (entry.get("bytes_received", 0) or 0)
                try:
                    conn["total_bytes"] += int(bytes_transferred)
                except (ValueError, TypeError):
                    pass
                
                conn["packet_count"] += 1
                
                # Update timestamps
                timestamp = entry.get("timestamp")
                if timestamp and isinstance(timestamp, str):
                    try:
                        timestamp = pd.to_datetime(timestamp)
                    except:
                        timestamp = datetime.now()
                
                if timestamp:
                    if conn["first_seen"] is None or timestamp < conn["first_seen"]:
                        conn["first_seen"] = timestamp
                    if conn["last_seen"] is None or timestamp > conn["last_seen"]:
                        conn["last_seen"] = timestamp
        
        # Convert to TopologyEdge objects
        edges = []
        for (source_ip, dest_ip), conn_info in connections.items():
            edge = TopologyEdge(
                id=f"edge_{source_ip.replace('.', '_')}_{dest_ip.replace('.', '_')}",
                source_node_id=node_map[source_ip],
                target_node_id=node_map[dest_ip],
                connection_type=self._determine_connection_type(conn_info["protocols"]),
                discovered_at=conn_info["first_seen"] or datetime.now(),
                last_tested=conn_info["last_seen"] or datetime.now(),
                metadata={
                    "protocols": list(conn_info["protocols"]),
                    "ports": list(conn_info["ports"]),
                    "services": list(conn_info["services"]),
                    "total_bytes": conn_info["total_bytes"],
                    "packet_count": conn_info["packet_count"]
                }
            )
            edges.append(edge)
        
        return edges
    
    def _determine_connection_type(self, protocols: Set[str]) -> ConnectionType:
        """Determine connection type based on protocols"""
        protocols_lower = {p.lower() for p in protocols}
        
        if 'tcp' in protocols_lower or 'udp' in protocols_lower:
            return ConnectionType.ETHERNET
        elif any(p in protocols_lower for p in ['wifi', '802.11', 'wireless']):
            return ConnectionType.WIFI
        elif any(p in protocols_lower for p in ['fiber', 'optical']):
            return ConnectionType.FIBER
        elif 'serial' in protocols_lower:
            return ConnectionType.SERIAL
        elif any(p in protocols_lower for p in ['vlan', 'virtual', 'tunnel']):
            return ConnectionType.VIRTUAL
        
        return ConnectionType.UNKNOWN
    
    async def _enhance_node_information(self, nodes: List[TopologyNode], log_data: List[Dict[str, Any]]) -> List[TopologyNode]:
        """Enhance node information with additional analysis"""
        # Create a map for quick lookup
        node_map = {node.ip_address: node for node in nodes}
        
        # Analyze patterns and enhance nodes
        for node in nodes:
            # Analyze communication patterns
            outbound_connections = 0
            inbound_connections = 0
            unique_destinations = set()
            unique_sources = set()
            
            for entry in log_data:
                source_ip = entry.get("source_ip") or entry.get("src_ip")
                dest_ip = entry.get("dest_ip") or entry.get("dst_ip")
                
                if source_ip == node.ip_address:
                    outbound_connections += 1
                    if dest_ip:
                        unique_destinations.add(dest_ip)
                
                if dest_ip == node.ip_address:
                    inbound_connections += 1
                    if source_ip:
                        unique_sources.add(source_ip)
            
            # Update node metadata with enhanced information
            node.metadata.update({
                "outbound_connections": outbound_connections,
                "inbound_connections": inbound_connections,
                "unique_destinations": len(unique_destinations),
                "unique_sources": len(unique_sources),
                "communication_ratio": outbound_connections / max(inbound_connections, 1)
            })
            
            # Refine node type based on communication patterns
            if node.node_type == NodeType.UNKNOWN:
                if len(unique_destinations) > 50:
                    node.node_type = NodeType.LOAD_BALANCER
                elif inbound_connections > outbound_connections * 3:
                    node.node_type = NodeType.SERVER
                elif outbound_connections > inbound_connections * 3:
                    node.node_type = NodeType.WORKSTATION
        
        return nodes
    
    def _generate_scan_statistics(self, nodes: List[TopologyNode], connections: List[TopologyEdge], log_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive scan statistics"""
        node_types = {}
        connection_types = {}
        protocols = set()
        services = set()
        
        # Analyze nodes
        for node in nodes:
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node.services:
                services.update(node.services)
        
        # Analyze connections
        for conn in connections:
            conn_type = conn.connection_type.value
            connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
            
            if conn.metadata and "protocols" in conn.metadata:
                protocols.update(conn.metadata["protocols"])
        
        # Calculate time range
        timestamps = []
        for entry in log_data:
            timestamp = entry.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        timestamp = pd.to_datetime(timestamp)
                    timestamps.append(timestamp)
                except:
                    pass
        
        time_range = None
        if timestamps:
            time_range = {
                "start": min(timestamps),
                "end": max(timestamps),
                "duration_hours": (max(timestamps) - min(timestamps)).total_seconds() / 3600
            }
        
        return {
            "total_nodes": len(nodes),
            "total_connections": len(connections),
            "node_types": node_types,
            "connection_types": connection_types,
            "protocols_detected": list(protocols),
            "services_detected": list(services),
            "time_range": time_range,
            "log_entries_processed": len(log_data),
            "scan_completion_time": datetime.now()
        }
    
    async def scan_extrahop_logs(self, log_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Specialized scanning for ExtraHop log format"""
        logger.info("Scanning ExtraHop logs")
        return await self.scan_from_logs(log_data, "extrahop")
    
    async def scan_splunk_logs(self, log_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Specialized scanning for Splunk log format"""
        logger.info("Scanning Splunk logs")
        return await self.scan_from_logs(log_data, "splunk")
    
    async def scan_dynatrace_logs(self, log_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Specialized scanning for DynaTrace log format"""
        logger.info("Scanning DynaTrace logs")
        return await self.scan_from_logs(log_data, "dynatrace")