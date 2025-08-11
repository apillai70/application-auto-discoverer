# setup_audit_system.py - Complete Setup Guide for File-Based Audit System

import os
import sys
import json
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

class AuditSystemSetup:
    """Complete setup and configuration for the file-based audit system"""
    
    def __init__(self, app_root: Path = None):
        self.app_root = app_root or Path.cwd()
        self.essentials_dir = self.app_root / "essentials"
        self.audit_dir = self.essentials_dir / "audit"
        
    async def setup_complete_system(self):
        """Set up the complete audit system with all components"""
        print("🚀 Setting up Complete File-Based Audit System")
        print("=" * 60)
        
        # 1. Create directory structure
        await self.create_directory_structure()
        
        # 2. Create configuration files
        await self.create_configuration_files()
        
        # 3. Set up storage system
        await self.initialize_storage_system()
        
        # 4. Create sample data for testing
        await self.create_sample_data()
        
        # 5. Set up processing utilities
        await self.setup_processing_utilities()
        
        # 6. Create monitoring scripts
        await self.create_monitoring_scripts()
        
        # 7. Generate documentation
        await self.generate_documentation()
        
        print("\n✅ Audit System Setup Complete!")
        print("📁 All files created in: essentials/audit/")
        print("🔧 Ready to process authentication events!")
        
    async def create_directory_structure(self):
        """Create the complete directory structure"""
        print("\n📁 Creating directory structure...")
        
        directories = [
            self.audit_dir / "events",
            self.audit_dir / "indexes", 
            self.audit_dir / "archives",
            self.audit_dir / "backups",
            self.audit_dir / "reports",
            self.audit_dir / "temp",
            self.audit_dir / "incidents",
            self.audit_dir / "config",
            self.audit_dir / "scripts",
            self.audit_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory.relative_to(self.app_root)}")
        
        # Create monthly subdirectories for current and next month
        current_date = datetime.now()
        for months_ahead in range(3):  # Current + next 2 months
            date = current_date + timedelta(days=30 * months_ahead)
            month_dir = self.audit_dir / "events" / f"{date.year:04d}" / f"{date.month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"   📅 Created monthly directories for event organization")
    
    async def create_configuration_files(self):
        """Create configuration files for the audit system"""
        print("\n⚙️ Creating configuration files...")
        
        # Main audit configuration
        audit_config = {
            "storage": {
                "type": "file_based",
                "base_path": "essentials/audit",
                "format": "jsonl",
                "rotation": "daily",
                "max_file_size_mb": 100,
                "compress_old_files": True,
                "retention_days": 365
            },
            "risk_assessment": {
                "enabled": True,
                "geographic_weight": 25.0,
                "temporal_weight": 15.0,
                "device_weight": 20.0,
                "behavioral_weight": 30.0,
                "thresholds": {
                    "low": 30,
                    "medium": 50,
                    "high": 70,
                    "critical": 90
                }
            },
            "integrations": {
                "azure_ad": True,
                "okta": True,
                "adfs": True,
                "siem_enabled": False
            },
            "monitoring": {
                "real_time_alerts": True,
                "suspicious_activity_threshold": 10,
                "high_risk_notification": True,
                "backup_enabled": True
            },
            "processing": {
                "background_tasks": True,
                "batch_size": 1000,
                "index_enabled": True,
                "auto_archival": True
            }
        }
        
        config_file = self.audit_dir / "config" / "audit_config.json"
        async with aiofiles.open(config_file, 'w') as f:
            await f.write(json.dumps(audit_config, indent=2))
        print(f"   ✅ Created: {config_file.relative_to(self.app_root)}")
        
        # Risk assessment rules
        risk_rules = {
            "geographic_rules": {
                "trusted_countries": ["United States", "Canada", "United Kingdom"],
                "high_risk_countries": ["Unknown", "TOR Exit Node"],
                "location_change_threshold": 1000  # km
            },
            "temporal_rules": {
                "business_hours": {"start": 6, "end": 22},
                "weekend_factor": 1.5,
                "holiday_factor": 2.0
            },
            "device_rules": {
                "trusted_device_threshold": 30,  # days
                "new_device_penalty": 20,
                "untrusted_device_penalty": 15
            },
            "behavioral_rules": {
                "failed_attempts_threshold": 5,
                "velocity_threshold": 300,  # seconds
                "session_anomaly_detection": True
            },
            "ip_reputation": {
                "blacklist_penalty": 50,
                "proxy_penalty": 25,
                "datacenter_penalty": 15
            }
        }
        
        rules_file = self.audit_dir / "config" / "risk_rules.json"
        async with aiofiles.open(rules_file, 'w') as f:
            await f.write(json.dumps(risk_rules, indent=2))
        print(f"   ✅ Created: {rules_file.relative_to(self.app_root)}")
        
        # Identity provider configurations
        idp_config = {
            "azure_ad": {
                "webhook_endpoint": "/api/v1/audit/integrations/azure-ad",
                "required_fields": ["userPrincipalName", "ipAddress", "resultType"],
                "field_mapping": {
                    "userPrincipalName": "user_id",
                    "ipAddress": "source_ip",
                    "resultType": "error_code",
                    "activityDisplayName": "action"
                }
            },
            "okta": {
                "webhook_endpoint": "/api/v1/audit/integrations/okta",
                "required_fields": ["actor.alternateId", "client.ipAddress", "outcome.result"],
                "field_mapping": {
                    "actor.alternateId": "user_id",
                    "client.ipAddress": "source_ip",
                    "outcome.result": "result",
                    "eventType": "action"
                }
            },
            "adfs": {
                "webhook_endpoint": "/api/v1/audit/integrations/adfs",
                "required_fields": ["username", "client_ip", "result"],
                "field_mapping": {
                    "username": "user_id",
                    "client_ip": "source_ip",
                    "result": "result",
                    "action": "action"
                }
            }
        }
        
        idp_file = self.audit_dir / "config" / "identity_providers.json"
        async with aiofiles.open(idp_file, 'w') as f:
            await f.write(json.dumps(idp_config, indent=2))
        print(f"   ✅ Created: {idp_file.relative_to(self.app_root)}")
    
    async def initialize_storage_system(self):
        """Initialize the storage system with metadata"""
        print("\n💾 Initializing storage system...")
        
        # Create storage metadata
        storage_metadata = {
            "system_info": {
                "version": "2.1.0",
                "created": datetime.now().isoformat(),
                "storage_type": "file_based",
                "format": "jsonl"
            },
            "statistics": {
                "total_events": 0,
                "total_files": 0,
                "total_size_bytes": 0,
                "last_updated": datetime.now().isoformat()
            },
            "schema_version": {
                "current": "1.0.0",
                "compatible": ["1.0.0"],
                "migration_required": False
            }
        }
        
        metadata_file = self.audit_dir / "storage_metadata.json"
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(storage_metadata, indent=2))
        print(f"   ✅ Created: {metadata_file.relative_to(self.app_root)}")
        
        # Create index template
        index_template = {
            "index_info": {
                "created": datetime.now().isoformat(),
                "period": "monthly",
                "total_events": 0
            },
            "events": []
        }
        
        current_month = datetime.now().strftime('%Y-%m')
        index_file = self.audit_dir / "indexes" / f"index_{current_month}.json"
        async with aiofiles.open(index_file, 'w') as f:
            await f.write(json.dumps(index_template, indent=2))
        print(f"   ✅ Created: {index_file.relative_to(self.app_root)}")
    
    async def create_sample_data(self):
        """Create sample audit data for testing"""
        print("\n📊 Creating sample audit data...")
        
        sample_events = [
            {
                "event_id": "sample-001",
                "event_type": "authentication",
                "timestamp": datetime.now().isoformat(),
                "user_id": "john.doe@company.com",
                "action": "login",
                "result": "success",
                "source_ip": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "auth_details": {
                    "identity_provider": "AzureAD",
                    "auth_method": "password_mfa",
                    "mfa_method": "push_notification"
                },
                "device_info": {
                    "device_type": "desktop",
                    "os": "Windows 10",
                    "browser": "Chrome",
                    "is_trusted": True,
                    "device_fingerprint": "device_001_john"
                },
                "geographic_info": {
                    "country": "United States",
                    "region": "California",
                    "city": "San Francisco"
                },
                "application": "Office365",
                "risk_assessment": {
                    "risk_level": "low",
                    "risk_score": 15.0,
                    "contributing_factors": [],
                    "geographic_risk": False,
                    "temporal_risk": False,
                    "device_risk": False,
                    "behavioral_risk": False
                },
                "tags": ["sample_data", "successful_login"]
            },
            {
                "event_id": "sample-002",
                "event_type": "authentication",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "user_id": "jane.smith@company.com",
                "action": "login",
                "result": "failure",
                "source_ip": "203.0.113.45",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
                "auth_details": {
                    "identity_provider": "Okta",
                    "auth_method": "password",
                    "failure_reason": "Invalid credentials",
                    "error_code": "E0000004"
                },
                "device_info": {
                    "device_type": "mobile",
                    "os": "iOS 14.7.1",
                    "browser": "Safari",
                    "is_trusted": False,
                    "device_fingerprint": "device_002_jane"
                },
                "geographic_info": {
                    "country": "United Kingdom",
                    "region": "England",
                    "city": "London"
                },
                "application": "VPN_Gateway",
                "risk_assessment": {
                    "risk_level": "medium",
                    "risk_score": 45.0,
                    "contributing_factors": ["New geographic location", "New device"],
                    "geographic_risk": True,
                    "temporal_risk": False,
                    "device_risk": True,
                    "behavioral_risk": False
                },
                "tags": ["sample_data", "failed_login", "new_location"]
            },
            {
                "event_id": "sample-003",
                "event_type": "authentication",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "user_id": "admin@company.com",
                "action": "login",
                "result": "success",
                "source_ip": "185.220.101.182",
                "user_agent": "curl/7.68.0",
                "auth_details": {
                    "identity_provider": "ADFS",
                    "auth_method": "password"
                },
                "device_info": {
                    "device_type": "unknown",
                    "os": "Linux",
                    "is_trusted": False,
                    "device_fingerprint": "device_003_admin"
                },
                "geographic_info": {
                    "country": "Russia",
                    "region": "Moscow",
                    "city": "Moscow"
                },
                "application": "AdminPanel",
                "risk_assessment": {
                    "risk_level": "critical",
                    "risk_score": 85.0,
                    "contributing_factors": [
                        "New geographic location",
                        "Suspicious user agent",
                        "Administrative account",
                        "Untrusted device"
                    ],
                    "geographic_risk": True,
                    "temporal_risk": False,
                    "device_risk": True,
                    "behavioral_risk": True
                },
                "tags": ["sample_data", "high_risk", "admin_access", "suspicious"]
            }
        ]
        
        # Write sample events to current day's file
        current_date = datetime.now()
        events_file = (self.audit_dir / "events" / 
                      f"{current_date.year:04d}" / 
                      f"{current_date.month:02d}" / 
                      f"events_{current_date.strftime('%Y-%m-%d')}.jsonl")
        
        async with aiofiles.open(events_file, 'w') as f:
            for event in sample_events:
                await f.write(json.dumps(event, default=str) + '\n')
        
        print(f"   ✅ Created: {events_file.relative_to(self.app_root)}")
        print(f"   📊 Added {len(sample_events)} sample events")
    
    async def setup_processing_utilities(self):
        """Set up processing and analysis utilities"""
        print("\n🔧 Setting up processing utilities...")
        
        # Create analysis script
        analysis_script = '''#!/usr/bin/env python3
"""
Audit Analysis Script
Run comprehensive analysis on stored audit data
"""

import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.audit_file_processor import AuditCLI

async def main():
    """Main analysis function"""
    cli = AuditCLI()
    
    # Default to last 7 days, or take from command line
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    
    print(f"🔍 Running audit analysis for last {days} days...")
    
    try:
        results = cli.run_analysis(days)
        print("\\n✅ Analysis completed successfully!")
        
        # Print key metrics
        analysis = results["analysis"]
        print(f"📊 Total events analyzed: {analysis.total_events:,}")
        print(f"🚨 Suspicious patterns found: {len(analysis.suspicious_patterns)}")
        
        if analysis.suspicious_patterns:
            print("\\n⚠️ Suspicious Activity Summary:")
            for pattern in analysis.suspicious_patterns[:5]:  # Show top 5
                print(f"   [{pattern['severity'].upper()}] {pattern['description']}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
'''
        
        script_file = self.audit_dir / "scripts" / "analyze_audit_data.py"
        async with aiofiles.open(script_file, 'w') as f:
            await f.write(analysis_script)
        
        # Make script executable on Unix systems
        try:
            script_file.chmod(0o755)
        except:
            pass
        
        print(f"   ✅ Created: {script_file.relative_to(self.app_root)}")
        
        # Create daily report script
        daily_report_script = '''#!/usr/bin/env python3
"""
Daily Audit Report Generator
Generates daily summary reports automatically
"""

import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.audit_file_processor import AuditFileProcessor

async def generate_daily_report():
    """Generate daily audit report"""
    processor = AuditFileProcessor()
    
    # Yesterday's data
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=1)
    
    print(f"📅 Generating daily report for {start_date.date()}")
    
    try:
        # Run analysis
        analysis = processor.analyze_files(start_date, end_date)
        
        # Create report filename
        report_date = start_date.strftime('%Y-%m-%d')
        report_file = f"daily_report_{report_date}.txt"
        
        # Generate reports
        summary_path = processor.create_summary_report(analysis, report_file)
        
        # Create visualizations
        charts_dir = f"charts_{report_date}"
        chart_files = processor.create_visualizations(analysis, 
                                                    processor.reports_dir / charts_dir)
        
        print(f"✅ Daily report generated:")
        print(f"   📄 Summary: {summary_path}")
        print(f"   📊 Charts: {len(chart_files)} files in {charts_dir}/")
        
        # Create daily summary JSON for programmatic access
        daily_summary = {
            "date": report_date,
            "total_events": analysis.total_events,
            "event_types": analysis.event_types,
            "authentication_results": analysis.authentication_results,
            "risk_levels": analysis.risk_levels,
            "suspicious_patterns_count": len(analysis.suspicious_patterns),
            "top_users": analysis.top_users[:5],
            "top_ips": analysis.top_ips[:5],
            "generated_at": datetime.now().isoformat()
        }
        
        json_file = processor.reports_dir / f"daily_summary_{report_date}.json"
        with open(json_file, 'w') as f:
            json.dump(daily_summary, f, indent=2, default=str)
        
        print(f"   📋 JSON Summary: {json_file}")
        
    except Exception as e:
        print(f"❌ Daily report generation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(generate_daily_report())
    sys.exit(exit_code)
'''
        
        daily_script_file = self.audit_dir / "scripts" / "daily_report.py"
        async with aiofiles.open(daily_script_file, 'w') as f:
            await f.write(daily_report_script)
        
        print(f"   ✅ Created: {daily_script_file.relative_to(self.app_root)}")
        
        # Create data export utility
        export_script = '''#!/usr/bin/env python3
"""
Audit Data Export Utility
Export audit data in various formats
"""

import sys
import argparse
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.audit_file_processor import AuditFileProcessor

async def export_data():
    """Export audit data based on command line arguments"""
    parser = argparse.ArgumentParser(description='Export audit data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to export')
    parser.add_argument('--format', choices=['json', 'csv', 'jsonl'], default='csv', 
                       help='Export format')
    parser.add_argument('--output', help='Output filename')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    processor = AuditFileProcessor()
    
    # Determine date range
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    
    print(f"📦 Exporting audit data from {start_date.date()} to {end_date.date()}")
    print(f"📄 Format: {args.format}")
    
    try:
        if args.format == 'csv':
            output_file = processor.export_to_csv(start_date, end_date, args.output)
        else:
            output_file = await processor.file_storage.export_events(
                start_date, end_date, args.format, args.output)
        
        print(f"✅ Export completed: {output_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(export_data())
    sys.exit(exit_code)
'''
        
        export_script_file = self.audit_dir / "scripts" / "export_data.py"
        async with aiofiles.open(export_script_file, 'w') as f:
            await f.write(export_script)
        
        print(f"   ✅ Created: {export_script_file.relative_to(self.app_root)}")
    
    async def create_monitoring_scripts(self):
        """Create monitoring and maintenance scripts"""
        print("\n📊 Creating monitoring scripts...")
        
        # Create system health check script
        health_check_script = '''#!/usr/bin/env python3
"""
Audit System Health Check
Monitor the health and performance of the audit system
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from storage.file_audit_storage import FileAuditStorage

async def health_check():
    """Perform comprehensive health check"""
    print("🏥 Audit System Health Check")
    print("=" * 40)
    
    storage = FileAuditStorage()
    
    try:
        # Check storage system
        storage_info = await storage.file_storage.get_storage_info()
        
        print(f"📁 Storage Status:")
        print(f"   Base Path: {storage_info['base_path']}")
        print(f"   Total Size: {storage_info['total_size_mb']:.2f} MB")
        print(f"   Total Files: {storage_info['total_files']}")
        print(f"   Format: {storage_info['storage_format']}")
        
        # Check recent activity
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        recent_events = await storage.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        print(f"\\n📊 Recent Activity (24h):")
        print(f"   Total Events: {len(recent_events)}")
        
        if recent_events:
            # Analyze event types
            event_types = {}
            auth_results = {}
            risk_levels = {}
            
            for event in recent_events:
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                
                if event_type == 'authentication':
                    result = event.get('result', 'unknown')
                    auth_results[result] = auth_results.get(result, 0) + 1
                
                risk_assessment = event.get('risk_assessment', {})
                if risk_assessment:
                    risk_level = risk_assessment.get('risk_level', 'unknown')
                    risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            print(f"   Event Types: {dict(event_types)}")
            print(f"   Auth Results: {dict(auth_results)}")
            print(f"   Risk Levels: {dict(risk_levels)}")
        
        # Check cache status
        cache_stats = storage_info.get('cache_statistics', {})
        print(f"\\n💾 Cache Status:")
        print(f"   User Profiles: {cache_stats.get('user_profiles', 0)}")
        print(f"   Suspicious IPs: {cache_stats.get('suspicious_ips', 0)}")
        print(f"   Device Scores: {cache_stats.get('device_trust_scores', 0)}")
        
        # Check disk space (simple check)
        import shutil
        base_path = Path(storage_info['base_path'])
        if base_path.exists():
            total, used, free = shutil.disk_usage(base_path)
            free_gb = free // (1024**3)
            used_gb = used // (1024**3)
            total_gb = total // (1024**3)
            
            print(f"\\n💿 Disk Usage:")
            print(f"   Total: {total_gb} GB")
            print(f"   Used: {used_gb} GB")
            print(f"   Free: {free_gb} GB")
            
            if free_gb < 5:
                print("   ⚠️  WARNING: Low disk space!")
        
        print(f"\\n✅ Health check completed at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)
'''
        
        health_script_file = self.audit_dir / "scripts" / "health_check.py"
        async with aiofiles.open(health_script_file, 'w') as f:
            await f.write(health_check_script)
        
        print(f"   ✅ Created: {health_script_file.relative_to(self.app_root)}")
        
        # Create cleanup script
        cleanup_script = '''#!/usr/bin/env python3
"""
Audit System Cleanup
Clean up old files and maintain the audit system
"""

import asyncio
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

async def cleanup_audit_system():
    """Clean up old audit files and maintain system"""
    print("🧹 Audit System Cleanup")
    print("=" * 30)
    
    base_path = Path("essentials/audit")
    
    # Configuration
    retention_days = 365
    compress_days = 7
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    compress_cutoff = datetime.now() - timedelta(days=compress_days)
    
    deleted_count = 0
    compressed_count = 0
    
    # Clean up old files
    print(f"🗑️  Removing files older than {retention_days} days...")
    
    events_dir = base_path / "events"
    if events_dir.exists():
        for year_dir in events_dir.iterdir():
            if not year_dir.is_dir():
                continue
            
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                
                for file_path in month_dir.iterdir():
                    if file_path.is_file():
                        # Get file modification time
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if mod_time < cutoff_date:
                            file_path.unlink()
                            deleted_count += 1
                            print(f"   Deleted: {file_path.name}")
                        elif mod_time < compress_cutoff and not file_path.name.endswith('.gz'):
                            # Compress old files
                            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                            
                            with open(file_path, 'rb') as f_in:
                                with gzip.open(compressed_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            
                            file_path.unlink()
                            compressed_count += 1
                            print(f"   Compressed: {file_path.name}")
    
    # Clean up old reports
    print(f"\\n📄 Cleaning old reports...")
    
    reports_dir = base_path / "reports"
    if reports_dir.exists():
        for file_path in reports_dir.iterdir():
            if file_path.is_file():
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time < cutoff_date:
                    file_path.unlink()
                    print(f"   Deleted report: {file_path.name}")
    
    print(f"\\n✅ Cleanup completed:")
    print(f"   Files deleted: {deleted_count}")
    print(f"   Files compressed: {compressed_count}")

if __name__ == "__main__":
    asyncio.run(cleanup_audit_system())
'''
        
        cleanup_script_file = self.audit_dir / "scripts" / "cleanup.py"
        async with aiofiles.open(cleanup_script_file, 'w') as f:
            await f.write(cleanup_script)
        
        print(f"   ✅ Created: {cleanup_script_file.relative_to(self.app_root)}")
    
    async def generate_documentation(self):
        """Generate comprehensive documentation"""
        print("\n📚 Generating documentation...")
        
        readme_content = '''# Audit System Documentation

## Overview
This is a comprehensive file-based audit system designed to capture, store, and analyze authentication events and security incidents.

## Directory Structure
```
essentials/audit/
├── events/           # Event storage organized by year/month
├── indexes/          # Search indexes for fast querying
├── archives/         # Archived old data
├── backups/          # System backups
├── reports/          # Generated reports and exports
├── temp/             # Temporary files
├── incidents/        # Security incidents
├── config/           # Configuration files
├── scripts/          # Utility scripts
└── logs/             # System logs
```

## Storage Format
Events are stored in JSONL (JSON Lines) format with daily rotation. Files are automatically compressed after 7 days and deleted after 365 days (configurable).

## Key Features
- **Real-time Risk Assessment**: Automatic calculation of risk scores
- **File-based Storage**: Persistent storage with compression and archival
- **Integration Support**: Azure AD, Okta, ADFS webhooks
- **Advanced Analytics**: Comprehensive reporting and visualization
- **Suspicious Activity Detection**: Pattern-based threat detection
- **Automated Maintenance**: Background cleanup and optimization

## Configuration Files

### audit_config.json
Main configuration for the audit system including storage settings, risk assessment parameters, and integration options.

### risk_rules.json
Detailed rules for risk assessment including geographic, temporal, device, and behavioral factors.

### identity_providers.json
Configuration for identity provider integrations including field mappings and webhook endpoints.

## Utility Scripts

### analyze_audit_data.py
Run comprehensive analysis on stored audit data:
```bash
python scripts/analyze_audit_data.py [days]
```

### daily_report.py
Generate daily summary reports:
```bash
python scripts/daily_report.py
```

### export_data.py
Export audit data in various formats:
```bash
python scripts/export_data.py --days 30 --format csv
```

### health_check.py
Monitor system health and performance:
```bash
python scripts/health_check.py
```

### cleanup.py
Clean up old files and maintain the system:
```bash
python scripts/cleanup.py
```

## API Integration

### FastAPI Router
The audit router is available at `/api/v1/audit/` and provides:
- Event creation and bulk processing
- Advanced querying and filtering
- Risk assessment and suspicious activity detection
- Data export and reporting
- Storage system information

### Identity Provider Webhooks
- Azure AD: `/api/v1/audit/integrations/azure-ad`
- Okta: `/api/v1/audit/integrations/okta`
- ADFS: `/api/v1/audit/integrations/adfs`

## Event Schema
Events are stored with the following key fields:
- `event_id`: Unique identifier
- `timestamp`: Event timestamp
- `event_type`: Type of event (authentication, etc.)
- `user_id`: User identifier
- `result`: Event result (success, failure, etc.)
- `source_ip`: Source IP address
- `risk_assessment`: Risk analysis data
- `auth_details`: Authentication-specific details
- `device_info`: Device information
- `geographic_info`: Location data

## Risk Assessment
The system automatically calculates risk scores based on:
- **Geographic Risk** (25 points): New or unusual locations
- **Temporal Risk** (15 points): Access outside business hours
- **Device Risk** (20 points): New or untrusted devices
- **Behavioral Risk** (30 points): Failed attempts, high velocity

Risk levels: Low (0-29), Medium (30-49), High (50-69), Critical (70+)

## Monitoring and Alerts
The system provides:
- Real-time high-risk event processing
- Suspicious activity pattern detection
- System health monitoring
- Automated incident creation
- Performance metrics tracking

## Backup and Recovery
- Automated monthly backups
- File compression for storage efficiency
- Configurable retention policies
- Data export capabilities for migration

## Security Considerations
- Encrypt sensitive audit data
- Implement proper access controls
- Monitor audit system health
- Regular backup verification
- Compliance with data retention policies

## Getting Started

1. **Setup**: Run the setup script to initialize the system
2. **Configuration**: Modify config files as needed
3. **Integration**: Set up identity provider webhooks
4. **Monitoring**: Schedule health checks and daily reports
5. **Analysis**: Use utility scripts for data analysis

## Support
For issues and questions, check the logs in the `logs/` directory and run the health check script for system status.
'''
        
        readme_file = self.audit_dir / "README.md"
        async with aiofiles.open(readme_file, 'w') as f:
            await f.write(readme_content)
        
        print(f"   ✅ Created: {readme_file.relative_to(self.app_root)}")
        
        # Create quick start guide
        quickstart_content = '''# Quick Start Guide

## 1. Verify Setup
```bash
# Check if system is properly initialized
python essentials/audit/scripts/health_check.py
```

## 2. Test with Sample Data
The system includes sample data. Analyze it:
```bash
# Run analysis on sample data
python essentials/audit/scripts/analyze_audit_data.py 1
```

## 3. Start Your FastAPI Server
```bash
# Start the server with audit router
python main.py
```

## 4. Test API Endpoints
```bash
# Check audit system status
curl http://localhost:8001/api/v1/audit/

# Get sample events
curl http://localhost:8001/api/v1/audit/events

# View suspicious activity
curl http://localhost:8001/api/v1/audit/suspicious-activity
```

## 5. Send Test Event
```bash
curl -X POST http://localhost:8001/api/v1/audit/events \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_type": "authentication",
    "user_id": "test.user@company.com",
    "action": "login",
    "result": "failure",
    "source_ip": "192.168.1.200",
    "auth_details": {
      "identity_provider": "TestSystem",
      "failure_reason": "Invalid password"
    }
  }'
```

## 6. Generate Reports
```bash
# Generate daily report
python essentials/audit/scripts/daily_report.py

# Export data to CSV
python essentials/audit/scripts/export_data.py --days 7 --format csv
```

## 7. Monitor System
```bash
# Schedule daily health checks (example crontab entry)
# 0 9 * * * /usr/bin/python3 /path/to/essentials/audit/scripts/health_check.py

# Schedule daily reports
# 0 8 * * * /usr/bin/python3 /path/to/essentials/audit/scripts/daily_report.py

# Schedule weekly cleanup
# 0 2 * * 0 /usr/bin/python3 /path/to/essentials/audit/scripts/cleanup.py
```

## Next Steps
- Configure identity provider integrations
- Set up real-time alerting
- Customize risk assessment rules
- Implement automated incident response
'''
        
        quickstart_file = self.audit_dir / "QUICKSTART.md"
        async with aiofiles.open(quickstart_file, 'w') as f:
            await f.write(quickstart_content)
        
        print(f"   ✅ Created: {quickstart_file.relative_to(self.app_root)}")

