#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/wda_app_update.sh"
LABEL="${WDA_R3_LAUNCHD_LABEL:-com.linze.wda.v0_2_r3.update}"
INTERVAL_SECONDS="${WDA_R3_UPDATE_INTERVAL_SECONDS:-86400}"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_ROOT="${WDA_R3_RUNTIME_ROOT:-/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r3_app_runtime}/logs"

mkdir -p "$(dirname "$PLIST_PATH")" "$LOG_ROOT"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$UPDATE_SCRIPT</string>
  </array>
  <key>StartInterval</key>
  <integer>$INTERVAL_SECONDS</integer>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$LOG_ROOT/launchd-update.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_ROOT/launchd-update.err.log</string>
</dict>
</plist>
EOF

if [ "${1:-}" = "--load" ]; then
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || launchctl load "$PLIST_PATH"
  echo "Loaded $LABEL"
else
  echo "Wrote launchd plist: $PLIST_PATH"
  echo "Run with --load to load it."
fi
