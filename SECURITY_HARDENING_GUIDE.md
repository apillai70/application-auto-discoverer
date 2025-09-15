# Security Hardening Guide
## Regions Bank Network Scanning Platform

---

## 🔒 Overview

This guide provides detailed, actionable steps for hardening the Regions Bank Network Scanning Platform to meet enterprise security standards and banking industry compliance requirements.

---

## 🎯 Security Hardening Roadmap

### Phase 1: Critical Security Fixes (Week 1-2)
- Authentication & Authorization
- Data Encryption
- Input Validation
- Network Security

### Phase 2: Infrastructure Security (Week 3-4)
- Database Security
- API Security
- Logging & Monitoring
- Error Handling

### Phase 3: Advanced Security (Week 5-8)
- Threat Detection
- Compliance Controls
- Security Testing
- Documentation

---

## 🔐 Phase 1: Critical Security Fixes

### 1.1 Authentication & Authorization

#### Current Issues:
```python
# EXISTING - Basic authentication only
@router.post("/upload")
async def upload_topology_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(check_permission("topology:write"))
):
```

#### Hardened Implementation:
```python
# NEW - Multi-factor authentication with RBAC
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.models import BaseUser
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
import pyotp
import qrcode

Base = declarative_base()

# User Model with MFA
class User(Base, BaseUser):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)

# Role-Based Access Control
class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(Enum(Role), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Permission(Enum):
    NETWORK_READ = "network:read"
    NETWORK_WRITE = "network:write"
    NETWORK_SCAN = "network:scan"
    SECURITY_READ = "security:read"
    SECURITY_WRITE = "security:write"
    USER_MANAGE = "user:manage"
    SYSTEM_ADMIN = "system:admin"

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    tokenUrl="auth/jwt/login",
)

# Enhanced Permission Checker
async def require_permission(permission: Permission):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if user is locked
            if current_user.account_locked_until and current_user.account_locked_until > datetime.utcnow():
                raise HTTPException(status_code=423, detail="Account temporarily locked")
            
            # Check permissions
            user_roles = await get_user_roles(current_user.id)
            has_permission = any(
                role_has_permission(role.role, permission) for role in user_roles
            )
            
            if not has_permission:
                # Log unauthorized access attempt
                await log_security_event(
                    "unauthorized_access_attempt",
                    current_user.id,
                    {"permission": permission.value, "endpoint": func.__name__},
                    "WARNING"
                )
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# MFA Implementation
class MFAService:
    def __init__(self):
        self.secret_key = os.getenv("MFA_SECRET_KEY", pyotp.random_base32())
    
    def generate_qr_code(self, user_email: str, user_id: int) -> str:
        totp_uri = pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=user_email,
            issuer_name="Regions Bank Network Scanner",
            user_id=user_id
        )
        return totp_uri
    
    def verify_token(self, user_id: int, token: str) -> bool:
        user = await get_user_by_id(user_id)
        if not user.mfa_enabled:
            return False
        
        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, user_id: int) -> List[str]:
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        await store_backup_codes(user_id, backup_codes)
        return backup_codes

# Account Lockout Protection
class AccountLockoutService:
    def __init__(self):
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
    
    async def handle_failed_login(self, user_id: int):
        user = await get_user_by_id(user_id)
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            
            # Log security event
            await log_security_event(
                "account_locked",
                user_id,
                {"reason": "too_many_failed_attempts", "lockout_duration": self.lockout_duration_minutes},
                "WARNING"
            )
        
        await update_user(user)
    
    async def handle_successful_login(self, user_id: int):
        user = await get_user_by_id(user_id)
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        await update_user(user)

# Hardened Authentication Endpoint
@router.post("/auth/login")
async def login(credentials: LoginCredentials, response: Response):
    user = await authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423, 
            detail=f"Account locked until {user.account_locked_until.isoformat()}"
        )
    
    # Verify MFA if enabled
    if user.mfa_enabled:
        if not credentials.mfa_token:
            raise HTTPException(
                status_code=202, 
                detail="MFA token required",
                headers={"X-MFA-Required": "true"}
            )
        
        if not await mfa_service.verify_token(user.id, credentials.mfa_token):
            await account_lockout.handle_failed_login(user.id)
            raise HTTPException(status_code=401, detail="Invalid MFA token")
    
    # Generate tokens
    access_token = jwt_authentication.get_login_token(user)
    refresh_token = create_refresh_token(user.id)
    
    # Log successful login
    await account_lockout.handle_successful_login(user.id)
    await log_security_event("successful_login", user.id, {}, "INFO")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
```

### 1.2 Data Encryption

#### Implement Encryption at Rest:
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os
import structlog

class DataEncryptionService:
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        self.logger = structlog.get_logger("encryption")
    
    def _get_or_create_master_key(self) -> bytes:
        key_file = Path("config/master.key")
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            self.logger.info("New master encryption key generated")
            return key
    
    def encrypt_file(self, file_path: Path, target_path: Path = None) -> Path:
        """Encrypt a file at rest"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.fernet.encrypt(data)
            
            if target_path is None:
                target_path = file_path.with_suffix(file_path.suffix + '.enc')
            
            with open(target_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Remove original file after encryption
            file_path.unlink()
            
            self.logger.info("File encrypted successfully", 
                           original_file=str(file_path), 
                           encrypted_file=str(target_path))
            return target_path
            
        except Exception as e:
            self.logger.error("File encryption failed", error=str(e))
            raise
    
    def decrypt_file(self, encrypted_path: Path, target_path: Path = None) -> Path:
        """Decrypt a file at rest"""
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            if target_path is None:
                target_path = encrypted_path.with_suffix('')
            
            with open(target_path, 'wb') as f:
                f.write(decrypted_data)
            
            self.logger.info("File decrypted successfully", 
                           encrypted_file=str(encrypted_path), 
                           decrypted_file=str(target_path))
            return target_path
            
        except Exception as e:
            self.logger.error("File decryption failed", error=str(e))
            raise
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive string data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

# Database Field Encryption
class EncryptedField:
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.encryption_service = DataEncryptionService()
    
    def __get__(self, instance, owner):
        encrypted_value = getattr(instance, f"_{self.field_name}_encrypted")
        if encrypted_value is None:
            return None
        return self.encryption_service.decrypt_sensitive_data(encrypted_value)
    
    def __set__(self, instance, value):
        if value is None:
            setattr(instance, f"_{self.field_name}_encrypted", None)
        else:
            encrypted_value = self.encryption_service.encrypt_sensitive_data(str(value))
            setattr(instance, f"_{self.field_name}_encrypted", encrypted_value)

# Enhanced User Model with Encrypted Fields
class SecureUser(Base):
    __tablename__ = "secure_users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    _ssn_encrypted = Column(String)  # Encrypted SSN
    _phone_encrypted = Column(String)  # Encrypted phone
    _address_encrypted = Column(String)  # Encrypted address
    
    ssn = EncryptedField("ssn")  # Use as regular field
    phone = EncryptedField("phone")
    address = EncryptedField("address")
```

### 1.3 Input Validation & Sanitization

#### Comprehensive Input Validation:
```python
from pydantic import BaseModel, validator, Field
import magic
import re
from typing import Optional, List
import bleach

class SecureFileUpload(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    size: int = Field(..., ge=1, le=100 * 1024 * 1024)  # Max 100MB
    file_content: bytes
    
    @validator('filename')
    def validate_filename(cls, v):
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in v for char in dangerous_chars):
            raise ValueError('Filename contains dangerous characters')
        
        # Check for reserved names
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
        if v.upper().split('.')[0] in reserved_names:
            raise ValueError('Filename is reserved')
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json', '.log']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError('File type not allowed')
        
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/json',
            'text/plain'
        ]
        if v not in allowed_types:
            raise ValueError('Content type not allowed')
        return v
    
    @validator('file_content')
    def validate_file_content(cls, v, values):
        # Verify file content matches declared type
        detected_type = magic.from_buffer(v, mime=True)
        declared_type = values.get('content_type')
        
        if detected_type != declared_type:
            raise ValueError('File content does not match declared type')
        
        # Scan for malicious content
        file_str = v.decode('utf-8', errors='ignore')
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                raise ValueError('File contains potentially malicious SQL patterns')
        
        # Check for script injection
        script_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'eval\(',
            r'exec\('
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                raise ValueError('File contains potentially malicious scripts')
        
        return v

# Enhanced Input Sanitization
class InputSanitizer:
    def __init__(self):
        self.bleach_allowed_tags = {'p', 'br', 'strong', 'em', 'u'}
        self.bleach_allowed_attributes = {}
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)  # Remove control characters
        sanitized = re.sub(r'\s+', '_', sanitized)  # Replace whitespace
        sanitized = sanitized.strip('._')  # Remove leading/trailing dots/underscores
        
        # Ensure reasonable length
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized or 'unnamed_file'
    
    def sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content"""
        return bleach.clean(
            html_content,
            tags=self.bleach_allowed_tags,
            attributes=self.bleach_allowed_attributes,
            strip=True
        )
    
    def sanitize_sql_input(self, sql_input: str) -> str:
        """Sanitize SQL input parameters"""
        # Remove or escape dangerous SQL characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        
        sanitized = sql_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Additional validation for SQL injection
        sql_keywords = ['union', 'select', 'drop', 'delete', 'insert', 'update', 'exec']
        words = sanitized.lower().split()
        
        for word in words:
            if word in sql_keywords:
                sanitized = sanitized.replace(word, '', 1)
        
        return sanitized.strip()
    
    def sanitize_json_input(self, json_input: str) -> str:
        """Sanitize JSON input"""
        try:
            # Parse and re-serialize to remove any malicious content
            data = json.loads(json_input)
            return json.dumps(data, separators=(',', ':'))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON input")

