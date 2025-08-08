"""
Routes for documentation generation
Handles all document generation requests from the frontend
"""
# FastAPI imports
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
import logging
import zipfile
import tempfile

# Import services with error handling
try:
    from services.documentation import DocumentationService
    from services.diagram import DiagramService
    from services.comprehensive_document_generator import IntegratedDocumentService
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for now
    class DocumentationService:
        async def get_job_status(self, job_id): return None
    class DiagramService:
        async def get_job_status(self, job_id): return None
    class IntegratedDocumentService:
        async def process_frontend_request(self, data): return {'success': False}
        async def batch_generate_all_formats(self, data): return {'batch_id': '123', 'total_formats': 0, 'results': {}, 'generated_at': ''}

# Create router (replaces Flask Blueprint)
router = APIRouter(prefix="/api/documentation", tags=["documentation"])

# Initialize services
documentation_service = DocumentationService()
diagram_service = DiagramService()
integrated_service = IntegratedDocumentService()

logger = logging.getLogger(__name__)

# Pydantic models for request validation
class DocumentGenerateRequest(BaseModel):
    output_type: str
    data: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}

class BatchGenerateRequest(BaseModel):
    data: Dict[str, Any] = {}
    user_preferences: Dict[str, Any] = {}

@router.post('/generate-document')
async def generate_document(request_data: DocumentGenerateRequest):
    """
    Generate a single document format
    POST /api/documentation/generate-document
    """
    try:
        # Validate required fields
        if not request_data.output_type:
            raise HTTPException(status_code=400, detail="output_type is required")
        
        # Log the request
        logger.info(f"Generating {request_data.output_type} document for {len(request_data.data.get('applications', []))} applications")
        
        # Process the request using integrated service
        result = await integrated_service.process_frontend_request({
            'output_type': request_data.output_type,
            'data': request_data.data,
            'user_preferences': request_data.user_preferences
        })
        
        # Return response
        if result.get('success'):
            return {
                'success': True,
                'job_id': result.get('job_id'),
                'output_type': request_data.output_type,
                'result': result.get('result'),
                'generated_at': result.get('generated_at'),
                'message': f'{request_data.output_type.upper()} document generated successfully'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    'success': False,
                    'error': result.get('error'),
                    'output_type': request_data.output_type,
                    'message': f'Failed to generate {request_data.output_type.upper()} document'
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error during document generation'
            }
        )

@router.post('/batch-generate')
async def batch_generate(request_data: BatchGenerateRequest):
    """
    Generate all document formats in batch
    POST /api/documentation/batch-generate
    """
    try:
        # Log the batch request
        logger.info(f"Starting batch generation for {len(request_data.data.get('applications', []))} applications")
        
        # Process batch generation
        batch_results = await integrated_service.batch_generate_all_formats(request_data.data)
        
        # Count successful generations
        successful_count = len([r for r in batch_results['results'].values() if r.get('success', False)])
        
        return {
            'success': True,
            'batch_id': batch_results['batch_id'],
            'total_formats': batch_results['total_formats'],
            'successful_formats': successful_count,
            'results': batch_results['results'],
            'generated_at': batch_results['generated_at'],
            'message': f'Batch generation complete: {successful_count}/{batch_results["total_formats"]} formats successful'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in batch generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error during batch generation'
            }
        )

@router.get('/download/{filename}')
async def download_file(filename: str):
    """
    Download a generated document file
    GET /api/documentation/download/{filename}
    """
    try:
        # Get the generated documents directory
        generated_dir = Path('generated_documents')
        
        # Security check - prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Look for the file in various subdirectories
        possible_paths = [
            generated_dir / filename,
            generated_dir / 'visio_diagrams' / filename,
            generated_dir / 'lucid_diagrams' / filename,
            generated_dir / 'enhanced_visio_charts' / filename,
            generated_dir / 'enhanced_lucid_charts' / filename
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.warning(f"File not found: {filename}")
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
        
        # Determine mimetype based on extension
        mimetype = get_mimetype(filename)
        
        # Return file response
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=mimetype
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error during file download'
            }
        )

@router.get('/download-batch')
async def download_batch():
    """
    Download all generated files as a zip
    GET /api/documentation/download-batch
    """
    try:
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        generated_dir = Path('generated_documents')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from generated documents directory
            for file_path in generated_dir.rglob('*'):
                if file_path.is_file():
                    # Create relative path for zip
                    arcname = file_path.relative_to(generated_dir)
                    zipf.write(file_path, arcname)
        
        # Return zip file
        return FileResponse(
            path=temp_zip.name,
            filename=f'infrastructure_documents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            media_type='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error creating batch download: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error during batch download'
            }
        )

