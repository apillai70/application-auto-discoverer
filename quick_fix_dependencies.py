#!/usr/bin/env python3
"""
Quick fix for common dependency issues
Place this file in your project root directory (same level as main.py)
"""

import subprocess
import sys

def run_command(cmd):
    """Run shell command and return success"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {cmd}")
            return True
        else:
            print(f"❌ Failed: {cmd}")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception running {cmd}: {e}")
        return False

def main():
    print("🔧 QUICK DEPENDENCY FIX")
    print("=" * 30)
    
    # Try to fix numpy issue
    print("\n1️⃣ Fixing numpy version...")
    if run_command("pip install 'numpy>=2.0,<2.3.0'"):
        print("   NumPy updated successfully")
    
    # Install core audit dependencies
    print("\n2️⃣ Installing core audit dependencies...")
    core_deps = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0", 
        "pydantic>=2.5.0",
        "aiofiles>=23.2.0",
        "aiohttp>=3.9.0"
    ]
    
    for dep in core_deps:
        run_command(f"pip install '{dep}'")
    
    # Try optional dependencies
    print("\n3️⃣ Installing optional dependencies...")
    optional_deps = [
        "pandas>=2.1.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0"
    ]
    
    for dep in optional_deps:
        if not run_command(f"pip install '{dep}'"):
            print(f"   ⚠️ Skipping {dep} - you can install manually later")
    
    print("\n✅ Dependency fix complete!")
    print("🧪 Run verification: python verify_dependencies.py")

if __name__ == "__main__":
    main()