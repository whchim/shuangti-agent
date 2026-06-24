# V2.0 架构设计文档 — 从 MVP 到生产级

> **状态**: 重构中 | **预计里程碑**: V2.0-alpha  
> **关联仓库**: 当前 `master` 分支为 V1.0 MVP，V2.0 开发在 `v2-dev` 分支进行

---

## 一、重构动机：V1.0 暴露的核心痛点

| # | 痛点 | 具体表现 | 根因 |
|---|------|---------|------|
| 1 | **Agent 黑盒死循环** | 复杂多步任务中 LLM 反复调用相同 Tool，无法退出循环 | LangChain `AgentExecutor` 缺少显式状态机控制，`max_iterations` 是唯一止损手段 |
| 2 | **ChromaDB 性能瓶颈** | 知识库 >10万条块时，召回延迟 >800ms，内存占用 2GB+ | ChromaDB 单机嵌入式架构无索引加速，全内存暴力检索 |
| 3 | **多轮记忆不可控** | 长对话中旧信息"污染"新 Query，无法按需激活记忆 | 简单滑动窗口 + 关键词触发，缺乏结构化记忆管理 |
| 4 | **可观测性缺失** | Agent 内部决策过程完全黑盒，调试靠 `print()` | 无 Tracing 标准，无法追踪一次请求的全链路 |
| 5 | **无状态服务局限** | 服务重启丢失会话状态，无法水平扩展 | 内存级 Session，无外部状态存储 |

> 这些不是设计失误，而是 MVP 阶段在"快速验证"与"生产可靠性"之间的合理取舍。  
> V2.0 的目标是在保留 V1.0 已验证业务闭环的前提下，逐项解决上述工程化问题。

---

## 二、V2.0 技术栈升级路线

```
V1.0 (MVP)                         V2.0 (Production)
─────────────────────────────────────────────────────────
LangChain AgentExecutor    ──→    LangGraph StateGraph (显式状态机)
ChromaDB (嵌入式)           ──→    Milvus (分布式向量库 + 索引加速)
内存级 Session              ──→    Redis (会话状态持久化 + 分布式锁)
无 Tracing                  ──→    OpenTelemetry (Traces + Metrics + Logs)
SQLite (aiosqlite)          ──→    PostgreSQL (可选，根据部署规模)
单进程 Uvicorn              ──→    Gunicorn + Uvicorn Workers (多进程)
```

---

## 三、核心架构图

```
                          ┌──────────────────────────────────────┐
                          │           OpenTelemetry              │
                          │   (Traces / Metrics / Logs 统一管道)  │
                          └──────────────┬───────────────────────┘
                                         │ 全链路埋点
┌──────────┐      ┌──────────────────────▼──────────────────────┐
│ Streamlit│      │              FastAPI Gateway                 │
│  Frontend│─────▶│         (Router / Auth / Middleware)         │
└──────────┘      └───┬──────────┬──────────┬───────────────────┘
                      │          │          │
               ┌──────▼──┐ ┌────▼────┐ ┌──▼───────────┐
               │  Redis  │ │ Milvus  │ │  PostgreSQL   │
               │ Session │ │ Vector  │ │  (Metadata)   │
               │  + Lock │ │  Store  │ │               │
               └─────────┘ └─────────┘ └───────────────┘
                      │
         ┌────────────▼────────────────┐
         │       LangGraph Agent       │
         │  ┌──────────────────────┐   │
         │  │   StateGraph (DAG)   │   │
         │  │                      │   │
         │  │  [Intent Router]     │   │
         │  │      │    │    │     │   │
         │  │      ▼    ▼    ▼     │   │
         │  │  [RAG] [Tool] [Chat] │   │
         │  │      │    │    │     │   │
         │  │      ▼    ▼    ▼     │   │
         │  │  [Response Synthesize]│  │
         │  └──────────────────────┘   │
         │    + Conditional Edges      │
         │    + Max Turns Guard        │
         │    + Tool Call Audit        │
         └─────────────────────────────┘
```

---

## 四、核心重构逻辑

### 4.1 Agent 治理：从 Executor 到 StateGraph

