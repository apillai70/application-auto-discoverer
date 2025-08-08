#!/usr/bin/env python3
"""
ACTIVnet File Processing System - Windows Compatible Version
Monitors data_staging folder, processes files, and appends to synthetic_flows_apps_archetype_mapped.xlsx
"""

import pandas as pd
import json
import os
import sys
import shutil
import time
import hashlib
from pathlib import Path
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from bs4 import BeautifulSoup
import threading
from typing import Dict, List, Set, Optional, Tuple
import argparse
from openpyxl import load_workbook
import tempfile

# Windows Unicode compatibility fix
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class SafeLogger:
    """Windows-safe logger that handles Unicode properly"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def _safe_message(self, msg):
        """Convert message to safe format for Windows console"""
        # Replace emoji with text equivalents
        emoji_map = {
            '✅': '[SUCCESS]',
            '❌': '[ERROR]',
            '🔄': '[PROCESSING]',
            '⚠️': '[WARNING]',
            '🆕': '[NEW]',
            '🔍': '[SCANNING]',
            '📁': '[FOLDER]',
            '📊': '[DATA]',
            '🌐': '[WEB]',
            '🎯': '[SYSTEM]',
            '🛑': '[STOP]'
        }
        
        safe_msg = str(msg)
        for emoji, replacement in emoji_map.items():
            safe_msg = safe_msg.replace(emoji, replacement)
        
        return safe_msg
    
    def info(self, msg):
        self.logger.info(self._safe_message(msg))
    
    def error(self, msg):
        self.logger.error(self._safe_message(msg))
    
    def warning(self, msg):
        self.logger.warning(self._safe_message(msg))
    
    def debug(self, msg):
        self.logger.debug(self._safe_message(msg))

class PortResearcher:
    """Port research functionality from the original transformer"""
    
    def __init__(self, cache_file='port_cache.json'):
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.well_known_ports = {
            7: "Echo Protocol", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 123: "NTP", 443: "HTTPS", 445: "SMB"
        }
        
        self.protocol_services = {
            "DNS": "Domain Name System", "HTTP": "HyperText Transfer Protocol",
            "HTTPS": "HTTP over SSL/TLS", "NTP": "Network Time Protocol",
            "CIFS": "Common Internet File System"
        }

    def load_cache(self):
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load cache: {e}")
        return {}

    def save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.warning(f"Could not save cache: {e}")

    def get_service_name(self, protocol, port, protocol_str):
        """Get service name with caching and research"""
        if protocol_str in self.protocol_services:
            return self.protocol_services[protocol_str]
        
        if port and port in self.well_known_ports:
            return self.well_known_ports[port]
        
        cache_key = f"{protocol}:{port}" if protocol and port else str(protocol_str)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # For unknown ports, create reasonable default and cache it
        default_service = f"Unknown {protocol} Service on port {port}" if protocol and port else f"Unknown Service ({protocol_str})"
        self.cache[cache_key] = default_service
        self.save_cache()
        
        return default_service

class FileProcessor:
    """
    Core file processing logic with web application directory integration
    """
    
    def __init__(self, project_root: Path):
        # Basic directory setup
        self.project_root = project_root
        self.staging_dir = project_root / "data_staging"
        self.processed_dir = self.staging_dir / "processed"
        self.failed_dir = self.staging_dir / "failed"
        
        # Web application directories - FIXED PATH ISSUE
        self.web_static_dir = project_root / "static" / "ui"
        self.web_js_dir = self.web_static_dir / "js"
        self.web_data_dir = self.web_static_dir / "data"
        self.web_templates_dir = self.web_static_dir / "templates"  # JSON files for web server
        self.templates_dir = project_root / "templates"  # Keep original for other templates
        
        # Target files - JSON goes in web-accessible location
        self.master_excel_file = self.web_data_dir / "synthetic_flows_apps_archetype_mapped.xlsx"
        self.json_data_file = self.web_templates_dir / "activnet_data.json"
        
        # Initialize collections
        self.data_hashes: Set[str] = set()
        self.processed_files: Dict[str, dict] = {}
        self.port_researcher = PortResearcher()
        
        # Ensure basic directories exist for logging
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Windows-safe logging
        self.setup_logging()
        self.logger = SafeLogger(__name__)
        
        # Create complete directory structure
        self.create_directory_structure()
        
        # Load existing hashes to prevent reprocessing
        self.load_processed_hashes()

    def setup_logging(self):
        """Setup Windows-compatible logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Create handlers with UTF-8 encoding
        log_file = self.staging_dir / 'processing.log'
        
        # File handler with UTF-8 encoding
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Setup root logger
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[file_handler, console_handler]
        )

    def create_directory_structure(self):
        """Create the required directory structure"""
        directories = [
            self.staging_dir,
            self.processed_dir,
            self.failed_dir,
            self.web_static_dir,
            self.web_js_dir,
            self.web_data_dir,
            self.web_templates_dir,  # Templates accessible by web server
            self.templates_dir       # Original templates directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Directory structure created/verified")
        self.logger.info(f"[WEB] JSON will be created at: {self.json_data_file}")

    def load_processed_hashes(self):
        """Load hashes of previously processed data to avoid duplicates"""
        hash_file = self.staging_dir / 'processed_hashes.json'
        try:
            if hash_file.exists():
                with open(hash_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.data_hashes = set(data.get('hashes', []))
                    self.processed_files = data.get('files', {})
                    self.logger.info(f"Loaded {len(self.data_hashes)} processed data hashes")
        except Exception as e:
            self.logger.warning(f"Could not load processed hashes: {e}")

    def save_processed_hashes(self):
        """Save hashes of processed data"""
        hash_file = self.staging_dir / 'processed_hashes.json'
        try:
            with open(hash_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'hashes': list(self.data_hashes),
                    'files': self.processed_files,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Could not save processed hashes: {e}")

    def calculate_data_hash(self, data: pd.DataFrame) -> str:
        """Calculate hash of DataFrame content for duplicate detection"""
        try:
            # Create a hash based on the data content
            data_str = data.to_string()
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating data hash: {e}")
            return ""

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported format"""
        supported_extensions = {'.csv', '.xlsx', '.xls', '.json'}
        return file_path.suffix.lower() in supported_extensions

    def load_data_from_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Load data from various file formats"""
        try:
            if file_path.suffix.lower() == '.csv':
                # Try different encodings for CSV files
                encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        return pd.read_csv(file_path, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                # If all encodings fail, try with error handling
                return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Try to find the right sheet
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                # Look for transformed/processed sheets first
                target_sheet = None
                for sheet in sheet_names:
                    if any(keyword in sheet.lower() for keyword in ['transformed', 'auto_research', 'processed', 'flows']):
                        target_sheet = sheet
                        break
                
                # If no special sheet found, use the first one
                if not target_sheet:
                    target_sheet = sheet_names[0]
                
                self.logger.info(f"Loading Excel sheet: {target_sheet}")
                return pd.read_excel(file_path, sheet_name=target_sheet)
            
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(json_data, list):
                    return pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    if 'data' in json_data:
                        return pd.DataFrame(json_data['data'])
                    else:
                        return pd.DataFrame([json_data])
                        
        except Exception as e:
            self.logger.error(f"Error loading {file_path}: {e}")
            return None

    def validate_data_format(self, data: pd.DataFrame) -> Tuple[bool, str]:
        """Validate if the data has the expected format for ACTIVnet processing"""
        required_columns = ['src', 'dst', 'protocol']
        
        missing_required = [col for col in required_columns if col not in data.columns]
        
        if missing_required:
            return False, f"Missing required columns: {missing_required}"
        
        if len(data) == 0:
            return False, "Data file is empty"
        
        # Check for reasonable data
        if data['src'].isna().all() or data['dst'].isna().all():
            return False, "Source or destination data is all empty"
        
        self.logger.info(f"Data validation passed: {len(data)} rows, columns: {list(data.columns)}")
        return True, "Valid"

    def detect_and_transform_raw_data(self, data: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """
        Detect if this is raw ACTIVnet data and transform it to standard format
        """
        # Check if data looks like raw ACTIVnet format
        raw_columns = ['IP', 'Name', 'Peer', 'Protocol', 'Bytes In', 'Bytes Out', 'Application Name']
        
        if all(col in data.columns for col in raw_columns[:4]):  # Has core raw columns
            self.logger.info(f"Detected raw ACTIVnet format in {file_path.name}, transforming...")
            return self.transform_raw_activnet_data(data)
        
        # If already in processed format or other format, return as-is
        return data

    def transform_raw_activnet_data(self, df_original: pd.DataFrame) -> pd.DataFrame:
        """Transform raw ACTIVnet data to standard format"""
        transformed_data = []
        
        for index, row in df_original.iterrows():
            # Parse protocol and port
            protocol, port, protocol_str = self.parse_protocol_port(row.get('Protocol', ''))
            
            # Get service name
            service_name = self.port_researcher.get_service_name(protocol, port, protocol_str)
            
            # Extract destination IP
            dst_ip = self.extract_ip_from_peer(row.get('Peer', ''))
            
            # Create timestamp
            timestamp = int(datetime.now().timestamp())
            
            # Create transformed row matching the expected format
            transformed_row = {
                'src': row.get('IP', ''),
                'dst': dst_ip,
                'port': port if port else '',
                'tier': 'Service',
                'archetype': 'Network Service',
                'application': row.get('Application Name', 'Unknown') if pd.notna(row.get('Application Name')) else 'Unknown',
                'protocol': protocol if protocol else protocol_str,
                'timestamp': timestamp,
                'info': f"{service_name}",
                'behavior': 'Network Communication',
                'application_original': row.get('Application Name', 'Unknown') if pd.notna(row.get('Application Name')) else 'Unknown',
                'review_required': False,
                'is_known_app': 1 if pd.notna(row.get('Application Name')) else 0,
                'service_definition': service_name,
                'bytes_in': row.get('Bytes In', 0) if pd.notna(row.get('Bytes In')) else 0,
                'bytes_out': row.get('Bytes Out', 0) if pd.notna(row.get('Bytes Out')) else 0,
                'original_protocol': row.get('Protocol', ''),
                'peer_info': row.get('Peer', ''),
                'device_name': row.get('Name', '').strip() if pd.notna(row.get('Name')) else ''
            }
            
            transformed_data.append(transformed_row)
        
        return pd.DataFrame(transformed_data)

    def parse_protocol_port(self, protocol_str):
        """Parse protocol string to extract protocol type and port number"""
        if not protocol_str or pd.isna(protocol_str):
            return None, None, "Unknown"
        
        protocol_str = str(protocol_str).strip()
        
        if ':' in protocol_str:
            proto_part, port_part = protocol_str.split(':', 1)
            try:
                port = int(port_part)
                if proto_part.upper() in ['UDP', 'TCP', 'SSL']:
                    return proto_part.upper(), port, f"{proto_part.upper()}:{port}"
                else:
                    return 'TCP', port, f"{proto_part}:{port}"
            except ValueError:
                return None, None, protocol_str
        
        return None, None, protocol_str

    def extract_ip_from_peer(self, peer_str):
        """Extract IP address from peer string"""
        if not peer_str or pd.isna(peer_str):
            return None
        
        import re
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        match = re.search(ip_pattern, str(peer_str))
        return match.group() if match else str(peer_str)

    def append_to_master_excel(self, new_data: pd.DataFrame, original_filename: str) -> bool:
        """
        Append new data to the master Excel file
        """
        try:
            self.logger.info(f"[APPEND] Appending {len(new_data)} rows to master Excel file...")
            
            # Add metadata columns to track source
            new_data = new_data.copy()
            new_data['source_file'] = original_filename
            new_data['processed_date'] = datetime.now().isoformat()
            new_data['batch_id'] = hashlib.md5(f"{original_filename}_{datetime.now()}".encode('utf-8')).hexdigest()[:8]
            
            if self.master_excel_file.exists():
                # Load existing data
                existing_data = pd.read_excel(self.master_excel_file)
                self.logger.info(f"Existing master file has {len(existing_data)} rows")
                
                # Combine with new data
                combined_data = pd.concat([existing_data, new_data], ignore_index=True)
                
                # Remove duplicates based on key columns
                key_columns = ['src', 'dst', 'port', 'protocol', 'application']
                available_key_columns = [col for col in key_columns if col in combined_data.columns]
                
                if available_key_columns:
                    combined_data = combined_data.drop_duplicates(subset=available_key_columns, keep='last')
                    self.logger.info(f"After deduplication: {len(combined_data)} rows")
                
                # Sort by timestamp if available
                if 'timestamp' in combined_data.columns:
                    combined_data = combined_data.sort_values('timestamp')
                
            else:
                # First time, create new file
                combined_data = new_data
                self.logger.info(f"Creating new master file with {len(combined_data)} rows")
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(self.master_excel_file, engine='openpyxl') as writer:
                # Main data sheet
                combined_data.to_excel(writer, sheet_name='synthetic_flows_apps_archetype_', index=False)
                
                # Summary sheet
                self.create_summary_sheet(combined_data, writer)
                
                # Source tracking sheet
                self.create_source_tracking_sheet(combined_data, writer)
            
            self.logger.info(f"[SUCCESS] Successfully updated master Excel file: {self.master_excel_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error appending to master Excel file: {e}")
            return False

    def create_summary_sheet(self, data: pd.DataFrame, writer):
        """Create a summary sheet with statistics"""
        try:
            # Safely calculate numeric values
            def safe_sum(column_name):
                if column_name in data.columns:
                    try:
                        return pd.to_numeric(data[column_name], errors='coerce').sum()
                    except:
                        return 0
                return 0
            
            def safe_timestamp_min():
                if 'timestamp' in data.columns:
                    try:
                        ts_series = pd.to_numeric(data['timestamp'], errors='coerce')
                        return ts_series.min() if not ts_series.isna().all() else 'N/A'
                    except:
                        return 'N/A'
                return 'N/A'
            
            def safe_timestamp_max():
                if 'timestamp' in data.columns:
                    try:
                        ts_series = pd.to_numeric(data['timestamp'], errors='coerce')
                        return ts_series.max() if not ts_series.isna().all() else 'N/A'
                    except:
                        return 'N/A'
                return 'N/A'
            
            summary_stats = {
                'Metric': [
                    'Total Records',
                    'Unique Source IPs',
                    'Unique Destination IPs', 
                    'Unique Applications',
                    'Unique Protocols',
                    'Unique Ports',
                    'Total Bytes In',
                    'Total Bytes Out',
                    'Date Range (Start)',
                    'Date Range (End)',
                    'Last Updated'
                ],
                'Value': [
                    len(data),
                    data['src'].nunique() if 'src' in data.columns else 0,
                    data['dst'].nunique() if 'dst' in data.columns else 0,
                    data['application'].nunique() if 'application' in data.columns else 0,
                    data['protocol'].nunique() if 'protocol' in data.columns else 0,
                    data['port'].nunique() if 'port' in data.columns else 0,
                    safe_sum('bytes_in'),
                    safe_sum('bytes_out'),
                    safe_timestamp_min(),
                    safe_timestamp_max(),
                    datetime.now().isoformat()
                ]
            }
            
            summary_df = pd.DataFrame(summary_stats)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
        except Exception as e:
            self.logger.warning(f"Could not create summary sheet: {e}")

    def create_source_tracking_sheet(self, data: pd.DataFrame, writer):
        """Create a sheet tracking data sources"""
        try:
            if 'source_file' in data.columns:
                source_stats = data.groupby('source_file').agg({
                    'src': 'count',
                    'processed_date': 'first',
                    'batch_id': 'first'
                }).rename(columns={
                    'src': 'record_count',
                    'processed_date': 'first_processed',
                    'batch_id': 'batch_id'
                }).reset_index()
                
                source_stats.to_excel(writer, sheet_name='Source_Tracking', index=False)
                
        except Exception as e:
            self.logger.warning(f"Could not create source tracking sheet: {e}")

    def update_json_data_file(self, data: pd.DataFrame, original_filename: str):
        """
        Update the JSON data file for web application consumption
        """
        try:
            self.logger.info(f"[JSON] Creating JSON data file for web application...")
            
            # Ensure web templates directory exists
            self.json_data_file.parent.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"[JSON] Web templates directory: {self.json_data_file.parent}")
            
            # Create application summary
            app_summary = self.create_application_summary(data)
            self.logger.info(f"[JSON] Created summary for {len(app_summary)} applications")
            
            # Create port service mapping
            port_services = self.create_port_service_mapping(data)
            self.logger.info(f"[JSON] Created {len(port_services)} port service mappings")
            
            # Prepare JSON data
            json_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'source_file': original_filename,
                    'total_records': len(data),
                    'version': '1.0.0',
                    'master_file_location': str(self.master_excel_file),
                    'last_updated': datetime.now().isoformat()
                },
                'applications': app_summary,
                'port_services': port_services,
                'summary_stats': {
                    'unique_sources': data['src'].nunique() if 'src' in data.columns else 0,
                    'unique_destinations': data['dst'].nunique() if 'dst' in data.columns else 0,
                    'unique_protocols': data['protocol'].nunique() if 'protocol' in data.columns else 0,
                    'unique_ports': data['port'].nunique() if 'port' in data.columns else 0,
                    'total_bytes': self.safe_sum_bytes(data)
                },
                'raw_data_sample': self.create_clean_sample_data(data, 50) if len(data) > 0 else []
            }
            
            # Clean the JSON data to remove NaN values
            json_data = self.clean_json_data(json_data)
            
            # Write JSON file with UTF-8 encoding
            self.logger.info(f"[JSON] Writing to: {self.json_data_file}")
            with open(self.json_data_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=self.json_serializer, ensure_ascii=False)
            
            # Verify file was created
            if self.json_data_file.exists():
                file_size = self.json_data_file.stat().st_size
                self.logger.info(f"[SUCCESS] JSON file created: {self.json_data_file} ({file_size:,} bytes)")
            else:
                self.logger.error(f"[ERROR] JSON file was not created: {self.json_data_file}")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error updating JSON data file: {e}")
            import traceback
            self.logger.error(f"[ERROR] Full traceback: {traceback.format_exc()}")
            # Don't re-raise the exception, just log it

    def clean_json_data(self, data):
        """Recursively clean JSON data to remove NaN values and make it JSON-serializable"""
        import math
        
        if isinstance(data, dict):
            return {key: self.clean_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_data(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None  # Convert NaN/Inf to null
            return data
        elif pd.isna(data):
            return None  # Convert pandas NaN to null
        else:
            return data
    
    def json_serializer(self, obj):
        """Custom JSON serializer to handle special types"""
        import math
        
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif pd.isna(obj):
            return None
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        else:
            return str(obj)

    def safe_sum_bytes(self, data: pd.DataFrame) -> float:
        """Safely calculate total bytes from bytes_in and bytes_out columns"""
        try:
            total = 0.0
            if 'bytes_in' in data.columns:
                bytes_in = pd.to_numeric(data['bytes_in'], errors='coerce').sum()
                if not pd.isna(bytes_in):
                    total += float(bytes_in)
            
            if 'bytes_out' in data.columns:
                bytes_out = pd.to_numeric(data['bytes_out'], errors='coerce').sum()
                if not pd.isna(bytes_out):
                    total += float(bytes_out)
            
            return total
        except Exception:
            return 0.0

    def create_application_summary(self, data: pd.DataFrame) -> List[dict]:
        """Create application summary from processed data"""
        app_summary = []
        
        if 'application' not in data.columns:
            self.logger.warning("No 'application' column found, creating generic summary")
            return [{
                'id': 'NETWORK_DATA',
                'name': 'Network Data Application',
                'total_records': len(data),
                'complexity': 'medium'
            }]
        
        # Group by application
        for app_name in data['application'].unique():
            if pd.isna(app_name):
                continue
                
            app_data = data[data['application'] == app_name]
            
            # Calculate metrics safely
            unique_sources = app_data['src'].nunique() if 'src' in app_data.columns else 0
            unique_destinations = app_data['dst'].nunique() if 'dst' in app_data.columns else 0
            
            # Safe byte calculations
            total_bytes_in = 0.0
            total_bytes_out = 0.0
            try:
                if 'bytes_in' in app_data.columns:
                    total_bytes_in = float(pd.to_numeric(app_data['bytes_in'], errors='coerce').sum())
                    if pd.isna(total_bytes_in):
                        total_bytes_in = 0.0
                        
                if 'bytes_out' in app_data.columns:
                    total_bytes_out = float(pd.to_numeric(app_data['bytes_out'], errors='coerce').sum())
                    if pd.isna(total_bytes_out):
                        total_bytes_out = 0.0
            except Exception:
                total_bytes_in = 0.0
                total_bytes_out = 0.0
            
            # Get most common values safely
            most_common_protocol = 'Unknown'
            if 'protocol' in app_data.columns and not app_data['protocol'].empty:
                try:
                    mode_values = app_data['protocol'].dropna().mode()
                    if len(mode_values) > 0:
                        most_common_protocol = str(mode_values.iloc[0])
                except:
                    pass
            
            most_common_service = 'Unknown'
            if 'service_definition' in app_data.columns and not app_data['service_definition'].empty:
                try:
                    mode_values = app_data['service_definition'].dropna().mode()
                    if len(mode_values) > 0:
                        most_common_service = str(mode_values.iloc[0])
                except:
                    pass
            
            # Determine complexity
            complexity = self.determine_complexity(len(app_data), 1, unique_sources + unique_destinations)
            
            app_info = {
                'id': str(app_name),
                'name': self.get_full_application_name(str(app_name)),
                'total_records': len(app_data),
                'unique_sources': unique_sources,
                'unique_destinations': unique_destinations,
                'unique_ips': unique_sources + unique_destinations,
                'total_bytes_in': total_bytes_in,
                'total_bytes_out': total_bytes_out,
                'total_bytes': total_bytes_in + total_bytes_out,
                'most_common_protocol': most_common_protocol,
                'most_common_service': most_common_service,
                'complexity': complexity,
                'ports': self.safe_extract_ports(app_data),
                'protocols': self.safe_extract_protocols(app_data)
            }
            
            app_summary.append(app_info)
        
        # Sort by total records
        app_summary.sort(key=lambda x: x['total_records'], reverse=True)
        return app_summary

    def create_clean_sample_data(self, data: pd.DataFrame, sample_size: int = 50) -> List[dict]:
        """Create a clean sample of data for JSON export, handling NaN values and cleaning ports"""
        try:
            # Get sample data
            sample_data = data.head(sample_size).copy()
            
            # Clean port numbers specifically to remove .0 suffix
            if 'port' in sample_data.columns:
                sample_data['port'] = sample_data['port'].apply(self.clean_port_value)
            
            # Replace NaN values with None (which becomes null in JSON)
            sample_data = sample_data.where(pd.notna(sample_data), None)
            
            # Convert to records and clean each record
            records = sample_data.to_dict('records')
            clean_records = []
            
            for record in records:
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    elif isinstance(value, float):
                        import math
                        if math.isnan(value) or math.isinf(value):
                            clean_record[key] = None
                        else:
                            # For numeric values, check if they should be integers (like ports)
                            if key == 'port' and value == int(value):
                                clean_record[key] = int(value)
                            else:
                                clean_record[key] = value
                    else:
                        clean_record[key] = value
                
                clean_records.append(clean_record)
            
            return clean_records
            
        except Exception as e:
            self.logger.warning(f"Error creating sample data: {e}")
            return []
    
    def clean_port_value(self, port_value):
        """Clean a single port value to remove .0 suffix"""
        try:
            if pd.isna(port_value):
                return None
            
            # If it's a float that's actually an integer, convert it
            if isinstance(port_value, float):
                if port_value == int(port_value):
                    return int(port_value)
                else:
                    return port_value
            
            # If it's a string with .0, remove it
            if isinstance(port_value, str) and port_value.endswith('.0'):
                try:
                    return int(float(port_value))
                except:
                    return port_value[:-2]  # Just remove .0
            
            return port_value
            
        except Exception:
            return port_value

    def safe_extract_ports(self, data: pd.DataFrame) -> List[str]:
        """Safely extract port numbers, filtering out NaN values and removing .0 suffix"""
        if 'port' not in data.columns:
            return []
        
        try:
            ports = []
            for port in data['port'].dropna().unique():
                if pd.notna(port) and str(port) not in ['nan', 'NaN', '']:
                    # Try to convert to int first, then to string (removes .0)
                    try:
                        # Convert float to int to remove .0 suffix
                        port_int = int(float(port))
                        if 0 <= port_int <= 65535:  # Valid port range
                            ports.append(str(port_int))  # This will be clean integer string
                    except (ValueError, TypeError):
                        # If not a number, keep as string if not empty
                        port_str = str(port).strip()
                        if port_str and port_str.lower() not in ['nan', 'none', 'null']:
                            # Remove .0 suffix from string representation if present
                            if port_str.endswith('.0'):
                                port_str = port_str[:-2]
                            ports.append(port_str)
            
            return sorted(list(set(ports)))  # Remove duplicates and sort
        except Exception:
            return []
    
    def safe_extract_protocols(self, data: pd.DataFrame) -> List[str]:
        """Safely extract protocols, filtering out NaN values"""
        if 'protocol' not in data.columns:
            return []
        
        try:
            protocols = []
            for protocol in data['protocol'].dropna().unique():
                if pd.notna(protocol):
                    protocol_str = str(protocol).strip()
                    if protocol_str and protocol_str.lower() not in ['nan', 'none', 'null', '']:
                        protocols.append(protocol_str)
            
            return sorted(list(set(protocols)))  # Remove duplicates and sort
        except Exception:
            return []

    def create_port_service_mapping(self, data: pd.DataFrame) -> dict:
        """Create port-to-service mapping with clean integer ports"""
        port_service_map = {}
        
        for _, row in data.iterrows():
            try:
                port = row.get('port', '')
                protocol = row.get('protocol', 'TCP')
                service = row.get('service_definition', 'Unknown Service')
                
                # Clean and validate port - convert to integer to remove .0
                if pd.notna(port) and str(port) not in ['nan', 'NaN', '']:
                    try:
                        # Convert to int to remove .0 suffix, then back to string
                        port_int = int(float(port))
                        if 0 <= port_int <= 65535:  # Valid port range
                            port_clean = str(port_int)  # Clean integer string
                        else:
                            continue  # Skip invalid ports
                    except (ValueError, TypeError):
                        # Handle string ports
                        port_str = str(port).strip()
                        if port_str.endswith('.0'):
                            port_str = port_str[:-2]
                        port_clean = port_str
                        if not port_clean or port_clean.lower() in ['nan', 'none', 'null']:
                            continue
                else:
                    continue  # Skip empty/NaN ports
                
                # Clean protocol
                if pd.notna(protocol):
                    protocol_clean = str(protocol).strip()
                    if not protocol_clean or protocol_clean.lower() in ['nan', 'none', 'null']:
                        protocol_clean = 'TCP'
                else:
                    protocol_clean = 'TCP'
                
                # Clean service
                if pd.notna(service):
                    service_clean = str(service).strip()
                    if not service_clean or service_clean.lower() in ['nan', 'none', 'null']:
                        service_clean = 'Unknown Service'
                else:
                    service_clean = 'Unknown Service'
                
                key = f"{protocol_clean}:{port_clean}"
                if key not in port_service_map:
                    port_service_map[key] = {
                        'port': port_clean,  # Clean integer port
                        'protocol': protocol_clean,
                        'service': service_clean,
                        'count': 0
                    }
                port_service_map[key]['count'] += 1
                
            except Exception:
                continue  # Skip problematic rows
        
        return port_service_map

    def determine_complexity(self, record_count, service_count, ip_count):
        """Determine application complexity"""
        if record_count > 100 or service_count > 10 or ip_count > 50:
            return 'very-high'
        elif record_count > 50 or service_count > 5 or ip_count > 20:
            return 'high'
        elif record_count > 10 or service_count > 2 or ip_count > 5:
            return 'medium'
        else:
            return 'low'

    def get_full_application_name(self, app_id):
        """Convert application ID to full name"""
        name_map = {
            'ACDM': 'Application Component Discovery and Mapping',
            'HTTP': 'Web Service Application',
            'HTTPS': 'Secure Web Service Application',
            'DNS': 'Domain Name Service',
            'NTP': 'Network Time Protocol Service',
            'CIFS': 'Common Internet File System'
        }
        return name_map.get(app_id, app_id)

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single file through the complete pipeline
        Returns True if successful, False if failed
        """
        self.logger.info(f"[PROCESSING] Processing file: {file_path.name}")
        
        try:
            # Check if file is supported
            if not self.is_supported_file(file_path):
                self.logger.warning(f"Unsupported file format: {file_path.suffix}")
                return False
            
            # Load data
            data = self.load_data_from_file(file_path)
            if data is None:
                self.logger.error(f"Failed to load data from {file_path.name}")
                return False
            
            # Transform raw data if needed
            data = self.detect_and_transform_raw_data(data, file_path)
            
            # Validate data format
            is_valid, validation_message = self.validate_data_format(data)
            if not is_valid:
                self.logger.error(f"Data validation failed: {validation_message}")
                return False
            
            # Calculate data hash for duplicate detection (after transformation)
            data_hash = self.calculate_data_hash(data)
            
            # Check for duplicates (but still update JSON even if duplicate)
            is_duplicate = data_hash in self.data_hashes
            if is_duplicate:
                self.logger.info(f"[WARNING] Duplicate data detected in {file_path.name}, updating JSON but skipping Excel append")
                excel_success = True  # Don't append to Excel, but mark as successful
            else:
                # Append to master Excel file only if not duplicate
                excel_success = self.append_to_master_excel(data, file_path.name)
            
            # Always update JSON data file (even for duplicates, to ensure it exists)
            self.update_json_data_file(data, file_path.name)
            
            # Record successful processing
            if not is_duplicate:
                self.data_hashes.add(data_hash)
            
            self.processed_files[file_path.name] = {
                'processed_date': datetime.now().isoformat(),
                'data_hash': data_hash,
                'records_count': len(data),
                'excel_updated': excel_success,
                'json_updated': True,
                'was_duplicate': is_duplicate
            }
            
            # Save hash database
            self.save_processed_hashes()
            
            self.logger.info(f"[SUCCESS] Successfully processed {file_path.name}: {len(data)} records")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error processing {file_path.name}: {e}")
            return False

    def move_file_to_destination(self, file_path: Path, success: bool):
        """Move file to appropriate destination folder"""
        try:
            if success:
                destination = self.processed_dir / file_path.name
                self.logger.info(f"[MOVE] Moving {file_path.name} to processed/")
            else:
                destination = self.failed_dir / file_path.name
                self.logger.info(f"[MOVE] Moving {file_path.name} to failed/")
            
            # Handle name conflicts
            counter = 1
            original_dest = destination
            while destination.exists():
                stem = original_dest.stem
                suffix = original_dest.suffix
                destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(file_path), str(destination))
            
        except Exception as e:
            self.logger.error(f"Error moving {file_path.name}: {e}")

class FileWatcher(FileSystemEventHandler):
    """File system watcher for monitoring new files in staging directory"""
    
    def __init__(self, processor: FileProcessor):
        self.processor = processor
        self.logger = SafeLogger(__name__)
        self.processing_lock = threading.Lock()
        
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Ignore files in subdirectories
        if file_path.parent != self.processor.staging_dir:
            return
        
        # Wait a moment for file to be completely written
        time.sleep(2)
        
        # Process the file
        self.process_new_file(file_path)
    
    def on_moved(self, event):
        """Handle file moves (like from temp to final name)"""
        if event.is_directory:
            return
            
        dest_path = Path(event.dest_path)
        
        # Only process if moved to staging root
        if dest_path.parent != self.processor.staging_dir:
            return
            
        time.sleep(2)
        self.process_new_file(dest_path)
    
    def process_new_file(self, file_path: Path):
        """Process a new file with thread safety"""
        with self.processing_lock:
            self.logger.info(f"[NEW] New file detected: {file_path.name}")
            
            # Check if file still exists
            if not file_path.exists():
                self.logger.warning(f"File {file_path.name} no longer exists")
                return
            
            # Process the file
            success = self.processor.process_file(file_path)
            
            # Move file to appropriate folder
            if file_path.exists():
                self.processor.move_file_to_destination(file_path, success)

class ACTIVnetFileProcessingSystem:
    """Main orchestration class for the file processing system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.staging_dir = self.project_root / "data_staging"
        
        # Initialize components
        self.processor = FileProcessor(self.project_root)
        self.file_watcher = FileWatcher(self.processor)
        self.observer = Observer()
        
        # Setup logging
        self.logger = SafeLogger(__name__)
        
    def process_existing_files(self):
        """Process any files that already exist in the staging directory"""
        self.logger.info("[SCANNING] Checking for existing files in staging directory...")
        
        existing_files = [f for f in self.staging_dir.iterdir() 
                         if f.is_file() and self.processor.is_supported_file(f)]
        
        if existing_files:
            self.logger.info(f"Found {len(existing_files)} existing files to process")
            
            for file_path in existing_files:
                self.logger.info(f"Processing existing file: {file_path.name}")
                success = self.processor.process_file(file_path)
                self.processor.move_file_to_destination(file_path, success)
        else:
            self.logger.info("No existing files found in staging directory")
    
    def start_monitoring(self):
        """Start the file monitoring system"""
        self.logger.info(f"[SYSTEM] Starting ACTIVnet File Processing System")
        self.logger.info(f"[FOLDER] Monitoring directory: {self.staging_dir}")
        self.logger.info(f"[DATA] Master Excel file: {self.processor.master_excel_file}")
        self.logger.info(f"[WEB] JSON data file (web-accessible): {self.processor.json_data_file}")
        self.logger.info(f"[WEB] Web server should serve from: {self.processor.web_static_dir}")
        self.logger.info(f"[WEB] JSON accessible at: /templates/activnet_data.json")
        
        # Process any existing files first
        self.process_existing_files()
        
        # Start file system monitoring
        self.observer.schedule(
            self.file_watcher, 
            str(self.staging_dir), 
            recursive=False
        )
        
        self.observer.start()
        self.logger.info("[PROCESSING] File monitoring started. Waiting for new files...")
        
        try:
            while True:
                time.sleep(10)  # Check every 10 seconds
                
                # Periodic status update
                processed_count = len(list((self.staging_dir / "processed").iterdir()))
                failed_count = len(list((self.staging_dir / "failed").iterdir()))
                
                if processed_count > 0 or failed_count > 0:
                    self.logger.info(f"[DATA] Status: {processed_count} processed, {failed_count} failed files")
                
        except KeyboardInterrupt:
            self.logger.info("[STOP] Stopping file monitoring...")
            self.observer.stop()
        
        self.observer.join()
        self.logger.info("[SUCCESS] File processing system stopped")
    
    def get_status(self) -> dict:
        """Get current system status"""
        processed_files = list((self.staging_dir / "processed").iterdir())
        failed_files = list((self.staging_dir / "failed").iterdir())
        staging_files = [f for f in self.staging_dir.iterdir() 
                        if f.is_file() and self.processor.is_supported_file(f)]
        
        master_excel_exists = self.processor.master_excel_file.exists()
        json_data_exists = self.processor.json_data_file.exists()
        
        return {
            'staging_directory': str(self.staging_dir),
            'files_in_staging': len(staging_files),
            'processed_files': len(processed_files),
            'failed_files': len(failed_files),
            'total_data_hashes': len(self.processor.data_hashes),
            'monitoring_active': self.observer.is_alive(),
            'master_excel_exists': master_excel_exists,
            'master_excel_path': str(self.processor.master_excel_file),
            'json_data_exists': json_data_exists,
            'json_data_path': str(self.processor.json_data_file),
            'last_check': datetime.now().isoformat()
        }

def main():
    """Main function with command line support"""
    parser = argparse.ArgumentParser(description='ACTIVnet File Processing System - Windows Compatible')
    parser.add_argument('--project-root', '-r', default='.',
                       help='Project root directory (default: current directory)')
    parser.add_argument('--process-existing', '-p', action='store_true',
                       help='Process existing files and exit (no monitoring)')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show current status and exit')
    
    args = parser.parse_args()
    
    # Initialize system
    system = ACTIVnetFileProcessingSystem(args.project_root)
    
    if args.status:
        # Show status and exit
        status = system.get_status()
        print("\n[SYSTEM] ACTIVnet File Processing System Status")
        print("=" * 50)
        for key, value in status.items():
            print(f"{key}: {value}")
        return
    
    if args.process_existing:
        # Process existing files only
        system.process_existing_files()
        print("[SUCCESS] Existing files processing completed")
        return
    
    # Start monitoring system
    try:
        system.start_monitoring()
    except Exception as e:
        logging.error(f"System error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())