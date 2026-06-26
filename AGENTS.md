# AGENTS.md — 双体智能体系统 AI 协作规则

> **版本**: 1.0.0 | **最后更新**: 2026-06-26 | **维护者**: shuangti-agent 项目组
>
> 本文档定义了 AI Agent（如 Cursor / Claude / Copilot）在本项目中协作时必须遵守的规则、约定和约束。所有 AI 生成的代码在提交前必须通过本文档的合规性自查。

---

## 目录

1. [项目概览](#1-项目概览)
2. [代码规范](#2-代码规范)
3. [架构约束](#3-架构约束)
4. [技术栈说明](#4-技术栈说明)
5. [开发流程](#5-开发流程)

---

## 1. 项目概览

### 1.1 项目定位

「双体智能体系统」是为**双体软件精英产业学院**打造的垂直领域智能对话系统，提供以下核心能力：

- **智能对话**: 基于 RAG 增强的多轮对话，支持 SSE 流式输出
- **知识库管理**: 上传 PDF/TXT/MD 文档构建内部知识库，支持网页抓取入库
- **联网搜索**: Tavily 实时搜索
- **对话记忆**: 短期记忆（最近10轮）+ 长期记忆（向量相似度自动触发）
- **特色工具**: 霍兰德职业测评、简历优化、岗位匹配、面试模拟

### 1.2 项目结构

```
shuangti-agent/
├── app/                        # 后端核心
│   ├── main.py                 # FastAPI 入口 + 生命周期 + 全局异常处理
│   ├── core/                   # 配置 / 数据库 / 安全 / 依赖注入
│   │   ├── config.py           # pydantic-settings, 从 .env 自动加载
│   │   ├── database.py         # aiosqlite 连接管理 + 表初始化 + 迁移
│   │   ├── security.py         # JWT 签发/验证 + bcrypt 密码哈希
│   │   └── dependencies.py     # FastAPI Depends: get_current_user / get_optional_user
│   ├── api/                    # REST 路由层 (薄层, 不写业务逻辑)
│   ├── service/                # 业务服务层 (核心逻辑所在)
│   ├── llm/                    # LLM 适配层 (BaseLLM → DeepSeek / Zhipu)
│   ├── rag/                    # RAG 管道 (loader → splitter → embeddings → store → retriever → chain)
│   ├── search/                 # 联网搜索 (Tavily)
│   ├── models/                 # Pydantic 请求/响应模型
│   └── v2_agent/               # [规划中] V2.0 Agent (LangGraph StateGraph)
├── frontend/                   # Streamlit 前端
│   ├── app.py                  # 主界面 + 7个路由页面
│   ├── auth.py                 # 登录/注册/用户菜单
│   └── api_client.py           # API 客户端封装
├── data/                       # 运行时数据 (不提交)
│   ├── chroma/                 # ChromaDB 持久化
│   ├── documents/              # 上传的原始文件
│   └── sqlite/                 # SQLite 数据库
├── scripts/                    # 运维脚本 (初始化/重新索引)
├── docs/                       # 设计文档
│   └── v2_architecture.md      # V2.0 架构设计文档
├── logs/                       # 运行日志 (不提交)
├── .env.example                # 环境变量模板
├── requirements.txt            # Python 依赖
└── README.md                   # 项目说明
```

### 1.3 核心对话流程

```
用户消息
  → app/api/chat.py (路由层, 选择同步/流式)
  → app/service/chat_service.py::process_chat()
      → 获取/创建会话 (SQLite)
      → 保存用户消息 + 向量化 (ChromaDB)
      → M01: 短期记忆加载 (最近10轮)
      → M02: 长期记忆触发 (第12轮起, 余弦相似度匹配)
      → RAG 检索 / 联网搜索 (根据 search_mode)
      → Prompt 组装 (chain.py: 系统提示词 + 记忆 + 检索结果 + 用户问题)
      → LLM 生成 (DeepSeek / Zhipu)
      → 保存助手回复 (SQLite)
      → 返回 {session_id, answer, sources, web_sources}
```

---

## 2. 代码规范

### 2.1 Python 风格

- **PEP 8** 为基准，使用 4 空格缩进
- 所有函数和类必须有 **Docstring**（Google 风格或 numpy 风格均可）
- 类型注解：所有函数参数和返回值必须标注类型

```python
# ✅ 推荐
async def process_chat(
    user_id: str,
    request: ChatRequest,
    llm: BaseLLM,
) -> dict[str, Any]:
    """处理对话的核心流水线。

    Args:
        user_id: 当前用户ID
        request: 对话请求，包含 message / model / search_mode
        llm: LLM 适配器实例

    Returns:
        dict 包含 session_id, answer, sources, web_sources
    """
    ...

# ❌ 避免
def process_chat(user_id, request, llm):
    ...
```

### 2.2 命名约定

| 类别 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写下划线 | `chat_service.py` |
| 类 | 大驼峰 | `DeepSeekAdapter`, `BM25Retriever` |
| 函数/方法 | 小写下划线 | `process_chat`, `build_prompt` |
| 常量 | 大写下划线 | `MAX_SHORT_TERM_ROUNDS = 10` |
| 私有函数 | 前导下划线 | `_tokenize`, `_build_index` |
| 模块级变量 | 小写下划线 | `settings`, `logger` |

### 2.3 异步编程规范

```python
# ✅ 异步函数调用必须加 await
result = await process_chat(user_id, request, llm)

# ✅ 同步阻塞操作必须用 asyncio.to_thread 包装
response = await asyncio.to_thread(
    self.client.chat.completions.create,
    model="deepseek-chat",
    messages=messages,
)

# ❌ 禁止在 async 函数中直接调用同步阻塞函数
response = requests.get(url)  # 会阻塞整个事件循环!

# ✅ 并行无依赖的 I/O 操作用 asyncio.gather
vector_results, bm25_results = await asyncio.gather(
    _vector_search(query, collection, top_k),
    _bm25_search(query, bm25_index, corpus, top_k),
)
```

### 2.4 导入顺序

```python
# 1. 标准库
import asyncio
from typing import Optional

# 2. 第三方库
import aiosqlite
from fastapi import FastAPI

# 3. 项目内部模块 (绝对路径)
from app.core.config import settings
from app.llm.base import BaseLLM
```

### 2.5 日志规范

```python
from loguru import logger

# 使用 Loguru 而非标准 logging
logger.info(f"用户 {user_id} 发起对话, session={session_id}")
logger.warning(f"Token 预算接近上限: {token_used}/{token_budget}")
logger.error(f"LLM 调用失败: {exc}", exc_info=True)
logger.debug(f"检索耗时: {duration}ms, 命中: {len(results)}")
```

### 2.6 错误处理

```python
# ✅ 业务层显式 raise ValueError (由全局异常处理器统一捕获)
if not row:
    raise ValueError(f"用户不存在: {username}")

# ✅ API 层信任 service 层, 不做冗余 try/except
@app.post("/api/auth/login")
async def login(req: LoginRequest):
    result = await login_user(req.username, req.password)
    return result
    # 异常由 app/main.py 的 global_exception_handler 统一处理

# ❌ 避免在 API 层吃掉异常
try:
    result = await service.do_something()
except Exception as e:
    logger.error(e)   # 吞了异常, 调用方收不到错误信息
    return {"error": "..."}
```

### 2.7 数据库操作

```python
# ✅ 始终通过 get_db() 获取单例连接
from app.core.database import get_db

async def some_query():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row:
        return dict(row)  # aiosqlite.Row 支持 dict() 转换
    return None
```

---

## 3. 架构约束

### 3.1 分层原则 (严格自上而下)

```
API 路由层 (app/api/)      ← 薄层, 仅做参数接收和路由转发
     ↓ 调用 (单向)
业务服务层 (app/service/)  ← 核心逻辑所在, 所有业务规则在此
     ↓ 调用 (单向)
基础设施层 (app/llm/ app/rag/ app/search/ app/core/)
```

**关键约束**:
- **API 层不写业务逻辑**: 所有 if/else 判断、数据转换、编排逻辑必须在 service 层
- **Service 层不直接操作 HTTP**: 返回 dict/Pydantic 对象而非 Response
- **禁止跨层调用**: API 层不能直接调 `app/rag/` 或 `app/llm/` 中的函数
- **禁止反向依赖**: 基础设施层不能 import service 层

### 3.2 API 设计规范

- 所有端点前缀: `/api/{module}/`
- 认证端点: `POST/PUT` 操作必须在 `Depends(get_current_user)` 之后
- 请求/响应使用 Pydantic 模型, 不在路由中手写 dict
- SSE 流式接口设置 `X-Accel-Buffering: no` 头

### 3.3 状态管理

- **V1.0**: 会话状态从前端 `st.session_state` 管理, 后端无状态
- **V2.0 规划**: 引入 Redis 统一管理 session + LangGraph checkpointer
- 任何状态修改必须通过显式的 API 调用, 不假设前端状态

### 3.4 安全约束

- 密码必须通过 bcrypt 哈希存储, 禁止明文或弱哈希
- JWT 密钥必须从环境变量读取, 禁止硬编码
- SQL 查询必须使用参数化查询 (`?` 占位符), 禁止字符串拼接
- API Key 在前端展示时必须脱敏（后端已在 `model_config` 中返回 `*_available: bool` 标志位）

### 3.5 性能约束

- 单次 API 请求 (非流式) 应在 **3 秒内**返回 (不包括 LLM 生成时间)
- ChromaDB 检索延迟应 < **200ms** (MVP 阶段可接受)
- 文件上传限制: **10MB** (前端 + 后端双重校验)
- 批量向量化时: 25 条/批, 间隔 1 秒 (百炼 API 限流)

### 3.6 V1.0 → V2.0 约束

- **master 分支是 V1.0 MVP**: 所有运行中的功能必须保持稳定
- **v2-dev 分支是 V2.0 开发**: 新架构代码放此分支
- **V2.0 不能删除 V1.0 代码**: V2.0 验收前 V1.0 仍对外提供服务
- **V2.0 可复用 V1.0 的业务逻辑代码**: app/rag/ app/search/ app/llm/ 中的工具代码保持不变, 只替换编排层

---

## 4. 技术栈说明

### 4.1 当前技术栈 (V1.0 MVP)

| 维度 | 选型 | 版本 | 用途 |
|------|------|------|------|
| **Web 框架** | FastAPI | 0.115.0 | RESTful API 骨架 |
| **ASGI 服务器** | Uvicorn | 0.30.6 | 运行 FastAPI 应用 |
| **前端** | Streamlit | 1.40.0 | 纯 Python Web 界面 |
| **异步数据库驱动** | aiosqlite | 0.20.0 | SQLite 异步操作 |
| **向量数据库** | ChromaDB | 0.5.5 | 嵌入向量存储与检索 |
| **LLM** | DeepSeek | — | 对话生成 |
| **LLM SDK** | OpenAI SDK | 1.47.0 | API 调用 |
| **Embedding** | 阿里百炼 text-embedding-v4 | 1024维 | 文本向量化 |
| **Embedding SDK** | dashscope | 1.21.0 | 百炼 API 调用 |
| **认证** | python-jose + passlib[bcrypt] | 3.3.0 / 1.7.4 | JWT + 密码哈希 |
| **文本分割** | LangChain | 0.3.0 | RecursiveCharacterTextSplitter |
| **BM25** | rank-bm25 | 0.2.2 | 关键词检索 (手动实现) |
| **文档解析** | pypdf2 / python-docx | 3.0.1 / 1.1.2 | PDF/Word 解析 |
| **网页抓取** | httpx + BeautifulSoup4 | 0.27.2 / 4.12.3 | URL 内容提取 |
| **SSE 流式** | sse-starlette | 2.1.3 | Server-Sent Events |
| **日志** | Loguru | 0.7.2 | 结构化日志 |
| **配置管理** | pydantic-settings | 2.5.0 | .env 自动加载 |
| **HTTP 客户端** | requests + httpx | 2.32.0 / 0.27.2 | API 调用 |

### 4.2 V2.0 规划技术栈

| 维度 | V1.0 | V2.0 |
|------|------|------|
| **Agent 编排** | 手动线性编排 (process_chat) | LangGraph StateGraph |
| **向量数据库** | ChromaDB | Milvus (HNSW 索引) |
| **会话持久化** | 仅内存/SQLite | Redis + RedisSaver |
| **可观测性** | Loguru 日志 | OpenTelemetry + Jaeger |
| **数据库** | SQLite | PostgreSQL (可选) |
| **部署模式** | 单进程 Uvicorn | Gunicorn + Uvicorn Workers |

### 4.3 禁止引入

以下技术在项目当前阶段**明确禁止引入** (避免过度工程化):
- ❌ ORM (SQLAlchemy/Tortoise): 直接 SQL 更可控, SQLite 场景不需要
- ❌ GraphQL: RESTful API 已满足需求
- ❌ Kubernetes: Docker Compose 已够用
- ❌ 微服务拆分: 当前单体架构对学院场景完全足够
- ❌ Redis/PostgreSQL (V1.0 阶段): MVP 阶段增加运维负担

---

## 5. 开发流程

### 5.1 分支策略

```
master (V1.0 稳定版)
  ├── v2-dev (V2.0 重构分支)
  ├── feat/xxx (功能分支, 合并到 master)
  └── fix/xxx (修复分支, 合并到 master)
```

**规则**:
- `master` 分支永远可部署, 禁止直接 push
- 新功能开发: `master` → `feat/xxx` → PR → code review → `master`
- V2.0 重构: `master` → `v2-dev` (长期分支, 阶段性合并回 master)
- Bug 修复: `master` → `fix/xxx` → PR → `master`

### 5.2 提交规范

使用 **Conventional Commits** 格式:

```
<type>: <简短描述>

[可选详细说明]

类型 (type):
  feat:     新功能
  fix:      Bug 修复
  docs:     文档变更
  style:    代码格式 (不影响功能)
  refactor: 重构 (不改变功能)
  perf:     性能优化
  test:     测试相关
  chore:    构建/工具/依赖变更
```

示例:
```
feat: 新增 URL 网页抓取入库功能

支持通过 /api/knowledge/url 端点提交网页链接,
后端使用 httpx + BeautifulSoup 抓取正文后自动向量化入库。
```

### 5.3 环境配置

```bash
# 1. 克隆仓库
git clone https://github.com/whchim/shuangti-agent
cd shuangti-agent

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env, 至少填入:
#   DEEPSEEK_API_KEY=xxx     (DeepSeek)
#   BAILIAN_API_KEY=xxx      (百炼Embedding)

# 5. 初始化数据库
python scripts/init_db.py

# 6. 启动后端 (终端1)
python -m app.main
# → http://localhost:8000
# → http://localhost:8000/docs (API文档)

# 7. 启动前端 (终端2)
streamlit run frontend/app.py
# → http://localhost:8501
```

### 5.4 开发调试

- **后端热重载**: `python -m app.main` 默认开启 reload (debug=true)
- **API 文档调试**: 浏览器打开 `http://localhost:8000/docs` 直接交互式调用
- **数据库查看**: 用任何 SQLite 客户端打开 `data/sqlite/shuangti.db`
- **日志位置**: stdout (实时) + `logs/app_YYYY-MM-DD.log` (持久化, 保留30天)
- **向量库调试**: ChromaDB 数据在 `data/chroma/`, 可直接用 ChromaDB 客户端连接

### 5.5 测试要求 (AI 生成代码必须遵守)

AI 生成的新代码在提交前必须通过以下检查:

1. **语法检查**: `python -c "import ast; ast.parse(open('文件路径').read())"`
2. **导入检查**: 确保所有 import 路径正确 (使用项目绝对路径 `from app.xxx import ...`)
3. **异步检查**: 确保 async 函数中的 I/O 操作都有 `await` 或 `asyncio.to_thread`
4. **类型检查**: 确保所有函数有类型注解
5. **文档检查**: 确保所有新函数/类有 Docstring

### 5.6 添加新 API 端点的步骤

```python
# Step 1: 在 app/models/ 定义 Pydantic 模型
class NewFeatureRequest(BaseModel):
    param1: str
    param2: int = 10

class NewFeatureResponse(BaseModel):
    result: str
    status: str

# Step 2: 在 app/service/ 实现业务逻辑
async def process_new_feature(user_id: str, request: NewFeatureRequest) -> dict:
    """业务逻辑"""
    ...

# Step 3: 在 app/api/ 定义路由
@router.post("/new-feature")
async def new_feature(
    request: NewFeatureRequest,
    user: dict = Depends(get_current_user),
):
    result = await process_new_feature(user["user_id"], request)
    return result

# Step 4: 在 app/main.py 注册路由
from app.api import new_feature
app.include_router(new_feature.router)

# Step 5: 在 frontend/api_client.py 添加前端调用函数
def api_new_feature(param1: str, param2: int = 10) -> dict:
    """调用新功能 API"""
    ...
```

### 5.7 修改记录规则

**每次代码修改必须在 `docs/record/` 目录下创建修改记录文件。**

- 文件名格式: `YYYY-MM-序号-DD-修改问题简述.md`
- 序号为两位数字（01, 02, 03...），按修改时间先后递增，置于月份与日期之间
- 问题简述不超过 **10个字**
- 文件内容自由描述本次修改的内容、原因和影响范围

示例:
```
docs/record/
  ├── 2026-06-01-26-移除注册邮箱字段.md
  ├── 2026-06-02-26-修正吉祥物图片路径.md
  └── 2026-06-03-26-个人中心优化.md
```

---

> **本文档会持续更新。每次对架构/规范/流程做出重大决策后, 必须同步更新此文档。**
>
> **AI Agent 注意**: 你生成的每一行代码都应该能通过本文档定义的每一条规则。如果某条规则在当前场景下不适用, 在代码注释中说明原因。
