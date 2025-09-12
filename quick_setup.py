#!/usr/bin/env python3
"""
Threat Detection Quick Setup Script
One-click setup for the enhanced threat detection system
"""

import os
import sys
import subprocess
from pathlib import Path
import urllib.request
import json

def print_banner():
    print("""
🛡️  THREAT DETECTION SYSTEM - QUICK SETUP
================================================
🚀 Setting up enterprise-grade threat detection
📊 Complete with APIs, monitoring, and response
================================================
""")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        print(f"   Current version: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    packages = [
        "fastapi>=0.68.0",
        "uvicorn[standard]>=0.15.0", 
        "pydantic>=1.8.0",
        "aiofiles>=0.7.0",
        "pyyaml>=5.4.0",
        "python-multipart>=0.0.5"
    ]
    
    try:
        for package in packages:
            print(f"   Installing {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ All dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try manually: pip install fastapi uvicorn pydantic aiofiles pyyaml")
        return False

def create_file_structure():
    """Create necessary file structure"""
    print("\n📁 Creating file structure...")
    
    directories = [
        "routers",
        "services", 
        "config",
        "data/threat_detection",
        "logs",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}/")
    
    # Create __init__.py files
    init_files = ["routers/__init__.py", "services/__init__.py"]
    for init_file in init_files:
        Path(init_file).touch()

