#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTERVAL_SECONDS="${RESEARCH_BUS_WATCH_INTERVAL_SECONDS:-60}"
MAX_LOOPS="${RESEARCH_BUS_WATCH_MAX_LOOPS:-0}"
LOOP_COUNT=0

while true; do
  scripts/syncResearchSystemsOnce.sh
  LOOP_COUNT=$((LOOP_COUNT + 1))
  if [[ "$MAX_LOOPS" != "0" && "$LOOP_COUNT" -ge "$MAX_LOOPS" ]]; then
    break
  fi
  sleep "$INTERVAL_SECONDS"
done
