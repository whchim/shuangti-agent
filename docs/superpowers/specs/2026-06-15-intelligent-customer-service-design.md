# 双体智能体系统 — 后端设计文档

**日期：** 2026-06-15（修订于 2026-06-17）
**负责人：** 何豫东 - 后端开发
**状态：** 已确认（根据需求规格说明书 v2.0 修订）

---

## 1. 项目概述

为双体软件精英产业学院搭建智能对话系统后端，基于 Python + FastAPI + LangChain，实现以下核心能力：

1. 用户注册、登录、个人中心管理
2. 多轮智能对话，支持历史会话管理、Markdown 渲染、流式输出（SSE）
3. 基于专用知识库的检索增强生成（RAG），召回准确率 Hit@1 ≥ 85%
4. 实时联网搜索（Tavily / Bing），融合外部信息
5. 对话记忆超过阈值后自动触发历史检索
6. 特色工具：职业测评、简历优化、岗位匹配、面试模拟

系统采用前后端分离架构，通过调用外部 LLM API、Embedding API 及搜索 API 实现智能能力。

---

## 2. 技术选型

| 维度 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步、自动生成 OpenAPI 文档 |
| RAG 框架 | LangChain | 生态成熟、组件丰富 |
| LLM | 智谱 GLM + DeepSeek 双模型 | 可切换的中文大模型 |
| 向量数据库 | ChromaDB | 轻量零部署、适合快速起步 |
| 关系数据库 | SQLite（开发）/ PostgreSQL（生产） | SQLite 轻量开发，生产环境按需迁移 PostgreSQL |
| Embedding | 与 LLM 配套的 Embedding 模型（1536 维） | 智谱 embedding-2 / DeepSeek embedding |
| 联网搜索 | Tavily Search API / Bing Web Search API | 实时联网搜索能力 |
| 流式输出 | SSE (Server-Sent Events) | 长响应流式输出 |
| 密码加密 | bcrypt (cost factor = 10) | 安全存储用户密码 |

---

## 3. 项目结构

```
shuangti-Agent/
├── app/
│   ├── api/                    # FastAPI 路由层
│   │   ├── __init__.py
│   │   ├── auth.py             # 用户认证接口 /api/auth
│   │   ├── user.py             # 用户管理接口 /api/user
│   │   ├── chat.py             # 对话接口 /api/chat
│   │   ├── knowledge.py        # 知识库管理接口 /api/knowledge
│   │   ├── search.py           # 联网搜索接口 /api/search
│   │   ├── model.py            # 模型配置接口 /api/model
│   │   ├── memory.py           # 记忆管理接口 /api/memory (M03)
│   │   ├── tools.py            # 特色工具接口 /api/tools
│   │   └── health.py           # 健康检查接口 /health
│   ├── core/                   # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理（环境变量、模型配置）
│   │   ├── database.py         # 数据库初始化与连接
│   │   ├── security.py         # 安全模块（JWT、bcrypt、权限校验）
│   │   └── dependencies.py     # FastAPI 依赖注入（含用户认证依赖）
│   ├── llm/                    # LLM 适配层
│   │   ├── __init__.py
│   │   ├── base.py             # 统一接口抽象
│   │   ├── zhipu.py            # 智谱 GLM 适配器
│   │   └── deepseek.py         # DeepSeek 适配器
│   ├── rag/                    # RAG 核心管道
│   │   ├── __init__.py
│   │   ├── loader.py           # 文档加载器（PDF/TXT/MD）
│   │   ├── splitter.py         # 文档分割策略
│   │   ├── embeddings.py       # 向量化（Embedding）
│   │   ├── store.py            # ChromaDB 向量存储
│   │   ├── retriever.py        # 检索器（混合检索：向量 + BM25）
│   │   └── chain.py            # RAG 链（检索 + 生成 + Prompt 组装）
│   ├── search/                 # 联网搜索模块
│   │   ├── __init__.py
│   │   ├── tavily_search.py    # Tavily Search API 适配器
│   │   └── bing_search.py      # Bing Web Search API 适配器
│   ├── service/                # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py     # 用户认证服务
│   │   ├── chat_service.py     # 对话服务（多轮记忆管理 M01/M02）
│   │   ├── knowledge_service.py # 知识库管理服务
│   │   ├── search_service.py   # 联网搜索服务
│   │   └── tools_service.py    # 特色工具服务
│   ├── models/                 # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户相关模型
│   │   ├── chat.py             # 对话请求/响应模型
│   │   ├── knowledge.py        # 知识库相关模型
│   │   ├── search.py           # 搜索相关模型
│   │   ├── model_config.py     # 模型配置模型
│   │   ├── memory.py           # 记忆相关模型
│   │   └── tools.py            # 工具相关模型
│   └── main.py                 # FastAPI 应用入口
├── data/                       # 数据目录
│   ├── documents/              # 上传的原始文档
│   ├── chroma/                 # ChromaDB 持久化目录
│   └── sqlite/                 # SQLite 数据库文件
├── scripts/                    # 运维脚本
│   ├── init_db.py              # 数据库初始化
│   ├── load_knowledge.py       # 知识库初始导入
│   └── reindex_knowledge.py    # 知识库重建索引
├── requirements.txt
├── .env.example                # 环境变量模板
└── README.md
```

