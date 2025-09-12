#!/usr/bin/env python3
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
    
    print("\n🎯 Test completed!")
    print("📱 Open http://localhost:8000/docs to explore the API")

if __name__ == "__main__":
    print("⚠️  Make sure the server is running first!")
    print("   python run_threat_detection.py")
    print()
    test_threat_detection_api()
