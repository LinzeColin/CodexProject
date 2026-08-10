#!/bin/bash
# 工作间体检 —— 一条命令看清 8 个仓是否守着铁律。
#
# 为什么需要它:铁律写在 README、CLAUDE.md、AGENT_ONBOARDING 三处,仍然被破。
# 2026-08-10 盘点发现 MetaDatabase 主树脏了 6 天、落后 45 个提交,原因不是谁
# "在主树上改代码",而是有人**在主树目录里跑了 Serenity-Alipay 的 preflight**,
# 产物直接写进工作树。铁律说"只 pull 不写",但没人把"在里面跑程序"算作写。
# 文档补不上这种缝,只能靠机器每次实测。
#
# 用法:
#   bash tools/workspace-doctor.sh          # 体检,只读
#   bash tools/workspace-doctor.sh --fix    # 顺手修可安全自动修的(pull、prune)
#
# 退出码:0=全绿,1=有违规。可以挂进 CI 或开工前跑。
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
REPOS="AgentDatabase CodexProject Governance KMOS LinzeHomeHub MetaDatabase NotionStudyProject Private-Database"
FIX=0; [ "${1:-}" = "--fix" ] && FIX=1
# 违规计数落在临时文件而不是变量:下面几处用了 `... | while read`,那是子 shell,
# 变量自增出了循环就丢。这个坑在本仓的脚本里犯过不止一次。
VIOLF=$(mktemp); trap 'rm -f "$VIOLF"' EXIT

say()  { printf "%s\n" "$*"; }
bad()  { echo x >> "$VIOLF"; printf "  ✗ %s\n" "$*"; }
good() { printf "  ✓ %s\n" "$*"; }

say "═══ 工作间体检 $(date '+%Y-%m-%d %H:%M') ═══"
say ""

