#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="${KMFA_REPO_ROOT:-$(cd "$SKILL_DIR/../.." && pwd)}"
INPUT_DIR="${KMFA_FUND_INPUT_DIR:-/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群}"
PROMPT_FILE="$SKILL_DIR/automation/daily_1130_sydney.prompt.md"

cd "$REPO_ROOT"
if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "ERROR: daily automation must run on main" >&2
  exit 2
fi

git fetch origin main
git merge --ff-only origin/main
python3 "$SKILL_DIR/tools/run_fund_weekly_analysis.py" --input-dir "$INPUT_DIR" --repo-root "$REPO_ROOT" --timezone Australia/Sydney

if command -v codex >/dev/null 2>&1; then
  # The exact Codex CLI may differ by local installation. Stdin keeps the prompt portable.
  codex exec < "$PROMPT_FILE"
else
  echo "WARN: codex CLI not found. Manifest created; run Codex with automation/daily_1130_sydney.prompt.md manually." >&2
fi
