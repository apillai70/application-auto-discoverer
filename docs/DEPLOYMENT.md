# DEPLOYMENT.md
# Deployment Guide

## Production Deployment
### Docker Deployment

#### Prerequisites
- Docker
- Docker Compose

#### Steps
1. Build the Docker image:
```bash
docker build -t application-auto-discoverer .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

### Manual Deployment

#### Prerequisites
- Python 3.8+
- PostgreSQL (optional, SQLite used by default)
- Redis (for background tasks)

#### Steps
1. Set up production environment
2. Configure environment variables
3. Set up database
4. Configure reverse proxy (nginx recommended)
5. Set up process manager (systemd, supervisor, or PM2)

### Environment Configuration

#### Required Environment Variables
```bash
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost/autodiscoverer
SECRET_KEY=your-production-secret-key
```

#### Optional Environment Variables
- `EXTRAHOP_API_KEY`
- `SPLUNK_API_ENDPOINT`
- `DYNATRACE_API_TOKEN`

### Security Considerations
- Use HTTPS in production
- Configure proper CORS settings
- Set up authentication/authorization
- Regular security updates
- Monitor access logs

### Performance Optimization
- Use production ASGI server (Gunicorn + Uvicorn)
- Configure proper worker processes
- Set up Redis for caching
- Database connection pooling
- File storage optimization

### Monitoring and Logging
- Set up application monitoring
- Configure structured logging
- Health check endpoints
- Performance metrics
- Error tracking

### Backup Strategy
- Database backups
- File storage backups
- Configuration backups
- Recovery procedures

### Scaling
- Horizontal scaling considerations
- Load balancing
- Database scaling
- File storage scaling

## Development Deployment

### Local Development
```bash
python main.py
```

### Development with Docker
```bash
docker-compose -f docker-compose.dev.yml up
```

### Testing
```bash
pytest
```

## Troubleshooting
[To be documented]