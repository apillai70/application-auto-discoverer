# main.py - Application Auto-Discovery Platform with Enhanced Diagram Service
# Fixed version with proper WebSocket support

# =================== IMPORTS ===================
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, Request, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from services.archetype_service import ArchetypeService
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
import pandas as pd
from pathlib import Path
import uuid
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# =================== ROUTER IMPORTS WITH ERROR HANDLING ===================
try:
    from routers.archetype_router import router as archetype_router
    ARCHETYPE_ROUTER_AVAILABLE = True
    logger.info("✓ Archetype router imported successfully")
except ImportError as e:
    ARCHETYPE_ROUTER_AVAILABLE = False
    logger.warning(f"✗ Archetype router not available: {e}")
    from fastapi import APIRouter
    archetype_router = APIRouter()

try:
    from routers.excel_processing_router import router as excel_router
    EXCEL_ROUTER_AVAILABLE = True
    logger.info("✓ Excel processing router imported successfully")
except ImportError as e:
    EXCEL_ROUTER_AVAILABLE = False
    logger.warning(f"✗ Excel processing router not available: {e}")
    from fastapi import APIRouter
    excel_router = APIRouter()

# =================== SERVICE IMPORTS ===================
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

# Global WebSocket manager
websocket_manager = WebSocketConnectionManager()

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
        
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")

# Initialize directories
AppConfig.ensure_directories()

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

# Global job managers
active_diagram_jobs = JobManager()

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

