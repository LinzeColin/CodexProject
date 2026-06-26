#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTERVAL_SECONDS="${RESEARCH_BUS_WATCH_INTERVAL_SECONDS:-30}"
MAX_LOOPS="${RESEARCH_BUS_WATCH_MAX_LOOPS:-0}"
LOOP_COUNT=0

while true; do
  PYTHONDONTWRITEBYTECODE=1 scripts/researchBusApi.sh heartbeat \
    --system-name ResearchBus \
    --status Ready \
    --capability sync_all \
    --capability chat_input \
    --capability chat_dropbox \
    --capability independent_validation \
    --capability holding_update_candidates \
    --capability portfolio_transactions \
    >/dev/null
  PYTHONDONTWRITEBYTECODE=1 scripts/researchBusApi.sh process-dropbox --json >/dev/null
  PYTHONDONTWRITEBYTECODE=1 scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json >/dev/null
  PYTHONDONTWRITEBYTECODE=1 scripts/syncResearchBus.sh --json >/dev/null
  LOOP_COUNT=$((LOOP_COUNT + 1))
  if [[ "$MAX_LOOPS" != "0" && "$LOOP_COUNT" -ge "$MAX_LOOPS" ]]; then
    break
  fi
  sleep "$INTERVAL_SECONDS"
done
