#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$ROOT/../.." && pwd)"
OUTPUT_DIR="${TAB_FIFA_OUTPUT_DIR:-$PROJECT_ROOT/outputs}"
MODE="${TAB_FIFA_VERIFY_MODE:-full}"
if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [--full|--hermetic|--live-artifacts|--artifact-chain-only]" >&2
  exit 2
fi
if [[ $# -eq 1 ]]; then
  case "$1" in
    --full) MODE="full" ;;
    --hermetic) MODE="hermetic" ;;
    --live-artifacts) MODE="live-artifacts" ;;
    --artifact-chain-only) MODE="artifact-chain-only" ;;
    -h|--help)
      echo "Usage: $0 [--full|--hermetic|--live-artifacts|--artifact-chain-only]"
      echo "  --hermetic       Run code, fixture, dry-run, and readonly security checks only."
      echo "  --live-artifacts Run current outputs/latest/raw safety checks plus latest attempted technical preflight."
      echo "  --artifact-chain-only Run the narrower historical latest/raw/public artifact checks only."
      echo "  --full           Run both hermetic and strict live artifact/preflight checks. Default."
      exit 0
      ;;
    *)
      echo "Unknown mode: $1" >&2
      echo "Usage: $0 [--full|--hermetic|--live-artifacts|--artifact-chain-only]" >&2
      exit 2
      ;;
  esac
fi
case "$MODE" in
  full|hermetic|live-artifacts|artifact-chain-only) ;;
  *)
    echo "Unknown TAB_FIFA_VERIFY_MODE: $MODE" >&2
    echo "Use full, hermetic, live-artifacts, or artifact-chain-only." >&2
    exit 2
    ;;
esac
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONOPTIMIZE

TMP_REFRESH="$(mktemp -t tab_fifa_refresh_dry_run.XXXXXX.json)"
TMP_DISCOVERY="$(mktemp -t tab_fifa_live_board_discovery_dry_run.XXXXXX.json)"
TMP_SMOKE_STDOUT="$(mktemp -t tab_fifa_real_refresh_smoke_dry_run.XXXXXX.json)"
TMP_SMOKE_SUMMARY="$(mktemp -t tab_fifa_real_refresh_smoke_summary.XXXXXX.json)"
trap 'rm -f "$TMP_REFRESH" "$TMP_DISCOVERY" "$TMP_SMOKE_STDOUT" "$TMP_SMOKE_SUMMARY"' EXIT

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

if [[ "$MODE" != "live-artifacts" && "$MODE" != "artifact-chain-only" ]]; then
echo "[1/8] Dependency manifest check"
python3 - <<'PY'
import json
from pathlib import Path

requirements = Path("requirements.txt").read_text(encoding="utf-8")
if "reportlab==" not in requirements:
    raise SystemExit("requirements.txt missing pinned reportlab dependency")
if "pypdf==" not in requirements:
    raise SystemExit("requirements.txt missing pinned pypdf dependency")
if "PyMuPDF==" not in requirements:
    raise SystemExit("requirements.txt missing pinned PyMuPDF dependency")
if "Pillow==" not in requirements:
    raise SystemExit("requirements.txt missing pinned Pillow dependency")
package = json.loads(Path("package.json").read_text(encoding="utf-8"))
if not package.get("dependencies", {}).get("playwright"):
    raise SystemExit("package.json missing playwright dependency")
PY

echo "[2/8] Python syntax check"
python3 - <<'PY'
from pathlib import Path

for path in sorted(Path(".").glob("**/*.py")):
    if "__pycache__" in path.parts:
        continue
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
PY

echo "[3/8] Python unit/integration fixture tests"
python3 -m unittest discover -s tests -p 'test*.py' -v

echo "[4/8] TAB readonly refresh script syntax"
"$NODE_BIN" --check scripts/refresh_tab_readonly.mjs
"$NODE_BIN" --check scripts/discover_tab_live_boards.mjs
"$NODE_BIN" --check scripts/capture_tab_my_bets_readonly.mjs

echo "[5/8] TAB readonly refresh offline security tests"
"$NODE_BIN" scripts/refresh_tab_readonly_security.test.mjs
"$NODE_BIN" scripts/capture_tab_my_bets_readonly_security.test.mjs

echo "[6/8] TAB readonly refresh dry-run contract"
TAB_FIFA_NODE_MODULES="${TAB_FIFA_NODE_MODULES:-/tmp/missing-tab-fifa-node-modules}" \
  "$NODE_BIN" scripts/refresh_tab_readonly.mjs --dry-run --board matches --refresh-id verify-readiness >"$TMP_REFRESH"
TAB_FIFA_NODE_MODULES="${TAB_FIFA_NODE_MODULES:-/tmp/missing-tab-fifa-node-modules}" \
  "$NODE_BIN" scripts/discover_tab_live_boards.mjs --dry-run --output-dir /tmp/tab-fifa-live-discovery >"$TMP_DISCOVERY"
python3 - "$TMP_REFRESH" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
if payload.get("dry_run") is not True:
    raise SystemExit("dry-run contract did not report dry_run=true")
if payload.get("refresh_id") != "verify-readiness":
    raise SystemExit("dry-run contract returned wrong refresh_id")
boards = payload.get("boards") or []
if not boards or boards[0].get("board_id") != "matches":
    raise SystemExit("dry-run contract returned wrong board")
