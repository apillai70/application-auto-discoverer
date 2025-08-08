#!/usr/bin/env python3
# ACTIVnet File Processor Startup

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(__file__).parent
os.chdir(project_root)

print("🎯 Starting ACTIVnet File Processing System")
print(f"📁 Project root: {project_root}")
print(f"📂 Monitoring: {project_root / 'data_staging'}")
print(f"📊 Master file: {project_root / 'static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx'}")
print(f"🌐 JSON data: {project_root / 'templates/activnet_data.json'}")
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
    print("\n🛑 Stopped by user")
    sys.exit(0)
