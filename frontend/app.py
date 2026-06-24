"""双体智能体系统 — 统一主界面（视觉增强版）"""
import streamlit as st
from auth import require_auth, show_sidebar_header
from api_client import (
    api_send_message, api_send_message_stream,
    api_list_sessions, api_create_session,
    api_get_session_messages, api_delete_session,
    api_upload_document, api_list_documents,
    api_delete_document, api_reload_documents, api_ingest_url,
    api_get_career_questions, api_career_assessment,
    api_resume_optimize, api_job_match,
    api_start_interview, api_answer_interview, api_interview_report,
    api_get_model_config, api_update_model_config,
    api_get_search_config, api_update_search_config,
    api_get_profile, api_update_profile,
)

st.set_page_config(page_title="双体智能体", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ==================== 全局 CSS 主题系统 ====================
st.markdown("""
<style>
/* === 品牌变量 === */
:root {
  --brand-start: #667eea;
  --brand-end: #764ba2;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;
  --card-shadow: 0 2px 12px rgba(0,0,0,0.06);
  --card-hover-shadow: 0 6px 24px rgba(0,0,0,0.10);
  --radius: 12px;
}

/* === 全局元素 === */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f8f9ff 0%, #f0f2ff 100%);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: var(--radius);
}
.stButton > button {
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  font-weight: 500 !important;
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
}

/* === 卡片系统 === */
.stCard {
  background: white;
  border: 1px solid #eee;
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--card-shadow);
  transition: all 0.25s ease;
  margin-bottom: 0.75rem;
}
.stCard:hover {
  box-shadow: var(--card-hover-shadow);
  border-color: #ddd;
}

/* === 渐变标题 === */
.stGradientTitle {
  background: linear-gradient(135deg, var(--brand-start), var(--brand-end));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
  font-size: 1.5rem;
  margin: 0;
  padding: 0;
}

/* === 统计指标卡 === */
.stMetricCard {
  background: white;
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  box-shadow: var(--card-shadow);
  text-align: center;
  border-top: 3px solid var(--brand-start);
}
.stMetricCard .label { color: #999; font-size: 0.8rem; margin-bottom: 0.25rem; }
.stMetricCard .value { font-size: 1.6rem; font-weight: 700; color: #333; }

/* === Badge 标签 === */
.stBadge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  margin: 0 2px;
}
.stBadge-success { background: #d1fae5; color: #065f46; }
.stBadge-warning { background: #fef3c7; color: #92400e; }
.stBadge-danger { background: #fee2e2; color: #991b1b; }
.stBadge-info { background: #dbeafe; color: #1e40af; }

/* === 标签云 === */
.stTag {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 16px;
  font-size: 0.82rem;
  margin: 2px 4px;
  font-weight: 500;
}
.stTag-green { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
.stTag-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.stTag-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
.stTag-purple { background: #ede9fe; color: #5b21b6; border: 1px solid #ddd6fe; }

/* === 进度增强 === */
div[data-testid="stProgress"] > div {
  border-radius: 10px !important;
}
div[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--brand-start), var(--brand-end)) !important;
  border-radius: 10px !important;
}

/* === 分区容器 === */
.stSection {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: var(--radius);
  padding: 1.5rem;
  margin-bottom: 1rem;
  box-shadow: var(--card-shadow);
}

/* === 搜索卡片 === */
.stSearchHero {
  background: linear-gradient(135deg, #667eea0a 0%, #764ba20a 100%);
  border: 2px dashed #e0e0e0;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
}

/* === 文档卡片 === */
.stDocCard {
  background: white;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
  transition: all 0.2s ease;
  border-left: 4px solid var(--brand-start);
}
.stDocCard:hover {
  box-shadow: 0 3px 14px rgba(0,0,0,0.08);
  border-left-color: var(--brand-end);
}

/* === 环形进度 === */
.ring-progress {
  width: 120px; height: 120px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto;
  font-size: 2rem; font-weight: 700;
  position: relative;
}
.ring-progress::before {
  content: '';
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: white;
}

/* === 聊天气泡增强 === */
div[data-testid="stChatMessage"] {
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
div[data-testid="stChatMessage"]:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* === Toast/Status 增强 === */
div[data-testid="stNotification"] {
  border-radius: 12px !important;
}
div[data-testid="stExpander"] {
  border-radius: 10px !important;
  border: 1px solid #f0f0f0 !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}

/* === 侧边栏按钮 === */
div[data-testid="stSidebar"] .stButton > button {
  border-radius: 6px !important;
  font-size: 0.9rem !important;
}
div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--brand-start), var(--brand-end)) !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
# 初始化所有 session_state 键值，防止首次渲染时报 KeyError
# 每个键控制一个独立的前端功能模块:
#   nav:          当前页面路由标识
#   sessions:     侧边栏会话列表缓存
#   messages:     当前会话的消息列表 (前端内存)
#   holland_*:    霍兰德测评的状态管理
#   interview_*:  面试模拟的状态机变量
INIT_STATE = {
    "api_base": "http://localhost:8000",
    "nav": "chat",
    "sessions": [], "current_session_id": None,
    "messages": [], "chat_count": 0, "sessions_loaded": False,
    "editing_message_idx": None, "edit_content": "",
    "holland_questions": None, "holland_result": None,
    "interview_session": None, "interview_question": None,
    "interview_q_num": 0, "interview_total": 0,
    "interview_feedback": None, "interview_done": False,
    "model_config": {}, "search_config": {}, "profile": {},
}
for k, v in INIT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

require_auth()

# ==================== 辅助函数 ====================

def load_sessions():
    """从后端 API 拉取当前用户的所有会话列表并写入 session_state。

    调用时机：
      - 进入 Sidebar 首次渲染时（sessions_loaded == False）
      - 创建/删除/切换会话后手动刷新
    """
    try:
        result = api_list_sessions()
        st.session_state.sessions = result if isinstance(result, list) else result.get("sessions", [])
        st.session_state.sessions_loaded = True
    except Exception:
        st.session_state.sessions = []
        st.session_state.sessions_loaded = True

def load_messages(session_id: str):
    """从后端加载指定会话的历史消息，并标准化为前端渲染格式。

    Args:
        session_id: 目标会话 ID

    会将 API 返回的消息列表转换为统一的 {"role", "content", "id"} 结构，
    同时更新 chat_count 计数器用于统计面板展示。
    """
    try:
        result = api_get_session_messages(session_id)
        msgs = result.get("messages", [])
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"], "id": m.get("id", "")}
            for m in msgs
        ]
        st.session_state.chat_count = len(msgs)
    except Exception:
        st.session_state.messages = []

def _format_answer(result: dict) -> str:
    """将后端 Chat API 返回的结果格式化为前端展示的 Markdown 字符串。

    拼接逻辑：
      - answer 正文作为主内容
      - sources 字段拼为「📖 参考来源」列表（知识库检索到的文档片段）
      - web_sources 字段拼为「🌐 网络来源」列表（联网搜索到的网页链接）

    Args:
        result: API 返回的原始响应字典

    Returns:
        格式化后的 Markdown 文本
    """
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    web_sources = result.get("web_sources", [])
    if sources:
        answer += "\n\n---\n**📖 参考来源：**\n"
        for i, src in enumerate(sources, 1):
            answer += f"{i}. {src.get('doc_name', '未知')} — {src.get('chunk', '')[:100]}\n"
    if web_sources:
        answer += "\n**🌐 网络来源：**\n"
        for i, src in enumerate(web_sources, 1):
            answer += f"{i}. [{src.get('title', '未知')}]({src.get('url', '#')})\n"
    return answer

def _handle_chat_result(result: dict) -> str:
    """处理 Chat API 响应 — 提取 session_id 并格式化答案。

    当后端为消息自动创建了 session_id 时，同步更新前端的 current_session_id，
    并刷新侧边栏会话列表。

    Args:
        result: API 返回的原始响应字典

    Returns:
        格式化后的 Markdown 答案文本
    """
    sid = result.get("session_id")
    if sid and not st.session_state.current_session_id:
        st.session_state.current_session_id = sid
        load_sessions()
    return _format_answer(result)

def delete_message_from_state(idx: int):
    """从 session_state 中删除指定索引的消息，并级联删除关联的配对消息。

    删除规则：
      - 删除 user 消息时，若其后紧接 assistant 消息，则一并删除（成对删除）
      - 删除 assistant 消息时，若其前紧接 user 消息，则一并删除
      - 边界情况（首/末条）只删除自身

    Args:
        idx: 要删除的消息在 messages 列表中的索引
    """
    msgs = st.session_state.messages
    if idx < len(msgs):
        role = msgs[idx]["role"]
        if role == "user" and idx + 1 < len(msgs) and msgs[idx + 1]["role"] == "assistant":
            del msgs[idx:idx + 2]
        elif role == "assistant" and idx > 0 and msgs[idx - 1]["role"] == "user":
            del msgs[idx - 1:idx + 1]
        else:
            del msgs[idx]
        st.session_state.chat_count = len(msgs)

def _render_badge(status: bool, label_true: str = "已配置", label_false: str = "未配置"):
    """渲染一个带状态颜色的 CSS Badge 标签。

    用于显示配置状态（如 API Key 是否已配置）、模型可用性等二元指标。

    Args:
        status: True 显示绿色「成功」样式，False 显示红色「危险」样式
        label_true: status=True 时的显示文本
        label_false: status=False 时的显示文本
    """
    cls = "stBadge stBadge-success" if status else "stBadge stBadge-danger"
    text = label_true if status else label_false
    st.markdown(f'<span class="{cls}">{text}</span>', unsafe_allow_html=True)

def _render_tag(text: str, color: str = "blue"):
    """渲染一个 CSS 样式的小标签（Tag/Pill）。

    用于展示技能标签、分类标记、职业推荐等短文本标签。

    Args:
        text: 标签文本
        color: 颜色主题，可选 "green" / "red" / "blue" / "purple"
    """
    st.markdown(f'<span class="stTag stTag-{color}">{text}</span>', unsafe_allow_html=True)


# ==================== 侧边栏（Kimi 风格）====================
with st.sidebar:
    # ---- 顶部：吉祥物 + 品牌标题 ----
    mascot_path = "双体形象.jpg"
    col_img, col_title = st.columns([1, 3])
    with col_img:
        st.image(mascot_path, width=48)
    with col_title:
        st.markdown("""
        <div style="padding-top:8px">
            <span style="font-weight:700;font-size:1.1rem;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent">双体智能体</span>
        </div>
        """, unsafe_allow_html=True)

    # ---- 新建对话（最顶部，最醒目）----
    if st.button("✨ 新建对话", use_container_width=True, type="primary"):
        try:
            session = api_create_session()
            st.session_state.current_session_id = session["id"]
            st.session_state.messages = []
            st.session_state.nav = "chat"
            load_sessions()
            st.rerun()
        except Exception as e:
            st.error(f"创建失败: {e}")

    st.divider()

    # ---- 历史对话列表（主体滚动区）----
    st.markdown("#### 📁 历史对话")
    if st.button("🔄 刷新", use_container_width=True):
        load_sessions()
        st.rerun()

    if not st.session_state.sessions:
        st.caption("暂无历史对话")
    else:
        for session in st.session_state.sessions:
            sid = session["id"]
            title = session.get("title", "未命名对话")
            col1, col2 = st.columns([4, 1])
            btn_type = "primary" if sid == st.session_state.current_session_id else "secondary"
            with col1:
                if st.button(title[:22], key=f"sess_{sid}", use_container_width=True, type=btn_type):
                    st.session_state.current_session_id = sid
                    st.session_state.nav = "chat"
                    load_messages(sid)
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{sid}", help="删除"):
                    try:
                        api_delete_session(sid)
                        if st.session_state.current_session_id == sid:
                            st.session_state.current_session_id = None
                            st.session_state.messages = []
                        load_sessions()
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # ---- 最底部：用户区域（Kimi 风格 — 紧凑用户行）----
    st.divider()
    show_sidebar_header()


# ==================== 主区域路由 ====================
nav = st.session_state.nav

# ═══════════════════ 智能对话 ═══════════════════
# 核心功能页面 — 处理消息发送/接收/编辑/删除的完整生命周期
# 支持两种模式: SSE 流式输出 与 同步请求（流式失败时自动回退）
if nav == "chat":
    # --- 统计指标卡 ---
    s_count = len(st.session_state.sessions)
    m_count = st.session_state.chat_count
    c_model = st.session_state.get("model", "deepseek")

    cols = st.columns(4)
    metric_items = [
        ("💬 会话数", s_count),
        ("📝 消息数", m_count),
        ("🧠 当前模型", c_model.upper()),
        ("🔍 搜索模式", {"knowledge_base": "知识库", "web_search": "联网", "hybrid": "混合"}.get(
            st.session_state.get("search_mode", "knowledge_base"), "知识库")),
    ]
    for col, (label, val) in zip(cols, metric_items):
        with col:
            st.metric(label, val)

    # --- 控制栏（统计区下方，位置固定）---
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.selectbox("搜索模式", ["knowledge_base", "web_search", "hybrid"],
                     format_func=lambda x: {"knowledge_base": "📚 知识库", "web_search": "🌐 联网", "hybrid": "🔀 混合"}[x],
                     key="search_mode")
    with c2:
        st.segmented_control("模型", ["deepseek", "zhipu"],
                            default=st.session_state.get("model", "deepseek"),
                            key="model")
    with c3:
        st.toggle("流式输出", value=True, key="use_stream")
    with c4:
        st.checkbox("🔧 功能工具", value=False, key="show_tools")

    show_tools = st.session_state.get("show_tools", False)
    if show_tools:
        func_items = [
            ("knowledge", "📤", "知识库"), ("career", "🎯", "测评"),
            ("tools_resume", "📄", "简历"), ("tools_job", "🔗", "匹配"),
            ("tools_interview", "🎤", "面试"), ("web_search", "🌐", "搜索"),
            ("settings", "⚙️", "设置"),
        ]
        cols = st.columns(len(func_items))
        for i, (fkey, icon, label) in enumerate(func_items):
            with cols[i]:
                if st.button(f"{icon}\n{label}", key=f"chat_fn_{fkey}", use_container_width=True,
                             type="secondary" if st.session_state.nav != fkey else "primary"):
                    st.session_state.nav = fkey
                    st.rerun()

    st.markdown("---")

    # --- 消息区（纯对话展示）---
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            with st.popover("···", help="操作"):
                if st.button("✏️ 编辑", key=f"edit_{i}", use_container_width=True):
                    st.session_state.editing_message_idx = i
                    st.session_state.edit_content = msg["content"]
                    st.rerun()
                if st.button("🗑 删除", key=f"delmsg_{i}", use_container_width=True):
                    delete_message_from_state(i)
                    st.rerun()

    # --- 编辑模式 ---
    if st.session_state.editing_message_idx is not None:
        idx = st.session_state.editing_message_idx
        if idx < len(st.session_state.messages):
            st.markdown('<div class="stSection">', unsafe_allow_html=True)
            st.markdown("**✏️ 编辑消息**")
            new_content = st.text_area("内容", value=st.session_state.edit_content, key="edit_input", height=100)
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("✅ 重新发送", use_container_width=True, type="primary"):
                    st.session_state.messages[idx]["content"] = new_content
                    st.session_state.editing_message_idx = None
                    st.session_state.edit_content = ""
                    with st.spinner("重新生成中..."):
                        try:
                            result = api_send_message(
                                session_id=st.session_state.current_session_id,
                                message=new_content,
                                model=st.session_state.get("model", "deepseek"),
                                search_mode=st.session_state.get("search_mode", "knowledge_base"),
                            )
                            ans = _handle_chat_result(result)
                            if idx + 1 < len(st.session_state.messages) and st.session_state.messages[idx + 1]["role"] == "assistant":
                                st.session_state.messages[idx + 1]["content"] = ans
                            else:
                                st.session_state.messages.insert(idx + 1, {"role": "assistant", "content": ans, "id": ""})
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            with c2:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state.editing_message_idx = None
                    st.session_state.edit_content = ""
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ---- 输入框 ----
    if prompt := st.chat_input("💬 输入你的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt, "id": ""})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            full_answer = ""
            use_stream = st.session_state.get("use_stream", True)

            # ── 主路径: SSE 流式输出 ──
            if use_stream:
                placeholder = st.empty()
                try:
                    stream = api_send_message_stream(
                        session_id=st.session_state.current_session_id,
                        message=prompt,
                        model=st.session_state.get("model", "deepseek"),
                        search_mode=st.session_state.get("search_mode", "knowledge_base"),
                    )
                    for event in stream:
                        ev_type = event.get("type", "chunk")
                        if ev_type == "session":
                            sid = event.get("session_id")
                            if sid and not st.session_state.current_session_id:
                                st.session_state.current_session_id = sid
                                load_sessions()
                        elif ev_type == "chunk":
                            full_answer += event.get("content", "")
                            placeholder.markdown(full_answer + "▌")
                        elif ev_type == "done":
                            full_answer = event.get("content", full_answer)
                            placeholder.markdown(full_answer)
                        elif ev_type == "error":
                            placeholder.error(f"错误: {event.get('detail', '')}")
                            st.stop()
                    if not full_answer:
                        placeholder.markdown("(回复为空)")
                except Exception:
                    # ── 降级兜底: 流式失败时自动回退到同步请求 ──
                    if not full_answer:
                        try:
                            with st.spinner("思考中..."):
                                result = api_send_message(
                                    session_id=st.session_state.current_session_id,
                                    message=prompt,
                                    model=st.session_state.get("model", "deepseek"),
                                    search_mode=st.session_state.get("search_mode", "knowledge_base"),
                                )
                                full_answer = _handle_chat_result(result)
                                placeholder.markdown(full_answer)
                        except Exception as e2:
                            st.error(f"请求失败: {e2}")
                            st.session_state.messages = st.session_state.messages[:-1]
                            st.stop()
            else:
                # ── 备选路径: 用户关闭了流式开关，直接同步请求 ──
                with st.spinner("思考中..."):
                    try:
                        result = api_send_message(
                            session_id=st.session_state.current_session_id,
                            message=prompt,
                            model=st.session_state.get("model", "deepseek"),
                            search_mode=st.session_state.get("search_mode", "knowledge_base"),
                        )
                        full_answer = _handle_chat_result(result)
                        st.markdown(full_answer)
                    except Exception as e:
                        st.error(f"请求失败: {e}")
                        st.session_state.messages = st.session_state.messages[:-1]
                        st.stop()

            # ── 将最终答案持久化到 session_state, 并确保侧边栏同步 ──
            if full_answer:
                st.session_state.messages.append({"role": "assistant", "content": full_answer, "id": ""})
                if not st.session_state.current_session_id:
                    load_sessions()


# ═══════════════════ 系统设置 ═══════════════════
elif nav == "settings":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">⚙️ 系统设置</p>', unsafe_allow_html=True)

    # 自动加载配置
    if not st.session_state.model_config:
        try: st.session_state.model_config = api_get_model_config()
        except Exception: st.session_state.model_config = {}
    if not st.session_state.search_config:
        try: st.session_state.search_config = api_get_search_config()
        except Exception: st.session_state.search_config = {}
    if not st.session_state.profile:
        try: st.session_state.profile = api_get_profile()
        except Exception: st.session_state.profile = {}

    # --- 状态概览卡片 ---
    cfg = st.session_state.model_config
    scfg = st.session_state.search_config
    cols = st.columns(4)
    with cols[0]:
        st.metric("默认模型", cfg.get("current_model", "zhipu").upper())
    with cols[1]:
        label = "✅ 已配置" if cfg.get("zhipu_available") else "❌ 未配置"
        st.metric("智谱 GLM", label)
    with cols[2]:
        label = "✅ 已配置" if cfg.get("deepseek_available") else "❌ 未配置"
        st.metric("DeepSeek", label)
    with cols[3]:
        st.metric("搜索引擎", scfg.get("default_engine", "tavily").title())
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🤖 模型配置", "🔍 搜索配置", "👤 个人资料"])

    with tab1:
        with st.form("model_form"):
            st.markdown("#### LLM 模型设置")
            dm = st.selectbox("默认模型", ["zhipu", "deepseek"],
                              index=0 if cfg.get("current_model") != "deepseek" else 1)
            zk = st.text_input("智谱 API Key", type="password", placeholder="留空不修改")
            dk = st.text_input("DeepSeek API Key", type="password", placeholder="留空不修改")
            if st.form_submit_button("💾 保存配置", type="primary", use_container_width=True):
                try:
                    payload = {"default_llm_model": dm}
                    if zk.strip(): payload["zhipu_api_key"] = zk.strip()
                    if dk.strip(): payload["deepseek_api_key"] = dk.strip()
                    st.session_state.model_config = api_update_model_config(payload)
                    st.success("配置已保存")
                except Exception as e:
                    st.error(str(e))
        if cfg:
            st.caption(f"当前模型: `{cfg.get('current_model')}`  |  "
                       f"智谱: {'✅' if cfg.get('zhipu_available') else '❌'}  |  "
                       f"DeepSeek: {'✅' if cfg.get('deepseek_available') else '❌'}")

    with tab2:
        with st.form("search_form"):
            st.markdown("#### 搜索引擎设置")
            eng = st.selectbox("默认引擎", ["tavily", "bing"],
                               index=0 if scfg.get("default_engine") != "bing" else 1)
            tk = st.text_input("Tavily API Key", type="password", placeholder="留空不修改")
            bk = st.text_input("Bing API Key", type="password", placeholder="留空不修改")
            if st.form_submit_button("💾 保存配置", type="primary", use_container_width=True):
                try:
                    payload = {"default_search_engine": eng}
                    if tk.strip(): payload["tavily_api_key"] = tk.strip()
                    if bk.strip(): payload["bing_search_api_key"] = bk.strip()
                    st.session_state.search_config = api_update_search_config(payload)
                    st.success("配置已保存")
                except Exception as e:
                    st.error(str(e))
        if scfg:
            st.caption(f"引擎: `{scfg.get('default_engine')}`  |  "
                       f"Tavily: {'✅' if scfg.get('tavily_available') else '❌'}  |  "
                       f"Bing: {'✅' if scfg.get('bing_available') else '❌'}")

    with tab3:
        p = st.session_state.profile
        with st.form("profile_form"):
            st.markdown("#### 个人资料")
            email = st.text_input("邮箱", value=p.get("email", ""))
            nickname = st.text_input("昵称", value=p.get("nickname", ""))
            if st.form_submit_button("💾 更新资料", type="primary", use_container_width=True):
                try:
                    st.session_state.profile = api_update_profile({"email": email, "nickname": nickname})
                    st.success("已更新")
                except Exception as e:
                    st.error(str(e))
        if p:
            st.caption(f"用户名: `{p.get('username')}`  |  注册时间: {p.get('created_at', 'N/A')}")


# ═══════════════════ 知识库 ═══════════════════
# 支持三种入库方式: 文件上传 (PDF/TXT/MD)、文本粘贴、网页抓取
# 文档列表以卡片形式展示，支持删除和重建索引
elif nav == "knowledge":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">📚 知识库管理</p>', unsafe_allow_html=True)
    st.caption("上传文档或抓取网页构建内部知识库，支持 PDF、TXT、Markdown、网页链接")

    # --- 文档统计 ---
    try:
        docs_data = api_list_documents()
        docs = docs_data.get("documents", [])
        total_docs = len(docs)
        total_size = sum(d.get("file_size", d.get("size", 0)) for d in docs)
    except Exception:
        docs, total_docs, total_size = [], 0, 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📄 文档总数", total_docs)
    with col2: st.metric("💾 总大小", f"{total_size / (1024*1024):.1f} MB" if total_size else "0 MB")
    with col3: st.metric("📂 分类数", len(set(d.get("category", "未分类") for d in docs)))

    st.markdown("---")

    # --- 上传区 ---
    tab1, tab2, tab3 = st.tabs(["📤 文件上传", "📝 文本粘贴", "🌐 网页链接"])
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            uf = st.file_uploader("拖拽或选择文件", type=["pdf", "txt", "md"], label_visibility="collapsed")
        with col2:
            cat = st.selectbox("分类", ["未分类", "规章制度", "课程信息", "FAQ", "通知公告"])
        if uf and st.button("📤 上传文档", type="primary", use_container_width=True):
            if uf.size > 10 * 1024 * 1024:
                st.error("文件不能超过 10MB")
            else:
                with st.spinner("正在向量化处理..."):
                    try:
                        api_upload_document(uf.read(), uf.name, cat)
                        st.toast("上传成功！", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    with tab2:
        with st.form("paste_form"):
            txt = st.text_area("文档内容", height=200, placeholder="在此粘贴文本内容...")
            nm = st.text_input("文档名称", placeholder="请输入文档名称")
            pcat = st.selectbox("分类", ["未分类", "规章制度", "课程信息", "FAQ", "通知公告"], key="pcat")
            if st.form_submit_button("📥 提交入库", type="primary", use_container_width=True):
                if not txt.strip(): st.error("请输入文档内容")
                elif not nm.strip(): st.error("请输入文档名称")
                else:
                    with st.spinner("处理中..."):
                        try:
                            api_upload_document(txt.encode("utf-8"), f"{nm}.txt", pcat)
                            st.toast("入库成功！", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
    with tab3:
        with st.form("url_form"):
            url_input = st.text_input("网页链接", placeholder="https://www.example.com")
            ucat = st.selectbox("分类", ["未分类", "规章制度", "课程信息", "FAQ", "通知公告"], key="ucat")
            if st.form_submit_button("🌐 抓取入库", type="primary", use_container_width=True):
                if not url_input.strip():
                    st.error("请输入网页链接")
                else:
                    with st.spinner("正在抓取网页并向量化..."):
                        try:
                            result = api_ingest_url(url_input.strip(), ucat)
                            st.toast(f"入库成功！{result.get('chunk_count', 0)} 个 chunk", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    st.markdown("---")

    # --- 操作栏 ---
    st.markdown("### 已入库文档")
    c1, c2 = st.columns([4, 1])
    with c2:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄", use_container_width=True, help="刷新列表"): st.rerun()
        with col_b:
            if st.button("🔁", use_container_width=True, help="重建全部索引", type="primary"):
                with st.spinner("重建索引中..."):
                    try:
                        api_reload_documents()
                        st.toast("索引重建完成", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # --- 文档卡片列表 ---
    if not docs:
        st.info("📭 暂无已入库文档，请上传文档开始构建知识库")
    else:
        for doc in docs:
            did = doc.get("id", "")
            dn = doc.get("filename", doc.get("doc_name", "未知文档"))
            dc = doc.get("category", "未分类")
            ds = doc.get("file_size", doc.get("size", 0))
            size_mb = f"{ds / (1024*1024):.2f} MB" if ds else "未知"

            col1, col2, col3, col4 = st.columns([2.5, 1, 0.8, 0.7])
            with col1:
                icon = {"pdf": "📕", "txt": "📄", "md": "📘"}.get(dn.split(".")[-1] if "." in dn else "", "📄")
                st.markdown(f"{icon} **{dn}**")
            with col2:
                _render_tag(dc, "purple")
            with col3:
                st.caption(size_mb)
            with col4:
                if st.button("🗑", key=f"kdel_{did}", help="删除"):
                    try:
                        api_delete_document(did)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            st.divider()


# ═══════════════════ 联网搜索 ═══════════════════
elif nav == "web_search":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">🌐 联网搜索</p>', unsafe_allow_html=True)

    st.markdown('<div class="stSearchHero">', unsafe_allow_html=True)
    st.markdown("### 🔍 实时联网检索")
    st.caption("通过 Tavily / Bing 搜索引擎获取最新网络信息")
    with st.form("web_search_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("搜索关键词", placeholder="输入任何你想搜索的内容...", label_visibility="collapsed")
        with col2:
            engine = st.selectbox("引擎", ["tavily", "bing"], label_visibility="collapsed")
        if st.form_submit_button("🔍 开始搜索", type="primary", use_container_width=True):
            if not query.strip():
                st.error("请输入搜索内容")
            else:
                with st.spinner("搜索中..."):
                    try:
                        from api_client import api_search_query
                        result = api_search_query(query, engine)
                        results = result.get("results", [])
                        if results:
                            st.session_state.search_results = results
                        else:
                            st.info("未找到相关结果")
                    except Exception as e:
                        st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    # 结果卡片
    if "search_results" in st.session_state and st.session_state.search_results:
        st.markdown("### 搜索结果")
        for i, r in enumerate(st.session_state.search_results, 1):
            st.markdown(f"""
            <div class="stSection" style="padding:1rem 1.25rem">
                <strong style="font-size:1.05rem">{i}. {r.get('title', '无标题')}</strong><br>
                <a href="{r.get('url', '#')}" style="color:#667eea;font-size:0.8rem">{r.get('url', '')[:80]}</a>
                <p style="color:#666;margin-top:0.4rem;font-size:0.9rem">{r.get('snippet', '')[:200]}</p>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════ 职业测评 ═══════════════════
# 三阶段流程: 加载题目 → 逐题作答 → 提交测评 + 展示结果
# 答题进度用 st.progress 可视化，各题答案存储在 session_state[hq_{id}] 中
elif nav == "career":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">🎯 霍兰德职业兴趣测评</p>', unsafe_allow_html=True)
    st.caption("基于 RIASEC 模型的 24 题职业兴趣评估")

    if not st.session_state.holland_questions:
        st.markdown('<div class="stSection" style="text-align:center;padding:3rem">', unsafe_allow_html=True)
        st.markdown("### 🧭 发现你的职业方向")
        st.markdown("霍兰德测评将帮助你找到最适合的职业类型")
        st.markdown("*R (现实型) · I (研究型) · A (艺术型) · S (社会型) · E (企业型) · C (常规型)*")
        if st.button("🚀 开始测评", type="primary", use_container_width=True):
            with st.spinner("加载题目..."):
                try:
                    result = api_get_career_questions()
                    st.session_state.holland_questions = result.get("questions", [])
                    st.session_state.holland_result = None
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    qs = st.session_state.holland_questions
    if qs:
        answered = sum(1 for i in range(len(qs)) if st.session_state.get(f"hq_{i+1}") is not None)
        progress_pct = answered / len(qs) if qs else 0
        st.progress(progress_pct, text=f"📝 答题进度: {answered}/{len(qs)}")

        with st.form("holland_form"):
            for q in qs:
                idx = q["id"]
                opts = q.get("options", ["非常不同意", "不同意", "中立", "同意", "非常同意"])
                st.radio(f"**{idx}. {q['question']}**", options=list(range(len(opts))),
                         format_func=lambda x, opts=opts: opts[x], key=f"hq_{idx}",
                         horizontal=True, index=None)
            if st.form_submit_button("📊 提交测评", type="primary", use_container_width=True):
                answers = [st.session_state.get(f"hq_{i+1}") for i in range(len(qs))]
                if any(a is None for a in answers):
                    st.error("请回答所有题目")
                else:
                    with st.spinner("分析中..."):
                        try:
                            st.session_state.holland_result = api_career_assessment(answers)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    result = st.session_state.holland_result
    if result:
        st.markdown("---")
        st.success("🎉 测评完成！")
        st.markdown(f"""
        <div class="stSection" style="text-align:center;padding:2rem">
            <h1 style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.5rem;margin:0">
                {result.get('type_code', 'N/A')}
            </h1>
            <h3>{result.get('type_name', 'N/A')}</h3>
            <p style="color:#666">{result.get('description', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("#### 💼 推荐职业方向")
        cols = st.columns(len(result.get("recommended_careers", [])) or 1)
        for i, career in enumerate(result.get("recommended_careers", [])):
            with cols[i]:
                _render_tag(career, "blue")


# ═══════════════════ 简历优化 ═══════════════════
elif nav == "tools_resume":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">📄 简历优化</p>', unsafe_allow_html=True)
    st.caption("AI 驱动的简历分析与结构化优化建议")

    # 左右分栏
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="stSection">', unsafe_allow_html=True)
        st.markdown("#### 📝 原始简历")
        txt = st.text_area("粘贴简历内容", height=320, placeholder="在此粘贴你的简历文本...", label_visibility="collapsed")
        optimize_clicked = st.button("🚀 开始优化", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="stSection">', unsafe_allow_html=True)
        st.markdown("#### ✨ 优化建议")
        if optimize_clicked:
            if not txt.strip():
                st.error("请输入简历内容")
            else:
                with st.spinner("AI 分析中..."):
                    try:
                        result = api_resume_optimize(txt)
                        suggestions = result.get("suggestions", [])
                        if suggestions:
                            for i, sug in enumerate(suggestions, 1):
                                with st.expander(f"💡 {i}. {sug.get('category', '建议')}", expanded=(i == 1)):
                                    st.markdown(f"**建议:** {sug.get('suggestion', '')}")
                                    if sug.get('example'):
                                        st.markdown(f"*示例: {sug['example']}*")
                        else:
                            st.info("暂无可优化建议")
                    except Exception as e:
                        st.error(str(e))
        else:
            st.info("👈 在左侧输入简历内容后点击「开始优化」")
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════ 岗位匹配 ═══════════════════
elif nav == "tools_job":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">🔗 岗位匹配分析</p>', unsafe_allow_html=True)
    st.caption("智能评估你的技能与目标岗位的匹配度")

    with st.form("jm_form"):
        col1, col2 = st.columns([1, 1])
        with col1:
            job = st.text_input("🎯 目标岗位", placeholder="如: Python后端开发工程师")
        with col2:
            skills = st.text_area("💪 你的技能 (一行一个)", placeholder="Python\nFastAPI\nMySQL\nDocker", height=100)

        if st.form_submit_button("🔍 开始匹配分析", type="primary", use_container_width=True):
            if not job.strip(): st.error("请输入目标岗位")
            elif not skills.strip(): st.error("请输入你的技能")
            else:
                slist = [s.strip() for s in skills.split("\n") if s.strip()]
                with st.spinner("AI 匹配分析中..."):
                    try:
                        result = api_job_match(job, slist)
                        pct = result.get("match_percentage", 0)
                        matched = result.get("matched_skills", [])
                        missing = result.get("missing_skills", [])

                        # 环形进度 + 技能标签
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
                            ring_css = f"""
                            <div style="width:140px;height:140px;border-radius:50%;
                            background:conic-gradient({color} {pct}%,#eee {pct}%);
                            display:flex;align-items:center;justify-content:center;margin:0 auto;
                            position:relative">
                              <div style="position:absolute;inset:12px;border-radius:50%;background:white;
                              display:flex;align-items:center;justify-content:center;flex-direction:column">
                                <span style="font-size:2rem;font-weight:700;color:{color}">{pct}%</span>
                                <span style="font-size:0.75rem;color:#999">匹配度</span>
                              </div>
                            </div>
                            """
                            st.markdown(ring_css, unsafe_allow_html=True)
                        with c2:
                            st.markdown("#### ✅ 已匹配技能")
                            mcols = st.columns(min(len(matched), 4) or 1)
                            for i, s in enumerate(matched):
                                with mcols[i % len(mcols)]:
                                    _render_tag(s, "green")
                            st.markdown("#### ❌ 待提升技能")
                            mcols2 = st.columns(min(len(missing), 4) or 1)
                            for i, s in enumerate(missing):
                                with mcols2[i % len(mcols2)]:
                                    _render_tag(s, "red")

                        st.markdown("---")
                        st.markdown("#### 📖 学习建议")
                        for s in result.get("learning_suggestions", []):
                            st.markdown(f"<div class='stSection' style='padding:0.75rem 1rem'>📌 {s}</div>", unsafe_allow_html=True)

                    except Exception as e:
                        st.error(str(e))


# ═══════════════════ 面试模拟 ═══════════════════
# 状态机流程:
#   interview_session=None → 岗位输入 + 开始面试
#   interview_session 存在 + interview_done=False → 逐题作答
#   interview_done=True → 展示综合评估报告
elif nav == "tools_interview":
    st.markdown('<p class="stGradientTitle" style="font-size:1.8rem">🎤 面试模拟</p>', unsafe_allow_html=True)
    st.caption("AI 面试官模拟真实面试场景，逐题回答并获取专业反馈")

    if not st.session_state.interview_session:
        st.markdown('<div class="stSection" style="text-align:center;padding:3rem">', unsafe_allow_html=True)
        st.markdown("### 👔 准备开始面试")
        st.markdown("选择你的目标岗位，AI 面试官将进行 5 轮专业面试")
        with st.form("iv_start"):
            job = st.text_input("面试岗位", placeholder="如: 前端开发工程师")
            if st.form_submit_button("🎬 开始面试", type="primary", use_container_width=True):
                if not job.strip(): st.error("请输入面试岗位")
                else:
                    with st.spinner("初始化面试..."):
                        try:
                            d = api_start_interview(job)
                            st.session_state.interview_session = d["session_id"]
                            st.session_state.interview_question = d["question"]
                            st.session_state.interview_q_num = d["question_number"]
                            st.session_state.interview_total = d["total_questions"]
                            st.session_state.interview_feedback = None
                            st.session_state.interview_done = False
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        total = st.session_state.interview_total
        current = st.session_state.interview_q_num
        st.progress(current / total, text=f"📊 面试进度: {current}/{total}")

        if st.session_state.interview_done:
            st.success("🎉 面试已完成！")
            with st.spinner("正在生成综合评估报告..."):
                try:
                    report = api_interview_report(st.session_state.interview_session)
                    st.markdown("## 📋 面试评估报告")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<div class="stSection">', unsafe_allow_html=True)
                        st.markdown("### 💪 优势")
                        for s in report.get("strengths", []):
                            st.markdown(f"- {s}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="stSection">', unsafe_allow_html=True)
                        st.markdown("### 📈 待提升")
                        for s in report.get("improvements", []):
                            st.markdown(f"- {s}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    if report.get("overall_feedback"):
                        st.markdown('<div class="stSection">', unsafe_allow_html=True)
                        st.markdown(f"**📝 综合评价:** {report['overall_feedback']}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    if st.button("🔄 重新开始面试", type="primary", use_container_width=True):
                        st.session_state.interview_session = None
                        st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.markdown(f'<div class="stSection"><strong>📋 第 {current} 题:</strong> {st.session_state.interview_question}</div>', unsafe_allow_html=True)

            if st.session_state.interview_feedback:
                st.markdown(f'<div class="stSection" style="border-left:3px solid #f59e0b"><strong>💬 上题反馈:</strong> {st.session_state.interview_feedback}</div>', unsafe_allow_html=True)

            answer = st.text_area("你的回答", height=150, key="iv_answer", placeholder="在此输入你的回答...")
            if st.button("📤 提交回答", type="primary", key="iv_submit", use_container_width=True):
                if not answer.strip():
                    st.error("请输入回答")
                else:
                    with st.spinner("AI 评估中..."):
                        try:
                            d = api_answer_interview(st.session_state.interview_session, answer)
                            st.session_state.interview_feedback = d.get("feedback", "")
                            st.session_state.pop("iv_answer", None)
                            nq = d.get("next_question")
                            if nq:
                                st.session_state.interview_question = nq
                                st.session_state.interview_q_num = d["question_number"]
                                st.session_state.interview_total = d["total_questions"]
                            else:
                                st.session_state.interview_done = True
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