if not str(boards[0].get("output", "")).endswith(".json"):
    raise SystemExit("dry-run contract output is not a JSON artifact")
PY
python3 - "$TMP_DISCOVERY" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
if payload.get("dry_run") is not True:
    raise SystemExit("discovery dry-run contract did not report dry_run=true")
if not str(payload.get("output", "")).endswith("tab_fifa_live_board_discovery_raw_latest.json"):
    raise SystemExit("discovery dry-run output is not the expected JSON artifact")
expected = payload.get("expected_boards") or []
if not any(row.get("refresh_board_id") == "australia_markets" for row in expected):
    raise SystemExit("discovery dry-run missing australia_markets expected board")
PY

echo "[7/8] Real TAB refresh smoke dry-run"
TAB_FIFA_SMOKE_SUMMARY_FILE="$TMP_SMOKE_SUMMARY" scripts/tab_real_refresh_smoke.sh --dry-run >"$TMP_SMOKE_STDOUT"
python3 - "$TMP_SMOKE_STDOUT" "$TMP_SMOKE_SUMMARY" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
summary = json.loads(Path(sys.argv[2]).read_text())
if payload.get("mode") != "dry-run":
    raise SystemExit("smoke dry-run mode mismatch")
if payload.get("ready") is not True:
    raise SystemExit("smoke dry-run did not report ready=true")
stdout = payload.get("stdout") or {}
if stdout.get("dry_run") is not True:
    raise SystemExit("smoke stdout dry_run=true missing")
if stdout.get("smoke") is not True:
    raise SystemExit("smoke stdout smoke=true missing")
if payload.get("refresh_id") != summary.get("refresh_id"):
    raise SystemExit("smoke refresh_id summary mismatch")
if not all("/" not in part for part in payload.get("command", [])):
    raise SystemExit("smoke command leaked a local path")
PY
fi

if [[ "$MODE" == "hermetic" ]]; then
  echo "OK: FIFA automation readiness hermetic verification passed."
  exit 0
fi

echo "[8/8] Report artifact safety and preflight scan"
python3 - "$OUTPUT_DIR" "$MODE" <<'PY'
import json
import sys
from pathlib import Path
from tab_research.automation_readiness import load_latest_attempt_preflight, technical_preflight_publication_blocker
from tab_research.latest_commit import latest_commit_artifact_consistency_issues
from tab_research.raw_refresh import audit_raw_refresh
from tab_research.safety import audit_output_safety, audit_public_artifact_safety

output_dir = Path(sys.argv[1])
mode = sys.argv[2]
output_gate = audit_output_safety(output_dir)
if not output_gate["automation_safety_ready"]:
    raise SystemExit("outputs safety gate failed: " + "; ".join(output_gate["blocking_reasons"]))

raw_gate = audit_raw_refresh(output_dir)
if not raw_gate["raw_refresh_ready"]:
    raise SystemExit("raw refresh gate failed: " + "; ".join(raw_gate["blocking_reasons"]))

latest_commit = output_dir / "latest_commit.json"
if not latest_commit.exists():
    raise SystemExit(f"latest_commit.json missing in {output_dir}")
payload = json.loads(latest_commit.read_text(encoding="utf-8"))
if payload.get("status") != "ready_for_manual_report":
    raise SystemExit(f"latest_commit status is not ready_for_manual_report: {payload.get('status')}")
if payload.get("technical_automation_ready") is not True:
    raise SystemExit("latest_commit technical_automation_ready is not true")
if payload.get("public_artifact_safety_ready") is not True:
    raise SystemExit("latest_commit public_artifact_safety_ready is not true")
if payload.get("ready_required_boards") != "5/5":
    raise SystemExit(f"latest_commit ready_required_boards is not 5/5: {payload.get('ready_required_boards')}")
consistency_issues = latest_commit_artifact_consistency_issues(payload)
if consistency_issues:
    raise SystemExit("latest_commit artifact consistency failed: " + "; ".join(consistency_issues))
artifact_names = set()
for section in ["artifacts", "run_artifacts"]:
    for value in (payload.get(section) or {}).values():
        if value:
            artifact_names.add(str(value))
required = {
    "pdf_run_copy",
    "bankroll_plan_run_copy",
    "dashboard_run_copy",
    "dashboard_data_run_copy",
    "manifest",
}
missing_required = [key for key in sorted(required) if not (payload.get("run_artifacts") or {}).get(key)]
if missing_required:
    raise SystemExit("latest_commit missing required run artifacts: " + ", ".join(missing_required))
artifact_paths = [output_dir / name for name in sorted(artifact_names)]
public_gate = audit_public_artifact_safety(artifact_paths)
if not public_gate["public_artifact_safety_ready"]:
    raise SystemExit("public artifact safety gate failed: " + "; ".join(public_gate["blocking_reasons"]))
if mode != "artifact-chain-only":
    preflight = load_latest_attempt_preflight(output_dir)
    if technical_preflight_publication_blocker(preflight, payload):
        run_id = preflight.get("run_id") or "unknown"
        reasons = "; ".join(preflight.get("blocking_reasons") or []) or "technical preflight failed"
        raise SystemExit(f"latest attempted technical preflight failed for {run_id}: {reasons}")
PY

echo "OK: FIFA automation readiness verification passed."
