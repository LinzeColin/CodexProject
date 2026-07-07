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

cat > "$RUN_DIR/README.TODO.txt" <<TXT
This folder is reserved for stage-2 run $run_index of $target_month.
The repo-specific adapter must write:
  run_manifest.json
  canonical_snapshot.json
  canonical_snapshot.sha256
  quality_report.json
  exception_report.json
  payroll_baseline_candidate.json
TXT

# TODO: replace this adapter call with the actual KMFA command once wired in repo.
# Example shape:
#   python -m kmfa.dingtalk_attendance run-monthly-stage2 \
#     --target-month "$target_month" \
#     --run-index "$run_index" \
#     --out-dir "$RUN_DIR" \
#     --require-location-evidence \
#     --write-db \
#     --canonicalize

if [[ "$run_index" == "5" ]]; then
  python3 "$SKILL_DIR/scripts/stage2_consensus_gate.py" \
    --stage2-root "$PRIVATE_RUNTIME/stage2/$target_month" \
    --target-month "$target_month" \
    --min-quality Q4
fi
