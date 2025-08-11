#!/usr/bin/env python3
"""
Automatic conflict resolution for numpy/scikit-learn/opencv
"""

import subprocess
import sys

def run_cmd(cmd, description):
    """Run command and report success/failure"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def check_packages():
    """Check current package versions"""
    packages = ['numpy', 'opencv-python', 'scikit-learn', 'pandas']
    
    print("📦 Current package versions:")
    for package in packages:
        try:
            module = __import__(package.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print(f"   {package}: {version}")
        except ImportError:
            print(f"   {package}: Not installed")

def solution_1_upgrade_sklearn():
    """Solution 1: Upgrade scikit-learn"""
    print("\n🚀 SOLUTION 1: Upgrading scikit-learn...")
    
    steps = [
        ("pip install --upgrade scikit-learn", "Upgrade scikit-learn"),
        ("pip install 'numpy>=2.0,<2.3.0'", "Install numpy 2.x"),
    ]
    
    for cmd, desc in steps:
        if not run_cmd(cmd, desc):
            return False
    return True

def solution_2_downgrade_opencv():
    """Solution 2: Downgrade opencv-python"""
    print("\n🚀 SOLUTION 2: Downgrading opencv-python...")
    
    steps = [
        ("pip install 'opencv-python<4.12.0'", "Downgrade opencv-python"),
        ("pip install 'numpy>=1.24,<2.0'", "Install numpy 1.x"),
    ]
    
    for cmd, desc in steps:
        if not run_cmd(cmd, desc):
            return False
    return True

def solution_3_remove_sklearn():
    """Solution 3: Remove scikit-learn"""
    print("\n🚀 SOLUTION 3: Removing scikit-learn...")
    
    steps = [
        ("pip uninstall scikit-learn -y", "Remove scikit-learn"),
        ("pip install 'numpy>=2.0,<2.3.0'", "Install numpy 2.x"),
    ]
    
    for cmd, desc in steps:
        if not run_cmd(cmd, desc):
            return False
    return True

def solution_4_minimal():
    """Solution 4: Minimal audit environment"""
    print("\n🚀 SOLUTION 4: Installing minimal audit environment...")
    
    return run_cmd("pip install -r requirements_audit_only.txt", "Install audit-only packages")

def main():
    print("🔧 AUTOMATIC CONFLICT RESOLUTION")
    print("=" * 40)
    
    check_packages()
    
    print("\nChoose a solution:")
    print("1. Upgrade scikit-learn (recommended)")
    print("2. Downgrade opencv-python") 
    print("3. Remove scikit-learn")
    print("4. Minimal audit system (no conflicts)")
    print("5. Check packages and exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            success = solution_1_upgrade_sklearn()
        elif choice == "2":
            success = solution_2_downgrade_opencv()
        elif choice == "3":
            success = solution_3_remove_sklearn()
        elif choice == "4":
            success = solution_4_minimal()
        elif choice == "5":
            print("✅ Package check complete")
            return 0
        else:
            print("❌ Invalid choice")
            return 1
        
        if success:
            print("\n✅ Conflict resolution completed!")
            print("🧪 Test with: python verify_dependencies.py")
        else:
            print("\n❌ Conflict resolution failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())