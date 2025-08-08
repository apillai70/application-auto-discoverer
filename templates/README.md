# Web Application Templates and Data

This directory contains:
- `activnet_data.json` - Primary JSON data file for web application
- HTML templates (if using a web framework)

## Data Flow
1. File processor transforms data from data_staging/
2. Updates activnet_data.json with latest application data
3. Web application automatically refreshes from this file
4. Updates happen every minute automatically
