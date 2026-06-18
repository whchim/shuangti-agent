from app.llm.base import BaseLLM, LLMResponse
from app.core.config import settings


class DeepSeekAdapter(BaseLLM):
    """DeepSeek 适配器（兼容 OpenAI API 格式）"""

    @property
    def model_name(self) -> str:
        return "deepseek"

    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        # TODO: 接入 DeepSeek API（OpenAI 兼容格式）
        raise NotImplementedError("DeepSeek 适配器待实现")

    async def chat_stream(self, messages: list[dict], **kwargs):
        # TODO: 接入 DeepSeek 流式 API
        raise NotImplementedError("DeepSeek 流式适配器待实现")

    async def generate_embedding(self, text: str) -> list[float]:
        # TODO: 调用 DeepSeek Embedding API
        raise NotImplementedError("DeepSeek Embedding 待实现")
