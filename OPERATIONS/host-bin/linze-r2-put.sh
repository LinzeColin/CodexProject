#!/bin/bash
# 往 Cloudflare R2 传一个对象。用法: linze-r2-put.sh <本地文件> <bucket> <对象key>
#
# 走 CF API 而不是 S3 SigV4:少一套签名代码,凭据就是一把 bearer token
# (/srv/linze/secrets/cf_r2_write_token,root 0600)。
# 按 owner 定的命名空间职责:
#   backups/private-database/  = Private-Database 可恢复快照的冷备
#   primary-objects/           = 大文件/二进制/隐私对象的字节权威源
# 单对象上限 300MB(CF API 单次 PUT 的实用上限),超了直接报错而不是静默截断。
set -uo pipefail
F=$1; B=$2; K=$3
ACC=a8e86fa4be62ee3f9b5873b2aa934256
T=$(cat /srv/linze/secrets/cf_r2_write_token 2>/dev/null)
[ -z "$T" ] && { echo "no-token"; exit 1; }
[ -s "$F" ] || { echo "no-file"; exit 1; }
SZ=$(stat -c%s "$F")
if [ "$SZ" -gt 314572800 ]; then echo "too-big:$((SZ/1024/1024))M"; exit 1; fi
# cf-r2-storage-class 必须显式写死 Standard。不写就继承**桶的默认存储类**——
# 2026-08-07 的 $9.92 账单就是这么来的:backups 桶建桶时默认值是 InfrequentAccess,
# 而 IA 完全没有免费额度且按整计费单位向上取整,51 次操作收了 $9.00。
# 桶默认值现在是对的,但那是一个看不见的单点开关,别再依赖它。
curl -s -o /dev/null -w '%{http_code}' -m 600 -X PUT \
  -H "Authorization: Bearer $T" -H "Content-Type: application/octet-stream" \
  -H "cf-r2-storage-class: Standard" \
  --data-binary @"$F" \
  "https://api.cloudflare.com/client/v4/accounts/$ACC/r2/buckets/$B/objects/$K"
