from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Network discovery feature not implemented yet"}