# Enhanced File Upload Endpoint
@router.post("/api/v1/files/upload")
async def upload_file_secure(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_permission(Permission.NETWORK_WRITE))
):
    """Secure file upload with comprehensive validation"""
    
    async def handle_file_upload(file: UploadFile):
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate file
            file_upload = SecureFileUpload(
                filename=file.filename,
                content_type=file.content_type,
                size=len(file_content),
                file_content=file_content
            )
            
            # Sanitize filename
            sanitizer = InputSanitizer()
            safe_filename = sanitizer.sanitize_filename(file_upload.filename)
            
            # Save file with sanitized name
            safe_path = Path("uploads") / safe_filename
            safe_path.parent.mkdir(exist_ok=True)
            
            with open(safe_path, 'wb') as f:
                f.write(file_content)
            
            # Log file upload
            await log_security_event(
                "file_uploaded",
                current_user.id,
                {
                    "original_filename": file.filename,
                    "safe_filename": safe_filename,
                    "file_size": file_upload.size,
                    "content_type": file_upload.content_type
                },
                "INFO"
            )
            
            # Process file in background
            background_tasks.add_task(process_uploaded_file, safe_path, current_user.id)
            
            return {
                "success": True,
                "message": "File uploaded successfully",
                "safe_filename": safe_filename,
                "file_id": str(uuid.uuid4())
            }
            
        except Exception as e:
            await log_security_event(
                "file_upload_failed",
                current_user.id,
                {"error": str(e), "filename": file.filename},
                "ERROR"
            )
            raise HTTPException(status_code=400, detail=f"File upload failed: {str(e)}")
```

### 1.4 Network Security

#### Secure CORS Configuration:
```python
# HARDENED CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

# Define allowed origins based on environment
ALLOWED_ORIGINS = {
    "development": [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000"
    ],
    "staging": [
        "https://network-scanner-staging.regionsbank.com",
        "https://staging.regionsbank.com"
    ],
    "production": [
        "https://network-scanner.regionsbank.com",
        "https://internal.regionsbank.com",
        "https://regionsbank.com"
    ]
}

# Get current environment
environment = os.getenv("ENVIRONMENT", "development")
allowed_origins = ALLOWED_ORIGINS.get(environment, ALLOWED_ORIGINS["development"])

# Configure CORS with security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Limited methods
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-API-Key"
    ],
    expose_headers=["X-Total-Count", "X-Page-Count"],
    max_age=600  # Cache preflight for 10 minutes
)

# Additional Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' wss:;"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
```

---

## 🛡️ Phase 2: Infrastructure Security

### 2.1 Database Security

```python
# Secure Database Configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import ssl

# Database Security Configuration
DATABASE_CONFIG = {
    'engine': {
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'echo': False  # Don't log SQL queries
    },
    'ssl': {
        'sslmode': 'require',
        'sslcert': 'config/db-client.crt',
        'sslkey': 'config/db-client.key',
        'sslrootcert': 'config/ca-cert.pem'
    },
    'connection': {
        'connect_timeout': 10,
        'command_timeout': 30,
        'application_name': 'regions_network_scanner'
    }
}

# Create secure engine
def create_secure_engine():
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            'sslmode': DATABASE_CONFIG['ssl']['sslmode'],
            'sslcert': DATABASE_CONFIG['ssl']['sslcert'],
            'sslkey': DATABASE_CONFIG['ssl']['sslkey'],
            'sslrootcert': DATABASE_CONFIG['ssl']['sslrootcert']
        },
        **DATABASE_CONFIG['engine']
    )
    
    # Enable connection pooling
    engine.connect().close()  # Test connection
    
    return engine

