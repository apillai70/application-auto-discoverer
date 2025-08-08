#!/usr/bin/env python3
"""
Verify that files are created in the correct locations for web server access
"""

from pathlib import Path
import json

def verify_web_paths():
    """Verify the file paths are correct for web server access"""
    
    print("🌐 Web Path Verification")
    print("=" * 40)
    
    project_root = Path('.')
    
    print(f"📁 Project root: {project_root.absolute()}")
    
    # Expected web server setup
    web_root = project_root / "static" / "ui"
    print(f"🌐 Web server root: {web_root}")
    print(f"   (You run 'python -m http.server' from this directory)")
    
    # File locations for web access
    files_to_check = {
        'JSON Data File': {
            'web_path': '/templates/activnet_data.json',
            'file_path': web_root / 'templates' / 'activnet_data.json',
            'url': 'http://localhost:8000/templates/activnet_data.json'
        },
        'Excel Data File': {
            'web_path': '/data/synthetic_flows_apps_archetype_mapped.xlsx', 
            'file_path': web_root / 'data' / 'synthetic_flows_apps_archetype_mapped.xlsx',
            'url': 'http://localhost:8000/data/synthetic_flows_apps_archetype_mapped.xlsx'
        }
    }
    
    print(f"\n📋 File Location Check:")
    print("-" * 50)
    
    for file_type, info in files_to_check.items():
        file_path = info['file_path']
        exists = file_path.exists()
        size = file_path.stat().st_size if exists else 0
        
        status = "✅ EXISTS" if exists else "❌ MISSING"
        
        print(f"\n{file_type}:")
        print(f"  Status: {status}")
        print(f"  Web URL: {info['url']}")
        print(f"  Web Path: {info['web_path']}")
        print(f"  File Path: {file_path}")
        
        if exists:
            print(f"  Size: {size:,} bytes")
            
            # For JSON files, try to validate content
            if file_type == 'JSON Data File' and size > 0:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"  ✅ Valid JSON with {len(data)} top-level keys")
                    
                    # Show key info
                    if 'metadata' in data:
                        metadata = data['metadata']
                        print(f"  📊 Records: {metadata.get('total_records', 'N/A')}")
                        print(f"  📊 Last Updated: {metadata.get('last_updated', 'N/A')}")
                    
                    if 'applications' in data:
                        print(f"  📊 Applications: {len(data['applications'])}")
                        
                except Exception as e:
                    print(f"  ❌ Invalid JSON: {e}")
        else:
            print(f"  📍 Directory exists: {file_path.parent.exists()}")
    
    # Directory structure check
    print(f"\n🗂️  Web Server Directory Structure:")
    print("-" * 40)
    
    web_dirs = [
        web_root,
        web_root / 'templates',
        web_root / 'data',
        web_root / 'js',
        web_root / 'css'
    ]
    
    for directory in web_dirs:
        exists = directory.exists()
        status = "✅" if exists else "❌"
        
        file_count = 0
        if exists and directory.is_dir():
            file_count = len(list(directory.iterdir()))
        
        rel_path = directory.relative_to(web_root) if exists else directory
        print(f"{status} /{rel_path} ({file_count} items)")
    
    # Instructions
    print(f"\n📝 Instructions:")
    print("-" * 20)
    print(f"1. Run the processor to create files:")
    print(f"   python activnet_file_processor.py --process-existing")
    print(f"")
    print(f"2. Start web server from the correct directory:")
    print(f"   cd {web_root}")
    print(f"   python -m http.server 8000")
    print(f"")
    print(f"3. Access your application at:")
    print(f"   http://localhost:8000/html/")
    print(f"")
    print(f"4. The JSON data will be available at:")
    print(f"   http://localhost:8000/templates/activnet_data.json")

if __name__ == "__main__":
    verify_web_paths()