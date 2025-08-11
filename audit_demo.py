# audit_demo.py - Demonstration script for the Enhanced Audit System

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import random
from typing import List, Dict

class AuditSystemDemo:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.audit_endpoint = f"{base_url}/api/v1/audit"
        
    async def run_demo(self):
        """Run comprehensive audit system demonstration"""
        print("🚀 Starting Audit System Demonstration")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            # 1. Test basic audit overview
            await self.test_audit_overview(session)
            
            # 2. Simulate authentication events
            await self.simulate_authentication_scenarios(session)
            
            # 3. Test bulk event processing
            await self.test_bulk_events(session)
            
            # 4. Test advanced querying
            await self.test_advanced_querying(session)
            
            # 5. Test risk analysis
            await self.test_risk_analysis(session)
            
            # 6. Test integration endpoints
            await self.test_identity_provider_integrations(session)
            
            # 7. Test suspicious activity detection
            await self.test_suspicious_activity_detection(session)
            
        print("\n✅ Audit System Demo Completed Successfully!")
    
    async def test_audit_overview(self, session):
        """Test audit system overview"""
        print("\n📊 Testing Audit Overview...")
        
        try:
            async with session.get(f"{self.audit_endpoint}/") as response:
                data = await response.json()
                print(f"✅ Audit System Status: {data['status']}")
                print(f"📈 Statistics: {data['statistics']}")
                print(f"🔧 Capabilities: {len(data['capabilities'])} features available")
        except Exception as e:
            print(f"❌ Error testing overview: {e}")
    
    async def simulate_authentication_scenarios(self, session):
        """Simulate various authentication scenarios"""
        print("\n🔐 Simulating Authentication Scenarios...")
        
        scenarios = [
            # Successful login from normal location
            {
                "event_type": "authentication",
                "user_id": "john.doe@company.com",
                "action": "login",
                "result": "success",
                "source_ip": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "auth_details": {
                    "auth_method": "password_mfa",
                    "mfa_method": "push_notification",
                    "identity_provider": "AzureAD"
                },
                "device_info": {
                    "device_type": "desktop",
                    "os": "Windows 10",
                    "browser": "Chrome",
                    "is_trusted": True,
                    "device_fingerprint": "dev_001_john_desktop"
                },
                "geographic_info": {
                    "country": "United States",
                    "region": "California",
                    "city": "San Francisco"
                },
                "application": "Office365"
            },
            
            # Failed login attempt with wrong password
            {
                "event_type": "authentication",
                "user_id": "jane.smith@company.com",
                "action": "login",
                "result": "failure",
                "source_ip": "203.0.113.45",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
                "auth_details": {
                    "auth_method": "password",
                    "identity_provider": "Okta",
                    "failure_reason": "Invalid credentials",
                    "error_code": "E0000004"
                },
                "device_info": {
                    "device_type": "mobile",
                    "os": "iOS 14.7.1",
                    "browser": "Safari",
                    "is_trusted": False,
                    "device_fingerprint": "dev_002_jane_iphone"
                },
                "geographic_info": {
                    "country": "United Kingdom",
                    "region": "England",
                    "city": "London"
                },
                "application": "VPN_Gateway"
            },
            
            # Suspicious login from new location at odd hours
            {
                "event_type": "authentication",
                "user_id": "admin@company.com",
                "action": "login",
                "result": "success",
                "source_ip": "185.220.101.182",  # Suspicious IP
                "timestamp": (datetime.utcnow() - timedelta(hours=22)).isoformat(),  # 2 AM
                "user_agent": "curl/7.68.0",  # Suspicious user agent
                "auth_details": {
                    "auth_method": "password",
                    "identity_provider": "ADFS",
                    "session_id": "sess_admin_suspicious"
                },
                "device_info": {
                    "device_type": "unknown",
                    "os": "Linux",
                    "is_trusted": False,
                    "device_fingerprint": "dev_003_admin_unknown"
                },
                "geographic_info": {
                    "country": "Russia",
                    "region": "Moscow",
                    "city": "Moscow"
                },
                "application": "AdminPanel",
                "severity": "warning"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            try:
                async with session.post(
                    f"{self.audit_endpoint}/events",
                    json=scenario
                ) as response:
                    result = await response.json()
                    risk_level = result.get('risk_level', 'unknown')
                    print(f"  ✅ Scenario {i}: {result['message']} (Risk: {risk_level})")
            except Exception as e:
                print(f"  ❌ Scenario {i} failed: {e}")
    
    async def test_bulk_events(self, session):
        """Test bulk event processing"""
        print("\n📦 Testing Bulk Event Processing...")
        
        # Generate multiple failed login attempts from the same IP
        bulk_events = []
        suspicious_ip = "198.51.100.42"
        
        for i in range(10):
            event = {
                "event_type": "authentication",
                "user_id": f"user{i:02d}@company.com",
                "action": "login",
                "result": "failure",
                "source_ip": suspicious_ip,
                "timestamp": (datetime.utcnow() - timedelta(minutes=i*2)).isoformat(),
                "auth_details": {
                    "auth_method": "password",
                    "identity_provider": "AzureAD",
                    "failure_reason": "Account locked due to too many failed attempts",
                    "error_code": "50053"
                },
                "device_info": {
                    "device_type": "desktop",
                    "os": "Windows 10",
                    "browser": "Firefox",
                    "is_trusted": False,
                    "device_fingerprint": f"dev_bulk_{i:02d}"
                },
                "application": "Office365",
                "severity": "warning"
            }
            bulk_events.append(event)
        
        bulk_payload = {
            "events": bulk_events,
            "source_system": "DemoSystem",
            "batch_id": f"demo_batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            async with session.post(
                f"{self.audit_endpoint}/events/bulk",
                json=bulk_payload
            ) as response:
                result = await response.json()
                print(f"✅ Bulk Events: {result['message']}")
                print(f"📊 High Risk Events: {result['high_risk_events']}")
        except Exception as e:
            print(f"❌ Bulk events test failed: {e}")
    
    async def test_advanced_querying(self, session):
        """Test advanced querying capabilities"""
        print("\n🔍 Testing Advanced Querying...")
        
        # Query for failed authentication events
        query = {
            "event_types": ["authentication"],
            "results": ["failure"],
            "limit": 50,
            "offset": 0
        }
        
        try:
            async with session.post(
                f"{self.audit_endpoint}/events/query",
                json=query
            ) as response:
                result = await response.json()
                print(f"✅ Query Results: Found {result['total_count']} failed auth events")
                print(f"📋 Returned: {result['returned_count']} events")
        except Exception as e:
            print(f"❌ Advanced query test failed: {e}")
        
        # Get audit summary
        try:
            async with session.get(f"{self.audit_endpoint}/summary") as response:
                summary = await response.json()
                print(f"📊 Audit Summary:")
                print(f"   Total Events: {summary['total_events']}")
                print(f"   Event Types: {list(summary['event_type_breakdown'].keys())}")
                print(f"   Risk Levels: {list(summary['risk_level_breakdown'].keys())}")
        except Exception as e:
            print(f"❌ Summary test failed: {e}")
    
    async def test_risk_analysis(self, session):
        """Test risk analysis functionality"""
        print("\n⚠️ Testing Risk Analysis...")
        
        # Check user risk profile
        user_id = "admin@company.com"
        try:
            async with session.get(f"{self.audit_endpoint}/risk-profiles/{user_id}") as response:
                if response.status == 200:
                    profile = await response.json()
                    print(f"✅ Risk Profile for {user_id}:")
                    print(f"   Average Risk Score: {profile['risk_profile']['average_risk_score']:.2f}")
                    print(f"   Failed Attempts (24h): {profile['risk_profile']['failed_login_count_24h']}")
                    print(f"   Known Locations: {len(profile['risk_profile']['locations'])}")
                    print(f"   Risk Indicators: {profile['risk_indicators']}")
                else:
                    print(f"⚠️ No risk profile found for {user_id}")
        except Exception as e:
            print(f"❌ Risk analysis test failed: {e}")
    
    async def test_identity_provider_integrations(self, session):
        """Test identity provider integration endpoints"""
        print("\n🔗 Testing Identity Provider Integrations...")
        
        # Test Azure AD integration
        azure_ad_event = {
            "userPrincipalName": "integration.test@company.com",
            "activityDisplayName": "Sign-in activity",
            "resultType": "50126",  # Invalid username or password
            "ipAddress": "203.0.113.100",
            "correlationId": "12345678-1234-1234-1234-123456789012",
            "failureReason": "Invalid username or password",
            "appDisplayName": "Office 365",
            "deviceDetail": {
                "browser": "Chrome 95.0.4638.69"
            }
        }
        
        try:
            async with session.post(
                f"{self.audit_endpoint}/integrations/azure-ad",
                json=azure_ad_event
            ) as response:
                result = await response.json()
                print(f"✅ Azure AD Integration: {result['message']}")
        except Exception as e:
            print(f"❌ Azure AD integration test failed: {e}")
        
        # Test Okta integration
        okta_event = {
            "eventType": "user.authentication.auth_via_mfa",
            "actor": {
                "alternateId": "integration.test@company.com"
            },
            "outcome": {
                "result": "FAILURE",
                "reason": "VERIFICATION_ERROR"
            },
            "client": {
                "ipAddress": "198.51.100.200",
                "userAgent": {
                    "rawUserAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                },
                "geographicalContext": {
                    "country": "Canada",
                    "state": "Ontario",
                    "city": "Toronto"
                }
            }
        }
        
        try:
            async with session.post(
                f"{self.audit_endpoint}/integrations/okta",
                json=okta_event
            ) as response:
                result = await response.json()
                print(f"✅ Okta Integration: {result['message']}")
        except Exception as e:
            print(f"❌ Okta integration test failed: {e}")
    
    async def test_suspicious_activity_detection(self, session):
        """Test suspicious activity detection"""
        print("\n🚨 Testing Suspicious Activity Detection...")
        
        try:
            async with session.get(f"{self.audit_endpoint}/suspicious-activity") as response:
                activity = await response.json()
                print(f"✅ Suspicious Activity Summary:")
                print(f"   High Risk Events (24h): {activity['summary']['high_risk_events_24h']}")
                print(f"   Suspicious IPs: {activity['summary']['suspicious_ips']}")
                print(f"   High Failure Users: {activity['summary']['high_failure_users']}")
                
                if activity['suspicious_ips']:
                    print(f"🔍 Top Suspicious IP: {activity['suspicious_ips'][0]['ip_address']} ({activity['suspicious_ips'][0]['failure_count']} failures)")
        except Exception as e:
            print(f"❌ Suspicious activity test failed: {e}")

# Usage example
async def main():
    """Main demo function"""
    demo = AuditSystemDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())

# =================== AUTHENTICATION FAILURE INTEGRATION EXAMPLES ===================

class AuthFailureLogger:
    """Example class showing how to integrate with external auth systems"""
    
    def __init__(self, audit_endpoint: str):
        self.audit_endpoint = audit_endpoint
    
    async def log_azure_ad_failure(self, signin_log: Dict):
        """Log Azure AD authentication failure"""
        event = {
            "event_type": "authentication",
            "user_id": signin_log.get("userPrincipalName"),
            "action": "azure_ad_signin",
            "result": "failure",
            "source_ip": signin_log.get("ipAddress"),
            "auth_details": {
                "identity_provider": "AzureAD",
                "error_code": signin_log.get("status", {}).get("errorCode"),
                "failure_reason": signin_log.get("status", {}).get("failureReason"),
                "correlation_id": signin_log.get("correlationId")
            },
            "device_info": {
                "os": signin_log.get("deviceDetail", {}).get("operatingSystem"),
                "browser": signin_log.get("deviceDetail", {}).get("browser"),
                "is_trusted": signin_log.get("deviceDetail", {}).get("isCompliant", False)
            },
            "application": signin_log.get("resourceDisplayName"),
            "timestamp": signin_log.get("createdDateTime")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.audit_endpoint}/events", json=event) as response:
                return await response.json()
    
    async def log_okta_mfa_failure(self, okta_log: Dict):
        """Log Okta MFA authentication failure"""
        event = {
            "event_type": "authentication",
            "user_id": okta_log.get("actor", {}).get("alternateId"),
            "action": "okta_mfa_verification",
            "result": "failure",
            "source_ip": okta_log.get("client", {}).get("ipAddress"),
            "auth_details": {
                "identity_provider": "Okta",
                "mfa_method": okta_log.get("authenticationContext", {}).get("credentialType"),
                "failure_reason": okta_log.get("outcome", {}).get("reason")
            },
            "geographic_info": {
                "country": okta_log.get("client", {}).get("geographicalContext", {}).get("country"),
                "city": okta_log.get("client", {}).get("geographicalContext", {}).get("city")
            },
            "timestamp": okta_log.get("published")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.audit_endpoint}/events", json=event) as response:
                return await response.json()
    
    async def log_adfs_failure(self, adfs_event: Dict):
        """Log ADFS authentication failure"""
        event = {
            "event_type": "authentication",
            "user_id": adfs_event.get("username"),
            "action": "adfs_authentication",
            "result": "failure",
            "source_ip": adfs_event.get("client_ip"),
            "user_agent": adfs_event.get("user_agent"),
            "auth_details": {
                "identity_provider": "ADFS",
                "failure_reason": adfs_event.get("failure_reason"),
                "error_code": adfs_event.get("error_code")
            },
            "application": adfs_event.get("relying_party"),
            "timestamp": adfs_event.get("timestamp")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.audit_endpoint}/events", json=event) as response:
                return await response.json()

# =================== DYNAMIC RULE INTEGRATION EXAMPLE ===================

class DynamicRuleProcessor:
    """Example class showing dynamic rule processing integration"""
    
    def __init__(self, audit_endpoint: str):
        self.audit_endpoint = audit_endpoint
        
    async def evaluate_authentication_request(self, auth_request: Dict) -> Dict:
        """Evaluate authentication request using audit data"""
        user_id = auth_request.get("user_id")
        source_ip = auth_request.get("source_ip")
        
        # Get user risk profile
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.audit_endpoint}/risk-profiles/{user_id}") as response:
                    if response.status == 200:
                        risk_profile = await response.json()
                        
                        # Apply dynamic rules based on risk profile
                        decision = self._apply_dynamic_rules(auth_request, risk_profile)
                        
                        # Log the decision as an audit event
                        await self._log_rule_decision(session, auth_request, decision)
                        
                        return decision
                    else:
                        # No risk profile - new user, apply default rules
                        return self._apply_default_rules(auth_request)
            except Exception as e:
                print(f"Error evaluating auth request: {e}")
                return {"decision": "allow", "reason": "fallback_policy"}
    
    def _apply_dynamic_rules(self, auth_request: Dict, risk_profile: Dict) -> Dict:
        """Apply dynamic rules based on user risk profile"""
        profile_data = risk_profile.get("risk_profile", {})
        risk_indicators = risk_profile.get("risk_indicators", {})
        
        # High failure rate - require step-up MFA
        if risk_indicators.get("high_failure_rate", False):
            return {
                "decision": "step_up_mfa",
                "reason": "high_failure_rate_detected",
                "required_mfa": "push_notification",
                "risk_score": 75
            }
        
        # Multiple locations - additional verification
        if risk_indicators.get("multiple_locations", False):
            return {
                "decision": "additional_verification",
                "reason": "multiple_geographic_locations",
                "verification_method": "email_verification",
                "risk_score": 60
            }
        
        # Elevated average risk - enhanced monitoring
        if risk_indicators.get("elevated_avg_risk", False):
            return {
                "decision": "allow_with_monitoring",
                "reason": "elevated_average_risk_score",
                "monitoring_duration": "24_hours",
                "risk_score": 55
            }
        
        # Normal risk - allow
        return {
            "decision": "allow",
            "reason": "normal_risk_profile",
            "risk_score": 25
        }
    
    def _apply_default_rules(self, auth_request: Dict) -> Dict:
        """Apply default rules for new users"""
        # Check if request is from suspicious IP or during odd hours
        current_hour = datetime.utcnow().hour
        
        if current_hour < 6 or current_hour > 22:
            return {
                "decision": "step_up_mfa",
                "reason": "outside_business_hours",
                "required_mfa": "totp",
                "risk_score": 40
            }
        
        return {
            "decision": "allow",
            "reason": "default_policy",
            "risk_score": 30
        }
    
    async def _log_rule_decision(self, session, auth_request: Dict, decision: Dict):
        """Log the rule decision as an audit event"""
        event = {
            "event_type": "system_event",
            "user_id": auth_request.get("user_id"),
            "action": "dynamic_rule_evaluation",
            "result": "success",
            "source_ip": auth_request.get("source_ip"),
            "description": f"Dynamic rule decision: {decision['decision']}",
            "raw_data": {
                "auth_request": auth_request,
                "rule_decision": decision
            },
            "tags": ["dynamic_rules", "authentication_policy"]
        }
        
        await session.post(f"{self.audit_endpoint}/events", json=event)

# Example usage
async def demo_integration():
    """Demonstrate integration with external systems"""
    print("\n🔗 Authentication Integration Demo")
    
    # Initialize loggers
    failure_logger = AuthFailureLogger("http://localhost:8001/api/v1/audit")
    rule_processor = DynamicRuleProcessor("http://localhost:8001/api/v1/audit")
    
    # Simulate Azure AD failure
    azure_signin = {
        "userPrincipalName": "test.user@company.com",
        "ipAddress": "203.0.113.50",
        "status": {
            "errorCode": 50126,
            "failureReason": "Invalid username or password"
        },
        "correlationId": "abc-123-def-456",
        "deviceDetail": {
            "operatingSystem": "Windows 10",
            "browser": "Edge 96.0",
            "isCompliant": False
        },
        "resourceDisplayName": "Office 365",
        "createdDateTime": datetime.utcnow().isoformat()
    }
    
    result = await failure_logger.log_azure_ad_failure(azure_signin)
    print(f"Azure AD failure logged: {result['event_id']}")
    
    # Simulate dynamic rule evaluation
    auth_request = {
        "user_id": "test.user@company.com",
        "source_ip": "203.0.113.50",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    decision = await rule_processor.evaluate_authentication_request(auth_request)
    print(f"Rule decision: {decision['decision']} (Risk: {decision['risk_score']})")

if __name__ == "__main__":
    # Run both demos
    asyncio.run(main())
    print("\n" + "="*60)
    asyncio.run(demo_integration())