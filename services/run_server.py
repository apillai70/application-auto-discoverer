#!/usr/bin/env python3
"""
Uvicorn Server Startup Script
Integration Hub - Data Normalization API
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main server startup function"""
    
    # Environment configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    workers = int(os.getenv("WORKERS", 1))
    
    # Log configuration
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }
    
    print(f"""
🚀 Starting Integration Hub Data Normalization API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Server Details:
   • Host: {host}
   • Port: {port}
   • Workers: {workers}
   • Reload: {reload}

🔗 Endpoints:
   • API Documentation: http://{host}:{port}/api/docs
   • ReDoc Documentation: http://{host}:{port}/api/redoc
   • Health Check: http://{host}:{port}/api/health
   • Integration Hub UI: http://{host}:{port}/

🧠 Features Enabled:
   • Cross-batch duplicate detection
   • ML vectorization & tensor preparation
   • Smart field mapping
   • Comprehensive audit logging
   • Real-time processing feeds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # Start the server
    uvicorn.run(
        "fastapi_endpoints:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # Workers > 1 incompatible with reload
        log_config=log_config,
        access_log=True,
        server_header=True,
        date_header=True
    )

if __name__ == "__main__":
    main()