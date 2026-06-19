#!/usr/bin/env bash
set -u -o pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$PIPELINE_DIR/../.." && pwd)"
OUT="$PROJECT_ROOT/outputs"
MODE="dry-run"
BOARD="${TAB_FIFA_SMOKE_BOARD:-matches}"
LIMIT="${TAB_FIFA_SMOKE_LIMIT:-1}"
TIMEOUT_MS="${TAB_FIFA_SMOKE_TIMEOUT_MS:-30000}"

for arg in "$@"; do
  case "$arg" in
    --live) MODE="live" ;;
    --dry-run) MODE="dry-run" ;;
    --board=*) BOARD="${arg#--board=}" ;;
    --limit=*) LIMIT="${arg#--limit=}" ;;
    --timeout-ms=*) TIMEOUT_MS="${arg#--timeout-ms=}" ;;
    *) echo "ERROR: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

NODE_BIN="${TAB_FIFA_NODE_BIN:-}"
if [[ -z "$NODE_BIN" ]]; then
  BUNDLED_NODE="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
  if [[ -x "$BUNDLED_NODE" ]]; then
    NODE_BIN="$BUNDLED_NODE"
  elif command -v node >/dev/null 2>&1; then
    NODE_BIN="$(command -v node)"
  else
    echo "ERROR: node runtime not found. Set TAB_FIFA_NODE_BIN." >&2
    exit 1
  fi
fi

mkdir -p "$OUT"
STAGING="$(mktemp -d -t tab-fifa-smoke-XXXXXX)"
STDOUT_FILE="$STAGING/stdout.json"
STDERR_FILE="$STAGING/stderr.txt"
SUMMARY_FILE="$OUT/tab_real_refresh_smoke_latest.json"
if [[ -n "${TAB_FIFA_SMOKE_SUMMARY_FILE:-}" ]]; then
  SUMMARY_FILE="$TAB_FIFA_SMOKE_SUMMARY_FILE"
fi
REFRESH_ID="smoke-$(date -u +%Y%m%dT%H%M%SZ)"

CMD=("$NODE_BIN" "$PIPELINE_DIR/scripts/refresh_tab_readonly.mjs" "--board" "$BOARD" "--refresh-id" "$REFRESH_ID" "--timeout-ms" "$TIMEOUT_MS" "--smoke")
if [[ "$MODE" == "dry-run" ]]; then
  CMD+=("--dry-run")
else
  CMD+=("--output-dir" "$STAGING" "--limit" "$LIMIT")
fi

"${CMD[@]}" >"$STDOUT_FILE" 2>"$STDERR_FILE"
STATUS=$?

python3 - "$SUMMARY_FILE" "$STDOUT_FILE" "$STDERR_FILE" "$STAGING" "$MODE" "$BOARD" "$LIMIT" "$TIMEOUT_MS" "$REFRESH_ID" "$STATUS" "${CMD[@]}" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

summary_path = Path(sys.argv[1])
stdout_path = Path(sys.argv[2])
stderr_path = Path(sys.argv[3])
staging = Path(sys.argv[4])
mode, board, limit, timeout_ms, refresh_id, status_text = sys.argv[5:11]
command = sys.argv[11:]
status = int(status_text)

try:
    stdout_payload = json.loads(stdout_path.read_text())
except Exception:
    stdout_payload = {"raw_stdout": stdout_path.read_text(errors="ignore")[:4000]}
stderr = stderr_path.read_text(errors="ignore")

def redact_local_paths(value):
    if isinstance(value, dict):
        return {key: redact_local_paths(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_local_paths(child) for child in value]
    if isinstance(value, str) and value.startswith("/") and not value.startswith("//"):
        return Path(value).name
    return value

safety = {}
if mode == "live" and status == 0:
    from tab_research.safety import audit_public_artifact_safety

    raw_outputs = [
        staging / Path(item.get("output", "")).name
        for item in stdout_payload.get("results", [])
        if item.get("output")
    ]
    safety = audit_public_artifact_safety(raw_outputs)
    if not raw_outputs:
        safety = {
            "public_artifact_safety_ready": False,
            "public_artifact_issue_count": 1,
            "public_artifact_issues": [{"path": staging.name, "markers": ["missing_smoke_raw_output"]}],
            "blocking_reasons": ["smoke did not produce a raw output artifact."],
        }
    safety_ready = safety.get("public_artifact_safety_ready", safety.get("automation_safety_ready", False))
    if not safety_ready:
        status = 1

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": mode,
    "board": board,
    "limit": int(limit),
    "timeout_ms": int(timeout_ms),
    "refresh_id": refresh_id,
    "command": [Path(part).name if "/" in part else part for part in command],
    "exit_code": status,
    "ready": status == 0,
    "staging_dir_name": staging.name,
    "stdout": redact_local_paths(stdout_payload),
    "stderr_tail": stderr[-4000:],
    "safety": safety,
}
summary_path.parent.mkdir(parents=True, exist_ok=True)
tmp_summary = summary_path.with_name(f".{summary_path.name}.{os.getpid()}.tmp")
tmp_summary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
os.replace(tmp_summary, summary_path)
print(json.dumps(payload, indent=2, ensure_ascii=False))
sys.exit(status)
PY
