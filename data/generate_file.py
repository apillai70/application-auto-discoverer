#!/usr/bin/env python3
"""
generate.py - Complete Data Preparation Pipeline with YAML Archetype Templates

Integrates comprehensive archetype templates from archetype_templates.yaml
with service classification for accurate architectural pattern detection.

Enhanced output columns include:
- application, source_ip, source_hostname, destination_ip, destination_hostname
- port, protocol, bytes_in, bytes_out, timestamp, behavior, info
- service_category, service_type, business_function
- archetype (with comprehensive YAML-based classification)
"""

from __future__ import annotations

# Fix Windows encoding issues
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import sys
import io

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import the enhanced archetype integration
from enhanced_archetype_integration import (
    ARCHETYPE_TEMPLATES, 
    apply_enhanced_archetype_mapping,
    get_archetype_details
)

import argparse
import ipaddress
import math
import random
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

import pandas as pd
import numpy as np

# Set random seed for reproducible results
random.seed(42)
np.random.seed(42)

# =================== CONSTANTS ===================
PEER_RE = re.compile(r'^\s*([^\s(]+)\s*(?:\(([^)]+)\))?\s*$')
HOSTLIKE_RE = re.compile(r'^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+\.?$')

# =================== SERVICE CLASSIFICATION (Enhanced) ===================

SERVICE_CATEGORIES = {
    'APPLICATION': {
        'web_server': {
            'protocols': ['HTTP', 'HTTPS'],
            'ports': [80, 443, 8080, 8443],
            'priority': 9,
            'description': 'Web servers serving user interfaces',
            'archetype_hints': ['Web + API Headless', '3-Tier', 'N-Tier Architecture']
        },
        'app_server': {
            'protocols': ['HTTP', 'HTTP-ALT', 'HTTP-PROXY'],
            'ports': [3000, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 9000, 9001, 9002, 9090],
            'priority': 8,
            'description': 'Application servers running business logic',
            'archetype_hints': ['N-Tier Architecture', 'Microservices', '3-Tier']
        },
        'api_gateway': {
            'protocols': ['HTTP', 'HTTPS', 'HTTP-ALT'],
            'ports': [8080, 8443, 9090, 3000],
            'priority': 8,
            'description': 'API gateways and service meshes',
            'archetype_hints': ['API-Centric (General)', 'Microservices', 'Cloud-Native']
        },
        'microservice': {
            'protocols': ['HTTP', 'GRPC', 'HTTP-ALT'],
            'ports': [8080, 9090, 50051] + list(range(3000, 3100)),
            'priority': 7,
            'description': 'Microservices and containerized apps',
            'archetype_hints': ['Microservices', 'Cloud-Native']
        }
    },
    'DATA': {
        'database': {
            'protocols': ['SQL', 'TDS', 'MYSQL', 'POSTGRESQL', 'ORACLE-TNS', 'TNS'],
            'ports': [3306, 5432, 1521, 1433, 1434],
            'priority': 10,
            'description': 'Relational databases',
            'archetype_hints': ['Database-Centric', 'Client-Server', '3-Tier']
        },
        'nosql_database': {
            'protocols': ['MONGODB', 'REDIS', 'CASSANDRA'],
            'ports': [27017, 6379, 9042, 7000, 7001],
            'priority': 9,
            'description': 'NoSQL and document databases',
            'archetype_hints': ['Database-Centric', 'Cloud-Native', 'Microservices']
        },
        'cache': {
            'protocols': ['REDIS', 'MEMCACHED'],
            'ports': [6379, 11211],
            'priority': 8,
            'description': 'In-memory caches',
            'archetype_hints': ['N-Tier Architecture', 'Cloud-Native', 'Microservices']
        }
    },
    'SECURITY': {
        'auth_server': {
            'protocols': ['LDAP', 'LDAPS', 'KERBEROS', 'RADIUS'],
            'ports': [389, 636, 88, 1812, 1813],
            'priority': 9,
            'description': 'Authentication and directory services',
            'archetype_hints': ['SOA', 'N-Tier Architecture', 'Client-Server']
        },
        'vpn_server': {
            'protocols': ['L2TP', 'PPTP', 'IKE', 'IPSEC-NAT'],
            'ports': [1701, 1723, 500, 4500],
            'priority': 8,
            'description': 'VPN servers and tunneling',
            'archetype_hints': ['Client-Server', 'Edge+Cloud Hybrid']
        }
    },
    'INFRASTRUCTURE': {
        'load_balancer': {
            'protocols': ['HTTP', 'HTTPS', 'TCP', 'UDP'],
            'ports': [80, 443, 8080, 1936, 8404],
            'priority': 10,
            'description': 'Load balancers and traffic distributors',
            'archetype_hints': ['N-Tier Architecture', 'Cloud-Native', 'Web + API Headless']
        },
        'dns_server': {
            'protocols': ['DNS'],
            'ports': [53],
            'priority': 9,
            'description': 'DNS servers',
            'archetype_hints': ['SOA', 'N-Tier Architecture']
        }
    },
    'MESSAGING': {
        'message_broker': {
            'protocols': ['AMQP', 'MQTT'],
            'ports': [5672, 9092, 61616, 1883, 5671, 15672],
            'priority': 9,
            'description': 'Message brokers and event streaming',
            'archetype_hints': ['Event-Driven', 'SOA with Message Broker', 'Microservices']
        },
        'email_server': {
            'protocols': ['SMTP', 'SMTP-SSL', 'SMTP-TLS', 'POP3', 'POP3S', 'IMAP', 'IMAPS'],
            'ports': [25, 465, 587, 110, 995, 143, 993],
            'priority': 8,
            'description': 'Email servers and mail transfer agents',
            'archetype_hints': ['Client-Server', 'SOA']
        }
    },
    'MONITORING': {
        'monitoring_server': {
            'protocols': ['SNMP', 'SNMPV3', 'HTTP', 'HTTPS'],
            'ports': [161, 162, 8080, 8443, 3000, 9090],
            'priority': 7,
            'description': 'Monitoring and observability platforms',
            'archetype_hints': ['Monolithic', 'Cloud-Native', 'Microservices']
        },
        'log_server': {
            'protocols': ['SYSLOG', 'HTTP', 'HTTPS'],
            'ports': [514, 6514, 5044, 9200],
            'priority': 7,
            'description': 'Log aggregation and SIEM systems',
            'archetype_hints': ['Monolithic', 'ETL/Data Pipeline']
        }
    },
    'NETWORK': {
        'file_server': {
            'protocols': ['FTP', 'FTPS', 'SFTP', 'SMB', 'NFS'],
            'ports': [21, 22, 445, 990, 2049],
            'priority': 6,
            'description': 'File servers and network storage',
            'archetype_hints': ['Client-Server', 'Host-Terminal']
        },
        'remote_access': {
            'protocols': ['SSH', 'TELNET', 'RDP', 'VNC'],
            'ports': [22, 23, 3389, 5900, 5901, 5902],
            'priority': 6,
            'description': 'Remote access servers',
            'archetype_hints': ['Host-Terminal', 'Client-Server']
        }
    }
}

