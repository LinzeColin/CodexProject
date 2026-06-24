#!/bin/zsh
set -u

ROOT="/Users/linzezhang/Documents/Codex/2026-06-12/codex-dev-automation-using-model-5"
PYTHON="/opt/anaconda3/bin/python"
OUT="$ROOT/data/serenity_launchd.out.log"
ERR="$ROOT/data/serenity_launchd.err.log"
mkdir -p "$ROOT/data"
{
	  echo "==== $(/bin/date '+%Y-%m-%d %H:%M:%S %Z') launchd tick start ===="
	  cd "$ROOT" || exit 78
	  export PATH="/opt/anaconda3/bin:/usr/bin:/bin:/usr/sbin:/sbin"
	  export SERENITY_OPEND_WAIT_SECONDS="${SERENITY_OPEND_WAIT_SECONDS:-75}"
	  "$PYTHON" -m app.cli automation-tick --no-dry-run --send-mail --local --json
  STATUS=$?
  echo "==== $(/bin/date '+%Y-%m-%d %H:%M:%S %Z') launchd tick exit_status=$STATUS ===="
  /bin/sleep 12
  exit 0
} >> "$OUT" 2>> "$ERR"
