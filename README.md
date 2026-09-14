`markdown
# one_RAG

> 个人知识库 AgentRAG 系统 —— 多源资料导入、多知识库管理、混合检索增强问答、LangGraph Agent 智能工作流

## 项目简介

one_RAG 是一个面向个人使用场景的知识库 AgentRAG 系统，支持 PDF、DOCX、PPTX、Markdown、网页、代码等多种格式文档的导入与解析，通过 **BM25 + 稠密向量 + Rerank** 三级混合检索，结合 **LangGraph Agent** 实现智能多步问答，提供完整的 Web UI 涵盖知识库管理、文档管理、对话问答、检索调试、模型配置和 Token 用量统计。
mermaid flowchart LR UI["Vue 3 Web UI"] -->|HTTP / SSE| API["FastAPI"] API --> AUTH["Auth / JWT"] API --> KB["Knowledge Base Service"] KB --> DB[("PostgreSQL")] KB --> FS[("Local File Volume")] ING["Ingestion Pipeline"] --> PARSER["Parser"] PARSER --> SPLIT["Chunker"] SPLIT --> EMB["Embedding Service"] EMB --> QD[("Qdrant")] SPLIT --> BM25["BM25 Index"] QD --> RET["Hybrid Retrieval"] BM25 --> RET RET --> RERANK["Reranker"] RERANK --> AGENT["LangGraph Agent"] AGENT --> LLM["Cloud LLM Providers"] AGENT --> API
## 功能与技术栈

| 模块 | 功能 | 技术选型 |
| --- | --- | --- |
| 📄 文档导入 | 拖拽上传、目录扫描、URL 抓取、API 批量导入 | FastAPI + SQLAlchemy |
| 📑 文件解析 | PDF / DOCX / PPTX / Markdown / TXT / HTML / CSV / XLSX / JSON / XML / 网页 / 代码 | 自研 Parser |
| 🔍 混合检索 | BM25 + 稠密向量 + Rerank，支持按知识库 / 文档 / 元数据过滤 | Qdrant + BM25 + bge-reranker |
| 💬 多轮对话 | 上下文保持、来源引用、原文跳转、SSE 流式输出 | SSE + LangGraph |
| 🤖 Agent | `knowledge_base_search` + `summarize`，多步任务编排 | LangGraph |
| ⚙️ 模型配置 | DeepSeek / Qwen / OpenAI / 智谱 / OpenAI 兼容，可配切换 | 多 Provider 抽象 |
| 📊 Token 用量 | 按模型统计 Token 消耗与成本估算，阈值提醒 | PostgreSQL |
| 🔐 用户管理 | JWT 登录、管理员创建用户、密码哈希存储 | JWT + bcrypt |

**完整技术栈：**
- **后端**：Python 3.13 + FastAPI + SQLAlchemy + LangGraph
- **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus
- **向量库**：Qdrant · **元数据数据库**：PostgreSQL 16
- **Embedding**：BAAI/bge-m3（本地） / 云端可切换 · **Reranker**：BAAI/bge-reranker-v2-m3

## 目录结构
text one_RAG/ ├── backend/ # FastAPI 后端 │ ├── app/ │ │ ├── agents/ # LangGraph Agent │ │ ├── api/v1/ # REST API 路由 │ │ ├── core/ # 配置与安全 │ │ ├── db/ # 数据库连接与初始化 │ │ ├── models/ # SQLAlchemy 数据模型 │ │ ├── rag/ # RAG 核心（解析/切分/向量/检索/重排） │ │ ├── schemas/ # Pydantic 模型 │ │ └── services/ # 业务服务层 │ └── tests/ # 单元测试 ├── frontend/ # Vue 3 前端 │ └── src/ │ ├── api/ # HTTP 请求封装 │ ├── layouts/ # 页面布局 │ ├── router/ # 路由配置 │ ├── stores/ # Pinia 状态管理 │ └── views/ # 页面组件 ├── docker/ # Nginx 配置 ├── docs/ # PRD 与部署文档 ├── scripts/ # 部署与备份脚本 ├── docker-compose.yml └── .env.example
## 快速开始

前置条件：Windows 10/11 + WSL2 + Docker Desktop。
powershell
1. 复制环境变量并编辑，填入 LLM_API_KEY 等配置
Copy-Item .env.example .env
2. 启动所有服务
docker compose up --build
启动后访问：
- 🖥️ 前端 UI：http://localhost:5173
- 📡 后端 API 文档：http://localhost:8000/docs
- 🔎 Qdrant 控制台：http://localhost:6333/dashboard
- 默认管理员：`admin` / `admin123`（首次登录后请及时修改，或通过 `.env` 中 `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` 指定）

编辑 `.env` 配置 LLM 与模型：
env LLM_PROVIDER=deepseek # 支持 deepseek / qwen / openai / zhipu / openai_compatible LLM_API_KEY=你的APIKey LLM_MODEL=deepseek-chat LLM_BASE_URL= # openai_compatible 时填写 EMBEDDING_PROVIDER=local # local 或 cloud，cloud 需配置 CLOUD_EMBEDDING_API_KEY
本地模型默认使用 `BAAI/bge-m3`（Embedding）和 `BAAI/bge-reranker-v2-m3`（Reranker），CPU 可运行。

不使用 Docker 的本地开发：
本地模型默认使用 `BAAI/bge-m3`（Embedding）和 `BAAI/bge-reranker-v2-m3`（Reranker），CPU 可运行。

不使用 Docker 的本地开发：
powershell
后端
cd backend python -m venv .venv; ..venv\Scripts\Activate.ps1 pip install -e . $env:DATABASE_URL="postgresql+asyncpg://rag:rag_password@localhost:5432/rag" $env:QDRANT_URL="http://localhost:6333" uvicorn app.main:app --reload
前端（另开终端）
cd frontend npm install; npm run dev
> ⚠️ 不使用 Docker 时需单独启动 PostgreSQL 和 Qdrant。

## 测试与部署
powershell
单元测试
cd backend && python -m pytest
Docker 内测试
docker compose exec backend pytest
Linux 服务器部署详见 [docs/deploy.md](docs/deploy.md)。

## 路线图

- **✅ v1 — MVP**：知识库管理、文档导入解析、混合检索、多轮对话、Agent、Token 统计、Web UI
- **🔜 v2 — 增强**：OCR（MinerU / PaddleOCR）、代码 AST 索引、自动标签与知识卡、联网搜索
- **🔜 v3 — 服务器部署**：Ubuntu + Nginx + HTTPS、备份恢复、多用户权限、审计日志

---

<p align="center">Made with ❤️ for personal knowledge management</p>
