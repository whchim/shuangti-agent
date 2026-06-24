from typing import Optional
from pydantic import BaseModel


class ModelConfig(BaseModel):
    current_model: str
    available_models: list[str]
    zhipu_available: bool
    deepseek_available: bool


class ModelConfigUpdate(BaseModel):
    default_llm_model: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
