#!/bin/bash
# status 快照镜像到 Cloudflare R2。
#
# 目的是容灾,不是加速:status.linzezhang.com 已经在 Cloudflare 代理后面,带宽早就
# 走 CF 了。真正的缺口是 —— 数据只存在 OVH 一台机器上,OVH 一挂,「云平台总览」这个
# 本来该告诉你出了什么事的页面,自己先看不见了。镜像到 R2 之后,即使 OVH 整个下线,
# 最后一份快照仍然取得到。
#
# 频率取舍:R2 免费额度是 Class A(写) 100 万次/月。6 个文件 × 每分钟 = 156 万/月,
# 超了;× 每 5 分钟 = 5.2 万/月,安全。容灾场景下 5 分钟的陈旧度完全够用。
#
# 命名空间按 owner 定的职责:对象字节进 primary-objects/。
# 由 /etc/cron.d/linze-status-mirror 每 5 分钟执行。零模型调用。
set -uo pipefail
SRC=/srv/linze/apps/status/data
BUCKET=primary-objects
PREFIX=status/latest
LOG=/srv/linze/logs/status-r2-mirror.log
FILES="snapshot.json history.json usage_history.json selfheal.json prices.json graph.json"

ok=0; fail=0
for f in $FILES; do
  [ -s "$SRC/$f" ] || continue
  code=$(/usr/local/bin/linze-r2-put.sh "$SRC/$f" "$BUCKET" "$PREFIX/$f" 2>/dev/null)
  if [ "$code" = "200" ]; then ok=$((ok+1)); else fail=$((fail+1)); FAILED="${FAILED:-}$f($code) "; fi
done

# 只在有失败、或整点时记一行 —— 平时不写,别给磁盘添垃圾
if [ "$fail" -gt 0 ]; then
  echo "$(date -u +%FT%TZ) ok=$ok fail=$fail ${FAILED:-}" >> "$LOG"
elif [ "$(date -u +%M)" = "00" ]; then
  echo "$(date -u +%FT%TZ) ok=$ok fail=0" >> "$LOG"
fi
exit 0
