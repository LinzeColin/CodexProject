#!/usr/bin/env bash
# 核对 OPERATIONS/host-bin 与生产主机 /usr/local/bin 是否已分叉。
#
# 为什么需要它:2026-08-11 把 14 个主机脚本收进仓之前,它们一年多只存在于机器上。
# 现在两边各有一份,**分叉只是时间问题** —— 有人在机器上热改一行救急,忘了回写仓,
# 半年后没人知道哪份是对的。这个脚本按 sha256 逐个比,不猜。
#
# 它只读、不改任何一边:发现分叉后**由人决定**哪份是对的。自动同步是危险的
# —— 方向猜错就把生产上的紧急修复覆盖掉了。
#
# 用法:
#   bash OPERATIONS/check-host-drift.sh          # 比对
#   bash OPERATIONS/check-host-drift.sh --cron   # 只输出结论行,给 cron 用
#
# 退出码:0=一致,1=有分叉,2=连不上主机(区分"不一致"和"没测成")
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

HOST="${LINZE_PROD_HOST:-15.235.141.201}"
KEY="${LINZE_PROD_KEY:-$HOME/Documents/Codex/GithubProject/_protected/alpha_deploy_private/linze_ovh_production_ed25519}"
QUIET=0; [ "${1:-}" = "--cron" ] && QUIET=1
say() { [ "$QUIET" = 1 ] || printf "%s\n" "$*"; }

[ -f "$KEY" ] || { echo "✗ 私钥不存在:$KEY"; exit 2; }

# 一次 ssh 把主机侧所有 sha 取回来 —— 逐个文件开一次连接会慢,而且 14 次连接
# 更容易撞上网络抖动被误判成分叉。
REMOTE=$(ssh -o BatchMode=yes -o ConnectTimeout=20 -i "$KEY" "ubuntu@$HOST" \
  'sudo sha256sum /usr/local/bin/linze-* 2>/dev/null | grep -v "\.bak"' 2>/dev/null)
if [ -z "$REMOTE" ]; then
  echo "✗ 连不上主机或取不到校验和 —— 这是「没测成」,不是「一致」"
  exit 2
fi

same=0; diff=0; only_repo=0; only_host=0
say "═══ 仓 ↔ 主机 脚本一致性 $(date '+%Y-%m-%d %H:%M') ═══"

for f in OPERATIONS/host-bin/*; do
  [ -f "$f" ] || continue
  n=$(basename "$f")
  a=$(shasum -a 256 "$f" 2>/dev/null | cut -d' ' -f1)
  b=$(printf "%s\n" "$REMOTE" | awk -v n="/usr/local/bin/$n" '$2==n{print $1}')
  if [ -z "$b" ]; then
    only_repo=$((only_repo+1)); say "  ✗ $n —— 仓里有,主机上没有(没部署?)"
  elif [ "$a" = "$b" ]; then
    same=$((same+1)); say "  ✓ $n"
  else
    diff=$((diff+1)); say "  ✗ $n —— **两边不一样**(仓 ${a:0:12} / 机 ${b:0:12})"
  fi
done

# 反向:主机上有、仓里没有的 —— 这类最危险,它是"又一个只存在于机器上的脚本"
while read -r _ path; do
  [ -n "$path" ] || continue
  n=$(basename "$path")
  [ -f "OPERATIONS/host-bin/$n" ] || { only_host=$((only_host+1)); say "  ✗ $n —— 主机上有,**仓里没有**(新脚本没进版本控制)"; }
done <<< "$REMOTE"

say ""
if [ $((diff + only_repo + only_host)) -eq 0 ]; then
  say "═══ 一致:$same 个脚本两边相同 ═══"; exit 0
fi
echo "分叉:内容不同 $diff · 仅仓有 $only_repo · 仅主机有 $only_host(一致 $same)"
say ""
say "**不要自动同步** —— 先弄清哪份是对的:"
say "  机器上那份新 = 有人热改救急没回写 → 把它 cp 回仓、提 PR"
say "  仓里那份新   = 改了没部署        → 按 OPERATIONS/README.md 的部署段推上去"
exit 1
