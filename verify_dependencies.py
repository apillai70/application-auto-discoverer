#!/usr/bin/env python3
"""
Verify all dependencies are properly installed
"""

import sys

def check_imports():
    """Check if all required packages can be imported"""
    
    required_packages = [
        ('fastapi', 'FastAPI core'),
        ('uvicorn', 'ASGI server'),
        ('pydantic', 'Data validation'),
        ('aiofiles', 'Async file operations'),
        ('aiohttp', 'HTTP client'),
        ('json', 'JSON processing (built-in)'),
        ('datetime', 'Date/time handling (built-in)'),
        ('pathlib', 'Path operations (built-in)')
    ]
    
    optional_packages = [
        ('pandas', 'Data analysis'),
        ('numpy', 'Numerical computing'),
        ('matplotlib', 'Plotting'),
        ('seaborn', 'Statistical visualization')
    ]
    
    print("🔍 DEPENDENCY VERIFICATION")
    print("=" * 40)
    
    print("\n📦 Required packages:")
    all_required_ok = True
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package:15} - {description}")
        except ImportError as e:
            print(f"   ❌ {package:15} - {description} - {e}")
            all_required_ok = False
    
    print("\n📊 Optional packages (for data analysis):")
    optional_ok = True
    
    for package, description in optional_packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {package:15} - {description} (v{version})")
        except ImportError as e:
            print(f"   ⚠️  {package:15} - {description} - Not installed")
            optional_ok = False
    
    print(f"\n📋 SUMMARY:")
    print(f"   Required packages: {'✅ All OK' if all_required_ok else '❌ Missing packages'}")
    print(f"   Optional packages: {'✅ All OK' if optional_ok else '⚠️ Some missing'}")
    
    if all_required_ok:
        print("\n🎉 Audit system core dependencies are ready!")
        if not optional_ok:
            print("💡 Install pandas, matplotlib, seaborn for full analytics features")
    else:
        print("\n❌ Please install missing required packages")
        return False
    
    return True

def check_numpy_opencv_conflict():
    """Check for numpy/opencv conflict"""
    try:
        import numpy
        numpy_version = numpy.__version__
        print(f"\n🔢 NumPy version: {numpy_version}")
        
        try:
            import cv2
            opencv_version = cv2.__version__
            print(f"📷 OpenCV version: {opencv_version}")
            
            # Check if versions are compatible
            numpy_major = int(numpy_version.split('.')[0])
            if numpy_major < 2:
                print("⚠️  WARNING: NumPy version may be incompatible with OpenCV")
                print("   Consider upgrading: pip install 'numpy>=2.0,<2.3.0'")
            else:
                print("✅ NumPy/OpenCV versions appear compatible")
                
        except ImportError:
            print("📷 OpenCV not installed (no conflict)")
            
    except ImportError:
        print("🔢 NumPy not installed")

if __name__ == "__main__":
    success = check_imports()
    check_numpy_opencv_conflict()
    
    if success:
        print("\n🚀 Ready to run audit system setup!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix dependency issues before proceeding")
        sys.exit(1)