# Standard port mappings for common protocols
STANDARD_PORTS = {
    'HTTP': 80, 'HTTPS': 443, 'HTTP-ALT': 8080, 'HTTP-PROXY': 3128,
    'SMTP': 25, 'SMTP-SSL': 465, 'SMTP-TLS': 587, 'POP3': 110, 'POP3S': 995, 'IMAP': 143, 'IMAPS': 993,
    'FTP': 21, 'FTP-DATA': 20, 'FTPS': 990, 'SFTP': 22, 'TFTP': 69,
    'SQL': 1433, 'MYSQL': 3306, 'POSTGRESQL': 5432, 'ORACLE-TNS': 1521, 'MONGODB': 27017, 'REDIS': 6379, 'TDS': 1433, 'TNS': 1521,
    'SSH': 22, 'TELNET': 23, 'RDP': 3389, 'VNC': 5900,
    'DNS': 53, 'LDAP': 389, 'LDAPS': 636, 'KERBEROS': 88, 'RADIUS': 1812,
    'SNMP': 161, 'SNMP-TRAP': 162, 'SNMPV3': 161, 'SYSLOG': 514, 'NTP': 123,
    'L2TP': 1701, 'PPTP': 1723, 'IKE': 500, 'IPSEC-NAT': 4500,
    'SIP': 5060, 'SIP-TLS': 5061, 'RTP': 5004, 'RTSP': 554,
    'XMPP': 5222, 'IRC': 6667, 'MSNP': 1863,
    'DHCP-SERVER': 67, 'DHCP-CLIENT': 68, 'BOOTPS': 67, 'BOOTPC': 68,
    'MSRPC': 135, 'NETBIOS-NS': 137, 'NETBIOS-DGM': 138, 'NETBIOS-SSN': 139, 'SMB': 445,
    'SSDP': 1900, 'MDNS': 5353, 'SLP': 427, 'QUIC': 443,
}

PORT_TO_PROTOCOL = {port: protocol for protocol, port in STANDARD_PORTS.items()}

