import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing router imports...")

try:
    # Test routers package
    import routers
    print(f"✅ Routers package imported")
    
    # Test diagram import
    from routers import diagram
    print(f"✅ Diagram module imported")
    
    # Check if router exists
    if hasattr(diagram, 'router'):
        print(f"✅ Router attribute exists")
        print(f"Router type: {type(diagram.router)}")
        
        # Check routes
        if hasattr(diagram.router, 'routes'):
            print(f"Number of routes: {len(diagram.router.routes)}")
            for route in diagram.router.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    print(f"  Route: {route.methods} {route.path}")
        else:
            print("No routes attribute found")
    else:
        print("❌ No router attribute in diagram module")
        
    # Test available routers
    available = routers.get_available_routers()
    print(f"Available routers: {[r['name'] for r in available]}")
    
    diagram_router = next((r for r in available if r['name'] == 'diagram'), None)
    if diagram_router:
        print(f"✅ Diagram router found in available list")
        print(f"Diagram router module: {diagram_router['module']}")
    else:
        print("❌ Diagram router not in available list")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()