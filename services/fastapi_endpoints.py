# FastAPI Endpoints for Data Normalization Integration
# Integration Hub - Network Topology Application
# Author: Integration Hub Team
# Version: 1.0.0

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import aiofiles
import logging
import json
import os
import io
from datetime import datetime
import traceback
from pathlib import Path

from data_normalization import DataNormalizer, ProcessingConfig, create_normalizer, ProcessingResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class ConfigUpdateRequest(BaseModel):
    duplicate_strategy: Optional[str] = Field(default="smart_upsert", description="Duplicate handling strategy")
    logging_level: Optional[str] = Field(default="detailed", description="Logging detail level")
    vectorization_enabled: Optional[bool] = Field(default=True, description="Enable ML vectorization")
    field_mapping_enabled: Optional[bool] = Field(default=True, description="Enable field mapping")
    max_file_size_mb: Optional[int] = Field(default=100, description="Maximum file size in MB")
    time_window_minutes: Optional[int] = Field(default=5, description="Time window for duplicate detection")
    quality_threshold: Optional[float] = Field(default=0.8, description="Data quality threshold")

class ProcessingResultResponse(BaseModel):
    file_name: str
    original_rows: int
    processed_rows: int
    quality_score: float
    known_applications: int
    unknown_applications: int
    duplicate_info: Dict[str, Any]
    field_mapping: Dict[str, str]
    vectorization_result: Optional[Dict[str, Any]]
    processing_time: float
    status: str
    errors: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str
    uptime_seconds: float

class ValidationResponse(BaseModel):
    filename: str
    file_size_mb: float
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    detected_fields: Optional[List[str]] = None
    field_count: Optional[int] = None

class StatisticsResponse(BaseModel):
    global_statistics: Dict[str, Any]
    processing_statistics: Dict[str, Any]
    duplicate_statistics: Dict[str, Any]

# Initialize FastAPI app
app = FastAPI(
    title="Integration Hub Data Normalization API",
    description="Advanced data normalization and ML vectorization for network topology data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state
normalizer: Optional[DataNormalizer] = None
processing_results: List[ProcessingResult] = []
app_start_time = datetime.utcnow()

async def get_normalizer() -> DataNormalizer:
    """Dependency to get or create normalizer instance"""
    global normalizer
    if normalizer is None:
        config = ProcessingConfig(
            duplicate_strategy='smart_upsert',
            logging_level='detailed',
            vectorization_enabled=True,
            field_mapping_enabled=True,
            max_file_size_mb=100,
            time_window_minutes=5,
            quality_threshold=0.8
        )
        normalizer = DataNormalizer(config)
        logger.info("DataNormalizer initialized")
    return normalizer

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Integration Hub Data Normalization API")
    await get_normalizer()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Integration Hub Data Normalization API")

# Health and status endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed status"""
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        service="Integration Hub Data Normalization API",
        version="1.0.0",
        uptime_seconds=uptime
    )

@app.get("/api/status")
async def get_status(normalizer: DataNormalizer = Depends(get_normalizer)):
    """Get detailed application status"""
    global processing_results
    
    return {
        "status": "running",
        "normalizer_config": {
            "duplicate_strategy": normalizer.config.duplicate_strategy,
            "logging_level": normalizer.config.logging_level,
            "vectorization_enabled": normalizer.config.vectorization_enabled,
            "field_mapping_enabled": normalizer.config.field_mapping_enabled,
            "max_file_size_mb": normalizer.config.max_file_size_mb,
            "time_window_minutes": normalizer.config.time_window_minutes,
            "quality_threshold": normalizer.config.quality_threshold
        },
        "processing_summary": {
            "total_files_processed": len(processing_results),
            "successful_files": len([r for r in processing_results if r.status == 'completed']),
            "failed_files": len([r for r in processing_results if r.status == 'error']),
            "global_records": len(normalizer.global_record_store),
            "total_logs": len(normalizer.processing_logs)
        },
        "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds()
    }

