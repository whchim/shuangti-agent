from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Optional[dict] = None


class BaseLLM(ABC):
    """LLM 适配器统一接口"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """发送对话请求，返回完整响应"""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs):
        """发送对话请求，流式返回 token"""
        ...