---

## 4. API 接口设计

### 4.1 用户认证接口 `/api/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录，返回 JWT token |
| `POST` | `/api/auth/logout` | 退出登录（token 加入黑名单，可选） |

**POST `/api/auth/register` 请求体：**

```json
{
  "username": "zhangsan",
  "password": "Abc123456!",
  "email": "zhangsan@example.com"
}
```

**POST `/api/auth/login` 响应体：**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "id": "uuid-xxx", "username": "zhangsan", "email": "zhangsan@example.com" }
}
```

### 4.2 用户管理接口 `/api/user`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/user/profile` | 获取当前用户资料 |
| `PUT` | `/api/user/profile` | 更新个人资料 |

### 4.3 对话接口 `/api/chat`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/chat/send` | 发送消息，返回 AI 回复（支持 SSE 流式） |
| `POST` | `/api/chat/send/stream` | 发送消息，SSE 流式返回 AI 回复 |
| `GET` | `/api/chat/sessions` | 获取当前用户的会话列表（按更新时间倒序） |
| `GET` | `/api/chat/sessions/{id}` | 获取某个会话的历史消息（分页，每页 20 条） |
| `DELETE` | `/api/chat/sessions/{id}` | 删除一个会话 |
| `POST` | `/api/chat/sessions` | 创建新会话 |

**POST `/api/chat/send` 请求体：**

```json
{
  "session_id": "uuid-xxx",
  "message": "计算机科学专业的培养方案是什么？",
  "model": "zhipu",
  "knowledge_base_ids": ["kb1"],
  "search_mode": "knowledge_base"
}
```

`search_mode` 取值：
- `knowledge_base` — 仅知识库
- `web_search` — 仅联网搜索
- `hybrid` — 混合（优先知识库，Top-1 相似度低于 0.7 则触发联网搜索）

**POST `/api/chat/send` 响应体：**

```json
{
  "session_id": "uuid-xxx",
  "answer": "计算机科学专业的培养方案包括...",
  "sources": [
    { "doc_name": "培养方案.pdf", "chunk": "...引用片段...", "page": 3 }
  ],
  "web_sources": [
    { "title": "计算机科学培养方案-某某大学", "url": "https://...", "snippet": "..." }
  ],
  "created_at": "2026-06-15T10:30:00Z"
}
```

### 4.4 知识库管理接口 `/api/knowledge`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/knowledge/upload` | 上传文档到知识库（单文件 ≤ 10MB，总数 ≤ 100） |
| `GET` | `/api/knowledge/documents` | 获取知识库文档列表 |
| `DELETE` | `/api/knowledge/documents/{id}` | 删除指定文档 |
| `POST` | `/api/knowledge/reload` | 重新向量化全部文档（异步任务） |

