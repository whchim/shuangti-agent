# 双体智能体系统 (Shuangti Agent)

双体软件精英产业学院智能对话系统 — 从 MVP 验证到生产级架构演进的完整工程实践。

> **当前仓库分支 `master` 开源的是 V1.0 MVP 版本。V2.0 重构正在进行中，详见下方架构演进说明。**

---

## ⚠️ 架构演进说明 (Architecture Evolution)

> [!IMPORTANT]
> **如果你正在阅读这份 README 作为技术评估的一部分，请知悉：**

本仓库当前 `master` 分支开源的 **V1.0 MVP** 版本，是我在项目早期阶段独立完成的业务闭环验证。它已经实现了完整的 RAG 对话、知识库管理、联网搜索与特色工具链路，并已在实际场景中投入使用。

然而，**一个好的工程师不仅能把东西做出来，更能在上线后识别问题并推动架构升级**。V1.0 在生产运行中暴露出了以下核心痛点：

| 痛点 | V1.0 现状 | V2.0 方案 |
|------|----------|----------|
| Agent 黑盒死循环 | LangChain `AgentExecutor` 无显式状态控制 | **LangGraph StateGraph** 显式状态机 + 条件边 |
| 向量检索性能瓶颈 | ChromaDB 嵌入式暴力检索，10万条块 >800ms | **Milvus** 分布式索引 (HNSW/IVF)，目标 <50ms |
| 服务无状态不可扩展 | 内存级 Session，重启即丢失 | **Redis** 会话持久化 + 分布式锁 |
| 全链路黑盒不可观测 | 调试靠 `print()` 看日志 | **OpenTelemetry** 统一 Traces / Metrics / Logs |
| 记忆管理粗糙 | 简单滑动窗口 + 关键词触发 | **Memory Graph** (Working / Episodic / Semantic) |

基于以上分析，我正在 `v2-dev` 分支进行 V2.0 架构重构，技术栈升级为 **LangGraph + Milvus + Redis + OpenTelemetry**。

**👉 面试官请查看 [`docs/v2_architecture.md`](docs/v2_architecture.md)**，其中包含：
- V1.0 → V2.0 的技术选型对比与决策逻辑
- LangGraph 状态机替代 AgentExecutor 的核心代码对照
- 完整的 V2.0 架构设计图与 Trace 链路示例
- 分阶段迁移计划与 FAQ

> 我相信真正有价值的不是"用了什么技术栈"，而是"为什么在这个阶段选择这个技术栈，以及如何从现状平滑演进到目标架构"——这正是 V2.0 重构要回答的核心问题。

---

## 功能特性

- 用户注册/登录（JWT 认证）
- 多轮智能对话，支持历史会话管理
- 知识库 RAG：上传文档（PDF/TXT/MD），混合检索（向量 + BM25）
- 联网搜索：Tavily / Bing 双引擎
- 对话记忆系统：短期记忆（最近 10 轮）+ 长期记忆自动触发检索
- 特色工具：职业测评（霍兰德）、简历优化、岗位匹配、面试模拟
- Streamlit 前端，支持局域网多用户访问

## 项目结构

```
shuangti-agent/
├── app/
│   ├── api/             # FastAPI 路由层
│   ├── core/            # 配置、数据库、安全、依赖注入
│   ├── llm/             # LLM 适配层（智谱 / DeepSeek）
│   ├── models/          # Pydantic 数据模型
│   ├── rag/             # RAG 管道（加载/分割/向量化/检索/编排）
│   ├── search/          # 联网搜索（Tavily / Bing）
│   └── service/         # 业务服务层
├── frontend/
│   ├── app.py           # Streamlit 主页面（智能对话）
│   ├── api_client.py    # API 客户端封装
│   ├── auth.py          # 登录/注册模块
│   └── pages/           # 子页面
│       ├── 01_知识库.py
│       ├── 02_特色工具.py
│       └── 03_设置.py
├── data/                # SQLite / ChromaDB / 上传文档
├── scripts/             # 运维脚本
├── docs/                # 设计文档 + V2.0 架构文档
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填入一个 LLM API Key：

```env
ZHIPU_API_KEY=your_key       # 智谱 API Key
DEEPSEEK_API_KEY=your_key    # DeepSeek API Key（可选）
```

### 3. 启动后端

```bash
python -m app.main
```

后端运行在 `http://localhost:8000`，API 文档：`http://localhost:8000/docs`

### 4. 启动前端

```bash
streamlit run frontend/app.py
```

前端运行在 `http://localhost:8501`

### 5. 局域网访问

```bash
# 后端（默认已监听 0.0.0.0）
python -m app.main

# 前端需显式指定
streamlit run frontend/app.py --server.address 0.0.0.0
```

其他设备通过 `http://<你的IP>:8501` 访问（首次需在防火墙放行 8000 / 8501 端口）。

## 技术栈

| 维度 | 选型 |
|------|------|
| Web 框架 | FastAPI |
| 前端 | Streamlit |
| LLM | 智谱 GLM-4-Flash / DeepSeek |
| Embedding | 智谱 embedding-2 / DeepSeek |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite (aiosqlite) |
| RAG 框架 | LangChain（文本分割） |
| 检索 | 向量检索 + BM25 + RRF 融合 |
| 搜索 | Tavily / Bing |

## API 概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/auth` | 注册、登录、退出 |
| 用户 | `/api/user` | 个人资料管理 |
| 对话 | `/api/chat` | 发送消息、会话管理、SSE 流式 |
| 知识库 | `/api/knowledge` | 文档上传、列表、删除、重建索引 |
| 搜索 | `/api/search` | 联网搜索、搜索配置 |
| 模型 | `/api/model` | LLM 模型切换与配置 |
| 工具 | `/api/tools` | 职业测评、简历优化、岗位匹配、面试模拟 |
| 健康 | `/health` | 服务健康检查 |
