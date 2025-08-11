# routers/audit.py - Updated Audit Router with File-Based Storage

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import uuid
import hashlib
from collections import defaultdict, deque
import ipaddress
import re
from pathlib import Path

# Import the file storage system
from storage.file_audit_storage import FileAuditStorage, StorageConfig, FileBasedAuditStorage

router = APIRouter()

# =================== ENUMS AND CONSTANTS ===================

class AuditEventType(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_INCIDENT = "security_incident"
    POLICY_VIOLATION = "policy_violation"
    SYSTEM_EVENT = "system_event"
    COMPLIANCE_EVENT = "compliance_event"

class AuthenticationResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    MFA_REQUIRED = "mfa_required"
    BLOCKED = "blocked"
    STEP_UP_REQUIRED = "step_up_required"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# =================== PYDANTIC MODELS ===================

class GeographicInfo(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

class DeviceInfo(BaseModel):
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    user_agent: Optional[str] = None
    is_trusted: bool = False
    device_fingerprint: Optional[str] = None

class AuthenticationDetails(BaseModel):
    auth_method: Optional[str] = None
    mfa_method: Optional[str] = None
    identity_provider: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    failure_reason: Optional[str] = None
    error_code: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    applied_rules: List[str] = []

class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0, le=100)
    contributing_factors: List[str] = []
    geographic_risk: bool = False
    temporal_risk: bool = False
    device_risk: bool = False
    behavioral_risk: bool = False

class AuditEvent(BaseModel):
    # Core event information
    event_id: Optional[str] = None
    event_type: AuditEventType
    timestamp: Optional[datetime] = None
    
    # User and identity information
    user_id: str
    user_principal_name: Optional[str] = None
    user_display_name: Optional[str] = None
    user_roles: List[str] = []
    
    # Action and result
    action: str
    result: AuthenticationResult
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Network and location information
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    geographic_info: Optional[GeographicInfo] = None
    device_info: Optional[DeviceInfo] = None
    
    # Authentication specific details
    auth_details: Optional[AuthenticationDetails] = None
    risk_assessment: Optional[RiskAssessment] = None
    
    # Target resource information
    target_resource: Optional[str] = None
    resource_type: Optional[str] = None
    application: Optional[str] = None
    
    # Additional context
    description: Optional[str] = None
    raw_data: Dict[str, Any] = {}
    tags: List[str] = []
    
    # Compliance and policy
    policy_violations: List[str] = []
    compliance_frameworks: List[str] = []
    
    class Config:
        use_enum_values = True
        
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.utcnow()
    
    @validator('event_id', pre=True, always=True)
    def set_event_id(cls, v):
        return v or str(uuid.uuid4())

class AuditQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: List[AuditEventType] = []
    user_ids: List[str] = []
    results: List[AuthenticationResult] = []
    risk_levels: List[RiskLevel] = []
    source_ips: List[str] = []
    applications: List[str] = []
    severity_levels: List[AuditSeverity] = []
    tags: List[str] = []
    limit: int = Field(100, le=1000)
    offset: int = 0
    search_text: Optional[str] = None

class BulkAuditEvent(BaseModel):
    events: List[AuditEvent]
    source_system: str
    batch_id: Optional[str] = None

class ExportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    format: str = Field("json", pattern="^(json|csv|jsonl)$")
    filters: Optional[AuditQuery] = None
    include_raw_data: bool = True

# =================== FILE-BASED STORAGE INITIALIZATION ===================

# Initialize file-based storage with configuration
storage_config = StorageConfig(
    base_path="essentials/audit",
    format="jsonl",  # JSON Lines for better performance
    rotation="daily",
    max_file_size_mb=100,
    compress_old_files=True,
    retention_days=365,
    backup_enabled=True,
    index_enabled=True
)

# Create the storage instance
audit_storage = FileBasedAuditStorage()
print(f"✅ File-based audit storage initialized at: {storage_config.base_path}")

# =================== RISK CALCULATION FUNCTIONS ===================

async def calculate_authentication_risk(event: AuditEvent) -> RiskAssessment:
    """Calculate risk score for authentication events"""
    risk_score = 0.0
    contributing_factors = []
    
    user_id = event.user_id
    profile = audit_storage.user_risk_profiles.get(user_id, {})
    
    # Geographic risk assessment
    geographic_risk = False
    if event.geographic_info and user_id in audit_storage.user_risk_profiles:
        user_locations = profile.get('locations', set())
        current_country = event.geographic_info.country
        
        if current_country and len(user_locations) > 0 and current_country not in user_locations:
            risk_score += 25
            contributing_factors.append("New geographic location")
            geographic_risk = True
    
    # Temporal risk assessment
    temporal_risk = False
    current_hour = event.timestamp.hour
    if current_hour < 6 or current_hour > 22:  # Outside business hours
        risk_score += 15
        contributing_factors.append("Outside business hours")
        temporal_risk = True
    
    # Device risk assessment
    device_risk = False
    if event.device_info and event.device_info.device_fingerprint:
        device_fp = event.device_info.device_fingerprint
        if device_fp not in profile.get('devices', set()):
            risk_score += 20
            contributing_factors.append("New device")
            device_risk = True
        
        # Check device trust score
        trust_score = audit_storage.device_trust_scores.get(device_fp, 50.0)
        if trust_score < 30:
            risk_score += 15
            contributing_factors.append("Low device trust score")
            device_risk = True
    
    # Behavioral risk assessment
    behavioral_risk = False
    failed_attempts = profile.get('failed_login_count_24h', 0)
    if failed_attempts > 3:
        risk_score += min(failed_attempts * 5, 30)
        contributing_factors.append(f"Multiple failed attempts ({failed_attempts})")
        behavioral_risk = True
    
    # IP reputation risk
    if event.source_ip and event.source_ip in audit_storage.suspicious_ips:
        ip_info = audit_storage.suspicious_ips[event.source_ip]
        if ip_info['count'] > 10:
            risk_score += 20
            contributing_factors.append("Suspicious IP address")
    
    # Velocity risk
    if user_id in audit_storage.user_risk_profiles:
        last_login = profile.get('last_successful_login')
        if last_login and (event.timestamp - last_login).total_seconds() < 300:  # Less than 5 minutes
            risk_score += 10
            contributing_factors.append("High login velocity")
            behavioral_risk = True
    
    # Determine risk level
    risk_level = RiskLevel.LOW
    if risk_score >= 70:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 50:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 30:
        risk_level = RiskLevel.MEDIUM
    
    return RiskAssessment(
        risk_level=risk_level,
        risk_score=min(risk_score, 100.0),
        contributing_factors=contributing_factors,
        geographic_risk=geographic_risk,
        temporal_risk=temporal_risk,
        device_risk=device_risk,
        behavioral_risk=behavioral_risk
    )

# =================== AUDIT ENDPOINTS ===================

@router.post("/events", response_model=Dict[str, str])
async def create_audit_event(event: AuditEvent, background_tasks: BackgroundTasks):
    """Create a new audit event and store it to file system"""
    try:
        # Calculate risk assessment for authentication events
        if event.event_type == AuditEventType.AUTHENTICATION and not event.risk_assessment:
            event.risk_assessment = await calculate_authentication_risk(event)
        
        # Store the event using file storage
        event_id = await audit_storage.store_event(event)
        
        # Schedule background processing for high-risk events
        if event.risk_assessment and event.risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            background_tasks.add_task(process_high_risk_event, event)
        
        return {
            "message": "Audit event created and stored to file system",
            "event_id": event_id,
            "risk_level": event.risk_assessment.risk_level if event.risk_assessment else "not_assessed",
            "storage_location": f"essentials/audit/events/{event.timestamp.strftime('%Y/%m')}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit event: {str(e)}")

@router.post("/events/bulk", response_model=Dict[str, Any])
async def create_bulk_audit_events(bulk_events: BulkAuditEvent, background_tasks: BackgroundTasks):
    """Create multiple audit events in bulk and store to file system"""
    try:
        event_ids = []
        high_risk_count = 0
        
        for event in bulk_events.events:
            if event.event_type == AuditEventType.AUTHENTICATION and not event.risk_assessment:
                event.risk_assessment = await calculate_authentication_risk(event)
            
            event_id = await audit_storage.store_event(event)
            event_ids.append(event_id)
            
            if event.risk_assessment and event.risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                high_risk_count += 1
                background_tasks.add_task(process_high_risk_event, event)
        
        return {
            "message": f"Successfully created and stored {len(event_ids)} audit events",
            "event_ids": event_ids,
            "high_risk_events": high_risk_count,
            "batch_id": bulk_events.batch_id or str(uuid.uuid4()),
            "storage_location": "essentials/audit/events/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bulk audit events: {str(e)}")

@router.get("/events", response_model=Dict[str, Any])
async def get_audit_events(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    event_type: Optional[AuditEventType] = Query(None, description="Event type filter"),
    user_id: Optional[str] = Query(None, description="User ID filter"),
    result: Optional[AuthenticationResult] = Query(None, description="Result filter"),
    risk_level: Optional[RiskLevel] = Query(None, description="Risk level filter"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, description="Number of events to skip")
):
    """Get audit events from file storage with filtering options"""
    try:
        # Build filter parameters
        filters = {}
        if user_id:
            filters['user_ids'] = [user_id]
        if event_type:
            filters['event_types'] = [event_type]
        if result:
            filters['results'] = [result]
        
        # Query from file storage
        events = await audit_storage.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            **filters
        )
        
        # Apply additional filters that aren't handled by file storage
        if risk_level:
            events = [e for e in events if e.get('risk_assessment', {}).get('risk_level') == risk_level]
        
        # Apply pagination
        total_count = len(events)
        paginated_events = events[offset:offset + limit] if offset > 0 else events[:limit]
        
        return {
            "events": paginated_events,
            "total_count": total_count,
            "returned_count": len(paginated_events),
            "offset": offset,
            "limit": limit,
            "source": "file_storage",
            "storage_location": "essentials/audit/events/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit events: {str(e)}")

