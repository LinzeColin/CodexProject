#!/bin/bash
# STAGE-15.4 死链巡检; 有死链则记 WARN(供后续告警接入)
OUT=$(python3 /usr/local/bin/linze_link_health.py 2>&1)
RC=$?
echo "$(date -u +%FT%TZ) rc=$RC"
echo "$OUT" | tail -3
[ $RC -ne 0 ] && echo "$(date -u +%FT%TZ) WARN 检测到死链,请核对 home 卡片"
exit 0
