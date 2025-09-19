# main.py - Application Auto-Discovery Platform with Enhanced Diagram Service and Dynamic File Discovery
# Updated version with dynamic CSV file discovery for data_staging pipeline

# =================== IMPORTS ===================
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, Request, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Dict, Any, List, Optional
import asyncio
import uvicorn
import os
import sys
import json
import zipfile
import tempfile
import shutil
import time
import pandas as pd
from pathlib import Path
import uuid
import re
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add this near the top of main.py with other imports
try:
    from routers.archetype_router import safe_filename
    SAFE_FILENAME_AVAILABLE = True
except ImportError:
    SAFE_FILENAME_AVAILABLE = False
    def safe_filename(filename: str) -> str:
        """Fallback safe filename function"""
        clean_name = re.sub(r'[<>:"/\\|?*]', '-', filename)
        clean_name = re.sub(r'\s+', '_', clean_name)
        return clean_name[:100]

# =================== REQUEST MODELS ===================
class EnhancedDiagramRequest(BaseModel):
    diagram_type: str = "network_topology"
    data: Dict[str, Any] = {}
    quality_level: Optional[str] = "professional"
    output_format: Optional[str] = "lucid"
    use_csv: Optional[bool] = True
    
    @validator('output_format')
    def validate_format(cls, v):
        valid_formats = ["lucid", "document", "excel", "pdf", "all"]
        if v not in valid_formats:
            return "lucid"
        return v

class LegacyDocumentRequest(BaseModel):
    output_type: str = "all"
    data: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}

class MoveFileRequest(BaseModel):
    filename: str
    action: str  # "processed" or "failed"
    error: str = None
    sourceData: dict = None
    failedAt: str = None

class SaveTopologyRequest(BaseModel):
    filename: str
    data: dict