APPLICATION_PROTOCOLS = set()
for category_services in SERVICE_CATEGORIES.values():
    for service_config in category_services.values():
        APPLICATION_PROTOCOLS.update(service_config['protocols'])

def classify_service_by_business_function(protocol: str, port: int, bytes_in: int, bytes_out: int) -> Tuple[str, str, str]:
    """Enhanced service classification with archetype awareness"""
    protocol_upper = str(protocol).upper().strip() if protocol else ''
    port_int = int(port) if port and str(port).strip().isdigit() else 0
    
    best_score = 0
    best_category = 'UNKNOWN'
    best_service = 'unknown'
    best_description = 'Unclassified service'
    
    for category, services in SERVICE_CATEGORIES.items():
        for service_type, config in services.items():
            score = 0
            
            # Protocol matches (higher weight)
            if protocol_upper in config['protocols']:
                score += 10 * config['priority']
            
            # Port matches
            if port_int in config['ports']:
                score += 5 * config['priority']
            
            # Enhanced scoring based on traffic patterns and archetype hints
            if category == 'APPLICATION' and (bytes_in + bytes_out) > 10000:
                score += 2
            
            if category == 'DATA' and bytes_out > bytes_in * 2:
                score += 3
            
            # Microservice port range bonus
            if service_type == 'microservice' and 3000 <= port_int <= 3100:
                score += 8
            
            # Database concentration bonus
            if category == 'DATA' and port_int in [3306, 5432, 1433, 1521, 27017]:
                score += 5
            
            if score > best_score:
                best_score = score
                best_category = category
                best_service = service_type
                best_description = config['description']
    
    return best_category, best_service, best_description

def is_application_protocol(protocol: str) -> bool:
    """Check if protocol is application-specific"""
    if not protocol:
        return False
    protocol_upper = protocol.upper().strip()
    return protocol_upper in APPLICATION_PROTOCOLS

def infer_port_from_protocol(protocol: str) -> Optional[int]:
    """Get standard port for a given protocol"""
    if not protocol:
        return None
    protocol_upper = protocol.upper().strip()
    return STANDARD_PORTS.get(protocol_upper)

def infer_protocol_from_port(port: int) -> Optional[str]:
    """Get protocol for a given port number"""
    if not port or port == 0:
        return None
    return PORT_TO_PROTOCOL.get(port)

def has_traffic_activity(bytes_in: int, bytes_out: int) -> bool:
    """Check if there's actual network traffic activity"""
    try:
        bytes_in_val = int(bytes_in) if bytes_in is not None else 0
        bytes_out_val = int(bytes_out) if bytes_out is not None else 0
        return bytes_in_val > 0 or bytes_out_val > 0
    except (ValueError, TypeError):
        return False

def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except Exception:
        return False

