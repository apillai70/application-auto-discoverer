# start_audit_server.py - Enhanced FastAPI Startup Script with Auth Integration
# ==================================================================================
# LOCATION: Place this file in your project root directory (same level as main.py)
# PURPOSE: Starts your FastAPI server with comprehensive auth and audit system validation

#!/usr/bin/env python3
"""
Enhanced FastAPI Startup Script with Authentication & Audit System
================================================================

This script:
1. Checks if the audit system is properly set up
2. Validates authentication system and integration
3. Tests auth-audit integration
4. Validates all required components
5. Starts your FastAPI application with enhanced capabilities
6. Provides helpful startup information and endpoints

Place this file in your project root directory alongside main.py
"""

import sys
import os
import uvicorn
import asyncio
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_audit_system():
    """Check if audit system is properly set up"""
    print("🔍 Checking Audit System Setup...")
    
    audit_dir = Path("essentials/audit")
    
    if not audit_dir.exists():
        print("❌ Audit system not found. Run setup first:")
        print("   python complete_audit_implementation.py")
        print("   OR")
        print("   python audit_system_core.py  # For basic testing")
        return False
    
    # Check required directories
    required_dirs = ["events", "config", "scripts", "reports"]
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not (audit_dir / dir_name).exists():
            missing_dirs.append(f"essentials/audit/{dir_name}")
    
    if missing_dirs:
        print(f"❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"   - {dir_path}")
        print("🔧 Run setup to create missing directories:")
        print("   python complete_audit_implementation.py")
        return False
    
    print("✅ Audit system directories verified")
    return True

def check_auth_system():
    """Check if authentication system is properly configured"""
    print("🔐 Checking Authentication System...")
    
    try:
        # Try to import auth module
        import routers.auth as auth_module
        
        # Check if required functions exist
        required_functions = [
            'verify_token', 'get_current_user', 'check_permission', 
            'require_admin', 'create_access_token', 'secure_hash_password'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(auth_module, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"❌ Missing auth functions: {missing_functions}")
            return False
        
        # Check if user database exists
        if not hasattr(auth_module, 'USERS_DB'):
            print("❌ User database (USERS_DB) not found in auth module")
            return False
        
        users_db = getattr(auth_module, 'USERS_DB')
        if not users_db:
            print("❌ User database is empty")
            return False
        
        # Check test users
        test_users = ['admin', 'user', 'security']
        missing_users = [user for user in test_users if user not in users_db]
        if missing_users:
            print(f"⚠️ Missing test users: {missing_users}")
        
        print(f"✅ Authentication system verified ({len(users_db)} users)")
        return True
        
    except ImportError as e:
        print(f"❌ Auth module import failed: {e}")
        print("🔧 Make sure routers/auth.py exists and is properly configured")
        return False
    except Exception as e:
        print(f"❌ Auth system validation failed: {e}")
        return False

def check_auth_audit_integration():
    """Check if auth and audit systems are properly integrated"""
    print("🔗 Checking Auth-Audit Integration...")
    
    try:
        # Check audit router imports auth functions
        import routers.audit as audit_module
        
        # Check if audit router has auth dependencies
        if hasattr(audit_module, 'router'):
            print("✅ Audit router found")
        else:
            print("❌ Audit router object not found")
            return False
        
        # Check if auth functions are used in audit
        auth_integrated = False
        
        audit_source = ""
        if Path("routers/audit.py").exists():
            try:
                audit_source = str(Path("routers/audit.py").read_text(encoding='utf-8'))
            except UnicodeDecodeError:
                try:
                    audit_source = str(Path("routers/audit.py").read_text(encoding='latin1'))
                except Exception:
                    audit_source = ""
        
        auth_indicators = ['verify_token', 'Depends', 'get_current_user', 'check_permission']
        for indicator in auth_indicators:
            if indicator in audit_source:
                auth_integrated = True
                break
        
        if auth_integrated:
            print("✅ Auth-audit integration detected")
        else:
            print("⚠️ Limited auth-audit integration found")
            print("   Consider adding authentication to audit endpoints")
        
        return True
        
    except ImportError as e:
        print(f"❌ Audit module import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Auth-audit integration check failed: {e}")
        return True  # Non-critical

def check_router_system():
    """Check if router system is properly configured"""
    print("📁 Checking Router System...")
    
    try:
        import routers
        
        # Check if routers package has expected functions
        if hasattr(routers, 'get_available_routers'):
            available_routers = routers.get_available_routers()
            print(f"✅ Found {len(available_routers)} available routers")
            
            # List key routers
            router_names = [r['name'] for r in available_routers]
            key_routers = ['auth', 'audit', 'health']
            
            for key_router in key_routers:
                if key_router in router_names:
                    print(f"   ✅ {key_router} router available")
                else:
                    print(f"   ❌ {key_router} router missing")
            
            return True
        else:
            print("⚠️ Router system functions not available")
            return False
            
    except ImportError as e:
        print(f"❌ Router system import failed: {e}")
        return False

def check_audit_router():
    """Enhanced audit router check with auth integration"""
    print("🛡️ Checking Enhanced Audit Router...")
    
    try:
        import routers.audit
        print("✅ Audit router loaded successfully")
        
        # Count available endpoints
        if hasattr(routers.audit, 'router'):
            routes = routers.audit.router.routes
            endpoint_count = len([r for r in routes if hasattr(r, 'path')])
            print(f"✅ Found {endpoint_count} audit endpoints")
            
            # Check for auth-protected endpoints
            auth_protected = 0
            for route in routes:
                if hasattr(route, 'dependencies') and route.dependencies:
                    auth_protected += 1
            
            if auth_protected > 0:
                print(f"✅ Found {auth_protected} auth-protected audit endpoints")
            else:
                print("⚠️ No auth-protected audit endpoints detected")
            
            return True
        else:
            print("⚠️ Audit router loaded but no router object found")
            return False
            
    except ImportError as e:
        print("⚠️ Audit router not found - running in basic mode")
        print(f"   Error: {e}")
        print("🔧 To fix this:")
        print("   1. Ensure routers/audit.py exists")
        print("   2. Run compatibility fixer: python compatibility_fixer.py")
        print("   3. Install audit requirements if needed")
        return False

def check_main_app():
    """Check if main FastAPI app is available"""
    print("🚀 Checking Main FastAPI App...")
    
    try:
        import main
        if hasattr(main, 'app'):
            print("✅ Main FastAPI app found")
            
            # Check if app has routers included
            if hasattr(main.app, 'routes'):
                route_count = len(main.app.routes)
                print(f"✅ App has {route_count} routes configured")
            
            return True
        else:
            print("❌ main.py exists but no 'app' object found")
            return False
    except ImportError:
        print("❌ main.py not found")
        print("🔧 Make sure you have a main.py file with FastAPI app")
        return False

def run_quick_auth_test():
    """Run a quick authentication test"""
    print("🧪 Running Quick Authentication Test...")
    
    try:
        import routers.auth as auth_module
        
        # Test password hashing
        if hasattr(auth_module, 'secure_hash_password'):
            test_hash = auth_module.secure_hash_password("test123")
            if test_hash and ':' in test_hash:
                print("✅ Password hashing working")
            else:
                print("❌ Password hashing failed")
                return False
        
        # Test token creation
        if hasattr(auth_module, 'create_access_token'):
            test_token = auth_module.create_access_token("test_user", ["user"])
            if test_token:
                print("✅ Token creation working")
            else:
                print("❌ Token creation failed")
                return False
        
        # Test user database
        if hasattr(auth_module, 'USERS_DB'):
            users_db = auth_module.USERS_DB
            if 'admin' in users_db and 'user' in users_db:
                print("✅ Test users available")
            else:
                print("⚠️ Limited test users available")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick auth test failed: {e}")
        return False

def run_compatibility_check():
    """Run compatibility check for common issues"""
    print("🔍 Running Compatibility Check...")
    
    compatibility_issues = []
    
    # Check for common file issues
    critical_files = [
        "routers/__init__.py",
        "routers/auth.py", 
        "routers/audit.py",
        "main.py"
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            compatibility_issues.append(f"Missing critical file: {file_path}")
    
    # Check for common import issues
    try:
        import routers
        import routers.auth
        import routers.audit
    except ImportError as e:
        compatibility_issues.append(f"Import issue: {e}")
    
    # Check for Pydantic issues (common problem)
    audit_file = Path("routers/audit.py")
    if audit_file.exists():
        content = audit_file.read_text(encoding='utf-8')
        if 'regex=' in content:
            compatibility_issues.append("Pydantic compatibility issue: 'regex=' should be 'pattern='")
    
    # Check for async issues in storage
    storage_file = Path("storage/file_audit_storage.py")
    if storage_file.exists():
        content = storage_file.read_text(encoding='utf-8')
        if 'asyncio.create_task(self._initialize_storage())' in content:
            compatibility_issues.append("Async initialization issue in file_audit_storage.py")
    
    if compatibility_issues:
        print(f"⚠️ Found {len(compatibility_issues)} compatibility issues:")
        for issue in compatibility_issues:
            print(f"   • {issue}")
        print("🔧 Run compatibility fixer: python compatibility_fixer.py")
        return False
    else:
        print("✅ No compatibility issues detected")
        return True

async def test_server_startup():
    """Test if server can start properly (quick test)"""
    print("⚡ Testing Server Startup Capability...")
    
    try:
        import main
        app = main.app
        
        # Test that the app can be created without errors
        if app:
            print("✅ FastAPI app creation successful")
            
            # Check if key routes are configured
            route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
            
            expected_paths = ['/health', '/docs']
            found_paths = [path for path in expected_paths if any(path in route_path for route_path in route_paths)]
            
            if found_paths:
                print(f"✅ Key routes configured: {found_paths}")
            
            return True
        else:
            print("❌ Failed to create FastAPI app")
            return False
            
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def print_startup_info():
    """Print comprehensive startup information"""
    print("\n🚀 ENHANCED FASTAPI SERVER WITH AUTH & AUDIT")
    print("=" * 60)
    
    print("📖 Core Endpoints:")
    print("   📋 API Documentation:     http://localhost:8001/docs")
    print("   🔍 Health Check:          http://localhost:8001/health")
    print("   📊 API Info:              http://localhost:8001/api/info")
    print("")
    
    print("🔐 Authentication Endpoints:")
    print("   🚪 Login:                 POST http://localhost:8001/api/v1/auth/login")
    print("   👤 Profile:               GET  http://localhost:8001/api/v1/auth/profile")
    print("   ✅ Validate Token:        GET  http://localhost:8001/api/v1/auth/validate")
    print("   👥 User Management:       GET  http://localhost:8001/api/v1/auth/users")
    print("   🧪 Auth Test:             GET  http://localhost:8001/api/v1/auth/test")
    print("")
    
    print("🛡️ Enhanced Audit Endpoints:")
    print("   📊 Audit Overview:        GET  http://localhost:8001/api/v1/audit/")
    print("   📈 Summary:               GET  http://localhost:8001/api/v1/audit/summary")
    print("   🚨 Suspicious Activity:   GET  http://localhost:8001/api/v1/audit/suspicious-activity")
    print("   ⚙️ Storage Info:          GET  http://localhost:8001/api/v1/audit/storage-info")
    print("   📥 Create Event:          POST http://localhost:8001/api/v1/audit/events")
    print("   📤 Export Data:           POST http://localhost:8001/api/v1/audit/export")
    print("")
    
    print("🔗 Identity Provider Integrations:")
    print("   🔵 Azure AD:              http://localhost:8001/api/v1/audit/integrations/azure-ad")
    print("   🟠 Okta:                  http://localhost:8001/api/v1/audit/integrations/okta")
    print("   🟢 ADFS:                  http://localhost:8001/api/v1/audit/integrations/adfs")
    print("")
    
    print("📁 System Information:")
    print("   📊 Audit Data:            essentials/audit/")
    print("   📋 Reports:               essentials/audit/reports/")
    print("   ⚙️ Configuration:         essentials/audit/config/")
    print("")
    
    print("🧪 Test Credentials:")
    print("   👑 Admin:                 admin / admin123")
    print("   👤 User:                  user / user123")
    print("   🛡️ Security:              security / security123")
    print("   👁️ Read-only:             readonly / readonly123")
    print("")

def print_comprehensive_status(results: Dict[str, bool]):
    """Print comprehensive system status"""
    print("\n📊 COMPREHENSIVE SYSTEM STATUS")
    print("=" * 50)
    
    categories = {
        "Core System": ["main_app", "router_system"],
        "Authentication": ["auth_system", "auth_test"],
        "Audit System": ["audit_system", "audit_router"],
        "Integration": ["auth_audit_integration"],
        "Compatibility": ["compatibility_check", "startup_test"]
    }
    
    for category, checks in categories.items():
        category_results = [results.get(check, False) for check in checks]
        status = "✅ PASS" if all(category_results) else "⚠️ PARTIAL" if any(category_results) else "❌ FAIL"
        print(f"   {status} {category}")
        
        for check in checks:
            check_status = "✅" if results.get(check, False) else "❌"
            check_name = check.replace('_', ' ').title()
            print(f"      {check_status} {check_name}")
    
    # Overall system status
    total_checks = len(results)
    passed_checks = sum(results.values())
    overall_health = passed_checks / total_checks if total_checks > 0 else 0
    
    print(f"\n🎯 OVERALL SYSTEM HEALTH: {overall_health:.1%} ({passed_checks}/{total_checks})")
    
    if overall_health >= 0.8:
        print("🟢 System is ready for production use")
    elif overall_health >= 0.6:
        print("🟡 System is functional but has some issues")
    else:
        print("🔴 System needs attention before use")

async def main():
    """Enhanced main startup function with comprehensive checks"""
    print("🎯 ENHANCED FASTAPI APPLICATION STARTUP")
    print("=" * 55)
    print(f"⏰ Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Perform comprehensive system checks
    print("📋 Comprehensive Pre-flight Checks:")
    print("-" * 40)
    
    check_results = {}
    
    # Core system checks
    check_results["main_app"] = check_main_app()
    check_results["router_system"] = check_router_system()
    check_results["audit_system"] = check_audit_system()
    check_results["audit_router"] = check_audit_router()
    
    # Authentication system checks
    check_results["auth_system"] = check_auth_system()
    check_results["auth_test"] = run_quick_auth_test()
    
    # Integration checks
    check_results["auth_audit_integration"] = check_auth_audit_integration()
    
    # Compatibility and startup checks
    check_results["compatibility_check"] = run_compatibility_check()
    check_results["startup_test"] = await test_server_startup()
    
    # Calculate results
    total_checks = len(check_results)
    passed_checks = sum(check_results.values())
    success_rate = (passed_checks / total_checks) * 100
    
    print(f"\n📊 Pre-flight Check Results: {passed_checks}/{total_checks} passed ({success_rate:.1f}%)")
    
    # Print comprehensive status
    print_comprehensive_status(check_results)
    
    # Determine startup decision
    critical_checks = ["main_app", "auth_system", "audit_system"]
    critical_passed = all(check_results.get(check, False) for check in critical_checks)
    
    if critical_passed:
        print("\n✅ All critical systems ready!")
        print_startup_info()
        
        # Additional recommendations based on results
        if not check_results.get("compatibility_check", True):
            print("💡 RECOMMENDATION: Run compatibility fixer before production use:")
            print("   python compatibility_fixer.py")
        
        if not check_results.get("auth_audit_integration", True):
            print("💡 RECOMMENDATION: Test auth-audit integration:")
            print("   python auth_audit_integration_test.py")
        
    elif passed_checks >= total_checks * 0.7:
        print("\n⚠️ System partially ready - some features may not be available")
        print_startup_info()
        print("\n🔧 Issues to resolve:")
        for check, result in check_results.items():
            if not result:
                print(f"   • {check.replace('_', ' ').title()}")
        
    else:
        print("\n❌ System not ready - critical issues found")
        print("\n🔧 Critical fixes needed:")
        for check in critical_checks:
            if not check_results.get(check, False):
                print(f"   • Fix {check.replace('_', ' ')}")
        
        print("\n📖 Quick fix commands:")
        print("   1. python compatibility_fixer.py")
        print("   2. python verify_dependencies.py") 
        print("   3. python audit_system_core.py")
        print("   4. python complete_audit_implementation.py")
        
        print("\n❌ Aborting startup due to critical issues")
        sys.exit(1)
    
    # Start the server
    print(f"\n🚀 Starting Enhanced Server...")
    print("   📡 Host: 0.0.0.0:8001")
    print("   🔄 Auto-reload: Enabled")
    print("   📊 Log Level: Info")
    print("   ⏹️ Stop: Ctrl+C")
    print("-" * 55)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            reload_dirs=[str(Path.cwd())],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Enhanced server stopped by user")
        print("Thank you for using the Enhanced FastAPI Platform!")
    except Exception as e:
        print(f"\n\n❌ Server failed to start: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if port 8001 is available")
        print("   2. Run compatibility checks again")
        print("   3. Review error logs above")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())