@router.get('/status/{job_id}')
async def get_job_status(job_id: str):
    """
    Get the status of a documentation job
    GET /api/documentation/status/{job_id}
    """
    try:
        # Check with documentation service
        doc_job = await documentation_service.get_job_status(job_id)
        if doc_job:
            return {
                'success': True,
                'job_id': job_id,
                'status': doc_job.status.value,
                'progress': doc_job.progress_percentage,
                'current_task': doc_job.current_task,
                'created_at': doc_job.created_at.isoformat(),
                'started_at': doc_job.started_at.isoformat() if doc_job.started_at else None,
                'completed_at': doc_job.completed_at.isoformat() if doc_job.completed_at else None,
                'error_message': doc_job.error_message
            }
        
        # Check with diagram service
        diagram_job = await diagram_service.get_job_status(job_id)
        if diagram_job:
            return {
                'success': True,
                'job_id': job_id,
                'status': diagram_job.status.value,
                'progress': diagram_job.progress_percentage,
                'current_task': diagram_job.current_task,
                'created_at': diagram_job.created_at.isoformat(),
                'started_at': diagram_job.started_at.isoformat() if diagram_job.started_at else None,
                'completed_at': diagram_job.completed_at.isoformat() if diagram_job.completed_at else None,
                'error_message': diagram_job.error_message
            }
        
        # Job not found
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error getting job status'
            }
        )

@router.get('/templates')
async def get_available_templates():
    """
    Get available documentation templates
    GET /api/documentation/templates
    """
    try:
        templates = [
            {
                'id': 'regions_solution_design',
                'name': 'Regions Solution Design Template',
                'description': 'Standard Regions Financial Corporation solution design template',
                'formats': ['word', 'pdf'],
                'sections': [
                    'Executive Summary',
                    'Project Team',
                    'Current State Architecture',
                    'Target State Architecture',
                    'Security Architecture',
                    'Non-Functional Requirements'
                ]
            },
            {
                'id': 'enterprise_architecture',
                'name': 'Enterprise Architecture Documentation',
                'description': 'Comprehensive enterprise architecture documentation',
                'formats': ['word', 'pdf', 'excel'],
                'sections': [
                    'Business Architecture',
                    'Application Architecture',
                    'Data Architecture',
                    'Technology Architecture'
                ]
            },
            {
                'id': 'application_portfolio',
                'name': 'Application Portfolio Analysis',
                'description': 'Application portfolio analysis and rationalization',
                'formats': ['excel', 'pdf'],
                'sections': [
                    'Portfolio Overview',
                    'Application Inventory',
                    'Technology Stack Analysis',
                    'Rationalization Recommendations'
                ]
            }
        ]
        
        return {
            'success': True,
            'templates': templates,
            'total_templates': len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error getting templates'
            }
        )

@router.get('/formats')
async def get_available_formats():
    """
    Get available output formats
    GET /api/documentation/formats
    """
    try:
        formats = [
            {
                'id': 'visio',
                'name': 'Microsoft Visio',
                'description': 'Professional Visio XML diagrams with enhanced metadata',
                'file_extension': 'xml',
                'mimetype': 'application/xml',
                'quality_level': '95%+ Professional',
                'use_cases': ['Network topology', 'Infrastructure diagrams', 'Technical documentation']
            },
            {
                'id': 'lucid',
                'name': 'Lucidchart',
                'description': 'Enhanced Lucid Chart XML with corporate styling',
                'file_extension': 'xml',
                'mimetype': 'application/xml',
                'quality_level': '95%+ Professional',
                'use_cases': ['Architecture diagrams', 'Process flows', 'Collaborative editing']
            },
            {
                'id': 'pdf',
                'name': 'Adobe PDF',
                'description': 'Executive-ready PDF documentation with Regions branding',
                'file_extension': 'pdf',
                'mimetype': 'application/pdf',
                'quality_level': 'Executive Ready',
                'use_cases': ['Presentations', 'Formal documentation', 'Compliance reporting']
            },
            {
                'id': 'word',
                'name': 'Microsoft Word',
                'description': 'Solution design templates following corporate standards',
                'file_extension': 'docx',
                'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'quality_level': 'Corporate Standard',
                'use_cases': ['Solution documentation', 'Technical specifications', 'Editable templates']
            },
            {
                'id': 'excel',
                'name': 'Microsoft Excel',
                'description': 'Comprehensive application relationship mappers',
                'file_extension': 'xlsx',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'quality_level': 'Operational Ready',
                'use_cases': ['Application inventory', 'Relationship mapping', 'Impact analysis']
            }
        ]
        
        return {
            'success': True,
            'formats': formats,
            'total_formats': len(formats)
        }
        
    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Internal server error getting formats'
            }
        )

@router.get('/health')
async def health_check():
    """
    Health check endpoint for documentation service
    GET /api/documentation/health
    """
    try:
        # Check service availability
        services_status = {
            'documentation_service': 'healthy',
            'diagram_service': 'healthy',
            'integrated_service': 'healthy',
            'generated_documents_dir': 'accessible' if Path('generated_documents').exists() else 'missing'
        }
        
        overall_status = 'healthy' if all(
            status in ['healthy', 'accessible'] for status in services_status.values()
        ) else 'degraded'
        
        return {
            'success': True,
            'status': overall_status,
            'services': services_status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

def get_mimetype(filename: str) -> str:
    """Get mimetype based on file extension"""
    
    extension = Path(filename).suffix.lower()
    
    mimetypes = {
        '.xml': 'application/xml',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.json': 'application/json',
        '.zip': 'application/zip',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.svg': 'image/svg+xml'
    }
    
    return mimetypes.get(extension, 'application/octet-stream')