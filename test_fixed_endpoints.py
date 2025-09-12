#!/usr/bin/env python3
"""
Test script for the fixed threat detection endpoints
"""

import requests
import json
import time
from datetime import datetime

def test_endpoints():
    """Test all threat detection endpoints"""
    base_url = "http://localhost:8001"
    security_url = f"{base_url}/api/v1/security"
    
    print("🧪 Testing Fixed Threat Detection Endpoints")
    print("="*50)
    
    # Test 1: Basic health check
    print("\n1️⃣ Testing basic health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Basic health: PASSED")
            print(f"   📊 Response: {response.json()}")
        else:
            print(f"   ❌ Basic health: FAILED ({response.status_code})")
    except Exception as e:
        print(f"   ❌ Basic health: ERROR - {e}")
    
    # Test 2: Security health check
    print("\n2️⃣ Testing security health check...")
    try:
        response = requests.get(f"{security_url}/health")
        if response.status_code == 200:
            print("   ✅ Security health: PASSED")
            print(f"   📊 Response: {response.json()}")
        else:
            print(f"   ❌ Security health: FAILED ({response.status_code})")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Security health: ERROR - {e}")
    
    # Test 3: Get alerts (empty initially)
    print("\n3️⃣ Testing get alerts...")
    try:
        response = requests.get(f"{security_url}/alerts")
        if response.status_code == 200:
            alerts = response.json()
            print("   ✅ Get alerts: PASSED")
            print(f"   📊 Found {alerts.get('count', 0)} alerts")
        else:
            print(f"   ❌ Get alerts: FAILED ({response.status_code})")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Get alerts: ERROR - {e}")
    
    # Test 4: Create a test alert
    print("\n4️⃣ Testing create alert...")
    try:
        alert_data = {
            "title": "Test Brute Force Attack",
            "description": "Automated test alert for API verification",
            "severity": "high",
            "threat_type": "brute_force",
            "source_ip": "192.168.1.100",
            "risk_score": 85.0
        }
        
        response = requests.post(f"{security_url}/alerts", json=alert_data)
        if response.status_code == 200:
            result = response.json()
            alert_id = result.get("alert_id")
            print("   ✅ Create alert: PASSED")
            print(f"   📊 Alert ID: {alert_id}")
            print(f"   📊 Severity: {result.get('severity')}")
            
            # Test 5: Get the specific alert
            print("\n5️⃣ Testing get specific alert...")
            try:
                response = requests.get(f"{security_url}/alerts/{alert_id}")
                if response.status_code == 200:
                    alert = response.json()
                    print("   ✅ Get specific alert: PASSED")
                    print(f"   📊 Alert title: {alert.get('alert', {}).get('title')}")
                else:
                    print(f"   ❌ Get specific alert: FAILED ({response.status_code})")
            except Exception as e:
                print(f"   ❌ Get specific alert: ERROR - {e}")
            
            # Test 6: Respond to alert
            print("\n6️⃣ Testing alert response...")
            try:
                response_data = {
                    "actions": [
                        {
                            "action_type": "block_ip",
                            "parameters": {"ip": "192.168.1.100"}
                        }
                    ]
                }
                
                response = requests.post(f"{security_url}/alerts/{alert_id}/respond", json=response_data)
                if response.status_code == 200:
                    result = response.json()
                    print("   ✅ Alert response: PASSED")
                    print(f"   📊 Response ID: {result.get('response_id')}")
                else:
                    print(f"   ❌ Alert response: FAILED ({response.status_code})")
                    print(f"   📄 Response: {response.text}")
            except Exception as e:
                print(f"   ❌ Alert response: ERROR - {e}")
                
        else:
            print(f"   ❌ Create alert: FAILED ({response.status_code})")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Create alert: ERROR - {e}")
    
    # Test 7: Get statistics
    print("\n7️⃣ Testing statistics...")
    try:
        response = requests.get(f"{security_url}/statistics")
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Get statistics: PASSED")
            print(f"   📊 Total alerts: {stats.get('total_alerts', 0)}")
            print(f"   📊 By severity: {stats.get('by_severity', {})}")
        else:
            print(f"   ❌ Get statistics: FAILED ({response.status_code})")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Get statistics: ERROR - {e}")
    
    # Test 8: Test filtering
    print("\n8️⃣ Testing alert filtering...")
    try:
        response = requests.get(f"{security_url}/alerts?severity=high&limit=10")
        if response.status_code == 200:
            alerts = response.json()
            print("   ✅ Alert filtering: PASSED")
            print(f"   📊 Filtered alerts: {alerts.get('count', 0)}")
        else:
            print(f"   ❌ Alert filtering: FAILED ({response.status_code})")
    except Exception as e:
        print(f"   ❌ Alert filtering: ERROR - {e}")
    
    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    print("✅ If all tests passed, your API is working correctly!")
    print("📱 Explore more at: http://localhost:8001/docs")
    print("🔍 Try the interactive API documentation")

