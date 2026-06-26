"""模型配置 API"""
from fastapi import APIRouter
from app.models.model_config import ModelConfig, ModelConfigUpdate
from app.core.config import settings

router = APIRouter(prefix="/api/model", tags=["模型配置"])


@router.get("/config", response_model=ModelConfig)
async def get_model_config():
    return ModelConfig(
        current_model=settings.default_llm_model,
        deepseek_available=bool(settings.deepseek_api_key),
    )


@router.put("/config", response_model=ModelConfig)
async def update_model_config(req: ModelConfigUpdate):
    if req.deepseek_api_key is not None:
        settings.deepseek_api_key = req.deepseek_api_key
    return ModelConfig(
        current_model=settings.default_llm_model,
        deepseek_available=bool(settings.deepseek_api_key),
    )
