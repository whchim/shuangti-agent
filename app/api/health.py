"""健康检查"""
from fastapi import APIRouter
from app.core.database import get_db
from app.rag.store import get_chroma_client

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    status = "ok"
    db_status = "ok"
    chroma_status = "ok"

    # 检查数据库
    try:
        db = await get_db()
        await db.execute("SELECT 1")
    except Exception as e:
        db_status = str(e)
        status = "degraded"

    # 检查 ChromaDB
    try:
        get_chroma_client()
    except Exception as e:
        chroma_status = str(e)
        status = "degraded"

    return {
        "status": status,
        "services": {"database": db_status, "chromadb": chroma_status},
    }
