"""向量化模块 - 使用阿里百炼云 text-embedding-v4"""
from app.llm.bailian_embedding import get_embedding


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量将文本转换为向量"""
    emb = get_embedding()
    return await emb.embed_documents(texts)


async def embed_query(query: str) -> list[float]:
    """将查询文本转换为向量"""
    emb = get_embedding()
    return await emb.embed_query(query)
