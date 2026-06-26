from typing import Optional
from pydantic import BaseModel


class ModelConfig(BaseModel):
    current_model: str
    deepseek_available: bool


class ModelConfigUpdate(BaseModel):
    deepseek_api_key: Optional[str] = None
