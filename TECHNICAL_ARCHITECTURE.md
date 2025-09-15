# Regions Bank Network Scanning Platform - Technical Architecture
## Comprehensive Technical Design & Implementation Guide

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Regions Bank Network Platform                │
├─────────────────────────────────────────────────────────────────┤
│  Client Layer                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Web UI    │ │  Mobile App │ │  API Client │              │
│  │  (React)    │ │  (Future)   │ │  (External) │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway Layer (FastAPI + Uvicorn)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  REST APIs  │ │ WebSocket   │ │  Middleware │              │
│  │  (v1/v2)    │ │  Real-time  │ │  (CORS,     │              │
│  │             │ │  Updates    │ │   Auth,     │              │
│  │             │ │             │ │   Rate Limit)│              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer (Microservices Architecture)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Network    │ │  Threat     │ │  Data       │              │
│  │  Discovery  │ │  Detection  │ │  Processing │              │
│  │  Service    │ │  Service    │ │  Service    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Diagram    │ │  Report     │ │  Audit      │              │
│  │  Generator  │ │  Generator  │ │  Service    │              │
│  │  Service    │ │  Service    │ │             │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer (Hybrid Storage Architecture)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  File       │ │  Database   │ │  Cache      │              │
│  │  Storage    │ │  (Future)   │ │  (Redis)    │              │
│  │  (Excel,    │ │  (PostgreSQL│ │  (In-Memory)│              │
│  │   JSON)     │ │   /MongoDB) │ │             │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Main Application (main.py)

#### Architecture:
```python
# FastAPI Application Factory
def create_app() -> FastAPI:
    app = FastAPI(
        title="Application Auto-Discovery Platform",
        description="Network scanning and segmentation platform",
        version="2.2.1",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Middleware Stack
    app.add_middleware(CORSMiddleware, ...)
    
    # Router Registration
    app.include_router(network_router, prefix="/api/v1/network")
    app.include_router(security_router, prefix="/api/v1/security")
    
    return app
```

#### Key Features:
- **WebSocket Support**: Real-time updates and communication
- **Error Handling**: Comprehensive error management
- **Health Checks**: System monitoring and status reporting
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

### 2. Network Discovery Service

#### Core Functionality:
```python
class NetworkScanner:
    def __init__(self):
        self.network_utils = NetworkUtils()
        self.discovered_nodes = {}
        self.discovered_connections = []
    
    async def scan_from_logs(self, log_data: List[Dict], source_type: str):
        # Extract nodes and connections from logs
        nodes = await self._extract_nodes_from_logs(log_data, source_type)
        connections = await self._extract_connections_from_logs(log_data, nodes)
        
        # Enhance node information
        enhanced_nodes = await self._enhance_node_information(nodes, log_data)
        
        return {
            "nodes": enhanced_nodes,
            "connections": connections,
            "statistics": self._generate_scan_statistics(enhanced_nodes, connections)
        }
```

#### Capabilities:
- **Log Analysis**: Multi-format log processing
- **Node Discovery**: Automatic network device identification
- **Connection Mapping**: Traffic flow analysis
- **Service Detection**: Port and protocol identification

### 3. Data Processing Pipeline

#### File Processing System:
```python
class FileProcessor:
    def __init__(self, project_root: Path):
        self.staging_dir = project_root / "data_staging"
        self.processed_dir = self.staging_dir / "processed"
        self.failed_dir = self.staging_dir / "failed"
        self.port_researcher = PortResearcher()
    
    def process_file(self, file_path: Path) -> bool:
        # Load and validate data
        data = self.load_data_from_file(file_path)
        data = self.detect_and_transform_raw_data(data, file_path)
        
        # Process and store
        excel_success = self.append_to_master_excel(data, file_path.name)
        self.update_json_data_file(data, file_path.name)
        
        return excel_success
```