# =================== WEBSOCKET ENDPOINTS ===================
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
                    # Send heartbeat
                    await websocket_manager.send_personal_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "active_jobs": len(websocket_manager.list_active_jobs())
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
                    await websocket_manager.send_personal_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                        "active_excel_jobs": len([
                            j for j in websocket_manager.processing_jobs.values() 
                            if j.get("job_type") == "excel_processing"
                        ])
                    }, websocket)
                    
        except WebSocketDisconnect:
            logger.info("Excel WebSocket client disconnected normally")
        except Exception as e:
            logger.error(f"Excel WebSocket error: {e}")
        finally:
            websocket_manager.disconnect(websocket)
    
    async def handle_websocket_message(message: dict, websocket: WebSocket):
        """Handle incoming WebSocket messages"""
        message_type = message.get("type", "unknown")
        
        if message_type == "ping":
            await websocket_manager.send_personal_message({
                "type": "pong", 
                "timestamp": datetime.now().isoformat()
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
    
    # WebSocket health check endpoint
    @app.get("/api/v1/ws/health")
    async def websocket_health():
        """WebSocket service health check"""
        return {
            "status": "healthy",
            "active_connections": len(websocket_manager.active_connections),
            "active_jobs": len(websocket_manager.processing_jobs),
            "websocket_endpoints": [
                "/ws",
                "/api/v1/excel/ws"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info("WebSocket endpoints configured:")
    logger.info("  - Main WebSocket: /ws")
    logger.info("  - Excel WebSocket: /api/v1/excel/ws") 
    logger.info("  - Health Check: /api/v1/ws/health")

# =================== EXCEL PROCESSING INTEGRATION ===================
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
    
    async def process_excel_background(job_id: str, file_data: dict):
        """Background Excel processing with WebSocket updates"""
        try:
            # Update to processing
            websocket_manager.update_job(job_id, {
                "status": "processing",
                "progress": 10,
                "message": "Processing Excel file..."
            })
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
                await websocket_manager.send_job_update(job_id, {
                    "progress": progress,
                    "message": message
                })
            
            # Complete
            websocket_manager.update_job(job_id, {
                "status": "completed",
                "progress": 100,
                "message": "Processing completed successfully"
            })
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
            await websocket_manager.send_job_update(job_id, {
                "status": "error",
                "error": str(e)
            })
    
    @app.get("/api/v1/excel/job/{job_id}")
    async def get_excel_job_status(job_id: str):
        """Get Excel job status"""
        job = websocket_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    
    logger.info("Excel processing integration endpoints added")

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

# =================== DIAGRAM SERVICE ENDPOINTS ===================
def setup_diagram_endpoints(app: FastAPI):
    """Setup Enhanced Diagram Service endpoints"""
    
    @app.post("/api/v1/diagram/generate-enhanced-diagram-by-format")
    async def generate_enhanced_diagram(request: EnhancedDiagramRequest):
        """Main endpoint for generating enhanced diagrams"""
        try:
            if not DIAGRAM_SERVICE_AVAILABLE:
                raise HTTPException(status_code=503, detail="Diagram service not available")
            
            data = request.data.copy()
            
            # Load CSV data if requested or no applications provided
            if request.use_csv or not data.get("applications"):
                csv_path = AppConfig.DATA_STAGING_DIR / "applicationList.csv"
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
                        logger.info(f"Loaded {len(applications)} applications from CSV")
                    except Exception as e:
                        logger.error(f"Error reading CSV: {e}")
                        data["applications"] = _get_demo_applications()
                else:
                    data["applications"] = _get_demo_applications()
            
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
                "processing_time": job.get("processing_time")
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Job status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    logger.info("Enhanced Diagram Service endpoints added")

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

# =================== BASIC ENDPOINTS ===================
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
        """Health check endpoint"""
        try:
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
                "version": "2.2.1"
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
                "Real-time WebSocket Communication"
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
            
            return {
                "platform": "Application Auto-Discovery with Enhanced Document Generation",
                "version": "2.2.1",
                "capabilities": capabilities,
                "supported_formats": ["lucid", "document", "excel", "pdf"],
                "websocket_endpoints": ["/ws", "/api/v1/excel/ws"],
                "services": {
                    "diagram_service": DIAGRAM_SERVICE_AVAILABLE,
                    "lucidchart_service": LUCIDCHART_SERVICE_AVAILABLE,
                    "enhancement_service": ENHANCEMENT_AVAILABLE
                },
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"API info error: {e}")
            return {"error": str(e), "version": "2.2.1"}

# =================== ERROR HANDLERS ===================
def setup_error_handlers(app: FastAPI):
    """Setup error handlers"""
    
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Endpoint not found",
                "message": "The requested endpoint is not available",
                "available_endpoints": ["/docs", "/health", "/api/info", "/ws"],
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
    
    logger.info(f"Project root: {AppConfig.PROJECT_ROOT}")
    logger.info(f"Static files: {'Available' if AppConfig.STATIC_DIR.exists() else 'Not found'}")
    logger.info(f"UI files: {'Available' if AppConfig.UI_DIR.exists() else 'Not found'}")
    
    # Check archetype service
    try:
        archetype_service = ArchetypeService()
        archetypes = archetype_service.get_archetypes()
        logger.info(f"Archetype Service: Available ({len(archetypes['archetypes'])} archetypes)")
    except Exception as e:
        logger.warning(f"Archetype Service: Not available ({e})")
    
    # LucidChart Service Check
    logger.info("LucidChart Service:")
    lucid_setup = check_lucidchart_setup()
    
    if lucid_setup["service_available"]:
        logger.info("✓ LucidChart Generation: Available")
        template_count = sum(1 for tf in lucid_setup['template_files'].values() if tf.get('exists', False))
        logger.info(f"✓ Template files: {template_count}/{len(lucid_setup['template_files'])} found")
    else:
        logger.info("✗ LucidChart Generation: Not available (basic XML generation will be used)")
    
    # WebSocket Service Check
    logger.info("WebSocket Service:")
    logger.info("✓ Main WebSocket: /ws")
    logger.info("✓ Excel WebSocket: /api/v1/excel/ws")
    logger.info("✓ Health Check: /api/v1/ws/health")
    
    # Report available endpoints
    logger.info("Enterprise Features:")
    if EXCEL_ROUTER_AVAILABLE:
        logger.info("✓ Excel Processing: http://localhost:8001/api/v1/excel/")
    else:
        logger.info("✗ Excel Processing: Not available")
        
    if ARCHETYPE_ROUTER_AVAILABLE:
        logger.info("✓ Archetype Classification: http://localhost:8001/api/v1/archetype/")
    else:
        logger.info("✗ Archetype Classification: Not available")
        
    logger.info("✓ API Documentation: http://localhost:8001/docs")
    logger.info("✓ WebSocket Endpoints: ws://localhost:8001/ws")
    
    yield
    
    # SHUTDOWN
    logger.info("Shutting down Application Auto-Discovery Platform...")

# =================== APP FACTORY FUNCTION ===================
def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Application Auto-Discovery Platform with Enhanced Document Generation",
        description="Comprehensive application portfolio management with professional document generation and real-time WebSocket communication",
        version="2.2.1",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    setup_websocket_endpoints(app)  # This adds both /ws and /api/v1/excel/ws
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
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
    
    # Include routers with error handling
    try:
        if EXCEL_ROUTER_AVAILABLE:
            app.include_router(
                excel_router,
                prefix="/api/v1/excel",
                tags=["excel-processing"]
            )
            logger.info("✓ Excel router included at /api/v1/excel")

        if ARCHETYPE_ROUTER_AVAILABLE:
            app.include_router(
                archetype_router,
                prefix="/api/v1/archetype",
                tags=["archetype-classification", "diagram-generation"]
            )
            logger.info("✓ Archetype router included at /api/v1/archetype")
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
    
    # Add service endpoints
    if DIAGRAM_SERVICE_AVAILABLE:
        setup_diagram_endpoints(app)
    
    setup_lucidchart_endpoints(app)
    setup_basic_endpoints(app)
  
    setup_excel_integration(app)  # This adds Excel endpoints that work with WebSocket
    setup_error_handlers(app)
    
    return app

# =================== CREATE APP INSTANCE ===================
app = create_app()

# =================== MAIN EXECUTION ===================
if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting Application Auto-Discovery Platform")
    logger.info("=" * 60)
    logger.info("Platform Features:")
    logger.info("   📊 Application portfolio management")
    logger.info("   🔍 Network topology discovery")
    logger.info("   📝 Documentation generation")
    logger.info("   📡 Real-time WebSocket communication")
    
    if DIAGRAM_SERVICE_AVAILABLE:
        logger.info("   ✅ Enhanced diagram service - Available")
    else:
        logger.info("   ❌ Enhanced diagram service - Not available")
    
    if LUCIDCHART_SERVICE_AVAILABLE:
        logger.info("   ✅ LucidChart generation service - Available")
    else:
        logger.info("   ❌ LucidChart generation service - Not available (basic XML fallback)")
    
    logger.info("\n🌐 Server Information:")
    logger.info(f"📚 API Documentation: http://localhost:8001/docs")
    logger.info(f"🏠 Main Application: http://localhost:8001/")
    logger.info(f"💚 Health Check: http://localhost:8001/health")
    logger.info(f"ℹ️  API Info: http://localhost:8001/api/info")
    
    logger.info("\n🔌 WebSocket Endpoints:")
    logger.info(f"📡 Main WebSocket: ws://localhost:8001/ws")
    logger.info(f"📊 Excel WebSocket: ws://localhost:8001/api/v1/excel/ws")
    logger.info(f"💊 WebSocket Health: http://localhost:8001/api/v1/ws/health")
    
    if LUCIDCHART_SERVICE_AVAILABLE:
        logger.info(f"📈 LucidChart Status: http://localhost:8001/api/v1/lucidchart/status")
    
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