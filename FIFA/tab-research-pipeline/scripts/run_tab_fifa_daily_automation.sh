#!/usr/bin/env bash
set -u
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${PIPELINE_DIR}/../.." && pwd)"
OUTPUT_DIR="${TAB_FIFA_OUTPUT_DIR:-${WORKSPACE_ROOT}/outputs}"
PRIVATE_DIR="${TAB_FIFA_PRIVATE_DIR:-${WORKSPACE_ROOT}/work/private/tab_fifa}"
LOG_DIR="${TAB_FIFA_LOG_DIR:-${PRIVATE_DIR}/automation_run_logs}"
RUN_STAMP="$(date -u +"%Y%m%dT%H%M%SZ")-$$"
STDOUT_LOG="${LOG_DIR}/tab_fifa_daily_${RUN_STAMP}.stdout.log"
STDERR_LOG="${LOG_DIR}/tab_fifa_daily_${RUN_STAMP}.stderr.log"
SUMMARY_JSON="${LOG_DIR}/tab_fifa_daily_${RUN_STAMP}.summary.json"
LATEST_SUMMARY_JSON="${OUTPUT_DIR}/automation_run_latest.json"
MODE="daily"
VERIFY_MODE="${TAB_FIFA_VERIFY_MODE:-hermetic}"
CAPTURE_MY_BETS="${TAB_FIFA_CAPTURE_MY_BETS:-0}"
ALLOW_RESEARCH_ONLY_SUCCESS="${TAB_FIFA_ALLOW_RESEARCH_ONLY_SUCCESS:-0}"
REPORT_DATE="${TAB_FIFA_REPORT_DATE:-}"
MY_BETS_WAIT_FOR_LOGIN_MS="${TAB_FIFA_MY_BETS_WAIT_FOR_LOGIN_MS:-0}"
MY_BETS_TIMEOUT_MS="${TAB_FIFA_MY_BETS_TIMEOUT_MS:-45000}"
MY_BETS_CHROME_PROFILE_DIR="${TAB_FIFA_CHROME_USER_DATA_DIR:-${PRIVATE_DIR}/tab_chrome_profile}"
RUNNER_LOCK_DIR="${TAB_FIFA_RUNNER_LOCK_DIR:-${PRIVATE_DIR}/.tab_fifa_daily_runner.lock}"
RUNNER_LOCK_HELD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --verify-only)
      MODE="verify-only"
      shift
      ;;
    --capture-my-bets)
      CAPTURE_MY_BETS="1"
      shift
      ;;
    --allow-research-only-success)
      ALLOW_RESEARCH_ONLY_SUCCESS="1"
      shift
      ;;
    --report-date)
      if [[ $# -lt 2 ]]; then
        echo "--report-date requires DDMMYYYY" >&2
        exit 2
      fi
      REPORT_DATE="${2:-}"
      shift 2
      ;;
    --wait-for-login-ms)
      if [[ $# -lt 2 ]]; then
        echo "--wait-for-login-ms requires a millisecond value" >&2
        exit 2
      fi
      MY_BETS_WAIT_FOR_LOGIN_MS="${2:-0}"
      shift 2
      ;;
    --help|-h)
  cat <<'EOF'
Usage:
  scripts/run_tab_fifa_daily_automation.sh
  scripts/run_tab_fifa_daily_automation.sh --verify-only
  scripts/run_tab_fifa_daily_automation.sh --allow-research-only-success
  scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY
  scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY --wait-for-login-ms 600000

Runs the local TAB FIFA report pipeline once. It does not create a recurring
automation, log in on your behalf, interact with wagering controls, add selections to Bet Slip,
or place bets.

Environment:
  TAB_FIFA_REFRESH_RAW=1           Request live TAB raw refresh before report; TAB AI controlled access rejection remains fail-closed.
  TAB_FIFA_REFRESH_RAW=reuse_fresh Reuse fresh valid raw snapshots if possible.
  TAB_FIFA_HEADLESS=0              Private My Bets login/bootstrap only; never a public raw fallback.
  TAB_FIFA_CAPTURE_MY_BETS=1       Before the report, read TAB My Bets through the private read-only chain.
  TAB_FIFA_ALLOW_RESEARCH_ONLY_SUCCESS=1
                                   Treat a fresh partial_daily_research PDF as a successful research-only run
                                   when the formal daily report fails closed. Formal report gates remain blocked.
  TAB_FIFA_REPORT_DATE=DDMMYYYY    Report date for My Bets capture/import.
  TAB_FIFA_VERIFY_MODE=hermetic    Verifier mode for --verify-only: hermetic, artifact-chain-only,
                                   live-artifacts, or full. Defaults to hermetic.
  TAB_FIFA_MY_BETS_WAIT_FOR_LOGIN_MS=0
                                   Optional headed bootstrap wait window for a reusable private profile.
  TAB_FIFA_OUTPUT_DIR=path         Write public latest summary to this directory.
  TAB_FIFA_LOG_DIR=path            Write private runner logs to this directory.
EOF
  exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: scripts/run_tab_fifa_daily_automation.sh [--verify-only] [--allow-research-only-success] [--capture-my-bets] [--report-date DDMMYYYY] [--wait-for-login-ms MS]" >&2
      exit 2
      ;;
  esac
done

if [[ -n "${REPORT_DATE}" && ! "${REPORT_DATE}" =~ ^[0-9]{8}$ ]]; then
  echo "report date must use DDMMYYYY format" >&2
  exit 2
fi
if [[ ! "${MY_BETS_WAIT_FOR_LOGIN_MS}" =~ ^[0-9]+$ ]]; then
  echo "TAB_FIFA_MY_BETS_WAIT_FOR_LOGIN_MS/--wait-for-login-ms must be a non-negative integer" >&2
  exit 2
fi
if [[ ! "${MY_BETS_TIMEOUT_MS}" =~ ^[0-9]+$ || "${MY_BETS_TIMEOUT_MS}" -le 0 ]]; then
  echo "TAB_FIFA_MY_BETS_TIMEOUT_MS must be a positive integer" >&2
  exit 2
fi
VERIFY_MODE="${VERIFY_MODE#--}"
case "${VERIFY_MODE}" in
  full|hermetic|live-artifacts|artifact-chain-only) ;;
  *)
    echo "TAB_FIFA_VERIFY_MODE must be one of: hermetic, artifact-chain-only, live-artifacts, full" >&2
    exit 2
    ;;
