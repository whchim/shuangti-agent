"""对话服务：多轮记忆管理 M01/M02"""
import json
import math
from typing import Optional
from uuid import uuid4

from loguru import logger
from app.core.database import get_db
from app.llm.base import BaseLLM
from app.rag.store import query_documents
from app.rag.chain import build_prompt, format_sources
from app.rag.embeddings import embed_query
from app.search.tavily_search import tavily_search

MAX_SHORT_TERM_ROUNDS = 10
LTM_TRIGGER_START = 12
LTM_TRIGGER_INTERVAL = 5
RAG_SIMILARITY_THRESHOLD = 0.35  # ChromaDB 余弦距离阈值（越低越相关）
WEB_SEARCH_DOMAIN_PREFIX = "双体软件精英产业学院"

# 领域拒答兜底文案
DOMAIN_REFUSAL_ANSWER = (
    "我是双体软件精英产业学院的专属助手，当前知识库中暂时没有与您问题相关的信息。\n\n"
    "您可以尝试：\n"
    "- 换一种方式描述您的问题\n"
    "- 询问关于双体学院的招生、教学、课程等话题\n"
    "- 使用特色工具（霍兰德测评、简历优化、岗位匹配、面试模拟）"
)


async def get_or_create_session(user_id: str, session_id: Optional[str],
                                message: str) -> str:
    db = await get_db()
    if session_id:
        cursor = await db.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )
        if await cursor.fetchone():
            return session_id

    session_id = uuid4().hex
    title = message[:20] + ("..." if len(message) > 20 else "")
    await db.execute(
        "INSERT INTO sessions (id, user_id, title) VALUES (?, ?, ?)",
        (session_id, user_id, title),
    )
    await db.commit()
    logger.info(f"创建新会话: {session_id}")
    return session_id


async def save_message(session_id: str, user_id: str, role: str,
                       content: str, round_number: int = 0,
                       embedding: Optional[list[float]] = None):
    """保存消息到数据库"""
    db = await get_db()
    msg_id = uuid4().hex
    embedding_json = json.dumps(embedding) if embedding else None
    await db.execute(
        "INSERT INTO messages (id, session_id, user_id, role, content, vector_embedding) VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, session_id, user_id, role, content, embedding_json),
    )
    await db.execute(
        "UPDATE sessions SET updated_at = datetime('now') WHERE id = ?", (session_id,)
    )
    await db.commit()


