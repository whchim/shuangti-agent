"""对话 API"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.models.chat import ChatSendRequest, ChatSendResponse, SessionItem, SessionDetail
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.service.chat_service import process_chat, get_sessions, get_session_messages, delete_session
from app.llm.base import BaseLLM

router = APIRouter(prefix="/api/chat", tags=["对话"])


def get_llm(model: str = None) -> BaseLLM:
    """根据请求参数或默认配置动态选择 LLM 适配器"""
    model = model or settings.default_llm_model
    if model == "deepseek":
        from app.llm.deepseek import DeepSeekAdapter
        return DeepSeekAdapter()
    else:
        from app.llm.zhipu import ZhipuAdapter
        return ZhipuAdapter()


@router.post("/send")
async def send_message(req: ChatSendRequest, user: dict = Depends(get_current_user)):
    try:
        llm = get_llm(req.model)
        result = await process_chat(user["user_id"], req.model_dump(), llm)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send/stream")
async def send_message_stream(req: ChatSendRequest, user: dict = Depends(get_current_user)):
    """SSE 流式对话接口"""
    async def event_stream():
        try:
            llm = get_llm(req.model)
            # 导入 process_chat 中用到的函数
            from app.service.chat_service import (
                get_or_create_session, get_round_number,
                save_message, get_short_term_memory,
                check_and_trigger_ltm,
            )
            from app.rag.store import query_documents
            from app.rag.embeddings import embed_query
            from app.rag.chain import build_prompt

            message = req.message
            session_id = req.session_id
            search_mode = req.search_mode

            # 1. 获取/创建会话
            session_id = await get_or_create_session(user["user_id"], session_id, message)
            yield f"data: {__import__('json').dumps({'type': 'session', 'session_id': session_id})}\n\n"

            # 2. 保存用户消息
            round_number = await get_round_number(session_id) + 1
            await save_message(session_id, user["user_id"], "user", message)

            # 3. M01 短期记忆
            short_term_memory = await get_short_term_memory(session_id)

            # 4. M02 长期记忆
            long_term_memory = []
            try:
                long_term_memory = await check_and_trigger_ltm(session_id, message, round_number)
            except Exception:
                pass

            # 5. RAG / 搜索
            context_chunks = []
            web_results = []
            if search_mode in ("knowledge_base", "hybrid"):
                try:
                    query_vec = await embed_query(message)
                    chroma_result = query_documents("knowledge_base", query_vec, top_k=5)
                    docs = chroma_result.get("documents", [[]])[0]
                    context_chunks = docs
                except Exception:
                    pass

            if search_mode == "web_search":
                try:
                    engine = req.model_dump().get("search_engine", "tavily")
                    if engine == "bing":
                        from app.search.bing_search import bing_search
                        web_items = await bing_search(message)
                    else:
                        from app.search.tavily_search import tavily_search
                        web_items = await tavily_search(message)
                    web_results = [f"[{w['title']}]({w['url']})\n{w['snippet']}" for w in web_items]
                except Exception:
                    pass

            # 6. Prompt 组装
            prompt_messages = build_prompt(
                query=message,
                context_chunks=context_chunks,
                web_results=web_results,
                short_term_memory=short_term_memory,
                long_term_memory=long_term_memory,
            )

            # 7. LLM 流式生成
            full_content = ""
            async for chunk in llm.chat_stream(prompt_messages):
                full_content += chunk
                yield f"data: {__import__('json').dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # 8. 保存助手回复
            await save_message(session_id, user["user_id"], "assistant", full_content)
            yield f"data: {__import__('json').dumps({'type': 'done', 'content': full_content})}\n\n"

        except Exception as e:
            yield f"data: {__import__('json').dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
