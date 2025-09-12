"""
Complete Archetype Service Router with /data Endpoint
Provides REST API endpoints for archetype management and diagram generation
with proper error handling, security, and modular design
"""

import logging
import os
import re
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
import pandas as pd
import uuid
import functools
import json
import random

# Configure logging
logger = logging.getLogger(__name__)

# =================== SERVICE IMPORTS WITH ERROR HANDLING ===================
try:
    from services.archetype_service import ArchetypeService
    ARCHETYPE_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Archetype service not available: {e}")
    ARCHETYPE_SERVICE_AVAILABLE = False
    ArchetypeService = None

try:
    from services.archetype_enhancement import enhance_archetype_diagram
    ENHANCEMENT_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Enhancement service not available: {e}")
    ENHANCEMENT_SERVICE_AVAILABLE = False
    enhance_archetype_diagram = None

try:
    from services.banking_archetype_enhancer import BankingArchetypeEnhancer
    BANKING_ENHANCER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Banking enhancer not available: {e}")
    BANKING_ENHANCER_AVAILABLE = False
    BankingArchetypeEnhancer = None

try:
    from services.practical_diagram_generators import generate_all_formats
    DIAGRAM_GENERATORS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Diagram generators not available: {e}")
    DIAGRAM_GENERATORS_AVAILABLE = False
    generate_all_formats = None

# =================== CONFIGURATION ===================
class AppConfig:
    """Application configuration"""
    BASE_DIR = Path(__file__).parent.parent
    RESULTS_DIR = BASE_DIR / "results"
    DATA_STAGING_DIR = BASE_DIR / "data_staging"
    TEMPLATES_DIR = BASE_DIR / "templates"
    
    # Job management
    MAX_JOB_AGE_HOURS = 24
    MAX_CONCURRENT_JOBS = 10
    
    # File handling
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES = {".lucid", ".svg", ".pdf", ".json", ".docx", ".xlsx"}
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        for dir_path in [cls.RESULTS_DIR, cls.DATA_STAGING_DIR, cls.TEMPLATES_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["diagrams", "lucid", "pdf", "excel"]:
            (cls.RESULTS_DIR / subdir).mkdir(parents=True, exist_ok=True)

# Initialize configuration
AppConfig.ensure_directories()

# =================== JOB MANAGEMENT ===================
class JobManager:
    """Thread-safe job management"""
    
    def __init__(self):
        self._jobs: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._max_jobs = AppConfig.MAX_CONCURRENT_JOBS
    
    def create_job(self, job_type: str, **kwargs) -> str:
        """Create a new job"""
        job_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            if len(self._jobs) >= self._max_jobs:
                self.cleanup_old_jobs()
                if len(self._jobs) >= self._max_jobs:
                    raise HTTPException(
                        status_code=429, 
                        detail="Too many concurrent jobs. Please try again later."
                    )
            
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": job_type,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "progress": 0,
                "message": "Job created",
                **kwargs
            }
        
        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id
    
    def update_job(self, job_id: str, **updates):
        """Update job status"""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)
                self._jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Deleted job {job_id}")
    
    def cleanup_old_jobs(self, max_age_hours: int = None):
        """Clean up old jobs"""
        if max_age_hours is None:
            max_age_hours = AppConfig.MAX_JOB_AGE_HOURS
            
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._lock:
            expired_jobs = []
            for job_id, job in self._jobs.items():
                try:
                    job_time = datetime.fromisoformat(job["created_at"])
                    if job_time < cutoff:
                        expired_jobs.append(job_id)
                except (KeyError, ValueError):
                    expired_jobs.append(job_id)  # Remove malformed jobs
            
            for job_id in expired_jobs:
                del self._jobs[job_id]
            
            if expired_jobs:
                logger.info(f"Cleaned up {len(expired_jobs)} old jobs")

# Global job manager
job_manager = JobManager()

# =================== SECURITY UTILITIES ===================
def safe_filename(filename: str) -> str:
    """Create a safe filename by removing dangerous characters"""
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)
    return safe_name[:100]

def safe_path_join(base_dir: Path, filename: str) -> Path:
    """Safely join paths to prevent directory traversal"""
    clean_filename = os.path.basename(filename)
    if not clean_filename or clean_filename in ('.', '..'):
        raise ValueError("Invalid filename")
    
    full_path = base_dir / clean_filename
    
    try:
        full_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError("Path traversal attempt detected")
    
    return full_path

