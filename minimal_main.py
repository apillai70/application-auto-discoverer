# minimal_main.py - Simplified version to test basic functionality
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic configuration
project_root = Path(__file__).parent

app = FastAPI(
    title="Application Auto-Discovery Platform - Minimal",
    description="Minimal version for testing",
    version="2.3.0-minimal",
    docs_url="/docs"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create basic directories
def ensure_basic_directories():
    directories = [
        project_root / "data_staging",
        project_root / "results",
        project_root / "static"
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

# Ensure directories exist
ensure_basic_directories()

# Mount static files for data_staging
data_staging_dir = project_root / "data_staging"
if data_staging_dir.exists():
    app.mount("/data_staging", StaticFiles(directory=str(data_staging_dir)), name="data_staging")
    logger.info(f"Mounted data_staging from {data_staging_dir}")

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Minimal API is running", "docs": "/docs", "health": "/health"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.3.0-minimal",
        "directories": {
            "data_staging": data_staging_dir.exists(),
            "results": (project_root / "results").exists(),
        }
    }

@app.get("/debug/files")
async def debug_files():
    """Debug endpoint to check what files exist"""
    try:
        data_dir = project_root / "data_staging"
        if not data_dir.exists():
            return {"error": "data_staging directory doesn't exist", "path": str(data_dir)}
        
        files = list(data_dir.glob("*.csv"))
        return {
            "directory": str(data_dir.absolute()),
            "exists": data_dir.exists(),
            "csv_files": [f.name for f in files],
            "all_files": [f.name for f in data_dir.iterdir()],
            "file_count": len(files)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/data/current")
async def get_current_csv():
    """Return info about latest normalized CSV file"""
    try:
        data_dir = project_root / "data_staging"
        
        # Find normalized CSV files (your actual pattern)
        normalized_files = [f for f in data_dir.glob("*_normalized_*.csv")]
        
        if normalized_files:
            # Get the most recently created normalized file
            latest_file = max(normalized_files, key=lambda f: f.stat().st_mtime)
            return {
                "endpoint": f"/data_staging/{latest_file.name}",
                "filename": latest_file.name,
                "status": "available",
                "pipeline_health": {"status": "healthy"},
                "file_type": "normalized",
                "processed_at": latest_file.stat().st_mtime
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No normalized CSV files available", 
                    "status": "no_data",
                    "message": "No *_normalized_*.csv files found in data_staging"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "error"}
        )

@app.get("/api/v1/data/files")
async def list_pipeline_files():
    """List all files in the processing pipeline"""
    try:
        data_dir = project_root / "data_staging"
        
        # Find different file types
        normalized_files = list(data_dir.glob("*_normalized_*.csv"))
        excel_files = list(data_dir.glob("*_normalized_*.xlsx"))
        static_files = [f for f in data_dir.glob("*.csv") if "normalized" not in f.name]
        
        return {
            "success": True,
            "current_file": max(normalized_files, key=lambda f: f.stat().st_mtime).name if normalized_files else None,
            "files": {
                "processed": {
                    "count": len(normalized_files),
                    "files": [f.name for f in sorted(normalized_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "excel_reports": {
                    "count": len(excel_files), 
                    "files": [f.name for f in sorted(excel_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "static": {
                    "count": len(static_files),
                    "files": [f.name for f in static_files]
                }
            },
            "pipeline_health": {
                "status": "healthy" if normalized_files else "no_processed_files",
                "message": f"{len(normalized_files)} normalized files available"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )
        
@app.get("/api/v1/data/check")
async def check_data_files():
    """Check for the specific files the frontend is looking for"""
    data_dir = project_root / "data_staging"
    
    # Files the frontend is looking for based on the logs
    expected_files = [
        "edges.csv",
        "edges20250917_161754.csv",
        "processed_edges.csv",
        "normalized_edges.csv",
        "App_Code_edges.csv"
    ]
    
    file_status = {}
    for filename in expected_files:
        file_path = data_dir / filename
        file_status[filename] = {
            "exists": file_path.exists(),
            "path": str(file_path)
        }
    
    return {
        "data_directory": str(data_dir),
        "directory_exists": data_dir.exists(),
        "expected_files": file_status,
        "recommendations": [
            "Create missing edge CSV files in data_staging/",
            "Check if frontend is looking for the right file names",
            "Verify static file mounting is working"
        ]
    }

if __name__ == "__main__":
    logger.info("Starting minimal Application Auto-Discovery Platform")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data staging: {data_staging_dir}")
    
    uvicorn.run(
        "minimal_main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        log_level="info"
    )