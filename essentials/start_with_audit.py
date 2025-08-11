# scripts/start_with_audit.py - Enhanced startup script

import uvicorn
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Start the application with enhanced audit capabilities"""
    print("🚀 Starting FastAPI Application with Enhanced Audit System")
    print("="*70)
    
    # Check audit configuration
    try:
        from config.audit_config import audit_config
        print(f"✅ Audit Configuration Loaded:")
        print(f"   - Storage Type: {audit_config.storage_type}")
        print(f"   - Risk Assessment: {'Enabled' if audit_config.enable_risk_assessment else 'Disabled'}")
        print(f"   - Azure AD Integration: {'Enabled' if audit_config.azure_ad_integration else 'Disabled'}")
        print(f"   - Okta Integration: {'Enabled' if audit_config.okta_integration else 'Disabled'}")
        print(f"   - ADFS Integration: {'Enabled' if audit_config.adfs_integration else 'Disabled'}")
    except ImportError:
        print("⚠️ Audit configuration not found, using defaults")
    
    # Check router availability
    try:
        import routers
        available_routers = routers.get_available_routers()
        audit_router = next((r for r in available_routers if r["name"] == "audit"), None)
        
        if audit_router and audit_router["status"] == "available":
            print(f"✅ Enhanced Audit Router: Available (v{audit_router['metadata']['version']})")
            features = audit_router['metadata'].get('features', [])
            print(f"   Features: {', '.join(features)}")
        else:
            print("❌ Enhanced Audit Router: Not available")
    except ImportError:
        print("⚠️ Router package not found")
    
    print(f"\n📖 API Documentation: http://localhost:8001/docs")
    print(f"🔍 Audit Endpoint: http://localhost:8001/api/v1/audit")
    print(f"📊 Audit Summary: http://localhost:8001/api/v1/audit/summary")
    print(f"⚠️ Suspicious Activity: http://localhost:8001/api/v1/audit/suspicious-activity")
    print("="*70)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=[str(project_root)],
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()