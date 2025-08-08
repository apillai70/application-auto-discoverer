# routers/topology.py
"""
Network topology discovery and visualization router
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import pandas as pd
import io
import uuid
from datetime import datetime

from services.topology_service import TopologyService
from services.log_analysis_service import LogAnalysisService
from routers.auth import get_current_user, check_permission

router = APIRouter()

# Pydantic models
class NetworkNode(BaseModel):
    id: str
    label: str
    application: Optional[str] = None
    ip: Optional[str] = None
    archetype: Optional[str] = None
    cluster: Optional[int] = None
    confidence: Optional[float] = None

class NetworkLink(BaseModel):
    source: str
    target: str
    protocol: Optional[str] = None
    port: Optional[int] = None
    value: Optional[int] = None
    predicted: Optional[bool] = False

class TopologyData(BaseModel):
    nodes: List[NetworkNode]
    links: List[NetworkLink]
    metadata: Optional[Dict[str, Any]] = None

class TopologyFilter(BaseModel):
    applications: Optional[List[str]] = None
    archetypes: Optional[List[str]] = None
    show_upstream: bool = False
    show_downstream: bool = False
    show_predicted_gaps: bool = False
    confidence_threshold: float = 0.7

class DiscoveryRequest(BaseModel):
    data_source: str  # 'extrahop', 'dynatrace', 'splunk', 'combined'
    time_range: str  # '24h', '7d', '30d', 'custom'
    custom_start: Optional[datetime] = None
    custom_end: Optional[datetime] = None
    include_ml_analysis: bool = True

class GapAnalysisRequest(BaseModel):
    confidence_threshold: float = 0.8
    include_predictions: bool = True
    analysis_depth: str = "standard"  # 'basic', 'standard', 'deep'

@router.post("/upload")
async def upload_topology_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Upload network topology data from file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.json', '.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="Unsupported file format. Use JSON, CSV, or XLSX.")
        
        # Read file contents
        contents = await file.read()
        
        # Process based on file type
        topology_service = TopologyService()
        
        if file.filename.endswith('.json'):
            data = json.loads(contents.decode('utf-8'))
            processed_data = await topology_service.process_json_upload(data, file.filename)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            processed_data = await topology_service.process_csv_upload(df, file.filename)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
            processed_data = await topology_service.process_excel_upload(df, file.filename)
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "file_size": len(contents),
            "nodes_count": len(processed_data.get('nodes', [])),
            "links_count": len(processed_data.get('links', [])),
            "upload_id": str(uuid.uuid4()),
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Empty or invalid data file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/discover")
async def start_network_discovery(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Start automated network discovery from monitoring tools"""
    try:
        log_service = LogAnalysisService()
        discovery_job_id = await log_service.start_discovery(request, background_tasks)
        
        return {
            "message": "Network discovery started",
            "job_id": discovery_job_id,
            "data_source": request.data_source,
            "time_range": request.time_range,
            "status": "started",
            "estimated_duration": "5-15 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting discovery: {str(e)}")

@router.get("/discovery/{job_id}")
async def get_discovery_status(
    job_id: str,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get network discovery job status"""
    try:
        log_service = LogAnalysisService()
        status = await log_service.get_discovery_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting discovery status: {str(e)}")

@router.post("/filter")
async def filter_topology(
    filter_params: TopologyFilter,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Filter network topology data based on criteria"""
    try:
        topology_service = TopologyService()
        filtered_data = await topology_service.apply_filter(filter_params)
        
        return {
            "nodes": filtered_data["nodes"],
            "links": filtered_data["links"],
            "filter_applied": filter_params.dict(),
            "filtered_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_nodes": len(filtered_data["nodes"]),
                "total_links": len(filtered_data["links"]),
                "predicted_gaps": len([l for l in filtered_data["links"] if l.get("predicted", False)])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering topology: {str(e)}")

@router.get("/applications")
async def get_applications(
    archetype_filter: Optional[str] = None,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get list of discovered applications"""
    try:
        topology_service = TopologyService()
        applications = await topology_service.get_applications(archetype_filter)
        
        return {
            "applications": applications,
            "total_count": len(applications),
            "archetype_filter": archetype_filter,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting applications: {str(e)}")

@router.get("/archetypes")
async def get_archetypes(current_user: dict = Depends(check_permission("topology:read"))):
    """Get list of application archetypes with counts"""
    try:
        topology_service = TopologyService()
        archetypes = await topology_service.get_archetypes_with_counts()
        
        return {
            "archetypes": archetypes,
            "total_archetypes": len(archetypes),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting archetypes: {str(e)}")

@router.post("/analyze")
async def analyze_topology(
    include_ml_predictions: bool = True,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Perform comprehensive topology analysis"""
    try:
        topology_service = TopologyService()
        analysis = await topology_service.analyze_topology(include_ml_predictions)
        
        return {
            "analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat(),
            "ml_predictions_included": include_ml_predictions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing topology: {str(e)}")

@router.post("/gaps/detect")
async def detect_network_gaps(
    request: GapAnalysisRequest,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Detect gaps in network topology using ML"""
    try:
        topology_service = TopologyService()
        gaps = await topology_service.detect_gaps(request)
        
        return {
            "predicted_gaps": gaps,
            "gap_count": len(gaps),
            "confidence_threshold": request.confidence_threshold,
            "analysis_depth": request.analysis_depth,
            "detected_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting gaps: {str(e)}")

@router.get("/stats")
async def get_topology_stats(current_user: dict = Depends(check_permission("topology:read"))):
    """Get network topology statistics"""
    try:
        topology_service = TopologyService()
        stats = await topology_service.get_topology_stats()
        
        return {
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting topology stats: {str(e)}")

@router.get("/export/{format}")
async def export_topology(
    format: str,  # 'json', 'csv', 'excel', 'graphml'
    include_predictions: bool = False,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Export topology data in specified format"""
    try:
        if format not in ['json', 'csv', 'excel', 'graphml']:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        topology_service = TopologyService()
        export_path = await topology_service.export_topology(format, include_predictions)
        
        return {
            "message": "Topology exported successfully",
            "export_path": export_path,
            "format": format,
            "include_predictions": include_predictions,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting topology: {str(e)}")

@router.delete("/clear")
async def clear_topology_data(
    confirm: bool = False,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Clear all topology data (requires confirmation)"""
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Confirmation required to clear data")
        
        topology_service = TopologyService()
        await topology_service.clear_all_data()
        
        return {
            "message": "All topology data cleared successfully",
            "cleared_at": datetime.utcnow().isoformat(),
            "cleared_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing topology data: {str(e)}")

@router.get("/health")
async def topology_health_check():
    """Health check for topology service"""
    try:
        topology_service = TopologyService()
        health_status = await topology_service.health_check()
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "service": "topology",
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "topology",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }