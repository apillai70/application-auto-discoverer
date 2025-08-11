
# middleware/audit_middleware.py - Middleware for automatic audit logging

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import json
from typing import Callable
import asyncio

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API requests and responses"""
    
    def __init__(self, app, audit_storage=None):
        super().__init__(app)
        self.audit_storage = audit_storage
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record start time
        start_time = time.time()
        
        # Extract request information
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": time.time()
        }
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log to audit system if available and it's a relevant endpoint
        if self.audit_storage and self._should_audit_request(request):
            await self._log_api_request(request_info, response, process_time)
        
        return response
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        # Audit authentication-related endpoints
        auth_paths = ["/api/v1/auth", "/api/v1/audit", "/login", "/logout"]
        
        return any(request.url.path.startswith(path) for path in auth_paths)
    
    async def _log_api_request(self, request_info: dict, response: Response, process_time: float):
        """Log API request to audit system"""
        try:
            from routers.audit import AuditEvent, AuditEventType, AuthenticationResult, AuditSeverity
            
            # Determine result based on status code
            if response.status_code < 300:
                result = AuthenticationResult.SUCCESS
                severity = AuditSeverity.INFO
            elif response.status_code < 500:
                result = AuthenticationResult.FAILURE
                severity = AuditSeverity.WARNING
            else:
                result = AuthenticationResult.FAILURE
                severity = AuditSeverity.ERROR
            
            # Create audit event
            audit_event = AuditEvent(
                event_type=AuditEventType.SYSTEM_EVENT,
                user_id="system_api",  # Will be overridden if user context is available
                action=f"{request_info['method']} {request_info['path']}",
                result=result,
                severity=severity,
                source_ip=request_info["client_ip"],
                user_agent=request_info["user_agent"],
                description=f"API request processed in {process_time:.3f}s",
                raw_data={
                    "request": request_info,
                    "response_status": response.status_code,
                    "process_time": process_time
                },
                tags=["api_request", "system_generated"]
            )
            
            # Store the event
            await self.audit_storage.store_event(audit_event)
            
        except Exception as e:
            # Don't let audit logging break the main request
            print(f"Error logging API request to audit: {e}")