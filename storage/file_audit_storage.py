# storage/file_audit_storage.py - File-based Audit Storage System

import json
import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Generator
from collections import defaultdict, deque
import asyncio
import aiofiles
import aiofiles.os
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid

class StorageFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"  # JSON Lines - one JSON object per line
    COMPRESSED = "gz"

class FileRotation(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    SIZE_BASED = "size"

@dataclass
class StorageConfig:
    """Configuration for file-based audit storage"""
    base_path: str = "essentials/audit"
    format: StorageFormat = StorageFormat.JSONL
    rotation: FileRotation = FileRotation.DAILY
    max_file_size_mb: int = 100
    compress_old_files: bool = True
    retention_days: int = 365
    backup_enabled: bool = True
    index_enabled: bool = True
    
class FileAuditStorage:
    """File-based audit storage with rotation, compression, and indexing"""
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        
        # Create directory structure
        self.events_dir = self.base_path / "events"
        self.indexes_dir = self.base_path / "indexes"
        self.archives_dir = self.base_path / "archives"
        self.backups_dir = self.base_path / "backups"
        self.reports_dir = self.base_path / "reports"
        self.temp_dir = self.base_path / "temp"
        
        # In-memory caches for performance
        self.failed_login_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.user_risk_profiles: Dict[str, Dict] = {}
        self.suspicious_ips: Dict[str, Dict] = {}
        self.device_trust_scores: Dict[str, float] = {}
        
        # Lazy initialization flags
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Initialize storage synchronously (directory creation only)
        self._ensure_directories_exist()
    
    def _ensure_directories_exist(self):
        """Ensure required directories exist (synchronous)"""
        try:
            # Create all directories synchronously
            for directory in [self.events_dir, self.indexes_dir, self.archives_dir, 
                            self.backups_dir, self.reports_dir, self.temp_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories by date for better organization
            today = datetime.now()
            year_month_dir = self.events_dir / f"{today.year:04d}" / f"{today.month:02d}"
            year_month_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ Created audit directories at: {self.base_path}")
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
    
    async def _ensure_initialized(self):
        """Ensure storage is initialized (lazy initialization)"""
        if not self._initialized:
            async with self._initialization_lock:
                if not self._initialized:  # Double-check pattern
                    await self._initialize_storage()
                    self._initialized = True
    
    async def _initialize_storage(self):
        """Initialize the storage system and directory structure"""
        try:
            # Directories already created synchronously, just load data
            await self._load_existing_data()
            
            # Start background tasks
            asyncio.create_task(self._background_maintenance())
            
            print(f"✅ File-based audit storage initialized at: {self.base_path}")
            
        except Exception as e:
            print(f"❌ Error initializing audit storage: {e}")
    
    async def _load_existing_data(self):
        """Load existing audit data into memory caches"""
        try:
            # Load recent events (last 7 days) into memory for fast access
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # Scan recent event files
            for year_dir in self.events_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    for event_file in month_dir.glob("*.jsonl"):
                        file_date = self._extract_date_from_filename(event_file.name)
                        if file_date and file_date >= cutoff_date:
                            await self._load_file_into_cache(event_file)
                            
            print(f"📊 Loaded cache data: {len(self.user_risk_profiles)} users, {len(self.suspicious_ips)} IPs")
                            
        except Exception as e:
            print(f"⚠️ Error loading existing data: {e}")
    
    async def _load_file_into_cache(self, file_path: Path):
        """Load a single file into memory cache"""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                async for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        await self._update_caches_from_event(event_data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️ Error loading file {file_path}: {e}")
    
    async def _update_caches_from_event(self, event_data: Dict[str, Any]):
        """Update in-memory caches from event data"""
        try:
            user_id = event_data.get('user_id')
            if not user_id:
                return
            
            # Update failed login tracking
            if (event_data.get('event_type') == 'authentication' and 
                event_data.get('result') == 'failure'):
                
                self.failed_login_attempts[user_id].append({
                    'timestamp': datetime.fromisoformat(event_data.get('timestamp', '')),
                    'source_ip': event_data.get('source_ip'),
                    'reason': event_data.get('auth_details', {}).get('failure_reason', 'Unknown')
                })
                
                # Update IP reputation
                source_ip = event_data.get('source_ip')
                if source_ip:
                    if source_ip not in self.suspicious_ips:
                        self.suspicious_ips[source_ip] = {
                            'count': 0, 
                            'first_seen': datetime.fromisoformat(event_data.get('timestamp', ''))
                        }
                    self.suspicious_ips[source_ip]['count'] += 1
                    self.suspicious_ips[source_ip]['last_seen'] = datetime.fromisoformat(event_data.get('timestamp', ''))
            
            # Update user risk profile
            if user_id not in self.user_risk_profiles:
                self.user_risk_profiles[user_id] = {
                    'last_successful_login': None,
                    'failed_login_count_24h': 0,
                    'locations': set(),
                    'devices': set(),
                    'average_risk_score': 0.0,
                    'last_updated': datetime.fromisoformat(event_data.get('timestamp', ''))
                }
            
            profile = self.user_risk_profiles[user_id]
            
            # Update geographic and device info
            if event_data.get('geographic_info', {}).get('country'):
                profile['locations'].add(event_data['geographic_info']['country'])
            
            if event_data.get('device_info', {}).get('device_fingerprint'):
                profile['devices'].add(event_data['device_info']['device_fingerprint'])
            
            # Update risk score
            risk_assessment = event_data.get('risk_assessment', {})
            if risk_assessment and 'risk_score' in risk_assessment:
                current_avg = profile['average_risk_score']
                new_score = risk_assessment['risk_score']
                profile['average_risk_score'] = (current_avg * 0.8) + (new_score * 0.2)
                
        except Exception as e:
            print(f"⚠️ Error updating caches from event: {e}")
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from event filename"""
        try:
            # Expected format: events_2024-01-15.jsonl
            date_part = filename.replace('events_', '').replace('.jsonl', '').replace('.json', '').replace('.gz', '')
            return datetime.strptime(date_part, '%Y-%m-%d')
        except:
            return None
    
    def _get_current_file_path(self, timestamp: datetime = None) -> Path:
        """Get the current file path for storing events"""
        if timestamp is None:
            timestamp = datetime.now()
        
        year_month_dir = self.events_dir / f"{timestamp.year:04d}" / f"{timestamp.month:02d}"
        
        if self.config.rotation == FileRotation.HOURLY:
            filename = f"events_{timestamp.strftime('%Y-%m-%d_%H')}.{self.config.format.value}"
        elif self.config.rotation == FileRotation.DAILY:
            filename = f"events_{timestamp.strftime('%Y-%m-%d')}.{self.config.format.value}"
        elif self.config.rotation == FileRotation.WEEKLY:
            week_start = timestamp - timedelta(days=timestamp.weekday())
            filename = f"events_{week_start.strftime('%Y-%m-%d')}_week.{self.config.format.value}"
        else:  # SIZE_BASED
            filename = f"events_{timestamp.strftime('%Y-%m-%d')}.{self.config.format.value}"
        
        return year_month_dir / filename
    
    async def store_event(self, event: Dict[str, Any]) -> str:
        """Store audit event to file system"""
        await self._ensure_initialized()  # Ensure initialization
        
        try:
            # Ensure timestamp and event_id
            if 'timestamp' not in event:
                event['timestamp'] = datetime.utcnow().isoformat()
            if 'event_id' not in event:
                event['event_id'] = str(uuid.uuid4())
            
            timestamp = datetime.fromisoformat(event['timestamp'])
            
            # Get file path and ensure directory exists
            file_path = self._get_current_file_path(timestamp)
            await aiofiles.os.makedirs(file_path.parent, exist_ok=True)
            
            # Check if file rotation is needed (size-based)
            if self.config.rotation == FileRotation.SIZE_BASED:
                if await self._should_rotate_file(file_path):
                    file_path = await self._rotate_file(file_path)
            
            # Write event to file
            if self.config.format == StorageFormat.JSONL:
                event_line = json.dumps(event, default=str) + '\n'
                async with aiofiles.open(file_path, 'a') as f:
                    await f.write(event_line)
            else:  # JSON format
                # For JSON format, we need to read, update, and write
                await self._append_to_json_file(file_path, event)
            
            # Update in-memory caches
            await self._update_caches_from_event(event)
            
            # Update index if enabled
            if self.config.index_enabled:
                await self._update_index(event)
            
            return event['event_id']
            
        except Exception as e:
            print(f"❌ Error storing event: {e}")
            raise
    
    async def _should_rotate_file(self, file_path: Path) -> bool:
        """Check if file should be rotated based on size"""
        try:
            if not file_path.exists():
                return False
            
            stat = await aiofiles.os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            return size_mb >= self.config.max_file_size_mb
        except:
            return False
    
    async def _rotate_file(self, file_path: Path) -> Path:
        """Rotate file when size limit is reached"""
        try:
            # Create new filename with rotation number
            base_name = file_path.stem
            extension = file_path.suffix
            counter = 1
            
            while True:
                new_path = file_path.parent / f"{base_name}_{counter:03d}{extension}"
                if not new_path.exists():
                    break
                counter += 1
            
            # Move current file to rotated name
            await aiofiles.os.rename(file_path, new_path)
            
            # Compress if enabled
            if self.config.compress_old_files:
                await self._compress_file(new_path)
            
            return file_path  # Return original path for new file
            
        except Exception as e:
            print(f"⚠️ Error rotating file: {e}")
            return file_path
    
    async def _compress_file(self, file_path: Path):
        """Compress a file using gzip"""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            # Use asyncio to run compression in thread pool
            def compress_sync():
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file_path)
            
            await asyncio.get_event_loop().run_in_executor(None, compress_sync)
            print(f"🗜️ Compressed {file_path.name} -> {compressed_path.name}")
            
        except Exception as e:
            print(f"⚠️ Error compressing file: {e}")
    
    async def _append_to_json_file(self, file_path: Path, event: Dict[str, Any]):
        """Append event to JSON array file"""
        try:
            events = []
            
            # Read existing events if file exists
            if file_path.exists():
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        events = json.loads(content)
            
            # Add new event
            events.append(event)
            
            # Write back to file
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(events, indent=2, default=str))
                
        except Exception as e:
            print(f"⚠️ Error appending to JSON file: {e}")
    
    async def _update_index(self, event: Dict[str, Any]):
        """Update search indexes for fast querying"""
        try:
            timestamp = datetime.fromisoformat(event['timestamp'])
            index_date = timestamp.strftime('%Y-%m')
            index_file = self.indexes_dir / f"index_{index_date}.json"
            
            # Create index entry
            index_entry = {
                'event_id': event['event_id'],
                'timestamp': event['timestamp'],
                'user_id': event['user_id'],
                'event_type': event['event_type'],
                'result': event['result'],
                'source_ip': event.get('source_ip'),
                'file_path': str(self._get_current_file_path(timestamp))
            }
            
            # Load existing index
            index_data = {'events': []}
            if index_file.exists():
                async with aiofiles.open(index_file, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        index_data = json.loads(content)
            
            # Add new entry and save
            index_data['events'].append(index_entry)
            
            async with aiofiles.open(index_file, 'w') as f:
                await f.write(json.dumps(index_data, indent=2, default=str))
                
        except Exception as e:
            print(f"⚠️ Error updating index: {e}")
    
    async def query_events(self, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          user_ids: List[str] = None,
                          event_types: List[str] = None,
                          results: List[str] = None,
                          source_ips: List[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Query events from file storage"""
        await self._ensure_initialized()  # Ensure initialization
        
        try:
            events = []
            
            # Determine date range for file scanning
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Scan relevant files
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= end_date:
                year_month_dir = self.events_dir / f"{current_date.year:04d}" / f"{current_date.month:02d}"
                
                if year_month_dir.exists():
                    # Find files for this date
                    pattern = f"events_{current_date.strftime('%Y-%m-%d')}*"
                    for file_path in year_month_dir.glob(pattern):
                        file_events = await self._read_events_from_file(file_path)
                        
                        # Apply filters
                        for event in file_events:
                            if self._event_matches_filters(event, user_ids, event_types, results, source_ips):
                                event_time = datetime.fromisoformat(event['timestamp'])
                                if start_date <= event_time <= end_date:
                                    events.append(event)
                                    
                                    # Respect limit
                                    if len(events) >= limit:
                                        return sorted(events, key=lambda x: x['timestamp'], reverse=True)
                
                current_date += timedelta(days=1)
            
            return sorted(events, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error querying events: {e}")
            return []
    
    async def _read_events_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read events from a single file"""
        try:
            events = []
            
            # Handle compressed files
            if file_path.suffix == '.gz':
                def read_compressed():
                    with gzip.open(file_path, 'rt') as f:
                        if file_path.name.endswith('.jsonl.gz'):
                            return [json.loads(line.strip()) for line in f if line.strip()]
                        else:
                            content = f.read()
                            return json.loads(content) if content.strip() else []
                
                events = await asyncio.get_event_loop().run_in_executor(None, read_compressed)
            
            elif self.config.format == StorageFormat.JSONL:
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            else:  # JSON format
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        events = json.loads(content)
            
            return events if isinstance(events, list) else []
            
        except Exception as e:
            print(f"⚠️ Error reading file {file_path}: {e}")
            return []
    
    def _event_matches_filters(self, event: Dict[str, Any], 
                              user_ids: List[str] = None,
                              event_types: List[str] = None,
                              results: List[str] = None,
                              source_ips: List[str] = None) -> bool:
        """Check if event matches the given filters"""
        if user_ids and event.get('user_id') not in user_ids:
            return False
        if event_types and event.get('event_type') not in event_types:
            return False
        if results and event.get('result') not in results:
            return False
        if source_ips and event.get('source_ip') not in source_ips:
            return False
        return True
    
    async def get_summary_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics from stored events"""
        await self._ensure_initialized()  # Ensure initialization
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            events = await self.query_events(start_date=cutoff_date, limit=10000)
            
            if not events:
                return {
                    'total_events': 0,
                    'event_type_breakdown': {},
                    'result_breakdown': {},
                    'top_users': [],
                    'top_ips': [],
                    'time_range': {'start': cutoff_date, 'end': datetime.now()}
                }
            
            # Calculate statistics
            event_type_breakdown = defaultdict(int)
            result_breakdown = defaultdict(int)
            user_counts = defaultdict(int)
            ip_counts = defaultdict(int)
            
            for event in events:
                event_type_breakdown[event.get('event_type', 'unknown')] += 1
                result_breakdown[event.get('result', 'unknown')] += 1
                user_counts[event.get('user_id', 'unknown')] += 1
                if event.get('source_ip'):
                    ip_counts[event.get('source_ip')] += 1
            
            # Get top users and IPs
            top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_events': len(events),
                'event_type_breakdown': dict(event_type_breakdown),
                'result_breakdown': dict(result_breakdown),
                'top_users': [{'user_id': k, 'count': v} for k, v in top_users],
                'top_ips': [{'ip_address': k, 'count': v} for k, v in top_ips],
                'time_range': {
                    'start': min(e['timestamp'] for e in events),
                    'end': max(e['timestamp'] for e in events)
                }
            }
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return {}
    
    async def export_events(self, 
                           start_date: datetime, 
                           end_date: datetime,
                           format: str = "json",
                           output_path: str = None) -> str:
        """Export events to a file"""
        await self._ensure_initialized()  # Ensure initialization
        
        try:
            events = await self.query_events(start_date=start_date, end_date=end_date, limit=100000)
            
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = str(self.reports_dir / f"export_{timestamp}.{format}")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(json.dumps(events, indent=2, default=str))
            
            elif format.lower() == 'csv':
                import csv
                import io
                
                # Convert to CSV format
                def to_csv():
                    output = io.StringIO()
                    if events:
                        writer = csv.DictWriter(output, fieldnames=events[0].keys())
                        writer.writeheader()
                        for event in events:
                            # Flatten nested dicts for CSV
                            flattened = self._flatten_dict(event)
                            writer.writerow(flattened)
                    return output.getvalue()
                
                csv_content = await asyncio.get_event_loop().run_in_executor(None, to_csv)
                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(csv_content)
            
            print(f"📄 Exported {len(events)} events to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error exporting events: {e}")
            raise
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    async def _background_maintenance(self):
        """Background task for maintenance operations"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Cleanup old files based on retention policy
                await self._cleanup_old_files()
                
                # Compress old files
                if self.config.compress_old_files:
                    await self._compress_old_files()
                
                # Create backup if enabled
                if self.config.backup_enabled:
                    await self._create_backup()
                
                # Update cache statistics
                await self._update_cache_statistics()
                
            except Exception as e:
                print(f"⚠️ Error in background maintenance: {e}")
    
    async def _cleanup_old_files(self):
        """Remove files older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            deleted_count = 0
            
            for year_dir in self.events_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    for file_path in month_dir.iterdir():
                        if file_path.is_file():
                            file_date = self._extract_date_from_filename(file_path.name)
                            if file_date and file_date < cutoff_date:
                                await aiofiles.os.remove(file_path)
                                deleted_count += 1
            
            if deleted_count > 0:
                print(f"🗑️ Cleaned up {deleted_count} old audit files")
                
        except Exception as e:
            print(f"⚠️ Error cleaning up old files: {e}")
    
    async def _compress_old_files(self):
        """Compress files older than 7 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            compressed_count = 0
            
            for year_dir in self.events_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    for file_path in month_dir.iterdir():
                        if file_path.is_file() and not file_path.name.endswith('.gz'):
                            file_date = self._extract_date_from_filename(file_path.name)
                            if file_date and file_date < cutoff_date:
                                await self._compress_file(file_path)
                                compressed_count += 1
            
            if compressed_count > 0:
                print(f"🗜️ Compressed {compressed_count} old audit files")
                
        except Exception as e:
            print(f"⚠️ Error compressing old files: {e}")
    
    async def _create_backup(self):
        """Create backup of audit data"""
        try:
            # Create monthly backups
            now = datetime.now()
            backup_name = f"audit_backup_{now.strftime('%Y_%m')}.tar.gz"
            backup_path = self.backups_dir / backup_name
            
            # Only create backup if it doesn't exist
            if not backup_path.exists():
                def create_backup_sync():
                    import tarfile
                    with tarfile.open(backup_path, 'w:gz') as tar:
                        tar.add(self.events_dir, arcname='events')
                        tar.add(self.indexes_dir, arcname='indexes')
                
                await asyncio.get_event_loop().run_in_executor(None, create_backup_sync)
                print(f"💾 Created backup: {backup_name}")
                
        except Exception as e:
            print(f"⚠️ Error creating backup: {e}")
    
    async def _update_cache_statistics(self):
        """Update and save cache statistics"""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'user_profiles': len(self.user_risk_profiles),
                'suspicious_ips': len(self.suspicious_ips),
                'device_trust_scores': len(self.device_trust_scores),
                'total_failed_attempts': sum(len(attempts) for attempts in self.failed_login_attempts.values())
            }
            
            stats_file = self.base_path / "cache_stats.json"
            async with aiofiles.open(stats_file, 'w') as f:
                await f.write(json.dumps(stats, indent=2))
                
        except Exception as e:
            print(f"⚠️ Error updating cache statistics: {e}")
    
    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage system"""
        await self._ensure_initialized()  # Ensure initialization
        
        try:
            total_size = 0
            file_count = 0
            
            # Calculate total storage size
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'base_path': str(self.base_path),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_files': file_count,
                'storage_format': self.config.format.value,
                'rotation_policy': self.config.rotation.value,
                'compression_enabled': self.config.compress_old_files,
                'retention_days': self.config.retention_days,
                'cache_statistics': {
                    'user_profiles': len(self.user_risk_profiles),
                    'suspicious_ips': len(self.suspicious_ips),
                    'failed_attempts_tracking': len(self.failed_login_attempts)
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting storage info: {e}")
            return {}

# =================== INTEGRATION WITH EXISTING AUDIT ROUTER ===================

# Update the existing audit router to use file storage
class FileBasedAuditStorage:
    """Updated audit storage using file system"""
    
    def __init__(self):
        # Initialize storage with lazy initialization
        self.file_storage = FileAuditStorage()
        
        # Delegate properties to file storage
        self.failed_login_attempts = self.file_storage.failed_login_attempts
        self.user_risk_profiles = self.file_storage.user_risk_profiles
        self.suspicious_ips = self.file_storage.suspicious_ips
        self.device_trust_scores = self.file_storage.device_trust_scores
    
    async def store_event(self, event) -> str:
        """Store audit event using file storage"""
        # Convert Pydantic model to dict if needed
        if hasattr(event, 'dict'):
            event_dict = event.dict()
        else:
            event_dict = event
        
        return await self.file_storage.store_event(event_dict)
    
    async def query_events(self, **kwargs):
        """Query events from file storage"""
        return await self.file_storage.query_events(**kwargs)
    
    async def get_summary(self, days: int = 7):
        """Get summary statistics"""
        return await self.file_storage.get_summary_statistics(days)
    
    async def export_data(self, start_date, end_date, format="json"):
        """Export audit data"""
        return await self.file_storage.export_events(start_date, end_date, format)

# =================== USAGE EXAMPLE ===================

async def example_usage():
    """Example of how to use the file-based audit storage"""
    
    # Initialize storage
    storage = FileAuditStorage()
    
    # Store some sample events
    sample_events = [
        {
            "event_type": "authentication",
            "user_id": "john.doe@company.com",
            "action": "login",
            "result": "failure",
            "source_ip": "192.168.1.100",
            "auth_details": {
                "identity_provider": "AzureAD",
                "failure_reason": "Invalid password"
            },
            "device_info": {
                "device_fingerprint": "device_001"
            },
            "geographic_info": {
                "country": "United States"
            }
        },
        {
            "event_type": "authentication",
            "user_id": "jane.smith@company.com",
            "action": "login", 
            "result": "success",
            "source_ip": "192.168.1.101",
            "auth_details": {
                "identity_provider": "Okta",
                "mfa_method": "push_notification"
            }
        }
    ]
    
    # Store events
    for event in sample_events:
        event_id = await storage.store_event(event)
        print(f"Stored event: {event_id}")
    
    # Query events
    events = await storage.query_events(
        start_date=datetime.now() - timedelta(days=1),
        event_types=["authentication"]
    )
    print(f"Found {len(events)} authentication events")
    
    # Get summary
    summary = await storage.get_summary_statistics(days=7)
    print(f"Summary: {summary}")
    
    # Export data
    export_path = await storage.export_events(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        format="json"
    )
    print(f"Exported to: {export_path}")
    
    # Get storage info
    info = await storage.get_storage_info()
    print(f"Storage info: {info}")

if __name__ == "__main__":
    asyncio.run(example_usage())