#!/usr/bin/env bash
set -euo pipefail

LABEL="${ALPHA_PHASE6_OWNER_GATE_LABEL:-com.linze.alpha.phase6-owner-gate-sampler}"
AGENT_DIR="${ALPHA_LAUNCH_AGENT_DIR:-$HOME/Library/LaunchAgents}"
PLIST_PATH="$AGENT_DIR/${LABEL}.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

echo "Alpha Phase 6 OWNER-GATE sampler LaunchAgent 已卸载：${LABEL}"
