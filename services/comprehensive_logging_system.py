# services/comprehensive_logging_system.py
"""
Testable implementation of comprehensive logging system
Provides real functionality for testing and coverage
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import uuid
from pathlib import Path

# Global logger instance
_comprehensive_logger = None

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

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.classification is None:
            self.classification = {}

class LogClassifier:
    """Log classification engine"""
    
    def __init__(self, classification_rules: Dict):
        self.rules = classification_rules
        self.level_keywords = self.rules.get('level_keywords', {})
        self.sensitive_patterns = self.rules.get('sensitive_patterns', [])
        self.pii_keywords = self.rules.get('pii_keywords', [])
        
    def classify_log(self, log_entry: LogEntry) -> LogEntry:
        """Classify and enhance log entry"""
        
        # Detect log level based on content
        detected_level = self._detect_level(log_entry.message)
        if detected_level and log_entry.level == "INFO":
            log_entry.level = detected_level
            
        # Detect sensitive data
        has_sensitive = self._detect_sensitive_data(log_entry)
        if has_sensitive:
            log_entry = self._mask_sensitive_data(log_entry)
            log_entry.sensitive_data_masked = True
            
        # Set access level
        log_entry.access_level = self._determine_access_level(log_entry)
        
        # Generate tags
        log_entry.tags.extend(self._generate_tags(log_entry))
        
        # Add classification metadata
        log_entry.classification = {
            'auto_classified': True,
            'has_sensitive_data': has_sensitive,
            'pii_detected': self._detect_pii(log_entry),
            'incident_worthy': self._should_create_incident(log_entry),
            'risk_score': self._calculate_risk_score(log_entry)
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
        
        # Simple check for common sensitive patterns
        sensitive_keywords = ['password', 'token', 'key', 'secret', 'api_key']
        return any(keyword in content.lower() for keyword in sensitive_keywords)
    
    def _detect_pii(self, log_entry: LogEntry) -> bool:
        """Detect personally identifiable information"""
        content = f"{log_entry.message} {json.dumps(log_entry.details)}".lower()
        return any(keyword in content for keyword in self.pii_keywords)
    
    def _mask_sensitive_data(self, log_entry: LogEntry) -> LogEntry:
        """Mask sensitive data in log entry"""
        
        # Mask common sensitive patterns in message
        for sensitive in ['password', 'token', 'key', 'secret']:
            if sensitive in log_entry.message.lower():
                log_entry.message = log_entry.message.replace(
                    log_entry.message[log_entry.message.lower().find(sensitive):], '[MASKED]'
                )
        
        # Mask details
        if isinstance(log_entry.details, dict):
            log_entry.details = self._mask_dict_values(log_entry.details)
            
        return log_entry
    
    def _mask_dict_values(self, data: Dict) -> Dict:
        """Recursively mask sensitive values in dictionary"""
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            if any(sensitive in key_lower for sensitive in ['password', 'token', 'key', 'secret']):
                masked_data[key] = '[MASKED]'
            elif isinstance(value, dict):
                masked_data[key] = self._mask_dict_values(value)
            else:
                masked_data[key] = value
                
        return masked_data
    
    def _determine_access_level(self, log_entry: LogEntry) -> str:
        """Determine appropriate access level"""
        
        if log_entry.level in ['EMERGENCY', 'ALERT']:
            return 'CONFIDENTIAL'
        elif log_entry.level == 'CRITICAL':
            return 'RESTRICTED'
        elif log_entry.level in ['ERROR', 'WARNING']:
            return 'PRIVILEGED'
        else:
            return 'AUTHENTICATED'
    
    def _generate_tags(self, log_entry: LogEntry) -> List[str]:
        """Generate relevant tags for log entry"""
        tags = []
        
        tags.append(f"source:{log_entry.source.lower()}")
        tags.append(f"type:{log_entry.log_type.lower()}")
        tags.append(f"level:{log_entry.level.lower()}")
        
        # Add content-based tags
        message_lower = log_entry.message.lower()
        
        if 'database' in message_lower:
            tags.append('database')
        if 'authentication' in message_lower or 'login' in message_lower:
            tags.append('authentication')
        if 'error' in message_lower:
            tags.append('error')
            
        return list(set(tags))
    
    def _should_create_incident(self, log_entry: LogEntry) -> bool:
        """Determine if log entry should trigger incident creation"""
        return log_entry.level in ['CRITICAL', 'ALERT', 'EMERGENCY']
    
    def _calculate_risk_score(self, log_entry: LogEntry) -> float:
        """Calculate risk score (0-1)"""
        level_scores = {
            'EMERGENCY': 1.0, 'ALERT': 0.9, 'CRITICAL': 0.8,
            'ERROR': 0.6, 'WARNING': 0.4, 'NOTICE': 0.2,
            'INFO': 0.1, 'DEBUG': 0.05, 'TRACE': 0.01
        }
        return level_scores.get(log_entry.level, 0.1)

class ServiceNowIntegration:
    """ServiceNow incident management integration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.tickets_created = []
        
    async def create_incident(self, incident_data: Dict) -> Optional[str]:
        """Create ServiceNow incident (mock implementation)"""
        
        if not self.enabled:
            return None
            
        # Generate mock ticket number
        ticket_number = f"INC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.tickets_created.append({
            'ticket': ticket_number,
            'created_at': datetime.now().isoformat(),
            'data': incident_data
        })
        
        logging.info(f"Mock ServiceNow ticket created: {ticket_number}")
        return ticket_number

