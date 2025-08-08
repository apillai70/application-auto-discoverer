from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

router = APIRouter()

class DiagramExportRequest(BaseModel):
    application: str
    format: str  # expected: 'vsdx' or 'lucidchart'

@router.post("/")
async def export_diagram(req: DiagramExportRequest):
    folder_map = {
        "vsdx": "vsdx",
        "lucidchart": "lucidchart"
    }
    folder = folder_map.get(req.format.lower())
    if not folder:
        raise HTTPException(status_code=400, detail="Unsupported format")

    file_path = os.path.join("results", folder, f"{req.application}.{req.format}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )
