from fastapi import APIRouter
from services.documentation_service import EnterpriseDocumentGenerator, ProjectInfo, DocumentSections, DocumentationResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

doc_generator = EnterpriseDocumentGenerator()

class TemplateRequest(BaseModel):
    project_info: ProjectInfo
    sections: DocumentSections = DocumentSections()
    template_type: Literal["word", "excel", "both"] = "both"

@router.post("/templates/generate", response_model=DocumentationResponse)
async def generate_templates(request: TemplateRequest):
    try:
        result = doc_generator.generate_output(
            project_info=request.project_info,
            sections=request.sections,
            template_type=request.template_type
        )
        return result
    
    except Exception as e:
        logger.exception("Template generation failed")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
