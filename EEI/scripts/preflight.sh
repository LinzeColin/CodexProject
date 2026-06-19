#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

printf '== Task Pack static validation ==\n'
python3 scripts/validate_task_pack.py

printf '\n== Shell syntax ==\n'
bash -n scripts/preflight.sh scripts/run_codex_autonomous.sh

printf '\n== Required host tools ==\n'
required=(git python3)
optional=(codex docker node pnpm uv make)
for tool in "${required[@]}"; do
  command -v "$tool" >/dev/null || { echo "ERROR: required tool missing: $tool"; exit 1; }
  printf 'OK  %s: %s\n' "$tool" "$(command -v "$tool")"
done
for tool in "${optional[@]}"; do
  if command -v "$tool" >/dev/null; then
    printf 'OK  %s: %s\n' "$tool" "$(command -v "$tool")"
  else
    printf 'WARN %s is not installed; implementation/release steps may not run.\n' "$tool"
  fi
done

mkdir -p artifacts

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [[ -n "$(git status --porcelain)" ]]; then
    printf '\nWARN repository has uncommitted changes. Commit the Task Pack baseline before autonomous execution.\n'
  else
    printf '\nOK repository worktree is clean.\n'
  fi
else
  printf '\nWARN this directory is not yet a Git repository. Follow RUN_CODEX.md first.\n'
fi

cat <<'EOF'

Preflight complete.
Default execution policy: plan in read-only sandbox; build/QA in workspace-write; network disabled unless explicitly approved.
EOF
