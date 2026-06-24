"""V2.0 Agent 共享状态定义

LangGraph 要求所有节点通过单一的共享状态 (TypedDict) 进行通信。
与 V1.0 AgentExecutor 的关键区别:
  - V1.0: 仅 messages 列表，无结构化状态
  - V2.0: 显式 TypedDict，每个字段可被图节点读写和条件边检查
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """
    LangGraph 共享状态 — 在整个 StateGraph 的所有节点间流转。

    每个节点函数签名为 (state: AgentState) -> dict[str, Any]，
    返回的字典会被浅合并到当前状态中。

    Attributes:
        messages:
            对话消息列表。使用 LangGraph 内置的 add_messages reducer
            作为 Annotated 元数据，确保增量追加而非全量覆盖。

        intent:
            意图路由结果。可选值: "chat" | "rag" | "tool" | "search"。
            由 intent_router 节点写入，条件边读取决定下游分支。
            TODO: 后续对接轻量级 TinyLLM 分类器，替换当前的规则匹配。

        retry_count:
            L1 熔断器: 当前 Agent 循环的累积重试次数。
            在 tool_node 中递增，在 should_continue 中检查。
            默认硬上限 max_retries = 8。
            TODO: 增加指数退避策略，超出 3 次后延长 wait_time。

        max_retries:
            L1 熔断器: 最大允许重试次数。可在运行时按用户/场景动态调整。

        current_tool:
            当前正在执行的工具名称 (str)。
            用于 L2 连续重复检测 —— 如果连续多次相同工具且无进展，
            判定为死循环并熔断。
            TODO: 扩展为 current_tool + tool_input_hash 联合去重。

        consecutive_same_tool:
            L2 熔断器: 同一工具连续调用计数器。
            当 current_tool 与上一轮相同时 +1，不同时重置为 1。
            默认阈值 max_consecutive = 3。

        max_consecutive:
            L2 熔断器: 连续重复阈值。

        token_budget:
            L3 熔断器: 单次对话的总 Token 预算上限。
            默认 8000 tokens (输入+输出合计)。

        token_used:
            L3 熔断器: 当前已消耗的 Token 计数。
            每次 LLM 调用后累加 prompt_tokens + completion_tokens。

        should_exit:
            强制退出标志。三种场景触发:
            1. retry_count >= max_retries (L1)
            2. consecutive_same_tool >= max_consecutive (L2)
            3. token_used >= token_budget (L3)
            TODO: 接入 CircuitState 枚举，区分 CLOSED / HALF_OPEN / OPEN。

        trace_id:
            OpenTelemetry Trace ID (32 位十六进制字符串)。
            由 FastAPI 中间件在请求入口注入，贯穿整个 Agent 执行链。
            用于 Jaeger / Grafana 全链路追踪。
            TODO: 对接 OTel propagator，从 HTTP Header (traceparent) 自动提取。

        session_id:
            会话 ID，对应 Redis/V1.0 SQLite 中的 session 记录。
            用于跨请求状态恢复 (LangGraph checkpointing)。

        user_id:
            当前认证用户 ID。
            用于权限校验、记忆检索、用户画像查询。

        knowledge_context:
            RAG 检索到的知识库文本片段列表。
            由 rag_node 写入，synthesize_node 读取拼入 LLM prompt。
            TODO: 支持多轮检索结果的增量合并与去重。

        tool_results:
            工具调用返回结果的列表，每个元素为 dict:
            {"tool_name": str, "input": dict, "output": str, "success": bool}
            由 tool_node 写入，synthesize_node 聚合展示。
    """

    # ── 核心消息流 ──
    messages: Annotated[list, add_messages]

    # ── 意图路由 ──
    intent: str

    # ── L1 熔断: 轮次计数 ──
    retry_count: int
    max_retries: int

    # ── L2 熔断: 连续重复检测 ──
    current_tool: Optional[str]
    consecutive_same_tool: int
    max_consecutive: int

    # ── L3 熔断: Token 预算 ──
    token_budget: int
    token_used: int

    # ── 终止控制 ──
    should_exit: bool

    # ── 可观测性 ──
    trace_id: str

    # ── 会话与用户 ──
    session_id: str
    user_id: str

    # ── 上下文数据 ──
    knowledge_context: list[str]
    tool_results: list[dict[str, Any]]
