#!/usr/bin/env python3
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
    
    print(f"\n✅ Created {len(created_alerts)} demo alerts")
    print("📱 View them at: http://localhost:8000/api/v1/security/alerts")
    
    return created_alerts

if __name__ == "__main__":
    print("⚠️  Make sure the server is running first!")
    print("   python run_threat_detection.py")
    print()
    create_demo_alerts()
