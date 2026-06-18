from pydantic import BaseModel


class ModelConfig(BaseModel):
    current_model: str
    available_models: list[str]
    zhipu_available: bool
    deepseek_available: bool


class ModelConfigUpdate(BaseModel):
    model: str
