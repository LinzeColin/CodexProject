#!/bin/bash
# 给 8 个仓装主树守卫（pre-commit hook）。
#
# 铁律 2 说"主树只读",但它只是一句话 —— 2026-08-10 之前它被破过不止一次。
# 这个 hook 让它变成机器强制:在主树的 main/master 上 commit 直接被拒,
# 在 worktree 里不受影响。
#
# hook 不进 git（.git/hooks/ 不受版本控制),所以 clone 新仓、或 .git 被重建之后
# 要重跑这个脚本。workspace-doctor.sh 会检查它还在不在岗。
#
# 逃生口:确实需要在主树提交时 LINZE_ALLOW_MAINTREE_COMMIT=1 git commit ...
# 用之前先想清楚为什么不开 worktree。
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
REPOS="AgentDatabase CodexProject Governance KMOS LinzeHomeHub MetaDatabase NotionStudyProject Private-Database"
N=0

for r in $REPOS; do
  [ -d "$r/.git" ] || continue
  hd="$r/.git/hooks"; mkdir -p "$hd"
  cat > "$hd/pre-commit" <<'HOOK'
#!/bin/sh
# linze-maintree-guard —— 铁律2 的机器强制版。由 tools/install-guards.sh 安装。
[ -n "${LINZE_ALLOW_MAINTREE_COMMIT:-}" ] && exit 0

gitdir=$(git rev-parse --git-dir 2>/dev/null)
case "$gitdir" in
  */worktrees/*) exit 0 ;;   # 在 worktree 里,放行 —— 开发本来就该在这儿
esac

br=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$br" = "main" ] || [ "$br" = "master" ]; then
  cat >&2 <<'MSG'

  ✗ 拒绝提交:你在主工作树的 main 上。

  铁律2 —— 主树只读。它永远停 main、永远干净,只 pull 不写;
  它是所有 worktree 的 base,被谁占着,整个仓的并行就被那个人锁死。

  开发请开 worktree:
      git worktree add ../_scratch/<repo>-<任务名> -b <分支名> origin/main

  另外:不要在主树目录里跑任何会写文件的程序(测试、preflight、采集脚本…)。
  "只 pull 不写" 包括不写产物 —— 2026-08-05 就是这么把 MetaDatabase 主树
  弄脏 6 天、卡住 45 个提交的。产物一律写到 _scratch。

  真要在主树提交:LINZE_ALLOW_MAINTREE_COMMIT=1 git commit ...

MSG
  exit 1
fi
exit 0
HOOK
  chmod +x "$hd/pre-commit"

  # ---- pre-push:大体积闸 ----
  cat > "$hd/pre-push" <<'HOOK2'
#!/bin/sh
# linze-bulk-push-guard —— 拦住把 GB 级产物推进仓的那一下。
#
# 2026-08-10 实测:AgentDatabase 有个本地分支的 CodexSkills/skill_log_evals 已经
# 攒到 2.6 GB / 9266 个文件,而 origin/main 上同一目录只有 7.1 MB。一旦那个分支被
# 推上去合并,这个仓就永久背上 2.6 GB —— 每个 clone、每个 worktree 都要复制一份,
# 而且 git 历史删不掉(rewrite 会改写所有 commit hash)。
#
# 注意:单文件阈值拦不住这种情况(9266 个文件个个都不大),所以这里按**本次推送新增
# 的 blob 总量**判。GitHub 自己只在单文件 >50MB 时才警告,那太晚了。
#
# 逃生口:LINZE_ALLOW_BULK_PUSH=1 git push ...
[ -n "${LINZE_ALLOW_BULK_PUSH:-}" ] && exit 0
LIMIT_MB=200
z=0000000000000000000000000000000000000000

while read -r lref lsha rref rsha; do
  [ "$lsha" = "$z" ] && continue            # 删分支
  if [ "$rsha" = "$z" ]; then rng="$lsha --not --remotes"; else rng="$rsha..$lsha"; fi
  # rev-list --objects 每行是 "<sha> <path>",而 cat-file --batch-check 只吃纯 sha:
  # 不切掉路径的话,带路径的 blob 行会被整行忽略,结果恒为 0 —— 这个闸就成了摆设。
  # 2026-08-10 第一版正是这么写的,拿 1.9 GB 的真分支去撞,它放行了。
  bytes=$(git rev-list --objects $rng 2>/dev/null | awk '{print $1}' \
    | git cat-file --batch-check='%(objecttype) %(objectsize)' 2>/dev/null \
    | awk '/^blob/{s+=$2} END{print s+0}')
  mb=$((bytes / 1048576))
  if [ "$mb" -gt "$LIMIT_MB" ]; then
    cat >&2 <<MSG

  ✗ 拒绝推送:本次要推 ${mb} MB 的新增内容（上限 ${LIMIT_MB} MB）。

  仓一旦收下这些字节就再也吐不出来 —— git 历史删不掉，除非 rewrite 全部
  commit hash。每个 clone、每个 worktree 都要跟着复制一份。

  先确认里面有没有本不该进 git 的东西（评估日志 / 构建产物 / 数据集 / 缓存）：
      git rev-list --objects $rng | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' | sort -k2 -rn | head -20

  这类产物应当 .gitignore 掉，另存 GitHub Release 或 R2。
  注意 R2 有额度红线（Standard 10GB 免费、IA 一次操作就起步 \$9.91），
  存之前先看 status 的 r2_free_tier_guard 判定。

  确认无误要强推:LINZE_ALLOW_BULK_PUSH=1 git push ...

MSG
    exit 1
  fi
done
exit 0
HOOK2
  chmod +x "$hd/pre-push"

  # 配了 core.hooksPath 的仓会绕过 .git/hooks —— 装了也不跑,必须点名说清楚
  hp=$(git -C "$r" config --get core.hooksPath 2>/dev/null)
  if [ -n "$hp" ]; then
    echo "  ⚠ $r 配了 core.hooksPath=$hp,.git/hooks 不会被调用。"
    echo "     请在 $r/$hp/pre-push 开头加一行:"
    echo "       bash \"\$(git rev-parse --show-toplevel)/../tools/bulk-guard.sh\" \"\$@\" || exit 1"
  fi
  N=$((N+1))
  echo "  ✓ $r"
done
echo "已装 $N 个仓的主树守卫。"
echo "体检:bash tools/workspace-doctor.sh"
