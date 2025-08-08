#!/usr/bin/env python3
"""
ACTIVnet Web Application Structure Setup and Deployment Script
Creates the complete directory structure for web application integration
"""

import os
import json
from pathlib import Path
import shutil
import argparse
from datetime import datetime

class WebApplicationSetup:
    """
    Setup and deployment helper for the ACTIVnet web application integration
    """
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        
        # Web application directory structure
        self.static_dir = self.project_root / "static"
        self.static_ui_dir = self.static_dir / "ui"
        self.static_js_dir = self.static_ui_dir / "js"
        self.static_css_dir = self.static_ui_dir / "css"
        self.static_data_dir = self.static_ui_dir / "data"
        self.templates_dir = self.project_root / "templates"
        
        # Staging directories
        self.staging_dir = self.project_root / "data_staging"
        self.processed_dir = self.staging_dir / "processed"
        self.failed_dir = self.staging_dir / "failed"
        
        # Key files
        self.master_excel_file = self.static_data_dir / "synthetic_flows_apps_archetype_mapped.xlsx"
        self.json_data_file = self.templates_dir / "activnet_data.json"
        self.app_data_js_file = self.static_js_dir / "app_data.js"
        
    def create_directory_structure(self):
        """Create the complete web application directory structure"""
        print("📁 Creating web application directory structure...")
        
        # Create all directories
        directories = [
            self.static_dir,
            self.static_ui_dir,
            self.static_js_dir,
            self.static_css_dir,
            self.static_data_dir,
            self.templates_dir,
            self.staging_dir,
            self.processed_dir,
            self.failed_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {directory.relative_to(self.project_root)}")
        
        # Create README files
        self.create_readme_files()
        
        # Create sample files
        self.create_sample_files()
        
        print(f"📂 Web application structure created at: {self.project_root}")
    
    def create_readme_files(self):
        """Create informative README files in each directory"""
        
        # Main project README
        main_readme = f"""# ACTIVnet Web Application Integration

This project integrates ACTIVnet data processing with a web application interface.

## Directory Structure

### Web Application Files
- `static/ui/js/app_data.js` - Main data management JavaScript
- `static/ui/css/` - CSS stylesheets  
- `static/ui/data/` - Processed data files for web consumption
- `templates/` - JSON data files for web application

### Data Processing
- `data_staging/` - Drop folder for new data files
- `data_staging/processed/` - Successfully processed files
- `data_staging/failed/` - Failed processing attempts

### Key Files
- `{self.master_excel_file.name}` - Master Excel file (appended with new data)
- `{self.json_data_file.name}` - JSON data for web application
- `activnet_file_processor.py` - File processing system

## Usage

1. Start the file processor:
   ```bash
   python activnet_file_processor.py
   ```

2. Drop data files in `data_staging/`

3. Serve the web application:
   ```bash
   python -m http.server 8000
   ```

4. Open browser to `http://localhost:8000`

## Features

- File-name agnostic processing
- Automatic duplicate detection
- Real-time web application updates
- Appending to master Excel file
- Comprehensive port service research
"""
        
        with open(self.project_root / "README.md", "w", encoding='utf-8') as f:
            f.write(main_readme)
        
        # Static directory README
        static_readme = """# Static Web Application Files

This directory contains all static files for the web application.

## Structure
- `ui/js/` - JavaScript files including app_data.js
- `ui/css/` - CSS stylesheets
- `ui/data/` - Processed data files (Excel, CSV)

## Key Files
- `ui/js/app_data.js` - Main data management and integration
- `ui/data/synthetic_flows_apps_archetype_mapped.xlsx` - Master data file

The web application automatically loads data from:
1. `/templates/activnet_data.json` (primary)
2. `/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx` (fallback)
"""
        
        with open(self.static_dir / "README.md", "w", encoding='utf-8') as f:
            f.write(static_readme)
        
        # Templates directory README
        templates_readme = """# Web Application Templates and Data

This directory contains:
- `activnet_data.json` - Primary JSON data file for web application
- HTML templates (if using a web framework)

## Data Flow
1. File processor transforms data from data_staging/
2. Updates activnet_data.json with latest application data
3. Web application automatically refreshes from this file
4. Updates happen every minute automatically
"""
        
        with open(self.templates_dir / "README.md", "w", encoding='utf-8') as f:
            f.write(templates_readme)
        
        # Data staging README
        staging_readme = """# ACTIVnet Data Staging

Drop ACTIVnet data files of any name here for automatic processing.

## Supported Formats
- CSV files (.csv)
- Excel files (.xlsx, .xls)
- JSON files (.json)

## Processing Flow
1. Drop file in this folder
2. System detects and processes automatically
3. Successful files -> `processed/`
4. Failed files -> `failed/`
5. Master Excel file updated at `/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx`
6. JSON data updated at `/templates/activnet_data.json`
7. Web application refreshes automatically

## Features
- File name agnostic (any name works)
- Automatic duplicate detection
- Real-time processing
- Comprehensive logging
"""
        
        with open(self.staging_dir / "README.md", "w", encoding='utf-8') as f:
            f.write(staging_readme)
        
        # Data staging README with ASCII-safe arrows
        staging_readme = """# ACTIVnet Data Staging

Drop ACTIVnet data files of any name here for automatic processing.

## Supported Formats
- CSV files (.csv)
- Excel files (.xlsx, .xls)
- JSON files (.json)

## Processing Flow
1. Drop file in this folder
2. System detects and processes automatically
3. Successful files -> `processed/`
4. Failed files -> `failed/`
5. Master Excel file updated at `/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx`
6. JSON data updated at `/templates/activnet_data.json`
7. Web application refreshes automatically

## Features
- File name agnostic (any name works)
- Automatic duplicate detection
- Real-time processing
- Comprehensive logging
"""
    
    def create_sample_files(self):
        """Create sample/template files"""
        print("📊 Creating sample files...")
        
        # Create sample JSON data file
        sample_json_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source_file": "sample_data",
                "total_records": 2,
                "version": "1.0.0",
                "master_file_location": str(self.master_excel_file),
                "last_updated": datetime.now().isoformat()
            },
            "applications": [
                {
                    "id": "SAMPLE_WEB_APP",
                    "name": "Sample Web Application",
                    "total_records": 1,
                    "complexity": "low",
                    "most_common_protocol": "HTTP",
                    "most_common_service": "Web Service",
                    "archetype": "Web Service"
                },
                {
                    "id": "SAMPLE_API",
                    "name": "Sample API Service", 
                    "total_records": 1,
                    "complexity": "medium",
                    "most_common_protocol": "HTTPS",
                    "most_common_service": "REST API",
                    "archetype": "API Service"
                }
            ],
            "port_services": {
                "HTTP:80": {
                    "port": "80",
                    "protocol": "HTTP",
                    "service": "Web Service",
                    "count": 1
                },
                "HTTPS:443": {
                    "port": "443",
                    "protocol": "HTTPS", 
                    "service": "Secure Web Service",
                    "count": 1
                }
            },
            "summary_stats": {
                "unique_sources": 2,
                "unique_destinations": 2,
                "unique_protocols": 2,
                "unique_ports": 2,
                "total_bytes": 4096
            },
            "raw_data_sample": [
                {
                    "src": "10.0.1.100",
                    "dst": "10.0.1.200",
                    "port": "80",
                    "protocol": "HTTP",
                    "application": "SAMPLE_WEB_APP",
                    "service_definition": "Web Service"
                },
                {
                    "src": "10.0.1.101", 
                    "dst": "10.0.1.201",
                    "port": "443",
                    "protocol": "HTTPS",
                    "application": "SAMPLE_API",
                    "service_definition": "REST API"
                }
            ]
        }
        
        if not self.json_data_file.exists():
            with open(self.json_data_file, 'w', encoding='utf-8') as f:
                json.dump(sample_json_data, f, indent=2, default=str)
            print(f"   ✅ Created sample JSON: {self.json_data_file.name}")
        
        # Create sample CSV for staging
        sample_csv_path = self.staging_dir / "sample_data.csv"
        if not sample_csv_path.exists():
            import pandas as pd
            sample_df = pd.DataFrame([
                {
                    "src": "10.0.1.100",
                    "dst": "10.0.1.200", 
                    "port": "80",
                    "protocol": "HTTP",
                    "application": "SAMPLE_WEB_APP",
                    "service_definition": "Web Service",
                    "bytes_in": 1024,
                    "bytes_out": 2048
                }
            ])
            sample_df.to_csv(sample_csv_path, index=False)
            print(f"   ✅ Created sample CSV: {sample_csv_path.name}")
    
    def deploy_application_files(self):
        """Deploy the application JavaScript files"""
        print("🚀 Deploying application files...")
        
        # Note: In actual usage, you would copy the real files here
        # For now, create deployment instructions
        
        deployment_note = f"""# File Deployment Instructions

## Required Files to Deploy:

1. **app_data.js** → `{self.app_data_js_file}`
   - Enhanced version that loads from `/templates/activnet_data.json`
   - Automatically refreshes every minute
   - Handles web application directory structure

2. **activnet_file_processor.py** → `{self.project_root / 'activnet_file_processor.py'}`
   - Main file processing system
   - Monitors data_staging/ folder
   - Appends to master Excel file
   - Updates JSON data file

3. **HTML Files** (user provided)
   - index.html → templates/ or static/
   - topology.html → templates/ or static/

4. **CSS Files** (user provided) 
   - topology.css → `{self.static_css_dir}/`
   - Any other stylesheets

5. **Additional JS Files** (user provided)
   - topology.js → `{self.static_js_dir}/`
   - Any other JavaScript files

## File Paths for Web Application:

### Data Files:
- Primary JSON: `/templates/activnet_data.json`
- Master Excel: `/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx`

### Static Assets:
- JavaScript: `/static/ui/js/`
- CSS: `/static/ui/css/`
- Data: `/static/ui/data/`

### Processing:
- Drop folder: `data_staging/`
- Processed: `data_staging/processed/`
- Failed: `data_staging/failed/`

## Auto-Integration Features:

1. **File Name Agnostic**: Any filename works in data_staging/
2. **Duplicate Prevention**: Same data won't be processed twice
3. **Auto-Append**: New data appends to master Excel file
4. **Real-time Updates**: Web app refreshes automatically
5. **Comprehensive Logging**: Check data_staging/processing.log

## Testing:

1. Start file processor: `python activnet_file_processor.py`
2. Start web server: `python -m http.server 8000`
3. Drop test file in data_staging/
4. Check web application for updates
"""
        
        deployment_file = self.project_root / "DEPLOYMENT_INSTRUCTIONS.md"
        with open(deployment_file, "w", encoding='utf-8') as f:
            f.write(deployment_note)
        
        print(f"   ✅ Created deployment instructions: {deployment_file.name}")
    
    def create_startup_scripts(self):
        """Create startup scripts for easy launching"""
        print("🚀 Creating startup scripts...")
        
        # Python startup script for file processor
        processor_script = f"""#!/usr/bin/env python3
# ACTIVnet File Processor Startup

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(__file__).parent
os.chdir(project_root)

print("🎯 Starting ACTIVnet File Processing System")
print(f"📁 Project root: {{project_root}}")
print(f"📂 Monitoring: {{project_root / 'data_staging'}}")
print(f"📊 Master file: {{project_root / 'static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx'}}")
print(f"🌐 JSON data: {{project_root / 'templates/activnet_data.json'}}")
print()

try:
    from activnet_file_processor import main
    exit_code = main()
    sys.exit(exit_code)
    
except ImportError:
    print("❌ Error: activnet_file_processor.py not found")
    print("Please ensure the file processor script is in the project root")
    sys.exit(1)
    
except KeyboardInterrupt:
    print("\\n🛑 Stopped by user")
    sys.exit(0)
"""
        
        processor_startup = self.project_root / "start_file_processor.py"
        with open(processor_startup, "w", encoding='utf-8') as f:
            f.write(processor_script)
        
        # Make executable on Unix systems
        try:
            os.chmod(processor_startup, 0o755)
        except:
            pass
        
        print(f"   ✅ Created processor startup: {processor_startup.name}")
        
        # Web server startup script
        web_server_script = f"""#!/usr/bin/env python3
# ACTIVnet Web Server Startup

import sys
import os
import http.server
import socketserver
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(__file__).parent
os.chdir(project_root)

PORT = 8000

print("🌐 Starting ACTIVnet Web Server")
print(f"📁 Serving from: {{project_root}}")
print(f"🔗 URL: http://localhost:{{PORT}}")
print(f"📊 Data files:")
print(f"   • JSON: /templates/activnet_data.json")
print(f"   • Excel: /static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx")
print(f"   • JavaScript: /static/ui/js/app_data.js")
print()
print("Press Ctrl+C to stop")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers if needed
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

try:
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"✅ Server started at http://localhost:{{PORT}}")
        httpd.serve_forever()
        
except KeyboardInterrupt:
    print("\\n🛑 Server stopped")
    sys.exit(0)
except Exception as e:
    print(f"❌ Server error: {{e}}")
    sys.exit(1)
"""
        
        web_server_startup = self.project_root / "start_web_server.py"
        with open(web_server_startup, "w", encoding='utf-8') as f:
            f.write(web_server_script)
        
        try:
            os.chmod(web_server_startup, 0o755)
        except:
            pass
        
        print(f"   ✅ Created web server startup: {web_server_startup.name}")
        
        # Combined startup script
        combined_script = f"""#!/usr/bin/env python3
# ACTIVnet Combined Startup (File Processor + Web Server)

import sys
import os
import subprocess
import threading
from pathlib import Path

project_root = Path(__file__).parent
os.chdir(project_root)

def start_file_processor():
    \"\"\"Start the file processor in a separate process\"\"\"
    try:
        subprocess.run([sys.executable, "start_file_processor.py"])
    except Exception as e:
        print(f"File processor error: {{e}}")

def start_web_server():
    \"\"\"Start the web server in a separate process\"\"\"
    try:
        subprocess.run([sys.executable, "start_web_server.py"])
    except Exception as e:
        print(f"Web server error: {{e}}")

if __name__ == "__main__":
    print("🚀 Starting ACTIVnet Complete System")
    print("=" * 50)
    
    # Start file processor in background thread
    processor_thread = threading.Thread(target=start_file_processor, daemon=True)
    processor_thread.start()
    
    # Start web server in main thread  
    start_web_server()
"""
        
        combined_startup = self.project_root / "start_complete_system.py"
        with open(combined_startup, "w", encoding='utf-8') as f:
            f.write(combined_script)
        
        try:
            os.chmod(combined_startup, 0o755)
        except:
            pass
        
        print(f"   ✅ Created combined startup: {combined_startup.name}")
    
    def create_config_file(self):
        """Create configuration file for the system"""
        print("⚙️ Creating configuration file...")
        
        config = {
            "web_application": {
                "static_directory": "static/ui",
                "templates_directory": "templates",
                "data_files": {
                    "json_data": "templates/activnet_data.json",
                    "master_excel": "static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx",
                    "app_data_js": "static/ui/js/app_data.js"
                }
            },
            "data_processing": {
                "staging_directory": "data_staging",
                "processed_directory": "data_staging/processed",
                "failed_directory": "data_staging/failed",
                "auto_refresh_interval": 60000,
                "supported_formats": [".json", ".csv", ".xlsx", ".xls"]
            },
            "features": {
                "file_name_agnostic": True,
                "duplicate_detection": True,
                "auto_append_excel": True,
                "port_research": True,
                "real_time_updates": True,
                "web_integration": True
            },
            "logging": {
                "level": "INFO",
                "file": "data_staging/processing.log",
                "web_access_log": "static/access.log"
            }
        }
        
        config_path = self.project_root / "activnet_config.json"
        with open(config_path, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"   ✅ Created config file: {config_path.name}")
    
    def install_dependencies(self):
        """Install required Python dependencies"""
        print("📦 Installing Python dependencies...")
        
        dependencies = [
            "pandas",
            "openpyxl", 
            "requests",
            "beautifulsoup4",
            "watchdog"
        ]
        
        try:
            import subprocess
            import sys
            
            for dep in dependencies:
                print(f"   Installing {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"   ✅ {dep} installed")
        
        except Exception as e:
            print(f"   ❌ Error installing dependencies: {e}")
            print(f"   Please run manually: pip install {' '.join(dependencies)}")
    
    def run_full_setup(self):
        """Run the complete setup process"""
        print("🎯 ACTIVnet Web Application Setup")
        print("=" * 50)
        
        try:
            # Create directory structure
            self.create_directory_structure()
            print()
            
            # Install dependencies
            self.install_dependencies()
            print()
            
            # Create configuration
            self.create_config_file()
            print()
            
            # Create startup scripts
            self.create_startup_scripts()
            print()
            
            # Deploy application files
            self.deploy_application_files()
            print()
            
            print("🎉 Web Application Setup Complete!")
            print("=" * 40)
            print(f"📁 Project root: {self.project_root}")
            print()
            print("📂 Directory Structure:")
            print(f"   • static/ui/js/app_data.js (main JavaScript)")
            print(f"   • static/ui/css/ (stylesheets)")
            print(f"   • static/ui/data/ (processed data)")
            print(f"   • templates/activnet_data.json (JSON data)")
            print(f"   • data_staging/ (file drop folder)")
            print()
            print("🔗 Key File Paths:")
            print(f"   • Master Excel: {self.master_excel_file}")
            print(f"   • JSON Data: {self.json_data_file}")
            print(f"   • App JavaScript: {self.app_data_js_file}")
            print()
            print("🚀 Next Steps:")
            print("1. Copy your app_data.js to static/ui/js/app_data.js")
            print("2. Copy your HTML files to templates/ or static/")
            print("3. Copy your CSS files to static/ui/css/")
            print("4. Copy activnet_file_processor.py to project root")
            print()
            print("📋 To Start System:")
            print("   Option 1 - File processor only:")
            print("   python start_file_processor.py")
            print()
            print("   Option 2 - Web server only:")
            print("   python start_web_server.py")
            print()
            print("   Option 3 - Complete system:")
            print("   python start_complete_system.py")
            print()
            print("📊 To Test:")
            print("   1. Start the system")
            print("   2. Drop a data file in data_staging/")
            print("   3. Check web application at http://localhost:8000")
            print("   4. Verify data updates automatically")
            print()
            print("📋 Files Created:")
            files_created = [
                "Complete directory structure",
                "Sample JSON data file",
                "Configuration file",
                "Startup scripts (3 options)",
                "Deployment instructions",
                "README files in each directory"
            ]
            for file in files_created:
                print(f"   • {file}")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
    
    def check_system_status(self):
        """Check the current system status"""
        print("📊 ACTIVnet Web Application System Status")
        print("=" * 50)
        
        # Check directory structure
        directories = {
            "Static UI Directory": self.static_ui_dir,
            "JavaScript Directory": self.static_js_dir,
            "Data Directory": self.static_data_dir,
            "Templates Directory": self.templates_dir,
            "Staging Directory": self.staging_dir,
            "Processed Directory": self.processed_dir,
            "Failed Directory": self.failed_dir
        }
        
        print("📁 Directory Structure:")
        for name, directory in directories.items():
            exists = directory.exists()
            file_count = len(list(directory.iterdir())) if exists else 0
            status = "✅" if exists else "❌"
            print(f"{status} {name}: {directory.relative_to(self.project_root)} ({file_count} files)")
        
        # Check key files
        key_files = {
            "JSON Data File": self.json_data_file,
            "Master Excel File": self.master_excel_file,
            "App JavaScript": self.app_data_js_file,
            "Config File": self.project_root / "activnet_config.json",
            "File Processor": self.project_root / "activnet_file_processor.py"
        }
        
        print("\n📄 Key Files:")
        for name, file_path in key_files.items():
            exists = file_path.exists()
            status = "✅" if exists else "❌"
            size = f"({file_path.stat().st_size} bytes)" if exists else "(missing)"
            print(f"{status} {name}: {file_path.relative_to(self.project_root)} {size}")
        
        # Check dependencies
        print("\n📦 Dependencies:")
        dependencies = ["pandas", "openpyxl", "requests", "beautifulsoup4", "watchdog"]
        
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep}: installed")
            except ImportError:
                print(f"❌ {dep}: missing")
        
        print(f"\n🌐 Web Application URLs (when server running):")
        print(f"   • Main: http://localhost:8000/")
        print(f"   • JSON Data: http://localhost:8000/templates/activnet_data.json")
        print(f"   • Excel Data: http://localhost:8000/static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx")

def main():
    parser = argparse.ArgumentParser(description='ACTIVnet Web Application Setup')
    parser.add_argument('--project-root', '-r', default='.',
                       help='Project root directory (default: current directory)')
    parser.add_argument('--setup', '-s', action='store_true',
                       help='Run full setup process')
    parser.add_argument('--status', action='store_true',
                       help='Check system status')
    
    args = parser.parse_args()
    
    setup = WebApplicationSetup(args.project_root)
    
    if args.status:
        setup.check_system_status()
        return
    
    if args.setup:
        setup.run_full_setup()
        return
    
    # Default: run basic setup
    print("🎯 Running basic web application setup...")
    print("(Use --setup for full setup, --status to check system)")
    setup.create_directory_structure()
    print("\n✅ Basic setup complete. Use --setup for full installation.")

if __name__ == "__main__":
    main()