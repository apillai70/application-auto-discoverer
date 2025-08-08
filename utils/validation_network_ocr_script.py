#!/usr/bin/env python3
"""
Setup validation script for Network OCR Processor
Tests dependencies and simulates processing
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        ('pandas', 'pip install pandas'),
        ('pytesseract', 'pip install pytesseract'),
        ('PIL', 'pip install pillow'),
        ('cv2', 'pip install opencv-python'),
        ('openpyxl', 'pip install openpyxl')
    ]
    
    missing = []
    for package, install_cmd in required_packages:
        try:
            __import__(package if package != 'PIL' else 'PIL.Image')
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(install_cmd)
    
    if missing:
        print(f"\n📦 Install missing packages:")
        for cmd in missing:
            print(f"   {cmd}")
        return False
    
    print("✅ All dependencies satisfied!")
    return True

def check_tesseract():
    """Check Tesseract OCR installation"""
    print("\n🔍 Checking Tesseract OCR...")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract v{version} - OK")
        return True
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        print("📥 Install Tesseract:")
        print("   Windows: https://github.com/tesseract-ocr/tesseract")
        print("   Linux: sudo apt-get install tesseract-ocr")
        print("   macOS: brew install tesseract")
        return False

def check_directories():
    """Check directory structure"""
    print("\n🔍 Checking directories...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == 'utils' else script_dir
    
    directories = {
        'download': project_root / 'download',
        'data_staging': project_root / 'data_staging', 
        'processed': project_root / 'download' / 'processed',
        'logs': project_root / 'logs',
        'utils': project_root / 'utils'
    }
    
    all_good = True
    for name, path in directories.items():
        if path.exists():
            print(f"✅ {name}/ - OK")
        else:
            print(f"📁 {name}/ - Creating...")
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ {name}/ - Created")
            except Exception as e:
                print(f"❌ {name}/ - Error: {e}")
                all_good = False
    
    return all_good

def simulate_processing():
    """Simulate network data processing"""
    print("\n🔍 Simulating data processing...")
    
    # Sample data from your images
    sample_data = [
        {
            'IP_Address': 'fe80::f98c:82a9:8652:6a46',
            'Device_Name': 'VMware BCF699',
            'Peer_Info': '10.164.145.69(upvulnapp43.unix.rgbk.com)',
            'Protocol': 'SSL:21047',
            'Bytes_In': 2525712,
            'Bytes_Out': 3823384,
            'Total_Bytes': 6349096
        },
        {
            'IP_Address': 'fe80::6029:20f8:8a4d:ef2', 
            'Device_Name': 'VMware BCC8B5',
            'Peer_Info': '10.164.145.61(upvulnapp36.unix.rgbk.com)',
            'Protocol': 'SSL:21047',
            'Bytes_In': 1248138,
            'Bytes_Out': 2102810,
            'Total_Bytes': 3350948
        }
    ]
    
    try:
        import pandas as pd
        df = pd.DataFrame(sample_data)
        print("✅ Sample data structure:")
        print(df.to_string(index=False))
        
        # Test Excel export
        script_dir = Path(__file__).parent
        project_root = script_dir.parent if script_dir.name == 'utils' else script_dir
        test_file = project_root / 'data_staging' / 'test_output.xlsx'
        
        df.to_excel(test_file, index=False, engine='openpyxl')
        print(f"✅ Excel export test: {test_file}")
        
        # Clean up test file
        if test_file.exists():
            test_file.unlink()
            
        return True
        
    except Exception as e:
        print(f"❌ Processing simulation failed: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🚀 Network OCR Processor - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Tesseract OCR", check_tesseract), 
        ("Directories", check_directories),
        ("Processing", simulate_processing)
    ]
    
    all_passed = True
    for name, check_func in checks:
        result = check_func()
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your setup is ready for OCR processing")
        print("\n📸 Next steps:")
        print("1. Place your images in download/ folder")
        print("2. Run: python utils/network_ocr_processor.py")
    else:
        print("❌ SETUP INCOMPLETE")
        print("Please resolve the issues above before processing images")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)