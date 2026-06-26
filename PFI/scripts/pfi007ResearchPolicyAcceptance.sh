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
      echo "Unknown pfi007ResearchPolicyAcceptance argument: $1" >&2
      exit 64
      ;;
  esac
done

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date -u +"%Y%m%d_%H%M%S")"
JSON_PATH="$OUTPUT_DIR/PFI007ResearchPolicyAcceptance_$STAMP.json"
LATEST_PATH="$OUTPUT_DIR/PFI007ResearchPolicyAcceptance_latest.json"

export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" - "$JSON_PATH" "$LATEST_PATH" <<'PY'
import json
import shutil
import sys
from pathlib import Path

from pfi_os.application import run_pfi007_research_policy_acceptance

json_path = Path(sys.argv[1])
latest_path = Path(sys.argv[2])
payload = run_pfi007_research_policy_acceptance()
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
summary = {
    "schema": payload.get("schema"),
    "status": payload.get("status"),
    "summary": payload.get("summary"),
    "workflow_id": payload.get("golden_metrics", {}).get("workflow_id"),
    "policy_record_count": payload.get("golden_metrics", {}).get("policy_record_count"),
    "official_citation_count": payload.get("golden_metrics", {}).get("official_citation_count"),
    "report_gap_count": payload.get("golden_metrics", {}).get("report_gap_count"),
    "report_manifest_count": payload.get("golden_metrics", {}).get("report_manifest_count"),
    "rollback_status": payload.get("rollback_proof", {}).get("status"),
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
print(
    "PFI-007 Research Policy Acceptance: "
    f"{payload.get('status')} "
    f"pass={summary.get('pass')} fail={summary.get('fail')} "
    f"workflow_id={payload.get('golden_metrics', {}).get('workflow_id')}"
)
PY
