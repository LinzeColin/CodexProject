#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
OUTPUT_DIR="$PROJECT_DIR/data/systemAudit"
JSON_OUTPUT=0
SUMMARY_JSON=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --json)
      JSON_OUTPUT=1
      shift
      ;;
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    *)
      echo "Unknown pfi011LocalLLMDeepPathAcceptance argument: $1" >&2
      exit 64
      ;;
  esac
done

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date -u +"%Y%m%d_%H%M%S")"
JSON_PATH="$OUTPUT_DIR/PFI011LocalLLMDeepPathAcceptance_$STAMP.json"
LATEST_PATH="$OUTPUT_DIR/PFI011LocalLLMDeepPathAcceptance_latest.json"

export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" - "$JSON_PATH" "$LATEST_PATH" <<'PY'
import json
import shutil
import sys
from pathlib import Path

from pfi_os.application import run_pfi011_local_llm_deep_path_acceptance

json_path = Path(sys.argv[1])
latest_path = Path(sys.argv[2])
payload = run_pfi011_local_llm_deep_path_acceptance()
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
raise SystemExit(0 if payload.get("status") == "Pass" else 2)
PY

if [[ "$JSON_OUTPUT" == "1" ]]; then
  cat "$JSON_PATH"
  exit 0
fi

if [[ "$SUMMARY_JSON" == "1" ]]; then
  PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" - "$JSON_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
qa = payload.get("qa_summary", {})
summary = {
    "schema": payload.get("schema"),
    "status": payload.get("status"),
    "summary": payload.get("summary"),
    "hardware_status": payload.get("hardware_audit", {}).get("status"),
    "schema_validation": qa.get("schema_validation"),
    "citation_validation": qa.get("citation_validation"),
    "citation_count": qa.get("citation_count"),
    "timeout_fallback": qa.get("timeout_fallback"),
    "cancel": qa.get("cancel"),
    "resource_budget": qa.get("resource_budget"),
    "prompt_injection": qa.get("prompt_injection"),
    "disabled_provider_fallback": qa.get("disabled_provider_fallback"),
    "failed_checks": [row.get("name") for row in payload.get("checks", []) if row.get("status") == "Fail"],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
  exit 0
fi

PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" - "$JSON_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = payload.get("summary", {})
qa = payload.get("qa_summary", {})
print(
    "PFI-011 Local LLM Deep Path Acceptance: "
    f"{payload.get('status')} "
    f"pass={summary.get('pass')} fail={summary.get('fail')} "
    f"citations={qa.get('citation_count')} "
    f"qa={qa.get('overall')}"
)
PY
