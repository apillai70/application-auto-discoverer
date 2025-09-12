# setup_storage_integration.py
"""
Setup script to initialize the integrated file-based logging and audit storage system
Run this script to set up the directory structure and test the integration
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
import json

# Import the storage components
from storage.file_audit_storage import FileAuditStorage, StorageConfig
from storage.log_storage_manager import LogStorageManager, LogCategory
from services.frontend_security_logs import FrontendSecurityLogService

async def setup_storage_system():
    """Initialize the complete storage system"""
    
    print("🔧 Setting up integrated file-based storage system...")
    
    # 1. Create directory structure
    print("\n📁 Creating directory structure...")
    
    base_dirs = [
        "essentials/logs/application",
        "essentials/logs/security", 
        "essentials/logs/network",
        "essentials/logs/threats",
        "essentials/logs/performance",
        "essentials/logs/audit",
        "essentials/logs/debug",
        "essentials/audit/events",
        "essentials/audit/indexes",
        "essentials/audit/archives",
        "essentials/audit/backups",
        "essentials/audit/reports",
        "essentials/audit/temp",
        "results/logs",
        "results/audit",
        "results/security",
        "config"
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")
    
    # 2. Initialize storage components
    print("\n🗄️ Initializing storage components...")
    
    # Configure audit storage
    audit_config = StorageConfig(
        base_path="essentials/audit",
        format="jsonl",
        retention_days=365,
        compress_old_files=True,
        backup_enabled=True
    )
    
    audit_storage = FileAuditStorage(audit_config)
    print("  ✅ Audit storage initialized")
    
    # Initialize log storage manager
    log_storage = LogStorageManager()
    print("  ✅ Log storage manager initialized")
    
    # Initialize frontend security log service
    frontend_service = FrontendSecurityLogService()
    print("  ✅ Frontend security log service initialized")
    
    # 3. Test the system with sample data
    print("\n🧪 Testing storage system with sample data...")
    
    # Test audit storage
    sample_audit_event = {
        "event_type": "authentication",
        "user_id": "test.user@company.com",
        "action": "login",
        "result": "success",
        "source_ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "auth_details": {
            "identity_provider": "AzureAD",
            "mfa_method": "push_notification"
        },
        "device_info": {
            "device_fingerprint": "test_device_001"
        },
        "geographic_info": {
            "country": "United States",
            "city": "New York"
        }
    }
    
    audit_event_id = await audit_storage.store_event(sample_audit_event)
    print(f"  ✅ Stored audit event: {audit_event_id}")
    
    # Test log storage
    await log_storage.log_application_event(
        level="info",
        component="test_system",
        message="Storage system initialization test",
        details={"initialization": True, "timestamp": datetime.now().isoformat()}
    )
    print("  ✅ Stored application log event")
    
    await log_storage.log_security_event(
        level="info",
        message="Security system test event",
        details={"test": True, "security_check": "passed"}
    )
    print("  ✅ Stored security log event")
    
    # Test frontend logging
    frontend_event_data = {
        "event_type": "user_action",
        "level": "info",
        "action": "test_interaction",
        "page_url": "/test-page",
        "user_id": "test.user@company.com",
        "session_id": "test_session_123",
        "source_ip": "192.168.1.100",
        "details": {"test": True, "component": "storage_setup"}
    }
    
    frontend_event_id = await frontend_service.log_frontend_event(frontend_event_data)
    print(f"  ✅ Stored frontend event: {frontend_event_id}")
    
    # 4. Verify storage
    print("\n📊 Verifying storage functionality...")
    
    # Check audit storage
    audit_info = await audit_storage.get_storage_info()
    print(f"  📁 Audit storage: {audit_info['total_files']} files, {audit_info['total_size_mb']:.2f} MB")
    
    # Check log storage
    log_stats = await log_storage.get_log_statistics(days=1)
    print(f"  📁 Log storage: {log_stats['total_logs']} logs, {log_stats['storage_size_mb']:.2f} MB")
    
    # Test queries
    recent_audit_events = await audit_storage.query_events(limit=5)
    print(f"  🔍 Found {len(recent_audit_events)} recent audit events")
    
    recent_app_logs = await log_storage.query_logs(
        category=LogCategory.APPLICATION,
        limit=5
    )
    print(f"  🔍 Found {len(recent_app_logs)} recent application logs")
    
    # 5. Create configuration files
    print("\n⚙️ Creating configuration files...")
    
    # Storage configuration
    storage_config = {
        "audit_storage": {
            "base_path": "essentials/audit",
            "format": "jsonl",
            "retention_days": 365,
            "compress_old_files": True,
            "backup_enabled": True,
            "max_file_size_mb": 100
        },
        "log_storage": {
            "base_path": "essentials/logs",
            "retention_days": 90,
            "compress_after_days": 7,
            "max_file_size_mb": 50,
            "format": "jsonl"
        },
        "frontend_logging": {
            "batch_size": 50,
            "batch_timeout": 30,
            "enable_risk_assessment": True,
            "enable_threat_detection": True
        }
    }
    
    config_file = Path("config/storage_config.json")
    with open(config_file, 'w') as f:
        json.dump(storage_config, f, indent=2)
    print(f"  ✅ Created: {config_file}")
    
    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "essentials/logs/application/app.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "detailed"
            },
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "simple"
            }
        },
        "loggers": {
            "storage": {
                "level": "INFO",
                "handlers": ["file", "console"],
                "propagate": False
            },
            "services": {
                "level": "INFO", 
                "handlers": ["file", "console"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }
    
    logging_config_file = Path("config/logging_config.json")
    with open(logging_config_file, 'w') as f:
        json.dump(logging_config, f, indent=2)
    print(f"  ✅ Created: {logging_config_file}")
    
    # 6. Create integration example
    print("\n📝 Creating integration examples...")
    
    integration_example = '''# Integration Example for main.py

# Add these imports to your main.py
from storage.file_audit_storage import FileAuditStorage, StorageConfig
from storage.log_storage_manager import LogStorageManager
from services.frontend_security_logs import FrontendSecurityLogService

# Initialize in your lifespan function
async def enhanced_lifespan(app: FastAPI):
    """Enhanced lifespan with storage initialization"""
    
    # STARTUP
    print("🚀 Initializing storage systems...")
    
    # Initialize audit storage
    audit_config = StorageConfig(
        base_path="essentials/audit",
        retention_days=365,
        compress_old_files=True
    )
    app.state.audit_storage = FileAuditStorage(audit_config)
    
    # Initialize log storage
    app.state.log_storage = LogStorageManager()
    
    # Initialize frontend service
    app.state.frontend_service = FrontendSecurityLogService()
    
    print("✅ Storage systems initialized")
    
    yield
    
    # SHUTDOWN
    print("🛑 Storage systems shutting down...")

# Update your router includes to use the enhanced audit router
app.include_router(
    enhanced_audit_router,
    prefix="/api/v1/audit",
    tags=["audit", "logging"]
)
'''
    
    integration_file = Path("integration_example.py")
    with open(integration_file, 'w') as f:
        f.write(integration_example)
    print(f"  ✅ Created: {integration_file}")
    
    # 7. Summary
    print("\n🎉 Storage system setup complete!")
    print("\n📋 Summary:")
    print(f"  • Directory structure created in essentials/")
    print(f"  • Audit storage: {audit_info['total_files']} files initialized")
    print(f"  • Log storage: {len(LogCategory)} categories configured")
    print(f"  • Configuration files created in config/")
    print(f"  • Test data stored successfully")
    
    print("\n🚀 Next steps:")
    print("  1. Update your main.py with the integration example")
    print("  2. Replace your existing audit router with enhanced_audit.py")
    print("  3. Add frontend logging calls to your UI components")
    print("  4. Configure log rotation and retention policies")
    print("  5. Set up monitoring for storage health")
    
    print(f"\n📁 Storage locations:")
    print(f"  • Audit events: {Path('essentials/audit/events').absolute()}")
    print(f"  • Application logs: {Path('essentials/logs').absolute()}")
    print(f"  • Export results: {Path('results').absolute()}")
    
    return {
        "audit_storage": audit_storage,
        "log_storage": log_storage,
        "frontend_service": frontend_service,
        "audit_info": audit_info,
        "log_stats": log_stats
    }

async def verify_integration():
    """Verify that the storage integration is working correctly"""
    
    print("\n🔍 Verifying storage integration...")
    
    try:
        # Test imports
        from storage.file_audit_storage import FileAuditStorage
        from storage.log_storage_manager import LogStorageManager
        from services.frontend_security_logs import FrontendSecurityLogService
        print("  ✅ All imports successful")
        
        # Test directory structure
        required_dirs = [
            "essentials/logs",
            "essentials/audit",
            "results"
        ]
        
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                print(f"  ✅ Directory exists: {dir_path}")
            else:
                print(f"  ❌ Missing directory: {dir_path}")
        
        # Test storage initialization
        audit_storage = FileAuditStorage()
        log_storage = LogStorageManager()
        print("  ✅ Storage components initialize successfully")
        
        # Test basic functionality
        test_event = {
            "event_type": "test",
            "user_id": "verify_user",
            "action": "verification_test",
            "result": "success"
        }
        
        event_id = await audit_storage.store_event(test_event)
        print(f"  ✅ Audit storage working: {event_id}")
        
        await log_storage.log_application_event(
            level="info",
            component="verification",
            message="Integration verification test"
        )
        print("  ✅ Log storage working")
        
        print("\n✅ Integration verification complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 File-based Storage Integration Setup")
    print("=" * 50)
    
    # Run setup
    asyncio.run(setup_storage_system())
    
    print("\n" + "=" * 50)
    print("✅ Setup complete! Run 'python -c \"import setup_storage_integration; import asyncio; asyncio.run(setup_storage_integration.verify_integration())\"' to verify.")