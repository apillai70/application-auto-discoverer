# storage/log_storage_manager.py
"""
Log Storage Manager for handling different types of logs in essentials/logs directory
Integrates with file_audit_storage.py for comprehensive logging solution
"""

import json
import asyncio
import aiofiles
import aiofiles.os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
import gzip

class LogCategory(str, Enum):
    APPLICATION = "application"
    SECURITY = "security"
    NETWORK = "network"
    THREATS = "threats"
    PERFORMANCE = "performance"
    AUDIT = "audit"
    DEBUG = "debug"

class LogFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"
    TEXT = "txt"

@dataclass
class LogStorageConfig:
    """Configuration for log storage"""
    base_path: str = "essentials/logs"
    max_file_size_mb: int = 50
    retention_days: int = 90
    compress_after_days: int = 7
    format: LogFormat = LogFormat.JSONL
    enable_rotation: bool = True
    enable_compression: bool = True

@dataclass
class LogEntry:
    """Standard log entry structure"""
    timestamp: datetime
    level: str
    category: LogCategory
    component: str
    message: str
    details: Dict[str, Any]
    log_id: str = None
    session_id: str = None
    user_id: str = None
    source_ip: str = None
    
    def __post_init__(self):
        if self.log_id is None:
            self.log_id = str(uuid.uuid4())

