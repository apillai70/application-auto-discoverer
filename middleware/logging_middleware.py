# middleware/logging_middleware.py
"""
Testable logging middleware for request/response capture
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Testable request/response logging middleware"""
    
    def __init__(self, app: ASGIApp, config: Dict[str, Any] = None):
        super().__init__(app)
        self.config = config or {}
        self.excluded_paths = self.config.get('excluded_paths', ['/health', '/metrics'])
        self.requests_logged = []
        logging.info("RequestResponseLoggingMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with logging"""
        
        # Skip excluded paths
        if any(request.url.path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract request context
        request_context = self._extract_request_context(request, correlation_id)
        
        # Process request
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "correlation_id": correlation_id}
            )
        
        # Calculate timing
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the request/response
        log_entry = {
            'correlation_id': correlation_id,
            'request': request_context,
            'response': {
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'headers': dict(response.headers)
            },
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        
        self.requests_logged.append(log_entry)
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log to comprehensive logging system if available
        await self._log_to_comprehensive_system(log_entry)
        
        return response
    
    def _extract_request_context(self, request: Request, correlation_id: str) -> Dict[str, Any]:
        """Extract request context"""
        
        return {
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': self._sanitize_headers(dict(request.headers)),
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', ''),
            'correlation_id': correlation_id
        }
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers"""
        
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = '[MASKED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        # Check for forwarded headers
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'
    
    async def _log_to_comprehensive_system(self, log_entry: Dict[str, Any]):
        """Log to comprehensive logging system if available"""
        
        try:
            from services.comprehensive_logging_system import get_comprehensive_logger
            
            logger = get_comprehensive_logger()
            if logger:
                # Convert middleware log to comprehensive log format
                comprehensive_log = {
                    'level': 'ERROR' if log_entry.get('error') else 'INFO',
                    'source': 'API',
                    'log_type': 'REQUEST',
                    'message': f"{log_entry['request']['method']} {log_entry['request']['path']} - {log_entry['response']['status_code']}",
                    'correlation_id': log_entry['correlation_id'],
                    'details': log_entry
                }
                
                await logger.log_entry(comprehensive_log)
                
        except Exception as e:
            logging.debug(f"Could not log to comprehensive system: {e}")
    
    def get_logged_requests(self) -> list:
        """Get all logged requests (for testing)"""
        return self.requests_logged.copy()
    
    def clear_logged_requests(self):
        """Clear logged requests (for testing)"""
        self.requests_logged.clear()
