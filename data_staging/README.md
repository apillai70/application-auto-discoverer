# ACTIVnet Data Staging

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
