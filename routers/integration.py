# routers/integration.py
"""
Data integration hub router for ExtraHop, DynaTrace, and Splunk
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from services.integration_service import IntegrationService
from routers.auth import get_current_user, check_permission

router = APIRouter()

# Pydantic models
class IntegrationConfig(BaseModel):
    source_type: str  # 'extrahop', 'dynatrace', 'splunk'
    api_endpoint: str
    api_key: str
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None

class DataCollectionRequest(BaseModel):
    sources: List[str]  # List of configured source names
    time_range: str  # '1h', '24h', '7d', '30d', 'custom'
    custom_start: Optional[datetime] = None
    custom_end: Optional[datetime] = None
    data_types: List[str]  # ['network_flows', 'applications', 'metrics', 'logs']
    normalize_data: bool = True
    enable_deduplication: bool = True

class NormalizationConfig(BaseModel):
    source_schemas: Dict[str, Dict[str, str]]
    target_schema: Dict[str, str]
    field_mappings: Dict[str, Dict[str, str]]
    transformation_rules: Optional[List[Dict[str, Any]]] = None

class IntegrationStatus(BaseModel):
    source_name: str
    source_type: str
    status: str  # 'connected', 'disconnected', 'error', 'testing'
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

@router.post("/sources/configure")
async def configure_data_source(
    source_name: str,
    config: IntegrationConfig,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Configure a new data source integration"""
    try:
        integration_service = IntegrationService()
        result = await integration_service.configure_source(source_name, config)
        
        return {
            "message": f"Data source '{source_name}' configured successfully",
            "source_name": source_name,
            "source_type": config.source_type,
            "configuration_id": result["config_id"],
            "configured_at": datetime.utcnow().isoformat(),
            "configured_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configuring data source: {str(e)}")

