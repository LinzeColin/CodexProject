#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
OUTPUT_DIR="$PROJECT_DIR/data/systemAudit"
JSON_OUTPUT=0
SUMMARY_JSON=0
CI_STATUS="${PFI012_CI_STATUS:-NotVerified}"
CI_URL="${PFI012_CI_URL:-}"
ROLLBACK_REF="${PFI012_ROLLBACK_REF:-}"
USER_UAT_STATUS="${PFI012_USER_UAT_STATUS:-AutomatedBrowserPass}"
REQUIRE_EXTERNAL=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --ci-status)
      CI_STATUS="$2"
      shift 2
      ;;
    --ci-url)
      CI_URL="$2"
      shift 2
      ;;
    --rollback-ref)
      ROLLBACK_REF="$2"
      shift 2
      ;;
    --user-uat-status)
      USER_UAT_STATUS="$2"
      shift 2
      ;;
    --require-external-release-evidence)
      REQUIRE_EXTERNAL=1
      shift
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
      echo "Unknown pfi012MVPReleaseGate argument: $1" >&2
      exit 64
      ;;
  esac
done

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date -u +"%Y%m%d_%H%M%S")"
JSON_PATH="$OUTPUT_DIR/PFI012MVPReleaseGate_$STAMP.json"
LATEST_PATH="$OUTPUT_DIR/PFI012MVPReleaseGate_latest.json"
GIT_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"
BRANCH="$(git branch --show-current 2>/dev/null || true)"

export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
source "$PROJECT_DIR/scripts/pfiRuntime.sh"
PYTHON_BIN="$(pfi_os_ensure_app_python "$PROJECT_DIR")"

PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" - "$PROJECT_DIR" "$JSON_PATH" "$LATEST_PATH" "$GIT_HEAD" "$BRANCH" "$CI_STATUS" "$CI_URL" "$ROLLBACK_REF" "$USER_UAT_STATUS" "$REQUIRE_EXTERNAL" <<'PY'
import json
import shutil
import sys
from pathlib import Path

from pfi_os.application import run_pfi012_mvp_release_gate_acceptance

project_root = Path(sys.argv[1])
json_path = Path(sys.argv[2])
latest_path = Path(sys.argv[3])
git_head = sys.argv[4]
branch = sys.argv[5]
ci_status = sys.argv[6]
ci_url = sys.argv[7]
rollback_ref = sys.argv[8]
user_uat_status = sys.argv[9]
require_external = sys.argv[10] == "1"

payload = run_pfi012_mvp_release_gate_acceptance(
    project_root,
    git_head=git_head,
    branch=branch,
    ci_status=ci_status,
    ci_url=ci_url,
    rollback_ref=rollback_ref,
    user_uat_status=user_uat_status,
    require_external_release_evidence=require_external,
)
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
raise SystemExit(0 if payload.get("local_release_candidate_status") == "Pass" and payload.get("summary", {}).get("fail") == 0 else 2)
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
external = payload.get("external_release_evidence", {})
manifest = payload.get("checksum_manifest", {})
summary = {
    "schema": payload.get("schema"),
    "status": payload.get("status"),
    "local_release_candidate_status": payload.get("local_release_candidate_status"),
    "summary": payload.get("summary"),
    "issue_count": payload.get("release_matrix", {}).get("issue_count"),
    "gate_count": payload.get("release_matrix", {}).get("gate_count"),
    "p0_open_count": payload.get("blocker_disposition", {}).get("p0_open_count"),
    "p1_without_disposition_count": payload.get("blocker_disposition", {}).get("p1_without_disposition_count"),
    "uat_status": payload.get("uat_evidence", {}).get("status"),
    "privacy_status": payload.get("privacy_audit", {}).get("status"),
    "legacy_freeze_status": payload.get("legacy_freeze", {}).get("status"),
    "manifest_status": manifest.get("status"),
    "manifest_signature": manifest.get("signature", {}).get("value"),
    "external_status": external.get("overall_status"),
    "ci_status": external.get("ci_status"),
    "rollback_ref": external.get("rollback_ref"),
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
external = payload.get("external_release_evidence", {})
print(
    "PFI-012 MVP Release Gate: "
    f"local={payload.get('local_release_candidate_status')} "
    f"status={payload.get('status')} "
    f"pass={summary.get('pass')} fail={summary.get('fail')} "
    f"external={external.get('overall_status')}"
)
PY
