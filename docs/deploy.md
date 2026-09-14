# 服务器部署指南

当前仓库已经提供完整生产部署文件，适合有 Linux 服务器后直接使用。

## 一、准备服务器

推荐环境：

- Ubuntu 22.04 或 24.04
- 至少 4GB 内存，建议 8GB 以上
- 已开放 80 端口；HTTPS 还需要 443 端口

安装 Docker：

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 二、上传项目

```bash
git clone <你的仓库地址> /opt/one_rag
cd /opt/one_rag
```

## 三、配置生产环境

```bash
cp .env.production.example .env.production
nano .env.production
```

必须修改：

- `SECRET_KEY`：长度至少 32 字节
- `POSTGRES_PASSWORD`
- `DEFAULT_ADMIN_PASSWORD`
- `LLM_API_KEY`
- `CORS_ORIGINS`：改为 `http://你的服务器IP` 或正式域名
- 如需 HTTPS：先准备域名，再继续后续 Certbot 步骤

## 四、启动服务

```bash
chmod +x scripts/deploy.sh scripts/backup.sh
./scripts/deploy.sh
```

检查状态：

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

访问：

- 无域名：`http://服务器公网IP`
- API 文档：`http://服务器公网IP/api/...` 由前端 Nginx 代理，后端不直接暴露

## 五、HTTPS 配置

HTTPS 需要域名解析到服务器。

1. 修改 `CORS_ORIGINS` 为正式域名。
2. 安装 Certbot：

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

3. 生成证书：

```bash
sudo certbot --nginx -d your-domain.com
```

4. 根据 Certbot 修改 Nginx 配置后重新加载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 六、数据备份

```bash
./scripts/backup.sh
```

备份文件会生成在 `backups/` 目录：

- `postgres-*.tar.gz`
- `qdrant-*.tar.gz`
- `files-*.tar.gz`

建议定期将 `backups/` 同步到异地存储。

## 七、数据迁移

从本地迁移到服务器时，需要复制三类数据：

- PostgreSQL 数据
- Qdrant 数据
- `file_data` 文件存储

最简单的方式：

```bash
# 本地导出
./scripts/backup.sh

# 把 backups/ 上传到服务器
scp -r backups/ user@服务器IP:/opt/one_rag/

# 服务器恢复时，将压缩包内容放回对应 Docker 命名卷
```

生产环境数据卷名称固定为：

- `one_rag_postgres_data`
- `one_rag_qdrant_data`
- `one_rag_file_data`