# File Deployment Instructions

## Required Files to Deploy:

1. **app_data.js** → `C:\Users\AjayPillai\application_auto_discoverer\static\ui\js\app_data.js`
   - Enhanced version that loads from `/templates/activnet_data.json`
   - Automatically refreshes every minute
   - Handles web application directory structure

2. **activnet_file_processor.py** → `C:\Users\AjayPillai\application_auto_discoverer\activnet_file_processor.py`
   - Main file processing system
   - Monitors data_staging/ folder
   - Appends to master Excel file
   - Updates JSON data file

3. **HTML Files** (user provided)
   - index.html → templates/ or static/
   - topology.html → templates/ or static/

4. **CSS Files** (user provided) 
   - topology.css → `C:\Users\AjayPillai\application_auto_discoverer\static\ui\css/`
   - Any other stylesheets

5. **Additional JS Files** (user provided)
   - topology.js → `C:\Users\AjayPillai\application_auto_discoverer\static\ui\js/`
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