# =================== DYNAMIC FILE DISCOVERY SERVICE ===================
class FileDiscoveryService:
    """Dynamic file discovery service for data_staging pipeline"""
    
    def __init__(self, data_staging_dir: str = "data_staging"):
        self.data_staging_dir = Path(data_staging_dir)
        self.processed_dir = self.data_staging_dir / "processed"
        self.failed_dir = self.data_staging_dir / "failed"
        self.pending_dir = self.data_staging_dir  # Root level for pending files
    
    def get_latest_processed_csv(self, pattern: str = "*traffic*.csv") -> Optional[str]:
        """Get the most recently processed CSV file"""
        if not self.processed_dir.exists():
            return None
            
        csv_files = list(self.processed_dir.glob(pattern))
        if not csv_files:
            # Try broader pattern
            csv_files = list(self.processed_dir.glob("*.csv"))
        
        if not csv_files:
            return None
        
        # Sort by modification time, get the latest
        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        return latest_file.name
    
    def get_pending_csv_files(self, pattern: str = "*.csv") -> List[str]:
        """Get CSV files waiting to be processed (in root data_staging)"""
        csv_files = []
        for file_path in self.data_staging_dir.glob(pattern):
            # Only include files in root directory (not in subdirectories)
            if file_path.parent == self.data_staging_dir:
                csv_files.append(file_path.name)
        return sorted(csv_files, key=lambda f: (self.data_staging_dir / f).stat().st_mtime, reverse=True)
    
    def get_current_active_csv(self) -> Optional[str]:
        """Get the CSV file that should be used by the frontend
        Priority: 1) Latest processed, 2) Latest pending, 3) Legacy hardcoded file
        """
        # First, try to get latest processed file
        latest_processed = self.get_latest_processed_csv()
        if latest_processed:
            return f"processed/{latest_processed}"
        
        # If no processed files, check for pending files with traffic pattern
        pending_files = self.get_pending_csv_files("*traffic*.csv")
        if pending_files:
            return pending_files[0]  # Most recent pending
        
        # Check for any CSV files
        pending_files = self.get_pending_csv_files("*.csv")
        if pending_files:
            return pending_files[0]
        
        # Fallback to hardcoded legacy filename if it exists
        legacy_file = "updated_normalized_synthetic_traffic.csv"
        if (self.data_staging_dir / legacy_file).exists():
            return legacy_file
        
        return None
    
    def get_file_status_report(self) -> Dict:
        """Complete status of all CSV files in the pipeline"""
        processed_files = list(self.processed_dir.glob("*.csv")) if self.processed_dir.exists() else []
        failed_files = list(self.failed_dir.glob("*.csv")) if self.failed_dir.exists() else []
        pending_files = self.get_pending_csv_files()
        
        current_file = self.get_current_active_csv()
        
        return {
            "current_active_file": current_file,
            "current_endpoint": f"/data_staging/{current_file}" if current_file else None,
            "status": {
                "processed": {
                    "count": len(processed_files),
                    "files": [f.name for f in sorted(processed_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "failed": {
                    "count": len(failed_files), 
                    "files": [f.name for f in sorted(failed_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "pending": {
                    "count": len(pending_files),
                    "files": pending_files
                }
            },
            "last_updated": datetime.now().isoformat(),
            "pipeline_health": self._assess_pipeline_health(processed_files, failed_files, pending_files)
        }
    
    def _assess_pipeline_health(self, processed_files, failed_files, pending_files) -> Dict:
        """Assess the health of the data processing pipeline"""
        total_files = len(processed_files) + len(failed_files) + len(pending_files)
        
        if total_files == 0:
            return {"status": "no_data", "message": "No CSV files found in pipeline"}
        
        success_rate = len(processed_files) / total_files if total_files > 0 else 0
        
        if len(pending_files) > 5:
            return {"status": "backlog", "message": f"{len(pending_files)} files waiting to be processed"}
        elif success_rate < 0.8 and len(failed_files) > 0:
            return {"status": "issues", "message": f"High failure rate: {len(failed_files)} failed files"}
        elif len(processed_files) > 0:
            return {"status": "healthy", "message": "Pipeline operating normally"}
        else:
            return {"status": "initializing", "message": "No processed files yet"}

# =================== SERVICE IMPORTS WITH ERROR HANDLING ===================
try:
    from services.archetype_service import ArchetypeService
    ARCHETYPE_SERVICE_AVAILABLE = True
    logger.info("Archetype service imported successfully")
except ImportError as e:
    ARCHETYPE_SERVICE_AVAILABLE = False
    logger.warning(f"Archetype service not available: {e}")

try:
    from routers.archetype_router import router as archetype_router
    ARCHETYPE_ROUTER_AVAILABLE = True
    logger.info("Archetype router imported successfully")
except ImportError as e:
    ARCHETYPE_ROUTER_AVAILABLE = False
    logger.warning(f"Archetype router not available: {e}")
    from fastapi import APIRouter
    archetype_router = APIRouter()

try:
    from routers.excel_processing_router import router as excel_router
    EXCEL_ROUTER_AVAILABLE = True
    logger.info("Excel processing router imported successfully")
except ImportError as e:
    EXCEL_ROUTER_AVAILABLE = False
    logger.warning(f"Excel processing router not available: {e}")
    from fastapi import APIRouter
    excel_router = APIRouter()

# Enhanced Diagram Service
try:
    from services.enhanced_diagram_generator import EnhancedDiagramService
    DIAGRAM_SERVICE_AVAILABLE = True
    diagram_service = EnhancedDiagramService()
    logger.info("Enhanced Diagram Service loaded successfully")
except ImportError as e:
    DIAGRAM_SERVICE_AVAILABLE = False
    diagram_service = None
    logger.warning(f"Enhanced Diagram Service not available: {e}")

# Archetype Enhancement Service
try:
    from services.archetype_enhancement import ArchetypeEnhancementService
    enhancement_service = ArchetypeEnhancementService()
    ENHANCEMENT_AVAILABLE = True
    logger.info("Archetype Enhancement Service loaded")
except ImportError as e:
    ENHANCEMENT_AVAILABLE = False
    enhancement_service = None
    logger.warning(f"Archetype Enhancement Service not available: {e}")

# LucidChart Service
try:
    from services.archetype_lucid_stencils import LucidChartGenerator, ArchetypeLayoutEngine
    LUCIDCHART_SERVICE_AVAILABLE = True
    lucid_generator = LucidChartGenerator()
    logger.info("LucidChart Service loaded successfully")
except ImportError as e:
    LUCIDCHART_SERVICE_AVAILABLE = False
    lucid_generator = None
    logger.warning(f"LucidChart Service not available: {e}")
    
# =================== WEBSOCKET MANAGEMENT ===================
class WebSocketConnectionManager:
    """Manage WebSocket connections for Excel processing"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.processing_jobs: Dict[str, Any] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_job_update(self, job_id: str, update_data: dict):
        """Send job-specific update to all connected clients"""
        message = {
            "type": "job_update",
            "job_id": job_id,
            **update_data
        }
        await self.broadcast(message)
    
    def add_job(self, job_id: str, job_data: dict):
        """Add job to tracking"""
        self.processing_jobs[job_id] = {
            **job_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def update_job(self, job_id: str, updates: dict):
        """Update job data"""
        if job_id in self.processing_jobs:
            self.processing_jobs[job_id].update(updates)
            self.processing_jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job data"""
        return self.processing_jobs.get(job_id)
    
    def list_active_jobs(self) -> Dict[str, Any]:
        """List jobs that are queued or processing"""
        return {
            job_id: job for job_id, job in self.processing_jobs.items()
            if job.get("status") in ["queued", "processing"]
        }

# =================== CONFIGURATION ===================
class AppConfig:
    """Application configuration"""
    PROJECT_ROOT = project_root
    RESULTS_BASE_DIR = project_root / "results"
    DATA_STAGING_DIR = project_root / "data_staging"
    TEMPLATES_DIR = project_root / "templates"
    STATIC_DIR = project_root / "static"
    UI_DIR = project_root / "ui"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        dirs_to_create = [
            cls.RESULTS_BASE_DIR,
            cls.DATA_STAGING_DIR,
            cls.TEMPLATES_DIR,
            cls.STATIC_DIR,
            cls.UI_DIR
        ]
        
        # Create result subdirectories
        result_subdirs = ["visio", "lucid", "document", "excel", "pdf", "diagrams"]
        for subdir in result_subdirs:
            dirs_to_create.append(cls.RESULTS_BASE_DIR / subdir)
            
        # Create UI subdirectories
        ui_subdirs = ["css", "js", "html", "images"]
        for subdir in ui_subdirs:
            dirs_to_create.append(cls.UI_DIR / subdir)
        
        # Create data staging subdirectories
        staging_subdirs = ["processed", "failed"]
        for subdir in staging_subdirs:
            dirs_to_create.append(cls.DATA_STAGING_DIR / subdir)
        
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")

# =================== GLOBAL STATE ===================
class JobManager:
    """Simple job manager for tracking active jobs"""
    def __init__(self):
        self._jobs: Dict[str, Any] = {}
    
    def add_job(self, job_id: str, job_data: Dict[str, Any]):
        self._jobs[job_id] = job_data
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)
    
    def remove_job(self, job_id: str):
        if job_id in self._jobs:
            del self._jobs[job_id]
    
    def list_jobs(self) -> Dict[str, Any]:
        return self._jobs.copy()

# Global instances
file_discovery = FileDiscoveryService()
websocket_manager = WebSocketConnectionManager()
active_diagram_jobs = JobManager()

# Initialize directories
AppConfig.ensure_directories()

# =================== UTILITY FUNCTIONS ===================
def safe_path_join(base_dir: Path, filename: str) -> Optional[Path]:
    """Safely join paths to prevent directory traversal"""
    try:
        clean_filename = os.path.basename(filename)
        if not clean_filename or clean_filename in ('.', '..'):
            return None
        
        full_path = base_dir / clean_filename
        full_path.resolve().relative_to(base_dir.resolve())
        return full_path
    except (ValueError, OSError):
        logger.warning(f"Path traversal attempt detected: {filename}")
        return None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    clean_name = re.sub(r'[<>:"/\\|?*]', '-', filename)
    clean_name = re.sub(r'\s+', '_', clean_name)
    return clean_name[:100]

def create_fallback_lucid_xml(archetype: str, app_name: str, job_id: str) -> str:
    """Create fallback LucidChart XML when full service isn't available"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<lucidchart version="2.0" archetype="{archetype}" fallback_generation="true">
  <metadata>
    <title>{app_name} - {archetype.replace("_", " ").title()}</title>
    <archetype>{archetype}</archetype>
    <app_name>{app_name}</app_name>
    <job_id>{job_id}</job_id>
    <timestamp>{datetime.now().isoformat()}</timestamp>
    <generation_method>fallback</generation_method>
  </metadata>
  <canvas><width>900</width><height>700</height></canvas>
  <components>
    <component id="web" type="web_server">
      <n>{app_name} Web Server</n>
      <position><x>150</x><y>200</y></position>
      <styling>
        <fill_color>#4ECDC4</fill_color>
        <border_color>#45B7D1</border_color>
        <width>120</width><height>80</height>
        <shape_type>rectangle</shape_type>
      </styling>
    </component>
    <component id="api" type="api_service">
      <n>{app_name} API Service</n>
      <position><x>400</x><y>200</y></position>
      <styling>
        <fill_color>#FFD93D</fill_color>
        <border_color>#FFC312</border_color>
        <width>120</width><height>80</height>
        <shape_type>rectangle</shape_type>
      </styling>
    </component>
    <component id="db" type="database">
      <n>{app_name} Database</n>
      <position><x>650</x><y>200</y></position>
      <styling>
        <fill_color>#6C5CE7</fill_color>
        <border_color>#5F3DC4</border_color>
        <width>100</width><height>120</height>
        <shape_type>cylinder</shape_type>
      </styling>
    </component>
  </components>
  <connections>
    <connection from="web" to="api" type="http">
      <styling><color>#4ECDC4</color><width>2</width><style>solid</style><arrow>true</arrow></styling>
    </connection>
    <connection from="api" to="db" type="sql">
      <styling><color>#6C5CE7</color><width>2</width><style>solid</style><arrow>true</arrow></styling>
    </connection>
  </connections>
</lucidchart>'''

def _get_demo_applications():
    """Get demo applications when CSV is not available"""
    return [
        {
            "id": "demo-web-portal",
            "name": "Customer Web Portal",
            "type": "web_application",
            "owner": "Digital Banking Team"
        },
        {
            "id": "demo-core-banking",
            "name": "Core Banking System",
            "type": "mainframe_system",
            "owner": "Core Systems Team"
        },
        {
            "id": "demo-payment-engine",
            "name": "Payment Processing Engine",
            "type": "service",
            "owner": "Payments Team"
        },
        {
            "id": "demo-customer-db",
            "name": "Customer Database",
            "type": "database",
            "owner": "Data Management Team"
        }
    ]

def _get_pipeline_recommendations(status: dict) -> List[str]:
    """Get recommendations based on pipeline status"""
    recommendations = []
    pipeline_health = status.get("pipeline_health", {})
    
    if pipeline_health.get("status") == "no_data":
        recommendations.append("Add CSV files to data_staging/ directory to begin processing")
    elif pipeline_health.get("status") == "backlog":
        recommendations.append("Consider investigating processing delays - multiple files are pending")
    elif pipeline_health.get("status") == "issues":
        recommendations.append("Check failed files in data_staging/failed/ directory")
        recommendations.append("Review processing logs for error details")
    elif pipeline_health.get("status") == "healthy":
        recommendations.append("Pipeline is operating normally")
    
    files = status.get("status", {})
    if files.get("pending", {}).get("count", 0) > 0:
        recommendations.append("Files are waiting to be processed")
    
    return recommendations

def ensure_pipeline_directories():
    """Ensure all pipeline directories exist"""
    directories = [
        Path("data_staging"),
        Path("data_staging/processed"),
        Path("data_staging/failed"),
        Path("results")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# =================== LUCIDCHART SETUP ===================
def check_lucidchart_setup():
    """Check LucidChart service setup and create necessary directories"""
    setup_status = {
        "service_available": LUCIDCHART_SERVICE_AVAILABLE,
        "template_files": {},
        "directories": {},
        "ready": False
    }
    
    # Check directories
    try:
        lucid_dir = AppConfig.RESULTS_BASE_DIR / "lucid"
        lucid_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = lucid_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
        setup_status["directories"]["lucid_results"] = {
            "path": str(lucid_dir),
            "exists": True,
            "writable": True
        }
    except Exception as e:
        setup_status["directories"]["lucid_results"] = {
            "path": str(AppConfig.RESULTS_BASE_DIR / "lucid"),
            "exists": False,
            "error": str(e)
        }
    
    # Check template files
    template_files = [
        ("stencil_library", "templates/stencil_library.yaml"),
        ("layout_templates", "templates/layout_templates.yaml"),
        ("archetype_templates", "templates/archetype_templates.yaml")
    ]
    
    for template_name, template_path in template_files:
        path = AppConfig.PROJECT_ROOT / template_path
        setup_status["template_files"][template_name] = {
            "path": str(path),
            "exists": path.exists(),
            "required": template_name in ["stencil_library", "layout_templates"]
        }
        
        if path.exists():
            try:
                import yaml
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    setup_status["template_files"][template_name]["valid"] = True
                    setup_status["template_files"][template_name]["keys"] = list(data.keys())
            except Exception as e:
                setup_status["template_files"][template_name]["valid"] = False
                setup_status["template_files"][template_name]["error"] = str(e)
    
    directories_ok = setup_status["directories"].get("lucid_results", {}).get("exists", False)
    setup_status["ready"] = LUCIDCHART_SERVICE_AVAILABLE or directories_ok
    
    return setup_status

# =================== WEBSOCKET HANDLERS ===================
async def handle_websocket_message(message: dict, websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type", "unknown")
    
    if message_type == "ping":
        await websocket_manager.send_personal_message({
            "type": "pong", 
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
    elif message_type == "get_pipeline_status":
        pipeline_status = file_discovery.get_file_status_report()
        await websocket_manager.send_personal_message({
            "type": "pipeline_status",
            **pipeline_status
        }, websocket)
        
    elif message_type == "get_job_status":
        job_id = message.get("job_id")
        if job_id:
            job = websocket_manager.get_job(job_id)
            await websocket_manager.send_personal_message({
                "type": "job_status",
                "job_id": job_id,
                "job": job
            }, websocket)
        else:
            await websocket_manager.send_personal_message({
                "type": "error",
                "message": "job_id required"
            }, websocket)
            
    elif message_type == "get_all_jobs":
        active_jobs = websocket_manager.list_active_jobs()
        await websocket_manager.send_personal_message({
            "type": "all_jobs",
            "jobs": active_jobs
        }, websocket)
        
    elif message_type == "subscribe_job":
        job_id = message.get("job_id")
        # Could implement job-specific subscriptions here
        await websocket_manager.send_personal_message({
            "type": "subscribed",
            "job_id": job_id
        }, websocket)
        
    else:
        logger.warning(f"Unknown WebSocket message type: {message_type}")

# =================== EXCEL PROCESSING BACKGROUND TASK ===================
async def process_excel_background(job_id: str, file_data: dict):
    """Background Excel processing with WebSocket updates"""
    try:
        # Update to processing
        websocket_manager.update_job(job_id, {
            "status": "processing",
            "progress": 10,
            "message": "Processing Excel file..."
        })
        
        # Only send WebSocket if there are connections
        if websocket_manager.active_connections:
            await websocket_manager.send_job_update(job_id, {
                "status": "processing", 
                "progress": 10,
                "message": "Processing Excel file..."
            })
        
        # Simulate processing steps
        for progress, message in [
            (30, "Reading Excel data..."),
            (50, "Analyzing applications..."),
            (70, "Classifying architectures..."),
            (90, "Generating results...")
        ]:
            await asyncio.sleep(2)  # Simulate work
            websocket_manager.update_job(job_id, {
                "progress": progress,
                "message": message
            })
            
            # Only send WebSocket updates if there are active connections
            if websocket_manager.active_connections:
                try:
                    await websocket_manager.send_job_update(job_id, {
                        "progress": progress,
                        "message": message
                    })
                except Exception as ws_error:
                    logger.warning(f"WebSocket update failed for job {job_id}: {ws_error}")
        
        # Complete
        websocket_manager.update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "Processing completed successfully"
        })
        
        if websocket_manager.active_connections:
            await websocket_manager.send_job_update(job_id, {
                "status": "completed",
                "progress": 100, 
                "message": "Processing completed successfully"
            })
        
    except Exception as e:
        logger.error(f"Excel processing error for job {job_id}: {e}")
        websocket_manager.update_job(job_id, {
            "status": "error",
            "error": str(e)
        })
        
        if websocket_manager.active_connections:
            try:
                await websocket_manager.send_job_update(job_id, {
                    "status": "error",
                    "error": str(e)
                })
            except Exception as ws_error:
                logger.warning(f"Failed to send error update via WebSocket: {ws_error}")

# =================== BACKGROUND TASK UTILITIES ===================
# process-all worker state & helpers - MOVED TO MODULE LEVEL
_process_all_lock = threading.Lock()
_process_all_state = {
    "running": False,
    "action": None,
    "started_at": None,
    "finished_at": None,
    "moved": 0,
    "errors": [],      # list of {"filename": "...", "error": "..."}
    "accepted": 0,     # how many files the job accepted initially
}

def _move_one_file_internal(filename: str, action: str = "processed", error: str | None = None, source_data: dict | None = None):
    """Pure python helper that mirrors POST /api/v1/data/move behavior."""
    data_staging_dir = Path("data_staging")
    source_file = data_staging_dir / filename
    if not source_file.exists():
        raise FileNotFoundError(f"Source file {filename} not found")

    if action == "processed":
        dest_dir = data_staging_dir / "processed"
        ts_key = "processed_at"
    elif action == "failed":
        dest_dir = data_staging_dir / "failed"
        ts_key = "failed_at"
    else:
        raise ValueError(f"Invalid action: {action}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / filename

    # move the csv
    shutil.move(str(source_file), str(dest_file))

    # write sidecar metadata
    meta = {
        "filename": filename,
        ts_key: datetime.now().isoformat(),
        "action": action,
        "error": error,
        "source_data": source_data or {},
    }
    with open(dest_dir / f"{filename}.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def _gather_pending_root_only():
    """Return root-level pending CSVs (excludes subfolders and applicationList.csv)."""
    data_staging_dir = Path("data_staging")
    if not data_staging_dir.exists():
        return []

    files = []
    for fp in data_staging_dir.glob("*.csv"):
        if fp.name == "applicationList.csv":
            continue
        if fp.parent != data_staging_dir:
            continue
        files.append(fp)
    # newest first
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.name for f in files]

def _process_all_job(action: str = "processed"):
    """Run in a background task: move every pending file to action (processed|failed)."""
    global _process_all_state
    
    try:
        pending = _gather_pending_root_only()
        
        with _process_all_lock:
            _process_all_state["accepted"] = len(pending)
        
        for name in pending:
            try:
                _move_one_file_internal(name, action=action)
                with _process_all_lock:
                    _process_all_state["moved"] += 1
            except Exception as e:
                with _process_all_lock:
                    _process_all_state["errors"].append({"filename": name, "error": str(e)})
    except Exception as global_error:
        with _process_all_lock:
            _process_all_state["errors"].append({
                "filename": "GLOBAL_ERROR", 
                "error": str(global_error)
            })
    finally:
        with _process_all_lock:
            _process_all_state["running"] = False
            _process_all_state["finished_at"] = datetime.now().isoformat()

# =================== ENDPOINT SETUP FUNCTIONS ===================
def setup_websocket_endpoints(app: FastAPI):
    """Setup WebSocket endpoints for real-time communication"""
    
    @app.websocket("/ws")
    async def main_websocket_endpoint(websocket: WebSocket):
        """Main WebSocket endpoint for Excel processing and general updates"""
        await websocket_manager.connect(websocket)
        
        try:
            while True:
                try:
                    # Wait for messages with timeout to send heartbeat
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    try:
                        message = json.loads(data)
                        await handle_websocket_message(message, websocket)
                    except json.JSONDecodeError:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }, websocket)
                        
                except asyncio.TimeoutError:
                    # Send heartbeat with pipeline status
                    pipeline_status = file_discovery.get_file_status_report()
                    await websocket_manager.send_personal_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "active_jobs": len(websocket_manager.list_active_jobs()),
                        "pipeline_health": pipeline_status["pipeline_health"],
                        "current_csv": pipeline_status["current_active_file"]
                    }, websocket)
                    
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            websocket_manager.disconnect(websocket)
    
    @app.websocket("/api/v1/excel/ws")  
    async def excel_websocket_endpoint(websocket: WebSocket):
        """Dedicated Excel processing WebSocket endpoint"""
        await websocket_manager.connect(websocket)
        
        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    try:
                        message = json.loads(data)
                        message["source"] = "excel_ws"  # Mark source
                        await handle_websocket_message(message, websocket)
                    except json.JSONDecodeError:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }, websocket)
                        
                except asyncio.TimeoutError:
                    pipeline_status = file_discovery.get_file_status_report()
                    await websocket_manager.send_personal_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "active_excel_jobs": len([
                            j for j in websocket_manager.processing_jobs.values() 
                            if j.get("job_type") == "excel_processing"
                        ]),
                        "pipeline_health": pipeline_status["pipeline_health"]
                    }, websocket)
                    
        except WebSocketDisconnect:
            logger.info("Excel WebSocket client disconnected normally")
        except Exception as e:
            logger.error(f"Excel WebSocket error: {e}")
        finally:
            websocket_manager.disconnect(websocket)
    
    # WebSocket health check endpoint
    @app.get("/api/v1/ws/health")
    async def websocket_health():
        """WebSocket service health check"""
        pipeline_status = file_discovery.get_file_status_report()
        return {
            "status": "healthy",
            "active_connections": len(websocket_manager.active_connections),
            "active_jobs": len(websocket_manager.processing_jobs),
            "pipeline_health": pipeline_status["pipeline_health"],
            "current_csv": pipeline_status["current_active_file"],
            "websocket_endpoints": [
                "/ws",
                "/api/v1/excel/ws"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info("WebSocket endpoints configured")

def setup_file_discovery_endpoints(app: FastAPI):
    """Setup dynamic file discovery endpoints"""
    
    @app.get("/api/v1/data/status")
    async def get_data_pipeline_status():
        """Get complete status of the data processing pipeline"""
        try:
            return file_discovery.get_file_status_report()
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "status": "error"}
            )

    @app.get("/api/v1/data/current")
    async def get_current_csv():
        """Return available normalized CSV files with priority logic"""
        try:
            data_dir = project_root / "data_staging"
            
            # Check processed folder first for ready files
            processed_dir = data_dir / "processed"
            if processed_dir.exists():
                processed_files = list(processed_dir.glob("*_normalized_*.csv"))
                if processed_files:
                    # Sort by modification time (newest first)
                    sorted_files = sorted(processed_files, key=lambda f: f.stat().st_mtime, reverse=True)
                    
                    # Prefer XECHK files if available
                    xechk_files = [f for f in sorted_files if f.name.startswith('XECHK')]
                    primary_file = xechk_files[0] if xechk_files else sorted_files[0]
                    
                    return {
                        "endpoint": f"/data_staging/processed/{primary_file.name}",
                        "filename": primary_file.name, 
                        "status": "ready",
                        "source": "processed_folder",
                        "pipeline_health": {"status": "healthy"}
                    }
            
            # Fallback: check main data_staging folder for normalized files
            normalized_files = [f for f in data_dir.glob("*_normalized_*.csv")]
            
            if normalized_files:
                # Sort by modification time
                sorted_files = sorted(normalized_files, key=lambda f: f.stat().st_mtime, reverse=True)
                
                # Prefer XECHK files if both exist
                xechk_files = [f for f in sorted_files if f.name.startswith('XECHK')]
                primary_file = xechk_files[0] if xechk_files else sorted_files[0]
                
                return {
                    "endpoint": f"/data_staging/{primary_file.name}",
                    "filename": primary_file.name, 
                    "status": "available",
                    "source": "main_folder",
                    "pipeline_health": {"status": "healthy"}
                }
            else:
                # No files found - return 404 gracefully
                return JSONResponse(status_code=404, content={
                    "error": "No normalized CSV files found", 
                    "status": "no_data",
                    "message": "Add CSV files to data_staging/ or data_staging/processed/",
                    "pipeline_health": {"status": "no_data"}
                })
                
        except Exception as e:
            logger.error(f"Error in get_current_csv: {e}")
            return JSONResponse(status_code=500, content={
                "error": f"Server error: {str(e)}", 
                "status": "error",
                "pipeline_health": {"status": "error"}
            })
            
    @app.get("/api/v1/data/files")
    async def list_all_csv_files():
        """List all CSV files in the pipeline with details"""
        try:
            status = file_discovery.get_file_status_report()
            return {
                "success": True,
                "current_file": status["current_active_file"],
                "files": status["status"],
                "pipeline_health": status["pipeline_health"],
                "recommendations": _get_pipeline_recommendations(status)
            }
        except Exception as e:
            logger.error(f"Error listing CSV files: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "success": False}
            )
    
    logger.info("Dynamic file discovery endpoints added")

def setup_file_movement_endpoints(app: FastAPI):
    """Setup file movement and topology endpoints"""
    
    @app.get("/api/v1/data/processed/{filename}")
    async def get_processed_file(filename: str):
        """Serve files from processed directory"""
        try:
            processed_dir = project_root / "data_staging" / "processed"
            file_path = safe_path_join(processed_dir, filename)
            
            if file_path and file_path.exists():
                return FileResponse(path=str(file_path), filename=filename)
            else:
                raise HTTPException(status_code=404, detail=f"Processed file not found: {filename}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error serving processed file: {str(e)}")

    @app.get("/api/v1/data/failed/{filename}")  
    async def get_failed_file(filename: str):
        """Serve files from failed directory"""
        try:
            failed_dir = project_root / "data_staging" / "failed"
            file_path = safe_path_join(failed_dir, filename)
            
            if file_path and file_path.exists():
                return FileResponse(path=str(file_path), filename=filename)
            else:
                raise HTTPException(status_code=404, detail=f"Failed file not found: {filename}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error serving failed file: {str(e)}")
    
    @app.post("/api/v1/data/move")
    async def move_file(request: MoveFileRequest):
        """Move file from data_staging to processed or failed directory"""
        try:
            # Define paths
            data_staging_dir = Path("data_staging")
            source_file = data_staging_dir / request.filename
            
            # Ensure source file exists
            if not source_file.exists():
                raise HTTPException(status_code=404, detail=f"Source file {request.filename} not found")
            
            # Determine destination based on action
            if request.action == "processed":
                dest_dir = data_staging_dir / "processed"
                dest_file = dest_dir / request.filename
                
                # Create processed directory if it doesn't exist
                dest_dir.mkdir(exist_ok=True)
                
                # Move the file
                shutil.move(str(source_file), str(dest_file))
                
                # Create processing metadata
                metadata = {
                    "filename": request.filename,
                    "processed_at": datetime.now().isoformat(),
                    "action": "processed",
                    "source_data": request.sourceData or {}
                }
                
                # Save metadata file
                metadata_file = dest_dir / f"{request.filename}.meta.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return {
                    "success": True,
                    "action": "processed",
                    "source_path": str(source_file),
                    "destination_path": str(dest_file),
                    "metadata": metadata
                }
                
            elif request.action == "failed":
                dest_dir = data_staging_dir / "failed"
                dest_file = dest_dir / request.filename
                
                # Create failed directory if it doesn't exist
                dest_dir.mkdir(exist_ok=True)
                
                # Move the file
                shutil.move(str(source_file), str(dest_file))
                
                # Create failure metadata
                metadata = {
                    "filename": request.filename,
                    "failed_at": request.failedAt or datetime.now().isoformat(),
                    "action": "failed",
                    "error": request.error,
                    "source_data": request.sourceData or {}
                }
                
                # Save metadata file
                metadata_file = dest_dir / f"{request.filename}.meta.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return {
                    "success": True,
                    "action": "failed",
                    "source_path": str(source_file),
                    "destination_path": str(dest_file),
                    "error": request.error,
                    "metadata": metadata
                }
            else:
                raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to move file: {str(e)}")

    @app.get("/api/v1/data/pending")
    async def list_pending_files():
        """List files in data_staging directory waiting to be processed"""
        try:
            data_staging_dir = Path("data_staging")
            
            if not data_staging_dir.exists():
                return {"files": [], "count": 0}
            
            # Get all CSV files in data_staging (excluding applicationList.csv)
            csv_files = []
            for file_path in data_staging_dir.glob("*.csv"):
                if file_path.name != "applicationList.csv":  # Skip static file
                    file_info = {
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "path": str(file_path)
                    }
                    csv_files.append(file_info)
            
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: x["modified"], reverse=True)
            
            return {
                "files": csv_files,
                "count": len(csv_files),
                "directory": str(data_staging_dir)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list pending files: {str(e)}")

    @app.post("/api/v1/data/process-all")
    async def process_all_files(background_tasks: BackgroundTasks, action: str = "processed"):
        """
        Kick off a background job that promotes every root-level pending CSV in data_staging/
        to /processed (or /failed if action='failed').
        """
        if action not in ("processed", "failed"):
            raise HTTPException(status_code=400, detail="action must be 'processed' or 'failed'")

        with _process_all_lock:
            if _process_all_state["running"]:
                return {
                    "status": "already_running",
                    "action": _process_all_state["action"],
                    "started_at": _process_all_state["started_at"],
                    "moved": _process_all_state["moved"],
                    "accepted": _process_all_state["accepted"],
                    "errors": _process_all_state["errors"],
                }
            # initialize new job state
            _process_all_state.update({
                "running": True,
                "action": action,
                "started_at": datetime.now().isoformat(),
                "finished_at": None,
                "moved": 0,
                "errors": [],
                "accepted": 0,
            })

        # start the job
        background_tasks.add_task(_process_all_job, action)
        # immediate response
        pending_now = _gather_pending_root_only()
        return {
            "status": "started",
            "action": action,
            "pending_detected": len(pending_now),
            "note": "Job runs in background; poll /api/v1/data/process-all/status for progress."
        }

    @app.get("/api/v1/data/process-all/status")
    async def process_all_status():
        """Return progress of the process-all background job + current pending count."""
        return {
            **_process_all_state,
            "pending_now": len(_gather_pending_root_only())
        }
        
    @app.get("/api/v1/data/directories")
    async def check_pipeline_directories():
        """Check status of pipeline directories"""
        try:
            data_staging_dir = Path("data_staging")
            directories = {
                "data_staging": data_staging_dir,
                "processed": data_staging_dir / "processed",
                "failed": data_staging_dir / "failed"
            }
            
            status = {}
            for name, dir_path in directories.items():
                status[name] = {
                    "exists": dir_path.exists(),
                    "path": str(dir_path),
                    "is_directory": dir_path.is_dir() if dir_path.exists() else False
                }
                
                if dir_path.exists() and dir_path.is_dir():
                    # Count files in directory
                    csv_files = list(dir_path.glob("*.csv"))
                    status[name]["csv_file_count"] = len(csv_files)
                    status[name]["csv_files"] = [f.name for f in csv_files]
            
            return status
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to check directories: {str(e)}")

    @app.post("/api/v1/topology/save")
    async def save_topology(request: SaveTopologyRequest):
        """Save network topology to results directory"""
        try:
            # Create results directory if it doesn't exist
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # Define the file path
            file_path = results_dir / request.filename
            
            # Save the topology data
            with open(file_path, 'w') as f:
                json.dump(request.data, f, indent=2)
            
            # Get file info
            file_info = {
                "filename": request.filename,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "created": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "message": f"Topology saved successfully",
                "file_info": file_info
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save topology: {str(e)}")

    @app.get("/api/v1/topology/list")
    async def list_saved_topologies():
        """List all saved topology files"""
        try:
            results_dir = Path("results")
            
            if not results_dir.exists():
                return {"topologies": [], "count": 0}
            
            # Get all JSON files in results directory
            topology_files = []
            for file_path in results_dir.glob("*.json"):
                if file_path.name.startswith("netseg_topology_"):
                    file_info = {
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "path": str(file_path)
                    }
                    topology_files.append(file_info)
            
            # Sort by creation time (newest first)
            topology_files.sort(key=lambda x: x["created"], reverse=True)
            
            return {
                "topologies": topology_files,
                "count": len(topology_files),
                "directory": str(results_dir)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list topologies: {str(e)}")

    @app.get("/api/v1/data/status/enhanced")
    async def get_enhanced_data_status():
        """Get comprehensive data pipeline status"""
        try:
            data_staging_dir = Path("data_staging")
            
            # Count files in each directory
            pending_files = list(data_staging_dir.glob("*.csv"))
            pending_files = [f for f in pending_files if f.name != "applicationList.csv"]
            
            processed_dir = data_staging_dir / "processed"
            processed_files = list(processed_dir.glob("*.csv")) if processed_dir.exists() else []
            
            failed_dir = data_staging_dir / "failed"
            failed_files = list(failed_dir.glob("*.csv")) if failed_dir.exists() else []
            
            # Get current file (most recent in data_staging)
            current_file = None
            if pending_files:
                current_file = max(pending_files, key=lambda f: f.stat().st_mtime)
            
            status = {
                "pipeline_health": {
                    "status": "healthy" if len(pending_files) > 0 else "no_pending_files",
                    "message": f"{len(pending_files)} files pending processing"
                },
                "status": {
                    "pending": {
                        "count": len(pending_files),
                        "files": [f.name for f in pending_files]
                    },
                    "processed": {
                        "count": len(processed_files),
                        "files": [f.name for f in processed_files[-5:]]  # Last 5 only
                    },
                    "failed": {
                        "count": len(failed_files),
                        "files": [f.name for f in failed_files[-5:]]  # Last 5 only
                    }
                },
                "current_active_file": current_file.name if current_file else None,
                "directories": {
                    "data_staging": str(data_staging_dir),
                    "processed": str(processed_dir),
                    "failed": str(failed_dir)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get enhanced status: {str(e)}")
    
    logger.info("File movement endpoints added")

def setup_excel_integration(app: FastAPI):
    """Setup Excel processing endpoints that work with main WebSocket"""
    
    @app.post("/api/v1/excel/process")
    async def process_excel_main(
        background_tasks: BackgroundTasks,
        file_data: dict  # Simplified for demo - in real implementation use UploadFile
    ):
        """Excel processing endpoint integrated with main WebSocket"""
        
        job_id = str(uuid.uuid4())
        
        # Add job to WebSocket manager
        websocket_manager.add_job(job_id, {
            "job_id": job_id,
            "job_type": "excel_processing", 
            "status": "queued",
            "progress": 0,
            "message": "Job created",
            "filename": file_data.get("filename", "unknown.xlsx")
        })
        
        # Send initial update via WebSocket
        await websocket_manager.send_job_update(job_id, {
            "status": "queued",
            "progress": 0,
            "message": "Excel processing job created"
        })
        
        # Start background processing
        background_tasks.add_task(process_excel_background, job_id, file_data)
        
        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Excel processing started",
            "websocket_support": True
        }
    
    @app.get("/api/v1/excel/job/{job_id}")
    async def get_excel_job_status(job_id: str):
        """Get Excel job status"""
        job = websocket_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    
    logger.info("Excel processing integration endpoints added")

def setup_lucidchart_endpoints(app: FastAPI):
    """Setup LucidChart-related endpoints"""
    
    @app.get("/api/v1/lucidchart/status")
    async def get_lucidchart_status():
        """Get comprehensive LucidChart service status"""
        try:
            setup_status = check_lucidchart_setup()
            
            setup_status["runtime"] = {
                "enhancement_service": ENHANCEMENT_AVAILABLE,
                "diagram_service": DIAGRAM_SERVICE_AVAILABLE,
                "project_root": str(AppConfig.PROJECT_ROOT),
                "websocket_connections": len(websocket_manager.active_connections)
            }
            
            try:
                lucid_dir = AppConfig.RESULTS_BASE_DIR / "lucid"
                if lucid_dir.exists():
                    existing_files = list(lucid_dir.glob("*.lucid"))
                    setup_status["existing_files"] = {
                        "count": len(existing_files),
                        "files": [f.name for f in existing_files[-5:]],
                        "total_size": sum(f.stat().st_size for f in existing_files)
                    }
            except Exception as e:
                setup_status["existing_files"] = {"error": str(e)}
            
            return setup_status
        except Exception as e:
            logger.error(f"Error getting LucidChart status: {e}")
            return {"error": str(e), "service_available": False}
    
    @app.post("/api/v1/lucidchart/test-generation/{archetype}")
    async def test_lucidchart_generation(archetype: str, app_name: str = "TestApp"):
        """Generate test LucidChart file"""
        try:
            results_dir = AppConfig.RESULTS_BASE_DIR / "lucid"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            job_id = str(uuid.uuid4())[:8]
            clean_app_name = sanitize_filename(app_name)
            
            filename = f"{clean_app_name}_{archetype}_{job_id}.lucid"
            file_path = results_dir / filename
            
            if LUCIDCHART_SERVICE_AVAILABLE:
                try:
                    from services.archetype_lucid_stencils import ArchetypeType
                    
                    archetype_mapping = {
                        "monolithic": ArchetypeType.MONOLITHIC,
                        "three_tier": ArchetypeType.THREE_TIER,
                        "microservices": ArchetypeType.MICROSERVICES,
                        "event_driven": ArchetypeType.EVENT_DRIVEN,
                        "soa": ArchetypeType.SOA,
                        "serverless": ArchetypeType.SERVERLESS
                    }
                    
                    archetype_type = archetype_mapping.get(archetype, ArchetypeType.THREE_TIER)
                    
                    test_apps = [
                        {"id": "app1", "name": f"{clean_app_name} Frontend", "type": "web"},
                        {"id": "app2", "name": f"{clean_app_name} API", "type": "api"},
                        {"id": "app3", "name": f"{clean_app_name} Database", "type": "database"}
                    ]
                    
                    xml_content = lucid_generator.generate_lucidchart_xml(archetype_type, test_apps)
                    generation_method = "full_service"
                    
                except Exception as service_error:
                    logger.warning(f"LucidChart service error, using fallback: {service_error}")
                    xml_content = create_fallback_lucid_xml(archetype, clean_app_name, job_id)
                    generation_method = "fallback_after_service_error"
            else:
                xml_content = create_fallback_lucid_xml(archetype, clean_app_name, job_id)
                generation_method = "basic_fallback"
            
            file_path.write_text(xml_content, encoding='utf-8')
            
            return {
                "success": True,
                "archetype": archetype,
                "app_name": clean_app_name,
                "job_id": job_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(xml_content),
                "generation_method": generation_method,
                "download_url": f"/api/v1/diagram/download/{filename}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LucidChart test generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "archetype": archetype,
                "app_name": app_name
            }
    
    logger.info("LucidChart management endpoints added")

def setup_diagram_endpoints(app: FastAPI):
    """Setup Enhanced Diagram Service endpoints"""
    
    @app.post("/api/v1/diagram/generate-enhanced-diagram-by-format")
    async def generate_enhanced_diagram(request: EnhancedDiagramRequest):
        """Main endpoint for generating enhanced diagrams with dynamic CSV discovery"""
        try:
            if not DIAGRAM_SERVICE_AVAILABLE:
                raise HTTPException(status_code=503, detail="Diagram service not available")
            
            data = request.data.copy()
            
            # Load CSV data if requested or no applications provided
            if request.use_csv or not data.get("applications"):
                # Use dynamic file discovery to get the current CSV
                current_csv = file_discovery.get_current_active_csv()
                
                if current_csv:
                    csv_path = AppConfig.DATA_STAGING_DIR / current_csv
                    logger.info(f"Using dynamically discovered CSV: {current_csv}")
                else:
                    # Fallback to legacy filename
                    csv_path = AppConfig.DATA_STAGING_DIR / "applicationList.csv"
                    logger.info("Using fallback CSV: applicationList.csv")
                
                if csv_path.exists():
                    try:
                        try:
                            df = pd.read_csv(csv_path, encoding='utf-8')
                        except UnicodeDecodeError:
                            df = pd.read_csv(csv_path, encoding='windows-1252')
                            
                        applications = []
                        for _, row in df.iterrows():
                            applications.append({
                                "id": row.get("id", f"app_{len(applications)}"),
                                "name": row.get("name", f"Application_{len(applications)}"),
                                "type": row.get("type", "application"),
                                "owner": row.get("owner", "Unknown")
                            })
                        data["applications"] = applications
                        data["csv_source"] = str(csv_path.name)
                        logger.info(f"Loaded {len(applications)} applications from {csv_path.name}")
                    except Exception as e:
                        logger.error(f"Error reading CSV {csv_path}: {e}")
                        data["applications"] = _get_demo_applications()
                        data["csv_source"] = "demo_data"
                else:
                    data["applications"] = _get_demo_applications()
                    data["csv_source"] = "demo_data"
                    logger.info("No CSV file found, using demo applications")
            
            result = await diagram_service.generate_enhanced_diagram_by_format(
                diagram_type=request.diagram_type,
                data=data,
                output_format=request.output_format,
                quality_level=request.quality_level
            )
            
            if result.get("success"):
                job_id = result.get("job_id")
                active_diagram_jobs.add_job(job_id, result)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Diagram generation error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": str(e),
                    "error_type": "diagram_generation_error"
                }
            )
    
    @app.get("/api/v1/diagram/download/{filename}")
    async def download_file(filename: str):
        """Download a specific generated file with security checks"""
        try:
            if not filename or '..' in filename or '/' in filename or '\\' in filename:
                raise HTTPException(status_code=400, detail="Invalid filename")
            
            base_dir = AppConfig.RESULTS_BASE_DIR
            subdirs = ["visio", "lucid", "document", "excel", "pdf"]
            
            for subdir in subdirs:
                file_path = safe_path_join(base_dir / subdir, filename)
                if file_path and file_path.exists():
                    return FileResponse(
                        path=str(file_path),
                        filename=filename,
                        media_type="application/octet-stream"
                    )
            
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/diagram/job-status/{job_id}")
    async def get_job_status(job_id: str):
        """Get the status of a generation job"""
        try:
            job = active_diagram_jobs.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "completed" if job.get("success") else "failed",
                "files": job.get("files", []),
                "quality_level": job.get("quality_level"),
                "processing_time": job.get("processing_time"),
                "csv_source": job.get("csv_source")
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Job status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    logger.info("Enhanced Diagram Service endpoints added")

def setup_basic_endpoints(app: FastAPI):
    """Setup basic endpoints"""
    
    @app.get("/")
    async def root():
        """Redirect to the main application"""
        try:
            index_path = AppConfig.STATIC_DIR / "index.html"
            if index_path.exists():
                return RedirectResponse(url="/static/index.html", status_code=302)
            else:
                return {"message": "API is running", "docs": "/docs", "health": "/health"}
        except Exception as e:
            logger.error(f"Root endpoint error: {e}")
            return {"error": "Service error", "docs": "/docs"}

    @app.get("/index.html")
    async def index_redirect():
        """Redirect index.html requests to static version"""
        try:
            index_path = AppConfig.STATIC_DIR / "index.html"
            if index_path.exists():
                return RedirectResponse(url="/static/index.html", status_code=302)
            else:
                raise HTTPException(status_code=404, detail="Index file not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Index redirect error: {e}")
            raise HTTPException(status_code=500, detail="Server error")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint with pipeline status"""
        try:
            pipeline_status = file_discovery.get_file_status_report()
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "diagram_service": DIAGRAM_SERVICE_AVAILABLE,
                    "lucidchart_service": LUCIDCHART_SERVICE_AVAILABLE,
                    "enhancement_service": ENHANCEMENT_AVAILABLE,
                    "archetype_router": ARCHETYPE_ROUTER_AVAILABLE,
                    "excel_router": EXCEL_ROUTER_AVAILABLE
                },
                "websocket": {
                    "active_connections": len(websocket_manager.active_connections),
                    "active_jobs": len(websocket_manager.processing_jobs),
                    "endpoints": ["/ws", "/api/v1/excel/ws"]
                },
                "directories": {
                    "results": AppConfig.RESULTS_BASE_DIR.exists(),
                    "data_staging": AppConfig.DATA_STAGING_DIR.exists(),
                    "templates": AppConfig.TEMPLATES_DIR.exists(),
                    "static": AppConfig.STATIC_DIR.exists(),
                    "ui": AppConfig.UI_DIR.exists()
                },
                "data_pipeline": {
                    "current_csv": pipeline_status["current_active_file"],
                    "health": pipeline_status["pipeline_health"],
                    "file_counts": {
                        "processed": pipeline_status["status"]["processed"]["count"],
                        "failed": pipeline_status["status"]["failed"]["count"],
                        "pending": pipeline_status["status"]["pending"]["count"]
                    }
                },
                "version": "2.3.0"
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @app.get("/api/info")
    async def api_info():
        """API information endpoint"""
        try:
            capabilities = [
                "Application Portfolio Management",
                "Network Topology Discovery",
                "Documentation Generation",
                "Real-time WebSocket Communication",
                "Dynamic CSV File Discovery",
                "Data Processing Pipeline Management"
            ]
            
            if DIAGRAM_SERVICE_AVAILABLE:
                capabilities.extend([
                    "Enhanced Diagram Generation",
                    "Professional Word Documents",
                    "Excel Data Exports",
                    "PDF Report Generation"
                ])
            
            if LUCIDCHART_SERVICE_AVAILABLE:
                capabilities.extend([
                    "LucidChart Diagram Generation",
                    "Archetype-Optimized Layouts",
                    "Professional XML Export"
                ])
            
            pipeline_status = file_discovery.get_file_status_report()
            
            return {
                "platform": "Application Auto-Discovery with Enhanced Document Generation",
                "version": "2.3.0",
                "capabilities": capabilities,
                "supported_formats": ["lucid", "document", "excel", "pdf"],
                "websocket_endpoints": ["/ws", "/api/v1/excel/ws"],
                "data_endpoints": ["/api/v1/data/status", "/api/v1/data/current", "/api/v1/data/files"],
                "services": {
                    "diagram_service": DIAGRAM_SERVICE_AVAILABLE,
                    "lucidchart_service": LUCIDCHART_SERVICE_AVAILABLE,
                    "enhancement_service": ENHANCEMENT_AVAILABLE,
                    "file_discovery": True
                },
                "current_data_source": pipeline_status["current_active_file"],
                "pipeline_health": pipeline_status["pipeline_health"],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"API info error: {e}")
            return {"error": str(e), "version": "2.3.0"}
            
    # ADD THE DEBUG ENDPOINT HERE
    @app.get("/debug/router-status")
    async def debug_router_status():
        return {
            "ARCHETYPE_ROUTER_AVAILABLE": ARCHETYPE_ROUTER_AVAILABLE,
            "ARCHETYPE_SERVICE_AVAILABLE": ARCHETYPE_SERVICE_AVAILABLE,
            "ENHANCEMENT_AVAILABLE": ENHANCEMENT_AVAILABLE,
            "DIAGRAM_SERVICE_AVAILABLE": DIAGRAM_SERVICE_AVAILABLE,
            "archetype_router_included": any("archetype" in str(route.path) for route in app.routes),
            "total_routes": len(app.routes),
            "archetype_routes": [str(route.path) for route in app.routes if "archetype" in str(route.path)],
            "all_routes": [f"{route.methods} {route.path}" for route in app.routes if hasattr(route, 'methods')]
        }
        
    @app.get("/debug/archetype-router")
    async def debug_archetype_router():
        return {
            "ARCHETYPE_ROUTER_AVAILABLE": ARCHETYPE_ROUTER_AVAILABLE,
            "archetype_router_type": str(type(archetype_router)) if 'archetype_router' in globals() else "Not imported",
            "router_routes": [str(route) for route in archetype_router.routes] if 'archetype_router' in globals() else []
        }

def setup_error_handlers(app: FastAPI):
    """Setup error handlers"""
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Endpoint not found",
                "message": "The requested endpoint is not available",
                "available_endpoints": ["/docs", "/health", "/api/info", "/ws", "/api/v1/data/status"],
                "timestamp": datetime.now().isoformat()
            }
        )

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat()
            }
        )