esac
if [[ "${MODE}" == "verify-only" ]]; then
  CAPTURE_MY_BETS="0"
fi

release_runner_lock() {
  if [[ "${RUNNER_LOCK_HELD}" == "1" ]]; then
    rm -f "${RUNNER_LOCK_DIR}/pid" "${RUNNER_LOCK_DIR}/started_at" "${RUNNER_LOCK_DIR}/mode" 2>/dev/null || true
    rmdir "${RUNNER_LOCK_DIR}" 2>/dev/null || true
    RUNNER_LOCK_HELD=0
  fi
}

acquire_runner_lock() {
  mkdir -p "$(dirname "${RUNNER_LOCK_DIR}")"
  if mkdir "${RUNNER_LOCK_DIR}" 2>/dev/null; then
    RUNNER_LOCK_HELD=1
    printf '%s\n' "$$" >"${RUNNER_LOCK_DIR}/pid"
    date -u +"%Y-%m-%dT%H:%M:%SZ" >"${RUNNER_LOCK_DIR}/started_at"
    printf '%s\n' "${MODE}" >"${RUNNER_LOCK_DIR}/mode"
    trap release_runner_lock EXIT INT TERM
    return 0
  fi
  local lock_pid=""
  if [[ -f "${RUNNER_LOCK_DIR}/pid" ]]; then
    lock_pid="$(cat "${RUNNER_LOCK_DIR}/pid" 2>/dev/null || true)"
  fi
  if [[ "${lock_pid}" =~ ^[0-9]+$ ]] && kill -0 "${lock_pid}" 2>/dev/null; then
    echo "another TAB FIFA automation runner is active: pid=${lock_pid}; lock=${RUNNER_LOCK_DIR}" >&2
    exit 75
  fi
  rm -f "${RUNNER_LOCK_DIR}/pid" "${RUNNER_LOCK_DIR}/started_at" "${RUNNER_LOCK_DIR}/mode" 2>/dev/null || true
  rmdir "${RUNNER_LOCK_DIR}" 2>/dev/null || {
    echo "stale TAB FIFA automation runner lock could not be cleared: ${RUNNER_LOCK_DIR}" >&2
    exit 75
  }
  mkdir "${RUNNER_LOCK_DIR}" || {
    echo "another TAB FIFA automation runner became active: lock=${RUNNER_LOCK_DIR}" >&2
    exit 75
  }
  RUNNER_LOCK_HELD=1
  printf '%s\n' "$$" >"${RUNNER_LOCK_DIR}/pid"
  date -u +"%Y-%m-%dT%H:%M:%SZ" >"${RUNNER_LOCK_DIR}/started_at"
  printf '%s\n' "${MODE}" >"${RUNNER_LOCK_DIR}/mode"
  trap release_runner_lock EXIT INT TERM
}

