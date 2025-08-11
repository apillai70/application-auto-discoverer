# docs/audit_system.md - Documentation

AUDIT_SYSTEM_DOCS = """
# Enhanced Audit System Documentation

## Overview
The Enhanced Audit System provides comprehensive authentication failure logging, risk assessment, and suspicious activity detection for your FastAPI application.

## Features
- **Real-time Risk Assessment**: Automatically calculates risk scores based on multiple factors
- **Authentication Integration**: Direct integration with Azure AD, Okta, and ADFS
- **Suspicious Activity Detection**: Identifies patterns indicating potential security threats
- **Bulk Processing**: Handles high-volume audit data efficiently
- **Advanced Querying**: Flexible filtering and search capabilities
- **User Risk Profiling**: Tracks user behavior patterns over time

## Quick Start

### 1. Basic Setup
```python
from routers.audit import router as audit_router
app.include_router(audit_router, prefix="/api/v1/audit", tags=["audit"])
```

### 2. Log Authentication Event
```python
import aiohttp

event = {
    "event_type": "authentication",
    "user_id": "user@company.com",
    "action": "login",
    "result": "failure",
    "source_ip": "192.168.1.100",
    "auth_details": {
        "identity_provider": "AzureAD",
        "failure_reason": "Invalid password"
    }
}

async with aiohttp.ClientSession() as session:
    async with session.post("http://localhost:8001/api/v1/audit/events", json=event) as response:
        result = await response.json()
        print(f"Event logged: {result['event_id']}")
```

### 3. Query Audit Events
```python
query = {
    "start_date": "2024-01-01T00:00:00Z",
    "event_types": ["authentication"],
    "results": ["failure"],
    "limit": 100
}

async with session.post("http://localhost:8001/api/v1/audit/events/query", json=query) as response:
    events = await response.json()
    print(f"Found {events['total_count']} events")
```

## Risk Assessment

The system automatically calculates risk scores based on:

- **Geographic Risk** (25 points): New or unusual locations
- **Temporal Risk** (15 points): Access outside business hours
- **Device Risk** (20 points): New or untrusted devices
- **Behavioral Risk** (30 points): Failed attempts, high velocity

Risk levels:
- **Low**: 0-29 points
- **Medium**: 30-49 points  
- **High**: 50-69 points
- **Critical**: 70+ points

## Integration Examples

### Azure AD Integration
```python
azure_event = {
    "userPrincipalName": "user@company.com",
    "resultType": "50126",  # Invalid credentials
    "ipAddress": "203.0.113.100",
    "failureReason": "Invalid username or password"
}

await session.post("http://localhost:8001/api/v1/audit/integrations/azure-ad", json=azure_event)
```

### Okta Integration
```python
okta_event = {
    "eventType": "user.authentication.auth_via_mfa",
    "actor": {"alternateId": "user@company.com"},
    "outcome": {"result": "FAILURE", "reason": "VERIFICATION_ERROR"},
    "client": {"ipAddress": "203.0.113.100"}
}

await session.post("http://localhost:8001/api/v1/audit/integrations/okta", json=okta_event)
```

## Configuration

Set environment variables:
```bash
export AUDIT_ENABLE_RISK_ASSESSMENT=true
export AUDIT_AZURE_AD_INTEGRATION=true
export AUDIT_OKTA_INTEGRATION=true
export AUDIT_ADFS_INTEGRATION=true
export AUDIT_SIEM_ENABLED=false
```

## API Endpoints

- `GET /api/v1/audit/` - System overview
- `POST /api/v1/audit/events` - Create audit event
- `POST /api/v1/audit/events/bulk` - Bulk event creation
- `GET /api/v1/audit/events` - Get events with basic filtering
- `POST /api/v1/audit/events/query` - Advanced event querying
- `GET /api/v1/audit/summary` - Audit summary and statistics
- `GET /api/v1/audit/risk-profiles/{user_id}` - User risk profile
- `GET /api/v1/audit/suspicious-activity` - Suspicious activity report
- `POST /api/v1/audit/integrations/azure-ad` - Azure AD integration
- `POST /api/v1/audit/integrations/okta` - Okta integration
- `POST /api/v1/audit/integrations/adfs` - ADFS integration

## Monitoring

Monitor key metrics:
- Failed authentication attempts per hour
- High-risk events per day
- Geographic distribution of logins
- Top users by failed attempts
- Suspicious IP addresses

## Security Considerations

- Encrypt sensitive audit data
- Implement proper access controls
- Monitor audit system health
- Regular backup of audit logs
- Compliance with data retention policies
"""

print("📋 Enhanced Audit System Configuration Complete!")
print("\nNext steps:")
print("1. Update your main.py to include the audit router")
print("2. Run the demo script to test functionality")
print("3. Configure integration endpoints for your identity providers")
print("4. Set up monitoring and alerting")
print("\nFor full documentation, see the generated docs above.")