### 4.5 联网搜索接口 `/api/search`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/search/query` | 执行联网搜索（独立调用，不经过对话） |
| `GET` | `/api/search/config` | 查看搜索配置（当前使用的搜索引擎、API Key 状态） |
| `PUT` | `/api/search/config` | 更新搜索配置 |

### 4.6 模型配置接口 `/api/model`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/model/config` | 查看当前模型配置 |
| `PUT` | `/api/model/config` | 切换模型 / 更新 API Key |

### 4.7 记忆管理接口 `/api/memory` (M03)

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/memory/facts?user_id=xxx` | 获取用户长期记忆关键事实 |
| `DELETE` | `/api/memory/facts/{id}` | 手动删除某条关键事实 |

### 4.8 特色工具接口 `/api/tools`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/tools/career-assessment` | 提交职业测评答案，获取分析结果 |
| `GET` | `/api/tools/career-assessment/questions` | 获取职业测评问卷（霍兰德 24 题） |
| `POST` | `/api/tools/resume-optimize` | 上传简历文本/文件，获取优化建议 |
| `POST` | `/api/tools/job-match` | 岗位匹配分析 |
| `POST` | `/api/tools/interview-simulator` | 开始面试模拟 |
| `POST` | `/api/tools/interview-simulator/answer` | 提交面试回答，获取下一题反馈 |
| `POST` | `/api/tools/interview-simulator/report` | 结束面试，生成评估报告 |

### 4.9 健康检查 `/health`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查，返回服务状态、数据库连接、向量库状态 |

---

## 5. 用户管理模块

### 5.1 注册流程

```
用户提交用户名、密码、邮箱 → 校验格式与唯一性 → bcrypt 哈希密码
→ 创建 user 记录 → 返回用户信息（不含密码）
```

### 5.2 登录流程

```
用户提交用户名、密码 → 查询 user 表 → bcrypt 验证密码 → 生成 JWT token
→ 返回 token + 用户信息
```

### 5.3 认证与鉴权

- 所有 `/api/chat`、`/api/user`、`/api/memory`、`/api/tools` 接口需携带 `Authorization: Bearer <token>` 请求头
- FastAPI 中间件 / 依赖注入统一校验 token
- 所有对话查询必须带 `user_id` 条件，防止水平越权

---

## 6. 记忆系统设计

### 6.1 M01 — 短期记忆

- 同一会话内，系统保留最近 **10 轮**（用户 + 助手）完整消息作为上下文直接注入 Prompt
- 10 轮之前的历史消息不再放入 Prompt，仅存储于数据库 `messages` 表
- `messages` 表存储全部消息，每条包含 `session_id`、`user_id`、`role`、`content`、`round_number`、`vector_embedding`
- 用户消息存储 vector_embedding，用于 M02 历史记忆检索

### 6.2 M02 — 长期记忆触发检索

**触发条件：** 当前会话总轮次 ≥ 12 轮时，在用户发送新问题后执行

**检索逻辑：**
1. 将用户当前问题生成向量（调用 Embedding 模型）
2. 在当前会话的 `messages` 表 `role = "user"` 的消息中进行向量检索
3. 召回 Top-3 最相关的历史消息片段（包括用户问题及其对应的助手关键回复）
4. 将这些片段作为"回忆上下文"注入 Prompt，标记为 `[历史相关对话片段]`

**冷却机制：** 首次触发于轮次 ≥ 12，之后每 5 轮触发一次（即第 12、17、22、27... 轮触发）。触发计数记录在 `sessions` 表的 `trigger_count` 字段中。未达触发轮次时，沿用上一次的检索结果（若有）。

