#!/bin/bash
# 僵尸等待循环守卫。
#
# 起因:2026-08-03 发现一个 `until [ -f /tmp/tb/private/github.json ]` 循环从
# 07-26 一直转到当天,整整 7 天 8 小时,而它等的那个文件连父目录都不存在 ——
# 也就是说它永远不会退出。这类循环是 agent 会话留下的孤儿:会话没了,循环还在,
# 每 5 秒 fork 一个 sleep,谁也不知道。历史上还有 7 个同类,最长 29 小时。
#
# 判定分两档,宁可漏杀不可误杀:
#   > 6h  记一行日志(给人看,可能是合法的长任务)
#   > 24h 终止(没有任何合法的 shell 等待循环需要转一整天;真需要的应当写成
#         systemd unit 或带超时上限的脚本)
#
# 白名单:带 timeout / --max-wait / SECONDS 上限的循环不算(它们自己会退)。
# 由 /etc/cron.d/linze-loop-guard 每小时执行。零模型调用。
set -uo pipefail
LOG=/srv/linze/logs/loop-guard.log
WARN=21600      # 6h
KILL=86400      # 24h
mkdir -p "$(dirname "$LOG")"

ps -eo pid,etimes,args --no-headers 2>/dev/null | while read -r pid etimes args; do
  case "$args" in
    *awk*|*loop-guard*|*ps\ -eo*) continue ;;
  esac
  # 只看 shell 里的 until/while + sleep 组合
  echo "$args" | grep -qE '(until|while) .*(sleep|usleep)' || continue
  # 自带超时上限的放过 —— 自身命令行有,或父进程是 timeout(timeout 包裹时,
  # 子进程的命令行里是看不到 "timeout" 字样的,只查自身会误杀)
  echo "$args" | grep -qE 'timeout |--max-wait|SECONDS -(lt|gt)|max_wait' && continue
  ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  if [ -n "$ppid" ] && [ "$ppid" != "1" ]; then
    ps -o args= -p "$ppid" 2>/dev/null | grep -qE '(^|/)timeout ' && continue
  fi

  if [ "$etimes" -gt "$KILL" ]; then
    kill "$pid" 2>/dev/null; sleep 2; kill -9 "$pid" 2>/dev/null
    echo "$(date -u +%FT%TZ) KILLED pid=$pid ran=$((etimes/3600))h cmd=$(echo "$args" | head -c 160)" >> "$LOG"
  elif [ "$etimes" -gt "$WARN" ]; then
    echo "$(date -u +%FT%TZ) WARN   pid=$pid ran=$((etimes/3600))h cmd=$(echo "$args" | head -c 160)" >> "$LOG"
  fi
done
exit 0