@router.post("/sources/{source_name}/test")
async def test_data_source_connection(
    source_name: str,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Test connection to a configured data source"""
    try:
        integration_service = IntegrationService()
        test_result = await integration_service.test_connection(source_name)
        
        return {
            "source_name": source_name,
            "connection_status": test_result["status"],
            "response_time": test_result["response_time"],
            "data_available": test_result["data_available"],
            "test_details": test_result["details"],
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing connection: {str(e)}")

@router.get("/sources")
async def list_data_sources(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """List all configured data sources"""
    try:
        integration_service = IntegrationService()
        sources = await integration_service.list_sources(status_filter)
        
        return {
            "sources": sources,
            "total_count": len(sources),
            "status_filter": status_filter,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing data sources: {str(e)}")

@router.get("/sources/{source_name}/status")
async def get_source_status(
    source_name: str,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get detailed status of a specific data source"""
    try:
        integration_service = IntegrationService()
        status = await integration_service.get_source_status(source_name)
        
        return {
            "source_status": status,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting source status: {str(e)}")

@router.post("/collect")
async def start_data_collection(
    request: DataCollectionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Start data collection from configured sources"""
    try:
        integration_service = IntegrationService()
        collection_job_id = await integration_service.start_collection(request, background_tasks)
        
        return {
            "message": "Data collection started",
            "job_id": collection_job_id,
            "sources": request.sources,
            "time_range": request.time_range,
            "data_types": request.data_types,
            "normalize_data": request.normalize_data,
            "started_at": datetime.utcnow().isoformat(),
            "started_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting data collection: {str(e)}")

@router.get("/jobs/{job_id}")
async def get_collection_job_status(
    job_id: str,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get status of a data collection job"""
    try:
        integration_service = IntegrationService()
        job_status = await integration_service.get_job_status(job_id)
        
        return {
            "job_status": job_status,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

@router.post("/normalize")
async def normalize_collected_data(
    job_id: str,
    normalization_config: Optional[NormalizationConfig] = None,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Normalize collected data from multiple sources"""
    try:
        integration_service = IntegrationService()
        normalization_result = await integration_service.normalize_data(job_id, normalization_config)
        
        return {
            "message": "Data normalization completed",
            "job_id": job_id,
            "records_processed": normalization_result["records_processed"],
            "records_normalized": normalization_result["records_normalized"],
            "normalization_stats": normalization_result["stats"],
            "normalized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error normalizing data: {str(e)}")

@router.post("/deduplicate")
async def deduplicate_data(
    job_id: str,
    deduplication_strategy: str = "hash_based",  # 'hash_based', 'field_based', 'ml_based'
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Remove duplicate records from collected data"""
    try:
        integration_service = IntegrationService()
        dedup_result = await integration_service.deduplicate_data(job_id, deduplication_strategy)
        
        return {
            "message": "Data deduplication completed",
            "job_id": job_id,
            "original_records": dedup_result["original_count"],
            "unique_records": dedup_result["unique_count"],
            "duplicates_removed": dedup_result["duplicates_removed"],
            "deduplication_strategy": deduplication_strategy,
            "deduplicated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deduplicating data: {str(e)}")

@router.post("/export")
async def export_integrated_data(
    job_id: str,
    export_format: str = "json",  # 'json', 'csv', 'parquet', 'excel'
    include_metadata: bool = True,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Export integrated and normalized data"""
    try:
        if export_format not in ['json', 'csv', 'parquet', 'excel']:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        integration_service = IntegrationService()
        export_result = await integration_service.export_data(job_id, export_format, include_metadata)
        
        return {
            "message": "Data export completed",
            "job_id": job_id,
            "export_path": export_result["file_path"],
            "export_format": export_format,
            "file_size": export_result["file_size"],
            "record_count": export_result["record_count"],
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@router.get("/schemas")
async def get_data_schemas(
    source_type: Optional[str] = None,
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get data schemas for different source types"""
    try:
        integration_service = IntegrationService()
        schemas = await integration_service.get_schemas(source_type)
        
        return {
            "schemas": schemas,
            "source_type_filter": source_type,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting schemas: {str(e)}")

@router.post("/mapping/auto-generate")
async def auto_generate_field_mapping(
    source_schemas: List[Dict[str, Any]],
    target_schema: Dict[str, str],
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Auto-generate field mappings between source and target schemas"""
    try:
        integration_service = IntegrationService()
        mapping_result = await integration_service.auto_generate_mapping(source_schemas, target_schema)
        
        return {
            "message": "Field mapping generated successfully",
            "field_mappings": mapping_result["mappings"],
            "confidence_scores": mapping_result["confidence"],
            "unmapped_fields": mapping_result["unmapped"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating field mapping: {str(e)}")

@router.get("/metrics")
async def get_integration_metrics(
    time_range: str = "24h",
    current_user: dict = Depends(check_permission("topology:read"))
):
    """Get integration hub metrics and statistics"""
    try:
        integration_service = IntegrationService()
        metrics = await integration_service.get_metrics(time_range)
        
        return {
            "metrics": metrics,
            "time_range": time_range,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting integration metrics: {str(e)}")

@router.delete("/sources/{source_name}")
async def delete_data_source(
    source_name: str,
    confirm: bool = False,
    current_user: dict = Depends(check_permission("topology:write"))
):
    """Delete a configured data source"""
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Confirmation required to delete data source")
        
        integration_service = IntegrationService()
        await integration_service.delete_source(source_name)
        
        return {
            "message": f"Data source '{source_name}' deleted successfully",
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": current_user["display_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting data source: {str(e)}")

@router.get("/health")
async def integration_health_check():
    """Health check for integration service"""
    try:
        integration_service = IntegrationService()
        health_status = await integration_service.health_check()
        
        return {
            "status": "healthy" if health_status["overall_healthy"] else "unhealthy",
            "service": "integration",
            "source_statuses": health_status["sources"],
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "integration",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }
 # Add to routers/integration.py
async def startup_event():
    """Application startup event handler"""
    print("Integration service starting up...")
    # Add any startup logic here
    pass