async def get_round_number(session_id: str) -> int:
    """获取当前会话的消息数（作为轮次）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = ?",
        (session_id,),
    )
    row = await cursor.fetchone()
    return row[0]


async def get_short_term_memory(session_id: str) -> list[dict]:
    """获取最近 10 条短期记忆"""
    db = await get_db()
    cursor = await db.execute(
        """SELECT role, content FROM messages
           WHERE session_id = ? AND role IN ('user', 'assistant')
           ORDER BY rowid DESC LIMIT ?""",
        (session_id, MAX_SHORT_TERM_ROUNDS * 2),
    )
    rows = await cursor.fetchall()
    result = [{"role": row["role"], "content": row["content"]} for row in rows]
    result.reverse()
    return result


async def check_and_trigger_ltm(session_id: str, query: str,
                                round_number: int) -> list[str]:
    """检查并触发 M02 长期记忆检索"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT trigger_count FROM sessions WHERE id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    trigger_count = row["trigger_count"]

    should_trigger = (
        round_number >= LTM_TRIGGER_START
        and (trigger_count == 0 or
             round_number >= LTM_TRIGGER_START + trigger_count * LTM_TRIGGER_INTERVAL)
    )

    if not should_trigger:
        return []

    logger.info(f"M02 触发: session={session_id}, round={round_number}")

    query_vec = await embed_query(query)
    cursor = await db.execute(
        "SELECT content, vector_embedding FROM messages WHERE session_id = ? AND role = 'user'",
        (session_id,),
    )
    rows = await cursor.fetchall()

    if not rows:
        return []

    scored = []
    for r in rows:
        if not r["vector_embedding"]:
            continue
        vec = json.loads(r["vector_embedding"])
        sim = cosine_similarity(query_vec, vec)
        scored.append((r["content"], sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_memories = [s[0] for s in scored[:3]]

    await db.execute(
        "UPDATE sessions SET trigger_count = trigger_count + 1 WHERE id = ?",
        (session_id,),
    )
    await db.commit()

    return top_memories


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def process_chat(user_id: str, request_data: dict, llm: BaseLLM) -> dict:
    """核心对话处理流程"""
    message = request_data["message"]
    search_mode = request_data["search_mode"]
    session_id = request_data.get("session_id")

    # 1. 获取/创建会话
    session_id = await get_or_create_session(user_id, session_id, message)

    # 2. 计算轮次
    round_number = await get_round_number(session_id) + 1

    # 3. 保存用户消息
    await save_message(session_id, user_id, "user", message)

    # 4. M01 - 短期记忆
    short_term_memory = await get_short_term_memory(session_id)

    # 5. M02 - 长期记忆触发检索
    long_term_memory = []
    try:
        long_term_memory = await check_and_trigger_ltm(session_id, message, round_number)
    except Exception as e:
        logger.warning(f"M02 检索跳过: {e}")

    # 6. RAG / 联网搜索（带相似度阈值 + 领域约束）
    context_chunks = []
    web_results = []
    sources = []
    web_sources = []

    if search_mode in ("knowledge_base", "hybrid"):
        try:
            query_vec = await embed_query(message)
            chroma_result = query_documents("knowledge_base", query_vec, top_k=5)
            docs = chroma_result.get("documents", [[]])[0]
            distances = chroma_result.get("distances", [[]])[0] if "distances" in chroma_result else []

            # 相似度阈值过滤：仅保留距离 < RAG_SIMILARITY_THRESHOLD 的文档
            if distances and docs:
                filtered_docs = [
                    docs[i] for i in range(len(docs))
                    if i < len(distances) and distances[i] < RAG_SIMILARITY_THRESHOLD
                ]
                if not filtered_docs and search_mode == "hybrid":
                    # 知识库无高质量匹配，触发联网降级
                    logger.info("知识库检索无高相关结果，降级为联网搜索")
                    search_mode = "web_search"
                else:
                    context_chunks = filtered_docs or docs
            else:
                context_chunks = docs

            sources = format_sources(chroma_result)
        except Exception as e:
            logger.warning(f"知识库检索失败: {e}")

    if search_mode == "web_search":
        try:
            # 联网搜索添加领域前缀，约束搜索范围
            search_query = f"{WEB_SEARCH_DOMAIN_PREFIX} {message}"
            web_items = await tavily_search(search_query)
            web_results = [f"[{w['title']}]({w['url']})\n{w['snippet']}" for w in web_items]
            web_sources = [{"title": w["title"], "url": w["url"], "snippet": w["snippet"]} for w in web_items]
        except Exception as e:
            logger.warning(f"联网搜索失败: {e}")

    # 6b. 领域拒答策略：知识库 + 搜索均无结果时，直接兜底拒答
    if not context_chunks and not web_results:
        from datetime import datetime
        await save_message(session_id, user_id, "assistant", DOMAIN_REFUSAL_ANSWER)
        return {
            "session_id": session_id,
            "answer": DOMAIN_REFUSAL_ANSWER,
            "sources": [],
            "web_sources": [],
            "created_at": datetime.utcnow().isoformat(),
        }

    # 7. Prompt 组装
    prompt_messages = build_prompt(
        query=message,
        context_chunks=context_chunks,
        web_results=web_results,
        short_term_memory=short_term_memory,
        long_term_memory=long_term_memory,
    )

    # 8. LLM 生成
    from datetime import datetime
    try:
        llm_response = await llm.chat(prompt_messages)
        answer = llm_response.content
    except Exception:
        answer = "模型暂时不可用，以下是与您问题相关的资料：\n\n"
        if context_chunks:
            answer += "\n\n---\n".join(context_chunks[:3])

    # 9. 保存助手回复
    await save_message(session_id, user_id, "assistant", answer)

    return {
        "session_id": session_id,
        "answer": answer,
        "sources": sources,
        "web_sources": web_sources,
        "created_at": datetime.utcnow().isoformat(),
    }


async def get_sessions(user_id: str, limit: int = 50) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT id, title, session_type, created_at, updated_at
           FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?""",
        (user_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_session_messages(session_id: str, user_id: str,
                               page: int = 1, page_size: int = 20) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, title, session_type FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    )
    session = await cursor.fetchone()
    if not session:
        return None

    cursor = await db.execute(
        "SELECT COUNT(*) as total FROM messages WHERE session_id = ?", (session_id,)
    )
    total = (await cursor.fetchone())["total"]

    offset = (page - 1) * page_size
    cursor = await db.execute(
        """SELECT id, role, content, created_at
           FROM messages WHERE session_id = ?
           ORDER BY rowid ASC LIMIT ? OFFSET ?""",
        (session_id, page_size, offset),
    )
    messages = [dict(row) for row in await cursor.fetchall()]

    return {
        "id": session["id"],
        "title": session["title"],
        "session_type": session["session_type"],
        "messages": messages,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def delete_session(session_id: str, user_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
    )
    if not await cursor.fetchone():
        return False
    await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    await db.execute("DELETE FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    await db.commit()
    return True
