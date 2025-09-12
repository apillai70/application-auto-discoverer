# Comprehensive Logging System Deployment Guide

## Overview
This guide covers deploying the complete comprehensive logging system that captures:
- ALL API endpoints from uvicorn/FastAPI
- ALL frontend user interactions
- Advanced log classification and categorization  
- ServiceNow incident management integration
- Role-based log access control
- Automated log lifecycle management

## Quick Start

### 1. Run Setup Script
```bash
python setup_comprehensive_logging.py
```

### 2. Update Your Main Application
Replace your main.py with:
```bash
cp enhanced_main_with_comprehensive_logging.py main.py
```

### 3. Configure ServiceNow (Optional)
```bash
# Edit ServiceNow configuration
nano config/servicenow/servicenow_config.yaml

# Set environment variables
export SNOW_API_PASSWORD="your_password"
export SNOW_BASE_URL="https://your-instance.service-now.com"
```

### 4. Start Enhanced Application
```bash
python enhanced_main_with_comprehensive_logging.py
```

### 5. Test Logging System
```bash
# Check system health
curl http://localhost:8001/api/v1/logs/system/health

# Query logs
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/api/v1/logs/query

# View statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/api/v1/logs/statistics
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Middleware     │───▶│ Comprehensive   │
│   Logging       │    │   Layer          │    │ Logging System  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   Uvicorn       │───▶│   Log            │             │
│   Interception  │    │   Classification │◀────────────┘
└─────────────────┘    └──────────────────┘             │
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   File Storage  │◀───│   Access Control │◀────────────┘
│   & Lifecycle   │    │   & Sanitization │             │
└─────────────────┘    └──────────────────┘             │
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   ServiceNow    │◀───│   Incident       │◀────────────┘
│   Integration   │    │   Management     │
└─────────────────┘    └──────────────────┘
```

## Features Included

### ✅ Request/Response Logging
- Captures ALL FastAPI endpoints automatically
- Request/response timing and status codes
- Request body and headers (sanitized)
- User context and authentication info
- IP addresses and user agents

### ✅ Frontend Activity Tracking
- User interactions (clicks, form submissions)
- Page navigation and performance metrics
- JavaScript errors and exceptions
- API call timing and success rates
- Security violation detection

### ✅ Advanced Classification
- Automatic log level detection (TRACE to EMERGENCY)
- Source identification (API, Frontend, System, etc.)
- Log type categorization (Request, Error, Security, etc.)
- Sensitive data detection and masking
- PII identification and protection

### ✅ Incident Management
- Automatic incident detection based on rules
- Log correlation within time windows
- ServiceNow ticket creation
- Priority and assignment group mapping
- Incident tracking and resolution

### ✅ Access Control
- Role-based log access (Admin, Security, User, etc.)
- Log sanitization based on permissions
- Audit trail for log access
- Data retention policies by classification

### ✅ Lifecycle Management
- Automatic log rotation and compression
- Retention policies by log level/type
- Archive and backup capabilities
- Bulk operations (export, delete, tag)

## Configuration Files

### Main Configuration: `config/logging/comprehensive_config.yaml`
Controls all aspects of the logging system including batch processing, storage, and feature flags.

### ServiceNow: `config/servicenow/servicenow_config.yaml` 
ServiceNow integration settings, incident mapping, and assignment rules.

### Classification: `config/classification/classification_rules.yaml`
Log classification rules, sensitivity patterns, and incident conditions.

## API Endpoints

### Log Management
- `POST /api/v1/logs/query` - Query logs with filtering
- `GET /api/v1/logs/search` - Full-text search across logs
- `GET /api/v1/logs/{log_id}` - Get detailed log information
- `GET /api/v1/logs/statistics` - Get log statistics and analytics

### Incident Management  
- `POST /api/v1/logs/incidents/create` - Create manual incident
- `GET /api/v1/logs/incidents` - List incidents and tickets
- `GET /api/v1/logs/incidents/{incident_id}` - Get incident details

### System Management
- `GET /api/v1/logs/system/health` - System health status
- `GET /api/v1/logs/system/configuration` - Current configuration
- `PUT /api/v1/logs/retention` - Update log retention policies
- `POST /api/v1/logs/bulk-action` - Bulk operations on logs

## Directory Structure
```
project_root/
├── essentials/
│   ├── logs/           # All application logs by category
│   └── audit/          # Enhanced audit storage
├── config/
│   ├── logging/        # Logging system configuration
│   ├── servicenow/     # ServiceNow integration config
│   └── classification/ # Log classification rules
├── middleware/         # Logging middleware components
├── services/           # Core logging services
├── routers/           # API routers including logging router
└── results/           # Exported logs and reports
```

## Monitoring and Maintenance

### Health Monitoring
```bash
# Check overall system health
curl http://localhost:8001/api/v1/logs/system/health

# Monitor log statistics
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/api/v1/logs/statistics?days=1
```

### Log Maintenance
```bash
# Archive old logs
curl -X POST -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/api/v1/logs/bulk-action \
     -d '{"action": "archive", "log_ids": ["..."]}'

# Export logs for compliance
curl -X POST -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/api/v1/logs/bulk-action \
     -d '{"action": "export", "parameters": {"format": "json"}}'
```

### ServiceNow Integration Monitoring
```bash
# Check ServiceNow connection
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/api/v1/logs/system/configuration

# List created incidents
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8001/api/v1/logs/incidents?days=30
```

## Troubleshooting

### Common Issues

**1. Logs not appearing**
- Check middleware is properly configured
- Verify comprehensive logging system is initialized
- Check file permissions on essentials/logs directory

**2. ServiceNow integration failing**
- Verify network connectivity to ServiceNow instance
- Check API credentials and permissions
- Review rate limiting settings

**3. High memory usage**
- Adjust batch_size and batch_timeout in configuration
- Enable log compression and archival
- Check log retention policies

**4. Access denied errors**
- Verify user roles and permissions
- Check log access level classifications
- Review authentication token validity

### Debug Mode
Enable debug logging by setting log level to DEBUG in configuration:
```yaml
comprehensive_logging:
  log_level: "DEBUG"
```

## Security Considerations

1. **Sensitive Data**: All passwords, tokens, and PII are automatically detected and masked
2. **Access Control**: Role-based access ensures users only see appropriate logs
3. **Audit Trail**: All log access is tracked and auditable
4. **Data Retention**: Sensitive logs are retained longer for compliance
5. **Encryption**: Consider encrypting log files at rest in production

## Performance Optimization

1. **Batch Processing**: Logs are processed in batches for efficiency
2. **Compression**: Old logs are automatically compressed
3. **Indexing**: Search indexes are maintained for fast queries
4. **Archival**: Old logs are archived to reduce active storage
5. **Caching**: Frequently accessed logs are cached in memory

## Production Deployment

1. **Environment Variables**: Use environment variables for sensitive configuration
2. **TLS/SSL**: Enable HTTPS for all API endpoints
3. **Load Balancing**: Consider load balancing for high-volume environments
4. **Monitoring**: Set up monitoring for log processing rates and errors
5. **Backup**: Implement backup strategies for log data
6. **Compliance**: Ensure configuration meets regulatory requirements

For additional support, refer to the specific setup guides:
- SERVICENOW_SETUP_GUIDE.md
- API documentation at /docs when running
