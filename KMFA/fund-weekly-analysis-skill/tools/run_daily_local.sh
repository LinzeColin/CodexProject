#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="${KMFA_REPO_ROOT:-$(cd "$SKILL_DIR/../.." && pwd)}"
INPUT_DIR="${KMFA_FUND_INPUT_DIR:-/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群}"
PROMPT_FILE="$SKILL_DIR/automation/weekly_1100_sydney.prompt.md"

cd "$REPO_ROOT"
if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "ERROR: daily automation must run on main" >&2
  exit 2
fi

git fetch origin main
git merge --ff-only origin/main

set +e
python3 "$SKILL_DIR/tools/check_source_readiness.py" --target-dir "$INPUT_DIR" --repo-root "$REPO_ROOT" --timezone Australia/Sydney
READINESS_EXIT=$?
set -e
if [[ "$READINESS_EXIT" -ne 0 ]]; then
  echo "ERROR: source readiness gate failed; run_fund_weekly_analysis.py was not started" >&2
  exit "$READINESS_EXIT"
fi

RUNNER_OUTPUT="$(python3 "$SKILL_DIR/tools/run_fund_weekly_analysis.py" --input-dir "$INPUT_DIR" --repo-root "$REPO_ROOT" --timezone Australia/Sydney)"
echo "$RUNNER_OUTPUT"
RUN_ID="$(printf '%s\n' "$RUNNER_OUTPUT" | sed -n 's/.*"run_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | tail -1)"
RUN_DIR="$(printf '%s\n' "$RUNNER_OUTPUT" | sed -n 's/.*"run_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | tail -1)"
if [[ -n "$RUN_DIR" ]]; then
  OCR_OUTPUT="$(python3 "$SKILL_DIR/tools/generate_screenshot_ocr_sidecars.py" --input-dir "$INPUT_DIR" --repo-root "$REPO_ROOT" --run-dir "$RUN_DIR" --engine "${KMFA_FUND_OCR_ENGINE:-vision}" --apply)"
  echo "$OCR_OUTPUT"
  GENERATED_SIDECAR_COUNT="$(printf '%s\n' "$OCR_OUTPUT" | sed -n 's/.*"generated_sidecar_count"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' | tail -1)"
  if [[ -n "$RUN_ID" && "${GENERATED_SIDECAR_COUNT:-0}" -gt 0 ]]; then
    RERUN_OUTPUT="$(python3 "$SKILL_DIR/tools/run_fund_weekly_analysis.py" --input-dir "$INPUT_DIR" --repo-root "$REPO_ROOT" --timezone Australia/Sydney --run-id "$RUN_ID")"
    echo "$RERUN_OUTPUT"
  fi
else
  echo "WARN: runner output did not include run_dir; OCR sidecar generation plan was skipped." >&2
fi

if command -v codex >/dev/null 2>&1; then
  # The exact Codex CLI may differ by local installation. Stdin keeps the prompt portable.
  codex exec < "$PROMPT_FILE"
else
  echo "WARN: codex CLI not found. Manifest created; run Codex with automation/weekly_1100_sydney.prompt.md manually." >&2
fi
