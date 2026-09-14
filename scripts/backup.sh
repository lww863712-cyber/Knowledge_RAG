#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR="backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "正在备份 PostgreSQL..."
docker run --rm \
  -v one_rag_postgres_data:/data \
  -v "$PWD/$BACKUP_DIR":/backup \
  alpine tar czf "/backup/postgres-$STAMP.tar.gz" -C /data .

echo "正在备份 Qdrant..."
docker run --rm \
  -v one_rag_qdrant_data:/data \
  -v "$PWD/$BACKUP_DIR":/backup \
  alpine tar czf "/backup/qdrant-$STAMP.tar.gz" -C /data .

echo "正在备份文件存储..."
docker run --rm \
  -v one_rag_file_data:/data \
  -v "$PWD/$BACKUP_DIR":/backup \
  alpine tar czf "/backup/files-$STAMP.tar.gz" -C /data .

echo "备份完成：$BACKUP_DIR"