def is_hostname_like(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s = s.strip()
    if not s or len(s) < 2:
        return False
    if is_ip(s):
        return False
    return bool(HOSTLIKE_RE.search(s))

def split_peer(peer_text: str) -> Tuple[str, Optional[str]]:
    if not isinstance(peer_text, str):
        return str(peer_text), None
    m = PEER_RE.match(peer_text.strip())
    if not m:
        return peer_text.strip(), None
    return m.group(1).strip(), (m.group(2).strip() if m.group(2) else None)

def parse_proto_port(s: str) -> Tuple[Optional[str], Optional[int]]:
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return None, None
    s = str(s).strip()
    if ":" in s:
        proto, port = s.split(":", 1)
        proto = proto.strip().upper()
        port = port.strip()
        try:
            return proto, int(port)
        except Exception:
            return proto, None
    return (s.upper() if s else None), None

def reverse_dns_socket(ip: str, timeout: float = 0.75) -> Optional[str]:
    try:
        socket.setdefaulttimeout(timeout)
        name, _, _ = socket.gethostbyaddr(ip)
        return name.rstrip(".")
    except Exception:
        return None

def reverse_dns_nslookup(ip: str, timeout: float = 1.5) -> Optional[str]:
    try:
        proc = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=timeout, check=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            L = line.strip()
            low = L.lower()
            if "name =" in low:
                host = L.split("=", 1)[1].strip().rstrip(".")
                return host
            if low.startswith("name:"):
                host = L.split(":", 1)[1].strip().rstrip(".")
                return host
        return None
    except Exception:
        return None

def forward_dns_socket(hostname: str, timeout: float = 0.75) -> Optional[str]:
    try:
        socket.setdefaulttimeout(timeout)
        ip = socket.gethostbyname(hostname)
        return ip
    except Exception:
        return None

def forward_dns_nslookup(hostname: str, timeout: float = 1.5) -> Optional[str]:
    try:
        proc = subprocess.run(["nslookup", hostname], capture_output=True, text=True, timeout=timeout, check=False)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in text.splitlines():
            L = line.strip()
            if "Address:" in L and "#" not in L:  # Skip the DNS server address line
                parts = L.split("Address:")
                if len(parts) > 1:
                    ip = parts[1].strip()
                    if is_ip(ip):
                        return ip
        return None
    except Exception:
        return None

def find_col(df: pd.DataFrame, name_opts: Iterable[str]) -> Optional[str]:
    norm = {str(c).strip().lower(): c for c in df.columns}
    for opt in name_opts:
        if opt in norm:
            return norm[opt]
    return None

def load_frame(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input not found: {p}")
    
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=sheet) if sheet else pd.read_excel(p)
    else:
        return pd.read_csv(p)

def save_to_staging(df: pd.DataFrame, filename: str, data_staging_dir: str = "data_staging"):
    staging_path = Path(data_staging_dir)
    staging_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(filename).stem
    
    if base_name.startswith("App_Code_"):
        clean_name = base_name.replace("App_Code_", "", 1)
        csv_filename = f"{clean_name}_normalized_{timestamp}.csv"
        xlsx_filename = f"{clean_name}_normalized_{timestamp}.xlsx"
    else:
        clean_name = base_name
        csv_filename = f"{clean_name}_normalized_{timestamp}.csv"
        xlsx_filename = f"{clean_name}_normalized_{timestamp}.xlsx"
        
    csv_path = staging_path / csv_filename
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    try:
        xlsx_path = staging_path / xlsx_filename
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="CompleteNetworkAnalysis", index=False)
        print(f"Saved Excel: {xlsx_path}")
    except Exception as e:
        print(f"Warning: Could not save Excel file: {e}")
    
    return csv_path

def perform_reverse_dns(ips: List[str], args) -> Dict[str, Optional[str]]:
    """Perform reverse DNS lookups"""
    rev_map: Dict[str, Optional[str]] = {}
    
    def rev_lookup(ip: str) -> Tuple[str, Optional[str]]:
        name: Optional[str] = None
        if args.dns in ("socket", "both"):
            name = reverse_dns_socket(ip, timeout=args.timeout)
        if not name and args.dns in ("nslookup", "both"):
            name = reverse_dns_nslookup(ip, timeout=max(args.timeout, 1.0))
        return ip, name

    with ThreadPoolExecutor(max_workers=max(1, args.threads)) as ex:
        futs = [ex.submit(rev_lookup, ip) for ip in ips]
        for fut in as_completed(futs):
            ip, name = fut.result()
            rev_map[ip] = name

    return rev_map

def perform_forward_dns(hostnames: List[str], args) -> Dict[str, Optional[str]]:
    """Perform forward DNS lookups (hostname -> IP)"""
    forward_map: Dict[str, Optional[str]] = {}
    
    def forward_lookup(hostname: str) -> Tuple[str, Optional[str]]:
        ip: Optional[str] = None
        if args.dns in ("socket", "both"):
            ip = forward_dns_socket(hostname, timeout=args.timeout)
        if not ip and args.dns in ("nslookup", "both"):
            ip = forward_dns_nslookup(hostname, timeout=max(args.timeout, 1.0))
        return hostname, ip

    with ThreadPoolExecutor(max_workers=max(1, args.threads)) as ex:
        futs = [ex.submit(forward_lookup, hostname) for hostname in hostnames]
        for fut in as_completed(futs):
            hostname, ip = fut.result()
            forward_map[hostname] = ip

    return forward_map

