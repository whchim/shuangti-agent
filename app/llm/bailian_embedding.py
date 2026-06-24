"""阿里百炼云 text-embedding-v4 适配器"""
import asyncio
import dashscope
from dashscope import TextEmbedding
from app.core.config import settings


class BailianEmbedding:
    """阿里百炼云嵌入模型，维度 1024"""

    MODEL_NAME = "text-embedding-v4"

    def __init__(self):
        if settings.bailian_api_key:
            dashscope.api_key = settings.bailian_api_key

    async def embed_query(self, text: str) -> list[float]:
        """将查询文本转为向量"""
        return await asyncio.to_thread(self._embed, text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量将文档转为向量"""
        return await asyncio.to_thread(self._embed_batch, texts)

    def _embed(self, text: str) -> list[float]:
        response = TextEmbedding.call(
            model=self.MODEL_NAME,
            input=text,
        )
        if response.status_code != 200:
            raise Exception(f"百炼 Embedding 失败: {response.message}")
        return response.output["embeddings"][0]["embedding"]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        # 百炼 API 单次最多支持 25 条文本
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = TextEmbedding.call(
                model=self.MODEL_NAME,
                input=batch,
            )
            if response.status_code != 200:
                raise Exception(f"百炼 Embedding 失败: {response.message}")
            for item in response.output["embeddings"]:
                results.append(item["embedding"])
        return results


_embedding_instance: BailianEmbedding = None


def get_embedding() -> BailianEmbedding:
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = BailianEmbedding()
    return _embedding_instance
