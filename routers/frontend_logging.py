# routers/frontend_logging.py
"""
Testable frontend logging router
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any, List
import logging

router = APIRouter()

router_metadata = {
    "prefix": "/api/v1/logs",
    "tags": ["frontend-logging"],
    "description": "Frontend log collection and processing",
    "version": "2.2.0", 
    "enabled": True
}

# Mock storage for frontend logs
frontend_logs = []
session_stats = {}

@router.post("/frontend")
async def receive_frontend_logs(
    log_batch: Dict[str, Any]
):
    """Receive and process frontend log batch"""
    
    logs = log_batch.get('logs', [])
    batch_id = log_batch.get('batch_id', 'unknown')
    
    processed_count = 0
    errors = []
    
    for log_entry in logs:
        try:
            # Validate log entry
            if not log_entry.get('message'):
                errors.append("Missing message field")
                continue
            
            # Process log entry
            processed_log = {
                **log_entry,
                'processed_at': datetime.now().isoformat(),
                'batch_id': batch_id
            }
            
            frontend_logs.append(processed_log)
            
            # Update session stats
            session_id = log_entry.get('session_id', 'unknown')
            if session_id not in session_stats:
                session_stats[session_id] = {
                    'log_count': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat()
                }
            
            session_stats[session_id]['log_count'] += 1
            session_stats[session_id]['last_seen'] = datetime.now().isoformat()
            
            processed_count += 1
            
        except Exception as e:
            errors.append(f"Error processing log: {str(e)}")
    
    # Send to comprehensive logging if available
    try:
        from services.comprehensive_logging_system import get_comprehensive_logger
        logger = get_comprehensive_logger()
        
        if logger:
            await logger.log_entry({
                'level': 'INFO',
                'source': 'FRONTEND',
                'log_type': 'BATCH_RECEIVED',
                'message': f'Frontend batch received: {processed_count} logs',
                'details': {
                    'batch_id': batch_id,
                    'total_logs': len(logs),
                    'processed_count': processed_count,
                    'error_count': len(errors)
                }
            })
    except Exception:
        pass  # Ignore if comprehensive logging not available
    
    return {
        "status": "success" if not errors else "partial",
        "received_count": len(logs),
        "processed_count": processed_count,
        "errors": errors,
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/frontend/health")
async def frontend_logging_health():
    """Health check for frontend logging"""
    
    return {
        "status": "healthy",
        "component": "frontend_logging",
        "logs_received": len(frontend_logs),
        "active_sessions": len(session_stats),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/frontend/statistics")
async def get_frontend_statistics():
    """Get frontend logging statistics"""
    
    return {
        "total_logs": len(frontend_logs),
        "active_sessions": len(session_stats),
        "session_stats": session_stats,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/frontend/session/{session_id}")
async def get_session_logs(session_id: str):
    """Get logs for specific session"""
    
    session_logs = [
        log for log in frontend_logs 
        if log.get('session_id') == session_id
    ]
    
    return {
        "session_id": session_id,
        "logs": session_logs,
        "total_count": len(session_logs),
        "session_stats": session_stats.get(session_id, {}),
        "timestamp": datetime.now().isoformat()
    }

# Test endpoints
@router.post("/frontend/test")
async def test_frontend_logging():
    """Test frontend logging functionality"""
    
    test_log_batch = {
        "batch_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "logs": [
            {
                "id": "test_log_1",
                "session_id": "test_session",
                "message": "Test frontend log",
                "level": "INFO",
                "timestamp": datetime.now().isoformat(),
                "event_type": "test",
                "action": "test_action"
            }
        ]
    }
    
    # Process the test batch
    result = await receive_frontend_logs(test_log_batch)
    
    return {
        "test_status": "completed",
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
