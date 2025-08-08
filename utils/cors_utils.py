# utils/cors_utils.py - CORS Utility Functions
import re
from typing import List

def validate_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Validate if origin is allowed"""
    if not origin:
        return False
        
    # Check for exact match
    if origin in allowed_origins:
        return True
        
    # Check for wildcard patterns
    for allowed in allowed_origins:
        if '*' in allowed:
            pattern = allowed.replace('*', '.*')
            if re.match(pattern, origin):
                return True
                
    return False

def get_cors_origins_from_env() -> List[str]:
    """Get CORS origins from environment variables"""
    import os
    import json
    
    origins_str = os.getenv('ALLOWED_ORIGINS', '[]')
    try:
        return json.loads(origins_str)
    except json.JSONDecodeError:
        # Fallback to comma-separated string
        return [origin.strip() for origin in origins_str.split(',') if origin.strip()]

def is_development() -> bool:
    """Check if running in development mode"""
    return os.getenv('DEBUG', 'false').lower() == 'true'