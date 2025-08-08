"""
Service for generating diagrams
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.diagram_models import (
    DiagramRequest, DiagramResponse, DiagramJob, DiagramStatus,
    DiagramType, DiagramFormat
)

logger = logging.getLogger(__name__)

class DiagramService:
    """Service for generating network and application diagrams"""
    
    def __init__(self):
        self.active_jobs: Dict[str, DiagramJob] = {}
        self.completed_jobs: Dict[str, DiagramJob] = {}
    
    async def start_diagram_generation(self, request: DiagramRequest) -> str:
        """Start diagram generation"""
        job_id = str(uuid.uuid4())
        
        job = DiagramJob(
            job_id=job_id,
            name=request.name,
            diagram_type=request.diagram_type,
            output_format=request.output_format,
            status=DiagramStatus.PENDING,
            created_at=datetime.now(),
            request=request
        )
        
        self.active_jobs[job_id] = job
        logger.info(f"Started diagram generation job {job_id}")
        return job_id
    
    async def execute_generation(self, job_id: str):
        """Execute diagram generation in background"""
        if job_id not in self.active_jobs:
            logger.error(f"Diagram job {job_id} not found")
            return
        
        job = self.active_jobs[job_id]
        
        try:
            job.status = DiagramStatus.GENERATING
            job.started_at = datetime.now()
            job.current_task = "Generating diagram"
            job.progress_percentage = 50.0
            
            # Simulate diagram generation
            await self._generate_diagram(job)
            
            job.status = DiagramStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress_percentage = 100.0
            job.current_task = "Diagram completed"
            
            # Move to completed jobs
            self.completed_jobs[job_id] = job
            
            logger.info(f"Completed diagram generation job {job_id}")
            
        except Exception as e:
            logger.error(f"Error generating diagram {job_id}: {str(e)}")
            job.status = DiagramStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
    
    async def _generate_diagram(self, job: DiagramJob):
        """Generate the actual diagram"""
        # Placeholder for actual diagram generation logic
        pass
    
    async def get_job_status(self, job_id: str) -> Optional[DiagramJob]:
        """Get job status"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        return self.completed_jobs.get(job_id)
    
    async def get_generated_file(self, job_id: str) -> Optional[str]:
        """Get generated file"""
        job = await self.get_job_status(job_id)
        if job and job.status == DiagramStatus.COMPLETED:
            return job.output_file_path
        return None
    
    async def get_available_types(self) -> List[Dict[str, str]]:
        """Get available diagram types"""
        return [
            {"name": DiagramType.NETWORK_TOPOLOGY, "description": "Network topology diagram"},
            {"name": DiagramType.APPLICATION_DEPENDENCY, "description": "Application dependency diagram"},
            {"name": DiagramType.DATA_FLOW, "description": "Data flow diagram"},
            {"name": DiagramType.INFRASTRUCTURE, "description": "Infrastructure diagram"},
            {"name": DiagramType.SERVICE_MAP, "description": "Service map diagram"}
        ]
    
    async def get_available_formats(self) -> List[Dict[str, str]]:
        """Get available formats"""
        return [
            {"name": DiagramFormat.PNG, "description": "PNG image"},
            {"name": DiagramFormat.SVG, "description": "SVG vector image"},
            {"name": DiagramFormat.PDF, "description": "PDF document"},
            {"name": DiagramFormat.VSDX, "description": "Visio diagram"},
            {"name": DiagramFormat.LUCID, "description": "Lucid chart"}
        ]
    
    async def get_all_jobs(self) -> List[DiagramJob]:
        """Get all jobs"""
        all_jobs = list(self.active_jobs.values()) + list(self.completed_jobs.values())
        return sorted(all_jobs, key=lambda x: x.created_at, reverse=True)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [DiagramStatus.PENDING, DiagramStatus.GENERATING]:
                job.status = DiagramStatus.CANCELLED
                job.completed_at = datetime.now()
                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]
                logger.info(f"Cancelled diagram job {job_id}")
                return True
        return False
    
    async def generate_preview(self, request: DiagramRequest) -> Dict[str, Any]:
        """Generate preview"""
        return {
            "preview_type": request.diagram_type,
            "estimated_size": f"{request.width}x{request.height}",
            "format": request.output_format,
            "preview_available": True
        }
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get templates"""
        return [
            {"name": "Standard Network", "type": "network_topology"},
            {"name": "Application Flow", "type": "application_dependency"},
            {"name": "Infrastructure Overview", "type": "infrastructure"}
        ]
    
    async def export_diagram_data(self, topology_id: str, diagram_type: str) -> Dict[str, Any]:
        """Export diagram data"""
        return {
            "topology_id": topology_id,
            "diagram_type": diagram_type,
            "export_format": "json",
            "data_exported": True
        }