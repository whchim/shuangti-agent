from app.llm.base import BaseLLM, LLMResponse
from app.core.config import settings


class ZhipuAdapter(BaseLLM):
    """智谱 GLM 适配器"""

    @property
    def model_name(self) -> str:
        return "zhipu"

    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        # TODO: 接入智谱官方 SDK
        raise NotImplementedError("智谱适配器待实现")

    async def chat_stream(self, messages: list[dict], **kwargs):
        # TODO: 接入智谱流式 API
        raise NotImplementedError("智谱流式适配器待实现")

    async def generate_embedding(self, text: str) -> list[float]:
        # TODO: 调用智谱 embedding-2 API
        raise NotImplementedError("智谱 Embedding 待实现")