# ---------- 铁律 2:主树只读、停 main、干净 ----------
say "【铁律2】主树只读"
for r in $REPOS; do
  [ -d "$ROOT/$r/.git" ] || continue
  br=$(git -C "$r" branch --show-current 2>/dev/null)
  dirty=$(git -C "$r" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  git -C "$r" fetch origin --quiet 2>/dev/null
  behind=$(git -C "$r" rev-list --count HEAD..origin/main 2>/dev/null || echo 0)

  if [ -z "$br" ]; then
    bad "$r 主树处于 detached HEAD（多半是别的 worktree 占着 main）"
  elif [ "$br" != "main" ]; then
    bad "$r 主树停在 '$br',应停 main —— 整个仓的并行被这一个分支锁死"
  fi
  if [ "$dirty" != "0" ]; then
    bad "$r 主树有 $dirty 处未提交改动（主树永远该是干净的；产物请写到 _scratch）"
    git -C "$r" status --porcelain 2>/dev/null | head -3 | sed 's/^/      /'
  fi
  if [ "$behind" != "0" ] && [ "$behind" != "" ]; then
    if [ "$FIX" = 1 ] && [ "$dirty" = "0" ] && [ "$br" = "main" ]; then
      git -C "$r" pull --ff-only --quiet 2>/dev/null && good "$r 已追上 origin/main（补了 $behind 个提交）"
    elif [ "$dirty" = "0" ] && [ "$br" = "main" ]; then
      # 干净只是没 pull —— 别报成"脏树 pull 不动",那是另一回事,会误导人去找不存在的脏文件
      bad "$r 主树落后 origin/main $behind 个提交（干净,--fix 可直接追上）"
    else
      bad "$r 主树落后 origin/main $behind 个提交，且主树不干净/不在 main —— pull 不动，先按上面的问题处理"
    fi
  fi
  [ "$br" = "main" ] && [ "$dirty" = "0" ] && [ "$behind" = "0" ] && good "$r"
done

# ---------- 铁律 3:谁开的谁收 ----------
say ""
say "【铁律3】worktree 位置与回收"
for r in $REPOS; do
  [ -d "$ROOT/$r/.git" ] || continue
  git -C "$r" worktree list 2>/dev/null | tail -n +2 | while read -r wp rest; do
    case "$wp" in
      "$ROOT"/_scratch/*) ;;   # 合规
      *) echo "OUTSIDE|$r|$wp" ;;
    esac
  done
done | while IFS='|' read -r _ r wp; do
  bad "$r 的 worktree 开在 _scratch 之外:$wp"
done

# _scratch 里疑似该收的 worktree。
#
# ⚠️ 判据必须带时间维度。2026-08-10 这脚本的第一版只看「已并入 main + 0 改动」,
# 结果把一个**刚开出来还没提交**的 worktree 判成垃圾并收掉了 —— 刚从 origin/main
# 开出来的新 worktree 天生就是这个状态。那个 Codex 会话一分钟后就把它重建了。
# 收别人正在用的 worktree,本身就是在破铁律3(谁开的谁收)。
#
# 所以只有「已并入 main + 0 改动 + 连续 STALE_DAYS 天没人动过」才提示,而且只提示,
# 永远不自动收 —— 收不收是开它那个人的决定。
STALE_DAYS=3
for r in $REPOS; do
  [ -d "$ROOT/$r/.git" ] || continue
  git -C "$r" worktree list 2>/dev/null | tail -n +2 | awk '{print $1}' | while read -r wp; do
    case "$wp" in "$ROOT"/_scratch/*) ;; *) continue ;; esac
    [ -d "$wp" ] || continue
    # 活跃度以「最后一次提交时间」为准,不看工作树文件 mtime。
    # 2026-08-10 教训:agentdb-nasmyth-153 的工作树文件显示"近 1 天 0 改动",
    # 而它 23 分钟前还在提交(半小时内 8 次,任务 #153 正在密集推进)。checkout
    # 之后文件 mtime 不随提交更新,拿它判活跃会把最忙的分支判成僵尸 —— 差一点
    # 就把 863 个提交删掉了。
    last=$(git -C "$wp" log -1 --format=%ct HEAD 2>/dev/null)
    if [ -n "$last" ]; then
      age=$(( ( $(date +%s) - last ) / 86400 ))
      [ "$age" -lt "$STALE_DAYS" ] && continue
    fi
    # 不再看文件 mtime:checkout 会把 mtime 重置成"现在",拿它当补充判据会把真正
    # 陈旧的 worktree 挡掉(实测过)。"有人在用但还没提交"这种情况由下面的
    # 未提交改动检查(d != 0)兜住,不需要 mtime。
    d=$(git -C "$wp" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    h=$(git -C "$wp" rev-parse HEAD 2>/dev/null)
    if [ "$d" = "0" ] && git -C "$wp" merge-base --is-ancestor "$h" origin/main 2>/dev/null; then
      echo "REAP|$r|$(basename "$wp")"
    fi
  done
done | while IFS='|' read -r _ r n; do
  bad "$r 的 worktree '$n' 已并入 main、无改动、且 ${STALE_DAYS}+ 天没有新提交 —— 大概率是垃圾。**确认是你开的再收**"
done

# ---------- 守卫自身是否还在岗 ----------
say ""
say "【守卫】pre-commit hook 安装状态"
for r in $REPOS; do
  [ -d "$ROOT/$r/.git" ] || continue
  hk="$ROOT/$r/.git/hooks/pre-commit"
  pp="$ROOT/$r/.git/hooks/pre-push"
  hp=$(git -C "$r" config --get core.hooksPath 2>/dev/null)
  if [ -n "$hp" ]; then
    # 配了 hooksPath 就绕过 .git/hooks —— 装了也不跑。不点名的话这里会假绿。
    # 认 LINZE_ALLOW_BULK_PUSH 这个逃生口变量名 —— 它是闸的稳定标识,
    # 比注释文案可靠(第一版按 "bulk-guard" 去匹配,而 hook 里根本没这个词,
    # 结果闸装好了 doctor 还在报红)
    if grep -rq "LINZE_ALLOW_BULK_PUSH" "$ROOT/$r/$hp" 2>/dev/null; then
      good "$r（hooksPath=$hp，体积闸已接入）"
    else
      bad "$r 配了 core.hooksPath=$hp —— .git/hooks 不会被调用，守卫形同虚设。需在 $hp/pre-push 里接入体积闸"
    fi
  elif [ -x "$hk" ] && grep -q "linze-maintree-guard" "$hk" 2>/dev/null \
       && [ -x "$pp" ] && grep -q "linze-bulk-push-guard" "$pp" 2>/dev/null; then
    good "$r"
  else
    bad "$r 守卫不全（跑 bash tools/install-guards.sh 安装）"
  fi
done

# ---------- 生产主机指向(2026-08-10 迁移后新增) ----------
# 2026-08-10 生产从 OVH VPS-1 (139.99.61.6) 迁到 VPS-3 (15.235.141.201)。
# 旧 IP 散落在文档、脚本、示例命令里,后来的人照着连会连到一台已退役的机器上,
# 而且它可能还活着、还能登进去 —— 那种"连上了但改的不是生产"最难发现。
say ""
say "【生产主机】旧 IP 残留"
OLD_IP="139.99.61.6"
# 排除本文件自身 —— 上面的注释里就写着那个旧 IP,不排除会自己报自己
hits=$(grep -rl "$OLD_IP" "$ROOT"/tools "$ROOT"/README.md 2>/dev/null | grep -v "workspace-doctor.sh" | head -5)
if [ -n "$hits" ]; then
  while read -r f; do [ -n "$f" ] && bad "还引用已退役的 VPS-1 IP:${f#$ROOT/}"; done <<< "$hits"
else
  good "工具与 README 已无旧 IP"
fi
if curl -s -o /dev/null -m 8 -w '%{http_code}' https://status.linzezhang.com/ 2>/dev/null | grep -q '^2'; then
  good "status.linzezhang.com 可达(生产在 VPS-3)"
else
  bad "status.linzezhang.com 不可达 —— 生产可能出问题了"
fi

# ---------- 工作间契约本身有没有版本(2026-08-11 新增) ----------
# 到 2026-08-11 为止,这个工作间最要紧的三样东西 —— README(七条铁律,全局 CLAUDE.md
# 称它是唯一真源)、workspace-doctor.sh、install-guards.sh —— **只存在于这一台 Mac 上**,
# 任何仓里都没有。守着铁律的工具自己没有版本控制,机器一坏全没。
# 现在它们进了 CodexProject/OPERATIONS/workspace/;**仓是源、本机是部署副本**。
# 这一节按 sha256 比,防的是同一件事:两边各改各的,半年后没人知道哪份是对的。
say ""
say "【工作间契约】本机 ↔ CodexProject 仓"
REPO_WS="$ROOT/CodexProject/OPERATIONS/workspace"
if [ ! -d "$REPO_WS" ]; then
  bad "CodexProject/OPERATIONS/workspace 不存在 —— 主树没拉到最新?先 git -C CodexProject pull"
else
  ws_bad=0
  for pair in "README.md:$ROOT/README.md" \
              "tools/workspace-doctor.sh:$ROOT/tools/workspace-doctor.sh" \
              "tools/install-guards.sh:$ROOT/tools/install-guards.sh"; do
    rel="${pair%%:*}"; loc="${pair##*:}"
    if [ ! -f "$loc" ]; then bad "本机缺 ${loc#$ROOT/}"; ws_bad=1; continue; fi
    if [ ! -f "$REPO_WS/$rel" ]; then bad "仓里缺 OPERATIONS/workspace/$rel"; ws_bad=1; continue; fi
    a=$(shasum -a 256 "$loc" 2>/dev/null | cut -d' ' -f1)
    b=$(shasum -a 256 "$REPO_WS/$rel" 2>/dev/null | cut -d' ' -f1)
    if [ "$a" != "$b" ]; then
      bad "${loc#$ROOT/} 与仓里的 OPERATIONS/workspace/$rel 不一致 —— 先弄清哪份是对的,别自动覆盖"
      ws_bad=1
    fi
  done
  [ "$ws_bad" = 0 ] && good "README 与两个工具脚本都与仓一致"
fi

VIOL=$(wc -l < "$VIOLF" | tr -d ' ')
say ""
if [ "$VIOL" = 0 ]; then
  say "═══ 全绿,没有违规 ═══"; exit 0
else
  say "═══ 发现 $VIOL 处违规 ═══"
  say "可安全自动修的部分:bash tools/workspace-doctor.sh --fix"
  exit 1
fi