# =================== LIFESPAN EVENT HANDLER ===================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events"""
    
    # STARTUP
    logger.info("=" * 60)
    logger.info("Application Auto-Discovery Platform Starting")
    logger.info("=" * 60)
    
    # Initialize pipeline directories
    ensure_pipeline_directories()
    logger.info("Pipeline directories initialized")
    
    logger.info(f"Project root: {AppConfig.PROJECT_ROOT}")
    logger.info(f"Static files: {'Available' if AppConfig.STATIC_DIR.exists() else 'Not found'}")
    logger.info(f"UI files: {'Available' if AppConfig.UI_DIR.exists() else 'Not found'}")
    
    # Check data pipeline
    pipeline_status = file_discovery.get_file_status_report()
    logger.info("Data Processing Pipeline:")
    logger.info(f"  Current CSV: {pipeline_status['current_active_file'] or 'None'}")
    logger.info(f"  Health: {pipeline_status['pipeline_health']['status']}")
    logger.info(f"  Processed: {pipeline_status['status']['processed']['count']} files")
    logger.info(f"  Failed: {pipeline_status['status']['failed']['count']} files")
    logger.info(f"  Pending: {pipeline_status['status']['pending']['count']} files")
    
    # Check archetype service
    if ARCHETYPE_SERVICE_AVAILABLE:
        try:
            archetype_service = ArchetypeService()
            archetypes = archetype_service.get_archetypes()
            logger.info(f"Archetype Service: Available ({len(archetypes['archetypes'])} archetypes)")
        except Exception as e:
            logger.warning(f"Archetype Service: Error loading ({e})")
    else:
        logger.warning("Archetype Service: Not available")
    
    # LucidChart Service Check
    logger.info("LucidChart Service:")
    lucid_setup = check_lucidchart_setup()
    
    if lucid_setup["service_available"]:
        logger.info("LucidChart Generation: Available")
        template_count = sum(1 for tf in lucid_setup['template_files'].values() if tf.get('exists', False))
        logger.info(f"Template files: {template_count}/{len(lucid_setup['template_files'])} found")
    else:
        logger.info("LucidChart Generation: Not available (basic XML generation will be used)")
    
    # WebSocket Service Check
    logger.info("WebSocket Service:")
    logger.info("Main WebSocket: /ws")
    logger.info("Excel WebSocket: /api/v1/excel/ws")
    logger.info("Health Check: /api/v1/ws/health")
    
    # Report available endpoints
    logger.info("Enterprise Features:")
    if EXCEL_ROUTER_AVAILABLE:
        logger.info("Excel Processing: http://localhost:8001/api/v1/excel/")
    else:
        logger.info("Excel Processing: Not available")
        
    if ARCHETYPE_ROUTER_AVAILABLE:
        logger.info("Archetype Classification: http://localhost:8001/api/v1/archetype/")
    else:
        logger.info("Archetype Classification: Not available")
        
    logger.info("Dynamic File Discovery: http://localhost:8001/api/v1/data/status")
    logger.info("API Documentation: http://localhost:8001/docs")
    logger.info("WebSocket Endpoints: ws://localhost:8001/ws")
    
    yield
    
    # SHUTDOWN
    logger.info("Shutting down Application Auto-Discovery Platform...")