mkdir -p "${LOG_DIR}"
mkdir -p "${OUTPUT_DIR}"
cd "${PIPELINE_DIR}" || exit 2

acquire_runner_lock
STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EXIT_CODE=0
MY_BETS_CAPTURE_EXIT_CODE=0
MY_BETS_IMPORT_EXIT_CODE=0
MY_BETS_CAPTURE_LOG=""
MY_BETS_IMPORT_LOG=""
MY_BETS_RAW_SEEN=0
MY_BETS_RAW_FRESH=0
MY_BETS_RAW_SCRAPED_AT=""
MY_BETS_IMPORT_SKIPPED_REASON=""

truthy() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_node_bin() {
  if [[ -n "${TAB_FIFA_NODE_BIN:-}" ]]; then
    printf '%s\n' "${TAB_FIFA_NODE_BIN}"
    return 0
  fi
  local bundled_node="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
  if [[ -x "${bundled_node}" ]]; then
    printf '%s\n' "${bundled_node}"
    return 0
  fi
  if command -v node >/dev/null 2>&1; then
    command -v node
    return 0
  fi
  return 1
}

if truthy "${CAPTURE_MY_BETS}" && [[ "${MODE}" != "verify-only" ]]; then
  if [[ -z "${REPORT_DATE}" ]]; then
    REPORT_DATE="$(TZ=Australia/Sydney date +"%d%m%Y")"
  fi
  MY_BETS_CAPTURE_LOG="${LOG_DIR}/tab_fifa_my_bets_capture_${RUN_STAMP}.log"
  MY_BETS_IMPORT_LOG="${LOG_DIR}/tab_fifa_my_bets_import_${RUN_STAMP}.log"
  NODE_BIN="$(resolve_node_bin)" || {
    echo "node runtime not found for My Bets capture" >"${MY_BETS_CAPTURE_LOG}"
    MY_BETS_CAPTURE_EXIT_CODE=127
  }
  if [[ "${MY_BETS_CAPTURE_EXIT_CODE}" -eq 0 ]]; then
    CAPTURE_CMD=(
      "${NODE_BIN}"
      scripts/capture_tab_my_bets_readonly.mjs
      --output-dir "${PRIVATE_DIR}"
      --chrome-user-data-dir "${MY_BETS_CHROME_PROFILE_DIR}"
      --report-date "${REPORT_DATE}"
      --timeout-ms "${MY_BETS_TIMEOUT_MS}"
    )
    if [[ "${MY_BETS_WAIT_FOR_LOGIN_MS}" != "0" ]]; then
      CAPTURE_CMD+=(--wait-for-login-ms "${MY_BETS_WAIT_FOR_LOGIN_MS}")
    fi
    "${CAPTURE_CMD[@]}" >"${MY_BETS_CAPTURE_LOG}" 2>&1 || MY_BETS_CAPTURE_EXIT_CODE=$?
	  fi
	  RAW_MY_BETS="${PRIVATE_DIR}/tab_my_bets_raw_${REPORT_DATE}.txt"
	  if [[ "${MY_BETS_CAPTURE_EXIT_CODE}" -ne 0 ]]; then
	    MY_BETS_IMPORT_SKIPPED_REASON="capture_failed"
	    printf 'private My Bets import skipped because capture failed with exit code %s\n' "${MY_BETS_CAPTURE_EXIT_CODE}" >"${MY_BETS_IMPORT_LOG}"
	  elif [[ ! -s "${RAW_MY_BETS}" ]]; then
	    MY_BETS_IMPORT_SKIPPED_REASON="raw_text_missing"
	    printf 'private My Bets raw text not available for %s\n' "${REPORT_DATE}" >"${MY_BETS_IMPORT_LOG}"
	  elif MY_BETS_RAW_SCRAPED_AT="$(python3 - "${RAW_MY_BETS}" "${STARTED_AT}" <<'PY'
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
started_at = datetime.fromisoformat(sys.argv[2].replace("Z", "+00:00"))
mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
if mtime < started_at:
    raise SystemExit(3)
