#!/usr/bin/env python3
"""
Topology Backend Data Processing
Handles large dataset processing for network topology visualization
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
from dataclasses import dataclass
import openpyxl
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TopologyConfig:
    """Configuration for topology processing"""
    max_nodes: int = 5000
    max_links: int = 15000
    include_upstream: bool = False
    include_downstream: bool = False
    archetype_mapping: Dict[str, str] = None

class TopologyDataProcessor:
    """Main class for processing topology data"""
    
    def __init__(self, config: TopologyConfig = None):
        self.config = config or TopologyConfig()
        self.application_list = self._load_application_list()
        self.archetype_mapping = self._create_archetype_mapping()
        
    def _load_application_list(self) -> List[Dict[str, str]]:
        """Load the 51 applications from CSV"""
        applications = [
            {"app_id": "ACDA", "app_name": "ATM Check Card Disputes API"},
            {"app_id": "ALE", "app_name": "Advisor Locator Engine"},
            {"app_id": "AODSVY", "app_name": "AOD Survey"},
            {"app_id": "APSE", "app_name": "Appointment Setting (Timetrade)"},
            {"app_id": "ARA", "app_name": "Account Analysis Request Application"},
            {"app_id": "AV", "app_name": "Automated Vault"},
            {"app_id": "BCA", "app_name": "Branch Customer Authentication"},
            {"app_id": "BKO", "app_name": "Banko POC"},
            {"app_id": "BLND", "app_name": "BLEND SSI"},
            {"app_id": "BLZD", "app_name": "FICO/Blaze Decisioning -Rules Development"},
            {"app_id": "BPM", "app_name": "Business Process Management"},
            {"app_id": "CALC", "app_name": "Online Calculators"},
            {"app_id": "CCAPI", "app_name": "Credit Card API"},
            {"app_id": "CNCT", "app_name": "Customer Connection"},
            {"app_id": "COP", "app_name": "Commercial Online Portal"},
            {"app_id": "CPS", "app_name": "Check Processing System"},
            {"app_id": "CRM", "app_name": "Customer Relationship Management"},
            {"app_id": "CUST", "app_name": "Customer Management System"},
            {"app_id": "DDA", "app_name": "Demand Deposit Accounting"},
            {"app_id": "DMS", "app_name": "Document Management System"},
            {"app_id": "DOCU", "app_name": "DocuSign Integration"},
            {"app_id": "DTPCK", "app_name": "Data Processing Check"},
            {"app_id": "EBANK", "app_name": "Electronic Banking"},
            {"app_id": "EDEPO", "app_name": "Electronic Deposit"},
            {"app_id": "EFMS", "app_name": "Enterprise Financial Management System"},
            {"app_id": "ELN", "app_name": "Electronic Loan Network"},
            {"app_id": "ENTPAY", "app_name": "Enterprise Payment System"},
            {"app_id": "FRAUD", "app_name": "Fraud Detection System"},
            {"app_id": "GLSYS", "app_name": "General Ledger System"},
            {"app_id": "INVST", "app_name": "Investment Management"},
            {"app_id": "JACK", "app_name": "Jack Henry Core System"},
            {"app_id": "KCCP", "app_name": "Know Your Customer Compliance Platform"},
            {"app_id": "LOAN", "app_name": "Loan Origination System"},
            {"app_id": "MOBAPP", "app_name": "Mobile Banking Application"},
            {"app_id": "NCINO", "app_name": "nCino Lending Platform"},
            {"app_id": "ONBD", "app_name": "Digital Onboarding Platform"},
            {"app_id": "PAYROLL", "app_name": "Payroll Processing System"},
            {"app_id": "PORTAL", "app_name": "Customer Web Portal"},
            {"app_id": "POS", "app_name": "Point of Sale System"},
            {"app_id": "RATES", "app_name": "Interest Rate Management"},
            {"app_id": "REMIT", "app_name": "Remittance Processing"},
            {"app_id": "REPORT", "app_name": "Reporting and Analytics"},
            {"app_id": "RISK", "app_name": "Risk Management System"},
            {"app_id": "SAFE", "app_name": "Safety Deposit Box Management"},
            {"app_id": "SWIFT", "app_name": "SWIFT Messaging System"},
            {"app_id": "TELLER", "app_name": "Teller System"},
            {"app_id": "TRADE", "app_name": "Trade Finance System"},
            {"app_id": "TRUST", "app_name": "Trust Management System"},
            {"app_id": "VAULT", "app_name": "Digital Vault System"},
            {"app_id": "WIRE", "app_name": "Wire Transfer System"},
            {"app_id": "ZELLE", "app_name": "Zelle Payment Network"}
        ]
        logger.info(f"Loaded {len(applications)} applications")
        return applications
    
    def _create_archetype_mapping(self) -> Dict[str, str]:
        """Create mapping of applications to archetypes"""
        mapping = {
            # Core Banking
            "JACK": "Core Banking", "DDA": "Core Banking", "GLSYS": "Core Banking",
            "TELLER": "Core Banking", "ACDA": "Core Banking",
            
            # Lending Platform
            "NCINO": "Lending Platform", "LOAN": "Lending Platform", "BLND": "Lending Platform",
            "ELN": "Lending Platform", "CRE": "Lending Platform",
            
            # Payment Processing
            "WIRE": "Payment Processing", "ZELLE": "Payment Processing", "ENTPAY": "Payment Processing",
            "POS": "Payment Processing", "REMIT": "Payment Processing",
            
            # Customer Management
            "CRM": "Customer Management", "CUST": "Customer Management", "CNCT": "Customer Management",
            "ONBD": "Customer Management", "Customer": "Customer Management",
            
            # Risk Management
            "RISK": "Risk Management", "FRAUD": "Risk Management", "KCCP": "Risk Management",
            
            # Digital Banking
            "EBANK": "Digital Banking", "MOBAPP": "Digital Banking", "PORTAL": "Digital Banking",
            "COP": "Digital Banking", "CALC": "Digital Banking",
            
            # Trading Systems
            "TRADE": "Trading Systems", "SWIFT": "Trading Systems", "MTS": "Trading Systems",
            "Calypso": "Trading Systems",
            
            # Treasury Management
            "iTreasury": "Treasury Management", "RATES": "Treasury Management",
            
            # Compliance
            "BLZD": "Compliance", "BPM": "Compliance",
            
            # Analytics
            "REPORT": "Analytics", "DNZEL": "Analytics",
            
            # Integration
            "DOCU": "Integration", "DMS": "Integration", "DTPCK": "Integration",
            
            # Security
            "AV": "Security", "SAFE": "Security", "VAULT": "Security"
        }
        
        # Add archetype based on port patterns for unknown applications
        default_archetypes = [
            "Microservices", "SOA", "3-Tier", "Monolithic", 
            "Web + API Headless", "Event-Driven", "Client-Server"
        ]
        
        return mapping

    async def process_large_dataset(self, file_path: str) -> Dict[str, Any]:
        """Process the 220K flow dataset"""
        logger.info(f"Processing large dataset: {file_path}")
        
        try:
            # Load Excel file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            logger.info(f"Loaded {len(df)} flow records")
            
            # Extract unique nodes from src and dst
            nodes_data = self._extract_nodes(df)
            
            # Create links from flow data
            links_data = self._extract_links(df)
            
            # Apply filtering based on config
            if len(nodes_data) > self.config.max_nodes:
                nodes_data = self._sample_nodes(nodes_data, self.config.max_nodes)
                
            if len(links_data) > self.config.max_links:
                links_data = self._sample_links(links_data, self.config.max_links)
            
            # Create final topology structure
            topology = {
                "nodes": nodes_data,
                "links": links_data,
                "metadata": {
                    "totalFlows": len(df),
                    "totalNodes": len(nodes_data),
                    "totalLinks": len(links_data),
                    "applications": list(set(node["application"] for node in nodes_data)),
                    "archetypes": list(set(node["archetype"] for node in nodes_data)),
                    "dataSource": file_path,
                    "processedAt": datetime.now().isoformat(),
                    "isLargeDataset": True
                }
            }
            
            logger.info(f"Created topology with {len(nodes_data)} nodes and {len(links_data)} links")
            return topology
            
        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}")
            raise
    
    def _extract_nodes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract unique nodes from flow data"""
        # Get all unique IP addresses
        src_ips = set(df['src'].dropna().unique())
        dst_ips = set(df['dst'].dropna().unique())
        all_ips = src_ips.union(dst_ips)
        
        logger.info(f"Found {len(all_ips)} unique IP addresses")
        
        nodes = []
        ip_to_app_map = self._create_ip_to_application_mapping(df)
        
        for ip in all_ips:
            app_info = ip_to_app_map.get(ip, {})
            application = app_info.get('application', 'Unknown')
            archetype = self._determine_archetype(application, app_info)
            
            node = {
                "id": ip,
                "ip": ip,
                "application": application,
                "archetype": archetype,
                "cluster": hash(archetype) % 20,  # Distribute across 20 clusters
                "group": hash(application) % 10,  # Distribute across 10 groups
                "connectionCount": app_info.get('connection_count', 0)
            }
            nodes.append(node)
        
        return nodes
    
    def _extract_links(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract links from flow data"""
        links = []
        
        # Sample data if too large
        sample_size = min(len(df), self.config.max_links)
        df_sample = df.sample(n=sample_size) if len(df) > sample_size else df
        
        for _, row in df_sample.iterrows():
            if pd.isna(row['src']) or pd.isna(row['dst']):
                continue
                
            link = {
                "source": str(row['src']),
                "target": str(row['dst']),
                "protocol": row.get('protocol', 'TCP'),
                "port": int(row.get('port', 80)),
                "application": row.get('application', 'Unknown'),
                "archetype": row.get('archetype', 'Unknown'),
                "value": 1
            }
            
            # Add additional metadata if available
            if 'timestamp' in row:
                link['timestamp'] = row['timestamp']
            if 'behavior' in row:
                link['behavior'] = row['behavior']
                
            links.append(link)
        
        logger.info(f"Created {len(links)} links from flow data")
        return links
    
    def _create_ip_to_application_mapping(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Create mapping of IP addresses to applications"""
        ip_app_map = defaultdict(lambda: {'applications': [], 'connection_count': 0})
        
        # Count connections per IP
        for _, row in df.iterrows():
            for ip_col in ['src', 'dst']:
                if pd.notna(row[ip_col]):
                    ip = str(row[ip_col])
                    app = row.get('application', 'Unknown')
                    
                    ip_app_map[ip]['applications'].append(app)
                    ip_app_map[ip]['connection_count'] += 1
        
        # Determine most common application per IP
        final_mapping = {}
        for ip, data in ip_app_map.items():
            # Get most frequent application
            app_counts = defaultdict(int)
            for app in data['applications']:
                app_counts[app] += 1
            
            most_common_app = max(app_counts.items(), key=lambda x: x[1])[0]
            
            final_mapping[ip] = {
                'application': most_common_app,
                'connection_count': data['connection_count'],
                'all_applications': list(set(data['applications']))
            }
        
        return final_mapping
    
    def _determine_archetype(self, application: str, app_info: Dict) -> str:
        """Determine archetype based on application name and connection patterns"""
        # Check direct mapping first
        for key, archetype in self.archetype_mapping.items():
            if key.lower() in application.lower():
                return archetype
        
        # Determine based on connection patterns or application name patterns
        connection_count = app_info.get('connection_count', 0)
        
        if 'api' in application.lower() or 'microservice' in application.lower():
            return "Microservices"
        elif 'core' in application.lower() or 'banking' in application.lower():
            return "Core Banking"
        elif 'payment' in application.lower() or 'wire' in application.lower():
            return "Payment Processing"
        elif 'risk' in application.lower() or 'fraud' in application.lower():
            return "Risk Management"
        elif 'web' in application.lower() or 'portal' in application.lower():
            return "Web + API Headless"
        elif connection_count > 100:
            return "SOA"  # High connectivity suggests SOA
        elif connection_count > 50:
            return "3-Tier"
        else:
            return "Client-Server"
    
    def _sample_nodes(self, nodes: List[Dict], max_count: int) -> List[Dict]:
        """Sample nodes while preserving important ones"""
        if len(nodes) <= max_count:
            return nodes
        
        # Sort by connection count and archetype importance
        archetype_priority = {
            "Core Banking": 10, "Payment Processing": 9, "Risk Management": 8,
            "Lending Platform": 7, "Trading Systems": 6, "Treasury Management": 5,
            "Customer Management": 4, "Digital Banking": 3, "Analytics": 2,
            "Integration": 1, "Security": 1
        }
        
        def node_priority(node):
            archetype_score = archetype_priority.get(node['archetype'], 0)
            connection_score = node.get('connectionCount', 0)
            return archetype_score * 1000 + connection_score
        
        # Sort and take top nodes
        sorted_nodes = sorted(nodes, key=node_priority, reverse=True)
        return sorted_nodes[:max_count]
    
    def _sample_links(self, links: List[Dict], max_count: int) -> List[Dict]:
        """Sample links while preserving important connections"""
        if len(links) <= max_count:
            return links
        
        # Prioritize HTTPS/secure connections and high-value ports
        def link_priority(link):
            protocol_score = 2 if link['protocol'] in ['HTTPS', 'TLS'] else 1
            port_score = 2 if link['port'] in [443, 8443, 9443] else 1
            return protocol_score * port_score
        
        # Sort and sample
        sorted_links = sorted(links, key=link_priority, reverse=True)
        return sorted_links[:max_count]

    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data for ML training and ServiceNow enrichment"""
        logger.info("Normalizing topology data for ML training")
        
        normalized = {
            "normalized_at": datetime.now().isoformat(),
            "source_metadata": data.get("metadata", {}),
            "feature_vectors": [],
            "training_labels": [],
            "node_features": {},
            "graph_statistics": {}
        }
        
        # Extract features for each node
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        # Create adjacency information
        adjacency = defaultdict(list)
        for link in links:
            adjacency[link["source"]].append(link["target"])
            adjacency[link["target"]].append(link["source"])
        
        for node in nodes:
            node_id = node["id"]
            neighbors = adjacency[node_id]
            
            # Calculate network features
            features = {
                "node_degree": len(neighbors),
                "clustering_coefficient": self._calculate_clustering_coefficient(node_id, adjacency),
                "betweenness_centrality": np.random.random(),  # Placeholder
                "archetype_encoded": self._encode_archetype(node["archetype"]),
                "application_encoded": hash(node["application"]) % 1000,
                "ip_subnet": int(node["ip"].split(".")[2]) if "." in node["ip"] else 0
            }
            
            normalized["feature_vectors"].append(list(features.values()))
            normalized["training_labels"].append(node["archetype"])
            normalized["node_features"][node_id] = features
        
        # Calculate graph-level statistics
        normalized["graph_statistics"] = {
            "total_nodes": len(nodes),
            "total_edges": len(links),
            "average_degree": sum(len(neighbors) for neighbors in adjacency.values()) / len(nodes) if nodes else 0,
            "density": len(links) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0
        }
        
        logger.info(f"Normalized data with {len(normalized['feature_vectors'])} feature vectors")
        return normalized
    
    def _calculate_clustering_coefficient(self, node_id: str, adjacency: Dict) -> float:
        """Calculate clustering coefficient for a node"""
        neighbors = adjacency[node_id]
        if len(neighbors) < 2:
            return 0.0
        
        # Count triangles
        triangles = 0
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if neighbors[j] in adjacency[neighbors[i]]:
                    triangles += 1
        
        possible_triangles = len(neighbors) * (len(neighbors) - 1) / 2
        return triangles / possible_triangles if possible_triangles > 0 else 0.0
    
    def _encode_archetype(self, archetype: str) -> int:
        """Encode archetype as integer for ML training"""
        archetype_map = {
            "Core Banking": 0, "Lending Platform": 1, "Payment Processing": 2,
            "Customer Management": 3, "Risk Management": 4, "Digital Banking": 5,
            "Trading Systems": 6, "Treasury Management": 7, "Compliance": 8,
            "Analytics": 9, "Integration": 10, "Security": 11,
            "Microservices": 12, "SOA": 13, "3-Tier": 14, "Monolithic": 15,
            "Web + API Headless": 16, "Event-Driven": 17, "Client-Server": 18
        }
        return archetype_map.get(archetype, 19)  # 19 for unknown

# Example usage and API integration
async def main():
    """Main function for testing"""
    processor = TopologyDataProcessor()
    
    # Example: Process large dataset
    try:
        topology = await processor.process_large_dataset("synthetic_flows_apps_archetype_mapped.xlsx")
        print(f"Processed topology: {topology['metadata']['totalNodes']} nodes")
        
        # Normalize for ML training
        normalized = processor.normalize_data(topology)
        print(f"Normalized features: {len(normalized['feature_vectors'])} samples")
        
        # Save results
        with open("topology_processed.json", "w") as f:
            json.dump(topology, f, indent=2)
            
        with open("topology_normalized.json", "w") as f:
            json.dump(normalized, f, indent=2)
            
        print("Processing complete!")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())