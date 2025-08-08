# routers/auth.py - FIXED PREVIOUS VERSION
# Just add the missing imports at the top

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List  # ← ADD THIS LINE (was missing)
import hashlib
import secrets
import time
import hmac

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Configuration
SECRET_KEY = "your-secret-key-change-in-production-2024"
TOKEN_EXPIRE_MINUTES = 30

# Simple token storage
ACTIVE_TOKENS: Dict[str, Dict[str, Any]] = {}

def secure_hash_password(password: str, salt: str = None) -> str:
    """Secure password hashing using PBKDF2"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, hash_hex = stored_hash.split(':')
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(hash_hex, password_hash.hex())
    except ValueError:
        return False

def create_access_token(username: str, roles: List[str]) -> str:
    """Create a secure access token"""
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + (TOKEN_EXPIRE_MINUTES * 60)
    
    ACTIVE_TOKENS[token] = {
        "username": username,
        "roles": roles,
        "expires_at": expires_at,
        "created_at": time.time(),
        "last_used": time.time()
    }
    
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify and return username from token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    if token not in ACTIVE_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = ACTIVE_TOKENS[token]
    
    if time.time() > token_data["expires_at"]:
        del ACTIVE_TOKENS[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data["last_used"] = time.time()
    return token_data["username"]

def optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Optional authentication - returns username or None"""
    if not credentials:
        return None
    
    try:
        return verify_token(credentials)
    except HTTPException:
        return None

# User database with secure password hashing
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": secure_hash_password("admin123"),
        "roles": ["admin", "user"],
        "is_active": True,
        "email": "admin@company.com",
        "full_name": "Administrator"
    },
    "user": {
        "username": "user",
        "hashed_password": secure_hash_password("user123"),
        "roles": ["user"],
        "is_active": True,
        "email": "user@company.com",
        "full_name": "Regular User"
    },
    "security": {
        "username": "security",
        "hashed_password": secure_hash_password("security123"),
        "roles": ["security", "analyst", "user"],
        "is_active": True,
        "email": "security@company.com",
        "full_name": "Security Analyst"
    },
    "readonly": {
        "username": "readonly",
        "hashed_password": secure_hash_password("readonly123"),
        "roles": ["readonly"],
        "is_active": True,
        "email": "readonly@company.com",
        "full_name": "Read Only User"
    }
}

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    username: str
    roles: List[str]

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: str
    roles: List[str]
    is_active: bool
    last_login: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    full_name: str
    roles: List[str] = ["user"]

