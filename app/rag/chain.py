"""RAG 链：检索 + 生成 + Prompt 组装"""

SYSTEM_PROMPT = """你是双体软件精英产业学院的智能客服助手。你的职责是：
1. 基于提供的知识库内容，准确回答学生和教师的问题
2. 回答要专业、准确、简洁
3. 如果知识库中找不到相关信息，请诚实说明
4. 使用 Markdown 格式组织回答，包括标题、列表、表格等"""


def build_prompt(
    query: str,
    context_chunks: list[str] = None,
    web_results: list[str] = None,
    short_term_memory: list[dict] = None,
    long_term_memory: list[str] = None,
    user_profile: list[str] = None,
) -> list[dict]:
    """组装完整 Prompt"""
    system_content = SYSTEM_PROMPT

    # 用户画像
    if user_profile:
        system_content += "\n\n## 用户画像\n" + "\n".join(f"- {f}" for f in user_profile)

    messages = [{"role": "system", "content": system_content}]

    # 长期记忆
    if long_term_memory:
        memory_text = "## 历史相关对话片段\n" + "\n\n".join(long_term_memory)
        messages.append({"role": "system", "content": memory_text})

    # 知识库检索结果
    if context_chunks:
        context_text = "## 参考知识库内容\n" + "\n\n---\n".join(context_chunks)
        messages.append({"role": "system", "content": context_text})
        messages.append(
            {"role": "system", "content": "请基于以上知识库内容回答问题。如果内容不足以回答，请明确说明。"}
        )

    # 联网搜索结果
    if web_results:
        web_text = "## 联网搜索结果\n" + "\n\n".join(web_results)
        messages.append({"role": "system", "content": web_text})

    # 短期记忆
    if short_term_memory:
        messages.extend(short_term_memory)

    # 用户问题
    messages.append({"role": "user", "content": query})

    return messages


def format_sources(chroma_result: dict) -> list[dict]:
    """格式化检索结果来源"""
    sources = []
    docs = chroma_result.get("documents", [[]])[0]
    metadatas = chroma_result.get("metadatas", [[]])[0]

    for i, doc in enumerate(docs):
        source = {
            "doc_name": metadatas[i].get("filename", "未知文档") if i < len(metadatas) else "未知文档",
            "chunk": doc[:300] + "..." if len(doc) > 300 else doc,
            "page": metadatas[i].get("page") if i < len(metadatas) else None,
        }
        sources.append(source)

    return sources
