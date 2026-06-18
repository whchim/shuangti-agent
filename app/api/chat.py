"""对话 API"""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.chat import ChatSendRequest, ChatSendResponse, SessionItem, SessionDetail
from app.core.dependencies import get_current_user
from app.service.chat_service import process_chat, get_sessions, get_session_messages, delete_session
from app.llm.base import BaseLLM

router = APIRouter(prefix="/api/chat", tags=["对话"])


def get_llm():
    # TODO: 根据配置动态返回 LLM 适配器
    from app.llm.zhipu import ZhipuAdapter
    return ZhipuAdapter()


@router.post("/send")
async def send_message(req: ChatSendRequest, user: dict = Depends(get_current_user)):
    try:
        llm = get_llm()
        result = await process_chat(user["user_id"], req.model_dump(), llm)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/stream")
async def send_message_stream(req: ChatSendRequest, user: dict = Depends(get_current_user)):
    # SSE 流式接口，待实现
    raise HTTPException(status_code=501, detail="流式接口待实现")


@router.post("/sessions")
async def create_session(user: dict = Depends(get_current_user)):
    from uuid import uuid4
    from app.core.database import get_db
    db = await get_db()
    session_id = uuid4().hex
    await db.execute(
        "INSERT INTO sessions (id, user_id, title) VALUES (?, ?, '新对话')",
        (session_id, user["user_id"]),
    )
    await db.commit()
    return {"id": session_id, "title": "新对话"}


@router.get("/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    sessions = await get_sessions(user["user_id"])
    return sessions


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user),
                      page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    detail = await get_session_messages(session_id, user["user_id"], page, page_size)
    if detail is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return detail


@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str, user: dict = Depends(get_current_user)):
    deleted = await delete_session(session_id, user["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "已删除"}