def process_network_edges_complete(df_in: pd.DataFrame, args, input_path: Path) -> pd.DataFrame:
    """Complete network processing with service classification and archetype mapping"""
    print("Processing network data with complete service classification and archetype mapping...")
    
    # Column mapping
    ip_col = find_col(df_in, {"ip", "source ip", "src", "source"})
    peer_col = find_col(df_in, {"peer", "destination", "dest", "dst", "dest ip"})
    proto_col = find_col(df_in, {"protocol", "proto"})
    bytes_in_col = find_col(df_in, {"bytes in", "bytes_in", "inbytes", "in bytes"})
    bytes_out_col = find_col(df_in, {"bytes out", "bytes_out", "outbytes", "out bytes"})
    app_col = find_col(df_in, {"app", "application", "app_name"})

    if not ip_col or not peer_col:
        raise ValueError("Input must contain 'IP' (or Source) and 'Peer' (or Dest) columns.")

    # Initialize variables outside the loop
    rev_need: set[str] = set()  # IPs needing hostnames
    forward_need: set[str] = set()  # Hostnames needing IPs
    parsed_rows: List[Dict[str, object]] = []
    service_classifications: Dict[str, Tuple[str, str]] = {}
    filtered_count = 0

    # Process each row
    for _, r in df_in.iterrows():
        src_raw = str(r.get(ip_col, "")).strip()
        peer_raw = str(r.get(peer_col, "")).strip()
        app_name = str(r.get(app_col, "")).strip() if app_col else ""
        
        if not app_name:
            raw_name = input_path.stem.replace("template-", "").replace("App_Code_", "").replace("_", " ")
            app_name = raw_name.strip()
            if not app_name or app_name.lower() in ['template', 'data', 'traffic']:
                app_name = "NetworkApp"

        peer_first, peer_host_paren = split_peer(peer_raw)
        src_ip = src_raw if is_ip(src_raw) else ""
        src_host_initial = "" if src_ip else (src_raw if is_hostname_like(src_raw) else "")

        dest_ip_candidate = peer_first
        if is_ip(dest_ip_candidate):
            dest_ip = dest_ip_candidate
            dest_host_initial = (peer_host_paren or "")
        else:
            dest_ip = ""
            dest_host_initial = (peer_host_paren or (dest_ip_candidate if is_hostname_like(dest_ip_candidate) else ""))

        if not src_ip and not dest_ip and not src_host_initial and not dest_host_initial:
            filtered_count += 1
            continue

        proto_val = r.get(proto_col, None)
        proto, port = parse_proto_port(str(proto_val) if proto_val is not None else "")

        def to_int(v):
            try:
                return int(v) if v is not None else 0
            except:
                return 0

        bytes_in = to_int(r.get(bytes_in_col, 0) if bytes_in_col else 0)
        bytes_out = to_int(r.get(bytes_out_col, 0) if bytes_out_col else 0)

        # Apply filters
        if not args.include_zero_traffic and not has_traffic_activity(bytes_in, bytes_out):
            filtered_count += 1
            continue

        # Port/protocol inference
        if not args.no_port_inference:
            if not port and proto:
                inferred_port = infer_port_from_protocol(proto)
                if inferred_port:
                    port = inferred_port
            if not proto and port:
                inferred_proto = infer_protocol_from_port(port)
                if inferred_proto:
                    proto = inferred_proto

        # Protocol filtering
        if not args.include_all_protocols:
            if proto and not is_application_protocol(proto):
                filtered_count += 1
                continue
            if not proto:
                filtered_count += 1
                continue

        # Enhanced service classification
        service_category, service_type, business_function = classify_service_by_business_function(
            proto, port, bytes_in, bytes_out
        )

        # Store service classification for destination
        dest_key = dest_ip or dest_host_initial
        if dest_key:
            service_classifications[dest_key] = (service_category, service_type)

        row = {
            "application": app_name,
            "source_ip": src_ip,
            "source_hostname": src_host_initial,
            "destination_ip": dest_ip,
            "destination_hostname": dest_host_initial,
            "port": (port if port is not None else ""),
            "protocol": (proto or ""),
            "bytes_in": bytes_in,
            "bytes_out": bytes_out,
            "timestamp": datetime.now().isoformat(),
            "behavior": "Network",
            "info": f"{proto}:{port}" if proto and port else (proto or ""),
            "service_category": service_category,
            "service_type": service_type,
            "business_function": business_function
        }
        parsed_rows.append(row)

        # Collect DNS lookup requirements
        if args.dns != "none":
            # Collect IPs that need reverse DNS (IP -> hostname)
            if row["source_ip"] and not row["source_hostname"]:
                rev_need.add(row["source_ip"])
            if row["destination_ip"] and not row["destination_hostname"]:
                rev_need.add(row["destination_ip"])
            
            # Collect hostnames that need forward DNS (hostname -> IP)
            if row["source_hostname"] and not row["source_ip"]:
                forward_need.add(row["source_hostname"])
            if row["destination_hostname"] and not row["destination_ip"]:
                forward_need.add(row["destination_hostname"])

    print(f"Filtered out {filtered_count} rows")

    # DNS lookups (after row processing)
    dns_results = {}

    if (rev_need or forward_need) and args.dns != "none":
        total_lookups = len(rev_need) + len(forward_need)
        print(f"Performing {len(rev_need)} reverse DNS and {len(forward_need)} forward DNS lookups ({total_lookups} total)...")
        
        # Reverse DNS lookups (IP -> hostname)
        if rev_need:
            rev_map = perform_reverse_dns(list(rev_need), args)
            dns_results.update(rev_map)
        
        # Forward DNS lookups (hostname -> IP)  
        if forward_need:
            forward_map = perform_forward_dns(list(forward_need), args)
            dns_results.update(forward_map)
        
        # Apply results to rows
        for row in parsed_rows:
            # Apply reverse DNS results
            if row["source_ip"] and not row["source_hostname"]:
                row["source_hostname"] = dns_results.get(row["source_ip"], "") or ""
            if row["destination_ip"] and not row["destination_hostname"]:
                row["destination_hostname"] = dns_results.get(row["destination_ip"], "") or ""
            
            # Apply forward DNS results
            if row["source_hostname"] and not row["source_ip"]:
                row["source_ip"] = dns_results.get(row["source_hostname"], "") or ""
            if row["destination_hostname"] and not row["destination_ip"]:
                row["destination_ip"] = dns_results.get(row["destination_hostname"], "") or ""

    # Deduplication process
    print(f"Total parsed rows before deduplication: {len(parsed_rows)}")

    # Check for large datasets
    if len(parsed_rows) > 100000:
        print(f"Large dataset detected ({len(parsed_rows):,} rows), using memory-efficient processing...")

    # Convert to DataFrame for efficient deduplication
    temp_df = pd.DataFrame(parsed_rows)

    # Define key columns for deduplication (connection + protocol + application)
    dedup_columns = [
        'application', 'source_ip', 'source_hostname', 
        'destination_ip', 'destination_hostname', 'protocol', 'port'
    ]

    # Keep first occurrence, sum traffic bytes for duplicates
    if len(temp_df) > 0:
        # Check for missing columns before groupby
        available_columns = [col for col in dedup_columns if col in temp_df.columns]
        if len(available_columns) < len(dedup_columns):
            missing = set(dedup_columns) - set(available_columns)
            print(f"Warning: Missing columns for dedup: {missing}")
            dedup_columns = available_columns
        
        # Define aggregation dictionary
        agg_dict = {
            'bytes_in': 'sum',
            'bytes_out': 'sum',
            'timestamp': 'first',
            'behavior': 'first',
            'info': 'first',
            'service_category': 'first',
            'service_type': 'first',
            'business_function': 'first'
        }
        
        # Add archetype if it exists
        if 'archetype' in temp_df.columns:
            agg_dict['archetype'] = 'first'
        
        # Group by connection details and aggregate traffic
        grouped = temp_df.groupby(dedup_columns, as_index=False).agg(agg_dict)
        
        parsed_rows = grouped.to_dict('records')
        duplicates_removed = len(temp_df) - len(parsed_rows)
        print(f"Rows after deduplication: {len(parsed_rows)} (removed {duplicates_removed:,} duplicates)")
    else:
        print("No data to deduplicate")

    result_df = pd.DataFrame(parsed_rows)

    if len(result_df) > 0:
        print("\nService Category Distribution:")
        category_counts = result_df['service_category'].value_counts()
        for category, count in category_counts.items():
            percentage = (count / len(result_df)) * 100
            print(f"  {category}: {count} records ({percentage:.1f}%)")

    # Apply enhanced archetype mapping using YAML templates
    if len(result_df) > 0:
        result_df = apply_enhanced_archetype_mapping(result_df, service_classifications)

    return result_df

