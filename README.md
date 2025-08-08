# ACTIVnet Web Application Integration

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
- `synthetic_flows_apps_archetype_mapped.xlsx` - Master Excel file (appended with new data)
- `activnet_data.json` - JSON data for web application
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