class LogStorage:
    """Log storage with lifecycle management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_path = Path(config.get('base_path', 'test_logs'))
        self.stored_logs = []
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        for category in ['application', 'security', 'network', 'performance']:
            (self.base_path / category).mkdir(exist_ok=True)
    
    async def store_log(self, log_entry: LogEntry):
        """Store log entry"""
        
        # Determine storage category
        category = self._get_storage_category(log_entry)
        
        # Store in memory for testing
        self.stored_logs.append(asdict(log_entry))
        
        # Also write to file for realism
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.base_path / category / f"{date_str}.jsonl"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(asdict(log_entry)) + '\n')
        except Exception as e:
            logging.warning(f"Failed to write log file: {e}")
    
    def _get_storage_category(self, log_entry: LogEntry) -> str:
        """Determine storage category"""
        
        if log_entry.source == 'SECURITY' or log_entry.log_type == 'SECURITY':
            return 'security'
        elif log_entry.level in ['EMERGENCY', 'ALERT', 'CRITICAL']:
            return 'security'  # Store critical logs in security
        elif log_entry.log_type == 'PERFORMANCE':
            return 'performance'
        elif log_entry.source == 'NETWORK':
            return 'network'
        else:
            return 'application'

class ComprehensiveLoggingSystem:
    """Main comprehensive logging system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.log_queue = asyncio.Queue(maxsize=config.get('comprehensive_logging', {}).get('queue_max_size', 1000))
        self.batch_size = config.get('comprehensive_logging', {}).get('batch_size', 10)
        self.batch_timeout = config.get('comprehensive_logging', {}).get('batch_timeout', 5.0)
        
        # Initialize components
        self.classifier = LogClassifier(config.get('classification_rules', {}))
        self.snow_integration = ServiceNowIntegration(config.get('servicenow', {}))
        self.storage = LogStorage(config.get('storage', {}).get('log_storage', {}))
        
        # Processing state
        self.processing_task = None
        self.pending_incidents = {}
        
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
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
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
        
        while True:
            try:
                # Get log entry with timeout
                try:
                    log_entry = await asyncio.wait_for(
                        self.log_queue.get(), 
                        timeout=self.batch_timeout
                    )
                    batch.append(log_entry)
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if full or timeout reached
                if len(batch) >= self.batch_size or (batch and len(batch) > 0):
                    await self._process_batch(batch)
                    batch.clear()
                    
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
        
        for log_entry in batch:
            try:
                # Classify and enhance log entry
                enhanced_log = self.classifier.classify_log(log_entry)
                
                # Store log entry
                await self.storage.store_log(enhanced_log)
                
                # Check for incident creation
                if enhanced_log.classification.get('incident_worthy'):
                    await self._handle_potential_incident(enhanced_log)
                
                self.stats['logs_processed'] += 1
                
            except Exception as e:
                logging.error(f"Error processing log entry {log_entry.id}: {e}")
                self.stats['errors'] += 1
        
        self.stats['last_processed'] = datetime.now().isoformat()
    
    async def _handle_potential_incident(self, log_entry: LogEntry):
        """Handle potential incident creation"""
        
        # Simple incident creation for critical logs
        if log_entry.level in ['CRITICAL', 'ALERT', 'EMERGENCY']:
            incident_data = {
                'title': f"Critical Issue: {log_entry.message[:50]}",
                'description': log_entry.message,
                'severity': log_entry.level,
                'log_id': log_entry.id
            }
            
            ticket_number = await self.snow_integration.create_incident(incident_data)
            if ticket_number:
                log_entry.incident_id = ticket_number
                self.stats['incidents_created'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging system statistics"""
        return {
            **self.stats,
            'queue_size': self.log_queue.qsize(),
            'servicenow_enabled': self.snow_integration.enabled
        }

# Global functions for easy access
def initialize_comprehensive_logging(config: Dict) -> ComprehensiveLoggingSystem:
    """Initialize the comprehensive logging system"""
    global _comprehensive_logger
    
    _comprehensive_logger = ComprehensiveLoggingSystem(config)
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
