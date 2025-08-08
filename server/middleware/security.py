# middleware/security.py - Security Middleware
from fastapi import Request, HTTPException
from fastapi.responses import Response
from typing import Callable

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, request: Request, call_next: Callable):
        # Check for common security threats
        if self._is_suspicious_request(request):
            raise HTTPException(status_code=403, detail="Forbidden")
            
        response = await call_next(request)
        
        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://d3js.org; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:;"
        })
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check for suspicious request patterns"""
        # Check for common attack patterns
        suspicious_patterns = [
            'script>', '<iframe', 'javascript:', 'data:text/html',
            'eval(', 'document.cookie', 'window.location'
        ]
        
        # Check headers and query parameters
        for key, value in request.headers.items():
            if isinstance(value, str):
                for pattern in suspicious_patterns:
                    if pattern.lower() in value.lower():
                        return True
                        
        return False