# Configuration endpoints
@app.get("/api/config")
async def get_config(normalizer: DataNormalizer = Depends(get_normalizer)):
    """Get current normalizer configuration"""
    return {
        "config": {
            "duplicate_strategy": normalizer.config.duplicate_strategy,
            "logging_level": normalizer.config.logging_level,
            "vectorization_enabled": normalizer.config.vectorization_enabled,
            "field_mapping_enabled": normalizer.config.field_mapping_enabled,
            "max_file_size_mb": normalizer.config.max_file_size_mb,
            "time_window_minutes": normalizer.config.time_window_minutes,
            "quality_threshold": normalizer.config.quality_threshold
        },
        "field_mappings": normalizer.STANDARD_FIELD_MAP,
        "vector_mappings": normalizer.VECTOR_FIELD_MAPPINGS
    }

@app.post("/api/config")
async def update_config(config_update: ConfigUpdateRequest):
    """Update normalizer configuration"""
    global normalizer
    
    try:
        # Create new config
        new_config = ProcessingConfig(
            duplicate_strategy=config_update.duplicate_strategy,
            logging_level=config_update.logging_level,
            vectorization_enabled=config_update.vectorization_enabled,
            field_mapping_enabled=config_update.field_mapping_enabled,
            max_file_size_mb=config_update.max_file_size_mb,
            time_window_minutes=config_update.time_window_minutes,
            quality_threshold=config_update.quality_threshold
        )
        
        # Reinitialize normalizer with new config
        normalizer = DataNormalizer(new_config)
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config": {
                "duplicate_strategy": normalizer.config.duplicate_strategy,
                "logging_level": normalizer.config.logging_level,
                "vectorization_enabled": normalizer.config.vectorization_enabled,
                "field_mapping_enabled": normalizer.config.field_mapping_enabled,
                "max_file_size_mb": normalizer.config.max_file_size_mb,
                "time_window_minutes": normalizer.config.time_window_minutes,
                "quality_threshold": normalizer.config.quality_threshold
            }
        }
        
    except Exception as e:
        logger.error(f"Configuration update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Configuration update failed: {str(e)}")