def validate_file_extension(filename: str) -> bool:
    """Validate file extension"""
    return Path(filename).suffix.lower() in AppConfig.ALLOWED_FILE_TYPES

# =================== ERROR HANDLING ===================
class APIError(Exception):
    """Custom API error"""
    def __init__(self, message: str, status_code: int = 500, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

def handle_service_error(func: Callable) -> Callable:
    """Decorator for consistent error handling"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError:
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "message": str(e),
                    "function": func.__name__
                }
            )
    return wrapper

# =================== REQUEST/RESPONSE MODELS ===================
class ApplicationData(BaseModel):
    applications: List[Dict[str, Any]]
    
class DiagramGenerationRequest(BaseModel):
    archetype: str
    application_data: Dict[str, Any] = {}
    template_customizations: Dict[str, Any] = {}
    output_formats: List[str] = ["svg", "json"]
    
    @validator('output_formats')
    def validate_formats(cls, v):
        allowed_formats = ["svg", "json", "lucid", "pdf"]
        return [f for f in v if f in allowed_formats]

class PortfolioAnalysisRequest(BaseModel):
    applications: List[Dict[str, Any]]
    include_diagram_recommendations: bool = True

class BatchDiagramRequest(BaseModel):
    filter_type: str = "batch"
    batch_size: int = 10
    batch_offset: int = 0
    app_names: Optional[List[str]] = None
    domain_keywords: Optional[List[str]] = None
    security_zone: Optional[str] = None
    output_formats: List[str] = ["svg"]
    include_connections: bool = True
    layout_style: str = "banking_flow"
    
class PracticalDiagramRequest(BaseModel):
    archetype: str = "three_tier"
    app_name: str = "TestApp"
    job_id: Optional[str] = None

# =================== SERVICE INITIALIZATION ===================
def initialize_services():
    """Initialize services with error handling"""
    services = {}
    
    if ARCHETYPE_SERVICE_AVAILABLE:
        try:
            services['archetype'] = ArchetypeService()
            logger.info("Archetype service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize archetype service: {e}")
    
    if BANKING_ENHANCER_AVAILABLE:
        try:
            services['banking_enhancer'] = BankingArchetypeEnhancer()
            logger.info("Banking enhancer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize banking enhancer: {e}")
    
    return services

# Initialize services
services = initialize_services()

# Global cache for Excel results
_excel_results_cache = []

# =================== ROUTER SETUP ===================
router = APIRouter()

# =================== NEW DATA ENDPOINT ===================
@router.get("/data")
@handle_service_error
async def get_archetype_data():
    """
    Get application data for archetype dashboard
    Data sources (in priority order):
    1. Excel processing results (if available)
    2. CSV file from data_staging directory (applicationList.csv)
    3. Fallback demo data
    """
    
    try:
        # First, check for Excel processing results
        excel_results = get_excel_processed_data()
        if excel_results:
            logger.info("Using Excel processed data")
            return format_archetype_data(excel_results, source="excel_processing")
        
        # Second, try to load CSV from data_staging
        csv_data = load_csv_data()
        if csv_data:
            logger.info("Using CSV data from data_staging")
            return format_archetype_data(csv_data, source="csv_file")
        
        # Fallback to demo data
        logger.info("Using fallback demo data")
        demo_data = create_demo_data()
        return format_archetype_data(demo_data, source="demo")
        
    except Exception as e:
        logger.error(f"Error loading archetype data: {e}")
        # Return minimal working data so frontend doesn't crash
        return {
            "applications": create_demo_data(),
            "archetype_definitions": get_default_archetype_definitions(),
            "source": "error_fallback",
            "error": str(e)
        }

def get_excel_processed_data():
    """Get data from Excel processing results if available"""
    try:
        # Check cache first
        global _excel_results_cache
        if _excel_results_cache:
            return _excel_results_cache
        
        # Try to get from results directory
        results_dir = Path("results/excel")
        if results_dir.exists():
            json_files = list(results_dir.glob("processed_*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    applications = data.get("applications", [])
                    if applications:
                        _excel_results_cache = applications
                        return applications
        
        return None
    except Exception as e:
        logger.warning(f"Could not load Excel processed data: {e}")
        return None

def load_csv_data():
    """Load data from applicationList.csv in data_staging directory"""
    try:
        # Look for applicationList.csv specifically
        csv_path = AppConfig.DATA_STAGING_DIR / "applicationList.csv"
        
        if not csv_path.exists():
            logger.warning(f"applicationList.csv not found at {csv_path}")
            return None
        
        # Read CSV with cp1252 encoding as specified
        df = pd.read_csv(csv_path, encoding='cp1252')
        
        logger.info(f"Loaded applicationList.csv: {len(df)} applications")
        
        # Convert CSV data to application format
        applications = []
        
        for _, row in df.iterrows():
            app_id = str(row.get('app_id', f'app_{len(applications)}'))
            app_name = str(row.get('app_name', f'Application {len(applications)}'))
            
            # Classify archetype based on app name patterns
            archetype = classify_archetype_from_name(app_name)
            
            app_data = {
                "id": app_id,
                "name": app_name,
                "archetype": archetype,
                "color": get_archetype_color(archetype),
                "status": "active",
                "flow_count": random.randint(100, 5000),  # Synthetic data
                "traffic_pattern": get_traffic_pattern_for_archetype(archetype),
                "primary_ports": generate_ports_for_archetype(archetype),
                "network_evidence": generate_evidence_for_archetype(archetype, app_name),
                "x": float(abs(hash(app_id)) % 800),
                "y": float((abs(hash(app_id)) // 800) % 600)
            }
            applications.append(app_data)
        
        logger.info(f"Processed {len(applications)} applications from CSV")
        return applications
        
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        return None

def classify_archetype_from_name(app_name):
    """Classify application archetype based on name patterns"""
    
    name_lower = app_name.lower()
    
    # Microservices indicators
    microservices_keywords = ['api', 'service', 'micro', 'rest', 'endpoint', 'gateway']
    if any(keyword in name_lower for keyword in microservices_keywords):
        return "Microservices"
    
    # Web application indicators  
    web_keywords = ['web', 'portal', 'ui', 'frontend', 'site', 'dashboard']
    if any(keyword in name_lower for keyword in web_keywords):
        return "Web + API Headless"
    
    # Database indicators
    db_keywords = ['db', 'database', 'data', 'warehouse', 'storage', 'repo']
    if any(keyword in name_lower for keyword in db_keywords):
        return "Database-Centric"
    
    # Event-driven indicators
    event_keywords = ['event', 'queue', 'stream', 'message', 'broker', 'kafka', 'rabbit']
    if any(keyword in name_lower for keyword in event_keywords):
        return "Event-Driven"
    
    # Legacy/Enterprise indicators
    legacy_keywords = ['legacy', 'mainframe', 'core', 'enterprise', 'erp', 'crm']
    if any(keyword in name_lower for keyword in legacy_keywords):
        return "Monolithic"
    
    # SOA indicators
    soa_keywords = ['soa', 'soap', 'enterprise service', 'esb']
    if any(keyword in name_lower for keyword in soa_keywords):
        return "SOA"
    
    # Client-server indicators
    client_keywords = ['client', 'desktop', 'thick client', 'fat client']
    if any(keyword in name_lower for keyword in client_keywords):
        return "Client-Server"
    
    # Default classification based on common patterns
    if 'system' in name_lower or 'application' in name_lower:
        return "3-Tier"
    
    return "3-Tier"  # Default

def generate_ports_for_archetype(archetype):
    """Generate realistic ports for each archetype"""
    port_mappings = {
        "Microservices": [
            {"port": 8080, "count": random.randint(500, 2000)},
            {"port": 8443, "count": random.randint(300, 1500)},
            {"port": 3000, "count": random.randint(200, 1000)}
        ],
        "3-Tier": [
            {"port": 80, "count": random.randint(1000, 3000)},
            {"port": 443, "count": random.randint(800, 2500)},
            {"port": 3306, "count": random.randint(100, 500)}
        ],
        "Web + API Headless": [
            {"port": 80, "count": random.randint(1500, 4000)},
            {"port": 443, "count": random.randint(1200, 3500)},
            {"port": 8080, "count": random.randint(800, 2000)}
        ],
        "Event-Driven": [
            {"port": 9092, "count": random.randint(300, 1500)},
            {"port": 5672, "count": random.randint(200, 1000)},
            {"port": 61616, "count": random.randint(100, 800)}
        ],
        "Database-Centric": [
            {"port": 3306, "count": random.randint(800, 3000)},
            {"port": 5432, "count": random.randint(600, 2500)},
            {"port": 1433, "count": random.randint(400, 2000)}
        ],
        "Monolithic": [
            {"port": 8080, "count": random.randint(2000, 5000)},
            {"port": 1433, "count": random.randint(500, 2000)}
        ],
        "SOA": [
            {"port": 8080, "count": random.randint(1000, 3000)},
            {"port": 8443, "count": random.randint(800, 2500)},
            {"port": 7001, "count": random.randint(300, 1500)}
        ],
        "Client-Server": [
            {"port": 1433, "count": random.randint(1000, 4000)},
            {"port": 3389, "count": random.randint(200, 1000)}
        ]
    }
    
    return port_mappings.get(archetype, [
        {"port": 80, "count": random.randint(500, 2000)}
    ])

def generate_evidence_for_archetype(archetype, app_name):
    """Generate realistic network evidence for each archetype"""
    evidence_mappings = {
        "Microservices": [
            "Container orchestration detected",
            "Service mesh communication",
            "RESTful API patterns"
        ],
        "3-Tier": [
            "Multi-tier architecture",
            "Database connectivity layer",
            "Web server frontend"
        ],
        "Web + API Headless": [
            "Frontend-backend separation", 
            "API-first design",
            "Modern web frameworks"
        ],
        "Event-Driven": [
            "Message queue integration",
            "Event streaming patterns",
            "Asynchronous processing"
        ],
        "Database-Centric": [
            "Heavy database interaction",
            "Data processing workflows",
            "Storage-focused architecture"
        ],
        "Monolithic": [
            "Single deployment unit",
            "Centralized processing",
            "Traditional architecture"
        ],
        "SOA": [
            "Service-oriented design",
            "Enterprise integration",
            "SOAP/XML protocols"
        ],
        "Client-Server": [
            "Direct client connections",
            "Desktop application",
            "Two-tier architecture"
        ]
    }
    
    base_evidence = evidence_mappings.get(archetype, ["Standard application pattern"])
    base_evidence.append(f"Application: {app_name}")
    
    return base_evidence

def get_archetype_color(archetype):
    """Get color for archetype"""
    colors = {
        "Microservices": "#10b981",
        "3-Tier": "#3b82f6", 
        "Monolithic": "#8b5cf6",
        "Event-Driven": "#f59e0b",
        "SOA": "#ef4444",
        "Web + API Headless": "#06b6d4",
        "Client-Server": "#84cc16",
        "Database-Centric": "#ec4899"
    }
    return colors.get(archetype, "#64748b")

def get_traffic_pattern_for_archetype(archetype):
    """Get traffic pattern for archetype"""
    patterns = {
        "Microservices": "East-West Service Communication",
        "3-Tier": "North-South Layered",
        "Monolithic": "Centralized Processing",
        "Event-Driven": "Event Streaming",
        "SOA": "Service Bus Communication", 
        "Web + API Headless": "API-First Communication",
        "Client-Server": "Direct Client Communication",
        "Database-Centric": "Data-Centric Communication"
    }
    return patterns.get(archetype, "Standard Communication")

def create_demo_data():
    """Create demo application data when no other sources available"""
    return [
        {
            "id": "demo-web-app",
            "name": "Customer Web Portal",
            "archetype": "3-Tier",
            "color": "#3b82f6",
            "status": "active", 
            "flow_count": 2500,
            "traffic_pattern": "North-South Layered",
            "primary_ports": [{"port": 80, "count": 1200}, {"port": 443, "count": 800}],
            "network_evidence": ["HTTP/HTTPS traffic", "Database connectivity", "Load balanced"],
            "x": 200.0,
            "y": 150.0
        },
        {
            "id": "demo-api-service", 
            "name": "Payment API Service",
            "archetype": "Microservices",
            "color": "#10b981",
            "status": "active",
            "flow_count": 3200,
            "traffic_pattern": "East-West Service Communication", 
            "primary_ports": [{"port": 8080, "count": 1500}, {"port": 8443, "count": 900}],
            "network_evidence": ["RESTful API", "Service mesh", "Container orchestration"],
            "x": 450.0,
            "y": 150.0
        },
        {
            "id": "demo-event-processor",
            "name": "Event Processing Engine", 
            "archetype": "Event-Driven",
            "color": "#f59e0b",
            "status": "active",
            "flow_count": 1800,
            "traffic_pattern": "Event Streaming",
            "primary_ports": [{"port": 9092, "count": 700}, {"port": 5672, "count": 600}],
            "network_evidence": ["Kafka messaging", "RabbitMQ queues", "Event streaming"],
            "x": 700.0, 
            "y": 150.0
        }
    ]

def get_default_archetype_definitions():
    """Get default archetype definitions for the frontend"""
    return {
        "3-Tier": {
            "color": "#3b82f6",
            "description": "Traditional presentation-business-data tier architecture",
            "traffic_pattern": "North-South Layered"
        },
        "Microservices": {
            "color": "#10b981", 
            "description": "Containerized microservices with service mesh",
            "traffic_pattern": "East-West Service Communication"
        },
        "Monolithic": {
            "color": "#8b5cf6",
            "description": "Single-tier monolithic application",
            "traffic_pattern": "Centralized Processing"
        },
        "Event-Driven": {
            "color": "#f59e0b",
            "description": "Event-driven architecture with message queues",
            "traffic_pattern": "Event Streaming" 
        },
        "SOA": {
            "color": "#ef4444",
            "description": "Service-oriented architecture with ESB",
            "traffic_pattern": "Service Bus Communication"
        },
        "Web + API Headless": {
            "color": "#06b6d4",
            "description": "Headless web application with RESTful APIs", 
            "traffic_pattern": "API-First Communication"
        },
        "Client-Server": {
            "color": "#84cc16",
            "description": "Traditional client-server architecture",
            "traffic_pattern": "Direct Client Communication"
        },
        "Database-Centric": {
            "color": "#ec4899",
            "description": "Database-centric architecture pattern",
            "traffic_pattern": "Data-Centric Communication"
        }
    }

def format_archetype_data(applications, source="unknown"):
    """Format application data for the frontend"""
    
    # Ensure applications have required fields
    formatted_applications = []
    for app in applications:
        formatted_app = {
            "id": app.get("id", f"app_{len(formatted_applications)}"),
            "name": app.get("name", app.get("app_name", "Unknown Application")),
            "archetype": app.get("archetype", app.get("architecture", "3-Tier")),
            "color": app.get("color", get_archetype_color(app.get("archetype", "3-Tier"))),
            "status": app.get("status", "active"),
            "flow_count": app.get("flow_count", 0),
            "traffic_pattern": app.get("traffic_pattern", get_traffic_pattern_for_archetype(app.get("archetype", "3-Tier"))),
            "primary_ports": app.get("primary_ports", []),
            "network_evidence": app.get("network_evidence", [f"Imported from {source}"]),
            "x": app.get("x", float(abs(hash(app.get("id", ""))) % 800)),
            "y": app.get("y", float((abs(hash(app.get("id", ""))) // 800) % 600))
        }
        formatted_applications.append(formatted_app)
    
    return {
        "applications": formatted_applications,
        "archetype_definitions": get_default_archetype_definitions(), 
        "source": source,
        "total_applications": len(formatted_applications),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/data/cache-excel-results")
@handle_service_error 
async def cache_excel_results(results: dict):
    """Cache Excel processing results for dashboard use"""
    try:
        global _excel_results_cache
        _excel_results_cache = results.get("applications", [])
        
        return {
            "success": True,
            "cached_applications": len(_excel_results_cache),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error caching Excel results: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# =================== BASIC ARCHETYPE ENDPOINTS ===================
@router.get("/archetypes")
@handle_service_error
async def get_all_archetypes():
    """Get all available archetypes with comprehensive information"""
    if not ARCHETYPE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Archetype service not available"
        )
    
    try:
        return services['archetype'].get_archetypes()
    except Exception as e:
        logger.error(f"Error retrieving archetypes: {e}")
        raise APIError(f"Error retrieving archetypes: {str(e)}", 500)

@router.get("/archetypes/{archetype_name}")
@handle_service_error
async def get_archetype_details(archetype_name: str):
    """Get detailed information about a specific archetype"""
    if not ARCHETYPE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Archetype service not available"
        )
    
    try:
        result = services['archetype'].get_archetype_details(archetype_name)
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Archetype '{archetype_name}' not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving archetype details for {archetype_name}: {e}")
        raise APIError(f"Error retrieving archetype details: {str(e)}", 500)

@router.post("/archetypes/{archetype_name}/strategy")
@handle_service_error
async def recommend_migration_strategy(
    archetype_name: str, 
    business_requirements: Optional[Dict[str, Any]] = None
):
    """Get migration strategy recommendation for an archetype"""
    if not ARCHETYPE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Archetype service not available"
        )
    
    try:
        result = services['archetype'].recommend_strategy(
            archetype_name, business_requirements
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating strategy for {archetype_name}: {e}")
        raise APIError(f"Error generating strategy recommendation: {str(e)}", 500)

# =================== DIAGRAM GENERATION ENDPOINTS ===================  
@router.get("/generate-practical-diagrams")
async def generate_practical_diagrams(
    archetype: str = "three_tier",
    app_name: str = "TestApp", 
    job_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Generate diagrams in practical formats"""
    try:
        if not DIAGRAM_GENERATORS_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Diagram generators not available"
            )
        
        if not job_id:
            job_id = job_manager.create_job(
                job_type="diagram_generation",
                archetype=archetype,
                app_name=app_name
            )
        
        background_tasks.add_task(
            _generate_practical_diagrams_background,
            job_id, archetype, app_name
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "archetype": archetype,
            "app_name": app_name,
            "status_url": f"/api/v1/archetype/jobs/{job_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_practical_diagrams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_practical_diagrams_background(
    job_id: str, archetype: str, app_name: str
):
    """Background task for generating practical diagrams"""
    try:
        job_manager.update_job(job_id, status="processing", progress=10)
        
        # Sample applications
        test_applications = [
            {"id": "web1", "name": safe_filename(app_name), "type": "web_application"},
            {"id": "api1", "name": f"{safe_filename(app_name)} API", "type": "api_service"},
            {"id": "db1", "name": f"{safe_filename(app_name)} DB", "type": "database"}
        ]
        
        job_manager.update_job(job_id, progress=50, message="Generating diagrams...")
        
        result = generate_all_formats(archetype, test_applications, app_name, job_id)
        
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            message=f"Generated {len(result['files'])} files",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Background diagram generation failed for job {job_id}: {e}")
        job_manager.update_job(
            job_id,
            status="error",
            error=str(e),
            completed_at=datetime.now().isoformat()
        )