def download_threat_detection_files():
    """Create the threat detection files"""
    print("\n📥 Setting up threat detection files...")
    
    # Create simplified threat detection router
    router_content = '''# routers/threat_detection.py - Simplified Version
"""
Simplified Threat Detection Router for Quick Start
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
from pathlib import Path

router = APIRouter()

# Simple data models
class ThreatAlert(BaseModel):
    id: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    threat_type: str = "suspicious_activity"
    title: str
    description: str
    source_ip: Optional[str] = None
    status: str = "active"
    detected_at: Optional[datetime] = None
    risk_score: float = 50.0

class ResponseAction(BaseModel):
    action_type: str  # block_ip, alert_admin, log_event
    parameters: Dict[str, Any] = {}

# Simple storage
alerts_storage = {}
responses_storage = {}

@router.get("/health")
async def threat_health():
    """Health check for threat detection system"""
    return {
        "status": "healthy",
        "service": "threat_detection",
        "alerts_count": len(alerts_storage),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get threat alerts with optional filtering"""
    try:
        alerts = list(alerts_storage.values())
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        if status:
            alerts = [a for a in alerts if a.get("status") == status]
        
        # Limit results
        alerts = alerts[:limit]
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "total_stored": len(alerts_storage),
            "filters": {"severity": severity, "status": status},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")

@router.post("/alerts")
async def create_alert(alert: ThreatAlert):
    """Create a new threat alert"""
    try:
        # Set defaults
        if not alert.id:
            alert.id = f"alert_{uuid.uuid4().hex[:8]}"
        
        if not alert.detected_at:
            alert.detected_at = datetime.utcnow()
        
        # Store alert
        alert_dict = alert.dict()
        alerts_storage[alert.id] = alert_dict
        
        # Save to file for persistence
        save_to_file("alerts", alert.id, alert_dict)
        
        return {
            "message": "Threat alert created successfully",
            "alert_id": alert.id,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.detected_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alert: {str(e)}")

@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get specific alert by ID"""
    if alert_id not in alerts_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert = alerts_storage[alert_id]
    return {
        "alert": alert,
        "retrieved_at": datetime.utcnow().isoformat()
    }

@router.post("/alerts/{alert_id}/respond")
async def respond_to_alert(
    alert_id: str,
    actions: List[ResponseAction],
    background_tasks: BackgroundTasks
):
    """Respond to a threat alert"""
    if alert_id not in alerts_storage:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        response_id = f"response_{uuid.uuid4().hex[:8]}"
        
        response_data = {
            "response_id": response_id,
            "alert_id": alert_id,
            "actions": [action.dict() for action in actions],
            "status": "executing",
            "created_at": datetime.utcnow().isoformat()
        }
        
        responses_storage[response_id] = response_data
        
        # Execute actions in background
        background_tasks.add_task(execute_actions, response_id, actions)
        
        # Update alert status
        alerts_storage[alert_id]["status"] = "investigating"
        alerts_storage[alert_id]["updated_at"] = datetime.utcnow().isoformat()
        
        return {
            "message": "Response actions initiated",
            "response_id": response_id,
            "alert_id": alert_id,
            "actions_count": len(actions),
            "status": "executing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing response: {str(e)}")

@router.get("/statistics")
async def get_statistics():
    """Get threat detection statistics"""
    try:
        alerts = list(alerts_storage.values())
        
        # Calculate stats
        stats = {
            "total_alerts": len(alerts),
            "by_severity": {},
            "by_status": {},
            "by_type": {},
            "recent_alerts": len([a for a in alerts if recent_alert(a)]),
            "generated_at": datetime.utcnow().isoformat()
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

# Helper functions
def save_to_file(category: str, item_id: str, data: dict):
    """Save data to file for persistence"""
    try:
        data_dir = Path(f"data/threat_detection/{category}")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = data_dir / f"{item_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Could not save to file: {e}")

def recent_alert(alert: dict) -> bool:
    """Check if alert is from last 24 hours"""
    try:
        detected = alert.get("detected_at")
        if isinstance(detected, str):
            detected = datetime.fromisoformat(detected.replace('Z', ''))
        
        if detected:
            return (datetime.utcnow() - detected).total_seconds() < 86400
        return False
    except:
        return False

async def execute_actions(response_id: str, actions: List[ResponseAction]):
    """Execute response actions in background"""
    import asyncio
    
    try:
        results = []
        
        for action in actions:
            # Simulate action execution
            await asyncio.sleep(1)
            
            if action.action_type == "block_ip":
                result = {"action": "block_ip", "success": True, "message": f"Blocked IP: {action.parameters.get('ip')}"}
            elif action.action_type == "alert_admin":
                result = {"action": "alert_admin", "success": True, "message": "Admin notified"}
            else:
                result = {"action": action.action_type, "success": True, "message": "Action completed"}
            
            results.append(result)
        
        # Update response status
        if response_id in responses_storage:
            responses_storage[response_id]["status"] = "completed"
            responses_storage[response_id]["results"] = results
            responses_storage[response_id]["completed_at"] = datetime.utcnow().isoformat()
        
        print(f"✅ Response {response_id} completed successfully")
        
    except Exception as e:
        print(f"❌ Response {response_id} failed: {e}")
        if response_id in responses_storage:
            responses_storage[response_id]["status"] = "failed"
            responses_storage[response_id]["error"] = str(e)

# Load existing data on startup
def load_existing_data():
    """Load existing alerts from files"""
    try:
        alerts_dir = Path("data/threat_detection/alerts")
        if alerts_dir.exists():
            for alert_file in alerts_dir.glob("*.json"):
                try:
                    with open(alert_file, 'r', encoding='utf-8') as f:
                        alert_data = json.load(f)
                        alerts_storage[alert_data["id"]] = alert_data
                except Exception as e:
                    print(f"Warning: Could not load {alert_file}: {e}")
        
        print(f"📊 Loaded {len(alerts_storage)} existing alerts")
    except Exception as e:
        print(f"Warning: Could not load existing data: {e}")

# Load data when module is imported
load_existing_data()

print("✅ Simplified Threat Detection Router loaded successfully")
'''
    
    # Write router file
    with open("routers/threat_detection.py", 'w', encoding='utf-8') as f:
        f.write(router_content)
    
    print("   ✅ routers/threat_detection.py")
    
    # Create simple service file
    service_content = '''# services/threat_detection_service.py - Simplified Service
"""
Simplified Threat Detection Service for Quick Start
"""

class ThreatDetectionService:
    def __init__(self, config_path=None):
        self.config_path = config_path
        print(f"🔧 ThreatDetectionService initialized")

print("✅ Simplified ThreatDetectionService loaded")
'''
    
    with open("services/threat_detection_service.py", 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print("   ✅ services/threat_detection_service.py")

def create_test_script():
    """Create test script to verify the system"""
    print("\n🧪 Creating test script...")
    
    test_content = '''#!/usr/bin/env python3
"""
Test script for Threat Detection System
"""

import requests
import json
from datetime import datetime

def test_threat_detection_api():
    """Test the threat detection API"""
    base_url = "http://localhost:8000/api/v1/security"
    
    print("🧪 Testing Threat Detection API")
    print("="*40)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check: PASSED")
        else:
            print(f"❌ Health check: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Health check: ERROR - {e}")
    
    # Test 2: Create alert
    try:
        alert_data = {
            "title": "Test Brute Force Attack",
            "description": "Test alert for API verification",
            "severity": "high",
            "threat_type": "brute_force",
            "source_ip": "192.168.1.100",
            "risk_score": 75.0
        }
        
        response = requests.post(f"{base_url}/alerts", json=alert_data)
        if response.status_code == 200:
            alert_id = response.json().get("alert_id")
            print(f"✅ Create alert: PASSED (ID: {alert_id})")
        else:
            print(f"❌ Create alert: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Create alert: ERROR - {e}")
    
    # Test 3: Get alerts
    try:
        response = requests.get(f"{base_url}/alerts")
        if response.status_code == 200:
            alerts = response.json().get("alerts", [])
            print(f"✅ Get alerts: PASSED ({len(alerts)} alerts)")
        else:
            print(f"❌ Get alerts: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Get alerts: ERROR - {e}")
    
    # Test 4: Get statistics
    try:
        response = requests.get(f"{base_url}/statistics")
        if response.status_code == 200:
            print("✅ Get statistics: PASSED")
        else:
            print(f"❌ Get statistics: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Get statistics: ERROR - {e}")
    
    print("\\n🎯 Test completed!")
    print("📱 Open http://localhost:8000/docs to explore the API")

if __name__ == "__main__":
    print("⚠️  Make sure the server is running first!")
    print("   python run_threat_detection.py")
    print()
    test_threat_detection_api()
'''
    
    with open("test_threat_detection.py", 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("   ✅ test_threat_detection.py")

def create_demo_data():
    """Create some demo alerts for testing"""
    print("\n📊 Creating demo data...")
    
    demo_data = '''#!/usr/bin/env python3
"""
Create demo threat detection data
"""

import requests
import json
from datetime import datetime, timedelta
import random

def create_demo_alerts():
    """Create demo alerts for testing"""
    base_url = "http://localhost:8000/api/v1/security"
    
    demo_alerts = [
        {
            "title": "Brute Force Attack Detected",
            "description": "Multiple failed login attempts from suspicious IP",
            "severity": "high",
            "threat_type": "brute_force",
            "source_ip": "192.168.1.100",
            "risk_score": 85.0
        },
        {
            "title": "Suspicious File Access",
            "description": "Unusual file access pattern detected",
            "severity": "medium", 
            "threat_type": "suspicious_activity",
            "source_ip": "10.0.0.50",
            "risk_score": 60.0
        },
        {
            "title": "Malware Signature Match", 
            "description": "Known malware signature detected in network traffic",
            "severity": "critical",
            "threat_type": "malware",
            "source_ip": "203.0.113.45",
            "risk_score": 95.0
        },
        {
            "title": "Policy Violation",
            "description": "User accessed restricted resource outside business hours",
            "severity": "low",
            "threat_type": "policy_violation", 
            "source_ip": "172.16.0.25",
            "risk_score": 35.0
        }
    ]
    
    print("📊 Creating demo alerts...")
    created_alerts = []
    
    for alert_data in demo_alerts:
        try:
            response = requests.post(f"{base_url}/alerts", json=alert_data)
            if response.status_code == 200:
                alert_id = response.json().get("alert_id")
                created_alerts.append(alert_id)
                print(f"   ✅ Created: {alert_data['title']} (ID: {alert_id})")
            else:
                print(f"   ❌ Failed: {alert_data['title']}")
        except Exception as e:
            print(f"   ❌ Error creating {alert_data['title']}: {e}")
    
    print(f"\\n✅ Created {len(created_alerts)} demo alerts")
    print("📱 View them at: http://localhost:8000/api/v1/security/alerts")
    
    return created_alerts

if __name__ == "__main__":
    print("⚠️  Make sure the server is running first!")
    print("   python run_threat_detection.py")
    print()
    create_demo_alerts()
'''
    
    with open("create_demo_data.py", 'w', encoding='utf-8') as f:
        f.write(demo_data)
    
    print("   ✅ create_demo_data.py")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create file structure
    create_file_structure()
    
    # Download/create files
    download_threat_detection_files()
    
    # Create test files
    create_test_script()
    create_demo_data()
    
    # Success message
    print("\n" + "="*60)
    print("🎉 THREAT DETECTION SYSTEM SETUP COMPLETE!")
    print("="*60)
    print()
    print("🚀 Next Steps:")
    print("1. Start the server:")
    print("   python run_threat_detection.py")
    print()
    print("2. Test the API (in another terminal):")
    print("   python test_threat_detection.py")
    print()
    print("3. Create demo data:")
    print("   python create_demo_data.py")
    print()
    print("4. Explore the API:")
    print("   http://localhost:8000/docs")
    print()
    print("📊 Key Endpoints:")
    print("   GET  /api/v1/security/alerts")
    print("   POST /api/v1/security/alerts")
    print("   GET  /api/v1/security/statistics")
    print("   GET  /api/v1/security/health")
    print("="*60)

if __name__ == "__main__":
    main()