print(mtime.isoformat().replace("+00:00", "Z"))
PY
	  )"; then
	    MY_BETS_RAW_SEEN=1
	    MY_BETS_RAW_FRESH=1
	    python3 import_my_bets_snapshot.py \
	      --source "${RAW_MY_BETS}" \
	      --report-date "${REPORT_DATE}" \
	      --private-dir "${PRIVATE_DIR}" \
	      --scraped-at "${MY_BETS_RAW_SCRAPED_AT}" \
	      >"${MY_BETS_IMPORT_LOG}" 2>&1 || MY_BETS_IMPORT_EXIT_CODE=$?
	  else
	    MY_BETS_IMPORT_SKIPPED_REASON="raw_text_stale"
	    printf 'private My Bets import skipped because raw text for %s is older than this runner start\n' "${REPORT_DATE}" >"${MY_BETS_IMPORT_LOG}"
	  fi
	fi
export TAB_FIFA_RUN_CAPTURE_MY_BETS="${CAPTURE_MY_BETS}"
export TAB_FIFA_RUN_MY_BETS_REPORT_DATE="${REPORT_DATE}"
export TAB_FIFA_RUN_MY_BETS_WAIT_FOR_LOGIN_MS="${MY_BETS_WAIT_FOR_LOGIN_MS}"
export TAB_FIFA_RUN_MY_BETS_CAPTURE_EXIT_CODE="${MY_BETS_CAPTURE_EXIT_CODE}"
export TAB_FIFA_RUN_MY_BETS_IMPORT_EXIT_CODE="${MY_BETS_IMPORT_EXIT_CODE}"
export TAB_FIFA_RUN_MY_BETS_RAW_SEEN="${MY_BETS_RAW_SEEN}"
export TAB_FIFA_RUN_MY_BETS_RAW_FRESH="${MY_BETS_RAW_FRESH}"
export TAB_FIFA_RUN_MY_BETS_RAW_SCRAPED_AT="${MY_BETS_RAW_SCRAPED_AT}"
export TAB_FIFA_RUN_MY_BETS_IMPORT_SKIPPED_REASON="${MY_BETS_IMPORT_SKIPPED_REASON}"
export TAB_FIFA_RUN_MY_BETS_CAPTURE_LOG="${MY_BETS_CAPTURE_LOG}"
export TAB_FIFA_RUN_MY_BETS_IMPORT_LOG="${MY_BETS_IMPORT_LOG}"
export TAB_FIFA_RUN_VERIFY_MODE="${VERIFY_MODE}"
export TAB_FIFA_RUN_ALLOW_RESEARCH_ONLY_SUCCESS="${ALLOW_RESEARCH_ONLY_SUCCESS}"

if [[ "${MODE}" == "verify-only" ]]; then
  "${SCRIPT_DIR}/verify_fifa_automation_readiness.sh" "--${VERIFY_MODE}" >"${STDOUT_LOG}" 2>"${STDERR_LOG}" || EXIT_CODE=$?
else
  python3 run_daily_report.py >"${STDOUT_LOG}" 2>"${STDERR_LOG}" || EXIT_CODE=$?
fi

FINISHED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

POST_EXIT=0
python3 - "$MODE" "$EXIT_CODE" "$STARTED_AT" "$FINISHED_AT" "$STDOUT_LOG" "$STDERR_LOG" "$SUMMARY_JSON" "$LATEST_SUMMARY_JSON" "$OUTPUT_DIR" <<'PY' || POST_EXIT=$?
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from tab_research.artifacts import sanitize_public_manifest
from tab_research.automation_candidate import write_automation_candidate, write_automation_candidate_pdf, write_automation_candidate_report
from tab_research.automation_config import load_automation_authorization
from tab_research.automation_readiness import write_automation_readiness_pdf, write_automation_readiness_report, write_automation_readiness_summary
from tab_research.report_store import store_automation_run