@router.post("/generate-diagram")
@handle_service_error
async def generate_architecture_diagram(
    request: DiagramGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate architecture diagram based on archetype template"""
    if not ARCHETYPE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Archetype service not available"
        )
    
    # Validate archetype
    try:
        archetype_details = services['archetype'].get_archetype_details(request.archetype)
        if not archetype_details:
            raise HTTPException(
                status_code=404, 
                detail=f"Archetype '{request.archetype}' not found"
            )
    except Exception as e:
        logger.error(f"Error validating archetype {request.archetype}: {e}")
        raise APIError(f"Error validating archetype: {str(e)}", 400)
    
    # Create job
    job_id = job_manager.create_job(
        job_type="diagram_generation",
        archetype=request.archetype,
        output_formats=request.output_formats
    )
    
    # Start background generation
    background_tasks.add_task(
        _generate_diagram_background,
        job_id, request, archetype_details
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "archetype": request.archetype,
        "output_formats": request.output_formats,
        "estimated_completion": "2-5 minutes",
        "status_url": f"/api/v1/archetype/jobs/{job_id}"
    }

async def _generate_diagram_background(
    job_id: str,
    request: DiagramGenerationRequest,
    archetype_details: Dict[str, Any]
):
    """Background task for diagram generation"""
    try:
        job_manager.update_job(
            job_id, 
            status="processing", 
            progress=10,
            message="Initializing diagram generation..."
        )
        
        # Create output directory
        output_dir = AppConfig.RESULTS_DIR / "diagrams" / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        job_manager.update_job(job_id, progress=30, message="Processing archetype data...")
        
        # Generate diagram data (simplified version)
        generated_files = []
        
        for format_type in request.output_formats:
            try:
                if format_type == "svg":
                    file_path = output_dir / f"diagram_{job_id}.svg"
                    # Generate basic SVG content
                    svg_content = _create_basic_svg(request.archetype, archetype_details)
                    file_path.write_text(svg_content)
                    
                elif format_type == "json":
                    file_path = output_dir / f"diagram_{job_id}.json"
                    json_content = {
                        "archetype": request.archetype,
                        "details": archetype_details,
                        "generated_at": datetime.now().isoformat()
                    }
                    file_path.write_text(json.dumps(json_content, indent=2))
                
                elif format_type == "lucid" and ENHANCEMENT_SERVICE_AVAILABLE:
                    # Call enhancement service for LucidChart generation
                    enhancement_result = await enhance_archetype_diagram({
                        "applications": [],
                        "archetype": request.archetype,
                        "app_name": f"Generated_{job_id}",
                        "job_id": job_id
                    })
                    
                    if enhancement_result.get("success"):
                        lucid_files = enhancement_result.get("files", [])
                        for lucid_file in lucid_files:
                            if lucid_file.get("format") == "lucid":
                                file_path = Path(lucid_file["file_path"])
                            
                if file_path and file_path.exists():
                    generated_files.append({
                        "format": format_type,
                        "filename": file_path.name,
                        "file_path": str(file_path),
                        "file_size": file_path.stat().st_size,
                        "download_url": f"/api/v1/archetype/download/{file_path.name}"
                    })
                    
            except Exception as format_error:
                logger.error(f"Error generating {format_type} format: {format_error}")
        
        # Complete job
        job_manager.update_job(
            job_id,
            status="completed",
            progress=100,
            message=f"Generated {len(generated_files)} files",
            result={"files": generated_files}
        )
        
    except Exception as e:
        logger.error(f"Diagram generation background task failed: {e}")
        job_manager.update_job(
            job_id,
            status="error",
            error=str(e),
            completed_at=datetime.now().isoformat()
        )

def _create_basic_svg(archetype: str, archetype_details: Dict) -> str:
    """Create basic SVG content"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="600" fill="#f8fafc"/>
    <text x="400" y="50" text-anchor="middle" font-size="24" font-weight="bold">
        {archetype.replace('_', ' ').title()} Architecture
    </text>
    <rect x="300" y="200" width="200" height="100" fill="#dbeafe" stroke="#3b82f6" rx="8"/>
    <text x="400" y="255" text-anchor="middle" font-size="14">
        {archetype_details.get('description', 'Architecture Pattern')}
    </text>
</svg>'''

# =================== JOB MANAGEMENT ENDPOINTS ===================
@router.get("/jobs/{job_id}")
@handle_service_error
async def get_job_status(job_id: str):
    """Get status of a job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/jobs/{job_id}")
@handle_service_error
async def delete_job(job_id: str):
    """Delete a job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_manager.delete_job(job_id)
    return {"message": f"Job {job_id} deleted"}

@router.get("/jobs")
@handle_service_error
async def list_jobs():
    """List all jobs"""
    job_manager.cleanup_old_jobs()  # Clean up before listing
    return {"jobs": list(job_manager._jobs.values())}

# =================== FILE DOWNLOAD ENDPOINTS ===================
@router.get("/download/{filename}")
@handle_service_error
async def download_file(filename: str):
    """Download generated file with security checks"""
    # Validate filename
    if not validate_file_extension(filename):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type"
        )
    
    # Search in results directories
    search_dirs = [
        AppConfig.RESULTS_DIR / "diagrams",
        AppConfig.RESULTS_DIR / "lucid",
        AppConfig.RESULTS_DIR / "pdf",
        AppConfig.RESULTS_DIR / "excel"
    ]
    
    for search_dir in search_dirs:
        try:
            file_path = safe_path_join(search_dir, filename)
            
            # Check if file exists in any job subdirectory
            if not file_path.exists():
                for job_dir in search_dir.glob("*"):
                    if job_dir.is_dir():
                        potential_path = safe_path_join(job_dir, filename)
                        if potential_path.exists():
                            file_path = potential_path
                            break
            
            if file_path.exists():
                # Check file size
                if file_path.stat().st_size > AppConfig.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413, 
                        detail="File too large"
                    )
                
                return FileResponse(
                    path=str(file_path),
                    filename=filename,
                    media_type="application/octet-stream"
                )
                
        except ValueError as e:
            logger.warning(f"Security violation attempt: {e}")
            raise HTTPException(status_code=400, detail="Invalid file path")
        except Exception as e:
            logger.error(f"Error accessing file {filename}: {e}")
            continue
    
    raise HTTPException(status_code=404, detail="File not found")

# =================== PORTFOLIO ANALYSIS ENDPOINTS ===================
@router.post("/portfolio/analyze")
@handle_service_error
async def analyze_application_portfolio(request: PortfolioAnalysisRequest):
    """Analyze entire application portfolio"""
    if not ARCHETYPE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Archetype service not available"
        )
    
    try:
        result = services['archetype'].analyze_portfolio_archetypes(
            request.applications
        )
        
        if request.include_diagram_recommendations:
            archetype_counts = result["portfolio_summary"]["archetype_distribution"]
            result["diagram_recommendations"] = services['archetype']._generate_diagram_recommendations(
                archetype_counts
            )
        
        return result
    except Exception as e:
        logger.error(f"Portfolio analysis error: {e}")
        raise APIError(f"Error analyzing portfolio: {str(e)}", 500)

# =================== HEALTH AND STATUS ENDPOINTS ===================
@router.get("/health")
@handle_service_error
async def health_check():
    """Health check for archetype service"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "archetype_service": ARCHETYPE_SERVICE_AVAILABLE,
            "enhancement_service": ENHANCEMENT_SERVICE_AVAILABLE,
            "banking_enhancer": BANKING_ENHANCER_AVAILABLE,
            "diagram_generators": DIAGRAM_GENERATORS_AVAILABLE
        },
        "directories": {
            "results": AppConfig.RESULTS_DIR.exists(),
            "data_staging": AppConfig.DATA_STAGING_DIR.exists(),
            "templates": AppConfig.TEMPLATES_DIR.exists()
        },
        "data_sources": {
            "excel_cache": len(_excel_results_cache),
            "csv_available": (AppConfig.DATA_STAGING_DIR / "applicationList.csv").exists()
        },
        "jobs": {
            "active_jobs": len(job_manager._jobs),
            "max_jobs": job_manager._max_jobs
        }
    }
    
    # Check if any critical services are down
    if not any(status["services"].values()):
        status["status"] = "degraded"
        status["message"] = "No services available"
    
    return status

@router.get("/status")
@handle_service_error 
async def get_service_status():
    """Detailed service status"""
    job_manager.cleanup_old_jobs()  # Clean up old jobs
    
    return {
        "archetype_service": {
            "available": ARCHETYPE_SERVICE_AVAILABLE,
            "initialized": "archetype" in services
        },
        "enhancement_service": {
            "available": ENHANCEMENT_SERVICE_AVAILABLE,
            "features": ["lucidchart_generation"] if ENHANCEMENT_SERVICE_AVAILABLE else []
        },
        "banking_enhancer": {
            "available": BANKING_ENHANCER_AVAILABLE,
            "initialized": "banking_enhancer" in services
        },
        "job_management": {
            "active_jobs": len(job_manager._jobs),
            "max_concurrent": job_manager._max_jobs,
            "cleanup_enabled": True
        },
        "file_system": {
            "results_dir": str(AppConfig.RESULTS_DIR),
            "max_file_size_mb": AppConfig.MAX_FILE_SIZE // (1024 * 1024),
            "allowed_extensions": list(AppConfig.ALLOWED_FILE_TYPES)
        },
        "data_integration": {
            "csv_path": str(AppConfig.DATA_STAGING_DIR / "applicationList.csv"),
            "csv_exists": (AppConfig.DATA_STAGING_DIR / "applicationList.csv").exists(),
            "excel_cache_size": len(_excel_results_cache)
        }
    }

# =================== CLEANUP TASKS ===================
def cleanup_expired_jobs():
    """Periodic cleanup task"""
    job_manager.cleanup_old_jobs()

# Schedule cleanup (you might want to use a proper task scheduler in production)
import atexit
atexit.register(cleanup_expired_jobs)