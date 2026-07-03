#!/usr/bin/env bash
set -euo pipefail

LABEL="${WDA_R3_LAUNCHD_LABEL:-com.linze.wda.v0_2_r3.update}"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ -f "$PLIST_PATH" ]; then
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || launchctl unload "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "Removed $PLIST_PATH"
else
  echo "No launchd plist found at $PLIST_PATH"
fi
