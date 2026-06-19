#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

command -v codex >/dev/null || { echo "ERROR: codex CLI not found." >&2; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "ERROR: initialize and commit a Git baseline first." >&2; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo "ERROR: worktree must be clean before autonomous execution." >&2; exit 1; }

bash scripts/preflight.sh
mkdir -p artifacts

run_prompt() {
  local name="$1" sandbox="$2" prompt="$3" output="$4"
  printf '\n== %s ==\n' "$name"
  local -a cmd=(codex exec --sandbox "$sandbox")
  if [[ "${ALLOW_NETWORK:-0}" == "1" && "$sandbox" == "workspace-write" ]]; then
    cmd+=(-c 'sandbox_workspace_write.network_access=true')
    echo "NETWORK EXCEPTION ENABLED for this run; review domains and restore ALLOW_NETWORK=0 after bootstrap."
  fi
  "${cmd[@]}" - < "$prompt" | tee "$output"
}

run_prompt "G0 read-only plan" "read-only" "prompts/01_PLAN_ONLY.md" "artifacts/01_plan_output.txt"

if [[ "${AUTO_CONTINUE_AFTER_PLAN:-0}" != "1" ]]; then
  cat <<'EOF'

Plan generated. Review artifacts/01_plan_output.txt.
To continue without another interactive checkpoint, rerun with:
  AUTO_CONTINUE_AFTER_PLAN=1 bash scripts/run_codex_autonomous.sh
EOF
  exit 0
fi

run_prompt "G1-G8 MVP build" "workspace-write" "prompts/02_BUILD_MVP.md" "artifacts/02_build_output.txt"
run_prompt "G9 QA/release" "workspace-write" "prompts/03_QA_RELEASE.md" "artifacts/03_qa_output.txt"

printf '\nAutonomous sequence finished. Inspect PLANS.md, artifacts/, git diff, and make verify before accepting the release candidate.\n'
