# AGENTS.md — 简历技术要点深度解析

> **目标**: 吃透简历上的每一项技术，能结合项目代码对面试官讲清楚"是什么 → 为什么用 → 怎么做的 → 遇到什么困难 → 为什么选它"。

---

## 目录

1. [FastAPI](#1-fastapi)
2. [LangChain → LangGraph (Agent 编排)](#2-langchain--langgraph-agent-编排)
3. [ChromaDB → Milvus (向量数据库)](#3-chromadb--milvus-向量数据库)
4. [BM25 + RRF (混合检索)](#4-bm25--rrf-混合检索)
5. [Redis (会话缓存与状态持久化)](#5-redis-会话缓存与状态持久化)
6. [DeepSeek / 智谱 GLM (LLM)](#6-deepseek--智谱-glm-llm)
7. [OpenTelemetry + Jaeger (全链路追踪)](#7-opentelemetry--jaeger-全链路追踪)
8. [Docker (容器化部署)](#8-docker-容器化部署)
9. [JWT (认证鉴权)](#9-jwt-认证鉴权)
10. [Pydantic (数据校验)](#10-pydantic-数据校验)
11. [Streamlit (前端框架)](#11-streamlit-前端框架)
12. [Asyncio (Python 异步并发)](#12-asyncio-python-异步并发)
13. [MCP (Model Context Protocol)](#13-mcp-model-context-protocol)
14. [SDD (规范驱动开发)](#14-sdd-规范驱动开发)
15. [Agent 熔断机制](#15-agent-熔断机制)

---

## 1. FastAPI

### 1.1 是什么？

FastAPI 是一个现代 Python Web 框架，专为构建高性能 RESTful API 设计。核心特性：基于 Python 类型提示的自动参数校验、自动生成 OpenAPI 文档、原生支持 `async/await`（基于 Starlette）、性能接近 Node.js/Go。

### 1.2 为什么用？在项目中的角色

在双体智能体中，FastAPI 是整个系统的 **入口层和路由层**：

- 承接前端的 HTTP/SSE 流式请求
- 将请求路由到对应的 Service 层处理
- 通过中间件注入认证、CORS、异常处理
- 提供 `/docs` 自动生成的 API 文档，方便前端联调

**项目证据**: [`app/main.py`](file:///d:/桌面/双体系统/双体系统/app/main.py) 中 CORS 中间件 + 9 个路由模块注册。

### 1.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| **SSE 流式响应不稳定**：LLM 生成时间可能超过默认超时 | 使用 `StreamingResponse` + `sse-starlette` 库，设置合理的 `timeout_keep_alive` |
| **异步数据库操作**：SQLite 本身不支持真正的异步 | 用 `aiosqlite` 包装，配合 FastAPI 的 async 路由避免阻塞事件循环 |
| **全局异常处理**：未捕获异常需要统一返回格式 | 自定义 `@app.exception_handler(Exception)` 全局兜底 |

### 1.4 类似技术对比

| 框架 | 优点 | 缺点 | 为什么选 FastAPI |
|------|------|------|-----------------|
| **Flask** | 生态成熟、简单 | 不支持原生 async，需手动参数校验 | Python 异步生态现在是主流，FastAPI 更契合 |
| **Django REST** | 功能全、ORM 强 | 太重，不适合微服务 | 本项目是轻量级 Agent 服务，不需要 Django 全家桶 |
| **Sanic** | 纯异步、性能好 | 生态小、社区不如 FastAPI | FastAPI 的自动文档 + Pydantic 集成是杀手锏 |

---

## 2. LangChain → LangGraph (Agent 编排)

### 2.1 是什么？

**LangChain** 是将 LLM 与外部工具、数据源串联的框架。它的 `AgentExecutor` 提供一个"思考-行动-观察"循环，让 LLM 自主决定调用哪些工具。

**LangGraph** 是 LangChain 团队推出的下一代框架，用 **有向图 (DAG)** 来显式定义 Agent 的执行流。每个节点是一个操作（如调用 LLM、执行工具），边是控制流转条件。

### 2.2 为什么从 LangChain 迁移到 LangGraph？

**在 V1.0 中**，使用 LangChain `AgentExecutor` 构建了完整的 ReAct Agent。业务跑通后，暴露出核心问题：

- LLM 在多步联网搜索中反复调用同一工具，无法识别"已获取足够信息"
- Token 消耗经常超 8K，其中 60% 是无效重试
- `max_iterations=10` 是唯一的止损手段——但第 10 轮可能是第 2 轮就该终止的循环

**根因**：`AgentExecutor` 的控制流完全由 LLM 的 Thought 驱动，开发者无法在中间插入挂载点观察或干预。

**V2.0 重构方案**：用 LangGraph 的 `StateGraph` 替换 AgentExecutor：
- 显式定义状态机 (`AgentState`)，包含 `retry_count`、`consecutive_same_tool`、`token_budget` 等治理字段
- 条件边实现三层熔断：轮次上限、连续重复检测、Token 预算控制
- 每个节点可作为独立 OTel Span 被追踪

**项目证据**: [`app/v2_agent/state.py`](file:///d:/桌面/双体系统/双体系统/app/v2_agent/state.py) 和 [`app/v2_agent/graph.py`](file:///d:/桌面/双体系统/双体系统/app/v2_agent/graph.py)。

### 2.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| AgentExecutor 是黑盒，无法中途干预 | 用 LangGraph 将每个步骤（意图路由→工具调用→结果合成）拆为独立节点 |
| LLM 重复调用同一工具（死循环） | 追踪 `consecutive_same_tool`，连续 ≥3 次熔断并注入终止提示词 |
| 单次调用 Token 不可控 | 累计 `token_used`，超过 8000 Token 强行截断 |

### 2.4 类似技术对比

| 框架 | 控制流 | 适合场景 |
|------|--------|---------|
| **LangChain AgentExecutor** | 隐式 (LLM 驱动) | 简单原型、工具调用少的场景 |
| **LangGraph** | 显式 (DAG 状态机) | 生产级 Agent、需要可观测性和熔断 |
| **AutoGen** | 对话式多 Agent | 多 Agent 协作讨论 |
| **CrewAI** | 角色扮演多 Agent | 团队模拟（产品经理+开发+测试） |

**选 LangGraph 的原因**：它保留了 V1.0 已验证的 ReAct 范式，同时通过显式状态图解决了 Agent 失控的根本问题。不是推翻重来，而是架构升级。

---

## 3. ChromaDB → Milvus (向量数据库)

### 3.1 是什么？

**ChromaDB** 是一个轻量级嵌入式向量数据库，适合原型开发。将文本 Embedding 化后存入，查询时通过向量相似度（余弦/欧氏距离）找到最相关的文档片段。

**Milvus** 是一个分布式向量数据库，支持多种索引算法（HNSW、IVF_FLAT、DiskANN），适合生产级大规模场景。

### 3.2 在项目中的角色

V1.0 使用 ChromaDB 存储学院规章制度、课程信息、FAQ 等文档的向量化片段，支撑 RAG 检索。

V2.0 升级到 Milvus 的原因：当知识库超过 10 万条 chunk 时，ChromaDB 的暴力检索延迟 >800ms，且内存占用超过 2GB。Milvus 的 HNSW 索引可将延迟降至 <50ms。

### 3.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| ChromaDB 大规模检索慢 | 为 V2.0 设计 Milvus 迁移方案，ChromaDB 保留只读备份 |
| 数据迁移时格式不兼容 | 编写数据迁移脚本，批量导出 ChromaDB 的 embedding 并重新导入 Milvus |

### 3.4 类似技术对比

| 数据库 | 优点 | 缺点 | 适用阶段 |
|--------|------|------|---------|
| **ChromaDB** | 零配置、pip install 即用 | 无索引加速、单机 | MVP/原型 |
| **FAISS** | Meta 开源、支持 GPU | 无持久化、需自建服务 | 算法验证 |
| **Milvus** | 分布式、HNSW 索引、生产级 | 部署复杂度高 | 生产环境 |
| **Pinecone** | 全托管、免运维 | 昂贵、数据不本地 | 预算充足的商业项目 |
| **Elasticsearch** | 全文检索+向量检索 | 向量性能不如专用库 | 已有 ES 栈的团队 |

---

## 4. BM25 + RRF (混合检索)

### 4.1 是什么？

**BM25** 是基于 TF-IDF 改进的关键词检索算法。核心公式：

$$Score(d, q) = \sum_{i=1}^{n} IDF(q_i) \cdot \frac{f(q_i, d) \cdot (k_1 + 1)}{f(q_i, d) + k_1 \cdot (1 - b + b \cdot \frac{|d|}{avgdl})}$$

**RRF (Reciprocal Rank Fusion)** 是将多个检索器的排名结果融合为统一分数的算法：

$$Score(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}$$

其中 $k=60$ 是经过多次 TREC 竞赛验证的经验最优值。

### 4.2 为什么用？在项目中的角色

纯向量检索的短板：
- "STP 菁英计划"中"STP"未被 Embedding 模型覆盖，向量表示退化为噪声
- "2023 级培养方案第 8 条"这种精确查询，向量检索 Top-5 命中率只有 61%

**双路召回方案**：
- 向量检索负责语义泛化（"怎么报名" ≈ "申请流程"）
- BM25 负责精确匹配（专有名词、编号）
- RRF 融合两者，精确查询命中率从 61% 提升到 89%

### 4.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| 两路检索分数量纲不同（余弦相似度 vs TF-IDF） | 用 RRF 只关心排名而非绝对分数，天然消解量纲问题 |
| 双路召回结果去重 | 基于 doc_id 构建交集并集，对每条文档按 RRF 公式独立算分 |
| 中文分词对 BM25 的影响 | 使用 jieba 分词构建 BM25 索引 |

### 4.4 为什么不用 Rerank 模型？

完整的检索管道可以是"召回→粗排→精排"。Rerank 模型（如 bge-reranker）做精排效果更好，但会引入额外延迟（+100-200ms）。在 V2.0 阶段，RRF 融合已经将命中率提升到 89-94%，Rerank 作为后续优化项。

---

## 5. Redis (会话缓存与状态持久化)

### 5.1 是什么？

Redis 是一个内存键值数据库，支持丰富的数据结构（String、Hash、List、Set、Sorted Set）。单线程事件循环模型，读写延迟 <1ms。

### 5.2 为什么用？在项目中的角色

在 V1.0 中，会话状态存储在 Python 内存中，服务重启即丢。V2.0 引入 Redis 解决三个问题：

| 用途 | 具体实现 |
|------|---------|
| **Session 持久化** | 用户对话会话存入 Redis，服务重启不丢失 |
| **LangGraph Checkpointer** | LangGraph 原生支持 `RedisSaver`，将 Agent 状态图的中断点存入 Redis，支持断点恢复 |
| **分布式锁** | 多 Worker 场景下防止同一用户并发写入冲突 |

### 5.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| 内存 Session → Redis 迁移 | 利用 LangGraph 原生的 `checkpointer` 参数，只需传 `RedisSaver` 即可 |
| 序列化问题 | LangGraph 内置 Message 序列化，Redis 以二进制存储 JSON |

### 5.4 类似技术对比

| 方案 | 优点 | 缺点 | 为什么选 Redis |
|------|------|------|---------------|
| **内存 (V1.0)** | 零延迟、零配置 | 重启丢失、不可扩展 | 仅适合 MVP |
| **Memcached** | 简单、快 | 数据结构单一、无持久化 | Redis 的 List/Set 更适合消息和会话 |
| **MongoDB** | 文档存储 | 延迟高（ms 级 vs μs 级） | 不适合高频读写的会话场景 |

---

## 6. DeepSeek / 智谱 GLM (LLM)

### 6.1 是什么？

**DeepSeek** 和 **智谱 GLM-4-Flash** 都是国产大语言模型，提供兼容 OpenAI 格式的 Chat Completion API。

| 维度 | DeepSeek | 智谱 GLM-4-Flash |
|------|----------|-----------------|
| 上下文窗口 | 128K | 128K |
| 价格 | 极低（0.001 元/1K tokens） | 免费额度（Flash 模型） |
| Tool Calling | 支持 | 支持 |

### 6.2 为什么用两个？在项目中的角色

- 前端允许用户自由切换模型（`st.segmented_control`）
- 后端通过统一的 `BaseLLM` 抽象类适配不同 API
- DeepSeek 用于需要长上下文推理的场景，智谱用于低成本默认模型

**项目证据**: [`app/llm/`](file:///d:/桌面/双体系统/双体系统/app/llm/) 目录，`deepseek.py` 和 `zhipu.py` 均继承自 `base.py`。

### 6.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| 不同厂商 API 格式不完全兼容 | 通过 `BaseLLM` 抽象基类统一 `chat()` 和 `stream()` 接口 |
| DeepSeek Tool Calling 格式与 OpenAI 有差异 | 在适配层做参数映射和响应格式转换 |
| 流式输出时 Token 实时排版 | SSE 逐 chunk 拼接，用 Streamlit `st.empty()` + `markdown` 实现打字效果 |

---

## 7. OpenTelemetry + Jaeger (全链路追踪)

### 7.1 是什么？

**OpenTelemetry** 是 CNCF 孵化的可观测性标准，统一了 Traces（调用链）、Metrics（指标）、Logs（日志）的采集规范。

**Jaeger** 是 Uber 开源的分布式追踪系统，用于 Trace 数据的存储与可视化。

### 7.2 为什么用？在 V2.0 的角色

V1.0 的调试方式只有 `logger.info()`，完全不知道一次对话请求中：
- LLM 调用了多少次
- 每次向量检索花了多少时间
- 哪个节点是性能瓶颈

V2.0 设计了三层 OTel 埋点：
1. **FastAPI Middleware 层**：自动为每个 HTTP 请求创建 Root Span
2. **LangGraph Node 层**：每个图节点（`intent_router`、`tool_execute`、`synthesize`）作为独立 Child Span
3. **基础设施层**：LLM 调用、Milvus 检索、Redis 读写各自独立追踪

### 7.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| LangGraph 异步节点中 Trace Context 丢失 | 使用 `@trace_node` 装饰器在节点入口手动获取 tracer，确保上下文传递 |
| 追踪开销影响性能 | OTel 使用 `BatchSpanProcessor` 异步批量上报，不阻塞主流程 |

### 7.4 类似技术对比

| 方案 | 优点 | 缺点 | 为什么选 OTel+Jaeger |
|------|------|------|---------------------|
| **print/logging** | 零成本 | 无法关联、无可视化 | 仅 V1.0 MVP 用 |
| **LangSmith** | LangChain 原生 | 商业产品、费用高 | 轻量项目不需要 |
| **OpenTelemetry** | 开源标准、生态最大 | 需要额外部署 Jaeger | **行业标准**，未来换 Grafana Tempo/SigNoz 也兼容 |

---

## 8. Docker (容器化部署)

### 8.1 是什么？

Docker 将应用及其依赖打包为轻量级容器，保证"在我机器上能跑"在任何环境都能跑。

### 8.2 为什么用？

双体智能体涉及 Python 运行时、ChromaDB、Milvus、Redis 等多个依赖，手动配置环境容易出错。Docker 容器化后：
- 一键启动全部服务（docker-compose）
- 局域网多用户访问时环境一致

### 8.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| ChromaDB 在 Docker 中的持久化路径 | 通过 volume 挂载 `data/` 目录 |
| 镜像体积过大 | 使用 python:3.11-slim 基础镜像，多层构建减少层数 |

---

## 9. JWT (认证鉴权)

### 9.1 是什么？

JWT (JSON Web Token) 是一种无状态身份认证机制。用户登录后服务器签发一个 Token（包含用户 ID + 过期时间 + HMAC 签名），后续请求在 HTTP Header 中携带此 Token 验证身份。

### 9.2 在项目中的角色

- 用户注册 (`/api/auth/register`) 和登录 (`/api/auth/login`) 返回 JWT Token
- 前端 `auth.py` 将 Token 存储在 `st.session_state`
- 后端 `dependencies.py` 中的 `get_current_user` 依赖注入函数自动解析 Token 获取用户身份

**项目证据**: [`app/core/security.py`](file:///d:/桌面/双体系统/双体系统/app/core/security.py) 和 [`app/api/auth.py`](file:///d:/桌面/双体系统/双体系统/app/api/auth.py)。

### 9.3 为什么不用 Session Cookie？

Session 需要服务端存储状态，与 V2.0 的无状态 + 水平扩展目标矛盾。JWT 是无状态的，任何 Worker 都能验证 Token。

---

## 10. Pydantic (数据校验)

### 10.1 是什么？

Pydantic 是 Python 的数据校验库，基于类型注解在运行时验证数据结构。核心用法：定义 model 类，自动校验输入类型、范围、格式，不合法时抛出明确错误。

### 10.2 在项目中的角色

- FastAPI 的路由输入参数校验（Request Body 自动映射为 Pydantic Model）
- API 请求/响应的结构化定义
- 配置文件管理 (`pydantic-settings`)

**项目证据**: [`app/models/`](file:///d:/桌面/双体系统/双体系统/app/models/) 目录中所有 dataclass/model 定义，[`app/core/config.py`](file:///d:/桌面/双体系统/双体系统/app/core/config.py) 中的 `Settings` 类。

### 10.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| FastAPI 自动生成的错误信息不够友好 | 自定义 `@app.exception_handler` 捕获 `ValidationError`，返回中文错误提示 |

---

## 11. Streamlit (前端框架)

### 11.1 是什么？

Streamlit 是一个纯 Python 的 Web 应用框架，通过 Python 脚本直接渲染 UI 组件（按钮、输入框、图表），无需写 HTML/CSS/JS。

### 11.2 为什么选它？

- 后端已用 Python，前端也用 Python 减少技术栈跨度
- 团队 5 人中无人熟悉 React/Vue，Streamlit 学习成本极低
- 内部工具/管理后台场景下，Streamlit 开发效率极高（一天就能完成整个对话界面）

### 11.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| Streamlit 每次交互都会重新执行整个脚本 | 用 `st.session_state` 持久化状态 + `st.cache_data` 缓存 API 数据 |
| 不支持 SPA 路由 | 用 `session_state.nav` 自定义状态变量模拟页面切换 |
| 不支持 st.tabs 编程切换 | 用按钮模拟标签页，通过 `session_state.auth_tab` 控制显示 |

### 11.4 类似技术对比

| 框架 | 优点 | 缺点 | 为什么选 Streamlit |
|------|------|------|-------------------|
| **Gradio** | HuggingFace 生态 | 适合模型 demo，不适合管理后台 | Streamlit 的布局组件更丰富 |
| **React** | 业界标准、性能好 | 需要独立前后端、学习成本高 | 团队技能栈限制 |
| **Dash** | Plotly 生态 | 适合数据可视化，不适合对话类应用 | 场景不匹配 |

---

## 12. Asyncio (Python 异步并发)

### 12.1 是什么？

Asyncio 是 Python 3.4+ 内置的异步编程框架，通过 `async/await` 语法在单线程中实现协作式并发。核心是事件循环 (Event Loop)，遇到 I/O 操作自动挂起并切换到其他任务。

### 12.2 在项目中的角色

- FastAPI 的路由处理函数全部是 `async def`
- LLM API 调用是 I/O 密集型，异步避免阻塞事件循环
- 数据库操作使用 `aiosqlite` 异步驱动
- V2.0 中双路检索（Milvus + BM25）可 `asyncio.gather` 并行执行

### 12.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| `passlib` / `bcrypt` 是同步库，会阻塞事件循环 | 用 `asyncio.to_thread` 将 CPU 密集型操作放到线程池执行 |
| ChromaDB 的 Python SDK 是同步的 | V1.0 中用 `run_in_executor` 包装，V2.0 Milvus SDK 原生支持 async |

---

## 13. MCP (Model Context Protocol)

### 13.1 是什么？

MCP 是 Anthropic 提出的开放协议，让 AI 模型能够通过标准化的 Client-Server 架构与外部工具、数据源交互。核心概念：MCP Server 暴露 tools/resources/prompts，MCP Client（如 Claude Desktop、Cursor）调用这些能力。

### 13.2 在 AI-Forge 项目中的角色

AI-Forge 开发了一个 MCP Server 作为代码质量门禁，在 AI 编程 Agent 完成代码生成后，自动调用 Pytest/Ruff 执行验证。未通过验证则阻断流程，强制 AI 修复。

### 13.3 遇到的困难与解决

| 困难 | 解决 |
|------|------|
| AI Agent 倾向于"自我评价"代码质量而非真实测试 | MCP Server 执行真实的 shell 命令，返回 Pytest 客观结果 |
| 长周期开发中上下文丢失 | SQLite 持久化状态机，记录 7 个开发阶段的中间状态 |

### 13.4 类似技术对比

| 协议/方案 | 特点 | MCP 相对优势 |
|----------|------|------------|
| **Function Calling** | LLM 原生支持的函数调用 | MCP 是标准化协议，跨模型通用 |
| **LangChain Tools** | 框架级工具封装 | MCP 是协议级，独立于任何框架 |
| **A2A (Agent-to-Agent)** | Google 的多 Agent 协作协议 | MCP 侧重工具暴露，A2A 侧重 Agent 间通信 |

---

## 14. SDD (规范驱动开发)

### 14.1 是什么？

SDD (Specification-Driven Development) 是一种开发方法论：**先写详细的规范文档，再由 AI 精确实现规范内容**，而不是让 AI 自由发挥。

### 14.2 AI-Forge 中如何使用？

1. 用户用自然语言描述需求
2. AI 通过 OpenAI Structured Output 将其转化为 JSON Schema 格式的结构化 Spec
3. Spec 作为"合同"约束 AI 的代码生成范围
4. 代码生成后通过 MCP 质量门禁验证

### 14.3 为什么有效？

传统 AI 编程的核心问题是**AI 容易偏离原始需求**。SDD 将"需求"固化为程序可解析的 Spec，AI 的每一步产出都必须对照 Spec 验证，从根本上减少需求漂移。

### 14.4 数据成果

- AI 代码首次通过率：**60% → 85%**
- 需求返工轮次：**3-5 轮 → 1 轮**
- 已成功应用于 3 个 AI 项目

---

## 15. Agent 熔断机制

### 15.1 是什么？

熔断器 (Circuit Breaker) 是一种容错设计模式。当系统检测到某种异常反复发生时，自动"断开"该通路，防止级联故障。

在 Agent 场景中，"异常"指的是 LLM 陷入无限循环——反复调用同一个工具但没有任何进展，持续消耗 Token。

### 15.2 三态熔断器设计

```text
                  ┌──────────────┐
                  │   L1: 轮次   │  硬上限 max_steps = 8
                  │   计数器     │  超过 → 强制路由到 Synthesizer
                  └──────┬───────┘
                         │ 未超限
                  ┌──────▼───────┐
                  │  L2: 连续调用 │  同一 Tool 连续 ≥ 3 次
                  │  重复检测器   │  触发 → 注入强制终止提示词
                  └──────┬───────┘
                         │ 未重复
                  ┌──────▼───────┐
                  │ L3: Token 预算│  单次对话总 Token > 8000
                  │   监控器      │  触发 → 截断+总结后退出
                  └──────────────┘
```

### 15.3 实现要点 (代码已在 `app/v2_agent/graph.py` 中)

1. **L1 轮次硬上限**：`step_counter >= max_steps` → 插入强制终止的系统消息
2. **L2 连续重复**：追踪 `last_tool_name` + `consecutive_same_tool`，≥3 次触发熔断
3. **L3 Token 预算**：累计 `token_used`，超过 8000 截断
4. **超时兜底**：`elapsed > 30s` 全局中断

### 15.4 面试加分说明

"这个设计来自**微服务领域的 Circuit Breaker 模式**。我在研究 Hystrix/Resilience4j 后，发现它天然适用于 Agent 场景：Agent 的每次 Tool Call 相当于一次外部服务调用，而 LLM 不具备自我终止能力，所以必须在框架层做熔断——这也是我选择 LangGraph 而非 AgentExecutor 的核心原因之一。"

---

## 面试备忘清单

面试官问"你在这个项目中具体做了什么"时，可以按以下层次回答：

| 层次 | 内容 | 对应章节 |
|------|------|---------|
| 业务层 | 学院 AI 助手解决了什么问题 | README |
| V1.0 工程层 | FastAPI + LangChain + ChromaDB + RAG 全栈 | 1, 2, 3, 11 |
| V2.0 架构层 | 为什么重构？做了什么决策？ | 2, 3, 4, 5, 7 |
| 核心创新 | 三态熔断 + 混合检索 RRF + OTel 全链路 | 15, 4, 7 |
| 独立项目 | AI-Forge: SDD + MCP + 质量门禁 | 13, 14 |
