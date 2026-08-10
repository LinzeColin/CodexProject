#!/bin/bash
set -euo pipefail
TS=$(date -u +%Y%m%d-%H%M%S)
DEST=/srv/linze/backups/coolify
mkdir -p "$DEST"
# DB 转储
docker exec coolify-db pg_dump -U coolify -d coolify | gzip > "$DEST/coolify-db-$TS.sql.gz"
# 关键配置(.env 含 APP_KEY)
cp /data/coolify/source/.env "$DEST/coolify-env-$TS.env"
chmod 600 "$DEST"/coolify-*
# 保留最近 14 份
ls -1t "$DEST"/coolify-db-*.sql.gz | tail -n +15 | xargs -r rm -f
ls -1t "$DEST"/coolify-env-*.env | tail -n +15 | xargs -r rm -f
echo "backup ok $TS"
