"""
Network utility functions for the Application Auto Discoverer
"""

import ipaddress
import logging
from typing import Dict, List, Optional, Any
from models.topology_models import NodeType, ConnectionType

logger = logging.getLogger(__name__)

class NetworkUtils:
    """Utility class for network-related operations"""
    
    def __init__(self):
        pass
    
    def validate_ip_address(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    def validate_network_range(self, network_range: str) -> bool:
        """Validate network range format (CIDR notation)"""
        try:
            ipaddress.ip_network(network_range, strict=False)
            return True
        except ValueError:
            return False
    
    def determine_node_type(self, host_info: Dict[str, Any]) -> NodeType:
        """Determine node type based on host information"""
        # Check for specific indicators in the host info
        services = host_info.get('services', [])
        ports = host_info.get('open_ports', [])
        hostname = host_info.get('hostname', '').lower()
        
        # Router indicators
        if any(service.lower() in ['snmp', 'bgp', 'ospf'] for service in services):
            return NodeType.ROUTER
        if 161 in ports or 179 in ports:  # SNMP, BGP
            return NodeType.ROUTER
        if any(keyword in hostname for keyword in ['router', 'gw', 'gateway']):
            return NodeType.ROUTER
        
        # Switch indicators
        if any(service.lower() in ['stp', 'spanning-tree'] for service in services):
            return NodeType.SWITCH
        if any(keyword in hostname for keyword in ['switch', 'sw']):
            return NodeType.SWITCH
        
        # Firewall indicators
        if any(service.lower() in ['ipsec', 'vpn'] for service in services):
            return NodeType.FIREWALL
        if any(keyword in hostname for keyword in ['firewall', 'fw', 'palo', 'fortinet']):
            return NodeType.FIREWALL
        
        # Load balancer indicators
        if any(service.lower() in ['haproxy', 'nginx', 'f5'] for service in services):
            return NodeType.LOAD_BALANCER
        if any(keyword in hostname for keyword in ['lb', 'loadbalancer', 'f5']):
            return NodeType.LOAD_BALANCER
        
        # Server indicators
        if any(service.lower() in ['http', 'https', 'ssh', 'ftp', 'smtp', 'dns'] for service in services):
            return NodeType.SERVER
        if any(port in ports for port in [22, 80, 443, 21, 25, 53]):
            return NodeType.SERVER
        if any(keyword in hostname for keyword in ['server', 'srv', 'db', 'web', 'mail']):
            return NodeType.SERVER
        
        # Workstation indicators
        if any(service.lower() in ['rdp', 'vnc'] for service in services):
            return NodeType.WORKSTATION
        if 3389 in ports or 5900 in ports:  # RDP, VNC
            return NodeType.WORKSTATION
        if any(keyword in hostname for keyword in ['pc', 'workstation', 'desktop', 'laptop']):
            return NodeType.WORKSTATION
        
        return NodeType.UNKNOWN
    
    def determine_node_type_from_ip(self, ip_address: str) -> NodeType:
        """Determine node type based on IP address patterns"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Common patterns based on IP ranges
            if str(ip).endswith('.1') or str(ip).endswith('.254'):
                return NodeType.ROUTER  # Common gateway IPs
            
            # Private network patterns
            if ip.is_private:
                octets = str(ip).split('.')
                last_octet = int(octets[-1])
                
                # Server range (typically lower numbers)
                if 1 <= last_octet <= 50:
                    return NodeType.SERVER
                # Workstation range (typically higher numbers)
                elif 100 <= last_octet <= 200:
                    return NodeType.WORKSTATION
        
        except ValueError:
            pass
        
        return NodeType.UNKNOWN
    
    def determine_connection_type(self, protocols: List[str]) -> ConnectionType:
        """Determine connection type based on protocols"""
        protocols_lower = [p.lower() for p in protocols]
        
        if 'tcp' in protocols_lower or 'udp' in protocols_lower:
            return ConnectionType.ETHERNET
        elif 'wifi' in protocols_lower or '802.11' in protocols_lower:
            return ConnectionType.WIFI
        elif 'fiber' in protocols_lower or 'optical' in protocols_lower:
            return ConnectionType.FIBER
        elif 'serial' in protocols_lower:
            return ConnectionType.SERIAL
        elif 'virtual' in protocols_lower or 'vlan' in protocols_lower:
            return ConnectionType.VIRTUAL
        
        return ConnectionType.UNKNOWN
    
    def get_network_info(self, ip_address: str) -> Dict[str, Any]:
        """Get network information for an IP address"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            return {
                "ip_address": str(ip),
                "is_private": ip.is_private,
                "is_multicast": ip.is_multicast,
                "is_loopback": ip.is_loopback,
                "is_link_local": ip.is_link_local,
                "version": ip.version,
                "network_class": self._get_network_class(str(ip))
            }
        except ValueError:
            return {"error": "Invalid IP address"}
    
    def _get_network_class(self, ip_address: str) -> str:
        """Get network class for IPv4 addresses"""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            first_octet = int(str(ip).split('.')[0])
            
            if 1 <= first_octet <= 126:
                return "Class A"
            elif 128 <= first_octet <= 191:
                return "Class B"
            elif 192 <= first_octet <= 223:
                return "Class C"
            elif 224 <= first_octet <= 239:
                return "Class D (Multicast)"
            elif 240 <= first_octet <= 255:
                return "Class E (Experimental)"
        except (ValueError, ipaddress.AddressValueError):
            pass
        
        return "Unknown"
    
    def calculate_subnet_info(self, network_range: str) -> Dict[str, Any]:
        """Calculate subnet information"""
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            
            return {
                "network_address": str(network.network_address),
                "broadcast_address": str(network.broadcast_address),
                "netmask": str(network.netmask),
                "prefix_length": network.prefixlen,
                "num_addresses": network.num_addresses,
                "num_hosts": network.num_addresses - 2 if network.num_addresses > 2 else 0,
                "is_private": network.is_private,
                "supernet": str(network.supernet()) if network.prefixlen > 0 else None
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def get_common_ports(self) -> Dict[int, str]:
        """Get mapping of common ports to services"""
        return {
            20: "FTP Data",
            21: "FTP Control",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            67: "DHCP Server",
            68: "DHCP Client",
            69: "TFTP",
            80: "HTTP",
            110: "POP3",
            123: "NTP",
            143: "IMAP",
            161: "SNMP",
            179: "BGP",
            389: "LDAP",
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            3389: "RDP",
            5900: "VNC"
        }
    
    def analyze_port_scan_results(self, ports: List[int]) -> Dict[str, Any]:
        """Analyze port scan results to identify services"""
        common_ports = self.get_common_ports()
        
        identified_services = []
        for port in ports:
            if port in common_ports:
                identified_services.append({
                    "port": port,
                    "service": common_ports[port]
                })
        
        # Categorize based on identified services
        categories = set()
        for service_info in identified_services:
            service = service_info["service"].lower()
            if any(web in service for web in ["http", "https"]):
                categories.add("Web Server")
            elif any(mail in service for mail in ["smtp", "pop", "imap"]):
                categories.add("Mail Server")
            elif "dns" in service:
                categories.add("DNS Server")
            elif any(remote in service for remote in ["ssh", "rdp", "vnc", "telnet"]):
                categories.add("Remote Access")
            elif any(net in service for net in ["snmp", "dhcp", "ntp"]):
                categories.add("Network Services")
        
        return {
            "total_open_ports": len(ports),
            "identified_services": identified_services,
            "unidentified_ports": [p for p in ports if p not in common_ports],
            "service_categories": list(categories)
        }
    
    def generate_network_summary(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of network topology"""
        if not nodes:
            return {"error": "No nodes provided"}
        
        node_types = {}
        total_nodes = len(nodes)
        ip_ranges = set()
        
        for node in nodes:
            # Count node types
            node_type = node.get("node_type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # Collect IP ranges
            ip = node.get("ip_address")
            if ip:
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    # Get /24 subnet
                    subnet = ipaddress.ip_network(f"{ip}/24", strict=False)
                    ip_ranges.add(str(subnet))
                except ValueError:
                    pass
        
        return {
            "total_nodes": total_nodes,
            "node_types": node_types,
            "unique_subnets": len(ip_ranges),
            "subnet_ranges": list(ip_ranges),
            "network_diversity": len(node_types)
        }