# Helper functions for other routers - FIXED
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user (alias for verify_token)"""
    return verify_token(credentials)

def get_current_user_roles(current_user: str = Depends(get_current_user)) -> List[str]:
    """Get current user's roles"""
    user = USERS_DB.get(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["roles"]

def check_permission(required_role: str):
    """Check if user has required role - COMPATIBILITY FUNCTION"""
    def permission_checker(current_user: str = Depends(get_current_user)):
        user = USERS_DB.get(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if required_role not in user["roles"]:
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied: '{required_role}' role required"
            )
        return current_user
    
    return permission_checker

def require_role(required_role: str):
    """Decorator to require specific role"""
    return check_permission(required_role)

def require_admin(current_user: str = Depends(get_current_user)):
    """Require admin role"""
    user = USERS_DB.get(current_user)
    if not user or "admin" not in user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def check_admin_access(current_user: str = Depends(get_current_user)):
    """Check if user has admin access - COMPATIBILITY FUNCTION"""
    return require_admin(current_user)

def check_security_access(current_user: str = Depends(get_current_user)):
    """Check if user has security access"""
    user = USERS_DB.get(current_user)
    if not user or not any(role in user["roles"] for role in ["admin", "security", "analyst"]):
        raise HTTPException(status_code=403, detail="Security access required")
    return current_user

def check_user_access(current_user: str = Depends(get_current_user)):
    """Check if user has basic user access"""
    user = USERS_DB.get(current_user)
    if not user or not any(role in user["roles"] for role in ["admin", "user", "security", "analyst"]):
        raise HTTPException(status_code=403, detail="User access required")
    return current_user

# Authentication endpoints
@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return access token"""
    user = USERS_DB.get(request.username)
    
    if not user:
        # Prevent username enumeration
        time.sleep(0.1)  # Small delay
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    access_token = create_access_token(user["username"], user["roles"])
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_MINUTES * 60,
        username=user["username"],
        roles=user["roles"]
    )

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: str = Depends(verify_token)):
    """Get current user profile"""
    user = USERS_DB.get(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        roles=user["roles"],
        is_active=user["is_active"],
        last_login=datetime.now().isoformat()
    )

@router.post("/logout")
async def logout(current_user: str = Depends(verify_token)):
    """Logout user by invalidating token"""
    # Find and remove user's tokens
    tokens_to_remove = []
    for token, data in ACTIVE_TOKENS.items():
        if data["username"] == current_user:
            tokens_to_remove.append(token)
    
    for token in tokens_to_remove:
        del ACTIVE_TOKENS[token]
    
    return {"message": f"User {current_user} logged out successfully"}

@router.get("/validate")
async def validate_token(current_user: str = Depends(verify_token)):
    """Validate current token"""
    user = USERS_DB.get(current_user)
    return {
        "valid": True,
        "user": current_user,
        "roles": user["roles"] if user else [],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/users")
async def list_users(current_user: str = Depends(verify_token)):
    """List all users (admin only)"""
    user = USERS_DB.get(current_user)
    if not user or "admin" not in user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = []
    for username, user_data in USERS_DB.items():
        users.append({
            "username": user_data["username"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "roles": user_data["roles"],
            "is_active": user_data["is_active"]
        })
    
    return {"users": users}

@router.post("/users")
async def create_user(user_data: UserCreate, current_user: str = Depends(verify_token)):
    """Create new user (admin only)"""
    current_user_data = USERS_DB.get(current_user)
    if not current_user_data or "admin" not in current_user_data["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user_data.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    USERS_DB[user_data.username] = {
        "username": user_data.username,
        "hashed_password": secure_hash_password(user_data.password),
        "email": user_data.email,
        "full_name": user_data.full_name,
        "roles": user_data.roles,
        "is_active": True
    }
    
    return {"message": f"User {user_data.username} created successfully"}

@router.get("/sessions")
async def get_active_sessions(current_user: str = Depends(verify_token)):
    """Get active sessions"""
    user = USERS_DB.get(current_user)
    if not user or "admin" not in user["roles"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sessions = []
    for token, data in ACTIVE_TOKENS.items():
        sessions.append({
            "token_preview": token[:8] + "...",
            "username": data["username"],
            "created_at": datetime.fromtimestamp(data["created_at"]).isoformat(),
            "last_used": datetime.fromtimestamp(data["last_used"]).isoformat(),
            "expires_at": datetime.fromtimestamp(data["expires_at"]).isoformat()
        })
    
    return {"active_sessions": sessions, "total": len(sessions)}

@router.post("/cleanup")
async def cleanup_expired_tokens():
    """Clean up expired tokens"""
    current_time = time.time()
    expired_tokens = [
        token for token, data in ACTIVE_TOKENS.items()
        if current_time > data["expires_at"]
    ]
    
    for token in expired_tokens:
        del ACTIVE_TOKENS[token]
    
    return {
        "message": f"Cleaned up {len(expired_tokens)} expired tokens",
        "active_tokens": len(ACTIVE_TOKENS)
    }

@router.get("/test")
async def test_auth():
    """Test authentication system"""
    return {
        "message": "Authentication system is working!",
        "hashing_method": "PBKDF2-SHA256",
        "available_users": list(USERS_DB.keys()),
        "active_tokens": len(ACTIVE_TOKENS),
        "token_expire_minutes": TOKEN_EXPIRE_MINUTES,
        "timestamp": datetime.now().isoformat(),
        "test_credentials": {
            "admin": "admin123",
            "user": "user123", 
            "security": "security123",
            "readonly": "readonly123"
        }
    }

# Export commonly used functions
__all__ = [
    "router",
    "verify_token", 
    "optional_auth",
    "get_current_user",
    "get_current_user_roles",
    "require_role",
    "require_admin",
    "check_permission",          # ← This was missing and causing the error
    "check_admin_access",        
    "check_security_access",     
    "check_user_access",         
    "USERS_DB",
    "ACTIVE_TOKENS"
]