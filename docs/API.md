# API.md
# Application Auto Discoverer API Documentation

## Overview
This document describes the REST API endpoints for the Application Auto Discoverer system.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently, the API does not require authentication. This will be implemented in future versions.

## Endpoints

### Topology Endpoints
- `POST /topology/analyze` - Start log analysis
- `POST /topology/upload` - Upload log files
- `GET /topology/analysis/{id}/status` - Get analysis status
- `GET /topology/analysis/{id}/results` - Get analysis results

### Integration Endpoints
- `GET /integration/status` - Get integration status
- `POST /integration/configure` - Configure integrations

### Documentation Endpoints
- `POST /documentation/generate` - Generate documentation
- `GET /documentation/templates` - Get documentation templates

### Diagram Endpoints
- `POST /diagram/generate` - Generate network diagrams
- `GET /diagram/types` - Get available diagram types

## Data Models
[To be documented]

## Error Handling
[To be documented]

## Rate Limiting
[To be documented]