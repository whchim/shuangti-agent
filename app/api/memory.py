"""记忆管理 API (M03)"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.memory import MemoryFact, MemoryFactsResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/memory", tags=["记忆管理"])


@router.get("/facts", response_model=MemoryFactsResponse)
async def get_facts(user: dict = Depends(get_current_user)):
    db = await get_db()
    cursor = await db.execute(
        """SELECT id, user_id, fact, source_session_id, created_at, updated_at
           FROM long_term_memories WHERE user_id = ? ORDER BY updated_at DESC""",
        (user["user_id"],),
    )
    rows = await cursor.fetchall()
    facts = [dict(row) for row in rows]
    return {"facts": facts, "total": len(facts)}


@router.delete("/facts/{fact_id}")
async def delete_fact(fact_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    cursor = await db.execute(
        "SELECT id FROM long_term_memories WHERE id = ? AND user_id = ?",
        (fact_id, user["user_id"]),
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="未找到该记忆")
    await db.execute("DELETE FROM long_term_memories WHERE id = ?", (fact_id,))
    await db.commit()
    return {"message": "已删除"}