#### Data Flow:
```
Raw Data → Validation → Transformation → Classification → Storage
    │           │            │              │            │
    ▼           ▼            ▼              ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  File   │ │  Format │ │  Port   │ │  App    │ │  Master │
│  Load   │ │  Check  │ │ Research│ │  Class  │ │  Excel  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 4. Threat Detection System

#### Security Engine:
```python
class ThreatDetectionService:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.threat_rules = self.load_threat_rules()
        self.response_engine = ResponseEngine()
    
    async def analyze_security_event(self, event: Dict) -> ThreatAssessment:
        # Apply threat detection rules
        threat_score = self.calculate_threat_score(event)
        
        if threat_score > self.config.thresholds.high:
            # Generate alert and response
            alert = await self.create_security_alert(event, threat_score)
            await self.response_engine.execute_response(alert)
        
        return ThreatAssessment(event, threat_score)
```

#### Security Features:
- **Real-time Analysis**: Continuous threat monitoring
- **Rule Engine**: Configurable detection rules
- **Response Actions**: Automated response capabilities
- **Audit Logging**: Comprehensive security event logging

---

## 📊 Data Models

### 1. Network Topology Models

```python
class TopologyNode(BaseModel):
    id: str
    ip_address: str
    hostname: Optional[str] = None
    node_type: NodeType
    services: List[str] = []
    operating_system: Optional[str] = None
    last_seen: datetime
    metadata: Dict[str, Any] = {}

class TopologyEdge(BaseModel):
    id: str
    source_node_id: str
    destination_node_id: str
    connection_type: ConnectionType
    protocols: List[str] = []
    ports: List[int] = []
    traffic_volume: int = 0
    last_seen: datetime
```

### 2. Application Models

```python
class Application(BaseModel):
    id: str
    name: str
    application_type: str
    tier: str
    archetype: str
    owner: str
    dependencies: List[str] = []
    security_classification: str
    compliance_requirements: List[str] = []
    last_updated: datetime

class NetworkService(BaseModel):
    port: int
    protocol: str
    service_name: str
    description: str
    security_risk: str
    compliance_status: str
```

### 3. Security Models

```python
class SecurityAlert(BaseModel):
    id: str
    severity: str
    threat_type: str
    title: str
    description: str
    source_ip: str
    destination_ip: str
    detected_at: datetime
    status: str
    risk_score: float
    confidence_score: float
    mitigation_actions: List[str] = []

class ThreatIntelligence(BaseModel):
    indicator: str
    indicator_type: str
    threat_type: str
    confidence: float
    source: str
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = []
```

---

## 🔌 API Architecture

### 1. REST API Endpoints

#### Network Discovery APIs:
```python
@router.post("/api/v1/network/discover")
async def start_network_discovery(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_auth("network:discover"))
):
    """Start automated network discovery"""
    job_id = await network_service.start_discovery(request, background_tasks)
    return {"job_id": job_id, "status": "started"}

@router.get("/api/v1/network/topology")
async def get_network_topology(
    current_user: dict = Depends(require_auth("network:read"))
):
    """Get current network topology"""
    return await network_service.get_topology()

@router.post("/api/v1/network/scan")
async def trigger_network_scan(
    scan_request: ScanRequest,
    current_user: dict = Depends(require_auth("network:scan"))
):
    """Trigger manual network scan"""
    return await network_service.trigger_scan(scan_request)
```

#### Security APIs:
```python
@router.get("/api/v1/security/alerts")
async def get_security_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_auth("security:read"))
):
    """Get security alerts with filtering"""
    return await security_service.get_alerts(severity, status, limit)

@router.post("/api/v1/security/alerts")
async def create_security_alert(
    alert: SecurityAlertCreate,
    current_user: dict = Depends(require_auth("security:write"))
):
    """Create new security alert"""
    return await security_service.create_alert(alert)

@router.get("/api/v1/security/statistics")
async def get_security_statistics(
    time_range: str = "24h",
    current_user: dict = Depends(require_auth("security:read"))
):
    """Get security statistics and metrics"""
    return await security_service.get_statistics(time_range)
