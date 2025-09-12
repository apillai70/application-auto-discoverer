# routers/enhanced_audit.py
"""
Enhanced audit router with file-based storage integration
Replaces or enhances the existing audit.py router
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid

# Import authentication
from routers.auth import get_current_user, require_admin, check_permission

# Import storage components
from storage.file_audit_storage import FileAuditStorage, StorageConfig
from storage.log_storage_manager import LogStorageManager, LogCategory
from services.frontend_security_logs import FrontendSecurityLogService

router = APIRouter()

# Initialize storage components
audit_storage = FileAuditStorage(StorageConfig(
    base_path="essentials/audit",
    retention_days=365,
    compress_old_files=True
))

log_storage = LogStorageManager()
frontend_log_service = FrontendSecurityLogService()

# Pydantic models
class AuditEventCreate(BaseModel):
    event_type: str
    action: str
    result: str
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class FrontendLogEvent(BaseModel):
    event_type: str = Field(..., description="Type of frontend event")
    level: str = Field(default="info", description="Log level")
    action: str = Field(..., description="Action performed")
    page_url: str = Field(..., description="Page URL where event occurred")
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class LogQuery(BaseModel):
    category: str = Field(..., description="Log category to query")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    level: Optional[str] = None
    component: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)

# ===================== AUDIT EVENT ENDPOINTS =====================

@router.post("/events")
async def create_audit_event(
    event: AuditEventCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Create a new audit event with file storage"""
    
    try:
        # Create audit event with file storage
        audit_event = {
            "event_type": event.event_type,
            "user_id": current_user["user_id"],
            "action": event.action,
            "result": event.result,
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "timestamp": datetime.now().isoformat(),
            "session_id": current_user.get("session_id"),
            "additional_data": event.additional_data or {}
        }
        
        # Store in file-based audit storage
        event_id = await audit_storage.store_event(audit_event)
        
        # Also log to application logs
        background_tasks.add_task(
            log_storage.log_audit_event,
            action=event.action,
            result=event.result,
            user_id=current_user["user_id"],
            details=audit_event,
            source_ip=event.source_ip
        )
        
        return {
            "event_id": event_id,
            "message": "Audit event created successfully",
            "timestamp": audit_event["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit event: {str(e)}")

@router.get("/events")
async def get_audit_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_ids: Optional[List[str]] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    results: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get audit events from file storage"""
    
    try:
        # Check permissions - only admin or security can view all events
        if not check_permission(current_user, ["admin", "security"]):
            # Regular users can only see their own events
            user_ids = [current_user["user_id"]]
        
        events = await audit_storage.query_events(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_ids,
            event_types=event_types,
            results=results,
            limit=limit
        )
        
        return {
            "events": events,
            "count": len(events),
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "user_ids": user_ids,
                "event_types": event_types,
                "results": results
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit events: {str(e)}")

@router.get("/events/summary")
async def get_audit_summary(
    days: int = Query(7, ge=1, le=365),
    current_user: dict = Depends(check_permission(["admin", "security"]))
):
    """Get audit event summary statistics"""
    
    try:
        summary = await audit_storage.get_summary_statistics(days=days)
        
        return {
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audit summary: {str(e)}")

@router.post("/events/export")
async def export_audit_events(
    start_date: datetime,
    end_date: datetime,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: dict = Depends(require_admin)
):
    """Export audit events to file"""
    
    try:
        export_path = await audit_storage.export_events(
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return {
            "export_path": export_path,
            "message": f"Audit events exported successfully",
            "format": format,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export audit events: {str(e)}")

# ===================== FRONTEND LOGGING ENDPOINTS =====================

@router.post("/frontend/events")
async def log_frontend_event(
    event: FrontendLogEvent,
    current_user: dict = Depends(get_current_user)
):
    """Log frontend security events"""
    
    try:
        # Prepare event data for frontend log service
        event_data = {
            "event_type": event.event_type,
            "level": event.level,
            "action": event.action,
            "page_url": event.page_url,
            "session_id": event.session_id or current_user.get("session_id"),
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "user_id": current_user["user_id"],
            "details": event.details or {}
        }
        
        # Log through frontend security service
        event_id = await frontend_log_service.log_frontend_event(event_data)
        
        return {
            "event_id": event_id,
            "message": "Frontend event logged successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log frontend event: {str(e)}")

@router.post("/frontend/interactions")
async def log_user_interaction(
    interaction_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Log user interaction events from frontend"""
    
    try:
        event_id = await frontend_log_service.log_user_interaction(
            user_id=current_user["user_id"],
            session_id=current_user.get("session_id"),
            interaction_data=interaction_data
        )
        
        return {
            "event_id": event_id,
            "message": "User interaction logged successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log user interaction: {str(e)}")

@router.post("/frontend/api-calls")
async def log_api_call(
    api_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Log API call events from frontend"""
    
    try:
        event_id = await frontend_log_service.log_api_interaction(
            user_id=current_user["user_id"],
            session_id=current_user.get("session_id"),
            api_data=api_data
        )
        
        return {
            "event_id": event_id,
            "message": "API call logged successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log API call: {str(e)}")

@router.post("/frontend/security-violations")
async def log_security_violation(
    violation_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Log security violation events from frontend"""
    
    try:
        event_id = await frontend_log_service.log_security_violation(
            user_id=current_user["user_id"],
            session_id=current_user.get("session_id"),
            violation_data=violation_data
        )
        
        # Also create audit event for security violations
        audit_event = {
            "event_type": "security_violation",
            "user_id": current_user["user_id"],
            "action": violation_data.get("violation_type", "unknown"),
            "result": "detected",
            "source_ip": violation_data.get("source_ip"),
            "additional_data": violation_data
        }
        await audit_storage.store_event(audit_event)
        
        return {
            "event_id": event_id,
            "message": "Security violation logged successfully",
            "severity": "high"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log security violation: {str(e)}")

@router.get("/frontend/user-activity/{user_id}")
async def get_user_activity_summary(
    user_id: str,
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user)
):
    """Get user activity summary from frontend logs"""
    
    try:
        # Check permissions - users can only see their own activity unless admin/security
        if (user_id != current_user["user_id"] and 
            not check_permission(current_user, ["admin", "security"])):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        summary = await frontend_log_service.get_user_activity_summary(user_id, hours)
        
        return {
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")

# ===================== LOG MANAGEMENT ENDPOINTS =====================

@router.post("/logs/query")
async def query_logs(
    query: LogQuery,
    current_user: dict = Depends(check_permission(["admin", "security"]))
):
    """Query logs from storage"""
    
    try:
        # Map category string to LogCategory enum
        from storage.log_storage_manager import LogCategory
        category = LogCategory(query.category)
        
        logs = await log_storage.query_logs(
            category=category,
            start_date=query.start_date,
            end_date=query.end_date,
            level=query.level,
            component=query.component,
            user_id=query.user_id,
            limit=query.limit
        )
        
        return {
            "logs": logs,
            "count": len(logs),
            "query": query.dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {query.category}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query logs: {str(e)}")

@router.get("/logs/categories")
async def get_log_categories(
    current_user: dict = Depends(check_permission(["admin", "security"]))
):
    """Get available log categories"""
    
    from storage.log_storage_manager import LogCategory
    return {
        "categories": [category.value for category in LogCategory],
        "descriptions": {
            "application": "General application events and errors",
            "security": "Security-related events and violations",
            "network": "Network topology and flow events",
            "threats": "Threat detection and response events",
            "performance": "Performance monitoring and metrics",
            "audit": "Audit trail events",
            "debug": "Debug and diagnostic information"
        }
    }

@router.get("/logs/statistics")
async def get_log_statistics(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(check_permission(["admin", "security"]))
):
    """Get log statistics across all categories"""
    
    try:
        stats = await log_storage.get_log_statistics(days=days)
        
        return {
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log statistics: {str(e)}")

@router.post("/logs/export")
async def export_logs(
    category: str,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: dict = Depends(require_admin)
):
    """Export logs to file"""
    
    try:
        from storage.log_storage_manager import LogCategory
        log_category = LogCategory(category)
        
        export_path = await log_storage.export_logs(
            category=log_category,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return {
            "export_path": export_path,
            "message": f"Logs exported successfully",
            "category": category,
            "format": format
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")

# ===================== STORAGE MANAGEMENT ENDPOINTS =====================

@router.get("/storage/info")
async def get_storage_info(
    current_user: dict = Depends(require_admin)
):
    """Get storage system information"""
    
    try:
        audit_info = await audit_storage.get_storage_info()
        log_stats = await log_storage.get_log_statistics(days=7)
        
        return {
            "audit_storage": audit_info,
            "log_storage": {
                "base_path": str(log_storage.base_path),
                "categories": len(log_storage.log_dirs),
                "total_logs_7_days": log_stats.get("total_logs", 0),
                "storage_size_mb": log_stats.get("storage_size_mb", 0)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}")

@router.post("/storage/maintenance")
async def trigger_maintenance(
    action: str = Query(..., regex="^(compress|cleanup|backup)$"),
    current_user: dict = Depends(require_admin)
):
    """Trigger storage maintenance actions"""
    
    try:
        if action == "compress":
            # Trigger compression of old files
            message = "Compression task initiated"
        elif action == "cleanup":
            # Trigger cleanup of old files
            message = "Cleanup task initiated"
        elif action == "backup":
            # Trigger backup creation
            message = "Backup task initiated"
        
        # Note: In a real implementation, these would be background tasks
        
        return {
            "action": action,
            "message": message,
            "initiated_at": datetime.now().isoformat(),
            "initiated_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger maintenance: {str(e)}")

# ===================== HEALTH AND STATUS =====================

@router.get("/health")
async def get_audit_health():
    """Get audit system health status"""
    
    try:
        # Check storage accessibility
        audit_health = await audit_storage.get_storage_info()
        log_health = await log_storage.get_log_statistics(days=1)
        
        # Determine overall health
        overall_status = "healthy"
        issues = []
        
        # Check for potential issues
        if audit_health.get("total_size_mb", 0) > 10000:  # > 10GB
            issues.append("Audit storage size is large - consider cleanup")
        
        if log_health.get("total_logs", 0) == 0:
            issues.append("No recent log activity detected")
        
        if issues:
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "audit_storage_health": {
                "accessible": bool(audit_health),
                "size_mb": audit_health.get("total_size_mb", 0),
                "file_count": audit_health.get("total_files", 0)
            },
            "log_storage_health": {
                "accessible": bool(log_health),
                "recent_logs": log_health.get("total_logs", 0),
                "categories_active": len(log_health.get("categories", {}))
            },
            "issues": issues,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }