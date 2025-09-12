#!/usr/bin/env python3
"""
Threat Detection System Runner
Complete setup and execution script for the enhanced threat detection system
"""

import os
import sys
import asyncio
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

def setup_logging():
    """Setup comprehensive logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "threat_detection.log"),
            logging.StreamHandler()
        ]
    )

def create_directories():
    """Create necessary directories"""
    directories = [
        "config",
        "data/threat_detection/alerts",
        "data/threat_detection/executions", 
        "logs/threat_detection",
        "services",
        "routers"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_config_file():
    """Create basic configuration file"""
    config_content = """# config/threat_detection.yaml
# Basic Threat Detection Configuration

storage:
  backend: "file"
  data_retention_days: 365
  backup_enabled: true

analysis:
  auto_analysis_enabled: true
  analysis_timeout_seconds: 120
  max_concurrent_analyses: 10
  
  threat_intelligence:
    enabled: true
    sources:
      - name: "internal_feeds"
        enabled: true

response:
  auto_response_enabled: false
  max_response_actions: 5
  response_timeout_seconds: 300
  approval_required: true
  
  actions:
    block_ip:
      enabled: true
      default_duration_hours: 24
    alert_admin:
      enabled: true

alerting:
  enabled: true
  severity_thresholds:
    critical: 90
    high: 70
    medium: 50
    low: 30

security:
  authentication:
    required: false  # Set to true in production
  rate_limiting:
    enabled: true
  audit:
    enabled: true

logging:
  level: "INFO"
  format: "json"
"""
    
    config_path = Path("config/threat_detection.yaml")
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ Created config file: {config_path}")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
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
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Basic health endpoint
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

    # Include threat detection router
    try:
        from routers.threat_detection import router as threat_router
        app.include_router(
            threat_router,
            prefix="/api/v1/security",
            tags=["threat-detection", "security"]
        )
        print("✅ Threat detection router loaded successfully")
    except ImportError as e:
        print(f"⚠️ Could not load threat detection router: {e}")
        print("📝 Make sure the threat_detection.py file is in the routers/ directory")

    return app

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "aiofiles",
        "pyyaml"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - missing")
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_requirements_file():
    """Create requirements.txt file"""
    requirements = """# Enhanced Threat Detection System Requirements

# Core FastAPI dependencies
fastapi>=0.68.0
uvicorn[standard]>=0.15.0
pydantic>=1.8.0
python-multipart>=0.0.5

# Async file operations
aiofiles>=0.7.0

# Configuration
pyyaml>=5.4.0

# Security and authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
cryptography>=3.4.0

# Optional: Database support
# asyncpg>=0.24.0  # PostgreSQL
# aiomysql>=0.0.21  # MySQL

# Optional: Advanced features
# requests>=2.25.0  # External API calls
# prometheus-client>=0.11.0  # Metrics
# psutil>=5.8.0  # System monitoring

# Development and testing
pytest>=6.2.0
pytest-asyncio>=0.15.0
httpx>=0.24.0  # For testing FastAPI
"""
    
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements)
        print(f"✅ Created requirements file: {requirements_path}")

def create_mock_service():
    """Create mock service file if the real one doesn't exist"""
    service_content = '''# services/threat_detection_service.py - Mock Implementation
"""
Mock Threat Detection Service for demonstration
Replace with the full service implementation from Claude artifacts
"""

class ThreatDetectionService:
    """Mock threat detection service"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        print(f"🔧 Mock ThreatDetectionService initialized with config: {config_path}")
    
    async def get_alerts_advanced(self, **kwargs):
        """Mock get alerts method"""
        return [
            {
                "id": "alert_123",
                "severity": "high",
                "threat_type": "brute_force",
                "title": "Mock Brute Force Attack",
                "description": "Mock alert for demonstration",
                "status": "active",
                "detected_at": "2024-01-15T10:30:00Z"
            }
        ]
    
    async def create_alert(self, alert_data):
        """Mock create alert method"""
        alert_id = alert_data.get("id", "alert_mock_123")
        print(f"📊 Mock alert created: {alert_id}")
        return alert_id

print("⚠️ Using mock ThreatDetectionService - replace with full implementation")
'''
    
    service_path = Path("services/threat_detection_service.py")
    if not service_path.exists():
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(service_content)
        print(f"✅ Created mock service file: {service_path}")
        print("📝 Replace this with the full service implementation from Claude artifacts")

def main():
    """Main application runner"""
    print("🛡️ Enhanced Threat Detection System")
    print("="*50)
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Missing dependencies. Install them and try again.")
        sys.exit(1)
    
    # Create directories and files
    print("\n📁 Setting up directory structure...")
    create_directories()
    create_config_file()
    create_requirements_file()
    create_mock_service()
    
    # Create application
    print("\n🚀 Creating FastAPI application...")
    app = create_app()
    
    # Display startup information
    print("\n" + "="*60)
    print("🎯 THREAT DETECTION SYSTEM READY")
    print("="*60)
    print("📱 API Documentation: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    print("🛡️ Threat Detection API: http://localhost:8000/api/v1/security/")
    print("📊 Sample Endpoints:")
    print("   GET  /api/v1/security/alerts")
    print("   POST /api/v1/security/alerts")
    print("   GET  /api/v1/security/statistics")
    print("   GET  /api/v1/security/health")
    print("="*60)
    
    # Start server
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Threat Detection System stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()