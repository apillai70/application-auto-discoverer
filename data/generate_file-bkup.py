#!/usr/bin/env python3
"""
generate.py - Combined Data Preparation Pipeline

Combines functionality from:
1. generate_file.py - Archetype mapping and refinement
2. build_edges.py - Network edge processing with DNS resolution

Processes raw network data files and creates properly formatted CSV files
for the application auto-discovery pipeline.

Input: Raw network data files in /data folder
Output: Processed CSV files in /data_staging folder (excluding applicationList.csv)

Usage:
    python generate.py --input /data/raw_traffic.xlsx
    python generate.py --input /data/template_XECHK.csv --dns both --min-rows 10000
    python generate.py --input /data/network_data.csv --no-synthesize --archetype-mapping
"""

from __future__ import annotations
import argparse
import ipaddress
import math
import os
import random
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

# Set random seed for reproducible results
random.seed(42)
np.random.seed(42)

# =================== CONSTANTS ===================
PEER_RE = re.compile(r'^\s*([^\s(]+)\s*(?:\(([^)]+)\))?\s*$')
HOSTLIKE_RE = re.compile(r'^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+\.?$')

# =================== ARCHETYPE MAPPING ===================

def map_to_ideal_archetype(row):
    """
    Map original archetypes to ideal ones based on patterns
    Enhanced version with more sophisticated mapping logic
    """
    archetype = row.get('archetype', '')
    protocol = str(row.get('protocol', '')).upper()
    info = str(row.get('info', ''))
    behavior = str(row.get('behavior', ''))
    port = str(row.get('Port', '') or row.get('port', ''))
    
    # Enhanced mapping logic
    if archetype == '3-Tier':
        if protocol == 'SQL' or 'SQL' in info or port in ['3306', '5432', '1521', '1433']:
            return 'Database-Centric'
        elif behavior == 'API' or 'API' in info or port in ['8080', '3000', '8443']:
            return 'API-Centric (General)'
        elif 'Web' in info and 'DB' in info:
            return 'N-Tier Architecture'
        else:
            return '3-Tier'
    
    elif archetype == 'Web + API Headless':
        if behavior == 'API' or 'API' in info or port in ['8080', '3000', '8443']:
            return 'API-Centric (General)'
        else:
            return 'Web + API Headless'
    
    elif archetype == 'Monolithic':
        if protocol == 'TCP' and (port in ['3306', '5432', '1521', '1433'] or 'SQL' in info):
            return 'Database-Centric'
        else:
            return 'Monolithic'
    
    elif archetype == 'Client-Server':
        if 'RDP' in info or port == '3389':
            return 'Host-Terminal'
        else:
            return 'Client-Server'
    
    elif archetype == 'SOA':
        # 30% chance to map to message broker variant
        if random.random() < 0.3 or port in ['5672', '61616']:
            return 'SOA with Message Broker'
        else:
            return 'SOA'
    
    elif archetype == 'Microservices':
        if protocol == 'GRPC' or 'gRPC' in info or port in ['9090', '50051']:
            return 'Cloud-Native'
        else:
            return 'Microservices'
    
    elif archetype == 'Event-Driven':
        if protocol == 'AMQP' or port in ['5672', '9092', '61616']:
            return 'SOA with Message Broker'
        else:
            return 'Event-Driven'
    
    # Keep these as-is
    elif archetype in ['Edge+Cloud Hybrid', 'ETL/Data Pipeline', 'Serverless']:
        return archetype
    
    else:
        # Default archetype assignment based on protocol/port
        if port in ['3306', '5432', '1521', '1433'] or protocol == 'SQL':
            return 'Database-Centric'
        elif port in ['80', '443', '8080'] or protocol in ['HTTP', 'HTTPS']:
            return 'Web + API Headless'
        elif port in ['5672', '9092', '61616'] or protocol in ['AMQP', 'MQTT']:
            return 'Event-Driven'
        else:
            return '3-Tier'  # Default fallback