# =================== APP FACTORY FUNCTION ===================
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Application Auto-Discovery Platform with Enhanced Document Generation",
        description="Comprehensive application portfolio management with professional document generation, real-time WebSocket communication, and dynamic CSV file discovery",
        version="2.3.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add cache-busting middleware right after CORS
    @app.middleware("http")
    async def add_cache_control_headers(request, call_next):
        response = await call_next(request)
        
        # More aggressive cache busting for all static content
        if any(request.url.path.endswith(ext) for ext in ['.js', '.css', '.html', '.json']):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response.headers["Last-Modified"] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
            response.headers["ETag"] = f'"{int(time.time())}"'
        
        return response
        
    # Setup all endpoint groups
    setup_websocket_endpoints(app)
    setup_file_discovery_endpoints(app)
    setup_file_movement_endpoints(app)
    setup_excel_integration(app)
    
    if DIAGRAM_SERVICE_AVAILABLE:
        setup_diagram_endpoints(app)
    
    setup_lucidchart_endpoints(app)
    setup_basic_endpoints(app)
    setup_error_handlers(app)
    
    # Mount static files - ORDER MATTERS!
    static_ui_dir = AppConfig.STATIC_DIR / "ui"
    if static_ui_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(static_ui_dir)), name="ui")
        logger.info(f"UI files mounted from {static_ui_dir}")
    elif AppConfig.UI_DIR.exists():
        app.mount("/ui", StaticFiles(directory=str(AppConfig.UI_DIR)), name="ui")
        logger.info(f"UI files mounted from {AppConfig.UI_DIR}")
    
    if AppConfig.STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(AppConfig.STATIC_DIR)), name="static")
        logger.info(f"Static files mounted from {AppConfig.STATIC_DIR}")
    
    if AppConfig.DATA_STAGING_DIR.exists():
        app.mount("/data_staging", StaticFiles(directory=str(AppConfig.DATA_STAGING_DIR)), name="data_staging")
        logger.info(f"Data staging files mounted from {AppConfig.DATA_STAGING_DIR}")
    
    if AppConfig.TEMPLATES_DIR.exists():
        app.mount("/templates", StaticFiles(directory=str(AppConfig.TEMPLATES_DIR)), name="templates")
        logger.info(f"Template files mounted from {AppConfig.TEMPLATES_DIR}")
        
    topology_dir = AppConfig.RESULTS_BASE_DIR
    if topology_dir.exists():
        app.mount("/results", StaticFiles(directory=str(topology_dir)), name="results")
        logger.info(f"Results directory mounted from {topology_dir}")
    
    # Include routers with error handling
    try:
        if EXCEL_ROUTER_AVAILABLE:
            app.include_router(
                excel_router,
                prefix="/api/v1/excel",
                tags=["excel-processing"]
            )
            logger.info("Excel router included at /api/v1/excel")

        if ARCHETYPE_ROUTER_AVAILABLE:
            app.include_router(
                archetype_router,
                prefix="/api/v1/archetype",
                tags=["archetype-classification", "diagram-generation"]
            )
            logger.info("Archetype router included at /api/v1/archetype")
    except Exception as e:
        logger.error(f"Error including routers: {e}")
    
    # Enhancement service endpoints
    if ENHANCEMENT_AVAILABLE:
        @app.get("/api/v1/archetype/stencils/{archetype}")
        async def get_archetype_stencils(archetype: str):
            try:
                return await enhancement_service.get_archetype_stencils(archetype)
            except Exception as e:
                logger.error(f"Stencils error: {e}")
                return {"error": str(e)}

        @app.post("/api/v1/archetype/preview-layout")
        async def preview_archetype_layout(data: dict):
            try:
                return await enhancement_service.preview_archetype_layout(
                    data.get("archetype"), data.get("applications", [])
                )
            except Exception as e:
                logger.error(f"Preview layout error: {e}")
                return {"error": str(e)}

        @app.get("/api/v1/archetype/supported-archetypes")
        async def get_supported_archetypes():
            try:
                return enhancement_service.get_supported_archetypes()
            except Exception as e:
                logger.error(f"Supported archetypes error: {e}")
                return {"supported_archetypes": {}, "error": str(e)}
    
    return app

