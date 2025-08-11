# start_audit_server.py - Enhanced FastAPI Startup Script
# ====================================================
# LOCATION: Place this file in your project root directory (same level as main.py)
# PURPOSE: Starts your FastAPI server with audit system validation

#!/usr/bin/env python3
"""
Enhanced FastAPI Startup Script with Audit System
================================================

This script:
1. Checks if the audit system is properly set up
2. Validates all required components
3. Starts your FastAPI application with enhanced audit capabilities
4. Provides helpful startup information and endpoints

Place this file in your project root directory alongside main.py
"""

import sys
import os
import uvicorn
from pathlib import Path

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

def check_audit_router():
    """Check if audit router is available"""
    try:
        import routers.audit
        print("✅ Audit router loaded successfully")
        
        # Count available endpoints
        if hasattr(routers.audit, 'router'):
            routes = routers.audit.router.routes
            endpoint_count = len([r for r in routes if hasattr(r, 'path')])
            print(f"✅ Found {endpoint_count} audit endpoints")
            return True
        else:
            print("⚠️ Audit router loaded but no router object found")
            return False
            
    except ImportError as e:
        print("⚠️ Audit router not found - running in basic mode")
        print(f"   Error: {e}")
        print("🔧 To fix this:")
        print("   1. Copy enhanced audit router to routers/audit.py")
        print("   2. Create storage/file_audit_storage.py")
        print("   3. Install audit requirements: pip install -r requirements_audit.txt")
        return False

def check_main_app():
    """Check if main FastAPI app is available"""
    try:
        import main
        if hasattr(main, 'app'):
            print("✅ Main FastAPI app found")
            return True
        else:
            print("❌ main.py exists but no 'app' object found")
            return False
    except ImportError:
        print("❌ main.py not found")
        print("🔧 Make sure you have a main.py file with FastAPI app")
        return False

def print_startup_info():
    """Print helpful startup information"""
    print("\n🚀 ENHANCED FASTAPI SERVER STARTING")
    print("=" * 50)
    print("📖 Available Endpoints:")
    print("   📋 API Documentation:     http://localhost:8001/docs")
    print("   🔍 Health Check:          http://localhost:8001/health")
    print("   🛡️ Audit System:          http://localhost:8001/api/v1/audit/")
    print("   📊 Audit Summary:         http://localhost:8001/api/v1/audit/summary")
    print("   🚨 Suspicious Activity:   http://localhost:8001/api/v1/audit/suspicious-activity")
    print("   ⚙️ Storage Info:          http://localhost:8001/api/v1/audit/storage-info")
    print("")
    print("🔗 Identity Provider Integrations:")
    print("   🔵 Azure AD:              http://localhost:8001/api/v1/audit/integrations/azure-ad")
    print("   🟠 Okta:                  http://localhost:8001/api/v1/audit/integrations/okta")
    print("   🟢 ADFS:                  http://localhost:8001/api/v1/audit/integrations/adfs")
    print("")
    print("📁 Audit Data Location:     essentials/audit/")
    print("📊 Reports Location:        essentials/audit/reports/")
    print("⚙️ Configuration:           essentials/audit/config/")
    print("")

def main():
    """Main startup function"""
    print("🎯 FASTAPI APPLICATION WITH ENHANCED AUDIT SYSTEM")
    print("=" * 55)
    
    # Perform system checks
    checks_passed = 0
    total_checks = 3
    
    print("\n📋 Pre-flight Checks:")
    print("-" * 20)
    
    if check_main_app():
        checks_passed += 1
    
    if check_audit_system():
        checks_passed += 1
    
    if check_audit_router():
        checks_passed += 1
    
    print(f"\n📊 System Check Results: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("✅ All systems ready!")
        print_startup_info()
    elif checks_passed >= 1:
        print("⚠️ Partial system ready - some features may not be available")
        print_startup_info()
    else:
        print("❌ System not ready - please fix errors before starting")
        print("\n🔧 Quick fixes:")
        print("   1. Run: python verify_dependencies.py")
        print("   2. Run: python audit_system_core.py")
        print("   3. Run: python complete_audit_implementation.py")
        sys.exit(1)
    
    # Start the server
    print("🚀 Starting server...")
    print("   Press Ctrl+C to stop")
    print("   Server will auto-reload on file changes")
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
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()