# =================== NETWORK UTILITIES ===================

def is_ip(s: str) -> bool:
    """Check if string is a valid IP address"""
    try:
        ipaddress.ip_address(s)
        return True
    except Exception:
        return False

def is_hostname_like(s: str) -> bool:
    """Check if string looks like a hostname"""
    if not isinstance(s, str):
        return False
    s = s.strip()
    if not s or len(s) < 2:
        return False
    if is_ip(s):
        return False
    return bool(HOSTLIKE_RE.search(s))

def split_peer(peer_text: str) -> Tuple[str, Optional[str]]:
    """Split '10.0.0.1(host.example)' -> ('10.0.0.1', 'host.example')"""
    if not isinstance(peer_text, str):
        return str(peer_text), None
    m = PEER_RE.match(peer_text.strip())
    if not m:
        return peer_text.strip(), None
    return m.group(1).strip(), (m.group(2).strip() if m.group(2) else None)

def parse_proto_port(s: str) -> Tuple[Optional[str], Optional[int]]:
    """Parse 'TCP:443' -> ('TCP', 443)"""
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

# =================== DNS UTILITIES ===================

def reverse_dns_socket(ip: str, timeout: float = 0.75) -> Optional[str]:
    """Reverse DNS lookup using socket"""
    try:
        socket.setdefaulttimeout(timeout)
        name, _, _ = socket.gethostbyaddr(ip)
        return name.rstrip(".")
    except Exception:
        return None

def reverse_dns_nslookup(ip: str, timeout: float = 1.5) -> Optional[str]:
    """Reverse DNS lookup using nslookup"""
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

def forward_dns_socket(name: str, timeout: float = 0.75) -> Tuple[List[str], List[str]]:
    """Forward DNS lookup using socket. Returns (ipv4_list, ipv6_list)"""
    v4, v6 = [], []
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(name, None, proto=socket.IPPROTO_TCP)
        for fam, _, _, _, sockaddr in infos:
            if fam == socket.AF_INET:
                ip = sockaddr[0]
                if ip not in v4:
                    v4.append(ip)
            elif fam == socket.AF_INET6:
                ip = sockaddr[0]
                if ip not in v6:
                    v6.append(ip)
    except Exception:
        pass
    return v4, v6

def pick_preferred(v4: List[str], v6: List[str], prefer: str = "ipv4") -> Optional[str]:
    """Pick preferred IP from lists"""
    prefer = (prefer or "ipv4").lower()
    if prefer == "ipv6":
        return (v6[0] if v6 else (v4[0] if v4 else None))
    if prefer == "any":
        return (v4[0] if v4 else (v6[0] if v6 else None))
    return (v4[0] if v4 else (v6[0] if v6 else None))

# =================== FILE I/O UTILITIES ===================

def find_col(df: pd.DataFrame, name_opts: Iterable[str]) -> Optional[str]:
    """Find column by name options (case-insensitive)"""
    norm = {str(c).strip().lower(): c for c in df.columns}
    for opt in name_opts:
        if opt in norm:
            return norm[opt]
    return None

