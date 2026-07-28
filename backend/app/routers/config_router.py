from fastapi import APIRouter
from app.models.schemas import ConfigStatusResponse
from app.services.translator import check_ollama_status

router = APIRouter()


@router.get("/api/config/status", response_model=ConfigStatusResponse)
async def config_status():
    ollama_ok = await check_ollama_status()
    return ConfigStatusResponse(ollama_available=ollama_ok, deepl_configured=False)
