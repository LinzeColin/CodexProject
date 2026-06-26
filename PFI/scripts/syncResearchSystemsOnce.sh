#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AI_ROOT="${RESEARCH_BUS_AI_ROOT:-$PFI_AI_RESEARCH_ROOT}"
CACHE_DIR="${ROOT_DIR}/data/cache"
LOCK_DIR="${CACHE_DIR}/research_bus_system_sync.lockdir"
LOG_FILE="${CACHE_DIR}/research_bus_system_sync.log"

mkdir -p "$CACHE_DIR"

timestamp() {
  date "+%Y-%m-%dT%H:%M:%S%z"
}

log_line() {
  printf "%s %s\n" "$(timestamp)" "$*" >> "$LOG_FILE"
}

run_step() {
  local label="$1"
  shift
  if "$@" >> "$LOG_FILE" 2>&1; then
    log_line "OK ${label}"
  else
    local status=$?
    log_line "WARN ${label} exited with status ${status}"
  fi
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log_line "SKIP another research bus sync is already running"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

cd "$ROOT_DIR" || exit 1
log_line "START research system sync"

run_step "PFI chat dropbox" scripts/researchBusApi.sh process-dropbox --min-age-seconds 0 --limit 100 --json
run_step "PFI heartbeat" scripts/researchBusApi.sh heartbeat \
  --system-name ResearchBus \
  --status Ready \
  --capability sync_all \
  --capability chat_input \
  --capability chat_dropbox \
  --capability independent_validation \
  --capability holding_update_candidates \
  --capability portfolio_transactions
run_step "PFI request processing" scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
run_step "PFI child system registry" scripts/orchestrateSystems.sh register --json
run_step "PFI child system artifacts" scripts/orchestrateSystems.sh sync-artifacts --json
run_step "PFI research bus sync" scripts/syncResearchBus.sh --json

if [[ -d "$AI_ROOT" ]]; then
  run_step "AI research heartbeat" bash -lc "cd '$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-heartbeat --system-name AI-Research-System --status Ready --capability publish_reports --capability pull_pfi_os_results --capability pull_validation_tasks --capability pull_independent_validation --capability pull_consumer_behavior_state --capability pull_holdings_master --capability pull_portfolio_transactions --capability pull_holding_update_candidates"
  run_step "AI research request processing" bash -lc "cd '$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-process --system-name AI-Research-System --limit 100 --json"
  run_step "AI research bus sync" bash -lc "cd '$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-sync --json"
else
  log_line "WARN AI_ROOT not found: ${AI_ROOT}"
fi

log_line "END research system sync"