**向量检索实现：** SQLite 不原生支持向量检索。M02 检索范围限定在当前 session 的用户消息（通常不超过数百条），因此采用**内存余弦相似度计算**：从 `messages` 表加载当前 session 所有 `role=user` 的消息向量到内存，计算余弦相似度，取 Top-3。数据量小时性能足够，避免引入额外的向量数据库 collection。

### 6.3 M03 — 记忆可视化

- 在会话结束时，调用 LLM 从完整对话中抽取关键事实
- 关键事实存入 `long_term_memories` 表
- 提供接口查询和手动删除关键事实
- 关键事实在新会话开始时作为用户画像注入 System Prompt

---

## 7. RAG Pipeline 设计

### 7.1 整体流程

```
用户提问 → 短期记忆组装(M01) → 长期记忆触发检查(M02)
→ 根据 search_mode 分支：知识库检索 / 联网搜索 / 混合（知识库优先，相似度不足时补联网）
→ 混合检索(向量+BM25) → RRF 混合排序 → Top-5 文档
→ Prompt 组装 → LLM 生成 → 返回答案（含来源引用）
```

### 7.2 文档处理（入库）

```
上传文档 → 格式解析(PDF/TXT/MD) → 文本清洗 → 智能分割 → Embedding → ChromaDB
```

- 单文件限制 ≤ 10MB，初期总文档数 ≤ 100
- 知识库支持动态增删文档，无需重启服务（重新向量化为异步任务）

### 7.3 文档分割

- 使用 `RecursiveCharacterTextSplitter`
- chunk_size=500, chunk_overlap=50
- 结构化的规章制度使用较小 chunk，确保内容聚焦

### 7.4 混合检索

- 向量检索（语义相似） + BM25 关键词检索
- RRF (Reciprocal Rank Fusion) 融合排序
- 取 Top-5 结果注入 Prompt

### 7.5 分类检索

- 文档上传时打标签：规章制度 / 课程信息 / FAQ / 通知公告
- 检索时可限定标签范围，提高精度

### 7.6 RAG 准确率要求

- 在 50 对问答测试集上，计算 Hit@1 ≥ 85%
- Hit@1 定义：对于测试问题，检索结果中排名第一的片段是否包含正确答案的关键信息

### 7.7 搜索模式开关 (K05)

前端/API 提供三种搜索模式：

| 模式 | 取值 | 行为 |
|------|------|------|
| 仅知识库 | `knowledge_base` | 只检索内部知识库，不进行联网搜索 |
| 仅联网 | `web_search` | 直接调用搜索 API，不检索知识库 |
| 混合 | `hybrid` | 先检索知识库，若 Top-1 相似度低于 0.7 则触发联网搜索 |

### 7.8 Prompt 组装结构

```
┌─────────────────────────────────────┐
│  系统指令 (role prompt)              │  ← "你是双体软件精英产业学院的智能客服助手"
├─────────────────────────────────────┤
│  用户画像 (M03，可选)                 │  ← 长期记忆中的关键事实
├─────────────────────────────────────┤
│  长期回忆上下文 (M02，条件注入)       │  ← "以下是你们之前聊过的相关内容：..."
├─────────────────────────────────────┤
│  知识库检索结果 (RAG Top-5)          │  ← 引用来源（内部文档）
├─────────────────────────────────────┤
│  联网搜索结果 (条件注入)              │  ← 外部搜索来源（标题+摘要+链接）
├─────────────────────────────────────┤
│  短期记忆 (M01，最近10轮)            │  ← 当前会话上下文
├─────────────────────────────────────┤
│  用户当前问题                        │
└─────────────────────────────────────┘
```

---

## 8. 联网搜索模块

### 8.1 搜索引擎

- 首选 Tavily Search API，备选 Bing Web Search API
- API Key 通过环境变量配置，运行时可切换

### 8.2 搜索流程

```
用户问题 → (可选) LLM 改写为搜索关键词 → 调用搜索 API → 取前 5 条结果
→ 格式化为上下文文本（标题 + 摘要 + 链接） → 注入 Prompt
```

