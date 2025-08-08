from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["*"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    # Data staging and processing directories
    DATA_STAGING_DIR: str = "data_staging"
    PROCESSED_DIR: str = "data_staging/processed"
    FAILED_DIR: str = "data_staging/failed"
    
    # Output directories with subfolders
    RESULTS_BASE_DIR: str = "results"
    EXCEL_OUTPUT_DIR: str = "results/excel"
    VISIO_OUTPUT_DIR: str = "results/visio"
    WORD_OUTPUT_DIR: str = "results/word"
    PDF_OUTPUT_DIR: str = "results/pdf"
    LUCID_OUTPUT_DIR: str = "results/lucid"
    
    # Log analysis settings
    LOG_PROCESSING_TIMEOUT: int = 300
    MAX_CONCURRENT_ANALYSIS: int = 5
    MAX_FILE_SIZE_MB: int = 100
    SUPPORTED_LOG_FORMATS: str = "csv,xlsx,json"
    
    # Documentation settings
    DOCS_OUTPUT_DIR: str = "results/word"
    DIAGRAMS_OUTPUT_DIR: str = "results/visio"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data source settings
    EXTRAHOP_API_KEY: Optional[str] = None
    EXTRAHOP_BASE_URL: str = "https://your-extrahop-instance.com"
    SPLUNK_API_ENDPOINT: Optional[str] = None
    SPLUNK_TOKEN: Optional[str] = None
    SPLUNK_USERNAME: str = "your-username"
    SPLUNK_PASSWORD: str = "your-password"
    DYNATRACE_API_TOKEN: Optional[str] = None
    DYNATRACE_ENVIRONMENT_URL: Optional[str] = None
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Application features
    ENABLE_FILE_UPLOAD: bool = True
    ENABLE_API_INTEGRATION: bool = True
    ENABLE_REAL_TIME_ANALYSIS: bool = False
    
    # File processing
    TEMP_DIR: str = "temp"
    
    # Output file naming
    APP_NAME_TAG_FORMAT: str = "{app_name}_{date}"
    DATE_FORMAT: str = "%Y%m%d_%H%M%S"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # This allows extra fields in .env without errors

# Global settings instance
settings = Settings()