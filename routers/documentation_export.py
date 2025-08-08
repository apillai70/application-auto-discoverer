# routes/documentation_export.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

router = APIRouter()

class ExportRequest(BaseModel):
    application: str
    format: str

@router.post("/documentation/export")
async def export_documentation(req: ExportRequest):
    filename = f"{req.application}.{req.format}"
    filepath = os.path.join("results", filename)  # Or wherever your exports live

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )
