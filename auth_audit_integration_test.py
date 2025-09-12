#!/usr/bin/env python3
"""
Authentication & Audit System Integration Test
=============================================
Comprehensive test suite to verify auth and audit systems work together
"""

import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class AuthAuditIntegrationTester:
    """Test authentication and audit system integration"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
    
    def test_server_health(self) -> bool:
        """Test if server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Health Check", True, f"Server responding at {self.base_url}")
                return True
            else:
                self.log_test("Server Health Check", False, f"Server returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Server Health Check", False, f"Cannot connect: {e}")
            return False
    
    def test_auth_endpoints_available(self) -> bool:
        """Test if auth endpoints are available"""
        auth_endpoints = [
            "/api/v1/auth/test",
            "/api/v1/auth/login", 
            "/api/v1/auth/validate"
        ]
        
        all_available = True
        for endpoint in auth_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if endpoint == "/api/v1/auth/test":
                    # Test endpoint should return 200
                    if response.status_code == 200:
                        self.log_test(f"Auth Endpoint {endpoint}", True)
                    else:
                        self.log_test(f"Auth Endpoint {endpoint}", False, f"Status: {response.status_code}")
                        all_available = False
                else:
                    # Other endpoints might return 401/422 but should not return 404
                    if response.status_code != 404:
                        self.log_test(f"Auth Endpoint {endpoint}", True, f"Endpoint exists (status: {response.status_code})")
                    else:
                        self.log_test(f"Auth Endpoint {endpoint}", False, "Endpoint not found")
                        all_available = False
            except Exception as e:
                self.log_test(f"Auth Endpoint {endpoint}", False, f"Error: {e}")
                all_available = False
        
        return all_available
    
    def test_audit_endpoints_available(self) -> bool:
        """Test if audit endpoints are available"""
        audit_endpoints = [
            "/api/v1/audit/",
            "/api/v1/audit/summary",
            "/api/v1/audit/storage-info"
        ]
        
        all_available = True
        for endpoint in audit_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # Audit endpoints should either work or require auth (401/403), not 404
                if response.status_code not in [404, 500]:
                    self.log_test(f"Audit Endpoint {endpoint}", True, f"Endpoint exists (status: {response.status_code})")
                else:
                    self.log_test(f"Audit Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    all_available = False
            except Exception as e:
                self.log_test(f"Audit Endpoint {endpoint}", False, f"Error: {e}")
                all_available = False
        
        return all_available
    
    def test_user_login(self, username: str, password: str) -> Dict[str, Any]:
        """Test user login and return token info"""
        try:
            login_data = {"username": username, "password": password}
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.tokens[username] = token_data.get("access_token")
                
                self.log_test(
                    f"Login Test ({username})", 
                    True, 
                    f"Roles: {token_data.get('roles', [])}"
                )
                return token_data
            else:
                self.log_test(
                    f"Login Test ({username})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return {}
                
        except Exception as e:
            self.log_test(f"Login Test ({username})", False, f"Error: {e}")
            return {}
    
    def test_authenticated_audit_access(self, username: str) -> bool:
        """Test accessing audit endpoints with authentication"""
        if username not in self.tokens:
            self.log_test(f"Audit Access ({username})", False, "No token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        # Test different audit endpoints
        test_endpoints = [
            ("/api/v1/audit/summary", "Audit Summary"),
            ("/api/v1/audit/storage-info", "Storage Info"),
            ("/api/v1/audit/", "Audit Overview")
        ]
        
        success_count = 0
        for endpoint, name in test_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(f"Authenticated {name} ({username})", True)
                    success_count += 1
                else:
                    self.log_test(
                        f"Authenticated {name} ({username})", 
                        False, 
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_test(f"Authenticated {name} ({username})", False, f"Error: {e}")
        
        return success_count == len(test_endpoints)
    
    def test_audit_event_creation(self, username: str) -> bool:
        """Test creating audit events with authentication"""
        if username not in self.tokens:
            self.log_test(f"Audit Event Creation ({username})", False, "No token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        # Create a test audit event
        test_event = {
            "event_type": "authentication",
            "user_id": f"test_{username}@company.com",
            "action": "test_login",
            "result": "success",
            "source_ip": "192.168.1.100",
            "auth_details": {
                "identity_provider": "test_system",
                "method": "password"
            },
            "device_info": {
                "device_fingerprint": "test_device_001",
                "user_agent": "Test Agent 1.0"
            },
            "geographic_info": {
                "country": "United States",
                "region": "Test Region"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/audit/events",
                json=test_event,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                event_response = response.json()
                self.log_test(
                    f"Audit Event Creation ({username})", 
                    True, 
                    f"Event ID: {event_response.get('event_id', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    f"Audit Event Creation ({username})", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(f"Audit Event Creation ({username})", False, f"Error: {e}")
            return False
    
    def test_role_based_access(self) -> bool:
        """Test role-based access to audit features"""
        role_tests = []
        
        # Test admin access
        if "admin" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            
            # Test admin-only endpoints
            admin_endpoints = [
                "/api/v1/auth/users",
                "/api/v1/auth/sessions",
                "/api/v1/audit/storage-info"
            ]
            
            admin_success = True
            for endpoint in admin_endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code not in [200, 201]:
                        admin_success = False
                        break
                except:
                    admin_success = False
                    break
            
            role_tests.append(("Admin Access", admin_success))
        
        # Test regular user access
        if "user" in self.tokens:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # Regular users should be able to access basic audit info but not admin functions
            try:
                # Should work
                response1 = requests.get(
                    f"{self.base_url}/api/v1/audit/summary",
                    headers=headers,
                    timeout=10
                )
                
                # Should be forbidden (403)
                response2 = requests.get(
                    f"{self.base_url}/api/v1/auth/users",
                    headers=headers,
                    timeout=10
                )
                
                user_success = response1.status_code == 200 and response2.status_code == 403
                role_tests.append(("User Access Control", user_success))
                
            except Exception as e:
                role_tests.append(("User Access Control", False))
        
        # Log results
        all_passed = True
        for test_name, passed in role_tests:
            self.log_test(test_name, passed)
            if not passed:
                all_passed = False
        
        return all_passed
    
    def test_token_validation(self) -> bool:
        """Test token validation functionality"""
        if "admin" not in self.tokens:
            self.log_test("Token Validation", False, "No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/validate",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                validation_data = response.json()
                is_valid = validation_data.get("valid", False)
                username = validation_data.get("user")
                
                self.log_test(
                    "Token Validation", 
                    is_valid and username == "admin",
                    f"Valid: {is_valid}, User: {username}"
                )
                return is_valid and username == "admin"
            else:
                self.log_test("Token Validation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Token Validation", False, f"Error: {e}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that unauthorized access is properly blocked"""
        # Test accessing protected endpoints without token
        protected_endpoints = [
            "/api/v1/audit/events",
            "/api/v1/auth/users",
            "/api/v1/auth/sessions"
        ]
        
        unauthorized_tests = []
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # Should return 401 (unauthorized)
                unauthorized_tests.append(response.status_code == 401)
            except:
                unauthorized_tests.append(False)
        
        all_blocked = all(unauthorized_tests)
        self.log_test(
            "Unauthorized Access Protection", 
            all_blocked,
            f"Protected endpoints properly blocked: {all_blocked}"
        )
        
        return all_blocked
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive authentication and audit integration test"""
        print("🧪 AUTHENTICATION & AUDIT INTEGRATION TEST")
        print("=" * 50)
        
        # Test 1: Server connectivity
        if not self.test_server_health():
            return {"overall_result": "FAILED", "reason": "Server not accessible"}
        
        # Test 2: Check endpoint availability
        auth_available = self.test_auth_endpoints_available()
        audit_available = self.test_audit_endpoints_available()
        
        if not auth_available:
            return {"overall_result": "FAILED", "reason": "Auth endpoints not available"}
        if not audit_available:
            return {"overall_result": "FAILED", "reason": "Audit endpoints not available"}
        
        # Test 3: User authentication
        test_users = [
            ("admin", "admin123"),
            ("user", "user123"),
            ("security", "security123")
        ]
        
        login_success = True
        for username, password in test_users:
            token_data = self.test_user_login(username, password)
            if not token_data:
                login_success = False
        
        if not login_success:
            return {"overall_result": "FAILED", "reason": "User authentication failed"}
        
        # Test 4: Authenticated audit access
        audit_access_success = True
        for username, _ in test_users:
            if not self.test_authenticated_audit_access(username):
                audit_access_success = False
        
        # Test 5: Audit event creation
        event_creation_success = True
        for username, _ in test_users:
            if not self.test_audit_event_creation(username):
                event_creation_success = False
        
        # Test 6: Role-based access control
        rbac_success = self.test_role_based_access()
        
        # Test 7: Token validation
        token_validation_success = self.test_token_validation()
        
        # Test 8: Unauthorized access protection
        unauthorized_protection = self.test_unauthorized_access()
        
        # Calculate overall result
        all_tests = [
            auth_available,
            audit_available, 
            login_success,
            audit_access_success,
            event_creation_success,
            rbac_success,
            token_validation_success,
            unauthorized_protection
        ]
        
        passed_tests = sum(all_tests)
        total_tests = len(all_tests)
        
        overall_success = all(all_tests)
        
        result = {
            "overall_result": "PASSED" if overall_success else "FAILED",
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
            "test_details": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Overall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        print(f"   Tests Passed: {passed_tests}/{total_tests} ({result['success_rate']})")
        print(f"   Timestamp: {result['timestamp']}")
        
        if not overall_success:
            print(f"\n⚠️  Failed Tests:")
            for test_result in self.test_results:
                if not test_result["passed"]:
                    print(f"   - {test_result['test']}: {test_result['details']}")
        
        return result

async def main():
    """Main test function"""
    tester = AuthAuditIntegrationTester()
    result = await tester.run_comprehensive_test()
    
    # Save results to file
    results_file = Path("auth_audit_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if result["overall_result"] == "PASSED" else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)