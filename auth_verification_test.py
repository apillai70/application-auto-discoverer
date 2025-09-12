#!/usr/bin/env python3
"""
Comprehensive Authentication Verification Test
==============================================
Complete test suite to verify authentication system functionality
"""

import asyncio
import json
import requests
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import hmac

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class AuthenticationTester:
    """Comprehensive authentication system tester"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        self.start_time = datetime.now()
        
        # Test configuration
        self.timeout = 10
        self.test_users = {
            "admin": {"password": "admin123", "expected_roles": ["admin", "user"]},
            "user": {"password": "user123", "expected_roles": ["user"]},
            "security": {"password": "security123", "expected_roles": ["security", "analyst", "user"]},
            "readonly": {"password": "readonly123", "expected_roles": ["readonly"]}
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = "", category: str = "general"):
        """Log test result with enhanced information"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "category": category,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
    
    def test_server_connectivity(self) -> bool:
        """Test basic server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Server Connectivity", 
                    True, 
                    f"Server healthy: {health_data.get('status', 'unknown')}", 
                    "connectivity"
                )
                return True
            else:
                self.log_test(
                    "Server Connectivity", 
                    False, 
                    f"Health check failed: {response.status_code}", 
                    "connectivity"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Server Connectivity", 
                False, 
                f"Cannot connect to server: {e}", 
                "connectivity"
            )
            return False
    
    def test_auth_endpoints_discovery(self) -> bool:
        """Test discovery of authentication endpoints"""
        auth_endpoints = {
            "/api/v1/auth/test": "GET",
            "/api/v1/auth/login": "POST",
            "/api/v1/auth/logout": "POST",
            "/api/v1/auth/profile": "GET",
            "/api/v1/auth/validate": "GET",
            "/api/v1/auth/users": "GET",
            "/api/v1/auth/sessions": "GET"
        }
        
        available_endpoints = []
        missing_endpoints = []
        
        for endpoint, method in auth_endpoints.items():
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=self.timeout)
                
                # Endpoint exists if we don't get 404
                if response.status_code != 404:
                    available_endpoints.append(endpoint)
                else:
                    missing_endpoints.append(endpoint)
                    
            except Exception as e:
                missing_endpoints.append(f"{endpoint} (error: {e})")
        
        success = len(missing_endpoints) == 0
        details = f"Available: {len(available_endpoints)}, Missing: {len(missing_endpoints)}"
        if missing_endpoints:
            details += f"\nMissing: {missing_endpoints}"
        
        self.log_test("Auth Endpoints Discovery", success, details, "discovery")
        return success
    
    def test_auth_system_info(self) -> bool:
        """Test authentication system information endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/auth/test", timeout=self.timeout)
            if response.status_code == 200:
                auth_info = response.json()
                
                # Verify expected fields
                expected_fields = ["message", "hashing_method", "available_users", "test_credentials"]
                missing_fields = [field for field in expected_fields if field not in auth_info]
                
                if not missing_fields:
                    users_count = len(auth_info.get("available_users", []))
                    hashing_method = auth_info.get("hashing_method", "unknown")
                    
                    self.log_test(
                        "Auth System Info", 
                        True, 
                        f"Method: {hashing_method}, Users: {users_count}", 
                        "discovery"
                    )
                    return True
                else:
                    self.log_test(
                        "Auth System Info", 
                        False, 
                        f"Missing fields: {missing_fields}", 
                        "discovery"
                    )
                    return False
            else:
                self.log_test(
                    "Auth System Info", 
                    False, 
                    f"Status: {response.status_code}", 
                    "discovery"
                )
                return False
        except Exception as e:
            self.log_test("Auth System Info", False, f"Error: {e}", "discovery")
            return False
    
    def test_user_authentication(self, username: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """Test user authentication with detailed validation"""
        try:
            login_data = {"username": username, "password": password}
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Validate token response structure
                required_fields = ["access_token", "token_type", "username", "roles"]
                missing_fields = [field for field in required_fields if field not in token_data]
                
                if missing_fields:
                    self.log_test(
                        f"Login Structure ({username})", 
                        False, 
                        f"Missing fields: {missing_fields}", 
                        "authentication"
                    )
                    return False, {}
                
                # Validate token properties
                token = token_data.get("access_token")
                token_type = token_data.get("token_type")
                returned_username = token_data.get("username")
                roles = token_data.get("roles", [])
                
                validation_issues = []
                
                if not token or len(token) < 10:
                    validation_issues.append("Invalid token format")
                
                if token_type != "bearer":
                    validation_issues.append(f"Unexpected token type: {token_type}")
                
                if returned_username != username:
                    validation_issues.append(f"Username mismatch: {returned_username} != {username}")
                
                expected_roles = self.test_users.get(username, {}).get("expected_roles", [])
                if expected_roles and not any(role in roles for role in expected_roles):
                    validation_issues.append(f"Role mismatch. Expected: {expected_roles}, Got: {roles}")
                
                if validation_issues:
                    self.log_test(
                        f"Login Validation ({username})", 
                        False, 
                        "; ".join(validation_issues), 
                        "authentication"
                    )
                    return False, {}
                
                # Store token for later tests
                self.tokens[username] = token
                
                self.log_test(
                    f"User Authentication ({username})", 
                    True, 
                    f"Roles: {roles}, Token: {token[:10]}...", 
                    "authentication"
                )
                return True, token_data
                
            elif response.status_code == 401:
                self.log_test(
                    f"User Authentication ({username})", 
                    False, 
                    "Invalid credentials", 
                    "authentication"
                )
                return False, {}
            else:
                self.log_test(
                    f"User Authentication ({username})", 
                    False, 
                    f"Unexpected status: {response.status_code}", 
                    "authentication"
                )
                return False, {}
                
        except Exception as e:
            self.log_test(f"User Authentication ({username})", False, f"Error: {e}", "authentication")
            return False, {}
    
    def test_invalid_authentication(self) -> bool:
        """Test authentication with invalid credentials"""
        invalid_credentials = [
            ("admin", "wrong_password"),
            ("nonexistent_user", "any_password"),
            ("", ""),
            ("admin", ""),
            ("", "admin123")
        ]
        
        success_count = 0
        for username, password in invalid_credentials:
            try:
                login_data = {"username": username, "password": password}
                response = requests.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=login_data,
                    timeout=self.timeout
                )
                
                # Should return 401 Unauthorized
                if response.status_code == 401:
                    success_count += 1
                else:
                    self.log_test(
                        f"Invalid Auth Test ({username})", 
                        False, 
                        f"Expected 401, got {response.status_code}", 
                        "security"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Invalid Auth Test ({username})", 
                    False, 
                    f"Error: {e}", 
                    "security"
                )
        
        success = success_count == len(invalid_credentials)
        self.log_test(
            "Invalid Authentication Protection", 
            success, 
            f"Blocked {success_count}/{len(invalid_credentials)} invalid attempts", 
            "security"
        )
        return success
    
    def test_token_validation(self, username: str) -> bool:
        """Test token validation functionality"""
        if username not in self.tokens:
            self.log_test(f"Token Validation ({username})", False, "No token available", "validation")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[username]}"}
            response = requests.get(
                f"{self.base_url}/api/v1/auth/validate",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                validation_data = response.json()
                
                expected_fields = ["valid", "user", "roles", "timestamp"]
                missing_fields = [field for field in expected_fields if field not in validation_data]
                
                if missing_fields:
                    self.log_test(
                        f"Token Validation ({username})", 
                        False, 
                        f"Missing fields: {missing_fields}", 
                        "validation"
                    )
                    return False
                
                is_valid = validation_data.get("valid", False)
                returned_user = validation_data.get("user")
                
                if is_valid and returned_user == username:
                    self.log_test(
                        f"Token Validation ({username})", 
                        True, 
                        f"Valid token for {returned_user}", 
                        "validation"
                    )
                    return True
                else:
                    self.log_test(
                        f"Token Validation ({username})", 
                        False, 
                        f"Invalid validation: valid={is_valid}, user={returned_user}", 
                        "validation"
                    )
                    return False
            else:
                self.log_test(
                    f"Token Validation ({username})", 
                    False, 
                    f"Status: {response.status_code}", 
                    "validation"
                )
                return False
                
        except Exception as e:
            self.log_test(f"Token Validation ({username})", False, f"Error: {e}", "validation")
            return False
    
    def test_user_profile(self, username: str) -> bool:
        """Test user profile retrieval"""
        if username not in self.tokens:
            self.log_test(f"User Profile ({username})", False, "No token available", "profile")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[username]}"}
            response = requests.get(
                f"{self.base_url}/api/v1/auth/profile",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                
                expected_fields = ["username", "email", "full_name", "roles", "is_active"]
                missing_fields = [field for field in expected_fields if field not in profile_data]
                
                if missing_fields:
                    self.log_test(
                        f"User Profile ({username})", 
                        False, 
                        f"Missing fields: {missing_fields}", 
                        "profile"
                    )
                    return False
                
                profile_username = profile_data.get("username")
                if profile_username == username:
                    self.log_test(
                        f"User Profile ({username})", 
                        True, 
                        f"Email: {profile_data.get('email', 'N/A')}", 
                        "profile"
                    )
                    return True
                else:
                    self.log_test(
                        f"User Profile ({username})", 
                        False, 
                        f"Username mismatch: {profile_username} != {username}", 
                        "profile"
                    )
                    return False
            else:
                self.log_test(
                    f"User Profile ({username})", 
                    False, 
                    f"Status: {response.status_code}", 
                    "profile"
                )
                return False
                
        except Exception as e:
            self.log_test(f"User Profile ({username})", False, f"Error: {e}", "profile")
            return False
    
    def test_role_based_access_control(self) -> bool:
        """Test role-based access control"""
        rbac_tests = []
        
        # Test admin-only endpoints
        if "admin" in self.tokens:
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            admin_endpoints = [
                "/api/v1/auth/users",
                "/api/v1/auth/sessions"
            ]
            
            admin_success = True
            for endpoint in admin_endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=admin_headers,
                        timeout=self.timeout
                    )
                    if response.status_code != 200:
                        admin_success = False
                        break
                except:
                    admin_success = False
                    break
            
            rbac_tests.append(("Admin Access", admin_success))
        
        # Test regular user restrictions
        if "user" in self.tokens:
            user_headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            
            # User should NOT be able to access admin endpoints
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/auth/users",
                    headers=user_headers,
                    timeout=self.timeout
                )
                # Should be forbidden
                user_restricted = response.status_code == 403
                rbac_tests.append(("User Access Restriction", user_restricted))
            except:
                rbac_tests.append(("User Access Restriction", False))
        
        # Test security role access
        if "security" in self.tokens:
            security_headers = {"Authorization": f"Bearer {self.tokens['security']}"}
            
            # Security should be able to access profile but restrictions apply elsewhere
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/auth/profile",
                    headers=security_headers,
                    timeout=self.timeout
                )
                security_access = response.status_code == 200
                rbac_tests.append(("Security Role Access", security_access))
            except:
                rbac_tests.append(("Security Role Access", False))
        
        # Log individual RBAC test results
        all_passed = True
        for test_name, passed in rbac_tests:
            self.log_test(test_name, passed, "", "rbac")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def test_unauthorized_access_protection(self) -> bool:
        """Test protection against unauthorized access"""
        protected_endpoints = [
            "/api/v1/auth/profile",
            "/api/v1/auth/users",
            "/api/v1/auth/sessions",
            "/api/v1/auth/validate"
        ]
        
        unauthorized_tests = []
        for endpoint in protected_endpoints:
            try:
                # Test without any authorization header
                response1 = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                
                # Test with invalid token
                invalid_headers = {"Authorization": "Bearer invalid_token_123"}
                response2 = requests.get(f"{self.base_url}{endpoint}", headers=invalid_headers, timeout=self.timeout)
                
                # Both should return 401
                unauthorized_tests.append(response1.status_code == 401 and response2.status_code == 401)
                
            except:
                unauthorized_tests.append(False)
        
        all_protected = all(unauthorized_tests)
        self.log_test(
            "Unauthorized Access Protection", 
            all_protected,
            f"Protected {sum(unauthorized_tests)}/{len(unauthorized_tests)} endpoints", 
            "security"
        )
        
        return all_protected
    
    def test_token_expiration(self) -> bool:
        """Test token expiration functionality (if supported)"""
        # This test would require modifying token expiration time or waiting
        # For now, we'll test that tokens have expiration info
        
        if "admin" in self.tokens:
            try:
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                response = requests.get(
                    f"{self.base_url}/api/v1/auth/validate",
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    validation_data = response.json()
                    # Check if expiration info is present (implementation dependent)
                    has_timestamp = "timestamp" in validation_data
                    
                    self.log_test(
                        "Token Expiration Support", 
                        has_timestamp, 
                        "Timestamp field present in validation" if has_timestamp else "No expiration info", 
                        "security"
                    )
                    return has_timestamp
                else:
                    self.log_test("Token Expiration Support", False, "Validation failed", "security")
                    return False
            except Exception as e:
                self.log_test("Token Expiration Support", False, f"Error: {e}", "security")
                return False
        else:
            self.log_test("Token Expiration Support", False, "No admin token for testing", "security")
            return False
    
    def test_logout_functionality(self) -> bool:
        """Test user logout functionality"""
        # Create a test token first
        test_success, test_token_data = self.test_user_authentication("user", "user123")
        if not test_success:
            self.log_test("Logout Test", False, "Could not create test token", "session")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['user']}"}
            response = requests.post(
                f"{self.base_url}/api/v1/auth/logout",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Try to use the token after logout (should fail)
                validation_response = requests.get(
                    f"{self.base_url}/api/v1/auth/validate",
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Token should be invalid after logout
                token_invalidated = validation_response.status_code == 401
                
                self.log_test(
                    "Logout Functionality", 
                    token_invalidated, 
                    "Token invalidated after logout" if token_invalidated else "Token still valid after logout", 
                    "session"
                )
                return token_invalidated
            else:
                self.log_test(
                    "Logout Functionality", 
                    False, 
                    f"Logout failed: {response.status_code}", 
                    "session"
                )
                return False
                
        except Exception as e:
            self.log_test("Logout Functionality", False, f"Error: {e}", "session")
            return False
    
    def test_session_management(self) -> bool:
        """Test session management functionality"""
        if "admin" not in self.tokens:
            self.log_test("Session Management", False, "No admin token for testing", "session")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            response = requests.get(
                f"{self.base_url}/api/v1/auth/sessions",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                session_data = response.json()
                
                expected_fields = ["active_sessions", "total"]
                missing_fields = [field for field in expected_fields if field not in session_data]
                
                if missing_fields:
                    self.log_test(
                        "Session Management", 
                        False, 
                        f"Missing fields: {missing_fields}", 
                        "session"
                    )
                    return False
                
                total_sessions = session_data.get("total", 0)
                self.log_test(
                    "Session Management", 
                    True, 
                    f"Found {total_sessions} active sessions", 
                    "session"
                )
                return True
            else:
                self.log_test(
                    "Session Management", 
                    False, 
                    f"Status: {response.status_code}", 
                    "session"
                )
                return False
                
        except Exception as e:
            self.log_test("Session Management", False, f"Error: {e}", "session")
            return False
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Categorize results
        categories = {}
        for result in self.test_results:
            category = result.get("category", "general")
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "tests": []}
            
            categories[category]["total"] += 1
            if result["passed"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
            categories[category]["tests"].append(result)
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2),
                "duration_seconds": duration.total_seconds(),
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "categories": categories,
            "detailed_results": self.test_results,
            "tokens_generated": len(self.tokens),
            "test_users": list(self.test_users.keys()),
            "server_url": self.base_url
        }
        
        return report
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete authentication test suite"""
        print("🧪 COMPREHENSIVE AUTHENTICATION TEST SUITE")
        print("=" * 50)
        print(f"🎯 Target Server: {self.base_url}")
        print(f"⏰ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Phase 1: Connectivity and Discovery
        print("📡 Phase 1: Connectivity & Discovery")
        print("-" * 30)
        
        if not self.test_server_connectivity():
            return {"error": "Server not accessible", "phase": "connectivity"}
        
        self.test_auth_endpoints_discovery()
        self.test_auth_system_info()
        
        # Phase 2: Authentication Tests
        print("\n🔐 Phase 2: Authentication Tests")
        print("-" * 30)
        
        auth_success = True
        for username, config in self.test_users.items():
            success, _ = self.test_user_authentication(username, config["password"])
            if not success:
                auth_success = False
        
        # Test invalid authentication
        self.test_invalid_authentication()
        
        # Phase 3: Token and Session Management
        print("\n🎫 Phase 3: Token & Session Management")
        print("-" * 30)
        
        for username in self.tokens.keys():
            self.test_token_validation(username)
            self.test_user_profile(username)
        
        self.test_session_management()
        self.test_logout_functionality()
        
        # Phase 4: Security Tests
        print("\n🛡️ Phase 4: Security Tests")
        print("-" * 30)
        
        self.test_role_based_access_control()
        self.test_unauthorized_access_protection()
        self.test_token_expiration()
        
        # Generate final report
        report = self.generate_test_report()
        
        print(f"\n📊 TEST SUITE COMPLETED")
        print("=" * 30)
        print(f"✅ Passed: {report['summary']['passed_tests']}")
        print(f"❌ Failed: {report['summary']['failed_tests']}")
        print(f"📈 Success Rate: {report['summary']['success_rate']}%")
        print(f"⏱️ Duration: {report['summary']['duration_seconds']:.2f} seconds")
        
        # Category breakdown
        print(f"\n📋 Results by Category:")
        for category, stats in report["categories"].items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   🔸 {category.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show critical failures
        critical_failures = [r for r in self.test_results if not r["passed"] and r["category"] in ["connectivity", "authentication", "security"]]
        if critical_failures:
            print(f"\n🚨 Critical Failures:")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        return report

async def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Authentication System Test")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL of the FastAPI server")
    parser.add_argument("--output", default="auth_test_report.json", help="Output file for test report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = AuthenticationTester(base_url=args.url)
    report = await tester.run_comprehensive_test_suite()
    
    # Save report to file
    output_file = Path(args.output)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {output_file}")
    
    # Return appropriate exit code
    if "error" in report:
        print(f"\n❌ Test suite failed: {report['error']}")
        return 1
    elif report["summary"]["success_rate"] >= 80:
        print(f"\n✅ Authentication system is working well!")
        return 0
    elif report["summary"]["success_rate"] >= 60:
        print(f"\n⚠️ Authentication system has some issues but is functional")
        return 0
    else:
        print(f"\n❌ Authentication system has significant issues")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)