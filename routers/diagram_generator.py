from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from services.diagram_service import ProductionDiagramAPI, DiagramConfig, GenerationResponse
import logging

router = APIRouter()
diagram_service = ProductionDiagramAPI()
logger = logging.getLogger(__name__)

diagram_generator = ProductionDiagramAPI()

@router.post("/generate", response_model=GenerationResponse)
async def generate_diagram(config: DiagramConfig, background_tasks: BackgroundTasks):
    try:
        logger.info("Generating diagram with config: %s", config.dict())
        result = await diagram_generator.generate_diagrams(config)

        background_tasks.add_task(
            logger.info,
            f"✅ {result.charts_generated} diagrams generated in {result.generation_time:.2f}s"
        )

        return result

    except Exception as e:
        logger.exception("Diagram generation failed")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
