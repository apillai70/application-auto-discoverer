#!/usr/bin/env python3
"""
Fixed Threat Detection Main Server
Ensures the router is properly included and endpoints work correctly
"""

import os
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_app() -> FastAPI:
    """Create and configure FastAPI application with proper router inclusion"""
    
    app = FastAPI(
        title="Enhanced Threat Detection System",
        description="Enterprise-grade threat detection and response platform",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Basic health endpoint (this one works)
    @app.get("/")
    async def root():
        return {
            "message": "Enhanced Threat Detection System",
            "version": "2.0.0",
            "status": "operational",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "threat_detection": "/api/v1/security/"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": "threat_detection",
            "version": "2.0.0"
        }

    # Try to include the threat detection router
    try:
        from routers.threat_detection import router as threat_router
        app.include_router(
            threat_router,
            prefix="/api/v1/security",
            tags=["threat-detection", "security"]
        )
        print("✅ Threat detection router loaded successfully")
        
        # Verify routes were added
        routes = [route.path for route in app.routes]
        security_routes = [route for route in routes if "/api/v1/security" in route]
        print(f"📊 Security routes registered: {len(security_routes)}")
        for route in security_routes:
            print(f"   🔗 {route}")
            
    except ImportError as e:
        print(f"⚠️ Could not load threat detection router: {e}")
        print("📝 Creating fallback endpoints...")
        
        # Create fallback endpoints if router fails to load
        create_fallback_endpoints(app)
    
    return app

def create_fallback_endpoints(app: FastAPI):
    """Create fallback endpoints if the main router fails to load"""
    
    # In-memory storage for fallback
    alerts_storage = {}
    
    @app.get("/api/v1/security/health")
    async def security_health():
        """Security system health check"""
        return {
            "status": "healthy",
            "service": "threat_detection_fallback",
            "alerts_count": len(alerts_storage),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "fallback"
        }
    
    @app.get("/api/v1/security/alerts")
    async def get_alerts_fallback(
        severity: str = None,
        status: str = None,
        limit: int = 100
    ):
        """Get threat alerts - fallback implementation"""
        try:
            alerts = list(alerts_storage.values())
            
            # Apply basic filtering
            if severity:
                alerts = [a for a in alerts if a.get("severity") == severity]
            if status:
                alerts = [a for a in alerts if a.get("status") == status]
            
            alerts = alerts[:limit]
            
            return {
                "alerts": alerts,
                "count": len(alerts),
                "total_stored": len(alerts_storage),
                "filters": {"severity": severity, "status": status},
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "fallback"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")
    
    @app.post("/api/v1/security/alerts")
    async def create_alert_fallback(alert_data: dict):
        """Create threat alert - fallback implementation"""
        try:
            import uuid
            
            # Generate alert ID
            alert_id = f"alert_{uuid.uuid4().hex[:8]}"
            
            # Set defaults
            alert = {
                "id": alert_id,
                "title": alert_data.get("title", "Unknown Threat"),
                "description": alert_data.get("description", ""),
                "severity": alert_data.get("severity", "medium"),
                "threat_type": alert_data.get("threat_type", "suspicious_activity"),
                "source_ip": alert_data.get("source_ip"),
                "status": "active",
                "risk_score": alert_data.get("risk_score", 50.0),
                "detected_at": datetime.utcnow().isoformat(),
                "created_by": "fallback_system"
            }
            
            # Store alert
            alerts_storage[alert_id] = alert
            
            return {
                "message": "Threat alert created successfully",
                "alert_id": alert_id,
                "severity": alert["severity"],
                "status": alert["status"],
                "created_at": alert["detected_at"],
                "mode": "fallback"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating alert: {str(e)}")
    
    @app.get("/api/v1/security/alerts/{alert_id}")
    async def get_alert_fallback(alert_id: str):
        """Get specific alert - fallback implementation"""
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "alert": alerts_storage[alert_id],
            "retrieved_at": datetime.utcnow().isoformat(),
            "mode": "fallback"
        }
    
    @app.post("/api/v1/security/alerts/{alert_id}/respond")
    async def respond_to_alert_fallback(alert_id: str, response_data: dict):
        """Respond to alert - fallback implementation"""
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        try:
            import uuid
            response_id = f"response_{uuid.uuid4().hex[:8]}"
            
            # Update alert status
            alerts_storage[alert_id]["status"] = "investigating"
            alerts_storage[alert_id]["updated_at"] = datetime.utcnow().isoformat()
            
            return {
                "message": "Response actions initiated (simulated)",
                "response_id": response_id,
                "alert_id": alert_id,
                "status": "completed",
                "mode": "fallback"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error executing response: {str(e)}")
    
    @app.get("/api/v1/security/statistics")
    async def get_statistics_fallback():
        """Get statistics - fallback implementation"""
        try:
            alerts = list(alerts_storage.values())
            
            stats = {
                "total_alerts": len(alerts),
                "by_severity": {},
                "by_status": {},
                "by_type": {},
                "generated_at": datetime.utcnow().isoformat(),
                "mode": "fallback"
            }
            
            # Count by categories
            for alert in alerts:
                severity = alert.get("severity", "unknown")
                status = alert.get("status", "unknown")
                threat_type = alert.get("threat_type", "unknown")
                
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                stats["by_type"][threat_type] = stats["by_type"].get(threat_type, 0) + 1
            
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating statistics: {str(e)}")
    
    print("✅ Fallback endpoints created successfully")
    print("📊 Available endpoints:")
    print("   GET  /api/v1/security/health")
    print("   GET  /api/v1/security/alerts")
    print("   POST /api/v1/security/alerts")
    print("   GET  /api/v1/security/alerts/{id}")
    print("   POST /api/v1/security/alerts/{id}/respond")
    print("   GET  /api/v1/security/statistics")

def main():
    """Main application runner with better error handling"""
    print("🛡️ Enhanced Threat Detection System - FIXED VERSION")
    print("="*60)
    
    # Create directories if they don't exist
    directories = ["routers", "services", "config", "data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Create app
    print("🚀 Creating FastAPI application...")
    app = create_app()
    
    # Display startup information
    print("\n" + "="*60)
    print("🎯 THREAT DETECTION SYSTEM READY")
    print("="*60)
    print("📱 API Documentation: http://localhost:8001/docs")
    print("🔧 Health Check: http://localhost:8001/health")
    print("🛡️ Security Health: http://localhost:8001/api/v1/security/health")
    print("📊 All Endpoints:")
    print("   GET  /")
    print("   GET  /health")
    print("   GET  /docs")
    print("   GET  /api/v1/security/health")
    print("   GET  /api/v1/security/alerts")
    print("   POST /api/v1/security/alerts")
    print("   GET  /api/v1/security/statistics")
    print("="*60)
    
    # Start server
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Threat Detection System stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

if __name__ == "__main__":
    main()