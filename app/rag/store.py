"""ChromaDB 向量存储"""
import chromadb
from loguru import logger
from typing import Optional
from app.core.config import settings

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info(f"ChromaDB 已初始化: {settings.chroma_persist_dir}")
    return _client


def get_or_create_collection(name: str = "knowledge_base"):
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


def add_documents(collection_name: str, ids: list[str], texts: list[str],
                  embeddings: list[list[float]], metadatas: Optional[list[dict]] = None):
    """向 ChromaDB 添加文档向量"""
    collection = get_or_create_collection(collection_name)
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas or [{}] * len(ids),
    )
    logger.info(f"已添加 {len(ids)} 个文档向量到 collection: {collection_name}")


def delete_documents(collection_name: str, ids: list[str]):
    """删除指定文档向量"""
    collection = get_or_create_collection(collection_name)
    collection.delete(ids=ids)
    logger.info(f"已删除 {len(ids)} 个文档向量")


def query_documents(collection_name: str, query_embedding: list[float],
                    top_k: int = 5) -> dict:
    """向量相似度检索"""
    collection = get_or_create_collection(collection_name)
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)
