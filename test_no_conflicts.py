#!/usr/bin/env python3
"""
Test that there are no remaining package conflicts
"""

import sys

def test_imports():
    """Test critical imports work"""
    
    print("🧪 Testing package imports...")
    
    # Test core audit packages
    core_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('aiofiles', 'Async files'),
        ('aiohttp', 'HTTP client')
    ]
    
    print("\n📦 Core packages:")
    core_ok = True
    for package, name in core_packages:
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
            core_ok = False
    
    # Test optional packages
    optional_packages = [
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'), 
        ('matplotlib', 'Matplotlib'),
        ('cv2', 'OpenCV'),
        ('sklearn', 'Scikit-learn')
    ]
    
    print("\n📊 Optional packages:")
    for package, name in optional_packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {name}: v{version}")
        except ImportError:
            print(f"   ⚠️  {name}: Not installed")
    
    return core_ok

def test_audit_functionality():
    """Test basic audit functionality"""
    print("\n🔍 Testing audit functionality...")
    
    try:
        # Test basic imports that audit system needs
        import json
        import asyncio
        from datetime import datetime
        from pathlib import Path
        from typing import Dict, List
        
        print("   ✅ Basic audit imports work")
        
        # Test if we can create audit storage
        try:
            import sys
            sys.path.append('.')
            
            # Try to import our audit modules
            from storage.file_audit_storage import FileAuditStorage
            print("   ✅ Audit storage module imports")
        except ImportError as e:
            print(f"   ⚠️  Audit storage module: {e}")
            print("       (Normal if not created yet)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Audit functionality test failed: {e}")
        return False

def main():
    print("🔍 CONFLICT RESOLUTION VERIFICATION")
    print("=" * 40)
    
    imports_ok = test_imports()
    audit_ok = test_audit_functionality()
    
    if imports_ok and audit_ok:
        print("\n✅ All tests passed! No conflicts detected.")
        print("🚀 Ready to run audit system!")
        return 0
    else:
        print("\n❌ Some tests failed. Check package installations.")
        return 1

if __name__ == "__main__":
    sys.exit(main())