def create_demo_alerts():
    """Create several demo alerts for testing"""
    base_url = "http://localhost:8001/api/v1/security"
    
    demo_alerts = [
        {
            "title": "Suspicious Login Activity",
            "description": "Multiple failed login attempts from foreign IP",
            "severity": "medium",
            "threat_type": "brute_force",
            "source_ip": "203.0.113.45",
            "risk_score": 65.0
        },
        {
            "title": "Malware Detection",
            "description": "Known malware signature detected in email attachment",
            "severity": "critical",
            "threat_type": "malware",
            "source_ip": "198.51.100.25",
            "risk_score": 95.0
        },
        {
            "title": "Policy Violation",
            "description": "User accessed restricted file outside business hours",
            "severity": "low",
            "threat_type": "policy_violation",
            "source_ip": "172.16.0.50",
            "risk_score": 30.0
        },
        {
            "title": "Data Exfiltration Attempt",
            "description": "Large volume of data transfer to external server",
            "severity": "high",
            "threat_type": "data_exfiltration",
            "source_ip": "10.0.0.75",
            "risk_score": 80.0
        }
    ]
    
    print("\n📊 Creating demo alerts...")
    created_count = 0
    
    for alert_data in demo_alerts:
        try:
            response = requests.post(f"{base_url}/alerts", json=alert_data)
            if response.status_code == 200:
                result = response.json()
                created_count += 1
                print(f"   ✅ Created: {alert_data['title']} (ID: {result.get('alert_id')})")
            else:
                print(f"   ❌ Failed: {alert_data['title']} ({response.status_code})")
        except Exception as e:
            print(f"   ❌ Error creating {alert_data['title']}: {e}")
    
    print(f"\n✅ Created {created_count} demo alerts")
    return created_count

def main():
    """Main test function"""
    print("⚠️  Make sure the server is running first!")
    print("   python fixed_main.py")
    print("\n" + "="*60)
    
    # Wait a moment for user to start server if needed
    print("Starting tests in 3 seconds...")
    time.sleep(3)
    
    # Run basic endpoint tests
    test_endpoints()
    
    # Ask if user wants demo data
    print("\n" + "="*50)
    create_demo = input("🎯 Create demo alerts? (y/n): ").lower().strip()
    if create_demo in ['y', 'yes']:
        create_demo_alerts()
        
        # Show final statistics
        print("\n📊 Final statistics:")
        try:
            response = requests.get("http://localhost:8001/api/v1/security/statistics")
            if response.status_code == 200:
                stats = response.json()
                print(f"   Total alerts: {stats.get('total_alerts', 0)}")
                print(f"   By severity: {stats.get('by_severity', {})}")
                print(f"   By type: {stats.get('by_type', {})}")
        except:
            print("   Could not retrieve final statistics")
    
    print("\n🎉 Testing completed!")
    print("📱 Visit http://localhost:8001/docs for interactive API exploration")

if __name__ == "__main__":
    main()