def load_frame(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    """Load DataFrame from Excel or CSV file"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input not found: {p}")
    
    if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(p, sheet_name=sheet) if sheet else pd.read_excel(p)
    else:
        return pd.read_csv(p)

def save_to_staging(df: pd.DataFrame, filename: str, data_staging_dir: str = "data_staging"):
    """Save DataFrame to data_staging directory"""
    staging_path = Path(data_staging_dir)
    staging_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(filename).stem
    
    #Custom naming logic: remove "App_Code_" prefix if present
    if base_name.startswith("App_Code_"):
        clean_name = base_name.replace("App_Code_", "", 1) # Remove first occurance
        csv_filename = f"{base_name}_normalized_{timestamp}.csv"
        xlsx_filename = f"{base_name}_normalized_{timestamp}.xlsx"
    else:
        csv_filename = f"{base_name}_{timestamp}.csv"
        xlsx_filename = f"{base_name}_{timestamp}.xlsx"
        
    csv_path = staging_path / csv_filename
    xlsx_path = staging_path / xlsx_filename
    
    # Save CSV
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    # Also save Excel if requested
    try:
        xlsx_filename = f"{base_name}_{timestamp}.xlsx"
        xlsx_path = staging_path / xlsx_filename
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="NetworkData", index=False)
        print(f"Saved Excel: {xlsx_path}")
    except Exception as e:
        print(f"Warning: Could not save Excel file: {e}")
    
    return csv_path

# =================== MAIN PROCESSING FUNCTIONS ===================

def process_network_edges(df_in: pd.DataFrame, args, input_path: Path) -> pd.DataFrame:
    """Process network edge data (from build_edges.py functionality)"""
    print("Processing network edge data...")
    
    # Map columns (case-insensitive)
    ip_col = find_col(df_in, {"ip", "source ip", "src", "source"})
    peer_col = find_col(df_in, {"peer", "destination", "dest", "dst", "dest ip"})
    proto_col = find_col(df_in, {"protocol", "proto"})
    bytes_in_col = find_col(df_in, {"bytes in", "bytes_in", "inbytes", "in bytes"})
    bytes_out_col = find_col(df_in, {"bytes out", "bytes_out", "outbytes", "out bytes"})
    app_col = find_col(df_in, {"app", "application", "app_name"})

    if not ip_col or not peer_col:
        raise ValueError("Input must contain 'IP' (or Source) and 'Peer' (or Dest) columns.")

    # Collect DNS lookup needs
    rev_need: set[str] = set()
    fwd_need: set[str] = set()
    parsed_rows: List[Dict[str, object]] = []

    for _, r in df_in.iterrows():
        src_raw = str(r.get(ip_col, "")).strip()
        peer_raw = str(r.get(peer_col, "")).strip()
        app_name = str(r.get(app_col, "")).strip() if app_col else ""
        if not app_name:
            # Extract app name from input filename
            raw_name = input_path.stem.replace("template-", "").replace("App_Code_", "").replace("_", " ")
            # Preserve original case instead of using .title() which lowercases everything
            app_name = raw_name.strip()
            if not app_name or app_name.lower() in ['template', 'data', 'traffic']:
                app_name = "NetworkApp"

        # Parse peer information
        peer_first, peer_host_paren = split_peer(peer_raw)

        # Source IP/hostname handling
        src_ip = src_raw if is_ip(src_raw) else ""
        src_host_initial = "" if src_ip else (src_raw if is_hostname_like(src_raw) else "")

        # Destination IP/hostname handling
        dest_ip_candidate = peer_first
        if is_ip(dest_ip_candidate):
            dest_ip = dest_ip_candidate
            dest_host_initial = (peer_host_paren or "")
        else:
            dest_ip = ""
            dest_host_initial = (peer_host_paren or (dest_ip_candidate if is_hostname_like(dest_ip_candidate) else ""))

        # Skip rows without usable identifiers
        if not src_ip and not dest_ip and not src_host_initial and not dest_host_initial:
            continue

        # Protocol/Port parsing
        proto_val = r.get(proto_col, None)
        proto, port = parse_proto_port(str(proto_val) if proto_val is not None else "")

        # Bytes handling
        def to_int(v):
            try:
                return int(v) if v is not None else 0
            except:
                return 0

        bytes_in = to_int(r.get(bytes_in_col, 0) if bytes_in_col else 0)
        bytes_out = to_int(r.get(bytes_out_col, 0) if bytes_out_col else 0)

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
        }
        parsed_rows.append(row)

        # Collect DNS lookup needs
        if row["source_ip"] and not row["source_hostname"] and args.dns != "none":
            rev_need.add(row["source_ip"])
        if row["destination_ip"] and not row["destination_hostname"] and args.dns != "none":
            rev_need.add(row["destination_ip"])

    # Perform DNS lookups if enabled
    if rev_need and args.dns != "none":
        print(f"Performing reverse DNS lookups for {len(rev_need)} IPs...")
        rev_map = perform_reverse_dns(list(rev_need), args)
        
        # Apply reverse DNS results
        for row in parsed_rows:
            if row["source_ip"] and not row["source_hostname"]:
                row["source_hostname"] = rev_map.get(row["source_ip"], "") or ""
            if row["destination_ip"] and not row["destination_hostname"]:
                row["destination_hostname"] = rev_map.get(row["destination_ip"], "") or ""

    return pd.DataFrame(parsed_rows)

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

def apply_archetype_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Apply archetype mapping and enrichment"""
    print("Applying archetype mapping...")
    
    if 'archetype' not in df.columns:
        # Assign default archetype based on available data
        df['archetype'] = df.apply(lambda row: infer_archetype_from_data(row), axis=1)
    
    # Apply archetype mapping
    df['archetype'] = df.apply(map_to_ideal_archetype, axis=1)
    
    return df

def infer_archetype_from_data(row) -> str:
    """Infer archetype from network data when not provided"""
    protocol = str(row.get('protocol', '')).upper()
    port = str(row.get('port', ''))
    behavior = str(row.get('behavior', ''))
    
    # Basic inference rules
    if protocol == 'SQL' or port in ['3306', '5432', '1521', '1433']:
        return 'Database-Centric'
    elif port in ['80', '443'] or protocol in ['HTTP', 'HTTPS']:
        return 'Web + API Headless'
    elif port in ['8080', '3000', '8443'] or 'API' in behavior:
        return 'API-Centric (General)'
    elif port in ['5672', '9092', '61616'] or protocol in ['AMQP', 'MQTT']:
        return 'Event-Driven'
    elif protocol == 'GRPC' or port in ['9090', '50051']:
        return 'Microservices'
    else:
        return '3-Tier'

def synthesize_additional_records(df: pd.DataFrame, target_count: int) -> pd.DataFrame:
    """Add synthetic records to reach target count"""
    if len(df) >= target_count:
        return df
    
    print(f"Synthesizing additional records to reach {target_count} total records...")
    
    # Create synthetic records based on existing patterns
    synthetic_records = []
    protocols = ['TCP', 'UDP', 'HTTP', 'HTTPS', 'SQL', 'GRPC', 'AMQP']
    ports = [22, 53, 80, 123, 161, 389, 443, 3306, 5432, 8080, 8443, 9090]
    
    while len(df) + len(synthetic_records) < target_count:
        src_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        dest_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        protocol = random.choice(protocols)
        port = random.choice(ports)
        
        synthetic_record = {
            "application": f"SyntheticApp_{len(synthetic_records)}",
            "source_ip": src_ip,
            "source_hostname": "",
            "destination_ip": dest_ip,
            "destination_hostname": "",
            "port": port,
            "protocol": protocol,
            "bytes_in": random.randint(1000, 1000000),
            "bytes_out": random.randint(1000, 1000000),
            "timestamp": datetime.now().isoformat(),
            "behavior": "Synthetic",
            "info": f"{protocol}:{port}",
            "archetype": infer_archetype_from_data({"protocol": protocol, "port": port, "behavior": "Synthetic"})
        }
        synthetic_records.append(synthetic_record)
    
    synthetic_df = pd.DataFrame(synthetic_records)
    return pd.concat([df, synthetic_df], ignore_index=True)

# =================== MAIN FUNCTION ===================

def main():
    parser = argparse.ArgumentParser(description="Combined data preparation pipeline for network auto-discovery")
    
    # Input/Output arguments
    parser.add_argument("--input", "-i", required=True, help="Path to input file (.xlsx, .csv)")
    parser.add_argument("--sheet", help="Excel sheet name (if applicable)")
    parser.add_argument("--data-dir", default="data", help="Input data directory")
    parser.add_argument("--staging-dir", default="data_staging", help="Output staging directory")
    
    # Processing options
    parser.add_argument("--archetype-mapping", action="store_true", default=True, help="Apply archetype mapping")
    parser.add_argument("--no-synthesize", action="store_true", help="Do not synthesize additional records")
    parser.add_argument("--min-rows", type=int, default=5000, help="Minimum number of rows to generate")
    parser.add_argument("--keep-blank-rows", action="store_true", help="Keep blank rows in input data")er.add_argument("--min-rows", type=int, default=5000, help="Minimum number of rows to generate")
    
    # DNS options
    parser.add_argument("--dns", choices=["none", "socket", "nslookup", "both"], default="socket",
                        help="Reverse DNS method")
    parser.add_argument("--timeout", type=float, default=0.75, help="DNS timeout (seconds)")
    parser.add_argument("--threads", type=int, default=20, help="DNS lookup threads")
    
    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Load input data
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = Path(args.data_dir) / input_path
        
        print(f"Loading data from: {input_path}")
        df_input = load_frame(input_path, args.sheet)
        print(f"Loaded {len(df_input)} rows, {len(df_input.columns)} columns")
        
        # Remove blank rows before processing
        initial_rows = len(df_input)
        df_input = df_input.dropna(how='all')  # Remove rows where all values are NaN
        df_input = df_input[df_input.astype(str).ne('').any(axis=1)]  # Remove rows where all values are empty strings
        df_input = df_input.reset_index(drop=True)  # Reset index after dropping rows
        
        rows_removed = initial_rows - len(df_input)
        if rows_removed > 0:
            print(f"Removed {rows_removed} blank rows")
        print(f"Processing {len(df_input)} rows after cleanup")
        
        if args.verbose:
            print(f"Columns: {list(df_input.columns)}")
            print(f"Sample data:\n{df_input.head()}")
        
        # Process network edges - pass input_path as parameter
        df_processed = process_network_edges(df_input, args, input_path)
        print(f"Processed {len(df_processed)} network edge records")
        
        # Apply archetype mapping if enabled
        if args.archetype_mapping:
            df_processed = apply_archetype_mapping(df_processed)
            
            # Show archetype distribution
            print("\nArchetype Distribution:")
            archetype_counts = df_processed['archetype'].value_counts()
            for archetype, count in archetype_counts.items():
                percentage = (count / len(df_processed)) * 100
                print(f"  {archetype}: {count} records ({percentage:.1f}%)")
        
        # Synthesize additional records if needed
        if not args.no_synthesize and len(df_processed) < args.min_rows:
            df_processed = synthesize_additional_records(df_processed, args.min_rows)
            print(f"Total records after synthesis: {len(df_processed)}")
        
        # Save to staging directory
        input_stem = input_path.stem
        if input_stem.startswith("App_Code_"):
            clean_name = input_stem.replace("App_Code_", "", 1)
            output_filename = f"{clean_name}_normalized"
        else:
            output_filename = f"{input_path.stem}"
            
        csv_path = save_to_staging(df_processed, output_filename, args.staging_dir)
        
        # Summary
        print(f"\n✅ Processing completed successfully!")
        print(f"📄 Output file: {csv_path}")
        print(f"📊 Total records: {len(df_processed):,}")
        print(f"🗂️ Unique archetypes: {df_processed['archetype'].nunique()}")
        
        file_size = csv_path.stat().st_size / (1024 * 1024)
        print(f"💾 File size: {file_size:.2f} MB")
        
        if args.verbose:
            print(f"\nSample of final data:")
            sample_cols = ['application', 'archetype', 'source_ip', 'destination_ip', 'protocol', 'port']
            available_cols = [col for col in sample_cols if col in df_processed.columns]
            print(df_processed[available_cols].head())
            
        print(f"\n🎯 File ready for pipeline processing in {args.staging_dir}/")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())