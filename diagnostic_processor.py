#!/usr/bin/env python3
"""
Diagnostic script to trace ACTIVnet processing step by step
Run this to see exactly where the JSON creation is failing
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib
import traceback

def diagnose_processing():
    """Step through the processing logic with detailed diagnostics"""
    
    print("🔍 ACTIVnet Processing Diagnostic")
    print("=" * 50)
    
    # Setup paths
    project_root = Path('.')
    staging_dir = project_root / "data_staging"
    templates_dir = project_root / "templates" 
    json_file = templates_dir / "activnet_data.json"
    
    print(f"📁 Project root: {project_root.absolute()}")
    print(f"📁 Staging dir: {staging_dir}")
    print(f"📁 Templates dir: {templates_dir}")
    print(f"📄 Target JSON: {json_file}")
    
    # Find files to process
    print(f"\n🔍 Step 1: Looking for files to process...")
    
    existing_files = []
    if staging_dir.exists():
        for f in staging_dir.iterdir():
            if f.is_file() and f.suffix.lower() in ['.csv', '.xlsx', '.xls', '.json']:
                existing_files.append(f)
                print(f"   📄 Found: {f.name}")
    
    if not existing_files:
        print("❌ No supported files found in staging directory")
        return False
    
    # Process each file
    for file_path in existing_files:
        print(f"\n🔄 Processing: {file_path.name}")
        print("-" * 30)
        
        success = process_file_diagnostic(file_path, json_file)
        if success:
            print(f"✅ Successfully processed {file_path.name}")
        else:
            print(f"❌ Failed to process {file_path.name}")
    
    return True

def process_file_diagnostic(file_path: Path, json_file: Path):
    """Process a single file with detailed diagnostics"""
    
    try:
        # Step 1: Load the file
        print(f"📥 Step 1: Loading file...")
        data = load_file_diagnostic(file_path)
        if data is None:
            print(f"❌ Failed to load file")
            return False
        
        print(f"✅ Loaded {len(data)} rows with columns: {list(data.columns)}")
        
        # Step 2: Validate data
        print(f"\n🔍 Step 2: Validating data format...")
        required_columns = ['src', 'dst', 'protocol']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        print(f"✅ All required columns present")
        
        # Step 3: Check for empty data
        if len(data) == 0:
            print(f"❌ Data file is empty")
            return False
        
        if data['src'].isna().all() or data['dst'].isna().all():
            print(f"❌ Source or destination data is all empty")
            return False
        
        print(f"✅ Data validation passed")
        
        # Step 4: Create hash for duplicate detection
        print(f"\n🔢 Step 3: Calculating data hash...")
        try:
            data_str = data.to_string()
            data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
            print(f"✅ Data hash: {data_hash[:16]}...")
        except Exception as e:
            print(f"❌ Hash calculation failed: {e}")
            return False
        
        # Step 5: Try to create JSON
        print(f"\n📄 Step 4: Creating JSON file...")
        success = create_json_diagnostic(data, file_path.name, json_file)
        
        return success
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"❌ Full traceback:")
        traceback.print_exc()
        return False

def load_file_diagnostic(file_path: Path):
    """Load file with diagnostics"""
    
    try:
        if file_path.suffix.lower() == '.csv':
            print(f"   📊 Loading CSV file...")
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    print(f"   🔄 Trying encoding: {encoding}")
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError as e:
                    print(f"   ❌ {encoding} failed: {e}")
                    continue
            
            # Last resort
            print(f"   🔄 Trying with error handling...")
            return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            print(f"   📊 Loading Excel file...")
            
            # Get sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"   📋 Available sheets: {sheet_names}")
            
            # Find target sheet
            target_sheet = None
            for sheet in sheet_names:
                if any(keyword in sheet.lower() for keyword in ['transformed', 'auto_research', 'processed', 'flows']):
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                target_sheet = sheet_names[0]
            
            print(f"   📋 Using sheet: {target_sheet}")
            return pd.read_excel(file_path, sheet_name=target_sheet)
            
        elif file_path.suffix.lower() == '.json':
            print(f"   📊 Loading JSON file...")
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if isinstance(json_data, list):
                return pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                if 'data' in json_data:
                    return pd.DataFrame(json_data['data'])
                else:
                    return pd.DataFrame([json_data])
                    
    except Exception as e:
        print(f"   ❌ Error loading file: {e}")
        return None

def create_json_diagnostic(data: pd.DataFrame, original_filename: str, json_file: Path):
    """Create JSON file with detailed diagnostics"""
    
    try:
        print(f"   📁 Ensuring templates directory exists...")
        json_file.parent.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Directory: {json_file.parent} (exists: {json_file.parent.exists()})")
        
        print(f"   🔄 Creating application summary...")
        app_summary = create_app_summary_diagnostic(data)
        print(f"   ✅ Created {len(app_summary)} application entries")
        
        print(f"   🔄 Creating port services mapping...")
        port_services = create_port_services_diagnostic(data)
        print(f"   ✅ Created {len(port_services)} port service mappings")
        
        print(f"   🔄 Building JSON data structure...")
        json_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'source_file': original_filename,
                'total_records': len(data),
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat()
            },
            'applications': app_summary,
            'port_services': port_services,
            'summary_stats': {
                'unique_sources': data['src'].nunique() if 'src' in data.columns else 0,
                'unique_destinations': data['dst'].nunique() if 'dst' in data.columns else 0,
                'unique_protocols': data['protocol'].nunique() if 'protocol' in data.columns else 0,
                'unique_ports': data['port'].nunique() if 'port' in data.columns else 0,
                'total_bytes': calculate_total_bytes_safe(data)
            },
            'raw_data_sample': data.head(10).to_dict('records') if len(data) > 0 else []
        }
        
        print(f"   ✅ JSON structure created")
        print(f"   📊 Metadata: {len(json_data['metadata'])} fields")
        print(f"   📊 Applications: {len(json_data['applications'])}")
        print(f"   📊 Port services: {len(json_data['port_services'])}")
        print(f"   📊 Sample records: {len(json_data['raw_data_sample'])}")
        
        print(f"   💾 Writing JSON file to: {json_file}")
        
        # Check if we can write to the directory
        if not os.access(json_file.parent, os.W_OK):
            print(f"   ❌ No write permission to directory: {json_file.parent}")
            return False
        
        # Write the file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
        
        # Verify file was created
        if json_file.exists():
            file_size = json_file.stat().st_size
            print(f"   ✅ JSON file created successfully!")
            print(f"   📊 File size: {file_size:,} bytes")
            print(f"   📊 File path: {json_file.absolute()}")
            
            # Try to read it back to verify it's valid
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                print(f"   ✅ File is valid JSON with {len(test_data)} top-level keys")
                return True
            except Exception as e:
                print(f"   ❌ File exists but is not valid JSON: {e}")
                return False
        else:
            print(f"   ❌ File was not created (unknown reason)")
            return False
            
    except PermissionError as e:
        print(f"   ❌ Permission error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error creating JSON: {e}")
        print(f"   ❌ Full traceback:")
        traceback.print_exc()
        return False

def create_app_summary_diagnostic(data):
    """Create application summary with diagnostics"""
    
    apps = []
    
    if 'application' not in data.columns:
        print(f"   ⚠️  No 'application' column found, creating generic entry")
        return [{
            'id': 'NETWORK_DATA',
            'name': 'Network Data Application',
            'total_records': len(data),
            'complexity': 'medium'
        }]
    
    print(f"   🔄 Processing applications...")
    unique_apps = data['application'].unique()
    print(f"   📊 Found {len(unique_apps)} unique applications: {list(unique_apps)[:5]}...")
    
    for app_name in unique_apps:
        if pd.isna(app_name):
            continue
            
        app_data = data[data['application'] == app_name]
        
        app_info = {
            'id': str(app_name),
            'name': str(app_name),
            'total_records': len(app_data),
            'unique_sources': app_data['src'].nunique() if 'src' in app_data.columns else 0,
            'unique_destinations': app_data['dst'].nunique() if 'dst' in app_data.columns else 0,
            'complexity': 'medium',  # Simplified for diagnostics
            'ports': [],
            'protocols': []
        }
        
        # Safe port extraction
        if 'port' in app_data.columns:
            try:
                ports = [str(p) for p in app_data['port'].dropna().unique() if p]
                app_info['ports'] = sorted(ports)[:10]  # Limit to first 10
            except:
                pass
        
        # Safe protocol extraction
        if 'protocol' in app_data.columns:
            try:
                protocols = [str(p) for p in app_data['protocol'].dropna().unique() if p]
                app_info['protocols'] = sorted(protocols)[:10]  # Limit to first 10
            except:
                pass
        
        apps.append(app_info)
    
    return sorted(apps, key=lambda x: x['total_records'], reverse=True)

def create_port_services_diagnostic(data):
    """Create port services mapping with diagnostics"""
    
    services = {}
    
    for _, row in data.iterrows():
        try:
            port = row.get('port', '')
            protocol = row.get('protocol', 'TCP')
            
            if port and not pd.isna(port):
                key = f"{protocol}:{port}"
                if key not in services:
                    services[key] = {
                        'port': str(port),
                        'protocol': str(protocol),
                        'service': str(row.get('service_definition', 'Unknown Service')),
                        'count': 0
                    }
                services[key]['count'] += 1
        except Exception:
            continue  # Skip problematic rows
    
    return services

def calculate_total_bytes_safe(data):
    """Safely calculate total bytes"""
    try:
        total = 0.0
        if 'bytes_in' in data.columns:
            bytes_in = pd.to_numeric(data['bytes_in'], errors='coerce').sum()
            if not pd.isna(bytes_in):
                total += float(bytes_in)
        
        if 'bytes_out' in data.columns:
            bytes_out = pd.to_numeric(data['bytes_out'], errors='coerce').sum()
            if not pd.isna(bytes_out):
                total += float(bytes_out)
        
        return total
    except Exception:
        return 0.0

if __name__ == "__main__":
    print("🚀 Starting ACTIVnet Processing Diagnostics")
    
    success = diagnose_processing()
    
    if success:
        print(f"\n✅ Diagnostic completed")
    else:
        print(f"\n❌ Diagnostic failed")
    
    # Check final file status
    json_file = Path('./templates/activnet_data.json')
    print(f"\n📋 Final Status:")
    print(f"   JSON file exists: {json_file.exists()}")
    if json_file.exists():
        print(f"   JSON file size: {json_file.stat().st_size:,} bytes")
        print(f"   JSON file path: {json_file.absolute()}")