# Database Access Control
class DatabaseAccessControl:
    def __init__(self):
        self.role_permissions = {
            'network_analyst': ['network_data', 'topology_data'],
            'security_analyst': ['security_alerts', 'threat_data'],
            'admin': ['*']  # All tables
        }
    
    def check_table_access(self, user_role: str, table_name: str) -> bool:
        """Check if user role can access specific table"""
        if user_role not in self.role_permissions:
            return False
        
        permissions = self.role_permissions[user_role]
        return '*' in permissions or table_name in permissions

# Row-Level Security
class RowLevelSecurity:
    def __init__(self):
        self.security_policies = {}
    
    def add_security_policy(self, table_name: str, policy_func):
        """Add row-level security policy"""
        self.security_policies[table_name] = policy_func
    
    def apply_security_filter(self, query, user_id: int, table_name: str):
        """Apply row-level security to query"""
        if table_name in self.security_policies:
            policy_func = self.security_policies[table_name]
            return policy_func(query, user_id)
        return query
```

### 2.2 API Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

# Redis connection for rate limiting
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

# Rate limiter configuration
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379",
    default_limits=["1000/hour"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate limiting decorators
def rate_limit_by_user(user_limit: str = "100/hour"):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user:
                user_key = f"user:{current_user.id}:{func.__name__}"
                return limiter.limit(user_limit, key_func=lambda: user_key)(func)(*args, **kwargs)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_by_ip(ip_limit: str = "500/hour"):
    def decorator(func):
        return limiter.limit(ip_limit)(func)
    return decorator

# Rate limited endpoints
@router.post("/api/v1/network/scan")
@rate_limit_by_user("10/hour")
@rate_limit_by_ip("50/hour")
async def trigger_network_scan(
    scan_request: ScanRequest,
    current_user: dict = Depends(require_permission(Permission.NETWORK_SCAN))
):
    """Rate-limited network scan endpoint"""
    return await network_service.trigger_scan(scan_request)

@router.post("/api/v1/security/alerts")
@rate_limit_by_user("50/hour")
@rate_limit_by_ip("200/hour")
async def create_security_alert(
    alert: SecurityAlertCreate,
    current_user: dict = Depends(require_permission(Permission.SECURITY_WRITE))
):
    """Rate-limited security alert creation"""
    return await security_service.create_alert(alert)
```

### 2.3 Comprehensive Logging & Monitoring

```python
import structlog
import logging
from datetime import datetime
import json

# Enhanced Security Logger
class SecurityLogger:
    def __init__(self):
        self.logger = structlog.get_logger("security")
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging for security events"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/security.log'),
                logging.StreamHandler()
            ]
        )
        
        # Configure structlog
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
    
    async def log_security_event(
        self, 
        event_type: str, 
        user_id: Optional[int], 
        details: dict, 
        severity: str = "INFO",
        source_ip: Optional[str] = None
    ):
        """Log security events with structured data"""
        event_data = {
            "event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": source_ip,
            "details": details,
            "session_id": getattr(g, 'session_id', None)
        }
        
        # Log to appropriate level
        if severity == "ERROR":
            self.logger.error("security_event", **event_data)
        elif severity == "WARNING":
            self.logger.warning("security_event", **event_data)
        else:
            self.logger.info("security_event", **event_data)
        
        # Send to SIEM if configured
        if os.getenv('SIEM_ENABLED', 'false').lower() == 'true':
            await self.send_to_siem(event_data)
    
    async def send_to_siem(self, event_data: dict):
        """Send security events to SIEM system"""
        try:
            siem_url = os.getenv('SIEM_URL')
            siem_api_key = os.getenv('SIEM_API_KEY')
            
            if siem_url and siem_api_key:
                headers = {
                    'Authorization': f'Bearer {siem_api_key}',
                    'Content-Type': 'application/json'
                }
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{siem_url}/api/v1/events",
                        json=event_data,
                        headers=headers,
                        timeout=5.0
                    )
        except Exception as e:
            self.logger.error("Failed to send event to SIEM", error=str(e))

# Security Event Types
class SecurityEventType:
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

# Enhanced Security Middleware
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    g.session_id = session_id
    
    try:
        response = await call_next(request)
        
        # Log successful request
        if response.status_code < 400:
            await security_logger.log_security_event(
                SecurityEventType.DATA_ACCESS,
                getattr(request.state, 'user_id', None),
                {
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "user_agent": user_agent
                },
                "INFO",
                client_ip
            )
        
        return response
        
    except Exception as e:
        # Log error
        await security_logger.log_security_event(
            SecurityEventType.SYSTEM_ERROR,
            getattr(request.state, 'user_id', None),
            {
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "error_type": type(e).__name__,
                "user_agent": user_agent
            },
            "ERROR",
            client_ip
        )
        raise
```

