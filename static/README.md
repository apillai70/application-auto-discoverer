# Static Web Application Files

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
