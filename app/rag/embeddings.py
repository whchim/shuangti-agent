"""向量化模块"""
from app.llm.base import BaseLLM
from app.core.config import settings


async def embed_texts(texts: list[str], llm: BaseLLM) -> list[list[float]]:
    """批量将文本转换为向量"""
    embeddings = []
    for text in texts:
        vec = await llm.generate_embedding(text)
        embeddings.append(vec)
    return embeddings


async def embed_query(query: str, llm: BaseLLM) -> list[float]:
    """将查询文本转换为向量"""
    return await llm.generate_embedding(query)