# =================== CREATE APP INSTANCE ===================
app = create_app()
# =================== MAIN EXECUTION ===================
if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("Starting Application Auto-Discovery Platform")
    logger.info("=" * 60)
    logger.info("Platform Features:")
    logger.info("   Application portfolio management")
    logger.info("   Network topology discovery")
    logger.info("   Documentation generation")
    logger.info("   Real-time WebSocket communication")
    logger.info("   Dynamic CSV file discovery")
    logger.info("   Data processing pipeline management")
    
    if DIAGRAM_SERVICE_AVAILABLE:
        logger.info("   Enhanced diagram service - Available")
    else:
        logger.info("   Enhanced diagram service - Not available")
    
    if LUCIDCHART_SERVICE_AVAILABLE:
        logger.info("   LucidChart generation service - Available")
    else:
        logger.info("   LucidChart generation service - Not available (basic XML fallback)")
    
    logger.info("\nServer Information:")
    logger.info(f"API Documentation: http://localhost:8001/docs")
    logger.info(f"Main Application: http://localhost:8001/")
    logger.info(f"Health Check: http://localhost:8001/health")
    logger.info(f"API Info: http://localhost:8001/api/info")
    logger.info(f"Data Pipeline Status: http://localhost:8001/api/v1/data/status")
    
    logger.info("\nWebSocket Endpoints:")
    logger.info(f"Main WebSocket: ws://localhost:8001/ws")
    logger.info(f"Excel WebSocket: ws://localhost:8001/api/v1/excel/ws")
    logger.info(f"WebSocket Health: http://localhost:8001/api/v1/ws/health")
    
    if LUCIDCHART_SERVICE_AVAILABLE:
        logger.info(f"LucidChart Status: http://localhost:8001/api/v1/lucidchart/status")
    
    logger.info("=" * 60)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=True,
        reload_dirs=[str(AppConfig.PROJECT_ROOT)],
        log_level="info",
        ws="websockets"  # Force websockets implementation
    )