```python
# V1.0: 黑盒 AgentExecutor
from langchain.agents import AgentExecutor
executor = AgentExecutor(agent=agent, tools=tools, max_iterations=10)

# V2.0: 显式状态机
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: list
    intent: str
    tool_calls: list
    loop_count: int
    should_continue: bool

graph = StateGraph(AgentState)
graph.add_node("intent_router", route_intent)
graph.add_node("rag_retrieve", do_rag)
graph.add_node("tool_execute", execute_tool)
graph.add_node("synthesize", build_response)

# 条件边：显式控制流转
graph.add_conditional_edges(
    "tool_execute",
    should_loop,           # 自定义判断函数
    {True: "intent_router", False: "synthesize"}
)

# 硬守卫：超过 5 轮强制退出
graph.add_conditional_edges(
    "synthesize",
    lambda s: s["loop_count"] < 5,
    {True: "intent_router", False: END}
)
```

**收益**：Agent 执行路径完全可视化，死循环可检测、可中断、可审计。

### 4.2 向量检索升级：ChromaDB → Milvus

| 维度 | ChromaDB (V1.0) | Milvus (V2.0) |
|------|----------------|----------------|
| 索引类型 | 无 (暴力检索) | IVF_FLAT / HNSW / DiskANN |
| 10万条块延迟 | ~800ms | ~50ms (HNSW) |
| 扩展方式 | 单机 | 分布式 (Proxy + QueryNode + DataNode) |
| 过滤能力 | 基础 metadata filter | 标量索引 + 混合查询 |

### 4.3 记忆系统重构

```
V1.0: Messages Window[−10:] + Keyword Trigger
                        ↓
V2.0: Redis Session Store + Memory Graph
      ├── Working Memory  (最近 N 轮 · Redis List)
      ├── Episodic Memory (关键事件 · 自动摘要存入)
      └── Semantic Memory (用户画像 · 长期偏好)
```

### 4.4 可观测性 (OTel)

```
一次对话请求的 Trace 示例：

Span: POST /api/chat/message         (入口)
  ├── Span: AuthMiddleware           (认证)
  ├── Span: AgentGraph.Execute       (Agent 图执行)
  │   ├── Span: IntentRouter         (意图路由)
  │   ├── Span: Milvus.Search        (向量检索)
  │   ├── Span: Tool.Execute         (工具调用)
  │   └── Span: LLM.Complete         (LLM 生成)
  ├── Span: Redis.Session.Write      (会话持久化)
  └── Span: Response                 (响应)
```

通过 Jaeger / Grafana 即可实时追踪每一次请求的完整调用链。

---

## 五、迁移计划

| 阶段 | 内容 | 分支 |
|------|------|------|
| Phase 1 | LangGraph Agent 核心重构 + 单元测试 | `v2-dev` |
| Phase 2 | Milvus 集成 + 数据迁移脚本 | `v2-dev` |
| Phase 3 | Redis Session + Memory Graph | `v2-dev` |
| Phase 4 | OTel 全链路埋点 + Grafana Dashboard | `v2-dev` |
| Phase 5 | 性能压测 + V1→V2 灰度切换方案 | `v2-dev` |

---

## 六、FAQ

**Q: 为什么不直接在 V1.0 上修修补补？**  
A: V1.0 的 LangChain AgentExecutor 是一个"黑盒"抽象，任何对其内部的 hack 都无法从根本上解决死循环和不可观测的问题。LangGraph 提供的显式 StateGraph 才是正确的架构范式——它让 Agent 的执行流从"隐式"变为"显式"，这是本质区别。

**Q: Milvus 比 ChromaDB 重很多，值得吗？**  
A: 当知识库规模 <1 万条块时，ChromaDB 足够。但我们的目标场景包含学院多年积累的教学文档、FAQ、政策文件，预计 10 万~50 万条块。在这个量级，Milvus 的索引加速（HNSW/IVF）和分布式扩展能力是必需品，而非奢侈品。

**Q: V1.0 还有维护价值吗？**  
A: 有。V1.0 是业务闭环的"概念验证"，它证明了 RAG + 工具调用的产品形态是成立的。V2.0 的所有功能设计都继承自 V1.0 的业务洞察。
