#!/usr/bin/env python3
"""
LucidChart Test Script
Run this to test your LucidChart file generation independently

Usage: python test_lucid.py
"""

import sys
import os
from pathlib import Path
import uuid
import asyncio

# Add your project root to path
sys.path.append(str(Path(__file__).parent))

async def test_lucid_creation():
    """Test LucidChart file creation with your specific requirements"""
    
    print("=== TESTING LUCID CHART GENERATION ===")
    
    # Test 1: Check template files exist
    print("\n1. Checking template files...")
    
    stencil_path = Path("templates/stencil_library.yaml") 
    layout_path = Path("templates/layout_templates.yaml")
    
    if not stencil_path.exists():
        print(f"❌ Missing: {stencil_path}")
        print("   Creating basic stencil template...")
        create_basic_stencil_template(stencil_path)
    else:
        print(f"✅ Found: {stencil_path}")
    
    if not layout_path.exists():
        print(f"❌ Missing: {layout_path}")
        print("   Creating basic layout template...")
        create_basic_layout_template(layout_path)
    else:
        print(f"✅ Found: {layout_path}")
    
    # Test 2: Check results directory
    print("\n2. Checking results directory...")
    
    results_dir = Path("results/lucid")
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Results directory: {results_dir}")
    
    # Test 3: Test LucidChart generation
    print("\n3. Testing LucidChart XML generation...")
    
    try:
        from services.archetype_lucid_stencils import (
            ArchetypeType, LucidChartGenerator
        )
        
        # Test data
        test_apps = [
            {"id": "web1", "name": "Customer Portal", "type": "web_application"},
            {"id": "api1", "name": "Payment API", "type": "api_service"}, 
            {"id": "db1", "name": "Transaction DB", "type": "database"}
        ]
        
        test_cases = [
            ("three_tier", ArchetypeType.THREE_TIER, "CustomerApp"),
            ("microservices", ArchetypeType.MICROSERVICES, "PaymentSystem"),
            ("monolithic", ArchetypeType.MONOLITHIC, "LegacyApp")
        ]
        
        generator = LucidChartGenerator()
        
        for archetype_str, archetype_type, app_name in test_cases:
            print(f"\n   Testing {archetype_str} archetype...")
            
            # Generate XML
            xml_content = generator.generate_lucidchart_xml(archetype_type, test_apps)
            
            # Generate filename with your required format
            job_id = str(uuid.uuid4())[:8]
            filename = f"{app_name}_{archetype_str}_{job_id}.lucid"
            file_path = results_dir / filename
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            file_size = file_path.stat().st_size
            print(f"   ✅ Generated: {filename} ({file_size} bytes)")
            
            # Show XML preview
            preview = xml_content[:200] + "..." if len(xml_content) > 200 else xml_content
            print(f"   XML Preview: {preview}")
        
        print(f"\n✅ All test files generated in: {results_dir}")
        
        # List generated files
        lucid_files = list(results_dir.glob("*.lucid"))
        print(f"\nGenerated files ({len(lucid_files)}):")
        for file_path in lucid_files:
            print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure your archetype_lucid_stencils.py file is in services/")
        return False
    
    except Exception as e:
        print(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_basic_stencil_template(path: Path):
    """Create a basic stencil template for testing"""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    basic_stencils = '''
version: "1.0"
description: "Basic stencil library for testing"

stencils:
  web_server:
    name: "Web Server"
    shape_type: "rectangle"
    dimensions:
      width: 120
      height: 80
    styling:
      fill_color: "#4ECDC4"
      border_color: "#45B7D1"
      border_width: 2
      corner_radius: 8
    display:
      icon: "WEB"
      text_size: 10
      font: "Arial"
    category: "web_frontend"
    
  database:
    name: "Database" 
    shape_type: "cylinder"
    dimensions:
      width: 100
      height: 120
    styling:
      fill_color: "#6C5CE7"
      border_color: "#5F3DC4"
      border_width: 2
      corner_radius: 8
    display:
      icon: "DB"
      text_size: 10
      font: "Arial"
    category: "data_storage"

archetype_stencils:
  monolithic:
    - web_server
    - database
  three_tier:
    - web_server
    - database
  microservices:
    - web_server
    - database
'''
    
    with open(path, 'w') as f:
        f.write(basic_stencils.strip())
    print(f"   ✅ Created basic template: {path}")

def create_basic_layout_template(path: Path):
    """Create a basic layout template for testing"""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    basic_layouts = '''
version: "1.0"
description: "Basic layout patterns for testing"

layouts:
  monolithic:
    name: "Monolithic Architecture"
    canvas:
      width: 800
      height: 600
    pattern: "vertical_stack"
    components:
      - id: "main_app"
        stencil: "web_server"
        position: { x: 400, y: 250 }
      - id: "database"
        stencil: "database"
        position: { x: 400, y: 400 }

  three_tier:
    name: "Three-Tier Architecture"
    canvas:
      width: 900
      height: 600
    pattern: "horizontal_tiers"
    components:
      - id: "web_server"
        stencil: "web_server"
        position: { x: 150, y: 250 }
      - id: "database"
        stencil: "database"
        position: { x: 650, y: 250 }

  microservices:
    name: "Microservices Architecture"
    canvas:
      width: 1000
      height: 700
    pattern: "service_mesh"
    components:
      - id: "service_1"
        stencil: "web_server"
        position: { x: 200, y: 200 }
      - id: "database"
        stencil: "database"
        position: { x: 500, y: 300 }
'''
    
    with open(path, 'w') as f:
        f.write(basic_layouts.strip())
    print(f"   ✅ Created basic template: {path}")

def test_api_endpoint():
    """Test the API endpoint if server is running"""
    import requests
    
    try:
        # Test the simple endpoint first
        response = requests.get("http://localhost:8000/api/v1/archetype/test-lucid-simple/three_tier")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Test passed: {result.get('success', False)}")
            if result.get('file_created'):
                print(f"   File created: {result['file_created']}")
        else:
            print(f"❌ API Test failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API not available: {e}")
        print("   Start your FastAPI server first")

if __name__ == "__main__":
    print("🧪 LucidChart File Generation Test")
    print("=" * 50)
    
    # Run async test
    success = asyncio.run(test_lucid_creation())
    
    if success:
        print("\n🎉 LucidChart generation test completed successfully!")
        print("\nNext steps:")
        print("1. Check the files in results/lucid/")
        print("2. Import one of the .lucid files into LucidChart to validate")
        print("3. Test the API endpoint: python test_lucid.py --api")
        
        if "--api" in sys.argv:
            print("\n📡 Testing API endpoint...")
            test_api_endpoint()
    else:
        print("\n❌ Test failed - check the errors above")
        sys.exit(1)