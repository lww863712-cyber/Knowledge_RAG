# Windows 本地运行指南

## Docker Desktop 安装

1. 以管理员身份打开 PowerShell。
2. 启用 WSL：

```powershell
wsl --install
```

3. 重启电脑。
4. 安装 Docker Desktop：https://www.docker.com/products/docker-desktop/
5. 打开 Docker Desktop，确认 Settings → General → Use the WSL 2 based engine 已勾选。
6. 在 PowerShell 验证：

```powershell
wsl --status
docker --version
docker compose version
```

## 首次启动项目

```powershell
cd F:\python\PycharmProjects\one_RAG
Copy-Item .env.example .env
docker compose up --build
```

## 检查服务

- 后端健康检查：http://localhost:8000/api/v1/health
- API 文档：http://localhost:8000/docs
- 前端：http://localhost:5173
- Qdrant：http://localhost:6333/dashboard

## 常见问题

### 端口被占用

- 5432 被本地 PostgreSQL 占用：停止本地服务或修改 `docker-compose.yml` 映射端口。
- 5173 / 8000 被占用：修改映射端口并同步 `.env` 中的 `CORS_ORIGINS`。

### 本地 embedding 下载慢

首次运行会下载 `BAAI/bge-m3` 和 `BAAI/bge-reranker-v2-m3`。如果下载慢，可提前配置 HuggingFace 镜像：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

Docker 中可在 `backend` 服务的 `environment` 增加 `HF_ENDPOINT`。

### Python 3.13 依赖不兼容

按 PRD 约定，退回 Python 3.12：

```text
修改 backend/Dockerfile 为 FROM python:3.12-slim
修改 pyproject.toml requires-python 为 >=3.12
```

### CPU 内存不足

在 `docker-compose.yml` 的 `backend` 服务中设置：

```yaml
deploy:
  resources:
    limits:
      memory: 8G
```

或将 `.env` 中 `EMBEDDING_PROVIDER` 改为 `cloud`。