# =================== INTEGRATION EXAMPLE ===================

async def integration_example():
    """Example of how to integrate the audit system with your application"""
    print("\n🔗 Integration Example")
    print("=" * 30)
    
    # Example: Update your main.py to include the audit router
    main_py_example = '''
# main.py - Updated with audit router

from fastapi import FastAPI
from routers import audit  # Import the updated audit router

app = FastAPI(title="Application with Enhanced Audit System")

# Include the audit router
app.include_router(
    audit.router, 
    prefix="/api/v1/audit", 
    tags=["audit", "security"]
)

# Your existing routers...
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])

@app.get("/")
async def root():
    return {
        "message": "Application with Enhanced Audit System",
        "audit_endpoint": "/api/v1/audit/",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
    
    print("📝 Update your main.py with:")
    print(main_py_example)
    
    # Example: How to log events programmatically
    logging_example = '''
# Example: How to log authentication events in your auth router

import aiohttp
from datetime import datetime

async def log_authentication_event(user_id: str, result: str, source_ip: str, details: dict = None):
    """Log authentication event to audit system"""
    
    event = {
        "event_type": "authentication",
        "user_id": user_id,
        "action": "login",
        "result": result,
        "source_ip": source_ip,
        "timestamp": datetime.utcnow().isoformat(),
        "auth_details": details or {},
        "tags": ["programmatic", "auth_router"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8001/api/v1/audit/events",
                json=event
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Audit event logged: {result['event_id']}")
                else:
                    print(f"Failed to log audit event: {response.status}")
    except Exception as e:
        print(f"Error logging audit event: {e}")

# Usage in your authentication endpoint:
@auth_router.post("/login")
async def login(credentials: UserCredentials, request: Request):
    # Your authentication logic...
    
    if authentication_successful:
        await log_authentication_event(
            user_id=credentials.username,
            result="success",
            source_ip=request.client.host,
            details={"auth_method": "password", "mfa_used": True}
        )
    else:
        await log_authentication_event(
            user_id=credentials.username,
            result="failure",
            source_ip=request.client.host,
            details={"failure_reason": "Invalid credentials"}
        )
'''
    
    print("\n📝 Example authentication logging:")
    print(logging_example)

# =================== MAIN SETUP FUNCTION ===================

async def main():
    """Main setup function"""
    setup = AuditSystemSetup()
    
    try:
        await setup.setup_complete_system()
        await integration_example()
        
        print("\n" + "="*60)
        print("🎉 AUDIT SYSTEM SETUP COMPLETE!")
        print("="*60)
        
        print("\n📁 Directory Structure Created:")
        print("   essentials/audit/")
        print("   ├── events/           # Event storage")
        print("   ├── reports/          # Analysis reports")
        print("   ├── scripts/          # Utility scripts")
        print("   ├── config/           # Configuration files")
        print("   └── README.md         # Documentation")
        
        print("\n🚀 Next Steps:")
        print("   1. Update your routers/audit.py with the enhanced version")
        print("   2. Test with: python essentials/audit/scripts/health_check.py")
        print("   3. Start your FastAPI server: python main.py")
        print("   4. Visit: http://localhost:8001/api/v1/audit/")
        print("   5. Check documentation: essentials/audit/README.md")
        
        print("\n📊 Sample Data Included:")
        print("   - 3 sample authentication events")
        print("   - Various risk levels (low, medium, critical)")
        print("   - Test with: python essentials/audit/scripts/analyze_audit_data.py 1")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)