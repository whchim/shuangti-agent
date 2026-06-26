import asyncio
from openai import OpenAI
from app.llm.base import BaseLLM, LLMResponse
from app.core.config import settings


class DeepSeekAdapter(BaseLLM):
    """DeepSeek 适配器（兼容 OpenAI API 格式，使用 deepseek-v4-flash）"""

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    @property
    def model_name(self) -> str:
        return "deepseek-v4-flash"

    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model="deepseek-v4-flash",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            } if response.usage else None,
        )

    async def chat_stream(self, messages: list[dict], **kwargs):
        response = self.client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