### 8.3 搜索结果引用

最终回答末尾以脚注形式列出信息来源：

```markdown
**参考来源：**
1. [计算机科学培养方案-某某大学](https://...)
2. [CS专业课程设置指南](https://...)
```

---

## 9. 特色工具模块

### 9.1 职业测评 (T01)

- 提供霍兰德职业兴趣测试（精简版，24 题）
- 题目通过 `GET /api/tools/career-assessment/questions` 获取
- 用户答题后，`POST /api/tools/career-assessment` 提交答案
- 后端根据计分规则输出职业建议（如"现实型：推荐工程师、机械师"）
- 测评结果可保存到用户资料

### 9.2 简历优化 (T02)

- `POST /api/tools/resume-optimize`，支持纯文本或 `.txt`/`.docx` 文件上传
- 系统结合知识库中的"优秀简历模板"和 LLM，给出：
  - 结构优化建议
  - 措辞改进（量化成果）
  - 排版提示
- 输出格式：分条列出，每条附示例

### 9.3 岗位匹配 (T03)

- 用户输入目标岗位名称 + 技能列表
- 系统调用知识库中的岗位技能要求（预置）或联网搜索获取最新岗位描述
- 输出：匹配度百分比 + 技能差距清单 + 学习建议

### 9.4 面试模拟 (T04)

- 用户选择目标岗位，`POST /api/tools/interview-simulator` 开始模拟
- 系统作为面试官依次提问（共 5~8 个问题），通过 `POST /api/tools/interview-simulator/answer` 提交回答
- 每个回答后系统给出简短反馈并追问下一题
- `POST /api/tools/interview-simulator/report` 结束模拟，生成评估报告（优点、待改进点）
- 面试对话需保存在 `messages` 表中（与普通对话隔离或标记 `session_type`）

---

## 10. 数据库设计

### 10.1 users 表（SQLite / PostgreSQL）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| username | TEXT UNIQUE NOT NULL | 用户名 |
| email | TEXT UNIQUE NOT NULL | 邮箱 |
| password_hash | TEXT NOT NULL | bcrypt 哈希密码 |
| avatar | TEXT | 头像 URL（可选） |
| profile_data | JSON | 个人资料（技能列表、测评结果等） |
| is_active | INTEGER | 账户状态：1 激活 / 0 禁用 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 10.2 messages 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| session_id | TEXT | 会话ID |
| user_id | TEXT | 用户ID |
| role | TEXT | user / assistant / system |
| content | TEXT | 消息内容 |
| round_number | INTEGER | 轮次编号 |
| vector_embedding | BLOB/JSON | 用户消息的向量（仅 role=user） |
| created_at | TEXT | 创建时间 |

### 10.3 long_term_memories 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| user_id | TEXT | 用户ID |
| fact | TEXT | 关键事实（如"用户喜欢 Python"） |
| source_session_id | TEXT | 来源会话ID |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 10.4 sessions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| user_id | TEXT | 用户ID |
| title | TEXT | 会话标题（首条消息前 20 字） |
| session_type | TEXT | 会话类型：chat / interview（面试模拟） |
| trigger_count | INTEGER | M02 触发计数（冷却机制） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 10.5 knowledge_documents 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID |
| filename | TEXT | 原始文件名 |
| category | TEXT | 分类标签 |
| chunk_count | INTEGER | 分割后的 chunk 数量 |
| status | TEXT | 处理状态 |
| created_at | TEXT | 创建时间 |

---

## 11. 安全性设计

### 11.1 密码安全

- 用户密码使用 bcrypt 哈希存储，cost factor = 10
- 禁止明文存储或传输密码

### 11.2 认证与鉴权

- JWT token 认证，token 有效期 7 天（可配置）
- 所有需要认证的接口通过 FastAPI 依赖注入统一校验
- 可选：退出登录时 token 加入 Redis/内存黑名单

### 11.3 数据隔离

