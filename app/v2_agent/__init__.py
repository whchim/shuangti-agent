"""V2.0 Agent 模块 — 基于 LangGraph 的显式状态机编排

迁移路线: langchain.agents.AgentExecutor → langgraph.graph.StateGraph
核心改进: 状态可控 · 条件路由 · 熔断机制 · OTel 可观测
"""

from app.v2_agent.state import AgentState
from app.v2_agent.graph import build_graph

__all__ = ["AgentState", "build_graph"]
