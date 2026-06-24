"""知识库管理服务"""
import os
from uuid import uuid4

from loguru import logger
from app.core.database import get_db
from app.core.config import settings
from app.rag.loader import load_document
from app.rag.splitter import split_document
from app.rag.store import add_documents, delete_documents, get_or_create_collection
from app.rag.embeddings import embed_texts

UPLOAD_DIR = "data/documents"


async def upload_and_index(file_content: bytes, filename: str, category: str) -> dict:
    """上传文档并向量化入 ChromaDB"""
    doc_id = uuid4().hex

    # 保存原始文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    with open(file_path, "wb") as f:
        f.write(file_content)

    # 解析文本
    text = await load_document(file_path)

    # 分割
    chunks = split_document(text)

    # 向量化
    embeddings = await embed_texts(chunks)

    # 存入 ChromaDB
    chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename, "category": category, "doc_id": doc_id} for _ in chunks]
    add_documents("knowledge_base", chunk_ids, chunks, embeddings, metadatas)

    # 记录到 SQLite
    db = await get_db()
    await db.execute(
        "INSERT INTO knowledge_documents (id, filename, category, chunk_count, status) VALUES (?, ?, ?, ?, 'completed')",
        (doc_id, filename, category, len(chunks)),
    )
    await db.commit()

    logger.info(f"文档入库完成: {filename}, {len(chunks)} chunks")
    return {"id": doc_id, "filename": filename, "category": category, "chunk_count": len(chunks)}


async def list_documents() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, filename, category, chunk_count, status, created_at FROM knowledge_documents ORDER BY created_at DESC"
    )
    return [dict(row) for row in await cursor.fetchall()]


async def delete_document(doc_id: str) -> bool:
    # 删除 ChromaDB 数据
    collection = get_or_create_collection("knowledge_base")
    result = collection.get(where={"doc_id": doc_id})
    if result and result["ids"]:
        delete_documents("knowledge_base", result["ids"])

    # 删除 SQLite 记录
    db = await get_db()
    await db.execute("DELETE FROM knowledge_documents WHERE id = ?", (doc_id,))
    await db.commit()

    # 删除原始文件
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(doc_id):
            os.remove(os.path.join(UPLOAD_DIR, f))

    return True


async def reload_all_documents() -> dict:
    """重新向量化全部文档"""
    db = await get_db()
    cursor = await db.execute("SELECT id, filename, category FROM knowledge_documents")
    docs = await cursor.fetchall()

    count = 0
    for doc in docs:
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(doc["id"]):
                file_path = os.path.join(UPLOAD_DIR, f)
                text = await load_document(file_path)
                chunks = split_document(text)
                embeddings = await embed_texts(chunks)
                chunk_ids = [f"{doc['id']}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {"filename": doc["filename"], "category": doc["category"], "doc_id": doc["id"]}
                    for _ in chunks
                ]
                add_documents("knowledge_base", chunk_ids, chunks, embeddings, metadatas)
                await db.execute(
                    "UPDATE knowledge_documents SET chunk_count = ?, status = 'completed' WHERE id = ?",
                    (len(chunks), doc["id"]),
                )
                count += 1
                break

    await db.commit()
    return {"message": f"已重新向量化 {count} 个文档", "total_documents": count}