- 所有对话查询、记忆查询、会话列表必须带 `user_id` 条件
- 防止水平越权：用户 A 无法访问用户 B 的会话或记忆

### 11.4 密钥管理

- 所有 API Key（LLM、Embedding、搜索）存储于 `.env` 文件
- `.env` 文件不得提交至版本控制系统（加入 `.gitignore`）

### 11.5 传输安全

- 生产环境强制 HTTPS，使用 TLS 1.2+
- 开发环境允许 HTTP

---

## 12. 流式输出 (SSE)

- 对话接口 `POST /api/chat/send/stream` 使用 Server-Sent Events 实现流式输出
- 客户端通过 `Accept: text/event-stream` 请求头标识流式请求
- 流式输出格式：

```
data: {"type": "thinking", "content": "正在检索知识库..."}

data: {"type": "sources", "content": [{ "doc_name": "...", ... }]}

data: {"type": "token", "content": "计"}

data: {"type": "token", "content": "算"}

data: {"type": "done"}
```

---

## 13. 错误处理

- API 层统一异常处理，返回 `{ "error": "...", "detail": "..." }` 格式
- LLM 调用超时（30s）自动降级：返回检索结果 + "模型暂时不可用，以下是与您问题相关的资料"
- 向量数据库不可用时，降级为纯 BM25 关键词检索
- 搜索 API 不可用时，降级为仅知识库模式（如用户选择了混合模式）
- 所有异常记录日志，便于排查
- HTTP 标准状态码：
  - 400：请求参数错误
  - 401：未认证 / token 过期
  - 403：无权限（水平越权）
  - 404：资源不存在
  - 500：服务器内部错误

---

## 14. 非功能需求

### 14.1 性能

| 指标 | 目标值 |
|------|--------|
| 对话接口响应时间 | 非流式 < 5s，流式首字 < 2s |
| 并发用户数 | 50 并发，错误率 < 1% |
| 知识库检索 | < 500ms |
| 系统可用性 | 99.5%（每月停机 ≤ 3.6 小时） |

### 14.2 备份与日志

- 对话数据每日凌晨 2 点全量备份，保留最近 30 天备份
- 日志分级（INFO、WARNING、ERROR），按天轮转，保留 30 天
- 关键错误需通过邮件或日志告警

---

## 15. 部署说明

### 15.1 环境准备

```bash
# Ubuntu
apt update && apt install python3.10 nginx
```

### 15.2 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入真实 API Key
python scripts/init_db.py
python scripts/load_knowledge.py --path ./knowledge_base
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 15.3 生产环境

- 使用 `gunicorn + uvicorn workers`
- ChromaDB 和 SQLite（或 PostgreSQL）数据文件挂载到持久化存储
- 前端配置 Nginx 反向代理 `/api` 到 `localhost:8000`
- 访问地址：
  - 前端：`http://your-domain`
  - API 文档：`http://your-domain/api/docs`
  - 健康检查：`http://your-domain/api/health`

### 15.4 运维要求

- 监控：Prometheus + Grafana 监控 CPU、内存、API 响应时间
- 日志：使用 ELK 或 Loki 收集日志，重点监控 LLM 调用失败率
- 备份：每日备份数据库，保留 7 天副本；每周全量备份知识库文件
- 更新：知识库更新后执行 `python scripts/reindex_knowledge.py`；代码更新需重启后端服务

---

## 16. 测试要求

### 16.1 测试范围

1. 单元测试（覆盖核心逻辑函数）
2. 集成测试（API 端到端）
3. 性能测试（并发、响应时间）

### 16.2 核心测试项

| 测试项 | 方法 | 通过标准 |
|--------|------|----------|
| RAG 准确率 | 50 对 Q/A 测试集 | Hit@1 ≥ 85% |
| M02 记忆检索触发 | 模拟 14 轮对话 | 第 12 轮后执行向量检索 |
| 并发测试 | 50 线程 × 2 分钟 | 错误率 < 1% |