def synthesize_additional_records(df: pd.DataFrame, target_count: int) -> pd.DataFrame:
    """Enhanced synthesis maintaining archetype distribution"""
    if len(df) >= target_count:
        return df
    
    print(f"Synthesizing additional records to reach {target_count} total records...")
    
    # Analyze existing distributions
    if len(df) > 0:
        category_dist = df['service_category'].value_counts(normalize=True)
        archetype_dist = df['archetype'].value_counts(normalize=True)
    else:
        category_dist = pd.Series({'APPLICATION': 0.4, 'DATA': 0.3, 'SECURITY': 0.1, 'INFRASTRUCTURE': 0.2})
        archetype_dist = pd.Series({'3-Tier': 0.3, 'Microservices': 0.2, 'Database-Centric': 0.15})
    
    synthetic_records = []
    records_needed = target_count - len(df)
    
    for i in range(records_needed):
        # Select archetype based on existing distribution
        archetype = np.random.choice(archetype_dist.index, p=archetype_dist.values)
        archetype_config = ARCHETYPE_TEMPLATES.get(archetype, ARCHETYPE_TEMPLATES['3-Tier'])
        
        # Generate synthetic data consistent with archetype
        protocol = np.random.choice(archetype_config.get('protocols', ['HTTP']))
        port = np.random.choice(archetype_config.get('typical_ports', [8080]))
        
        src_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        dest_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        
        service_category, service_type, business_function = classify_service_by_business_function(
            protocol, port, random.randint(1000, 100000), random.randint(1000, 100000)
        )
        
        synthetic_record = {
            "application": f"SyntheticApp_{i}",
            "source_ip": src_ip,
            "source_hostname": "",
            "destination_ip": dest_ip,
            "destination_hostname": "",
            "port": port,
            "protocol": protocol,
            "bytes_in": random.randint(1000, 100000),
            "bytes_out": random.randint(1000, 100000),
            "timestamp": datetime.now().isoformat(),
            "behavior": "Synthetic",
            "info": f"{protocol}:{port}",
            "service_category": service_category,
            "service_type": service_type,
            "business_function": business_function,
            "archetype": archetype
        }
        synthetic_records.append(synthetic_record)
    
    synthetic_df = pd.DataFrame(synthetic_records)
    return pd.concat([df, synthetic_df], ignore_index=True)