# File processing endpoints
@app.post("/api/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    normalizer: DataNormalizer = Depends(get_normalizer)
):
    """Upload and process a single file asynchronously"""
    global processing_results
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Read file content asynchronously
        file_content = await file.read()
        filename = file.filename
        
        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > normalizer.config.max_file_size_mb:
            raise HTTPException(
                status_code=400, 
                detail=f"File size ({file_size_mb:.1f}MB) exceeds limit ({normalizer.config.max_file_size_mb}MB)"
            )
        
        # Process file asynchronously
        result = await asyncio.get_event_loop().run_in_executor(
            None, normalizer.process_file, file_content, filename
        )
        
        # Store result
        processing_results.append(result)
        
        # Convert result to response model
        result_dict = {
            "file_name": result.file_name,
            "original_rows": result.original_rows,
            "processed_rows": result.processed_rows,
            "quality_score": result.quality_score,
            "known_applications": result.known_applications,
            "unknown_applications": result.unknown_applications,
            "duplicate_info": result.duplicate_info,
            "field_mapping": result.field_mapping,
            "vectorization_result": result.vectorization_result,
            "processing_time": result.processing_time,
            "status": result.status,
            "errors": result.errors or []
        }
        
        logger.info(f"File processed successfully: {filename}")
        
        return {
            "status": "success",
            "message": f"File {filename} processed successfully",
            "result": result_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.post("/api/upload/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    normalizer: DataNormalizer = Depends(get_normalizer)
):
    """Upload and process multiple files asynchronously"""
    global processing_results
    
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        async def process_single_file(file: UploadFile) -> Dict[str, Any]:
            """Process a single file asynchronously"""
            try:
                if not file.filename:
                    return {
                        "file_name": "unknown",
                        "status": "error",
                        "message": "Empty filename"
                    }
                
                # Read file content
                file_content = await file.read()
                filename = file.filename
                
                # Validate file size
                file_size_mb = len(file_content) / (1024 * 1024)
                if file_size_mb > normalizer.config.max_file_size_mb:
                    return {
                        "file_name": filename,
                        "status": "error",
                        "message": f"File size ({file_size_mb:.1f}MB) exceeds limit"
                    }
                
                # Process file
                result = await asyncio.get_event_loop().run_in_executor(
                    None, normalizer.process_file, file_content, filename
                )
                processing_results.append(result)
                
                # Convert to response format
                return {
                    "file_name": result.file_name,
                    "original_rows": result.original_rows,
                    "processed_rows": result.processed_rows,
                    "quality_score": result.quality_score,
                    "known_applications": result.known_applications,
                    "unknown_applications": result.unknown_applications,
                    "duplicate_info": result.duplicate_info,
                    "field_mapping": result.field_mapping,
                    "vectorization_result": result.vectorization_result,
                    "processing_time": result.processing_time,
                    "status": result.status,
                    "errors": result.errors or []
                }
                
            except Exception as e:
                logger.error(f"Failed to process file {file.filename}: {str(e)}")
                return {
                    "file_name": file.filename,
                    "status": "error",
                    "message": str(e)
                }
        
        # Process all files concurrently
        batch_results = await asyncio.gather(
            *[process_single_file(file) for file in files],
            return_exceptions=True
        )
        
        # Handle any exceptions
        processed_results = []
        for result in batch_results:
            if isinstance(result, Exception):
                processed_results.append({
                    "file_name": "unknown",
                    "status": "error",
                    "message": str(result)
                })
            else:
                processed_results.append(result)
        
        successful_files = [r for r in processed_results if r.get('status') != 'error']
        failed_files = [r for r in processed_results if r.get('status') == 'error']
        
        return {
            "status": "success",
            "message": f"Batch processing completed: {len(successful_files)} successful, {len(failed_files)} failed",
            "results": processed_results,
            "summary": {
                "total_files": len(files),
                "successful": len(successful_files),
                "failed": len(failed_files)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# Results endpoints
@app.get("/api/results")
async def get_results(
    limit: Optional[int] = Query(None, description="Limit number of results"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get all processing results with optional filtering"""
    global processing_results
    
    try:
        results = processing_results.copy()
        
        # Apply filters
        if status:
            results = [r for r in results if r.status == status]
        
        if limit:
            results = results[-limit:]
        
        # Convert to response format
        results_json = []
        for result in results:
            result_dict = {
                "file_name": result.file_name,
                "original_rows": result.original_rows,
                "processed_rows": result.processed_rows,
                "quality_score": result.quality_score,
                "known_applications": result.known_applications,
                "unknown_applications": result.unknown_applications,
                "duplicate_info": result.duplicate_info,
                "field_mapping": result.field_mapping,
                "vectorization_result": result.vectorization_result,
                "processing_time": result.processing_time,
                "status": result.status,
                "errors": result.errors or []
            }
            results_json.append(result_dict)
        
        return {
            "status": "success",
            "results": results_json,
            "total_count": len(results_json),
            "filters": {
                "limit": limit,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")

@app.get("/api/results/{filename}")
async def get_result_by_filename(filename: str):
    """Get processing result for specific file"""
    global processing_results
    
    try:
        for result in processing_results:
            if result.file_name == filename:
                result_dict = {
                    "file_name": result.file_name,
                    "original_rows": result.original_rows,
                    "processed_rows": result.processed_rows,
                    "quality_score": result.quality_score,
                    "known_applications": result.known_applications,
                    "unknown_applications": result.unknown_applications,
                    "duplicate_info": result.duplicate_info,
                    "field_mapping": result.field_mapping,
                    "vectorization_result": result.vectorization_result,
                    "processing_time": result.processing_time,
                    "status": result.status,
                    "errors": result.errors or []
                }
                return {
                    "status": "success",
                    "result": result_dict
                }
        
        raise HTTPException(status_code=404, detail=f"No results found for file: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve result for {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve result: {str(e)}")

# Export endpoints
@app.get("/api/export/normalized")
async def export_normalized_data(
    format: str = Query("json", description="Export format (json, csv)"),
    normalizer: DataNormalizer = Depends(get_normalizer)
):
    """Export all normalized data"""
    try:
        if not normalizer.global_record_store:
            raise HTTPException(status_code=404, detail="No normalized data available for export")
        
        # Convert global record store to exportable format
        records = []
        for key, record_info in normalizer.global_record_store.items():
            record = record_info['data'].copy()
            if hasattr(record, 'to_dict'):
                record = record.to_dict()
            record['_global_key'] = key
            record['_first_seen'] = record_info['first_seen']
            record['_last_updated'] = record_info['last_updated']
            record['_update_count'] = record_info.get('update_count', 0)
            records.append(record)
        
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_records": len(records),
            "export_format": format.lower(),
            "schema_version": "1.0",
            "data": records
        }
        
        if format.lower() == "json":
            return {
                "status": "success",
                "export_data": export_data
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/export/ml/{filename}")
async def export_ml_data(
    filename: str,
    format: str = Query("json", description="Export format")
):
    """Export ML-ready data for specific file"""
    global processing_results
    
    try:
        # Find result for filename
        target_result = None
        for result in processing_results:
            if result.file_name == filename:
                target_result = result
                break
        
        if not target_result:
            raise HTTPException(status_code=404, detail=f"No results found for file: {filename}")
        
        if not target_result.vectorization_result or not target_result.vectorization_result.get('ready_for_ml'):
            raise HTTPException(status_code=404, detail=f"No ML-ready data available for file: {filename}")
        
        ml_export = {
            "exported_at": datetime.utcnow().isoformat(),
            "file_name": filename,
            "format": format.lower(),
            "tensor_shape": target_result.vectorization_result['tensor_shape'],
            "feature_count": target_result.vectorization_result['feature_count'],
            "feature_names": target_result.vectorization_result['feature_names'],
            "encoding_maps": target_result.vectorization_result['encoding_maps'],
            "statistics": target_result.vectorization_result['statistics'],
            "metadata": {
                "original_rows": target_result.original_rows,
                "processed_rows": target_result.processed_rows,
                "quality_score": target_result.quality_score,
                "processing_time": target_result.processing_time
            }
        }
        
        return {
            "status": "success",
            "ml_data": ml_export
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML export failed for {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ML export failed: {str(e)}")

# Logging and monitoring endpoints
@app.get("/api/logs")
async def get_processing_logs(
    limit: int = Query(100, description="Number of logs to return"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    normalizer: DataNormalizer = Depends(get_normalizer)
):
    """Get processing logs with filtering"""
    try:
        logs = normalizer.get_processing_logs()
        
        # Filter logs
        if level:
            logs = [log for log in logs if log['level'] == level]
        if category:
            logs = [log for log in logs if log['category'] == category]
        
        # Limit results
        if limit:
            logs = logs[-limit:]
        
        return {
            "status": "success",
            "logs": logs,
            "total_count": len(logs),
            "filters": {
                "level": level,
                "category": category,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@app.get("/api/statistics", response_model=Dict[str, Any])
async def get_statistics(normalizer: DataNormalizer = Depends(get_normalizer)):
    """Get comprehensive processing statistics"""
    global processing_results
    
    try:
        # Get global statistics
        global_stats = normalizer.get_global_statistics()
        
        # Calculate processing statistics
        completed_results = [r for r in processing_results if r.status == 'completed']
        processing_stats = {
            "total_files_processed": len(processing_results),
            "successful_files": len(completed_results),
            "failed_files": len([r for r in processing_results if r.status == 'error']),
            "total_records_processed": sum(r.processed_rows for r in completed_results),
            "average_quality_score": sum(r.quality_score for r in completed_results) / len(completed_results) if completed_results else 0,
            "total_processing_time": sum(r.processing_time for r in processing_results),
            "ml_ready_files": len([r for r in processing_results if r.vectorization_result and r.vectorization_result.get('ready_for_ml')]),
            "average_processing_time": sum(r.processing_time for r in processing_results) / len(processing_results) if processing_results else 0
        }
        
        # Calculate duplicate statistics
        duplicate_stats = {
            "total_new_records": sum(r.duplicate_info.get('new_records', 0) for r in processing_results),
            "total_updated_records": sum(r.duplicate_info.get('updated_records', 0) for r in processing_results),
            "total_ignored_duplicates": sum(r.duplicate_info.get('ignored_duplicates', 0) for r in processing_results),
            "duplicate_efficiency": 0
        }
        
        # Calculate duplicate efficiency
        total_duplicates = duplicate_stats["total_updated_records"] + duplicate_stats["total_ignored_duplicates"]
        if total_duplicates > 0:
            duplicate_stats["duplicate_efficiency"] = (duplicate_stats["total_updated_records"] / total_duplicates) * 100
        
        return {
            "status": "success",
            "statistics": {
                "global_statistics": global_stats,
                "processing_statistics": processing_stats,
                "duplicate_statistics": duplicate_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

# Utility endpoints
@app.post("/api/validate", response_model=Dict[str, Any])
async def validate_file(file: UploadFile = File(...)):
    """Validate file without processing"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Read file content
        file_content = await file.read()
        filename = file.filename
        file_size_mb = len(file_content) / (1024 * 1024)
        
        validation_result = {
            "filename": filename,
            "file_size_mb": round(file_size_mb, 2),
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate file size
        if file_size_mb > 100:  # 100MB limit
            validation_result["errors"].append(f"File size ({file_size_mb:.1f}MB) exceeds 100MB limit")
            validation_result["is_valid"] = False
        
        # Validate file type
        supported_extensions = ['.csv', '.xlsx', '.xls', '.json']
        if not any(filename.lower().endswith(ext) for ext in supported_extensions):
            validation_result["errors"].append("Unsupported file type. Supported: CSV, Excel, JSON")
            validation_result["is_valid"] = False
        
        # Try to detect fields (basic check)
        try:
            if filename.lower().endswith('.csv'):
                content_str = file_content.decode('utf-8')
                first_line = content_str.split('\n')[0]
                detected_fields = [field.strip().strip('"') for field in first_line.split(',')]
                validation_result["detected_fields"] = detected_fields
                validation_result["field_count"] = len(detected_fields)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                validation_result["warnings"].append("Excel file detected - field validation will occur during processing")
            elif filename.lower().endswith('.json'):
                json_data = json.loads(file_content.decode('utf-8'))
                if isinstance(json_data, list) and len(json_data) > 0:
                    detected_fields = list(json_data[0].keys())
                    validation_result["detected_fields"] = detected_fields
                    validation_result["field_count"] = len(detected_fields)
        except Exception as e:
            validation_result["warnings"].append(f"Could not analyze file structure: {str(e)}")
        
        return {
            "status": "success",
            "validation": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File validation failed: {str(e)}")

@app.post("/api/reset")
async def reset_normalizer():
    """Reset normalizer state"""
    global normalizer, processing_results
    
    try:
        # Clear processing results
        processing_results.clear()
        
        # Reinitialize normalizer
        normalizer = None
        await get_normalizer()
        
        logger.info("Normalizer state reset successfully")
        
        return {
            "status": "success",
            "message": "Normalizer state reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset normalizer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset normalizer: {str(e)}")

# Static file serving for frontend
@app.get("/")
async def serve_index():
    """Serve the main integration hub interface"""
    return FileResponse("templates/integration-hub-normalization.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)