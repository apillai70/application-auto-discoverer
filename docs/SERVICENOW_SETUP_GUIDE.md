# ServiceNow Integration Setup Guide

## Prerequisites
1. ServiceNow instance with API access
2. ServiceNow user account with incident table permissions
3. Network connectivity to ServiceNow instance

## Configuration Steps

### 1. Create ServiceNow API User
```
- Login to ServiceNow as admin
- Navigate to User Administration > Users
- Create new user with incident table read/write permissions
- Generate API credentials
```

### 2. Configure ServiceNow Settings
Edit `config/servicenow/servicenow_config.yaml`:

```yaml
servicenow:
  enabled: true
  base_url: "https://your-instance.service-now.com"
  username: "api_user"
  password: "api_password"  # Use environment variable: SNOW_API_PASSWORD
  table: "incident"
  max_tickets_per_hour: 10
```

### 3. Set Environment Variables
```bash
export SNOW_API_PASSWORD="your_secure_password"
export SNOW_BASE_URL="https://your-instance.service-now.com"
```

### 4. Test ServiceNow Connection
```python
python -c "
from services.comprehensive_logging_system import ServiceNowIntegration
import asyncio

config = {
    'enabled': True,
    'base_url': 'https://your-instance.service-now.com',
    'username': 'api_user',
    'password': 'api_password'
}

snow = ServiceNowIntegration(config)
print('ServiceNow integration configured successfully')
"
```

### 5. Incident Creation Flow
1. Log entries are classified automatically
2. Critical/Alert level logs trigger incident detection
3. Related logs are correlated within 15-minute window
4. ServiceNow incident is created automatically
5. Log entries are updated with ticket ID

### 6. Incident Priority Mapping
- EMERGENCY/ALERT logs → Priority 1 (Critical)
- CRITICAL logs → Priority 2 (High)  
- ERROR logs → Priority 3 (Moderate)
- WARNING logs → Priority 4 (Low)

### 7. Assignment Group Logic
- Security logs → Security Team
- Database logs → Database Team
- Network logs → Network Team
- API logs → Application Team
- Default → IT Support

## Testing
Create test incident:
```bash
curl -X POST "http://localhost:8001/api/v1/logs/incidents/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Incident",
    "description": "Test incident from logging system",
    "severity": "SEV3_MODERATE",
    "log_ids": ["test-log-id"]
  }'
```

## Monitoring
- Check incident creation status: `/api/v1/logs/incidents`
- Monitor ServiceNow integration health: `/api/v1/logs/system/health`
- View incident statistics: `/api/v1/logs/statistics`
