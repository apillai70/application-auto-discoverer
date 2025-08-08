#!/usr/bin/env python3
"""
Manual JSON data file creator for ACTIVnet web application
Run this if the processor didn't create the JSON file
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys

def create_json_from_excel():
    """Create JSON data file from existing Excel file"""
    
    project_root = Path('.')
    excel_file = project_root / "static" / "ui" / "data" / "synthetic_flows_apps_archetype_mapped.xlsx"
    json_file = project_root / "templates" / "activnet_data.json"
    
    # Ensure templates directory exists
    json_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Looking for Excel file: {excel_file}")
    
    if not excel_file.exists():
        print(f"❌ Excel file not found at: {excel_file}")
        print("📋 Available files in static/ui/data/:")
        data_dir