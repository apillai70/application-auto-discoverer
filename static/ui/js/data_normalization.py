# Data Normalization and ML Vectorization Module
# Integration Hub - Network Topology Application
# Author: Integration Hub Team
# Version: 1.0.0

import pandas as pd
import numpy as np
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import io
from dataclasses import dataclass, asdict
from collections import defaultdict
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """Configuration for data processing pipeline"""
    duplicate_strategy: str = 'smart_upsert'
    logging_level: str = 'detailed'
    vectorization_enabled: bool = True
    field_mapping_enabled: bool = True
    max_file_size_mb: int = 100
    time_window_minutes: int = 5
    quality_threshold: float = 0.8

@dataclass
class ProcessingResult:
    """Result structure for processing operations"""
    file_name: str
    original_rows: int
    processed_rows: int
    quality_score: float
    known_applications: int
    unknown_applications: int
    duplicate_info: Dict[str, Any]
    field_mapping: Dict[str, str]
    vectorization_result: Optional[Dict[str, Any]]
    processing_time: float
    status: str = 'completed'
    errors: List[str] = None

class DataNormalizer:
    """Main class for network data normalization and ML preparation"""
    
    # Standard field mappings for network data
    STANDARD_FIELD_MAP = {
        # Application fields
        'application': ['application', 'app', 'app_name', 'application_name', 'service', 'service_name', 'system', 'component'],
        'app_id': ['app_id', 'application_id', 'id', 'service_id', 'system_id', 'component_id'],
        
        # Network fields
        'source_ip': ['source_ip', 'src_ip', 'source', 'src', 'client_ip', 'from_ip', 'origin_ip'],
        'destination_ip': ['destination_ip', 'dest_ip', 'dst_ip', 'destination', 'dest', 'dst', 'server_ip', 'to_ip', 'target_ip'],
        'protocol': ['protocol', 'proto', 'transport', 'transport_protocol', 'network_protocol'],
        'port': ['port', 'destination_port', 'dest_port', 'dst_port', 'server_port', 'service_port'],
        
        # Traffic fields (ML-ready numerical features)
        'bytes': ['bytes', 'byte_count', 'total_bytes', 'data_bytes', 'payload_bytes'],
        'packets': ['packets', 'packet_count', 'total_packets', 'pkt_count'],
        'traffic_volume': ['traffic_volume', 'volume', 'data_volume', 'throughput'],
        'response_time': ['response_time', 'latency', 'rtt', 'delay'],
        
        # Temporal fields
        'timestamp': ['timestamp', 'time', 'datetime', 'date_time', 'event_time', 'created_at', 'occurred_at'],
        'first_seen': ['first_seen', 'start_time', 'session_start'],
        'last_seen': ['last_seen', 'end_time', 'session_end'],
        
        # Behavioral features for ML
        'connection_count': ['connection_count', 'conn_count', 'sessions', 'flows'],
        'unique_destinations': ['unique_destinations', 'dest_count', 'target_count'],
        'traffic_pattern': ['traffic_pattern', 'pattern', 'behavior_type'],
        
        # Metadata fields
        'cluster': ['cluster', 'cluster_id', 'group', 'group_id', 'zone', 'segment'],
        'archetype': ['archetype', 'type', 'category', 'classification', 'role', 'function'],
        'security_zone': ['security_zone', 'zone', 'network_segment', 'dmz']
    }
    
    # Vector field mappings for ML model preparation
    VECTOR_FIELD_MAPPINGS = {
        'numerical': ['bytes', 'packets', 'traffic_volume', 'port', 'response_time', 'latency', 'connection_count'],
        'categorical': ['protocol', 'application', 'archetype', 'security_zone', 'traffic_pattern'],
        'temporal': ['timestamp', 'first_seen', 'last_seen'],
        'network': ['source_ip', 'destination_ip'],
        'behavioral': ['connection_count', 'unique_destinations', 'traffic_pattern']
    }
    
    def __init__(self, config: ProcessingConfig = None):
        """Initialize the DataNormalizer with configuration"""
        self.config = config or ProcessingConfig()
        self.global_record_store = {}  # Cross-batch duplicate tracking
        self.processing_logs = []
        self.session_id = self._generate_session_id()
        
        logger.info(f"DataNormalizer initialized with session {self.session_id}")
        self._log_event('standard', 'initialization', 'DataNormalizer initialized')
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(id(self)) % 10000:04d}"
    
    def _log_event(self, level: str, category: str, message: str, data: Any = None):
        """Log processing events with structured format"""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'data': data,
            'session_id': self.session_id
        }
        
        self.processing_logs.append(log_entry)
        
        # Also log to Python logger
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, f"{category}: {message}")
    
    def normalize_excel(self, file_content: bytes, filename: str = "unknown") -> pd.DataFrame:
        """
        Normalize an Excel file from bytes with enhanced processing
        
        Args:
            file_content: Raw file bytes
            filename: Original filename for logging
            
        Returns:
            Normalized DataFrame
        """
        try:
            self._log_event('standard', 'file_processing', f'Starting Excel normalization for {filename}')
            
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content))
            
            # Apply standard normalization
            normalized_df = self._apply_standard_normalization(df, filename)
            
            self._log_event('standard', 'file_processing', f'Excel normalization completed for {filename}', {
                'original_rows': len(df),
                'processed_rows': len(normalized_df),
                'columns': list(normalized_df.columns)
            })
            
            return normalized_df
            
        except Exception as e:
            self._log_event('standard', 'error', f'Excel normalization failed for {filename}: {str(e)}')
            raise ValueError(f"Failed to normalize Excel content: {e}")
    
    def normalize_csv(self, file_content: Union[str, bytes], filename: str = "unknown") -> pd.DataFrame:
        """
        Normalize a CSV file with enhanced processing
        
        Args:
            file_content: CSV content as string or bytes
            filename: Original filename for logging
            
        Returns:
            Normalized DataFrame
        """
        try:
            self._log_event('standard', 'file_processing', f'Starting CSV normalization for {filename}')
            
            # Handle bytes input
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Read CSV with robust parsing
            df = pd.read_csv(
                io.StringIO(file_content),
                encoding='utf-8',
                na_values=['', 'NA', 'na', 'none', 'None', 'UNKNOWN', 'unknown', 'null'],
                keep_default_na=True
            )
            
            # Apply standard normalization
            normalized_df = self._apply_standard_normalization(df, filename)
            
            self._log_event('standard', 'file_processing', f'CSV normalization completed for {filename}', {
                'original_rows': len(df),
                'processed_rows': len(normalized_df),
                'columns': list(normalized_df.columns)
            })
            
            return normalized_df
            
        except Exception as e:
            self._log_event('standard', 'error', f'CSV normalization failed for {filename}: {str(e)}')
            raise ValueError(f"Failed to normalize CSV content: {e}")
    
    def normalize_json(self, file_content: Union[str, bytes], filename: str = "unknown") -> pd.DataFrame:
        """
        Normalize a JSON file with enhanced processing
        
        Args:
            file_content: JSON content as string or bytes
            filename: Original filename for logging
            
        Returns:
            Normalized DataFrame
        """
        try:
            self._log_event('standard', 'file_processing', f'Starting JSON normalization for {filename}')
            
            # Handle bytes input
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse JSON
            data = json.loads(file_content)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("JSON structure not supported")
            
            # Apply standard normalization
            normalized_df = self._apply_standard_normalization(df, filename)
            
            self._log_event('standard', 'file_processing', f'JSON normalization completed for {filename}', {
                'original_rows': len(df),
                'processed_rows': len(normalized_df),
                'columns': list(normalized_df.columns)
            })
            
            return normalized_df
            
        except Exception as e:
            self._log_event('standard', 'error', f'JSON normalization failed for {filename}: {str(e)}')
            raise ValueError(f"Failed to normalize JSON content: {e}")
    
    def _apply_standard_normalization(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Apply standard normalization rules to DataFrame"""
        
        # Clean column names
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Drop completely empty rows
        initial_rows = len(df)
        df = df.dropna(how='all').reset_index(drop=True)
        dropped_rows = initial_rows - len(df)
        
        if dropped_rows > 0:
            self._log_event('detailed', 'data_cleaning', f'Dropped {dropped_rows} empty rows from {filename}')
        
        # Apply field mapping if enabled
        if self.config.field_mapping_enabled:
            field_mapping = self._detect_field_mappings(df.columns)
            df = self._apply_field_mapping(df, field_mapping)
            self._log_event('detailed', 'field_mapping', f'Applied field mapping to {filename}', field_mapping)
        
        # Normalize application field
        df = self._normalize_application_field(df)
        
        # Normalize network fields
        df = self._normalize_network_fields(df)
        
        # Add metadata
        df['_record_id'] = [f"rec_{i:06d}_{hash(str(row)) % 10000:04d}" for i, row in df.iterrows()]
        df['_processed_at'] = datetime.now(timezone.utc).isoformat()
        df['_source_file'] = filename
        df['_session_id'] = self.session_id
        
        return df
    
    def _detect_field_mappings(self, columns: List[str]) -> Dict[str, str]:
        """Detect field mappings automatically"""
        mappings = {}
        
        for column in columns:
            normalized_column = column.lower().strip()
            
            for standard_field, variations in self.STANDARD_FIELD_MAP.items():
                if any(variation in normalized_column or normalized_column in variation 
                      for variation in variations):
                    mappings[column] = standard_field
                    break
        
        confidence_score = len(mappings) / len(columns) * 100 if columns else 0
        
        self._log_event('detailed', 'field_detection', f'Field mapping confidence: {confidence_score:.1f}%', {
            'total_fields': len(columns),
            'mapped_fields': len(mappings),
            'mappings': mappings
        })
        
        return mappings
    
    def _apply_field_mapping(self, df: pd.DataFrame, mappings: Dict[str, str]) -> pd.DataFrame:
        """Apply field mappings to DataFrame"""
        if not mappings:
            return df
        
        # Rename columns according to mappings
        df = df.rename(columns=mappings)
        
        return df
    
    def _normalize_application_field(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize application field with comprehensive rules"""
        if 'application' not in df.columns:
            return df
        
        # Handle missing values
        df['application_original'] = df['application'].copy()
        df['application'] = df['application'].fillna('unknown')
        df['application'] = df['application'].astype(str).str.strip()
        
        # Normalize unknown values
        unknown_values = ['', 'na', 'none', 'unknown', 'null', 'n/a', '-', 'undefined']
        df['application'] = df['application'].apply(
            lambda x: 'unknown' if x.lower() in unknown_values else x
        )
        
        # Create known/unknown flag
        df['is_known_app'] = (df['application'] != 'unknown').astype(int)
        
        known_count = df['is_known_app'].sum()
        total_count = len(df)
        
        self._log_event('detailed', 'application_normalization', 'Application field normalized', {
            'total_records': total_count,
            'known_applications': known_count,
            'unknown_applications': total_count - known_count,
            'quality_ratio': known_count / total_count if total_count > 0 else 0
        })
        
        return df
    
    def _normalize_network_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize network-specific fields"""
        
        # Normalize IP addresses
        for ip_field in ['source_ip', 'destination_ip']:
            if ip_field in df.columns:
                df[ip_field] = df[ip_field].astype(str).str.strip()
                # Add subnet information
                df[f'{ip_field}_subnet'] = df[ip_field].apply(self._extract_subnet)
        
        # Normalize protocol field
        if 'protocol' in df.columns:
            df['protocol'] = df['protocol'].astype(str).str.upper().str.strip()
        
        # Normalize port field
        if 'port' in df.columns:
            df['port'] = pd.to_numeric(df['port'], errors='coerce').fillna(0).astype(int)
        
        # Normalize timestamp fields
        for time_field in ['timestamp', 'first_seen', 'last_seen']:
            if time_field in df.columns:
                df[time_field] = pd.to_datetime(df[time_field], errors='coerce')
        
        return df
    
    def _extract_subnet(self, ip_address: str) -> str:
        """Extract subnet from IP address (first 3 octets)"""
        try:
            parts = str(ip_address).split('.')
            if len(parts) >= 3:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            return "unknown"
        except:
            return "unknown"
    
    def handle_cross_batch_duplicates(self, df: pd.DataFrame, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Handle cross-batch duplicate detection and resolution"""
        
        duplicate_info = {
            'strategy': self.config.duplicate_strategy,
            'new_records': 0,
            'updated_records': 0,
            'ignored_duplicates': 0,
            'conflicts': [],
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        self._log_event('standard', 'duplicate_processing', f'Starting cross-batch duplicate handling for {filename}')
        
        processed_records = []
        
        for _, row in df.iterrows():
            record_key = self._create_advanced_record_key(row)
            record_hash = self._create_data_hash(row)
            
            if record_key in self.global_record_store:
                existing_record = self.global_record_store[record_key]
                change_detection = self._detect_field_changes(existing_record['data'], row)
                
                if change_detection['has_changes']:
                    if self.config.duplicate_strategy == 'smart_upsert':
                        updated_record = self._perform_smart_upsert(
                            existing_record['data'], row, change_detection
                        )
                        
                        self.global_record_store[record_key] = {
                            'data': updated_record,
                            'hash': self._create_data_hash(updated_record),
                            'first_seen': existing_record['first_seen'],
                            'last_updated': datetime.now(timezone.utc).isoformat(),
                            'update_count': existing_record.get('update_count', 0) + 1
                        }
                        
                        processed_records.append(updated_record)
                        duplicate_info['updated_records'] += 1
                        
                        self._log_event('debug', 'smart_upsert', f'Record upserted: {record_key}', {
                            'changes': change_detection['changes']
                        })
                        
                    elif self.config.duplicate_strategy == 'timestamp_priority':
                        if self._is_newer_record(row, existing_record['data']):
                            self.global_record_store[record_key] = {
                                'data': row,
                                'hash': record_hash,
                                'first_seen': existing_record['first_seen'],
                                'last_updated': datetime.now(timezone.utc).isoformat(),
                                'update_count': existing_record.get('update_count', 0) + 1
                            }
                            processed_records.append(row)
                            duplicate_info['updated_records'] += 1
                        else:
                            duplicate_info['ignored_duplicates'] += 1
                    else:
                        duplicate_info['ignored_duplicates'] += 1
                else:
                    duplicate_info['ignored_duplicates'] += 1
            else:
                # New record
                self.global_record_store[record_key] = {
                    'data': row,
                    'hash': record_hash,
                    'first_seen': datetime.now(timezone.utc).isoformat(),
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'update_count': 0
                }
                processed_records.append(row)
                duplicate_info['new_records'] += 1
        
        duplicate_info['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        self._log_event('standard', 'duplicate_processing', f'Cross-batch duplicate processing completed for {filename}', duplicate_info)
        
        return pd.DataFrame(processed_records), duplicate_info
    
    def _create_advanced_record_key(self, row: pd.Series) -> str:
        """Create advanced record key for duplicate detection"""
        primary_keys = ['source_ip', 'destination_ip', 'application', 'protocol', 'port']
        
        key_values = []
        for key in primary_keys:
            value = row.get(key, '')
            key_values.append(str(value).lower().strip())
        
        # Add temporal component for time-windowed deduplication
        timestamp = row.get('timestamp', datetime.now())
        if pd.notna(timestamp):
            time_window = int(pd.Timestamp(timestamp).timestamp() // (self.config.time_window_minutes * 60))
            key_values.append(str(time_window))
        
        return '|'.join(key_values)
    
    def _create_data_hash(self, row: Union[pd.Series, Dict]) -> str:
        """Create hash for data change detection"""
        if isinstance(row, pd.Series):
            row = row.to_dict()
        
        # Create deterministic hash
        sorted_items = sorted(row.items())
        data_string = '|'.join(f"{k}:{v}" for k, v in sorted_items)
        return hashlib.md5(data_string.encode()).hexdigest()[:16]
    
    def _detect_field_changes(self, existing_record: Union[pd.Series, Dict], new_record: Union[pd.Series, Dict]) -> Dict[str, Any]:
        """Detect changes between records"""
        if isinstance(existing_record, pd.Series):
            existing_record = existing_record.to_dict()
        if isinstance(new_record, pd.Series):
            new_record = new_record.to_dict()
        
        changes = []
        all_keys = set(existing_record.keys()) | set(new_record.keys())
        
        for key in all_keys:
            old_value = existing_record.get(key)
            new_value = new_record.get(key)
            
            if old_value != new_value:
                changes.append({
                    'field': key,
                    'old_value': old_value,
                    'new_value': new_value,
                    'change_type': self._get_change_type(old_value, new_value)
                })
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'significant_changes': [c for c in changes if c['change_type'] != 'minor']
        }
    
    def _get_change_type(self, old_value: Any, new_value: Any) -> str:
        """Classify the type of change"""
        if pd.isna(old_value) and pd.notna(new_value):
            return 'addition'
        if pd.notna(old_value) and pd.isna(new_value):
            return 'deletion'
        
        # For numerical fields, check significance
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if old_value != 0:
                percent_change = abs((new_value - old_value) / old_value) * 100
                return 'significant' if percent_change > 10 else 'minor'
        
        return 'modification'
    
    def _perform_smart_upsert(self, existing_record: Dict, new_record: Union[pd.Series, Dict], change_detection: Dict) -> Dict:
        """Perform smart upsert with intelligent field merging"""
        if isinstance(new_record, pd.Series):
            new_record = new_record.to_dict()
        
        upserted = existing_record.copy()
        
        for change in change_detection['changes']:
            field = change['field']
            old_value = change['old_value']
            new_value = change['new_value']
            change_type = change['change_type']
            
            if change_type == 'addition' and (pd.isna(old_value) or old_value == ''):
                # Fill missing fields
                upserted[field] = new_value
            elif field in ['bytes', 'packets', 'traffic_volume', 'connection_count']:
                # Accumulate traffic metrics
                old_val = float(old_value) if pd.notna(old_value) else 0
                new_val = float(new_value) if pd.notna(new_value) else 0
                upserted[field] = old_val + new_val
            elif 'timestamp' in field or 'time' in field:
                # Use latest timestamp
                if pd.notna(new_value) and pd.notna(old_value):
                    if pd.Timestamp(new_value) > pd.Timestamp(old_value):
                        upserted[field] = new_value
                    upserted['last_seen'] = datetime.now(timezone.utc).isoformat()
                elif pd.notna(new_value):
                    upserted[field] = new_value
            elif change_type == 'significant':
                # Update significant changes
                upserted[field] = new_value
        
        return upserted
    
    def _is_newer_record(self, new_record: Union[pd.Series, Dict], existing_record: Dict) -> bool:
        """Check if new record is newer based on timestamp"""
        if isinstance(new_record, pd.Series):
            new_record = new_record.to_dict()
        
        new_time = new_record.get('timestamp') or new_record.get('time')
        existing_time = existing_record.get('timestamp') or existing_record.get('time')
        
        if pd.notna(new_time) and pd.notna(existing_time):
            return pd.Timestamp(new_time) > pd.Timestamp(existing_time)
        
        return pd.notna(new_time)  # Prefer records with timestamps
    
    def vectorize_for_ml(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Vectorize data for machine learning models"""
        if not self.config.vectorization_enabled:
            return None
        
        self._log_event('standard', 'vectorization', f'Starting ML vectorization for {filename}')
        
        vectorization_result = {
            'numerical_features': [],
            'categorical_features': [],
            'temporal_features': [],
            'network_features': [],
            'feature_names': [],
            'encoding_maps': {},
            'statistics': {},
            'tensor_ready': True
        }
        
        try:
            # Process numerical features
            for field in self.VECTOR_FIELD_MAPPINGS['numerical']:
                if field in df.columns:
                    values = pd.to_numeric(df[field], errors='coerce').fillna(0).values
                    if np.any(values != 0):
                        vectorization_result['numerical_features'].append(values.tolist())
                        vectorization_result['feature_names'].append(f'num_{field}')
                        
                        # Calculate statistics
                        valid_values = values[~np.isnan(values)]
                        if len(valid_values) > 0:
                            vectorization_result['statistics'][field] = {
                                'mean': float(np.mean(valid_values)),
                                'std': float(np.std(valid_values)),
                                'min': float(np.min(valid_values)),
                                'max': float(np.max(valid_values)),
                                'count': len(valid_values)
                            }
            
            # Process categorical features
            for field in self.VECTOR_FIELD_MAPPINGS['categorical']:
                if field in df.columns:
                    values = df[field].astype(str).fillna('unknown')
                    unique_values = values.unique()
                    
                    if len(unique_values) > 1:
                        # Create encoding map
                        encoding_map = {val: idx for idx, val in enumerate(unique_values)}
                        encoded_values = values.map(encoding_map).values
                        
                        vectorization_result['categorical_features'].append(encoded_values.tolist())
                        vectorization_result['feature_names'].append(f'cat_{field}')
                        vectorization_result['encoding_maps'][field] = encoding_map
            
            # Process temporal features
            for field in self.VECTOR_FIELD_MAPPINGS['temporal']:
                if field in df.columns:
                    timestamps = pd.to_datetime(df[field], errors='coerce')
                    valid_timestamps = timestamps.dropna()
                    
                    if len(valid_timestamps) > 0:
                        # Convert to hours since epoch, normalized
                        min_time = valid_timestamps.min().timestamp()
                        normalized_times = timestamps.apply(
                            lambda x: (x.timestamp() - min_time) / 3600 if pd.notna(x) else 0
                        ).values
                        
                        vectorization_result['temporal_features'].append(normalized_times.tolist())
                        vectorization_result['feature_names'].append(f'time_{field}')
            
            # Process network features (IP embeddings)
            network_embeddings = self._create_network_embeddings(df)
            if network_embeddings:
                vectorization_result['network_features'] = network_embeddings
                vectorization_result['feature_names'].extend(['ip_src_embed', 'ip_dst_embed', 'subnet_src', 'subnet_dst'])
            
            # Calculate final metrics
            total_features = (len(vectorization_result['numerical_features']) + 
                            len(vectorization_result['categorical_features']) + 
                            len(vectorization_result['temporal_features']) + 
                            len(vectorization_result['network_features']))
            
            final_result = {
                'feature_count': total_features,
                'tensor_shape': [len(df), total_features],
                'numerical_count': len(vectorization_result['numerical_features']),
                'categorical_count': len(vectorization_result['categorical_features']),
                'temporal_count': len(vectorization_result['temporal_features']),
                'network_count': len(vectorization_result['network_features']),
                'ready_for_ml': total_features > 0,
                'encoding_maps': vectorization_result['encoding_maps'],
                'statistics': vectorization_result['statistics'],
                'feature_names': vectorization_result['feature_names']
            }
            
            self._log_event('standard', 'vectorization', f'ML vectorization completed for {filename}', {
                'total_features': total_features,
                'tensor_shape': final_result['tensor_shape']
            })
            
            return final_result
            
        except Exception as e:
            self._log_event('standard', 'vectorization_error', f'Vectorization failed for {filename}: {str(e)}')
            return {'feature_count': 0, 'tensor_ready': False, 'error': str(e)}
    
    def _create_network_embeddings(self, df: pd.DataFrame) -> List[List[float]]:
        """Create network embeddings for IP addresses"""
        embeddings = []
        
        for ip_field in ['source_ip', 'destination_ip']:
            if ip_field in df.columns:
                ip_embeddings = df[ip_field].apply(self._ip_to_number).values.tolist()
                embeddings.append(ip_embeddings)
        
        # Add subnet embeddings
        for ip_field in ['source_ip', 'destination_ip']:
            if f'{ip_field}_subnet' in df.columns:
                subnet_embeddings = df[f'{ip_field}_subnet'].apply(self._subnet_to_hash).values.tolist()
                embeddings.append(subnet_embeddings)
        
        return embeddings
    
    def _ip_to_number(self, ip_address: str) -> float:
        """Convert IP address to numerical representation"""
        try:
            parts = str(ip_address).split('.')
            if len(parts) == 4:
                return sum(int(part) * (256 ** (3 - i)) for i, part in enumerate(parts))
            return 0.0
        except:
            return 0.0
    
    def _subnet_to_hash(self, subnet: str) -> float:
        """Convert subnet to hash value"""
        try:
            return float(hash(str(subnet)) % 10000)
        except:
            return 0.0
    
    def process_file(self, file_content: bytes, filename: str, file_type: str = None) -> ProcessingResult:
        """
        Process a single file with complete normalization pipeline
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: File type override (csv, excel, json)
            
        Returns:
            ProcessingResult with complete processing information
        """
        start_time = datetime.now()
        
        try:
            self._log_event('standard', 'file_processing', f'Starting complete processing pipeline for {filename}')
            
            # Determine file type
            if file_type is None:
                file_type = self._detect_file_type(filename)
            
            # Load and normalize data
            if file_type == 'excel':
                df = self.normalize_excel(file_content, filename)
            elif file_type == 'csv':
                df = self.normalize_csv(file_content, filename)
            elif file_type == 'json':
                df = self.normalize_json(file_content, filename)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            original_rows = len(df)
            
            # Handle cross-batch duplicates
            df, duplicate_info = self.handle_cross_batch_duplicates(df, filename)
            
            # Detect field mappings
            field_mapping = self._detect_field_mappings(df.columns) if self.config.field_mapping_enabled else {}
            
            # Vectorize for ML
            vectorization_result = self.vectorize_for_ml(df, filename)
            
            # Calculate quality metrics
            quality_score = self._calculate_quality_score(df)
            known_apps = df['is_known_app'].sum() if 'is_known_app' in df.columns else 0
            unknown_apps = len(df) - known_apps if 'is_known_app' in df.columns else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ProcessingResult(
                file_name=filename,
                original_rows=original_rows,
                processed_rows=len(df),
                quality_score=quality_score,
                known_applications=known_apps,
                unknown_applications=unknown_apps,
                duplicate_info=duplicate_info,
                field_mapping=field_mapping,
                vectorization_result=vectorization_result,
                processing_time=processing_time,
                status='completed'
            )
            
            self._log_event('standard', 'file_processing', f'Complete processing pipeline finished for {filename}', {
                'processing_time': processing_time,
                'quality_score': quality_score,
                'processed_rows': len(df)
            })
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._log_event('standard', 'error', f'Processing pipeline failed for {filename}: {str(e)}')
            
            return ProcessingResult(
                file_name=filename,
                original_rows=0,
                processed_rows=0,
                quality_score=0.0,
                known_applications=0,
                unknown_applications=0,
                duplicate_info={},
                field_mapping={},
                vectorization_result=None,
                processing_time=processing_time,
                status='error',
                errors=[str(e)]
            )
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        filename_lower = filename.lower()
        if filename_lower.endswith(('.xlsx', '.xls')):
            return 'excel'
        elif filename_lower.endswith('.csv'):
            return 'csv'
        elif filename_lower.endswith('.json'):
            return 'json'
        else:
            raise ValueError(f"Cannot determine file type for {filename}")
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score"""
        if len(df) == 0:
            return 0.0
        
        scores = []
        
        # Application completeness score
        if 'is_known_app' in df.columns:
            app_score = df['is_known_app'].mean()
            scores.append(app_score)
        
        # Data completeness score
        completeness_score = 1 - df.isnull().mean().mean()
        scores.append(completeness_score)
        
        # Network field completeness
        network_fields = ['source_ip', 'destination_ip', 'protocol']
        available_network_fields = [f for f in network_fields if f in df.columns]
        if available_network_fields:
            network_completeness = 1 - df[available_network_fields].isnull().mean().mean()
            scores.append(network_completeness)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def export_normalized_data(self, output_path: str, format: str = 'csv') -> None:
        """Export all normalized data from global record store"""
        
        if not self.global_record_store:
            self._log_event('standard', 'export', 'No data available for export')
            return
        
        # Convert global record store to DataFrame
        records = []
        for key, record_info in self.global_record_store.items():
            record = record_info['data'].copy()
            record['_global_key'] = key
            record['_first_seen'] = record_info['first_seen']
            record['_last_updated'] = record_info['last_updated']
            record['_update_count'] = record_info.get('update_count', 0)
            records.append(record)
        
        df = pd.DataFrame(records)
        
        # Export in specified format
        if format.lower() == 'csv':
            df.to_csv(output_path, index=False)
        elif format.lower() == 'excel':
            df.to_excel(output_path, index=False)
        elif format.lower() == 'json':
            df.to_json(output_path, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self._log_event('standard', 'export', f'Normalized data exported to {output_path}', {
            'format': format,
            'record_count': len(df),
            'file_path': output_path
        })
    
    def get_processing_logs(self) -> List[Dict[str, Any]]:
        """Get all processing logs"""
        return self.processing_logs.copy()
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global processing statistics"""
        return {
            'total_unique_records': len(self.global_record_store),
            'session_id': self.session_id,
            'total_log_entries': len(self.processing_logs),
            'processing_config': asdict(self.config)
        }

# Factory function for easy instantiation
def create_normalizer(config: Dict[str, Any] = None) -> DataNormalizer:
    """
    Factory function to create DataNormalizer instance
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured DataNormalizer instance
    """
    if config:
        processing_config = ProcessingConfig(**config)
    else:
        processing_config = ProcessingConfig()
    
    return DataNormalizer(processing_config)