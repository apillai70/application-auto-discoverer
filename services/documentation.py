"""
Service for generating documentation
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.documentation_models import (
    DocumentationRequest, DocumentationResponse, DocumentTemplate,
    DocumentationJob, DocumentStatus
)

logger = logging.getLogger(__name__)

class DocumentationService:
    """Service for generating application documentation"""
    
    def __init__(self):
        self.active_jobs: Dict[str, DocumentationJob] = {}
        self.completed_jobs: Dict[str, DocumentationJob] = {}
        self.templates: Dict[str, DocumentTemplate] = {}
    
    async def start_documentation_generation(self, request: DocumentationRequest) -> str:
        """Start documentation generation"""
        job_id = str(uuid.uuid4())
        
        job = DocumentationJob(
            job_id=job_id,
            name=request.name,
            document_type=request.document_type,
            output_format=request.output_format,
            status=DocumentStatus.PENDING,
            created_at=datetime.now(),
            request=request
        )
        
        self.active_jobs[job_id] = job
        logger.info(f"Started documentation generation job {job_id}")
        return job_id
    
    async def execute_generation(self, job_id: str):
        """Execute documentation generation in background"""
        if job_id not in self.active_jobs:
            logger.error(f"Documentation job {job_id} not found")
            return
        
        job = self.active_jobs[job_id]
        
        try:
            job.status = DocumentStatus.GENERATING
            job.started_at = datetime.now()
            job.current_task = "Generating documentation"
            job.progress_percentage = 50.0
            
            # Simulate documentation generation
            # In real implementation, this would generate actual documentation
            await self._generate_document(job)
            
            job.status = DocumentStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress_percentage = 100.0
            job.current_task = "Documentation completed"
            
            # Move to completed jobs
            self.completed_jobs[job_id] = job
            
            logger.info(f"Completed documentation generation job {job_id}")
            
        except Exception as e:
            logger.error(f"Error generating documentation {job_id}: {str(e)}")
            job.status = DocumentStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
    
    async def _generate_document(self, job: DocumentationJob):
        """Generate the actual document"""
        # Placeholder for actual document generation logic
        # This would integrate with your output service to generate
        # Word docs, PDFs, etc.
        pass
    
    async def get_job_status(self, job_id: str) -> Optional[DocumentationJob]:
        """Get job status"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        return self.completed_jobs.get(job_id)
    
    async def get_generated_file(self, job_id: str) -> Optional[str]:
        """Get generated file path"""
        job = await self.get_job_status(job_id)
        if job and job.status == DocumentStatus.COMPLETED:
            return job.output_file_path
        return None
    
    async def get_available_templates(self) -> List[DocumentTemplate]:
        """Get available templates"""
        return list(self.templates.values())
    
    async def create_template(self, template: DocumentTemplate) -> str:
        """Create template"""
        template_id = str(uuid.uuid4())
        template.id = template_id
        self.templates[template_id] = template
        return template_id
    
    async def get_template(self, template_id: str) -> Optional[DocumentTemplate]:
        """Get template"""
        return self.templates.get(template_id)
    
    async def update_template(self, template_id: str, template: DocumentTemplate) -> bool:
        """Update template"""
        if template_id in self.templates:
            template.id = template_id
            template.updated_at = datetime.now()
            self.templates[template_id] = template
            return True
        return False
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    async def get_all_jobs(self) -> List[DocumentationJob]:
        """Get all jobs"""
        all_jobs = list(self.active_jobs.values()) + list(self.completed_jobs.values())
        return sorted(all_jobs, key=lambda x: x.created_at, reverse=True)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [DocumentStatus.PENDING, DocumentStatus.GENERATING]:
                job.status = DocumentStatus.CANCELLED
                job.completed_at = datetime.now()
                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]
                logger.info(f"Cancelled documentation job {job_id}")
                return True
        return False