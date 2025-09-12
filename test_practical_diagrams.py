#!/usr/bin/env python3
"""
Test Script for Practical Diagram Generation
Tests Draw.io, PDF, and CSV generation

Usage: python test_practical_diagrams.py
"""

import sys
import os
from pathlib import Path
import asyncio
import reportlab

# Add your project root to path
sys.path.append(str(Path(__file__).parent))

def test_practical_generation():
    """Test all practical diagram formats"""
    
    print("🧪 Testing Practical Diagram Generation")
    print("=" * 50)
    
    # Step 1: Create the generator file
    print("1. Setting up practical diagram generators...")
    
    services_dir = Path("services")
    services_dir.mkdir(exist_ok=True)
    
    generator_file = services_dir / "practical_diagram_generators.py"
    
    if not generator_file.exists():
        print("   Creating practical_diagram_generators.py...")
        # Copy the generator code from the artifact above
        print("   ⚠️  Please copy the generator code from the artifact into:")
        print(f"      {generator_file}")
        return False
    else:
        print(f"   ✅ Found: {generator_file}")
    
    # Step 2: Test imports
    print("\n2. Testing imports...")
    
    try:
        from services.practical_diagram_generators import generate_all_formats
        print("   ✅ Imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Step 3: Create test data
    print("\n3. Creating test data...")
    
    test_cases = [
        ("three_tier", "CustomerPortal", [
            {"id": "web1", "name": "Customer Portal", "type": "web"},
            {"id": "api1", "name": "Customer API", "type": "api"},
            {"id": "db1", "name": "Customer DB", "type": "database"}
        ]),
        ("microservices", "ECommerceApp", [
            {"id": "svc1", "name": "User Service", "type": "microservice"},
            {"id": "svc2", "name": "Order Service", "type": "microservice"},
            {"id": "svc3", "name": "Payment Service", "type": "microservice"},
            {"id": "db1", "name": "Shared DB", "type": "database"}
        ]),
        ("monolithic", "LegacySystem", [
            {"id": "app1", "name": "Legacy Application", "type": "monolithic"}
        ])
    ]
    
    # Step 4: Generate diagrams
    print("\n4. Generating diagrams...")
    
    for archetype, app_name, applications in test_cases:
        print(f"\n   Testing {archetype} archetype...")
        
        try:
            result = generate_all_formats(archetype, applications, app_name)
            
            if result["success"]:
                print(f"   ✅ Generated {len(result['files'])} files for {app_name}")
                
                for file_info in result["files"]:
                    print(f"      - {file_info['filename']} ({file_info['format']})")
            else:
                print(f"   ❌ Failed to generate files for {app_name}")
                
        except Exception as e:
            print(f"   ❌ Error generating {archetype}: {e}")
    
    # Step 5: List all generated files
    print("\n5. Summary of generated files...")
    
    results_dir = Path("results/lucid")
    if results_dir.exists():
        files = list(results_dir.glob("*"))
        print(f"   Total files: {len(files)}")
        
        for file_path in sorted(files):
            size_kb = file_path.stat().st_size / 1024
            print(f"   - {file_path.name} ({size_kb:.1f} KB)")
    
    return True

def test_api_endpoints():
    """Test API endpoints if server is running"""
    
    try:
        import requests
        
        print("\n📡 Testing API Endpoints...")
        
        # Test endpoints
        test_urls = [
            ("GET", "http://localhost:8000/api/v1/archetype/test-drawio/three_tier"),
            ("POST", "http://localhost:8000/api/v1/archetype/generate-practical-diagrams"),
            ("GET", "http://localhost:8000/api/v1/archetype/list-generated-files")
        ]
        
        for method, url in test_urls:
            try:
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json={
                        "archetype": "microservices",
                        "app_name": "TestAPI",
                        "job_id": "test123"
                    }, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {method} {url.split('/')[-1]}: {result.get('success', 'OK')}")
                else:
                    print(f"   ❌ {method} {url.split('/')[-1]}: Status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  {method} {url.split('/')[-1]}: Not available ({e})")
        
    except ImportError:
        print("   ⚠️  requests library not available - skip API tests")

def show_usage_instructions():
    """Show how to use the generated files"""
    
    print("\n📋 How to Use Generated Files:")
    print("=" * 50)
    
    print("\n🎨 Draw.io Files (.drawio):")
    print("   1. Go to https://app.diagrams.net/")
    print("   2. Click 'Open Existing Diagram'") 
    print("   3. Upload your .drawio file")
    print("   4. Edit, save, or export as needed")
    
    print("\n📄 PDF Files (.pdf):")
    print("   1. Open in any PDF viewer")
    print("   2. Print or share directly")
    print("   3. Good for presentations and documentation")
    
    print("\n📊 CSV Files (.csv):")
    print("   1. Go to https://lucid.app/")
    print("   2. Create new diagram")
    print("   3. Import > CSV")
    print("   4. Upload the shapes CSV first, then connections CSV")
    
    print("\n🔧 Integration with Your App:")
    print("   Add to your archetype_router.py:")
    print("   ```python")
    print("   from services.practical_diagram_generators import generate_all_formats")
    print("   ")
    print("   @router.post('/generate-diagrams')")
    print("   async def generate_diagrams(archetype: str, app_name: str):")
    print("       result = generate_all_formats(archetype, applications, app_name)")
    print("       return result")
    print("   ```")

if __name__ == "__main__":
    print("Starting practical diagram generation tests...")
    
    success = test_practical_generation()
    
    if success:
        print("\n🎉 All tests passed!")
        
        if "--api" in sys.argv:
            test_api_endpoints()
        
        show_usage_instructions()
        
        # Show results directory
        results_dir = Path("results/lucid")
        if results_dir.exists():
            print(f"\n📁 Check your files in: {results_dir.absolute()}")
    else:
        print("\n❌ Tests failed - check the setup steps above")
        sys.exit(1)