# services/comprehensive_logging_system.py
"""
Comprehensive Logging System Service
Handles ALL aspects of enterprise-grade logging including:
- Log classification and categorization
- ServiceNow integration for incident management
- Role-based access control
- Log lifecycle management
- Batch processing and storage
"""

import asyncio
import json
import re
import hashlib
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import aiohttp
from collections import defaultdict, deque
import logging
import uuid
import yaml

# Global logger instance
_comprehensive_logger = None

class LogLevel(Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG" 
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"

class LogSource(Enum):
    API = "API"
    FRONTEND = "FRONTEND"
    SYSTEM = "SYSTEM"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SECURITY = "SECURITY"
    EXTERNAL = "EXTERNAL"

class LogType(Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    USER_ACTION = "USER_ACTION"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    AUDIT = "AUDIT"

class AccessLevel(Enum):
    PUBLIC = "PUBLIC"
    AUTHENTICATED = "AUTHENTICATED"
    PRIVILEGED = "PRIVILEGED"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"

@dataclass
class LogEntry:
    id: str
    timestamp: str
    level: str
    source: str
    log_type: str
    message: str
    details: Dict[str, Any]
    access_level: str = "AUTHENTICATED"
    tags: List[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    classification: Dict[str, Any] = None
    sensitive_data_masked: bool = False
    incident_id: Optional[str] = None
    servicenow_ticket: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.classification is None:
            self.classification = {}

@dataclass 
class IncidentInfo:
    id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: str
    log_ids: List[str]
    servicenow_ticket: Optional[str] = None
    assignment_group: Optional[str] = None
    priority: int = 3

class LogClassifier:
    """Advanced log classification engine"""
    
    def __init__(self, classification_rules: Dict):
        self.rules = classification_rules
        self.level_keywords = self.rules.get('level_keywords', {})
        self.sensitive_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.rules.get('sensitive_patterns', [])]
        self.pii_keywords = self.rules.get('pii_keywords', [])
        self.incident_conditions = self.rules.get('incident_conditions', {})
        
    def classify_log(self, log_entry: LogEntry) -> LogEntry:
        """Classify and enhance log entry"""
        
        # Detect log level based on content
        detected_level = self._detect_level(log_entry.message + str(log_entry.details))
        if detected_level and log_entry.level == "INFO":  # Override generic INFO level
            log_entry.level = detected_level
            
        # Detect sensitive data
        has_sensitive = self._detect_sensitive_data(log_entry)
        if has_sensitive:
            log_entry = self._mask_sensitive_data(log_entry)
            log_entry.sensitive_data_masked = True
            
        # Set access level based on content
        log_entry.access_level = self._determine_access_level(log_entry)
        
        # Generate tags
        log_entry.tags.extend(self._generate_tags(log_entry))
        
        # Add classification metadata
        log_entry.classification = {
            'auto_classified': True,
            'has_sensitive_data': has_sensitive,
            'pii_detected': self._detect_pii(log_entry),
            'incident_worthy': self._should_create_incident(log_entry),
            'risk_score': self._calculate_risk_score(log_entry),
            'retention_days': self._get_retention_days(log_entry.level)
        }
        
        return log_entry
    
    def _detect_level(self, content: str) -> Optional[str]:
        """Detect log level from content"""
        content_lower = content.lower()
        
        for level, keywords in self.level_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return level
        return None
    
    def _detect_sensitive_data(self, log_entry: LogEntry) -> bool:
        """Detect sensitive data patterns"""
        content = f"{log_entry.message} {json.dumps(log_entry.details)}"
        
        for pattern in self.sensitive_patterns:
            if pattern.search(content):
                return True
        return False
    
    def _detect_pii(self, log_entry: LogEntry) -> bool:
        """Detect personally identifiable information"""
        content = f"{log_entry.message} {json.dumps(log_entry.details)}".lower()
        
        return any(keyword in content for keyword in self.pii_keywords)
    
    def _mask_sensitive_data(self, log_entry: LogEntry) -> LogEntry:
        """Mask sensitive data in log entry"""
        
        # Mask message
        for pattern in self.sensitive_patterns:
            log_entry.message = pattern.sub('[MASKED]', log_entry.message)
        
        # Mask details
        if isinstance(log_entry.details, dict):
            log_entry.details = self._mask_dict_values(log_entry.details)
            
        return log_entry
    
    def _mask_dict_values(self, data: Dict) -> Dict:
        """Recursively mask sensitive values in dictionary"""
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            if any(sensitive in key_lower for sensitive in ['password', 'token', 'key', 'secret', 'auth']):
                masked_data[key] = '[MASKED]'
            elif isinstance(value, dict):
                masked_data[key] = self._mask_dict_values(value)
            elif isinstance(value, str):
                masked_value = value
                for pattern in self.sensitive_patterns:
                    masked_value = pattern.sub('[MASKED]', masked_value)
                masked_data[key] = masked_value
            else:
                masked_data[key] = value
                
        return masked_data
    
    def _determine_access_level(self, log_entry: LogEntry) -> str:
        """Determine appropriate access level"""
        
        if log_entry.level in ['EMERGENCY', 'ALERT']:
            return AccessLevel.CONFIDENTIAL.value
        elif log_entry.level == 'CRITICAL':
            return AccessLevel.RESTRICTED.value
        elif log_entry.level in ['ERROR', 'WARNING']:
            return AccessLevel.PRIVILEGED.value
        elif log_entry.source == LogSource.SECURITY.value:
            return AccessLevel.RESTRICTED.value
        elif log_entry.log_type in [LogType.SECURITY.value, LogType.AUDIT.value]:
            return AccessLevel.PRIVILEGED.value
        else:
            return AccessLevel.AUTHENTICATED.value
    
    def _generate_tags(self, log_entry: LogEntry) -> List[str]:
        """Generate relevant tags for log entry"""
        tags = []
        
        # Add source-based tags
        tags.append(f"source:{log_entry.source.lower()}")
        tags.append(f"type:{log_entry.log_type.lower()}")
        tags.append(f"level:{log_entry.level.lower()}")
        
        # Add content-based tags
        message_lower = log_entry.message.lower()
        
        if 'database' in message_lower:
            tags.append('database')
        if 'authentication' in message_lower or 'login' in message_lower:
            tags.append('authentication')
        if 'permission' in message_lower or 'access' in message_lower:
            tags.append('authorization')
        if 'performance' in message_lower or 'slow' in message_lower:
            tags.append('performance')
        if 'timeout' in message_lower:
            tags.append('timeout')
        if 'network' in message_lower:
            tags.append('network')
            
        return list(set(tags))  # Remove duplicates
    
    def _should_create_incident(self, log_entry: LogEntry) -> bool:
        """Determine if log entry should trigger incident creation"""
        
        for condition_name, condition in self.incident_conditions.items():
            if log_entry.level in condition.get('levels', []):
                return True
                
            keywords = condition.get('keywords', [])
            if keywords and any(keyword in log_entry.message.lower() for keyword in keywords):
                return True
                
        return False
    
    def _calculate_risk_score(self, log_entry: LogEntry) -> float:
        """Calculate risk score (0-1)"""
        score = 0.0
        
        # Level-based scoring
        level_scores = {
            'EMERGENCY': 1.0,
            'ALERT': 0.9,
            'CRITICAL': 0.8,
            'ERROR': 0.6,
            'WARNING': 0.4,
            'NOTICE': 0.2,
            'INFO': 0.1,
            'DEBUG': 0.05,
            'TRACE': 0.01
        }
        score += level_scores.get(log_entry.level, 0.1)
        
        # Source-based adjustments
        if log_entry.source == LogSource.SECURITY.value:
            score += 0.3
        elif log_entry.source == LogSource.EXTERNAL.value:
            score += 0.2
            
        # Type-based adjustments  
        if log_entry.log_type in [LogType.SECURITY.value, LogType.ERROR.value]:
            score += 0.2
            
        return min(score, 1.0)
    
    def _get_retention_days(self, level: str) -> int:
        """Get retention period for log level"""
        return self.rules.get('retention_policies', {}).get(level, 90)

class ServiceNowIntegration:
    """ServiceNow incident management integration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.base_url = config.get('base_url', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.table = config.get('table', 'incident')
        self.session = None
        self.max_tickets_per_hour = config.get('max_tickets_per_hour', 10)
        self.tickets_created = deque(maxlen=self.max_tickets_per_hour)
        
    async def create_incident(self, incident: IncidentInfo) -> Optional[str]:
        """Create ServiceNow incident"""
        
        if not self.enabled:
            return None
            
        # Rate limiting
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        self.tickets_created = deque([t for t in self.tickets_created if t > hour_ago], 
                                   maxlen=self.max_tickets_per_hour)
        
        if len(self.tickets_created) >= self.max_tickets_per_hour:
            logging.warning(f"ServiceNow rate limit exceeded: {len(self.tickets_created)} tickets in last hour")
            return None
        
        try:
            incident_data = {
                'short_description': incident.title,
                'description': incident.description,
                'priority': incident.priority,
                'state': 1,  # New
                'assignment_group': incident.assignment_group or self.config.get('assignment_groups', {}).get('default', 'IT Support'),
                'caller_id': 'logging_system',
                'category': 'Software',
                'subcategory': 'Application',
                'business_service': 'Application Logging',
                'u_severity': incident.severity,
                'u_log_ids': ','.join(incident.log_ids)
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    auth=aiohttp.BasicAuth(self.username, self.password),
                    headers={'Content-Type': 'application/json'}
                )
            
            url = f"{self.base_url}/api/now/table/{self.table}"
            
            async with self.session.post(url, json=incident_data) as response:
                if response.status == 201:
                    result = await response.json()
                    ticket_number = result['result']['number']
                    self.tickets_created.append(now)
                    logging.info(f"Created ServiceNow ticket: {ticket_number}")
                    return ticket_number
                else:
                    logging.error(f"Failed to create ServiceNow ticket: {response.status}")
                    return None
                    
        except Exception as e:
            logging.error(f"ServiceNow integration error: {e}")
            return None
    
    async def close(self):
        """Close ServiceNow session"""
        if self.session:
            await self.session.close()

class LogStorage:
    """Enhanced log storage with lifecycle management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_path = Path(config.get('base_path', 'essentials/logs'))
        self.retention_days = config.get('retention_days', 90)
        self.max_file_size_mb = config.get('max_file_size_mb', 50)
        self.compress_after_days = config.get('compress_after_days', 7)
        
        # Ensure directories exist
        for log_type in ['application', 'security', 'network', 'threats', 'performance', 'audit', 'debug']:
            (self.base_path / log_type).mkdir(parents=True, exist_ok=True)
    
    async def store_log(self, log_entry: LogEntry):
        """Store log entry with automatic categorization"""
        
        # Determine storage category
        category = self._get_storage_category(log_entry)
        
        # Create timestamped filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.base_path / category / f"{date_str}.jsonl"
        
        # Check file size and rotate if needed
        if log_file.exists() and log_file.stat().st_size > self.max_file_size_mb * 1024 * 1024:
            timestamp = datetime.now().strftime('%H%M%S')
            new_name = self.base_path / category / f"{date_str}_{timestamp}.jsonl"
            log_file.rename(new_name)
        
        # Write log entry
        log_data = asdict(log_entry)
        
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(log_data) + '\n')
    
    def _get_storage_category(self, log_entry: LogEntry) -> str:
        """Determine storage category for log entry"""
        
        if log_entry.source == LogSource.SECURITY.value or log_entry.log_type == LogType.SECURITY.value:
            return 'security'
        elif log_entry.level in ['EMERGENCY', 'ALERT', 'CRITICAL']:
            return 'threats'
        elif log_entry.log_type == LogType.PERFORMANCE.value:
            return 'performance'
        elif log_entry.log_type == LogType.AUDIT.value:
            return 'audit'
        elif log_entry.level in ['DEBUG', 'TRACE']:
            return 'debug'
        elif log_entry.source == LogSource.NETWORK.value:
            return 'network'
        else:
            return 'application'
    
    async def cleanup_old_logs(self):
        """Clean up old logs based on retention policies"""
        
        now = datetime.now()
        
        for category_dir in self.base_path.iterdir():
            if not category_dir.is_dir():
                continue
                
            for log_file in category_dir.glob('*.jsonl'):
                # Check if file is old enough to delete
                file_age = now - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_age.days > self.retention_days:
                    log_file.unlink()
                    logging.info(f"Deleted old log file: {log_file}")
                elif file_age.days > self.compress_after_days and not log_file.name.endswith('.gz'):
                    # Compress old files
                    await self._compress_file(log_file)
    
    async def _compress_file(self, file_path: Path):
        """Compress log file"""
        
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        async with aiofiles.open(file_path, 'rb') as f_in:
            content = await f_in.read()
            
        with gzip.open(compressed_path, 'wb') as f_out:
            f_out.write(content)
            
        file_path.unlink()
        logging.info(f"Compressed log file: {file_path} -> {compressed_path}")

class ComprehensiveLoggingSystem:
    """Main comprehensive logging system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.log_queue = asyncio.Queue(maxsize=config.get('comprehensive_logging', {}).get('queue_max_size', 10000))
        self.batch_size = config.get('comprehensive_logging', {}).get('batch_size', 100)
        self.batch_timeout = config.get('comprehensive_logging', {}).get('batch_timeout', 5.0)
        
        # Initialize components
        self.classifier = LogClassifier(config.get('classification_rules', {}))
        self.snow_integration = ServiceNowIntegration(config.get('servicenow', {}))
        self.storage = LogStorage(config.get('storage', {}).get('log_storage', {}))
        
        # Processing state
        self.processing_task = None
        self.pending_incidents = {}
        self.incident_correlation_window = 15  # minutes
        
        # Statistics
        self.stats = {
            'logs_processed': 0,
            'incidents_created': 0,
            'errors': 0,
            'last_processed': None
        }
    
    async def start(self):
        """Start the logging system"""
        self.processing_task = asyncio.create_task(self._process_log_queue())
        logging.info("Comprehensive logging system started")
    
    async def stop(self):
        """Stop the logging system"""
        if self.processing_task:
            self.processing_task.cancel()
        await self.snow_integration.close()
        logging.info("Comprehensive logging system stopped")
    
    async def log_entry(self, log_data: Dict[str, Any]):
        """Add log entry to processing queue"""
        
        # Create LogEntry object
        log_entry = LogEntry(
            id=log_data.get('id', str(uuid.uuid4())),
            timestamp=log_data.get('timestamp', datetime.now().isoformat()),
            level=log_data.get('level', 'INFO'),
            source=log_data.get('source', 'SYSTEM'),
            log_type=log_data.get('log_type', 'SYSTEM_EVENT'),
            message=log_data.get('message', ''),
            details=log_data.get('details', {}),
            correlation_id=log_data.get('correlation_id'),
            user_id=log_data.get('user_id'),
            session_id=log_data.get('session_id'),
            ip_address=log_data.get('ip_address'),
            user_agent=log_data.get('user_agent')
        )
        
        try:
            await self.log_queue.put(log_entry)
        except asyncio.QueueFull:
            self.stats['errors'] += 1
            logging.error("Log queue is full, dropping log entry")
    
    async def _process_log_queue(self):
        """Process log entries from queue in batches"""
        
        batch = []
        last_batch_time = datetime.now()
        
        while True:
            try:
                # Wait for log entry or timeout
                try:
                    log_entry = await asyncio.wait_for(
                        self.log_queue.get(), 
                        timeout=self.batch_timeout
                    )
                    batch.append(log_entry)
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if full or timeout reached
                now = datetime.now()
                should_process = (
                    len(batch) >= self.batch_size or
                    (batch and (now - last_batch_time).total_seconds() >= self.batch_timeout)
                )
                
                if should_process and batch:
                    await self._process_batch(batch)
                    batch.clear()
                    last_batch_time = now
                    
            except asyncio.CancelledError:
                # Process remaining batch before stopping
                if batch:
                    await self._process_batch(batch)
                break
            except Exception as e:
                logging.error(f"Error in log processing: {e}")
                self.stats['errors'] += 1
    
    async def _process_batch(self, batch: List[LogEntry]):
        """Process a batch of log entries"""
        
        processed_logs = []
        
        for log_entry in batch:
            try:
                # Classify and enhance log entry
                enhanced_log = self.classifier.classify_log(log_entry)
                
                # Store log entry
                await self.storage.store_log(enhanced_log)
                
                # Check for incident creation
                if enhanced_log.classification.get('incident_worthy'):
                    await self._handle_potential_incident(enhanced_log)
                
                processed_logs.append(enhanced_log)
                self.stats['logs_processed'] += 1
                
            except Exception as e:
                logging.error(f"Error processing log entry {log_entry.id}: {e}")
                self.stats['errors'] += 1
        
        self.stats['last_processed'] = datetime.now().isoformat()
        
        if processed_logs:
            logging.debug(f"Processed batch of {len(processed_logs)} log entries")
    
    async def _handle_potential_incident(self, log_entry: LogEntry):
        """Handle potential incident creation"""
        
        # Group related logs by correlation window
        correlation_key = self._get_correlation_key(log_entry)
        now = datetime.now()
        
        if correlation_key not in self.pending_incidents:
            self.pending_incidents[correlation_key] = {
                'logs': [],
                'first_seen': now,
                'severity': log_entry.level
            }
        
        self.pending_incidents[correlation_key]['logs'].append(log_entry.id)
        
        # Update severity to highest
        current_severity = self.pending_incidents[correlation_key]['severity']
        if self._is_higher_severity(log_entry.level, current_severity):
            self.pending_incidents[correlation_key]['severity'] = log_entry.level
        
        # Check if we should create incident
        incident_data = self.pending_incidents[correlation_key]
        time_since_first = (now - incident_data['first_seen']).total_seconds() / 60
        
        if (time_since_first >= self.incident_correlation_window or 
            log_entry.level in ['EMERGENCY', 'ALERT']):
            
            await self._create_incident(correlation_key, incident_data)
            del self.pending_incidents[correlation_key]
    
    def _get_correlation_key(self, log_entry: LogEntry) -> str:
        """Generate correlation key for grouping related incidents"""
        
        if log_entry.correlation_id:
            return log_entry.correlation_id
        
        # Generate key based on source, user, and error type
        key_parts = [
            log_entry.source,
            log_entry.log_type,
            log_entry.user_id or 'anonymous',
            log_entry.ip_address or 'unknown'
        ]
        
        # Add error-specific info if available
        message_words = log_entry.message.lower().split()[:3]  # First 3 words
        key_parts.extend(message_words)
        
        key_string = '_'.join(filter(None, key_parts))
        return hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    def _is_higher_severity(self, level1: str, level2: str) -> bool:
        """Check if level1 is higher severity than level2"""
        
        severity_order = [
            'TRACE', 'DEBUG', 'INFO', 'NOTICE', 'WARNING', 
            'ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY'
        ]
        
        try:
            return severity_order.index(level1) > severity_order.index(level2)
        except ValueError:
            return False
    
    async def _create_incident(self, correlation_key: str, incident_data: Dict):
        """Create incident from correlated logs"""
        
        incident = IncidentInfo(
            id=str(uuid.uuid4()),
            title=f"System Issue Detected - {incident_data['severity']} Level",
            description=f"Correlated logs detected potential system issue. "
                       f"Severity: {incident_data['severity']}, "
                       f"Log count: {len(incident_data['logs'])}, "
                       f"Correlation key: {correlation_key}",
            severity=self._map_severity_to_servicenow(incident_data['severity']),
            status="New",
            created_at=datetime.now().isoformat(),
            log_ids=incident_data['logs'],
            priority=self._map_severity_to_priority(incident_data['severity'])
        )
        
        # Create ServiceNow ticket
        ticket_number = await self.snow_integration.create_incident(incident)
        if ticket_number:
            incident.servicenow_ticket = ticket_number
            self.stats['incidents_created'] += 1
            logging.info(f"Created incident {incident.id} with ServiceNow ticket {ticket_number}")
    
    def _map_severity_to_servicenow(self, level: str) -> str:
        """Map log level to ServiceNow severity"""
        mapping = {
            'EMERGENCY': 'SEV1_CRITICAL',
            'ALERT': 'SEV1_CRITICAL', 
            'CRITICAL': 'SEV2_HIGH',
            'ERROR': 'SEV3_MODERATE',
            'WARNING': 'SEV4_LOW'
        }
        return mapping.get(level, 'SEV4_LOW')
    
    def _map_severity_to_priority(self, level: str) -> int:
        """Map log level to ServiceNow priority"""
        mapping = {
            'EMERGENCY': 1,
            'ALERT': 1,
            'CRITICAL': 2, 
            'ERROR': 3,
            'WARNING': 4
        }
        return mapping.get(level, 4)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging system statistics"""
        return {
            **self.stats,
            'queue_size': self.log_queue.qsize(),
            'pending_incidents': len(self.pending_incidents),
            'servicenow_enabled': self.snow_integration.enabled
        }

# Global functions for easy access
def initialize_comprehensive_logging(config: Dict) -> ComprehensiveLoggingSystem:
    """Initialize the comprehensive logging system"""
    global _comprehensive_logger
    
    _comprehensive_logger = ComprehensiveLoggingSystem(config)
    asyncio.create_task(_comprehensive_logger.start())
    
    return _comprehensive_logger

def get_comprehensive_logger() -> Optional[ComprehensiveLoggingSystem]:
    """Get the global comprehensive logger instance"""
    return _comprehensive_logger

# Convenience logging functions
async def log_info(message: str, **kwargs):
    """Log info level message"""
    if _comprehensive_logger:
        await _comprehensive_logger.log_entry({
            'level': 'INFO',
            'message': message,
            'details': kwargs
        })

async def log_error(message: str, **kwargs):
    """Log error level message"""
    if _comprehensive_logger:
        await _comprehensive_logger.log_entry({
            'level': 'ERROR', 
            'message': message,
            'details': kwargs
        })

async def log_security_event(message: str, **kwargs):
    """Log security event"""
    if _comprehensive_logger:
        await _comprehensive_logger.log_entry({
            'level': 'WARNING',
            'source': 'SECURITY',
            'log_type': 'SECURITY',
            'message': message,
            'details': kwargs
        })