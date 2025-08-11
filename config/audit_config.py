# config/audit_config.py - Configuration for Enhanced Audit System

from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from enum import Enum
import os

class AuditStorageType(str, Enum):
    MEMORY = "memory"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"

class AuditConfig(BaseSettings):
    # Basic configuration
    enabled: bool = Field(True, description="Enable audit logging")
    storage_type: AuditStorageType = Field(AuditStorageType.MEMORY, description="Storage backend type")
    
    # Risk assessment configuration
    enable_risk_assessment: bool = Field(True, description="Enable automatic risk assessment")
    geographic_risk_weight: float = Field(25.0, description="Weight for geographic risk factor")
    temporal_risk_weight: float = Field(15.0, description="Weight for temporal risk factor")
    device_risk_weight: float = Field(20.0, description="Weight for device risk factor")
    behavioral_risk_weight: float = Field(30.0, description="Weight for behavioral risk factor")
    
    # Risk thresholds
    low_risk_threshold: float = Field(30.0, description="Low risk threshold")
    medium_risk_threshold: float = Field(50.0, description="Medium risk threshold")
    high_risk_threshold: float = Field(70.0, description="High risk threshold")
    
    # Authentication failure tracking
    max_failed_attempts_window: int = Field(100, description="Max failed attempts to track per user")
    failed_attempts_time_window: int = Field(24, description="Time window in hours for failure tracking")
    suspicious_ip_threshold: int = Field(10, description="Failed attempts threshold for suspicious IP")
    
    # Integration settings
    azure_ad_integration: bool = Field(True, description="Enable Azure AD integration")
    okta_integration: bool = Field(True, description="Enable Okta integration")
    adfs_integration: bool = Field(True, description="Enable ADFS integration")
    
    # SIEM integration
    siem_enabled: bool = Field(False, description="Enable SIEM integration")
    siem_endpoint: Optional[str] = Field(None, description="SIEM webhook endpoint")
    siem_api_key: Optional[str] = Field(None, description="SIEM API key")
    
    # Database settings (if using external storage)
    database_url: Optional[str] = Field(None, description="Database connection URL")
    database_pool_size: int = Field(10, description="Database connection pool size")
    
    # Security settings
    encrypt_sensitive_data: bool = Field(True, description="Encrypt sensitive audit data")
    retention_days: int = Field(365, description="Audit log retention period in days")
    
    # Performance settings
    bulk_insert_size: int = Field(1000, description="Bulk insert batch size")
    background_processing: bool = Field(True, description="Enable background processing")
    
    class Config:
        env_prefix = "AUDIT_"
        case_sensitive = False

# Load configuration
audit_config = AuditConfig()