def main():
    parser = argparse.ArgumentParser(description="Complete data preparation pipeline with YAML archetype templates")
    
    # Input/Output arguments
    parser.add_argument("--input", "-i", required=True, help="Path to input file (.xlsx, .csv)")
    parser.add_argument("--sheet", help="Excel sheet name (if applicable)")
    parser.add_argument("--data-dir", default="data", help="Input data directory")
    parser.add_argument("--staging-dir", default="data_staging", help="Output staging directory")
    
    # Processing options
    parser.add_argument("--no-synthesize", action="store_true", help="Do not synthesize additional records")
    parser.add_argument("--min-rows", type=int, default=5000, help="Minimum number of rows to generate")
    parser.add_argument("--keep-blank-rows", action="store_true", help="Keep blank rows in input data")
    parser.add_argument("--include-zero-traffic", action="store_true", help="Include rows with zero traffic")
    parser.add_argument("--include-all-protocols", action="store_true", help="Include non-application protocols")
    parser.add_argument("--no-port-inference", action="store_true", help="Don't infer missing ports")
    
    # Service classification options
    parser.add_argument("--show-service-stats", action="store_true", help="Show detailed service statistics")
    parser.add_argument("--category-filter", help="Filter to specific service category")
    parser.add_argument("--show-archetype-details", action="store_true", help="Show detailed archetype analysis")
    
    # DNS options
    parser.add_argument("--dns", choices=["none", "socket", "nslookup", "both"], default="socket")
    parser.add_argument("--timeout", type=float, default=0.75, help="DNS timeout (seconds)")
    parser.add_argument("--threads", type=int, default=20, help="DNS lookup threads")
    
    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = Path(args.data_dir) / input_path
        
        print(f"Loading data from: {input_path}")
        df_input = load_frame(input_path, args.sheet)
        print(f"Loaded {len(df_input)} rows, {len(df_input.columns)} columns")
        
        # Remove blank rows
        if not args.keep_blank_rows:
            initial_rows = len(df_input)
            df_input = df_input.dropna(how='all')
            df_input = df_input[df_input.astype(str).ne('').any(axis=1)]
            df_input = df_input.reset_index(drop=True)
            
            rows_removed = initial_rows - len(df_input)
            if rows_removed > 0:
                print(f"Removed {rows_removed} blank rows")
        
        if args.verbose:
            print(f"Columns: {list(df_input.columns)}")
            print(f"Sample data:\n{df_input.head()}")
        
        # Complete processing with archetype mapping
        df_processed = process_network_edges_complete(df_input, args, input_path)
        print(f"Processed {len(df_processed)} network edge records")
        
        # Filter by category if requested
        if args.category_filter:
            category_filter = args.category_filter.upper()
            initial_count = len(df_processed)
            df_processed = df_processed[df_processed['service_category'] == category_filter]
            print(f"Filtered to {category_filter} services: {len(df_processed)} records (was {initial_count})")
        
        # Show detailed service statistics
        if args.show_service_stats and len(df_processed) > 0:
            print("\n" + "="*60)
            print("DETAILED SERVICE CLASSIFICATION STATISTICS")
            print("="*60)
            
            for category in sorted(df_processed['service_category'].unique()):
                category_data = df_processed[df_processed['service_category'] == category]
                print(f"\n{category} SERVICES ({len(category_data)} records):")
                
                service_type_counts = category_data['service_type'].value_counts()
                for service_type, count in service_type_counts.items():
                    percentage = (count / len(category_data)) * 100
                    
                    # Get description from SERVICE_CATEGORIES
                    description = "Unknown service type"
                    if category in SERVICE_CATEGORIES and service_type in SERVICE_CATEGORIES[category]:
                        description = SERVICE_CATEGORIES[category][service_type]['description']
                    
                    print(f"  • {service_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
                    print(f"    {description}")
                    
                    # Show archetype hints
                    if category in SERVICE_CATEGORIES and service_type in SERVICE_CATEGORIES[category]:
                        hints = SERVICE_CATEGORIES[category][service_type].get('archetype_hints', [])
                        if hints:
                            print(f"    Suggested archetypes: {', '.join(hints[:3])}")
                    print()
        
        # Show detailed archetype analysis
        if args.show_archetype_details and len(df_processed) > 0:
            print("\n" + "="*60)
            print("DETAILED ARCHETYPE ANALYSIS")
            print("="*60)
            
            archetype_counts = df_processed['archetype'].value_counts()
            for archetype, count in archetype_counts.items():
                percentage = (count / len(df_processed)) * 100
                details = get_archetype_details(archetype)
                
                print(f"\n{archetype.upper()}: {count} records ({percentage:.1f}%)")
                print(f"Description: {details.get('description', 'No description available')}")
                print(f"Traffic Pattern: {details.get('traffic_pattern', 'Unknown')}")
                
                indicators = details.get('indicators', [])
                if indicators:
                    print(f"Key Indicators: {', '.join(indicators[:5])}")
                
                typical_ports = details.get('typical_ports', [])
                if typical_ports:
                    print(f"Typical Ports: {', '.join(map(str, typical_ports[:10]))}")
                
                # Show applications using this archetype
                archetype_apps = df_processed[df_processed['archetype'] == archetype]['application'].unique()
                if len(archetype_apps) <= 5:
                    print(f"Applications: {', '.join(archetype_apps)}")
                else:
                    print(f"Applications: {', '.join(archetype_apps[:5])} ... and {len(archetype_apps)-5} more")
        
        # Synthesize additional records if needed
        if not args.no_synthesize and len(df_processed) < args.min_rows:
            df_processed = synthesize_additional_records(df_processed, args.min_rows)
            print(f"Total records after synthesis: {len(df_processed)}")
        
        # Save to staging directory
        input_stem = input_path.stem
        if input_stem.startswith("App_Code_"):
            clean_name = input_stem.replace("App_Code_", "", 1)
            output_filename = f"{clean_name}_complete_archetype"
        else:
            output_filename = f"{input_path.stem}_complete_archetype"
            
        csv_path = save_to_staging(df_processed, output_filename, args.staging_dir)
        
        # Summary
        print(f"\nSUCCESS: Complete processing with YAML archetype templates completed successfully!")
        print(f"Output file: {csv_path}")
        print(f"Total records: {len(df_processed):,}")
        print(f"Service categories: {df_processed['service_category'].nunique()}")
        print(f"Service types: {df_processed['service_type'].nunique()}")
        print(f"Archetype patterns: {df_processed['archetype'].nunique()}")
        
        file_size = csv_path.stat().st_size / (1024 * 1024)
        print(f"File size: {file_size:.2f} MB")
        
        # Final archetype summary
        print(f"\nFINAL ARCHETYPE DISTRIBUTION:")
        archetype_counts = df_processed['archetype'].value_counts()
        for archetype, count in archetype_counts.items():
            percentage = (count / len(df_processed)) * 100
            print(f"  {archetype}: {count} records ({percentage:.1f}%)")
        
        if args.verbose:
            print(f"\nSample of complete enhanced data:")
            sample_cols = ['application', 'service_category', 'service_type', 'archetype', 'source_ip', 'destination_ip', 'protocol', 'port']
            available_cols = [col for col in sample_cols if col in df_processed.columns]
            print(df_processed[available_cols].head())
            
        print(f"\nComplete file ready for advanced topology analysis!")
        print(f"Next steps:")
        print(f"   1. Service topology: python enhanced_service_classification.py --input {csv_path}")
        print(f"   2. Advanced clustering: python advanced_topology_with_clustering.py --input {csv_path}")
        print(f"   3. Complete workflow: python integration_workflow.py --input {csv_path}")
        print(f"\nAvailable archetype patterns from YAML templates:")
        for archetype in sorted(ARCHETYPE_TEMPLATES.keys()):
            if archetype in df_processed['archetype'].values:
                print(f"   AVAILABLE: {archetype}")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())