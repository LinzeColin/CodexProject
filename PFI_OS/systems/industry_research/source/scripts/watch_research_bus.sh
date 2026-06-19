#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTERVAL_SECONDS="${RESEARCH_BUS_WATCH_INTERVAL_SECONDS:-30}"
MAX_LOOPS="${RESEARCH_BUS_WATCH_MAX_LOOPS:-0}"
LOOP_COUNT=0

while true; do
  PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-heartbeat \
    --system-name AI-Research-System \
    --status Ready \
    --capability publish_reports \
    --capability pull_pfi_os_results \
    --capability pull_validation_tasks \
    --capability pull_independent_validation \
    --capability pull_consumer_behavior_state \
    --capability pull_holdings_master \
    --capability pull_portfolio_transactions \
    --capability pull_holding_update_candidates \
    >/dev/null
  PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-process --system-name AI-Research-System --limit 100 --json >/dev/null
  PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-sync --json >/dev/null
  LOOP_COUNT=$((LOOP_COUNT + 1))
  if [[ "$MAX_LOOPS" != "0" && "$LOOP_COUNT" -ge "$MAX_LOOPS" ]]; then
    break
  fi
  sleep "$INTERVAL_SECONDS"
done
