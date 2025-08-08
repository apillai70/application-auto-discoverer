# config/cors.py - Advanced CORS Configuration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

class CORSConfig:
    def __init__(self, app: FastAPI, allowed_origins: List[str] = None, allow_all: bool = False):
        self.app = app
        self.allowed_origins = allowed_origins or []
        self.allow_all = allow_all
        
    def setup_cors(self):
        """Configure CORS middleware with proper settings"""
        origins = ["*"] if self.allow_all else self.allowed_origins
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "X-CSRF-Token",
                "X-API-Key",
                "Cache-Control",
                "Pragma",
                "Expires"
            ],
            expose_headers=[
                "Content-Type",
                "Authorization",
                "X-Total-Count",
                "X-Page-Count",
                "X-Per-Page",
                "X-Current-Page"
            ],
            max_age=3600  # Cache preflight requests for 1 hour
        )
        
        # Add CORS headers to responses
        @self.app.middleware("http")
        async def add_cors_headers(request, call_next):
            response = await call_next(request)
            
            # Add additional security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            return response