---

## 🔍 Phase 3: Advanced Security

### 3.1 Threat Detection Enhancement

```python
class AdvancedThreatDetection:
    def __init__(self):
        self.threat_rules = self.load_threat_rules()
        self.ml_model = self.load_ml_model()
        self.anomaly_detector = AnomalyDetector()
    
    def load_threat_rules(self):
        """Load threat detection rules from configuration"""
        return {
            "brute_force": BruteForceRule(),
            "sql_injection": SQLInjectionRule(),
            "xss_attack": XSSAttackRule(),
            "file_upload_abuse": FileUploadAbuseRule(),
            "privilege_escalation": PrivilegeEscalationRule(),
            "data_exfiltration": DataExfiltrationRule()
        }
    
    async def analyze_request(self, request: Request, user: Optional[User] = None) -> ThreatAssessment:
        """Analyze request for threats"""
        threat_score = 0.0
        detected_threats = []
        
        # Apply rule-based detection
        for rule_name, rule in self.threat_rules.items():
            if await rule.detect(request, user):
                threat_score += rule.severity
                detected_threats.append(rule_name)
        
        # Apply ML-based detection
        ml_score = await self.ml_threat_detection(request, user)
        threat_score += ml_score * 0.3  # Weight ML results
        
        # Check for anomalies
        anomaly_score = await self.anomaly_detector.detect_anomaly(request, user)
        threat_score += anomaly_score * 0.2
        
        return ThreatAssessment(
            threat_score=min(threat_score, 100.0),
            detected_threats=detected_threats,
            confidence=min(threat_score / 10, 1.0)
        )

class BruteForceRule:
    def __init__(self):
        self.failed_attempts = {}
        self.time_window = 300  # 5 minutes
        self.max_attempts = 5
        self.severity = 50
    
    async def detect(self, request: Request, user: Optional[User] = None) -> bool:
        if request.url.path == "/auth/login":
            client_ip = get_client_ip(request)
            now = datetime.utcnow()
            
            # Clean old attempts
            self.failed_attempts = {
                k: v for k, v in self.failed_attempts.items()
                if now - v["last_attempt"] < timedelta(seconds=self.time_window)
            }
            
            # Check if IP is in failed attempts
            if client_ip in self.failed_attempts:
                attempts = self.failed_attempts[client_ip]["count"]
                if attempts >= self.max_attempts:
                    # Log brute force attempt
                    await security_logger.log_security_event(
                        "brute_force_detected",
                        user.id if user else None,
                        {
                            "ip_address": client_ip,
                            "attempt_count": attempts,
                            "time_window": self.time_window
                        },
                        "WARNING",
                        client_ip
                    )
                    return True
        
        return False

class SQLInjectionRule:
    def __init__(self):
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'sp_',
            r'xp_',
            r'--',
            r'/\*.*\*/'
        ]
        self.severity = 80
    
    async def detect(self, request: Request, user: Optional[User] = None) -> bool:
        # Check query parameters
        for key, value in request.query_params.items():
            if self.contains_sql_pattern(str(value)):
                await security_logger.log_security_event(
                    "sql_injection_detected",
                    user.id if user else None,
                    {
                        "parameter": key,
                        "value": value,
                        "url": str(request.url)
                    },
                    "WARNING",
                    get_client_ip(request)
                )
                return True
        
        # Check request body for JSON/POST data
        if request.method == "POST":
            try:
                body = await request.json()
                if self.scan_dict_for_sql(body):
                    await security_logger.log_security_event(
                        "sql_injection_detected",
                        user.id if user else None,
                        {
                            "body_data": str(body),
                            "url": str(request.url)
                        },
                        "WARNING",
                        get_client_ip(request)
                    )
                    return True
            except:
                pass
        
        return False
    
    def contains_sql_pattern(self, text: str) -> bool:
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.sql_patterns)
    
    def scan_dict_for_sql(self, data: dict) -> bool:
        for key, value in data.items():
            if isinstance(value, str) and self.contains_sql_pattern(value):
                return True
            elif isinstance(value, dict) and self.scan_dict_for_sql(value):
                return True
        return False
```

This comprehensive security hardening guide provides detailed implementation steps for transforming your network scanning platform into a production-ready, security-hardened system suitable for Regions Bank's requirements. Each phase builds upon the previous one, ensuring a systematic approach to security enhancement.

