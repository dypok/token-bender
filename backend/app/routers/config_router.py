from fastapi import APIRouter
from app.models.schemas import ConfigStatusResponse

router = APIRouter()


@router.get("/api/config/status", response_model=ConfigStatusResponse)
async def config_status():
    return ConfigStatusResponse(engine="ctranslate2", model_ready=True)