```

### 2. WebSocket APIs

#### Real-time Updates:
```python
@app.websocket("/ws")
async def main_websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_websocket_message(message, websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.websocket("/api/v1/excel/ws")
async def excel_websocket_endpoint(websocket: WebSocket):
    """Excel processing WebSocket endpoint"""
    await websocket_manager.connect(websocket)
    # Handle Excel processing updates
```

---

## 🗄️ Data Storage Architecture

### 1. File-Based Storage

#### Current Implementation:
```
data_staging/
├── processed/           # Successfully processed files
├── failed/             # Failed processing attempts
├── activnet_data.json  # Web application data
└── processing.log      # Processing logs

results/
├── visio/              # Visio diagram exports
├── lucid/              # LucidChart exports
├── document/           # Word document exports
├── excel/              # Excel file exports
└── pdf/                # PDF report exports
```

#### Data Formats:
- **Excel Files**: Master data storage with multiple sheets
- **JSON Files**: API data and web application consumption
- **CSV Files**: Data exchange and import/export
- **Log Files**: System and processing logs

### 2. Future Database Integration

#### PostgreSQL Schema:
```sql
-- Network topology tables
CREATE TABLE network_nodes (
    id UUID PRIMARY KEY,
    ip_address INET NOT NULL,
    hostname VARCHAR(255),
    node_type VARCHAR(50),
    operating_system VARCHAR(100),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE network_connections (
    id UUID PRIMARY KEY,
    source_node_id UUID REFERENCES network_nodes(id),
    destination_node_id UUID REFERENCES network_nodes(id),
    connection_type VARCHAR(50),
    protocols TEXT[],
    ports INTEGER[],
    traffic_volume BIGINT,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Security tables
CREATE TABLE security_alerts (
    id UUID PRIMARY KEY,
    severity VARCHAR(20),
    threat_type VARCHAR(50),
    title VARCHAR(255),
    description TEXT,
    source_ip INET,
    destination_ip INET,
    risk_score DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    status VARCHAR(20),
    detected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔒 Security Architecture

### 1. Authentication & Authorization

#### JWT-Based Authentication:
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

# JWT Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# JWT Authentication
jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    tokenUrl="auth/jwt/login",
)

# User Management
fastapi_users = FastAPIUsers(
    user_db, [jwt_authentication]
)
```

#### Role-Based Access Control:
```python
class Role(Enum):
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    NETWORK_ENGINEER = "network_engineer"
    READONLY_USER = "readonly_user"

class Permission(Enum):
    READ_NETWORK_DATA = "read:network_data"
    WRITE_NETWORK_DATA = "write:network_data"
    MANAGE_USERS = "manage:users"
    VIEW_SECURITY_ALERTS = "view:security_alerts"

# Permission checking decorator
def require_permission(permission: Permission):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check user permissions
            if not current_user.has_permission(permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 2. Data Encryption

#### Encryption at Rest:
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    def __init__(self, password: str, salt: bytes):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

#### Encryption in Transit:
```python
# TLS Configuration
import ssl
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# SSL Context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_context.load_cert_chain("cert.pem", "key.pem")
ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
```

---

## 📈 Performance & Scalability

### 1. Performance Optimization

#### Caching Strategy:
```python
import redis
from functools import wraps

# Redis Cache
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### Database Connection Pooling:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Database Engine with Connection Pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. Horizontal Scaling

#### Load Balancing:
```nginx
# Nginx Configuration
upstream app_servers {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    server_name regions-network-scanner.com;
    
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### Microservices Architecture:
```python
# Service Discovery
from fastapi import FastAPI
from consul import Consul

class ServiceRegistry:
    def __init__(self):
        self.consul = Consul()
    
    def register_service(self, service_name: str, service_address: str, service_port: int):
        self.consul.agent.service.register(
            name=service_name,
            service_id=f"{service_name}-{service_port}",
            address=service_address,
            port=service_port,
            check=consul.Check.http(f"http://{service_address}:{service_port}/health")
        )
```

---

## 🔧 Deployment Architecture

### 1. Container Deployment

#### Docker Configuration:
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose:
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/network_scanner
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=network_scanner
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Kubernetes Deployment

#### Deployment Manifest:
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: network-scanner
spec:
  replicas: 3
  selector:
    matchLabels:
      app: network-scanner
  template:
    metadata:
      labels:
        app: network-scanner
    spec:
      containers:
      - name: network-scanner
        image: regions-bank/network-scanner:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 📊 Monitoring & Observability

### 1. Application Monitoring

#### Metrics Collection:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
PROCESSED_FILES = Counter('files_processed_total', 'Total files processed', ['status'])

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response
```

#### Health Checks:
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "file_system": await check_file_system_health(),
            "external_apis": await check_external_apis_health()
        },
        "metrics": {
            "active_connections": len(websocket_manager.active_connections),
            "processed_files": get_processed_files_count(),
            "memory_usage": get_memory_usage(),
            "cpu_usage": get_cpu_usage()
        }
    }
    
    return health_status
```

### 2. Logging Architecture

#### Structured Logging:
```python
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Security event logging
class SecurityLogger:
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_security_event(self, event_type: str, user_id: str, details: dict):
        self.logger.info(
            "security_event",
            event_type=event_type,
            user_id=user_id,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )
```

---

## 🔄 CI/CD Pipeline

### 1. Continuous Integration

#### GitHub Actions Workflow:
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Run security scan
      run: |
        bandit -r app/
        safety check
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t regions-bank/network-scanner:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker push regions-bank/network-scanner:${{ github.sha }}
```

### 2. Continuous Deployment

#### Deployment Pipeline:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
        kubectl set image deployment/network-scanner network-scanner=regions-bank/network-scanner:${{ github.sha }}
    
    - name: Run smoke tests
      run: |
        pytest tests/smoke/ --base-url https://network-scanner.regionsbank.com
```

---

## 📋 Configuration Management

### 1. Environment Configuration

#### Configuration Classes:
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Network Scanner"
    app_version: str = "2.2.1"
    debug: bool = False
    
    # Database settings
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis settings
    redis_url: str
    redis_password: Optional[str] = None
    
    # Security settings
    secret_key: str
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # Network settings
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["https://regionsbank.com"]
    
    # File processing settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_formats: List[str] = [".csv", ".xlsx", ".xls", ".json"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 2. Feature Flags

#### Feature Toggle System:
```python
class FeatureFlags:
    def __init__(self):
        self.flags = {
            "advanced_threat_detection": False,
            "real_time_processing": True,
            "ai_insights": False,
            "mobile_app": False
        }
    
    def is_enabled(self, flag_name: str) -> bool:
        return self.flags.get(flag_name, False)
    
    def enable(self, flag_name: str):
        self.flags[flag_name] = True
    
    def disable(self, flag_name: str):
        self.flags[flag_name] = False

feature_flags = FeatureFlags()
```

---

## 🎯 Performance Benchmarks

### 1. Performance Targets

#### Response Time Targets:
- **API Endpoints**: <200ms (95th percentile)
- **WebSocket Messages**: <50ms
- **File Processing**: 1000+ records/minute
- **Network Discovery**: 1000+ IPs/hour

#### Throughput Targets:
- **Concurrent Users**: 100+ simultaneous users
- **API Requests**: 1000+ requests/minute
- **File Uploads**: 10+ files/minute
- **Data Processing**: 10MB+ logs/minute

### 2. Resource Requirements

#### Minimum Requirements:
- **CPU**: 2 cores, 2.4GHz
- **Memory**: 4GB RAM
- **Storage**: 100GB SSD
- **Network**: 100Mbps

#### Recommended Requirements:
- **CPU**: 4 cores, 3.0GHz
- **Memory**: 8GB RAM
- **Storage**: 500GB SSD
- **Network**: 1Gbps

#### Production Requirements:
- **CPU**: 8+ cores, 3.5GHz
- **Memory**: 16GB+ RAM
- **Storage**: 1TB+ SSD
- **Network**: 10Gbps

---

## 📞 Support & Maintenance

### 1. Support Tiers

#### Tier 1 Support:
- Basic troubleshooting
- User account issues
- Simple configuration changes
- Documentation questions

#### Tier 2 Support:
- Complex technical issues
- Performance problems
- Integration issues
- Security incidents

#### Tier 3 Support:
- Critical system failures
- Security breaches
- Data corruption
- Emergency response

### 2. Maintenance Windows

#### Regular Maintenance:
- **Weekly**: System health checks
- **Monthly**: Security updates
- **Quarterly**: Performance optimization
- **Annually**: Major version upgrades

#### Emergency Maintenance:
- **Critical Security Patches**: As needed
- **System Failures**: Immediate response
- **Data Issues**: Within 4 hours
- **Performance Issues**: Within 24 hours

---

*This technical architecture document provides comprehensive guidance for implementing and maintaining the Regions Bank Network Scanning Platform. Regular updates are recommended as the system evolves.*