mode, exit_code_text, started_at, finished_at, stdout_log, stderr_log, summary_json, latest_summary_json, output_dir = sys.argv[1:]
exit_code = int(exit_code_text)
out = Path(output_dir)


def load_json(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def tail(path: Path, limit: int = 4000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-limit:]


def safe_tail(path: Path, limit: int = 4000) -> str:
    return sanitize_public_manifest({"text": tail(path, limit)}).get("text", "")


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


latest_commit = load_json(out / "latest_commit.json")
latest_manifest = load_json(out / "daily_report_manifest_latest.json")
raw_health = load_json(out / "raw_refresh_health_latest.json")
diagnostics = load_json(out / "raw_refresh_diagnostics_latest.json")
partial_daily_research = load_json(out / "partial_daily_research_latest.json")
response = {}
stdout_text = tail(Path(stdout_log), 200000)
if mode == "daily":
    start = stdout_text.find("{")
    end = stdout_text.rfind("}")
    if start >= 0 and end > start:
        try:
            response = json.loads(stdout_text[start : end + 1])
        except json.JSONDecodeError:
            response = {}

current_payload = response if mode == "daily" else latest_commit
automation_authorization = (
    current_payload.get("automation_authorization")
    or latest_commit.get("automation_authorization")
    or load_automation_authorization().to_public_dict()
)
partial_exec = partial_daily_research.get("executive_status") or {}
partial_summary = partial_daily_research.get("summary") or {}
partial_artifacts = partial_daily_research.get("artifacts") or {}
research_only_daily_report_ready = (
    mode == "daily"
    and bool(partial_exec.get("partial_daily_report_ready"))
    and partial_exec.get("execution_allowed") is False
    and int(partial_exec.get("current_executable_new_stake_aud") or 0) == 0
    and bool(partial_summary.get("partial_fresh_within_sla"))
    and bool(partial_artifacts.get("pdf"))
)
allow_research_only_success = str(os.environ.get("TAB_FIFA_RUN_ALLOW_RESEARCH_ONLY_SUCCESS", "")).lower() in {"1", "true", "yes", "y", "on"}
research_only_success_exit_override = bool(exit_code != 0 and allow_research_only_success and research_only_daily_report_ready)
run_status = "ready_for_manual_report" if exit_code == 0 and mode == "daily" else ("verified" if exit_code == 0 else "failed")
if research_only_daily_report_ready and exit_code != 0 and mode == "daily":
    run_status = "research_only_report_ready"
summary = {
    "schema_version": 1,
    "mode": mode,
    "verify_mode": os.environ.get("TAB_FIFA_RUN_VERIFY_MODE", ""),
    "status": run_status,
    "exit_code": exit_code,
    "formal_exit_code": exit_code,
    "effective_exit_code": 0 if research_only_success_exit_override else exit_code,
    "allow_research_only_success": allow_research_only_success,
    "research_only_success_exit_override": research_only_success_exit_override,
    "started_at": started_at,
    "finished_at": finished_at,
    "stdout_log": Path(stdout_log).name,
    "stderr_log": Path(stderr_log).name,
    "run_id": response.get("run_id") if mode == "daily" else (latest_commit.get("run_id") or latest_manifest.get("run_id")),
    "latest_commit_status": latest_commit.get("status"),
    "technical_automation_ready": bool(current_payload.get("technical_automation_ready")) if exit_code == 0 else False,
    "automation_entry_ready": bool(current_payload.get("automation_entry_ready")) if exit_code == 0 else False,
    "automation_authorization": automation_authorization if exit_code == 0 else {},
    "public_artifact_safety_ready": bool(current_payload.get("public_artifact_safety_ready")) if exit_code == 0 else False,
    "ready_required_boards": current_payload.get("ready_required_boards") if exit_code == 0 else None,
    "time_adjusted_new_exposure_aud": current_payload.get("time_adjusted_new_exposure_aud") if exit_code == 0 else None,
    "raw_refresh_status": raw_health.get("status") if exit_code == 0 or mode == "verify-only" or research_only_daily_report_ready else None,
    "raw_refresh_ready": bool(raw_health.get("ready")) if exit_code == 0 or mode == "verify-only" or research_only_daily_report_ready else False,
    "raw_refresh_blocker_codes": raw_health.get("blocker_codes", []) if exit_code == 0 or mode == "verify-only" or research_only_daily_report_ready else [],
    "raw_refresh_diagnostics_status": diagnostics.get("status") if exit_code == 0 or mode == "verify-only" or research_only_daily_report_ready else None,
    "raw_refresh_heartbeat_count": diagnostics.get("heartbeat_count") if exit_code == 0 or mode == "verify-only" or research_only_daily_report_ready else None,
    "research_only_daily_report_ready": research_only_daily_report_ready,
    "partial_daily_research": {
        "status": partial_exec.get("status", "missing") if partial_daily_research else "missing",
        "ready": research_only_daily_report_ready,
        "report_date": partial_daily_research.get("report_date", ""),
        "generated_at": partial_daily_research.get("generated_at", ""),
        "partial_successful_board_count": int(partial_summary.get("partial_successful_board_count") or 0),
        "partial_attempted_board_count": int(partial_summary.get("partial_attempted_board_count") or 0),
        "unavailable_board_count": int(partial_summary.get("unavailable_board_count") or 0),
        "board_scope_source": partial_summary.get("board_scope_source", ""),
        "current_executable_new_stake_aud": int(partial_exec.get("current_executable_new_stake_aud") or 0),
        "execution_allowed": bool(partial_exec.get("execution_allowed")),
        "pdf_report": str(partial_artifacts.get("pdf", "")),
        "dated_pdf_report": str(partial_artifacts.get("dated_pdf", "")),
    },
    "pdf_report": Path(response.get("downloads_pdf_copy") or response.get("pdf_latest_copy") or "").name,
    "dashboard": Path(response.get("dashboard_latest") or response.get("dashboard") or "").name,
    "database": "tab_fifa_reports.sqlite3" if (out / "tab_fifa_reports.sqlite3").exists() else "",
    "last_success": {
        "run_id": latest_commit.get("run_id"),
        "status": latest_commit.get("status"),
        "technical_automation_ready": bool(latest_commit.get("technical_automation_ready")),
        "automation_entry_ready": bool(latest_commit.get("automation_entry_ready")),
        "automation_authorization": latest_commit.get("automation_authorization") or {},
        "ready_required_boards": latest_commit.get("ready_required_boards"),
        "time_adjusted_new_exposure_aud": latest_commit.get("time_adjusted_new_exposure_aud"),
    },
    "stderr_tail": safe_tail(Path(stderr_log), 1200),
}
my_bets_capture = {
    "enabled": str(os.environ.get("TAB_FIFA_RUN_CAPTURE_MY_BETS", "")).lower() in {"1", "true", "yes", "y", "on"},
    "report_date": os.environ.get("TAB_FIFA_RUN_MY_BETS_REPORT_DATE", ""),
    "wait_for_login_ms": int(os.environ.get("TAB_FIFA_RUN_MY_BETS_WAIT_FOR_LOGIN_MS") or 0),
    "capture_exit_code": int(os.environ.get("TAB_FIFA_RUN_MY_BETS_CAPTURE_EXIT_CODE") or 0),
    "import_exit_code": int(os.environ.get("TAB_FIFA_RUN_MY_BETS_IMPORT_EXIT_CODE") or 0),
    "raw_text_seen": os.environ.get("TAB_FIFA_RUN_MY_BETS_RAW_SEEN") == "1",
    "raw_text_fresh": os.environ.get("TAB_FIFA_RUN_MY_BETS_RAW_FRESH") == "1",
    "raw_scraped_at": os.environ.get("TAB_FIFA_RUN_MY_BETS_RAW_SCRAPED_AT") or "",
    "import_skipped_reason": os.environ.get("TAB_FIFA_RUN_MY_BETS_IMPORT_SKIPPED_REASON") or "",
    "capture_log": Path(os.environ.get("TAB_FIFA_RUN_MY_BETS_CAPTURE_LOG") or "").name,
    "import_log": Path(os.environ.get("TAB_FIFA_RUN_MY_BETS_IMPORT_LOG") or "").name,
}
summary["my_bets_capture"] = my_bets_capture

post_run_persistence_failed = False
try:
    candidate = write_automation_candidate(out, out / "automation_candidate_latest.json")
    candidate_report = write_automation_candidate_report(out, out / "automation_candidate_latest.md", candidate=candidate)
    candidate_pdf = write_automation_candidate_pdf(out, out / "automation_candidate_latest.pdf", candidate=candidate)
    summary["automation_candidate"] = {
        "status": candidate.get("status"),
        "candidate_ready": candidate.get("candidate_ready"),
        "installed": candidate.get("installed"),
        "recommended_cadence": candidate.get("recommended_cadence"),
        "artifact": "automation_candidate_latest.json",
        "report_artifact": "automation_candidate_latest.md",
        "pdf_artifact": "automation_candidate_latest.pdf",
        "report_mermaid_blocks": candidate_report.get("mermaid_blocks", 0),
        "pdf_chart_count": candidate_pdf.get("chart_count", 0),
    }
    readiness = write_automation_readiness_summary(
        out,
        out / "automation_readiness_latest.json",
        command_status={
            "mode": mode,
            "exit_code": exit_code,
            "formal_exit_code": exit_code,
            "effective_exit_code": 0 if research_only_success_exit_override else exit_code,
            "status": summary["status"],
            "research_only_daily_report_ready": research_only_daily_report_ready,
            "research_only_success_exit_override": research_only_success_exit_override,
            "started_at": started_at,
            "finished_at": finished_at,
            "my_bets_capture": my_bets_capture,
        },
    )
    readiness_report = write_automation_readiness_report(
        out,
        out / "automation_readiness_latest.md",
        summary=readiness,
    )
    readiness_pdf = write_automation_readiness_pdf(
        out,
        out / "automation_readiness_latest.pdf",
        summary=readiness,
    )
    summary["automation_readiness"] = {
        "status": readiness.get("status"),
        "formal_report_publish_ready": readiness.get("formal_report_publish_ready"),
        "recurring_automation_ready": readiness.get("recurring_automation_ready"),
        "research_only_daily_report_ready": readiness.get("research_only_daily_report_ready"),
        "research_only_recurring_candidate_ready": readiness.get("research_only_recurring_candidate_ready"),
        "blocking_reasons": readiness.get("blocking_reasons", []),
        "research_only_daily_report": readiness.get("research_only_daily_report", {}),
        "private_position_bootstrap": readiness.get("private_position_bootstrap", {}),
        "artifact": "automation_readiness_latest.json",
        "report_artifact": "automation_readiness_latest.md",
        "pdf_artifact": "automation_readiness_latest.pdf",
        "report_mermaid_blocks": readiness_report.get("mermaid_blocks", 0),
        "pdf_chart_count": readiness_pdf.get("chart_count", 0),
    }
except Exception as exc:
    post_run_persistence_failed = True
    summary["automation_readiness"] = {
        "status": "summary_failed",
        "formal_report_publish_ready": False,
        "recurring_automation_ready": False,
        "blocking_reasons": [f"{type(exc).__name__}: {exc}"],
        "artifact": "",
    }

try:
    db_path = out / "tab_fifa_reports.sqlite3"
    summary["automation_run_store"] = store_automation_run(db_path, summary)
except Exception as exc:
    post_run_persistence_failed = True
    summary["automation_run_store"] = {
        "status": "store_failed",
        "error": f"{type(exc).__name__}: {exc}",
    }

for target in [Path(summary_json), Path(latest_summary_json)]:
    atomic_write_json(target, sanitize_public_manifest(summary))

print(json.dumps(summary, indent=2, ensure_ascii=False))
if post_run_persistence_failed:
    raise SystemExit(5)
PY
	
if [[ "${POST_EXIT}" -ne 0 ]]; then
  exit "${POST_EXIT}"
fi
if truthy "${ALLOW_RESEARCH_ONLY_SUCCESS}" && [[ "${MODE}" == "daily" && "${EXIT_CODE}" -ne 0 ]]; then
  if python3 - "$OUTPUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "automation_run_latest.json"
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if payload.get("research_only_success_exit_override") is True and payload.get("research_only_daily_report_ready") is True:
    raise SystemExit(0)
raise SystemExit(1)
PY
  then
    exit 0
  fi
fi
exit "${EXIT_CODE}"