@router.post("/events/query", response_model=Dict[str, Any])
async def query_audit_events(query: AuditQuery):
    """Advanced audit event querying from file storage"""
    try:
        # Convert query parameters to file storage format
        filters = {}
        if query.user_ids:
            filters['user_ids'] = query.user_ids
        if query.event_types:
            filters['event_types'] = [str(et) for et in query.event_types]
        if query.results:
            filters['results'] = [str(r) for r in query.results]
        if query.source_ips:
            filters['source_ips'] = query.source_ips
        
        # Query from file storage
        events = await audit_storage.query_events(
            start_date=query.start_date,
            end_date=query.end_date,
            limit=query.limit + query.offset,  # Get extra for offset
            **filters
        )
        
        # Apply additional client-side filters
        if query.applications:
            events = [e for e in events if e.get('application') in query.applications]
        if query.severity_levels:
            events = [e for e in events if e.get('severity') in [str(s) for s in query.severity_levels]]
        if query.risk_levels:
            events = [e for e in events if e.get('risk_assessment', {}).get('risk_level') in [str(r) for r in query.risk_levels]]
        if query.tags:
            events = [e for e in events if any(tag in e.get('tags', []) for tag in query.tags)]
        
        # Text search
        if query.search_text:
            search_lower = query.search_text.lower()
            events = [
                e for e in events 
                if (search_lower in e.get('user_id', '').lower() or 
                    search_lower in e.get('action', '').lower() or 
                    (e.get('description') and search_lower in e.get('description', '').lower()))
            ]
        
        # Apply pagination
        total_count = len(events)
        paginated_events = events[query.offset:query.offset + query.limit]
        
        return {
            "events": paginated_events,
            "total_count": total_count,
            "returned_count": len(paginated_events),
            "query_summary": {
                "filters_applied": sum([
                    bool(query.start_date), bool(query.end_date), bool(query.event_types),
                    bool(query.user_ids), bool(query.results), bool(query.risk_levels),
                    bool(query.source_ips), bool(query.applications), bool(query.search_text)
                ]),
                "time_range": {
                    "start": query.start_date,
                    "end": query.end_date
                },
                "storage_source": "file_system"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query audit events: {str(e)}")

@router.get("/summary", response_model=Dict[str, Any])
async def get_audit_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    days: int = Query(7, description="Number of days to include in summary")
):
    """Get audit summary and statistics from file storage"""
    try:
        # Get summary from file storage
        summary = await audit_storage.get_summary(days=days)
        
        # Add storage information
        storage_info = await audit_storage.file_storage.get_storage_info()
        
        return {
            **summary,
            "storage_info": {
                "total_size_mb": storage_info.get('total_size_mb', 0),
                "total_files": storage_info.get('total_files', 0),
                "storage_format": storage_info.get('storage_format', 'jsonl'),
                "base_path": storage_info.get('base_path', 'essentials/audit')
            },
            "summary_period_days": days,
            "generated_from": "file_storage"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audit summary: {str(e)}")

@router.post("/export", response_model=Dict[str, str])
async def export_audit_data(export_request: ExportRequest, background_tasks: BackgroundTasks):
    """Export audit data from file storage to specified format"""
    try:
        # Generate export filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_export_{timestamp}.{export_request.format}"
        
        # Schedule export in background
        background_tasks.add_task(
            perform_export,
            export_request.start_date,
            export_request.end_date,
            export_request.format,
            filename,
            export_request.filters
        )
        
        return {
            "message": "Export started in background",
            "export_id": timestamp,
            "estimated_completion": "5-10 minutes",
            "output_location": f"essentials/audit/reports/{filename}",
            "format": export_request.format
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start export: {str(e)}")

@router.get("/storage-info")
async def get_storage_information():
    """Get detailed information about the file storage system"""
    try:
        storage_info = await audit_storage.file_storage.get_storage_info()
        
        # Add directory structure information
        base_path = Path(storage_info['base_path'])
        structure = {
            "events": str(base_path / "events"),
            "indexes": str(base_path / "indexes"), 
            "archives": str(base_path / "archives"),
            "backups": str(base_path / "backups"),
            "reports": str(base_path / "reports"),
            "temp": str(base_path / "temp")
        }
        
        return {
            **storage_info,
            "directory_structure": structure,
            "features": {
                "file_rotation": True,
                "compression": storage_config.compress_old_files,
                "indexing": storage_config.index_enabled,
                "backup": storage_config.backup_enabled,
                "retention_policy": f"{storage_config.retention_days} days"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}")

@router.get("/files")
async def list_audit_files(
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month"),
    include_compressed: bool = Query(True, description="Include compressed files")
):
    """List audit files in the storage system"""
    try:
        base_path = Path("essentials/audit/events")
        files_info = []
        
        if not base_path.exists():
            return {"files": [], "message": "No audit files found"}
        
        # Scan directory structure
        for year_dir in base_path.iterdir():
            if not year_dir.is_dir():
                continue
            
            year_num = int(year_dir.name)
            if year and year_num != year:
                continue
            
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                
                month_num = int(month_dir.name)
                if month and month_num != month:
                    continue
                
                for file_path in month_dir.iterdir():
                    if file_path.is_file():
                        # Skip compressed files if not requested
                        if not include_compressed and file_path.suffix == '.gz':
                            continue
                        
                        stat = file_path.stat()
                        files_info.append({
                            "filename": file_path.name,
                            "path": str(file_path.relative_to(base_path)),
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "compressed": file_path.suffix == '.gz',
                            "year": year_num,
                            "month": month_num
                        })
        
        # Sort by modification date
        files_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "files": files_info,
            "total_files": len(files_info),
            "total_size_mb": sum(f['size_mb'] for f in files_info),
            "filters_applied": {
                "year": year,
                "month": month,
                "include_compressed": include_compressed
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list audit files: {str(e)}")

# =================== EXISTING ENDPOINTS (Updated for File Storage) ===================

@router.get("/risk-profiles/{user_id}")
async def get_user_risk_profile(user_id: str):
    """Get risk profile for a specific user from cached data"""
    try:
        profile = audit_storage.user_risk_profiles.get(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User risk profile not found")
        
        # Convert sets to lists for JSON serialization
        profile_copy = profile.copy()
        profile_copy['locations'] = list(profile_copy.get('locations', set()))
        profile_copy['devices'] = list(profile_copy.get('devices', set()))
        
        # Get recent failed attempts
        recent_failures = list(audit_storage.failed_login_attempts.get(user_id, []))
        
        return {
            "user_id": user_id,
            "risk_profile": profile_copy,
            "recent_failed_attempts": recent_failures,
            "risk_indicators": {
                "high_failure_rate": profile.get('failed_login_count_24h', 0) > 5,
                "multiple_locations": len(profile.get('locations', set())) > 3,
                "multiple_devices": len(profile.get('devices', set())) > 5,
                "elevated_avg_risk": profile.get('average_risk_score', 0) > 50
            },
            "data_source": "file_storage_cache"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user risk profile: {str(e)}")

@router.get("/suspicious-activity")
async def get_suspicious_activity():
    """Get suspicious activity indicators from cached data"""
    try:
        # Get high-risk recent events from file storage
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        high_risk_events = await audit_storage.query_events(
            start_date=recent_cutoff,
            limit=1000
        )
        
        # Filter for high-risk events
        high_risk_events = [
            e for e in high_risk_events 
            if e.get('risk_assessment', {}).get('risk_level') in ['high', 'critical']
        ]
        
        # Get suspicious IPs from cache
        suspicious_ips = [
            {
                "ip_address": ip,
                "failure_count": info['count'],
                "first_seen": info['first_seen'].isoformat() if isinstance(info['first_seen'], datetime) else info['first_seen'],
                "last_seen": info['last_seen'].isoformat() if isinstance(info['last_seen'], datetime) else info['last_seen']
            }
            for ip, info in audit_storage.suspicious_ips.items()
            if info['count'] > 5
        ]
        
        # Get users with high failure rates from cache
        high_failure_users = [
            {
                "user_id": user_id,
                "failed_attempts_24h": profile['failed_login_count_24h'],
                "average_risk_score": profile['average_risk_score']
            }
            for user_id, profile in audit_storage.user_risk_profiles.items()
            if profile.get('failed_login_count_24h', 0) > 5
        ]
        
        return {
            "summary": {
                "high_risk_events_24h": len(high_risk_events),
                "suspicious_ips": len(suspicious_ips),
                "high_failure_users": len(high_failure_users)
            },
            "high_risk_events": high_risk_events[:20],  # Limit to 20 most recent
            "suspicious_ips": suspicious_ips,
            "high_failure_users": high_failure_users,
            "data_source": "file_storage_with_cache",
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve suspicious activity: {str(e)}")

@router.get("/")
async def get_audit_overview():
    """Get audit system overview with file storage information"""
    try:
        # Get storage info
        storage_info = await audit_storage.file_storage.get_storage_info()
        
        # Get recent statistics
        summary = await audit_storage.get_summary(days=1)
        
        return {
            "message": "Enhanced Audit System with File-Based Storage",
            "version": "2.1.0",
            "status": "operational",
            "storage": {
                "type": "file_based",
                "location": storage_info.get('base_path', 'essentials/audit'),
                "format": storage_info.get('storage_format', 'jsonl'),
                "total_size_mb": storage_info.get('total_size_mb', 0),
                "total_files": storage_info.get('total_files', 0),
                "compression_enabled": storage_config.compress_old_files,
                "retention_days": storage_config.retention_days
            },
            "statistics": {
                "total_events": summary.get('total_events', 0),
                "events_last_24h": summary.get('total_events', 0),
                "monitored_users": len(audit_storage.user_risk_profiles),
                "suspicious_ips": len(audit_storage.suspicious_ips),
                "cache_size": storage_info.get('cache_statistics', {})
            },
            "capabilities": [
                "Real-time risk assessment",
                "File-based persistent storage",
                "Authentication failure tracking",
                "Geographic and device analysis",
                "Bulk event processing",
                "Advanced querying and filtering",
                "Suspicious activity detection",
                "User risk profiling",
                "Data export and reporting",
                "File compression and archival",
                "Automated backup system"
            ],
            "endpoints": {
                "create_event": "/events",
                "bulk_events": "/events/bulk",
                "query_events": "/events/query",
                "summary": "/summary",
                "export": "/export",
                "storage_info": "/storage-info",
                "list_files": "/files",
                "risk_profiles": "/risk-profiles/{user_id}",
                "suspicious_activity": "/suspicious-activity"
            },
            "file_structure": {
                "events": "essentials/audit/events/YYYY/MM/",
                "indexes": "essentials/audit/indexes/",
                "archives": "essentials/audit/archives/",
                "backups": "essentials/audit/backups/",
                "reports": "essentials/audit/reports/"
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit overview: {str(e)}")

# =================== INTEGRATION ENDPOINTS (Updated) ===================

@router.post("/integrations/azure-ad", response_model=Dict[str, str])
async def receive_azure_ad_event(raw_event: Dict[str, Any]):
    """Receive and process Azure AD audit events, storing to file system"""
    try:
        # Transform Azure AD event to our audit format
        audit_event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            user_id=raw_event.get('userPrincipalName', 'unknown'),
            user_principal_name=raw_event.get('userPrincipalName'),
            action=raw_event.get('activityDisplayName', 'login'),
            result=AuthenticationResult.SUCCESS if raw_event.get('resultType') == '0' else AuthenticationResult.FAILURE,
            source_ip=raw_event.get('ipAddress'),
            user_agent=raw_event.get('deviceDetail', {}).get('browser'),
            auth_details=AuthenticationDetails(
                identity_provider="AzureAD",
                correlation_id=raw_event.get('correlationId'),
                failure_reason=raw_event.get('failureReason'),
                error_code=raw_event.get('resultType')
            ),
            application=raw_event.get('appDisplayName'),
            raw_data=raw_event,
            tags=["azure_ad", "integration"]
        )
        
        event_id = await audit_storage.store_event(audit_event)
        return {
            "message": "Azure AD event processed and stored",
            "event_id": event_id,
            "storage_location": "essentials/audit/events/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Azure AD event: {str(e)}")

@router.post("/integrations/okta", response_model=Dict[str, str])
async def receive_okta_event(raw_event: Dict[str, Any]):
    """Receive and process Okta audit events, storing to file system"""
    try:
        # Transform Okta event to our audit format
        audit_event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            user_id=raw_event.get('actor', {}).get('alternateId', 'unknown'),
            action=raw_event.get('eventType', 'authentication'),
            result=AuthenticationResult.SUCCESS if raw_event.get('outcome', {}).get('result') == 'SUCCESS' else AuthenticationResult.FAILURE,
            source_ip=raw_event.get('client', {}).get('ipAddress'),
            user_agent=raw_event.get('client', {}).get('userAgent', {}).get('rawUserAgent'),
            auth_details=AuthenticationDetails(
                identity_provider="Okta",
                failure_reason=raw_event.get('outcome', {}).get('reason')
            ),
            geographic_info=GeographicInfo(
                country=raw_event.get('client', {}).get('geographicalContext', {}).get('country'),
                region=raw_event.get('client', {}).get('geographicalContext', {}).get('state'),
                city=raw_event.get('client', {}).get('geographicalContext', {}).get('city')
            ),
            raw_data=raw_event,
            tags=["okta", "integration"]
        )
        
        event_id = await audit_storage.store_event(audit_event)
        return {
            "message": "Okta event processed and stored",
            "event_id": event_id,
            "storage_location": "essentials/audit/events/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Okta event: {str(e)}")

@router.post("/integrations/adfs", response_model=Dict[str, str])
async def receive_adfs_event(raw_event: Dict[str, Any]):
    """Receive and process ADFS audit events, storing to file system"""
    try:
        # Transform ADFS event to our audit format
        audit_event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            user_id=raw_event.get('username', 'unknown'),
            action=raw_event.get('action', 'login'),
            result=AuthenticationResult.SUCCESS if raw_event.get('result') == 'success' else AuthenticationResult.FAILURE,
            source_ip=raw_event.get('client_ip'),
            user_agent=raw_event.get('user_agent'),
            auth_details=AuthenticationDetails(
                identity_provider="ADFS",
                failure_reason=raw_event.get('failure_reason'),
                error_code=raw_event.get('error_code')
            ),
            raw_data=raw_event,
            tags=["adfs", "integration"]
        )
        
        event_id = await audit_storage.store_event(audit_event)
        return {
            "message": "ADFS event processed and stored",
            "event_id": event_id,
            "storage_location": "essentials/audit/events/"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process ADFS event: {str(e)}")

# =================== BACKGROUND TASKS ===================

async def process_high_risk_event(event: AuditEvent):
    """Process high-risk events in the background"""
    try:
        # Simulate alerting to SIEM or security team
        print(f"🚨 HIGH RISK EVENT DETECTED:")
        print(f"   User: {event.user_id}")
        print(f"   Risk Score: {event.risk_assessment.risk_score}")
        print(f"   Source IP: {event.source_ip}")
        print(f"   Factors: {', '.join(event.risk_assessment.contributing_factors)}")
        print(f"   Stored to: essentials/audit/events/{event.timestamp.strftime('%Y/%m')}")
        
        # Create incident record in file system
        incident_data = {
            "incident_id": str(uuid.uuid4()),
            "event_id": event.event_id,
            "user_id": event.user_id,
            "risk_score": event.risk_assessment.risk_score,
            "risk_level": event.risk_assessment.risk_level,
            "contributing_factors": event.risk_assessment.contributing_factors,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open",
            "assigned_to": None,
            "resolution": None
        }
        
        # Store incident to incidents file
        incident_file = Path("essentials/audit/incidents") / f"incidents_{datetime.now().strftime('%Y-%m')}.jsonl"
        incident_file.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(incident_file, 'a') as f:
            await f.write(json.dumps(incident_data) + '\n')
        
        await asyncio.sleep(1)  # Simulate processing time
        
    except Exception as e:
        print(f"Error processing high-risk event: {e}")

async def perform_export(start_date: datetime, end_date: datetime, format: str, filename: str, filters: Optional[AuditQuery] = None):
    """Perform audit data export in background"""
    try:
        print(f"🔄 Starting export: {filename}")
        
        # Export using file storage
        output_path = await audit_storage.file_storage.export_events(
            start_date=start_date,
            end_date=end_date,
            format=format,
            output_path=f"essentials/audit/reports/{filename}"
        )
        
        print(f"✅ Export completed: {output_path}")
        
        # Create export metadata
        metadata = {
            "export_id": filename.replace(f'.{format}', ''),
            "filename": filename,
            "format": format,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "file_path": output_path,
            "status": "completed"
        }
        
        metadata_file = Path("essentials/audit/reports") / f"{filename}.metadata.json"
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        
        # Create error metadata
        error_metadata = {
            "export_id": filename.replace(f'.{format}', ''),
            "filename": filename,
            "status": "failed",
            "error": str(e),
            "created_at": datetime.utcnow().isoformat()
        }
        
        error_file = Path("essentials/audit/reports") / f"{filename}.error.json"
        async with aiofiles.open(error_file, 'w') as f:
            await f.write(json.dumps(error_metadata, indent=2))

print("✅ Enhanced Audit Router with File-Based Storage loaded successfully!")
print(f"📁 Storage Location: essentials/audit/")
print(f"📄 File Format: {storage_config.format}")
print(f"🔄 Rotation: {storage_config.rotation}")
print(f"🗜️ Compression: {storage_config.compress_old_files}")
print(f"💾 Backup: {storage_config.backup_enabled}")