class LogStorageManager:
    """Manages different types of logs in the essentials/logs directory structure"""
    
    def __init__(self, config: LogStorageConfig = None):
        self.config = config or LogStorageConfig()
        self.base_path = Path(self.config.base_path)
        
        # Create log directory structure
        self.log_dirs = {
            LogCategory.APPLICATION: self.base_path / "application",
            LogCategory.SECURITY: self.base_path / "security", 
            LogCategory.NETWORK: self.base_path / "network",
            LogCategory.THREATS: self.base_path / "threats",
            LogCategory.PERFORMANCE: self.base_path / "performance",
            LogCategory.AUDIT: self.base_path / "audit",
            LogCategory.DEBUG: self.base_path / "debug"
        }
        
        # Create all directories
        self._ensure_directories_exist()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Background maintenance
        asyncio.create_task(self._background_maintenance())
    
    def _ensure_directories_exist(self):
        """Create all required log directories"""
        try:
            for category, directory in self.log_dirs.items():
                directory.mkdir(parents=True, exist_ok=True)
                
                # Create subdirectories by date for better organization
                today = datetime.now()
                year_month_dir = directory / f"{today.year:04d}" / f"{today.month:02d}"
                year_month_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Created log directories at: {self.base_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating log directories: {e}")
    
    def _get_log_file_path(self, category: LogCategory, timestamp: datetime = None) -> Path:
        """Get the log file path for a specific category and timestamp"""
        if timestamp is None:
            timestamp = datetime.now()
        
        base_dir = self.log_dirs[category]
        year_month_dir = base_dir / f"{timestamp.year:04d}" / f"{timestamp.month:02d}"
        
        # Ensure directory exists
        year_month_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with date
        filename = f"{category.value}_{timestamp.strftime('%Y-%m-%d')}.{self.config.format.value}"
        
        return year_month_dir / filename
    
    async def _write_log_entry(self, entry: LogEntry):
        """Write a log entry to the appropriate file"""
        try:
            file_path = self._get_log_file_path(entry.category, entry.timestamp)
            
            # Check if file rotation is needed
            if self.config.enable_rotation:
                await self._check_and_rotate_file(file_path)
            
            # Prepare log data
            log_data = asdict(entry)
            log_data['timestamp'] = entry.timestamp.isoformat()
            
            # Write based on format
            if self.config.format == LogFormat.JSONL:
                log_line = json.dumps(log_data, default=str) + '\n'
                async with aiofiles.open(file_path, 'a') as f:
                    await f.write(log_line)
            
            elif self.config.format == LogFormat.JSON:
                # For JSON format, read existing, append, and write back
                await self._append_to_json_file(file_path, log_data)
            
            else:  # TEXT format
                text_line = f"[{entry.timestamp.isoformat()}] {entry.level.upper()} - {entry.component}: {entry.message}\n"
                async with aiofiles.open(file_path, 'a') as f:
                    await f.write(text_line)
                    
        except Exception as e:
            self.logger.error(f"Error writing log entry: {e}")
    
    async def _append_to_json_file(self, file_path: Path, log_data: Dict[str, Any]):
        """Append log data to JSON array file"""
        try:
            logs = []
            
            # Read existing logs if file exists
            if file_path.exists():
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        logs = json.loads(content)
            
            # Add new log
            logs.append(log_data)
            
            # Write back to file
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(logs, indent=2, default=str))
                
        except Exception as e:
            self.logger.error(f"Error appending to JSON file: {e}")
    
    async def _check_and_rotate_file(self, file_path: Path):
        """Check if file needs rotation and rotate if necessary"""
        try:
            if not file_path.exists():
                return
            
            stat = await aiofiles.os.stat(file_path)
            size_mb = stat.st_size / (1024 * 1024)
            
            if size_mb >= self.config.max_file_size_mb:
                await self._rotate_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Error checking file rotation: {e}")
    
    async def _rotate_file(self, file_path: Path):
        """Rotate log file when size limit is reached"""
        try:
            base_name = file_path.stem
            extension = file_path.suffix
            counter = 1
            
            # Find next available rotation name
            while True:
                new_path = file_path.parent / f"{base_name}_{counter:03d}{extension}"
                if not new_path.exists():
                    break
                counter += 1
            
            # Move current file to rotated name
            await aiofiles.os.rename(file_path, new_path)
            
            # Compress if enabled
            if self.config.enable_compression:
                await self._compress_file(new_path)
            
            self.logger.info(f"Rotated log file: {file_path.name} -> {new_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error rotating file: {e}")
    
    async def _compress_file(self, file_path: Path):
        """Compress a log file using gzip"""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            def compress_sync():
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                file_path.unlink()  # Remove original file
            
            await asyncio.get_event_loop().run_in_executor(None, compress_sync)
            self.logger.info(f"Compressed log file: {file_path.name} -> {compressed_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error compressing file: {e}")
    
    # Public logging methods
    
    async def log_application_event(self, level: str, component: str, message: str, 
                                  details: Dict[str, Any] = None, user_id: str = None,
                                  session_id: str = None, source_ip: str = None):
        """Log application events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=LogCategory.APPLICATION,
            component=component,
            message=message,
            details=details or {},
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip
        )
        await self._write_log_entry(entry)
    
    async def log_security_event(self, level: str, message: str, 
                               details: Dict[str, Any] = None, user_id: str = None,
                               session_id: str = None, source_ip: str = None):
        """Log security events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=LogCategory.SECURITY,
            component="security_system",
            message=message,
            details=details or {},
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip
        )
        await self._write_log_entry(entry)
    
    async def log_network_event(self, event_type: str, source_ip: str, dest_ip: str,
                              details: Dict[str, Any] = None):
        """Log network topology and flow events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="info",
            category=LogCategory.NETWORK,
            component="network_mapper",
            message=f"Network event: {event_type} from {source_ip} to {dest_ip}",
            details=details or {},
            source_ip=source_ip
        )
        await self._write_log_entry(entry)
    
    async def log_threat_event(self, threat_type: str, severity: str,
                             details: Dict[str, Any] = None, source_ip: str = None):
        """Log threat detection events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=severity,
            category=LogCategory.THREATS,
            component="threat_detection",
            message=f"Threat detected: {threat_type}",
            details=details or {},
            source_ip=source_ip
        )
        await self._write_log_entry(entry)
    
    async def log_performance_event(self, metric_name: str, value: float,
                                  details: Dict[str, Any] = None, component: str = "system"):
        """Log performance monitoring events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="info",
            category=LogCategory.PERFORMANCE,
            component=component,
            message=f"Performance metric: {metric_name} = {value}",
            details=details or {}
        )
        await self._write_log_entry(entry)
    
    async def log_audit_event(self, action: str, result: str, user_id: str,
                            details: Dict[str, Any] = None, source_ip: str = None):
        """Log audit events (duplicates to audit storage for backup)"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="info",
            category=LogCategory.AUDIT,
            component="audit_system",
            message=f"Audit: {action} - {result}",
            details=details or {},
            user_id=user_id,
            source_ip=source_ip
        )
        await self._write_log_entry(entry)
    
    async def log_debug_event(self, component: str, message: str,
                            details: Dict[str, Any] = None):
        """Log debug events"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level="debug",
            category=LogCategory.DEBUG,
            component=component,
            message=message,
            details=details or {}
        )
        await self._write_log_entry(entry)
    
    # Query and export methods
    
    async def query_logs(self, category: LogCategory, 
                        start_date: datetime = None,
                        end_date: datetime = None,
                        level: str = None,
                        component: str = None,
                        user_id: str = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Query logs from storage"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            logs = []
            
            # Scan files in date range
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= end_date and len(logs) < limit:
                file_path = self._get_log_file_path(category, current_date)
                
                if file_path.exists():
                    file_logs = await self._read_logs_from_file(file_path)
                    
                    # Apply filters
                    for log in file_logs:
                        if self._log_matches_filters(log, level, component, user_id):
                            log_time = datetime.fromisoformat(log['timestamp'])
                            if start_date <= log_time <= end_date:
                                logs.append(log)
                                
                                if len(logs) >= limit:
                                    break
                
                current_date += timedelta(days=1)
            
            return sorted(logs, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error querying logs: {e}")
            return []
    
    async def _read_logs_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read logs from a single file"""
        try:
            logs = []
            
            # Handle compressed files
            if file_path.suffix == '.gz':
                def read_compressed():
                    with gzip.open(file_path, 'rt') as f:
                        if self.config.format == LogFormat.JSONL:
                            return [json.loads(line.strip()) for line in f if line.strip()]
                        elif self.config.format == LogFormat.JSON:
                            content = f.read()
                            return json.loads(content) if content.strip() else []
                        else:  # TEXT format
                            return []  # Text format doesn't support structured querying
                
                logs = await asyncio.get_event_loop().run_in_executor(None, read_compressed)
            
            elif self.config.format == LogFormat.JSONL:
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        line = line.strip()
                        if line:
                            try:
                                logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            
            elif self.config.format == LogFormat.JSON:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        logs = json.loads(content)
            
            return logs if isinstance(logs, list) else []
            
        except Exception as e:
            self.logger.error(f"Error reading log file {file_path}: {e}")
            return []
    
    def _log_matches_filters(self, log: Dict[str, Any], level: str = None,
                           component: str = None, user_id: str = None) -> bool:
        """Check if log entry matches the given filters"""
        if level and log.get('level') != level:
            return False
        if component and log.get('component') != component:
            return False
        if user_id and log.get('user_id') != user_id:
            return False
        return True
    
    async def export_logs(self, category: LogCategory, start_date: datetime,
                         end_date: datetime, format: str = "json",
                         output_path: str = None) -> str:
        """Export logs to a file"""
        try:
            logs = await self.query_logs(
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=100000
            )
            
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"results/logs/{category.value}_export_{timestamp}.{format}"
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(json.dumps(logs, indent=2, default=str))
            
            elif format.lower() == 'csv':
                import csv
                import io
                
                def to_csv():
                    output = io.StringIO()
                    if logs:
                        # Flatten nested dictionaries for CSV
                        flattened_logs = [self._flatten_dict(log) for log in logs]
                        writer = csv.DictWriter(output, fieldnames=flattened_logs[0].keys())
                        writer.writeheader()
                        writer.writerows(flattened_logs)
                    return output.getvalue()
                
                csv_content = await asyncio.get_event_loop().run_in_executor(None, to_csv)
                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(csv_content)
            
            self.logger.info(f"Exported {len(logs)} {category.value} logs to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
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
    
    async def get_log_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get log statistics across all categories"""
        try:
            stats = {
                'time_period_days': days,
                'total_logs': 0,
                'categories': {},
                'levels': {},
                'components': {},
                'top_users': {},
                'storage_size_mb': 0
            }
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Query logs for each category
            for category in LogCategory:
                category_logs = await self.query_logs(
                    category=category,
                    start_date=start_date,
                    limit=10000
                )
                
                stats['categories'][category.value] = len(category_logs)
                stats['total_logs'] += len(category_logs)
                
                # Analyze logs
                for log in category_logs:
                    level = log.get('level', 'unknown')
                    component = log.get('component', 'unknown')
                    user_id = log.get('user_id')
                    
                    stats['levels'][level] = stats['levels'].get(level, 0) + 1
                    stats['components'][component] = stats['components'].get(component, 0) + 1
                    
                    if user_id:
                        stats['top_users'][user_id] = stats['top_users'].get(user_id, 0) + 1
            
            # Calculate storage size
            total_size = 0
            for root, dirs, files in self.base_path.rglob('*'):
                if root.is_file():
                    total_size += root.stat().st_size
            stats['storage_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Sort top users
            stats['top_users'] = dict(sorted(stats['top_users'].items(), 
                                           key=lambda x: x[1], reverse=True)[:10])
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating log statistics: {e}")
            return {}
    
    async def _background_maintenance(self):
        """Background task for log maintenance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Compress old files
                if self.config.enable_compression:
                    await self._compress_old_logs()
                
                # Cleanup old files based on retention
                await self._cleanup_old_logs()
                
            except Exception as e:
                self.logger.error(f"Error in log maintenance: {e}")
    
    async def _compress_old_logs(self):
        """Compress log files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.compress_after_days)
            compressed_count = 0
            
            for category_dir in self.log_dirs.values():
                for year_dir in category_dir.iterdir():
                    if not year_dir.is_dir():
                        continue
                        
                    for month_dir in year_dir.iterdir():
                        if not month_dir.is_dir():
                            continue
                        
                        for file_path in month_dir.iterdir():
                            if (file_path.is_file() and 
                                not file_path.name.endswith('.gz')):
                                
                                # Extract date from filename
                                try:
                                    date_str = file_path.stem.split('_')[-1]
                                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                                    
                                    if file_date < cutoff_date:
                                        await self._compress_file(file_path)
                                        compressed_count += 1
                                except:
                                    continue
            
            if compressed_count > 0:
                self.logger.info(f"Compressed {compressed_count} old log files")
                
        except Exception as e:
            self.logger.error(f"Error compressing old logs: {e}")
    
    async def _cleanup_old_logs(self):
        """Remove log files older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            deleted_count = 0
            
            for category_dir in self.log_dirs.values():
                for year_dir in category_dir.iterdir():
                    if not year_dir.is_dir():
                        continue
                        
                    for month_dir in year_dir.iterdir():
                        if not month_dir.is_dir():
                            continue
                        
                        for file_path in month_dir.iterdir():
                            if file_path.is_file():
                                # Extract date from filename
                                try:
                                    date_str = file_path.stem.split('_')[-1]
                                    if '_' in date_str:  # Handle rotated files
                                        date_str = date_str.split('_')[0]
                                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                                    
                                    if file_date < cutoff_date:
                                        await aiofiles.os.remove(file_path)
                                        deleted_count += 1
                                except:
                                    continue
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old log files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")

# Global instance
log_storage_manager = LogStorageManager()