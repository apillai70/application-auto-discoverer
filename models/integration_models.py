# models/integration_models.py
"""
Pydantic models for external integrations
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IntegrationConfig(BaseModel):
    """Base integration configuration"""
    pass

class IntegrationStatus(BaseModel):
    """Integration status information"""
    pass

class SNMPConfig(BaseModel):
    """SNMP integration configuration"""
    pass

class SSHConfig(BaseModel):
    """SSH integration configuration"""
    pass

class APIConfig(BaseModel):
    """API integration configuration"""
    pass