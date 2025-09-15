# Security Quick Reference Guide
## Critical Security Implementations for Regions Bank

---

## 🚨 Immediate Actions Required

### 1. Fix CORS Configuration (5 minutes)
```python
# BEFORE (INSECURE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # SECURITY RISK!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER (SECURE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://network-scanner.regionsbank.com",
        "https://internal.regionsbank.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)
```

### 2. Add Security Headers (10 minutes)
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
```

### 3. Implement Basic Authentication (30 minutes)
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=1800,  # 30 minutes
    tokenUrl="auth/jwt/login",
)

# Protect endpoints
@router.post("/api/v1/network/scan")
async def trigger_network_scan(
    current_user: dict = Depends(require_auth("network:scan"))
):
    # Your existing code here
    pass
```

---

## 🔐 Critical Security Functions

### Input Validation
```python
from pydantic import BaseModel, validator
import re

class SecureInput(BaseModel):
    filename: str
    content: str
    
    @validator('filename')
    def validate_filename(cls, v):
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        # Check for SQL injection
        sql_patterns = [r'union\s+select', r'drop\s+table', r'delete\s+from']
        if any(re.search(pattern, v, re.IGNORECASE) for pattern in sql_patterns):
            raise ValueError('Potentially malicious content detected')
        return v
```

### File Upload Security
```python
import magic
from pathlib import Path

async def secure_file_upload(file: UploadFile):
    # Validate file type
    file_content = await file.read()
    detected_type = magic.from_buffer(file_content, mime=True)
    
    allowed_types = ['text/csv', 'application/vnd.ms-excel', 'application/json']
    if detected_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Sanitize filename
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file.filename)
    
    # Save file
    safe_path = Path("uploads") / safe_filename
    with open(safe_path, 'wb') as f:
        f.write(file_content)
    
    return safe_path
```

### Data Encryption
```python
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Usage
encryption = DataEncryption()
encrypted_ssn = encryption.encrypt_data("123-45-6789")
```

---

## 🛡️ Security Monitoring

### Basic Security Logging
```python
import logging
from datetime import datetime

# Configure security logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)

security_logger = logging.getLogger('security')

def log_security_event(event_type: str, user_id: str, details: dict):
    security_logger.info(f"SECURITY_EVENT: {event_type} - User: {user_id} - Details: {details}")

# Usage
log_security_event("login_attempt", "user123", {"ip": "192.168.1.100", "success": True})
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/api/v1/network/scan")
@limiter.limit("10/hour")
async def trigger_network_scan(request: Request):
    # Your existing code here
    pass
```

---

## 🔍 Threat Detection

### Basic Brute Force Detection
```python
from collections import defaultdict
from datetime import datetime, timedelta

class BruteForceDetector:
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.max_attempts = 5
        self.time_window = 300  # 5 minutes
    
    def check_attempt(self, ip_address: str) -> bool:
        now = datetime.utcnow()
        
        # Clean old attempts
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if now - attempt < timedelta(seconds=self.time_window)
        ]
        
        # Check if too many attempts
        if len(self.failed_attempts[ip_address]) >= self.max_attempts:
            return True  # Block this IP
        
        return False
    
    def record_failed_attempt(self, ip_address: str):
        self.failed_attempts[ip_address].append(datetime.utcnow())

# Usage
brute_force_detector = BruteForceDetector()

@router.post("/auth/login")
async def login(credentials: LoginCredentials, request: Request):
    client_ip = get_client_ip(request)
    
    if brute_force_detector.check_attempt(client_ip):
        raise HTTPException(status_code=429, detail="Too many failed attempts")
    
    # Your login logic here
    if not authenticate_user(credentials.email, credentials.password):
        brute_force_detector.record_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

### SQL Injection Detection
```python
import re

class SQLInjectionDetector:
    def __init__(self):
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'--',
            r'/\*.*\*/'
        ]
    
    def detect(self, text: str) -> bool:
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.sql_patterns)

# Usage
sql_detector = SQLInjectionDetector()

@router.get("/api/v1/network/topology")
async def get_network_topology(query: str = None):
    if query and sql_detector.detect(query):
        raise HTTPException(status_code=400, detail="Invalid query detected")
    
    # Your existing code here
    pass
```

---

## 📋 Security Checklist

### Immediate (Today)
- [ ] Fix CORS configuration
- [ ] Add security headers
- [ ] Implement basic authentication
- [ ] Add input validation
- [ ] Enable HTTPS

### Short-term (This Week)
- [ ] Implement file upload security
- [ ] Add data encryption
- [ ] Implement rate limiting
- [ ] Add security logging
- [ ] Enable database SSL

### Medium-term (This Month)
- [ ] Implement MFA
- [ ] Add role-based access control
- [ ] Implement threat detection
- [ ] Add security monitoring
- [ ] Conduct security testing

---

## 🚨 Emergency Response

### If Security Breach Detected
1. **Immediate Actions**
   - [ ] Isolate affected systems
   - [ ] Change all passwords
   - [ ] Revoke all API keys
   - [ ] Enable additional logging
   - [ ] Notify security team

2. **Investigation**
   - [ ] Review security logs
   - [ ] Identify attack vector
   - [ ] Assess data exposure
   - [ ] Document findings
   - [ ] Implement fixes

3. **Recovery**
   - [ ] Patch vulnerabilities
   - [ ] Restore from backups
   - [ ] Update security controls
   - [ ] Conduct post-incident review
   - [ ] Update procedures

---

## 📞 Security Contacts

### Internal Team
- **Security Team Lead**: [Contact Information]
- **Incident Response**: [Contact Information]
- **Network Security**: [Contact Information]
- **Compliance Officer**: [Contact Information]

### External Support
- **Security Consultant**: [Contact Information]
- **Penetration Testing**: [Contact Information]
- **Compliance Auditor**: [Contact Information]
- **Emergency Response**: [Contact Information]

---

## 🔧 Security Tools

### Development Tools
```bash
# Install security tools
pip install bandit safety semgrep

# Run security scans
bandit -r . -f json -o security-report.json
safety check
semgrep --config=auto .
```

### Monitoring Tools
```bash
# Install monitoring tools
pip install prometheus-client psutil

# Monitor system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

---

*This quick reference guide provides immediate security implementations that can be deployed today to significantly improve the security posture of your Regions Bank Network Scanning Platform.*

