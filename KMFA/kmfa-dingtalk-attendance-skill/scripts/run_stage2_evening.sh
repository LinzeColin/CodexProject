#!/usr/bin/env bash
set -euo pipefail

# Wrapper for evening automation. This script resolves the monthly gate and,
# if eligible, expects the repo-specific adapter to produce run artifacts.
# Integrate the TODO adapter command with the existing KMFA attendance pipeline.

REPO_ROOT="${KMFA_REPO_ROOT:-/Users/linzezhang/CodexProject/KMFA}"
PRIVATE_RUNTIME="${KMFA_PRIVATE_RUNTIME:-$REPO_ROOT/metadata/dingtalk_attendance/private_runtime}"
SKILL_DIR="${KMFA_SKILL_DIR:-$REPO_ROOT/kmfa-dingtalk-attendance-skill}"
export KMFA_RUN_SLOT="${KMFA_RUN_SLOT:-evening}"

GATE_JSON="$PRIVATE_RUNTIME/month_gate_$(date +%Y%m%dT%H%M%S).json"
mkdir -p "$PRIVATE_RUNTIME"
python3 "$SKILL_DIR/scripts/month_gate.py" --run-slot "$KMFA_RUN_SLOT" --print-json > "$GATE_JSON"
cat "$GATE_JSON"

eligible="$(python3 - "$GATE_JSON" <<'PY'
import json, sys
print(str(json.load(open(sys.argv[1]))["stage2_eligible"]).lower())
PY
)"

target_month="$(python3 - "$GATE_JSON" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["target_month"])
PY
)"
run_index="$(python3 - "$GATE_JSON" <<'PY'
import json, sys
d=json.load(open(sys.argv[1])); print(d.get("stage2_run_index") or "")
PY
)"

if [[ "$eligible" != "true" ]]; then
  echo "stage2_not_eligible; normal evening validation should continue via repo adapter"
  exit 0
fi

RUN_DIR="$PRIVATE_RUNTIME/stage2/$target_month/run_$(printf '%02d' "$run_index")"
mkdir -p "$RUN_DIR"

set +e
SOURCE_STATUS_JSON="$(python3 "$SKILL_DIR/scripts/resolve_stage2_source.py" \
  --target-month "$target_month" \
  --run-index "$run_index" \
  --run-dir "$RUN_DIR" \
  --repo-root "$REPO_ROOT" \
  --source-mode "${KMFA_STAGE2_SOURCE_MODE:-auto}" \
  --source-json "${KMFA_STAGE2_SOURCE_JSON:-}" \
  --print-json)"
SOURCE_STATUS_CODE=$?
set -e
SOURCE_STATUS="$(python3 - <<'PY' "$SOURCE_STATUS_JSON"
import json, sys
print(json.loads(sys.argv[1]).get("status", ""))
PY
)"
SOURCE_JSON="$(python3 - <<'PY' "$SOURCE_STATUS_JSON"
import json, sys
print(json.loads(sys.argv[1]).get("source_json", ""))
PY
)"

if [[ "$SOURCE_STATUS_CODE" != "0" || "$SOURCE_STATUS" != "READY" ]]; then
  echo "STAGE2_ADAPTER_SOURCE_MISSING: $(python3 - <<'PY' "$SOURCE_STATUS_JSON"
import json, sys
print(json.loads(sys.argv[1]).get("failure_reason", "stage-2 source unavailable"))
PY
)" >&2
  exit 2
fi

python3 "$SKILL_DIR/scripts/write_stage2_run_artifacts.py" \
  --source-json "$SOURCE_JSON" \
  --out-dir "$RUN_DIR" \
  --target-month "$target_month" \
  --run-index "$run_index"

if [[ "$run_index" == "5" ]]; then
  python3 "$SKILL_DIR/scripts/stage2_consensus_gate.py" \
    --stage2-root "$PRIVATE_RUNTIME/stage2/$target_month" \
    --target-month "$target_month" \
    --min-quality Q4
fi
